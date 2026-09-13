import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import os
import sqlite3
from datetime import datetime
from google import genai
from google.genai import types

st.set_page_config(
    page_title="MOBA FT 330 & FL 330 AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# ----------------------------------------------------
# 1. SAMBUNGAN GOOGLE GEMINI API
# ----------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
if not api_key:
    st.error("API Key Gemini tidak ditemui! Sila masukkan GEMINI_API_KEY dalam Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# ----------------------------------------------------
# 2. PANGKALAN DATA PEMBELAJARAN KILANG (SQLITE)
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
# 3. PENGINDEKSAN & EKSTRAKSI TEKS MANUAL (CACHE)
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
                if len(text.strip()) > 30:
                    docs_payload.append({
                        "file": filename,
                        "doc_name": display_name,
                        "page": p_num + 1,
                        "text": text
                    })
    return docs_payload

manual_data = load_all_manuals()

def retrieve_relevant_chunks(query, top_n=5):
    """Mencari muka surat manual paling relevan berdasarkan skor perkataan."""
    words = [w.lower() for w in query.split() if len(w) > 2]
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

# Fungsi Memaparkan Halaman PDF
def get_pdf_page_image(pdf_path, page_num):
    if os.path.exists(pdf_path):
        try:
            doc = fitz.open(pdf_path)
            actual_page = max(1, min(page_num, len(doc)))
            page = doc[actual_page - 1]
            pix = page.get_pixmap(dpi=150)
            return pix.tobytes("png"), len(doc)
        except Exception as e:
            return None, 0
    return None, 0

# ----------------------------------------------------
# 4. MEMORI STATE UNTUK PAPARAN MANUAL
# ----------------------------------------------------
if "view_doc" not in st.session_state:
    st.session_state.view_doc = "Omnia_FT_Service.pdf"
if "view_page" not in st.session_state:
    st.session_state.view_page = 156

# ----------------------------------------------------
# 5. ANTARAMUKA STREAMLIT
# ----------------------------------------------------
tab_ai, tab_map, tab_logs = st.tabs([
    "🤖 AI Troubleshooter Pintar", 
    "🗺️ Pelan Susun Atur Mesin", 
    "📚 Rekod Pengalaman Kilang (Learning Store)"
])

# ====================================================
# TAB 1: AI DIAGNOSTIK GENERATIF (GEMINI + RAG)
# ====================================================
with tab_ai:
    col_chat, col_view = st.columns([1, 1])

    with col_chat:
        st.subheader("Tanya Apa Saja Isu Kerosakan")
        user_problem = st.text_area(
            "Huraikan masalah di lantai kilang (boleh guna BM biasa/santai):",
            placeholder="cth: semalam ada masalah packing lane, chain bergegar kuat bawah bufferset tu. apa perlu adjust?",
            height=90
        )

        btn_diagnose = st.button("🚀 Analisis Masalah & Cari Solusi", use_container_width=True)

        if btn_diagnose and user_problem.strip():
            with st.spinner("AI sedang membaca Service Manual & Sejarah Kerosakan Kilang..."):
                # 1. Dapatkan keratan teks manual berkaitan
                relevant_chunks = retrieve_relevant_chunks(user_problem, top_n=6)
                
                # 2. Dapatkan rekod kerosakan lepas dari pangkalan data pembelajaran
                past_logs_df = get_past_logs()
                past_logs_text = ""
                if not past_logs_df.empty:
                    past_logs_text = past_logs_df.head(5).to_string(index=False)

                # 3. Bina konteks untuk Gemini
                context_text = "\n---\n".join([
                    f"[DOKUMEN: {c['doc_name']} | FAIL: {c['file']} | MUKA SURAT: {c['page']}]\n{c['text'][:1200]}"
                    for c in relevant_chunks
                ])

                system_prompt = (
                    "Anda ialah Jurutera Kanan Penyelenggaraan bagi mesin gred telur MOBA Omnia FT 330 "
                    "dan Foodtec Loader FL 330. Jawab dalam Bahasa Melayu secara profesional, padat, dan teknikal.\n"
                    "Gunakan maklumat rujukan manual dan sejarah kilang yang dibekalkan di bawah.\n"
                    "FORMAT JAWAPAN:\n"
                    "1. Ringkasan Diagnostik & Punca Mekanikal/Elektrikal.\n"
                    "2. Soalan Pengesahan (jika aduan juruteknik masih kabur).\n"
                    "3. Tindakan Pembetulan Langkah demi Langkah (nyatakan nombor bab, nilai mm, Hz, atau bar).\n"
                    "4. Rujukan Muka Surat & Dokumen Tepat (wajib nyatakan nama fail dan muka surat)."
                )

                full_prompt = (
                    f"SEJARAH REKOD KEROSAKAN KILANG SEBELUM INI:\n{past_logs_text}\n\n"
                    f"PETIKAN MANUAL TEKNIKAL MOBA:\n{context_text}\n\n"
                    f"ADUAN JURUTEKNIK:\n{user_problem}"
                )

                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=0.2
                        )
                    )
                    st.session_state.ai_response = response.text
                    st.session_state.relevant_chunks = relevant_chunks
                except Exception as e:
                    st.error(f"Ralat AI: {e}")

        # Paparan Jawapan AI
        if "ai_response" in st.session_state:
            st.markdown("### 📋 Hasil Diagnostik AI:")
            st.markdown(st.session_state.ai_response)

            # Papar pintasan butang untuk membuka muka surat manual yang dikesan
            if "relevant_chunks" in st.session_state:
                st.markdown("---")
                st.markdown("**Buka Muka Surat Manual Berkaitan:**")
                cols_btn = st.columns(len(st.session_state.relevant_chunks[:3]))
                for i, chunk in enumerate(st.session_state.relevant_chunks[:3]):
                    with cols_btn[i]:
                        lbl = f"📖 {chunk['file'][:8]}.. M/S {chunk['page']}"
                        if st.button(lbl, key=f"btn_src_{i}"):
                            st.session_state.view_doc = chunk["file"]
                            st.session_state.view_page = chunk["page"]
                            st.rerun()

            # Bahagian Gelung Pembelajaran (Feedback Loop)
            st.markdown("---")
            with st.expander("📝 Rekod Solusi Sebenar di Kilang (AI Belajar Daripada Ini)"):
                st.caption("Selepas masalah selesai dibaiki, masukkan apa yang sebenarnya berlaku supaya AI lebih pintar pada masa depan.")
                actual_cause = st.text_input("Punca Sebenar Ditemui:", placeholder="cth: Bearing sprocket penegang pecah, bukan rantai kendur")
                action_done = st.text_input("Tindakan Pembaikan Dibuat:", placeholder="cth: Tukar bearing 6204 dan tala semula spring ke 1.0 mm")
                mod_affected = st.selectbox("Bahagian Terlibat:", ["Packing Lane", "Loader FL 330", "Infeed FT 330", "Penimbang", "Lain-lain"])
                
                if st.button("💾 Simpan ke Pangkalan Data Kilang"):
                    if actual_cause and action_done:
                        save_log(user_problem, actual_cause, action_done, mod_affected)
                        st.success("✅ Berjaya disimpan! AI akan menggunakan maklumat ini untuk cadangan masa depan.")
                        st.rerun()

    # Kolum Kanan: Paparan Halaman Manual
    with col_view:
        st.subheader("📄 Paparan Dokumen Rujukan Asal")
        if st.session_state.view_doc:
            img_bytes, total = get_pdf_page_image(st.session_state.view_doc, st.session_state.view_page)
            if img_bytes:
                st.success(f"Fail: `{st.session_state.view_doc}` | Muka Surat {st.session_state.view_page} / {total}")
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

