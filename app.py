import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import os

st.set_page_config(
    page_title="MOBA FT 330 & FL 330 Maintenance Assistant",
    page_icon="⚙️",
    layout="wide"
)

# ----------------------------------------------------
# 1. MEMORI STATE
# ----------------------------------------------------
if "target_doc" not in st.session_state:
    st.session_state.target_doc = "FL_Loader_Service.pdf"
if "target_page" not in st.session_state:
    st.session_state.target_page = 57

def get_pdf_page_image(pdf_path, page_num):
    if os.path.exists(pdf_path):
        try:
            doc = fitz.open(pdf_path)
            actual_page = max(1, min(page_num, len(doc)))
            page = doc[actual_page - 1]
            pix = page.get_pixmap(dpi=150)
            return pix.tobytes("png"), len(doc)
        except Exception as e:
            st.error(f"Ralat render PDF: {e}")
            return None, 0
    return None, 0

# ----------------------------------------------------
# 2. DATA DIAGNOSTIK MENGIKUT ZON MESIN
# ----------------------------------------------------
TROUBLESHOOTING_DB = [
    {
        "id": "loader_vacuum_loss",
        "zone": "Loader: Suction Head",
        "title": "Loader: Telur Jatuh / Cawan Sedutan Hilang Vakum",
        "doc": "FL_Loader_Service.pdf",
        "page": 157,
        "keywords": ["sedut", "vacuum", "suction", "drop", "jatuh", "tak sedut"],
        "symptom": "Cawan sedutan gagal mengangkat telur daripada dulang atau terlepas semasa pemindahan.",
        "root_cause": "Injap blow-back bocor/tersumbat, pemasaan piring lengkung lari, atau tekanan udara < 5 bar.",
        "action": "Tala pemasaan vakum menggunakan pin pelaras 15 mm melalui piring lengkung (curve disk).",
        "specs": "Tekanan Min: 5.0 bar | Tinggi Cawan atas Plateau: 30 - 33 mm"
    },
    {
        "id": "loader_belt_timing",
        "zone": "Loader: Drive Mechanism",
        "title": "Loader: Timing Lari / Tali Sawat Bunyi / Tersentak",
        "doc": "FL_Loader_Service.pdf",
        "page": 112,
        "keywords": ["timing", "belt", "tali sawat", "toothed", "gegar", "frekuensi"],
        "symptom": "Pergerakan Suction Head tersentak atau telur tidak mendarat tepat pada roller.",
        "root_cause": "Ketegangan tali sawat toothed belt kendur atau lari frekuensi standard.",
        "action": "Gunakan acoustic frequency meter. Laraskan bolt sehingga ketegangan mencapai 60 Hz.",
        "specs": "Suction Head: 60 Hz | Gripper Head: 46 - 47 Hz | Suction-Gripper: 55 - 60 Hz"
    },
    {
        "id": "loader_stack_stop_jam",
        "zone": "Loader: Infeed & Lift",
        "title": "Loader: Dulang Bertindih / Stack Stop Jamming",
        "doc": "FL_Loader_Service.pdf",
        "page": 84,
        "keywords": ["stack", "stop", "meja angkat", "lift", "dulang jam", "jamming"],
        "symptom": "Timbunan dulang telur tersangkut semasa masuk ke meja angkat (lift bridge).",
        "root_cause": "Lejang silinder stack stop tidak tepat 90 darjah terhadap belt.",
        "action": "Laraskan kepala rod silinder sehingga flap tepat 90 darjah terhadap tali sawat.",
        "specs": "Lejang Meja Angkat: Maks 260 mm | Jarak Pusat Lift-Transfer: 140 mm"
    },
    {
        "id": "infeed_shaking",
        "zone": "Infeed: Double Roll & MultiDrum",
        "title": "Infeed: Rantai Bergerak Kasar / MultiDrum Trip",
        "doc": "Omnia_FT_Service.pdf",
        "page": 61,
        "keywords": ["infeed", "gegar", "shaking", "rantai", "vibrate", "drum trip"],
        "symptom": "Rantai Double Roll bergetar kuat atau suis keselamatan MultiDrum kerap trip.",
        "root_cause": "Spring MultiDrum kendur, rel sokongan rantai rendah, atau kelegaan roller ketat.",
        "action": "Tala spring MultiDrum kepada 110 mm. Tinggikan rel sokongan rantai kembali.",
        "specs": "Spring MultiDrum: 110 mm (Min: 100 mm) | Kelegaan Roller: 0.5 - 1.0 mm"
    },
    {
        "id": "weighing_loadcell_error",
        "zone": "Grader: Weighing Section",
        "title": "Penimbang: Bacaan Gram Telur Lari / Kalibrasi Gagal",
        "doc": "Omnia_FT_Service.pdf",
        "page": 105,
        "keywords": ["timbang", "weighing", "loadcell", "berat", "gram", "carwgpc"],
        "symptom": "Gred berat telur tidak tepat atau paparan ralat 'PrEr' pada sistem.",
        "root_cause": "Cecair telur kering pada loadcell atau piring pemasaan utama (timing disk) lari.",
        "action": "Jalankan Empty Carrier Calibration (10 kitaran) dan kalibrasi pembawa dengan pemberat 63g.",
        "specs": "Pemberat Kalibrasi Pembawa: 63 gram (Art. 80206980) | Ujian Loadcell: 130 gram"
    }
]

