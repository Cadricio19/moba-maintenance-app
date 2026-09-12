import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import base64
import os

st.set_page_config(
    page_title="MOBA FT 330 & FL 330 Assistant",
    page_icon="⚙️",
    layout="wide"
)

# Fungsi Memaparkan Halaman PDF Spesifik
def display_pdf_page(pdf_path, page_num):
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_html = f'<iframe src="data:application/pdf;base64,{base64_pdf}#page={page_num}" width="100%" height="650" type="application/pdf"></iframe>'
        st.markdown(pdf_html, unsafe_allow_html=True)
    else:
        st.warning(f"Fail '{pdf_path}' tidak ditemui dalam folder projek.")

# Pangkalan Data Isu Lazim & Muka Surat Dokumen Asal
PRESET_DIAGNOSTICS = [
    {
        "title": "Infeed Shaking / Gegaran Rantai Masukan",
        "module": "Omnia FT 330",
        "doc": "Omnia_FT_Service.pdf",
        "page": 61,
        "vague_check": "Adakah MultiDrum kerap trip (Emergency Stop) atau rantai bawah melompat?",
        "summary": "1. Spring keselamatan MultiDrum standard: 110 mm (min 100 mm).\n2. Rel sokongan rantai kembali Double Roll mesti setinggi mungkin.\n3. Kelegaan roller mestilah 0.5 - 1.0 mm.\n4. Rujuk bab 6.3.7 untuk talaan penuh."
    },
    {
        "title": "Ketegangan Toothed Belt Suction Head",
        "module": "Loader FL 330",
        "doc": "FL_Loader_Service.pdf",
        "page": 112,
        "vague_check": "Adakah tali sawat berbunyi atau pergerakan cawan sedutan tersentak?",
        "summary": "1. Tetapkan ketegangan toothed belt pada 60 Hz menggunakan meter frekuensi akustik.\n2. Jarak cawan sedutan di atas plateau: 30 - 33 mm.\n3. Rujuk bab 8.9.1 manual FL."
    },
    {
        "title": "Ketegangan Toothed Belt Gripper Head",
        "module": "Loader FL 330",
        "doc": "FL_Loader_Service.pdf",
        "page": 126,
        "vague_check": "Adakah kedudukan pencengkam lari dari dulang?",
        "summary": "1. Tetapkan ketegangan toothed belt Gripper Head pada 46 - 47 Hz.\n2. Jarak bukaan grippers standard: 290 mm.\n3. Rujuk bab 8.10.4 manual FL."
    },
    {
        "title": "Penentukuran Penimbang (Loadcell Calibration)",
        "module": "Omnia FT 330",
        "doc": "Omnia_FT_Service.pdf",
        "page": 105,
        "vague_check": "Adakah gram telur lari atau berlaku ralat komunikasi CarWgPc?",
        "summary": "1. Jalankan Empty Carrier Calibration (10/10 cycles).\n2. Kalibrasi pembawa menggunakan pemberat plastik rasmi MOBA 63 gram (Art. 80206980).\n3. Rujuk bab 9.7 manual FT."
    },
    {
        "title": "Jangka Hayat Tiub Lampu UV-C Infeed",
        "module": "Sanitasi Infeed",
        "doc": "Philips_UV_Specs.pdf",
        "page": 1,
        "vague_check": "Adakah lampu menyala malap atau meter jam melebihi had?",
        "summary": "1. Model tiub: Philips TUV PL-L 55W/4P HF (Pangkalan 2G11).\n2. Jangka hayat operasi: 9,000 jam sebelum penurunan radiasi >15%.\n3. Sentiasa matikan mesin sebelum menyentuh modul UV."
    }
]

# Navigasi Tab
tab_diag, tab_specs, tab_pm = st.tabs([
    "🔍 Diagnostik & Rujukan Dokumen", 
    "📏 Parameter & Toleransi Kunci", 
    "🛠️ Penjejak PM & Jam Operasi"
])