# ====================================================
# TAB 2: PELAN ATAS SKEMATIK
# ====================================================
with tab_map:
    st.subheader("🗺️ Pelan Pandangan Atas")
    plan_choice = st.radio("Pilih Pandangan:", ["Packing Lane (Bab 11)", "Loader FL 330 (M/S 57)", "Omnia FT Grader (M/S 188)"], horizontal=True)
    if plan_choice == "Packing Lane (Bab 11)":
        img, _ = get_pdf_page_image("Omnia_FT_Service.pdf", 133)
    elif plan_choice == "Loader FL 330 (M/S 57)":
        img, _ = get_pdf_page_image("FL_Loader_Service.pdf", 57)
    else:
        img, _ = get_pdf_page_image("Omnia_FT_Service.pdf", 188)
    if img:
        st.image(img, use_container_width=True)

# ====================================================
# TAB 3: LOG SEJARAH & PEMBELAJARAN KILANG
# ====================================================
with tab_logs:
    st.subheader("📚 Rekod Pengalaman Pembaikan Kilang")
    st.caption("Pangkalan data ini dibina secara automatik daripada maklum balas juruteknik dan dirujuk oleh AI semasa setiap sesi diagnostik.")
    logs_df = get_past_logs()
    if not logs_df.empty:
        st.dataframe(logs_df, use_container_width=True)
    else:
        st.info("Belum ada rekod kerosakan disimpan. Masukkan solusi di Tab 1 selepas kerja servis dilakukan.")