# ----------------------------------------------------
# 3. SUSUN ATUR TAB UTAMA
# ----------------------------------------------------
tab_map, tab_diag, tab_specs, tab_pm = st.tabs([
    "🗺️ Pelan Susun Atur Mesin (Top-Down)",
    "🔍 Diagnostik Kerosakan & Manual", 
    "📏 Parameter & Toleransi Kunci", 
    "🛠️ Penjejak PM & Jam Operasi"
])

# ====================================================
# TAB 1: PELAN SUSUN ATUR DARI ATAS (TOP-DOWN VIEW)
# ====================================================
with tab_map:
    st.subheader("🗺️ Pelan Pandangan Atas Mesin (Pilih Zon Kerosakan)")
    st.caption("Gunakan pelan skematik ini untuk mengenal pasti bahagian fizikal mesin yang mengalami gangguan.")

    col_map_sel, col_map_view = st.columns([1, 2])

    with col_map_sel:
        st.markdown("### 1. Pilih Pelan Unit:")
        plan_choice = st.radio(
            "Pelan Sistem:",
            ["Foodtec Loader FL 330 (13 Modul Penuh)", "Omnia FT 330 Grader (Susun Atur Keseluruhan)"]
        )

        if plan_choice == "Foodtec Loader FL 330 (13 Modul Penuh)":
            st.markdown("""
            **Zon Utama Loader FL 330 (Rujuk Nombor Rajah):**
            * **[1 - 3]**: Infeed Belt, Unit Pusingan & Hentian Dulang (*Stack Stop*)
            * **[4]**: Meja Angkat (*Lift Bridge*)
            * **[5]**: *Suction-Gripper Head*
            * **[6]**: Penghantar Plateau (*PT Chain*)
            * **[7]**: Cawan Sedutan (*Suction Head*)
            * **[8]**: Pencengkam Dulang Kosong (*Gripper Head*)
            * **[9]**: Unit Penyingkir Dulang (*Shedder Unit*)
            """)
            
            st.markdown("---")
            st.markdown("### 2. Tindakan Pantas Mengikut Zon:")
            if st.button("🔧 Masalah Suction Head [Zon 7]"):
                st.session_state.target_doc = "FL_Loader_Service.pdf"
                st.session_state.target_page = 112
                st.success("Manual dimuatkan: Ketegangan Toothed Belt Suction Head (m/s 112)")
            if st.button("🔧 Masalah Meja Angkat & Dulang Bertindih [Zon 3-4]"):
                st.session_state.target_doc = "FL_Loader_Service.pdf"
                st.session_state.target_page = 84
                st.success("Manual dimuatkan: Pelarasan Lejang Silinder Stack Stop (m/s 84)")
            if st.button("🔧 Masalah Pencengkam Dulang [Zon 8]"):
                st.session_state.target_doc = "FL_Loader_Service.pdf"
                st.session_state.target_page = 106
                st.success("Manual dimuatkan: Pelarasan Bukaan Gripper 290 mm (m/s 106)")

        else:
            st.markdown("""
            **Zon Utama Omnia FT 330 Grader:**
            * **[1] Infeed / Accumulator**: Penerimaan telur dari ladang/loader.
            * **[2] MultiDrum™ & Infeed**: Jajaran telur & orientasi sebelum penimbang.
            * **[3] Transfer Unit**: Pemindahan telur ke pembawa penimbang.
            * **[4] Frame & Weighing**: Penimbang loadcell & pembawa utama.
            * **[5] Packing Lanes**: Lorong pembungkusan automatik.
            """)
            
            st.markdown("---")
            st.markdown("### 2. Tindakan Pantas Mengikut Zon:")
            if st.button("🔧 Gegaran Infeed & Rantai [Zon 2]"):
                st.session_state.target_doc = "Omnia_FT_Service.pdf"
                st.session_state.target_page = 61
                st.success("Manual dimuatkan: Penyelesaian Rantai Shaking & Spring 110 mm (m/s 61)")
            if st.button("🔧 Penimbang Loadcell Ralat [Zon 4]"):
                st.session_state.target_doc = "Omnia_FT_Service.pdf"
                st.session_state.target_page = 105
                st.success("Manual dimuatkan: Prosedur Kalibrasi Penimbang CarWgPc (m/s 105)")

    with col_map_view:
        # Papar gambar pelan skematik terus dari manual
        if plan_choice == "Foodtec Loader FL 330 (13 Modul Penuh)":
            st.markdown("#### 📐 Rajah Pelan Atas Berwarna: Foodtec Loader FL 330 (M/S 57)")
            img, _ = get_pdf_page_image("FL_Loader_Service.pdf", 57)
            if img:
                st.image(img, use_container_width=True)
        else:
            st.markdown("#### 📐 Rajah Pelan Atas: Omnia FT Grader & Packing Lanes (M/S 188)")
            img, _ = get_pdf_page_image("Omnia_FT_Service.pdf", 188)
            if img:
                st.image(img, use_container_width=True)