# ----------------------------------------------------
# TAB 1: DIAGNOSTIK & SEARCH MANUAL
# ----------------------------------------------------
with tab_diag:
    col_left, col_right = st.columns([1, 1])
    
    target_doc = None
    target_page = 1

    with col_left:
        st.subheader("Pilih Isu Kerosakan")
        issue_names = ["-- Pilih Masalah --"] + [f"{p['title']} ({p['module']})" for p in PRESET_DIAGNOSTICS]
        selected = st.selectbox("Masalah Lazim:", issue_names)

        if selected != "-- Pilih Masalah --":
            match = next(p for p in PRESET_DIAGNOSTICS if f"{p['title']} ({p['module']})" == selected)
            st.warning(f"**Soalan Penentu:** {match['vague_check']}")
            st.info(f"**Tindakan Pantas:**\n{match['summary']}")
            target_doc = match["doc"]
            target_page = match["page"]

        st.markdown("---")
        st.subheader("Atau Cari Teks Terus Dalam Manual")
        search_query = st.text_input("Kata kunci carian (cth: resolver, vacuum, spring):")

        if search_query:
            st.write("Keputusan padanan muka surat:")
            manuals_to_search = [
                ("Omnia FT Service", "Omnia_FT_Service.pdf"),
                ("FL Loader Service", "FL_Loader_Service.pdf"),
                ("Philips UV Specs", "Philips_UV_Specs.pdf")
            ]
            for name, path in manuals_to_search:
                if os.path.exists(path):
                    doc = fitz.open(path)
                    for p_num in range(len(doc)):
                        if search_query.lower() in doc[p_num].get_text().lower():
                            if st.button(f"Lihat {name} - M/S {p_num + 1}", key=f"{name}_{p_num}"):
                                target_doc = path
                                target_page = p_num + 1
                            break

    with col_right:
        st.subheader("📄 Muka Surat Manual Asal")
        if target_doc:
            st.caption(f"Memaparkan `{target_doc}` pada Halaman {target_page}")
            display_pdf_page(target_doc, target_page)
        else:
            st.info("Pilih masalah di sebelah kiri atau buat carian teks untuk membuka manual rujukan asal secara automatik di sini.")

# ----------------------------------------------------
# TAB 2: PARAMETER & TOLERANSI KUNCI
# ----------------------------------------------------
with tab_specs:
    st.subheader("Jadual Toleransi & Parameter Rasmi")
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

# ----------------------------------------------------
# TAB 3: PENJEJAK PM & JAM OPERASI
# ----------------------------------------------------
with tab_pm:
    st.subheader("Penjejak Penyelenggaraan & Jangka Hayat Lampu UV-C")
    hrs = st.number_input("Masukkan Jumlah Jam Operasi Mesin:", min_value=0, value=2400, step=50)

    # Status Lampu UV (9,000 jam had)
    uv_used = hrs % 9000
    st.write(f"**Status Tiub Philips TUV PL-L 55W:** {uv_used} / 9,000 Jam Operasi")
    st.progress(min(uv_used / 9000.0, 1.0))
    if uv_used >= 8500:
        st.error("PERHATIAN: Lampu UV-C sudah menghampiri had 9,000 jam! Sediakan gantian untuk elak degradasi dos nyahkuman.")
    else:
        st.success("Intensiti UV-C dalam keadaan memuaskan.")

    st.markdown("---")
    st.markdown("**Tugasan PM Berpandukan Jam Operasi:**")
    st.write("• **Setiap 8 Jam:** Cuci sisa telur pada pembawa dan lap penderia optik.")
    st.write("• **Setiap 40 Jam:** Bersihkan bulu/kulit telur di kawasan dropset.")
    st.write("• **Setiap 200 Jam:** Pelinciran rantai infeed & cuci penapis semburan air.")
    st.write("• **Setiap 1,200 Jam:** Periksa ketegangan toothed belt (Hz) dan rantai.")
    st.write("• **Setiap 2,400 Jam:** Ganti penapis udara dan uji semua suis interlock/Emergency Stop.")