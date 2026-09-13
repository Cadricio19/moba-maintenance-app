import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import os
import re
import sqlite3
import requests
import json
import zipfile
import gdown
from datetime import datetime

st.set_page_config(
    page_title="MOBA FT 330 & FL 330 AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# ----------------------------------------------------
# 1. TETAPAN KUNCI & GOOGLE DRIVE FILE ID
# ----------------------------------------------------
raw_api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
CLEAN_API_KEY = str(raw_api_key).strip().strip('"').strip("'")

PARTS_FILE_ID = st.secrets.get("PARTS_ZIP_FILE_ID", os.getenv("PARTS_ZIP_FILE_ID", ""))

if not CLEAN_API_KEY:
    st.error("API Key Gemini tidak ditemui! Sila semak GEMINI_API_KEY dalam Streamlit Secrets.")
    st.stop()

# ----------------------------------------------------
# 2. SISTEM PENGURUSAN 16,000+ GAMBAR ALAT GANTI
# ----------------------------------------------------
PARTS_EXTRACT_DIR = "moba_parts_extracted"

@st.cache_resource(show_spinner="Memuat turun & mengekstrak 16,000+ gambar komponen dari Google Drive...")
def setup_parts_database():
    """Muat turun moba_parts.zip dari Google Drive sekali sahaja dan indekskan failnya."""
    part_index = {} # format: {'0131157': 'moba_parts_extracted/0131157-01.jpg'}

    if not os.path.exists(PARTS_EXTRACT_DIR) or len(os.listdir(PARTS_EXTRACT_DIR)) < 100:
        os.makedirs(PARTS_EXTRACT_DIR, exist_ok=True)
        zip_path = "moba_parts.zip"

        if PARTS_FILE_ID:
            try:
                download_url = f"https://drive.google.com/uc?id={PARTS_FILE_ID}"
                gdown.download(download_url, zip_path, quiet=False)
                
                if os.path.exists(zip_path):
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(PARTS_EXTRACT_DIR)
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
            except Exception as e:
                st.sidebar.warning(f"Gagal memuat turun gambar komponen: {e}")

    # Indeks semua fail gambar yang berjaya diekstrak
    if os.path.exists(PARTS_EXTRACT_DIR):
        for root, _, files in os.walk(PARTS_EXTRACT_DIR):
            for f in files:
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    # Bersihkan nombor bahagian dari nama fail (cth: 0131157-01.jpg -> 0131157)
                    base_name = os.path.splitext(f)[0]
                    clean_core = re.sub(r'[^0-9a-zA-Z]', '', base_name.split('-')[0])
                    full_path = os.path.join(root, f)
                    if clean_core not in part_index:
                        part_index[clean_core] = full_path

    return part_index

part_lookup_db = setup_parts_database()

def find_component_image(search_query):
    """Cari gambar komponen menggunakan nombor bahagian atau nama asas."""
    clean_q = re.sub(r'[^0-9a-zA-Z]', '', str(search_query))
    if clean_q in part_lookup_db:
        return part_lookup_db[clean_q]
    
    # Carian padanan fleksibel jika nombor bahagian separa
    for p_num, p_path in part_lookup_db.items():
        if len(clean_q) >= 5 and (clean_q in p_num or p_num in clean_q):
            return p_path
    return None

# ----------------------------------------------------
# 3. SAMBUNGAN GEMINI API DENGAN DYNAMIC SELECTOR
# ----------------------------------------------------
@st.cache_data(ttl=3600)
def get_working_gemini_models():
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={CLEAN_API_KEY}"
    valid_models = []
    try:
        res = requests.get(list_url, timeout=15)
        if res.status_code == 200:
            data = res.json()
            for m in data.get("models", []):
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
                    valid_models.append(m.get("name", "").replace("models/", ""))
    except Exception:
        pass
    
    fallback_priority = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-3.8-flash", "gemini-flash-experimental"]
    for fb in fallback_priority:
        if fb not in valid_models:
            valid_models.append(fb)
    return valid_models

def call_gemini_api(conversation_history):
    candidate_models = get_working_gemini_models()
    last_error = ""

    contents_payload = []
    for msg in conversation_history:
        role = "user" if msg["role"] == "user" else "model"
        contents_payload.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    for model_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={CLEAN_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": contents_payload,
            "generationConfig": {"temperature": 0.2}
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=35)
            if response.status_code == 200:
                data = response.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    return "Ralat: Format respons AI tidak dapat diproses."
            else:
                last_error = f"Model {model_name} -> HTTP {response.status_code}: {response.text}"
        except Exception as e:
            last_error = str(e)

    raise Exception(f"Semua model gagal dihubungi. Respons terakhir: {last_error}")

# ----------------------------------------------------
# 4. PANGKALAN DATA SEJARAH REKOD KILANG (SQLITE)
# ----------------------------------------------------
def init_db():
    conn = sqlite3.connect("factory_logs.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS breakdown_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_query TEXT,
            actual_root_cause TEXT,
            action_taken TEXT,
            module TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_log(query, root_cause, action, module):
    conn = sqlite3.connect("factory_logs.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO breakdown_logs (timestamp, user_query, actual_root_cause, action_taken, module)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), query, root_cause, action, module))
    conn.commit()
    conn.close()

def get_past_logs():
    conn = sqlite3.connect("factory_logs.db")
    df = pd.read_sql_query("SELECT * FROM breakdown_logs ORDER BY id DESC", conn)
    conn.close()
    return df

init_db()

# ----------------------------------------------------
# 5. PENGINDEKSAN MANUAL & CARIAN TEKS KONTEKS
# ----------------------------------------------------
@st.cache_resource
def load_all_manuals():
    docs_payload = []
    files = [
        ("Omnia_FT_Service.pdf", "Omnia FT 330 Service Manual"),
        ("FL_Loader_Service.pdf", "Foodtec Loader FL 330 Service Manual"),
        ("Philips_UV_Specs.pdf", "Philips TUV PL-L 55W UV-C Specs")
    ]
    for filename, display_name in files:
        if os.path.exists(filename):
            doc = fitz.open(filename)
            for p_num in range(len(doc)):
                text = doc[p_num].get_text()
                if len(text.strip()) > 20:
                    docs_payload.append({
                        "file": filename,
                        "doc_name": display_name,
                        "page": p_num + 1,
                        "text": text
                    })
    return docs_payload

manual_data = load_all_manuals()

BM_SYNONYMS = {
    "tali sawat": "belt toothed timing",
    "rantai": "chain sprocket",
    "penimbang": "loadcell weighing",
    "pencengkam": "gripper suction cup",
    "sedut": "suction vacuum manifold",
    "bergegar": "shaking vibrate flapping play loose",
    "gegar": "shaking vibrate flapping",
    "bawah": "bottom lower pusher guide",
    "bufferset": "buffer dropset",
    "plastic hitam": "pusher auxiliary transport carrier",
    "bekas": "tray package carton"
}

def retrieve_relevant_chunks(query, top_n=6):
    query_expanded = query.lower()
    for bm, syn in BM_SYNONYMS.items():
        if bm in query_expanded:
            query_expanded += f" {syn}"

    words = [w for w in re.findall(r'\b\w+\b', query_expanded) if len(w) > 2]
    scored = []
    for item in manual_data:
        score = 0
        text_lower = item["text"].lower()
        for w in words:
            if w in text_lower:
                score += text_lower.count(w)
        if score > 0:
            scored.append((score, item))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_n]]

def get_pdf_page_image(pdf_path, page_num):
    if os.path.exists(pdf_path):
        try:
            doc = fitz.open(pdf_path)
            actual_page = max(1, min(page_num, len(doc)))
            page = doc[actual_page - 1]
            pix = page.get_pixmap(dpi=150)
            return pix.tobytes("png"), len(doc)
        except Exception:
            return None, 0
    return None, 0

# ----------------------------------------------------
# 6. SESSION STATES
# ----------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "view_doc" not in st.session_state:
    st.session_state.view_doc = "Omnia_FT_Service.pdf"
if "view_page" not in st.session_state:
    st.session_state.view_page = 154
if "relevant_chunks" not in st.session_state:
    st.session_state.relevant_chunks = []
if "detected_parts" not in st.session_state:
    st.session_state.detected_parts = []

# ----------------------------------------------------
# 7. ANTARAMUKA STREAMLIT
# ----------------------------------------------------
tab_ai, tab_parts, tab_map, tab_logs = st.tabs([
    "🤖 AI Troubleshooter Pintar", 
    "📦 Galeri Komponen (16,000+ Parts)",
    "🗺️ Pelan Susun Atur Mesin", 
    "📚 Rekod Pengalaman Kilang (Learning Store)"
])

with tab_ai:
    col_chat, col_view = st.columns([1, 1])

    with col_chat:
        st.subheader("Pusat Diagnostik Interaktif MOBA")
        
        c_head1, c_head2 = st.columns([3, 1])
        with c_head2:
            if st.button("🔄 Mulakan Kes Baharu"):
                st.session_state.messages = []
                st.session_state.relevant_chunks = []
                st.session_state.detected_parts = []
                st.rerun()

        # Paparan Sejarah Perbualan Chat
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg["content"])

        # Input Box Interaktif (Menyokong Soalan Susulan & Double Confirmation)
        chat_ph = "Jawab soalan pengesahan di atas ATAU huraikan masalah baru..." if st.session_state.messages else "Huraikan masalah di lantai kilang (cth: rantai pusher bergegar lejang ke-4)..."
        user_input = st.chat_input(chat_ph)

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner("AI sedang membaca manual MOBA, pangkalan data komponen & merangka solusi..."):
                full_search = " ".join([m["content"] for m in st.session_state.messages if m["role"] == "user"])
                chunks = retrieve_relevant_chunks(full_search, top_n=6)
                st.session_state.relevant_chunks = chunks

                if chunks:
                    st.session_state.view_doc = chunks[0]["file"]
                    st.session_state.view_page = chunks[0]["page"]

                past_logs_df = get_past_logs()
                past_logs_text = past_logs_df.head(5).to_string(index=False) if not past_logs_df.empty else "Tiada rekod sebelumnya."

                context_text = "\n---\n".join([
                    f"[DOKUMEN: {c['doc_name']} | FAIL: {c['file']} | MUKA SURAT: {c['page']}]\n{c['text'][:1400]}"
                    for c in chunks
                ])

                system_instruction = f"""Anda ialah Jurutera Kanan Penyelenggaraan bagi mesin gred telur MOBA Omnia FT 330 dan Foodtec Loader FL 330.
Jawab dalam Bahasa Melayu secara profesional, berstruktur, dan mesra juruteknik kilang.

PANDUAN FORMAT JAWAPAN:
1. Ringkasan Diagnostik & Punca Mekanikal/Elektrikal.
2. Soalan Pengesahan (Kemukakan soalan susulan teknikal bagi double-confirm keadaan mesin).
3. Komponen Terlibat & Rujukan Visual:
   - Nyatakan nama teknikal komponen tepat (cth: Pusher, Tensioner Chain-Wheel, Spring-Tensioner, Bearing).
   - Nyatakan nombor Figure dan nombor muka surat (cth: Fig. 179 M/S 154).
   - Wajib sertakan tag bahagian jika ada nombor part dalam manual/teks: `PART_REF: <nombor_part>` (cth: PART_REF: 0131157).
4. Tindakan Pembetulan Langkah demi Langkah (nyatakan toleransi tepat dalam mm/bar/Hz).
5. Rujukan Dokumen & Muka Surat Tepat.

---
REKOD SEJARAH KEROSAKAN KILANG:
{past_logs_text}

---
PETIKAN MANUAL TEKNIKAL BERKAITAN:
{context_text}
"""

                convo = [
                    {"role": "user", "content": system_instruction},
                    {"role": "model", "content": "Difahami. Saya bersedia mendiagnosis masalah mekanikal mesin MOBA/FL secara terperinci."}
                ]
                for m in st.session_state.messages:
                    convo.append(m)

                try:
                    reply = call_gemini_api(convo)
                    st.session_state.messages.append({"role": "assistant", "content": reply})

                    # Ekstrak jika AI menyebut nombor bahagian PART_REF
                    found_parts = re.findall(r'PART_REF:\s*([0-9A-Za-z\-_]+)', reply)
                    st.session_state.detected_parts = list(set(found_parts))
                    st.rerun()
                except Exception as e:
                    st.error(f"Ralat AI: {e}")

        # Paparan Gambar Komponen Automatik Jika AI Mengesan Part Number
        if st.session_state.detected_parts:
            st.markdown("---")
            st.markdown("#### 🔍 Komponen Fizikal Yang Dikenal Pasti Oleh AI:")
            p_cols = st.columns(min(len(st.session_state.detected_parts), 3))
            for i, p_num in enumerate(st.session_state.detected_parts[:3]):
                with p_cols[i]:
                    img_file = find_component_image(p_num)
                    if img_file and os.path.exists(img_file):
                        st.image(img_file, caption=f"Part No: {p_num}", use_container_width=True)
                    else:
                        st.info(f"Nombor Bahagian: `{p_num}`\n(Imej tiada dalam folder fail)")

        # Butang Pintasan Muka Surat Manual
        if st.session_state.relevant_chunks:
            st.markdown("---")
            st.markdown("**Buka Muka Surat Manual Berkaitan:**")
            cols_btn = st.columns(len(st.session_state.relevant_chunks[:4]))
            for i, chunk in enumerate(st.session_state.relevant_chunks[:4]):
                with cols_btn[i]:
                    lbl = f"📖 {chunk['file'][:9]}.. M/S {chunk['page']}"
                    if st.button(lbl, key=f"btn_src_{i}"):
                        st.session_state.view_doc = chunk["file"]
                        st.session_state.view_page = chunk["page"]
                        st.rerun()

        # Gelung Pembelajaran Kilang (Feedback Store)
        if len(st.session_state.messages) > 1:
            st.markdown("---")
            with st.expander("📝 Rekod Solusi Sebenar di Kilang (AI Belajar Daripada Ini)"):
                actual_cause = st.text_input("Punca Sebenar Ditemui:", placeholder="cth: Gear wheel penegang spring longgar")
                action_done = st.text_input("Tindakan Dibuat:", placeholder="cth: Pindah gear wheel 1 lubang ke bawah dan set kelegaan 1 mm")
                mod_affected = st.selectbox("Bahagian Terlibat:", ["Packing Lane", "Loader FL 330", "Infeed FT 330", "Penimbang", "Lain-lain"])
                
                if st.button("💾 Simpan ke Pangkalan Data Kilang"):
                    first_query = st.session_state.messages[0]["content"] if st.session_state.messages else "Kerosakan"
                    if actual_cause and action_done:
                        save_log(first_query, actual_cause, action_done, mod_affected)
                        st.success("✅ Berjaya disimpan! AI akan mengingati penyelesaian ini.")
                        st.rerun()

    # Panel Kanan: Paparan Manual Asal
    with col_view:
        st.subheader("📄 Paparan Skematik & Muka Surat Manual")
        if st.session_state.view_doc:
            img_bytes, total = get_pdf_page_image(st.session_state.view_doc, st.session_state.view_page)
            if img_bytes:
                st.success(f"Fail: `{st.session_state.view_doc}` | Halaman {st.session_state.view_page} daripada {total}")
                c_prev, c_next = st.columns(2)
                with c_prev:
                    if st.button("⬅️ Muka Surat Sebelumnya", use_container_width=True):
                        if st.session_state.view_page > 1:
                            st.session_state.view_page -= 1
                            st.rerun()
                with c_next:
                    if st.button("Muka Surat Seterusnya ➡️", use_container_width=True):
                        if st.session_state.view_page < total:
                            st.session_state.view_page += 1
                            st.rerun()
                st.image(img_bytes, use_container_width=True)