# ====================================================
# TAB 2: DIAGNOSTIK KEROSAKAN & RUJUKAN MANUAL
# ====================================================
with tab_diag:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Carian Masalah Kerosakan")
        user_query = st.text_input("Taip kerosakan di lantai kilang (cth: loader, gegar, timbang, belt):")

        matched = []
        q = user_query.lower() if user_query else ""
        for c in TROUBLESHOOTING_DB:
            if q:
                if any(k in q for k in c["keywords"]) or any(w in c["title"].lower() for w in q.split()):
                    matched.append(c)
            else:
                matched.append(c)

        for c in matched:
            with st.expander(f"🔴 {c['title']}", expanded=(len(matched) == 1)):
                st.write(f"**Zon Mesin:** `{c['zone']}`")
                st.write(f"**Simptom:** {c['symptom']}")
                st.write(f"**Punca:** `{c['root_cause']}`")
                st.success(f"**Tindakan:** {c['action']}")
                st.info(f"**Toleransi Standard:** `{c['specs']}`")
                if st.button(f"📖 Buka Manual {c['doc']} (M/S {c['page']})", key=f"btn_diag_{c['id']}"):
                    st.session_state.target_doc = c["doc"]
                    st.session_state.target_page = c["page"]
                    st.rerun()

    with col_right:
        st.subheader("📄 Dokumen Servis Rasmi")
        if st.session_state.target_doc:
            img_bytes, total = get_pdf_page_image(st.session_state.target_doc, st.session_state.target_page)
            if img_bytes:
                st.success(f"Fail: `{st.session_state.target_doc}` | Halaman {st.session_state.target_page} / {total}")
                c_prev, c_next = st.columns(2)
                with c_prev:
                    if st.button("⬅️ Muka Surat Sebelumnya", use_container_width=True):
                        if st.session_state.target_page > 1:
                            st.session_state.target_page -= 1
                            st.rerun()
                with c_next:
                    if st.button("Muka Surat Seterusnya ➡️", use_container_width=True):
                        if st.session_state.target_page < total:
                            st.session_state.target_page += 1
                            st.rerun()
                st.image(img_bytes, use_container_width=True)

# ====================================================
# TAB 3: PARAMETER & TOLERANSI KUNCI
# ====================================================
with tab_specs:
    st.subheader("Jadual Toleransi & Parameter Standard")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🚜 Foodtec Loader FL 330")
        st.table(pd.DataFrame([
            {"Komponen": "Toothed Belt Suction Head", "Nilai": "60 Hz", "Rujukan": "m/s 112"},
            {"Komponen": "Toothed Belt Gripper Head", "Nilai": "46 – 47 Hz", "Rujukan": "m/s 126"},
            {"Komponen": "Tinggi Cawan Suction atas Plateau", "Nilai": "30 – 33 mm", "Rujukan": "m/s 116"},
            {"Komponen": "Bukaan Grippers Dulang", "Nilai": "290 mm", "Rujukan": "m/s 106"},
            {"Komponen": "Tekanan Udara Minima", "Nilai": "4.0 bar (Trip) / 5.0 bar", "Rujukan": "m/s 151"}
        ]))
    with col2:
        st.markdown("#### 🥚 Omnia FT 330 Grader")
        st.table(pd.DataFrame([
            {"Komponen": "Spring MultiDrum™ FT 330", "Nilai": "110 mm (Min: 100 mm)", "Rujukan": "m/s 58"},
            {"Komponen": "Kelegaan Double Roll Infeed", "Nilai": "0.5 – 1.0 mm", "Rujukan": "m/s 61"},
            {"Komponen": "Jarak Penderia Logam Keluli", "Nilai": "2.0 mm", "Rujukan": "m/s 35"},
            {"Komponen": "Jarak Sensor Loadcell 0", "Nilai": "1.0 mm", "Rujukan": "m/s 104"},
            {"Komponen": "Pemberat Kalibrasi Pembawa", "Nilai": "63 gram (Art. 80206980)", "Rujukan": "m/s 107"}
        ]))

# ====================================================
# TAB 4: PENJEJAK PM & JAM OPERASI
# ====================================================
with tab_pm:
    st.subheader("Penjejak Kitaran Hayat & Jadual PM")
    hrs = st.number_input("Masukkan Jam Operasi Terkini:", min_value=0, value=2400, step=100)
    uv_used = hrs % 9000
    st.write(f"**Lampu UV-C Philips TUV PL-L 55W:** {uv_used} / 9,000 Jam Operasi")
    st.progress(min(uv_used / 9000.0, 1.0))
    if uv_used >= 8500:
        st.error("🚨 Sediakan tiub gantian: Philips TUV PL-L 55W/4P HF (Kod: 927908704007).")
    else:
        st.success("✅ Intensiti tiub UV-C dalam keadaan baik.")
