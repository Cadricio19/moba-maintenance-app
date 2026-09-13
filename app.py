import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import os

st.set_page_config(
    page_title="MOBA FT 330 & FL 330 Assistant",
    page_icon="⚙️",
    layout="wide"
)

# 1. Inisialisasi Session State (Simpan memori dokumen & muka surat)
if "target_doc" not in st.session_state:
    st.session_state.target_doc = None
if "target_page" not in st.session_state:
    st.session_state.target_page = 1

# 2. Fungsi Ekstrak Halaman PDF kepada Gambar PNG
def get_pdf_page_image(pdf_path, page_num):
    if os.path.exists(pdf_path):
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            # Pastikan nombor halaman sah (1-indexed ke 0-indexed)
            actual_page = max(1, min(page_num, total_pages))
            page = doc[actual_page - 1]
            
            # Render halaman ke imej beresolusi 150 DPI (jelas dibaca)
            pix = page.get_pixmap(dpi=150)
            return pix.tobytes("png"), total_pages
        except Exception as e:
            st.error(f"Ralat memproses fail PDF: {e}")
            return None, 0
    return None, 0

# 3. Pangkalan Data Masalah Lazim
PRESET_DIAGNOSTICS = [
    {
        "title": "Infeed Shaking / Gegaran Rantai Masukan",
        "module": "Omnia FT 330",
        "doc": "Omnia_FT_Service.pdf",
        "page": 61,
        "vague_check": "Adakah MultiDrum kerap trip (Emergency Stop) atau rantai bawah melompat?",
        "summary": "1. Spring keselamatan MultiDrum standard: 110 mm (min: 100 mm).\n2. Rel sokongan rantai kembali Double Roll mesti dilaraskan setinggi mungkin.\n3. Kelegaan roller mestilah 0.5 - 1.0 mm.\n4. Rujuk Bab 6.3.7 manual FT."
    },
    {
        "title": "Ketegangan Toothed Belt Suction Head",
        "module": "Loader FL 330",
        "doc": "FL_Loader_Service.pdf",
        "page": 112,
        "vague_check": "Adakah pergerakan cawan sedutan tersentak atau belt berbunyi?",
        "summary": "1. Tetapkan ketegangan toothed belt pada frekuensi tepat 60 Hz.\n2. Jarak cawan sedutan di atas plateau: 30 - 33 mm.\n3. Rujuk Bab 8.9.1 manual FL."
    },
    {
        "title": "Ketegangan Toothed Belt Gripper Head",
        "module": "Loader FL 330",
        "doc": "FL_Loader_Service.pdf",
        "page": 126,
        "vague_check": "Adakah cengkaman dulang lari dari kedudukan asal?",
        "summary": "1. Tetapkan ketegangan toothed belt Gripper Head pada 46 – 47 Hz.\n2. Jarak bukaan grippers: 290 mm.\n3. Rujuk Bab 8.10.4 manual FL."
    },
    {
        "title": "Penentukuran Penimbang (Loadcell Calibration)",
        "module": "Omnia FT 330",
        "doc": "Omnia_FT_Service.pdf",
        "page": 105,
        "vague_check": "Adakah gram telur lari atau ralat komunikasi CarWgPc?",
        "summary": "1. Jalankan Empty Carrier Calibration (10/10 kitaran kelajuan tinggi).\n2. Kalibrasi pembawa dengan pemberat plastik MOBA 63 gram (Art. 80206980).\n3. Rujuk Bab 9.7 manual FT."
    },
    {
        "title": "Jangka Hayat Tiub Lampu UV-C Infeed",
        "module": "Sanitasi Infeed",
        "doc": "Philips_UV_Specs.pdf",
        "page": 1,
        "vague_check": "Adakah meter jam operasi sudah melebihi 9,000 jam?",
        "summary": "1. Model tiub: Philips TUV PL-L 55W/4P HF (Pangkalan 2G11 4-Pin).\n2. Jangka hayat berguna: 9,000 jam sebelum penurunan radiasi melebihi 15%.\n3. Pastikan LOTO dipatuhi sebelum menukar tiub."
    }
]

# Susun Atur Tab
tab_diag, tab_specs, tab_pm = st.tabs([
    "🔍 Diagnostik & Rujukan Dokumen", 
    "📏 Parameter & Toleransi Kunci", 
    "🛠️ Penjejak PM & Jam Operasi"
])