# TAB 2: GALERI CARIAN 16,000+ GAMBAR SECARA MANUAL
with tab_parts:
    st.subheader("📦 Carian Komponen MOBA Segera")
    st.caption(f"Jumlah komponen sedia ada dalam indeks pantas: **{len(part_lookup_db):,} komponen**")
    
    search_part_no = st.text_input("Masukkan Nombor Bahagian MOBA (cth: 0131157, 0100236, 0103310):", "")
    if search_part_no.strip():
        img_res = find_component_image(search_part_no.strip())
        if img_res and os.path.exists(img_res):
            st.image(img_res, caption=f"Imej Rasmi Bahagian: {os.path.basename(img_res)}", width=400)
        else:
            st.warning("Komponen dengan nombor tersebut tiada dalam pangkalan data.")

with tab_map:
    st.subheader("🗺️ Pelan Susun Atur Mesin")
    plan_choice = st.radio("Pilih Pandangan:", ["Packing Lane (Bab 11)", "Loader FL 330 (M/S 57)", "Omnia FT Grader (M/S 188)"], horizontal=True)
    if plan_choice == "Packing Lane (Bab 11)":
        img, _ = get_pdf_page_image("Omnia_FT_Service.pdf", 133)
    elif plan_choice == "Loader FL 330 (M/S 57)":
        img, _ = get_pdf_page_image("FL_Loader_Service.pdf", 57)
    else:
        img, _ = get_pdf_page_image("Omnia_FT_Service.pdf", 188)
    if img:
        st.image(img, use_container_width=True)

with tab_logs:
    st.subheader("📚 Rekod Pengalaman Pembaikan Kilang")
    logs_df = get_past_logs()
    if not logs_df.empty:
        st.dataframe(logs_df, use_container_width=True)
    else:
        st.info("Belum ada rekod kerosakan disimpan.")