# ====================================================
# TAB 1: DIAGNOSTIK & SEMAKAN MANUAL ASAL
# ====================================================
with tab_diag:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("1. Pilih Masalah Lazim")
        issue_names = ["-- Pilih Masalah --"] + [f"{p['title']} ({p['module']})" for p in PRESET_DIAGNOSTICS]
        selected = st.selectbox("Senarai Isu Operasi:", issue_names)

        if selected != "-- Pilih Masalah --":
            match = next(p for p in PRESET_DIAGNOSTICS if f"{p['title']} ({p['module']})" == selected)
            st.warning(f"**Soalan Penentu (Triage):** {match['vague_check']}")
            st.info(f"**Tindakan Pantas:**\n{match['summary']}")
            if st.button(f"📖 Buka Dokumen: {match['doc']} (M/S {match['page']})", key="btn_preset"):
                st.session_state.target_doc = match["doc"]
                st.session_state.target_page = match["page"]

        st.markdown("---")
        st.subheader("2. Carian Teks Bebas Dalam Manual")
        search_query = st.text_input("Taip kata kunci teknikal (cth: loader, vacuum, chain, sensor):")

        if search_query:
            st.write("Padanan ditemui dalam fail PDF (Klik butang untuk buka):")
            manuals_to_search = [
                ("Omnia FT Service", "Omnia_FT_Service.pdf"),
                ("FL Loader Service", "FL_Loader_Service.pdf"),
                ("Philips UV Specs", "Philips_UV_Specs.pdf")
            ]
            for doc_name, doc_path in manuals_to_search:
                if os.path.exists(doc_path):
                    doc = fitz.open(doc_path)
                    found_count = 0
                    for p_num in range(len(doc)):
                        if search_query.lower() in doc[p_num].get_text().lower():
                            btn_label = f"Lihat {doc_name} — Muka Surat {p_num + 1}"
                            if st.button(btn_label, key=f"search_{doc_name}_{p_num}"):
                                st.session_state.target_doc = doc_path
                                st.session_state.target_page = p_num + 1
                            found_count += 1
                            if found_count >= 3:  # Hadkan paparan 3 muka surat pertama yang sepadan
                                break

    with col_right:
        st.subheader("📄 Paparan Dokumen Rujukan Asal")
        
        if st.session_state.target_doc:
            img_bytes, total = get_pdf_page_image(st.session_state.target_doc, st.session_state.target_page)
            if img_bytes:
                st.success(f"Memaparkan `{st.session_state.target_doc}` | Halaman {st.session_state.target_page} daripada {total}")
                
                # Navigasi halaman sebelumnya / seterusnya
                nav_prev, nav_next = st.columns(2)
                with nav_prev:
                    if st.button("⬅️ Muka Surat Sebelumnya", use_container_width=True):
                        if st.session_state.target_page > 1:
                            st.session_state.target_page -= 1
                            st.rerun()
                with nav_next:
                    if st.button("Muka Surat Seterusnya ➡️", use_container_width=True):
                        if st.session_state.target_page < total:
                            st.session_state.target_page += 1
                            st.rerun()

                # Papar imej dokumen asal
                st.image(img_bytes, use_container_width=True)
        else:
            st.info("Pilih isu kerosakan di sebelah kiri atau klik butang carian muka surat untuk memaparkan lembaran manual rasmi di sini.")

# ====================================================
# TAB 2: PARAMETER & TOLERANSI KUNCI
# ====================================================
with tab_specs:
    st.subheader("Jadual Toleransi & Parameter Rasmi MOBA")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Foodtec Loader FL 330**")
        st.table(pd.DataFrame([
            {"Komponen": "Suction Head Toothed Belt", "Nilai": "60 Hz"},
            {"Komponen": "Gripper Head Toothed Belt", "Nilai": "46 – 47 Hz"},
            {"Komponen": "Suction-Gripper Belt", "Nilai": "55 – 60 Hz"},
            {"Komponen": "Tinggi Cawan Suction atas Plateau", "Nilai": "30 – 33 mm"},
            {"Komponen": "Jarak Bukaan Grippers", "Nilai": "290 mm"},
            {"Komponen": "Tekanan Minimum Pneumatik", "Nilai": "4.0 bar (Trip) / 5.0 bar"}
        ]))
    with col2:
        st.markdown("**Omnia FT 330 Grader**")
        st.table(pd.DataFrame([
            {"Komponen": "Spring MultiDrum™ FT 330", "Nilai": "110 mm (Min: 100 mm)"},
            {"Komponen": "Kelegaan Double Roll / Crack Roller", "Nilai": "0.5 – 1.0 mm"},
            {"Komponen": "Jarak Penderia Logam Keluli", "Nilai": "2.0 mm"},
            {"Komponen": "Jarak Penderia Stainless Steel", "Nilai": "1.0 mm"},
            {"Komponen": "Pemberat Kalibrasi Pembawa", "Nilai": "63 gram (Art. 80206980)"},
            {"Komponen": "Pemberat Ujian Loadcell", "Nilai": "130 gram"}
        ]))

# ====================================================
# TAB 3: PENJEJAK PM & JAM OPERASI
# ====================================================
with tab_pm:
    st.subheader("Penjejak Penyelenggaraan & Jangka Hayat Lampu UV-C")
    hrs = st.number_input("Masukkan Jumlah Jam Operasi Mesin:", min_value=0, value=2400, step=50)

    uv_used = hrs % 9000
    st.write(f"**Status Tiub Philips TUV PL-L 55W:** {uv_used} / 9,000 Jam Operasi")
    st.progress(min(uv_used / 9000.0, 1.0))
    if uv_used >= 8500:
        st.error("PERHATIAN: Lampu UV-C menghampiri had 9,000 jam! Sediakan gantian segera.")
    else:
        st.success("Intensiti UV-C dalam keadaan memuaskan.")

    st.markdown("---")
    st.markdown("**Tugasan PM Berpandukan Jam Operasi:**")
    st.write("• **Setiap 8 Jam:** Cuci sisa telur pada pembawa dan lap penderia optik.")
    st.write("• **Setiap 40 Jam:** Bersihkan bulu/kulit telur di kawasan dropset.")
    st.write("• **Setiap 200 Jam:** Pelinciran rantai infeed & cuci penapis semburan air.")
    st.write("• **Setiap 1,200 Jam:** Periksa ketegangan toothed belt (Hz) dan rantai.")
    st.write("• **Setiap 2,400 Jam:** Ganti penapis udara dan periksa semua suis Emergency Stop.")
