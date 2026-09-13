import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import os
import re

st.set_page_config(
    page_title="MOBA FT 330 & FL 330 Maintenance Assistant",
    page_icon="⚙️",
    layout="wide"
)

# ----------------------------------------------------
# 1. INISIALISASI MEMORI SESSION STATE
# ----------------------------------------------------
if "target_doc" not in st.session_state:
    st.session_state.target_doc = "FL_Loader_Service.pdf"
if "target_page" not in st.session_state:
    st.session_state.target_page = 112

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
# 2. PANGKALAN DATA DIAGNOSTIK KEJURUTERAAN (TROUBLESHOOTING MATRIX)
# ----------------------------------------------------
TROUBLESHOOTING_DB = [
    {
        "id": "loader_vacuum_loss",
        "category": "Loader FL 330",
        "title": "Loader: Telur Jatuh / Cawan Sedutan Hilang Vakum",
        "doc": "FL_Loader_Service.pdf",
        "page": 157,
        "keywords": ["sedut", "vacuum", "vakum", "suction", "drop", "jatuh", "tak sedut", "loader tak berfungsi", "pecah"],
        "symptom": "Cawan sedutan (suction cups) gagal mengangkat telur daripada dulang atau telur terlepas semasa pemindahan ke infeed.",
        "root_cause": "Injap blow-back bocor/tersumbat, pemasaan piring lengkung (curve disk) lari, atau tekanan udara sistem bawah had minimum.",
        "investigation": [
            "1. Periksa tolok tekanan pneumatik manifold: Tekanan mesti sekurang-kurangnya 5 bar untuk mula, 6 bar semasa operasi.",
            "2. Periksa cawan sedutan: Pastikan tiada rekahan getah dan cuci hanya dengan air bersih suhu bilik (<30°C).",
            "3. Periksa injap 'blow-back': Pastikan injap ditekan rapat ke dudukannya oleh tekanan spring semasa fasa sedutan."
        ],
        "action": "Laraskan pemasaan vakum menggunakan pin pelaras 15 mm melalui piring lengkung (curve disk) dan perisai kerangka. Buka muka surat 157 untuk rajah skru pelaras.",
        "specs": "Tekanan Min: 5.0 bar | Ketinggian Suction Cup atas Plateau: 30 - 33 mm"
    },
    {
        "id": "loader_belt_timing",
        "category": "Loader FL 330",
        "title": "Loader: Timing Lari / Tali Sawat Bunyi / Tersentak",
        "doc": "FL_Loader_Service.pdf",
        "page": 112,
        "keywords": ["timing", "belt", "tali sawat", "toothed", "gegar", "bunyi", "singkron", "tersentak", "frekuensi"],
        "symptom": "Pergerakan Suction Head atau Gripper Head tersentak, bunyi ketukan tali sawat, atau telur tidak mendarat tepat pada roller.",
        "root_cause": "Ketegangan tali sawat bergerigi (toothed belt) kendur atau terkeluar daripada frekuensi akustik standard.",
        "investigation": [
            "1. Periksa sama ada tali sawat baru ditukar (Tali sawat baru WAJIB ditegangkan semula selepas 2 jam operasi pertama).",
            "2. Pastikan pin pelaras 15 mm boleh masuk lancar ke dalam lubang jajaran kerangka sebelum talaan dibuat."
        ],
        "action": "Gunakan meter frekuensi akustik. Longgarkan nat kunci dan putar bolt pelaras sehingga frekuensi getaran tali sawat mencapai nilai standard.",
        "specs": "Suction Head Belt: 60 Hz | Gripper Head Belt: 46 - 47 Hz | Suction-Gripper: 55 - 60 Hz"
    },
    {
        "id": "loader_gripper_crash",
        "category": "Loader FL 330",
        "title": "Loader: Pencengkam (Gripper) Langgar Dulang / Tak Sentral",
        "doc": "FL_Loader_Service.pdf",
        "page": 106,
        "keywords": ["gripper", "pencengkam", "dulang", "tray", "sangkut", "langgar", "bengkok", "tak lepas"],
        "symptom": "Pencengkam dulang berlanggar dengan bucu tray plastik/kertas atau gagal memegang dulang kosong dengan kemas ke bahagian shedder.",
        "root_cause": "Jarak bukaan rod silinder lari atau kedudukan penderia resolver motor PT teranjak.",
        "investigation": [
            "1. Tolak rod silinder keluar sepenuhnya secara manual.",
            "2. Ukur jarak antara kedua-dua hujung pencengkam."
        ],
        "action": "Longgarkan nat pengunci pada rod silinder. Laraskan kepala rod (rod head) sehingga bukaan tepat 290 mm. Rujuk Bab 8.7.8 muka surat 106.",
        "specs": "Bukaan Gripper Standard: Tepat 290 mm | Spring Kompresi: 5.3 darjah (~30 mm)"
    },
    {
        "id": "loader_stack_stop_jam",
        "category": "Loader FL 330",
        "title": "Loader: Dulang Bertindih / Stack Stop Meja Angkat Jamming",
        "doc": "FL_Loader_Service.pdf",
        "page": 84,
        "keywords": ["stack", "stop", "meja angkat", "lift", "bertindih", "dulang jam", "jamming", "transfer"],
        "symptom": "Timbunan dulang telur terbalik, tersangkut semasa masuk ke meja angkat (lift bridge), atau hentian dulang mengeluarkan bunyi bising.",
        "root_cause": "Lejang silinder stack stop tidak tepat 90 darjah terhadap tali sawat, atau penampan getah telah haus.",
        "investigation": [
            "1. Periksa sama ada flap hentian berada tepat pada sudut 90 darjah terhadap tali sawat apabila silinder ditarik masuk penuh.",
            "2. Pastikan penampan getah tidak menahan pergerakan lejang penuh."
        ],
        "action": "Laraskan kepala rod silinder sehingga flap tepat berserenjang. Laraskan penampan getah sehingga menyentuh flap kemudian tambah separuh putaran. Rujuk muka surat 84.",
        "specs": "Lejang Meja Angkat Maksimum: 260 mm | Jarak Pusat Lift-Transfer: 140 mm"
    },
    {
        "id": "infeed_shaking",
        "category": "Infeed FT 330",
        "title": "Infeed: Rantai Bergerak Kasar / Gegaran Infeed / MultiDrum Trip",
        "doc": "Omnia_FT_Service.pdf",
        "page": 61,
        "keywords": ["infeed", "gegar", "shaking", "rantai", "vibrate", "lompat", "drum trip", "emergency", "infeed gegar"],
        "symptom": "Rantai Double Roll bergetar kuat, telur melompat keluar dari poket roller, atau suis keselamatan MultiDrum kerap mencetuskan Emergency Stop.",
        "root_cause": "Spring penegang keselamatan MultiDrum kendur, rel sokongan rantai kembali terlalu rendah, atau kelegaan roller terlalu ketat.",
        "investigation": [
            "1. Ukur panjang spring keselamatan MultiDrum di kedua-dua belah.",
            "2. Periksa kelegaan sisi (play) setiap roller pada seksyen masukan dan crack detector."
        ],
        "action": "Tala panjang spring keselamatan MultiDrum kepada 110 mm (boleh dikurangkan ke 100 mm jika kerap trip). Tinggikan rel sokongan rantai kembali Double Roll setinggi mungkin tanpa rantai melompat. Rujuk Bab 6.3.7 muka surat 61.",
        "specs": "Spring MultiDrum FT 330: 110 mm (Min: 100 mm) | Kelegaan Roller: 0.5 - 1.0 mm"
    },
    {
        "id": "infeed_multidrum_sync",
        "category": "Infeed FT 330",
        "title": "Infeed: MultiDrum™ Tak Singkron / Telur Pecah Masuk Drum",
        "doc": "Omnia_FT_Service.pdf",
        "page": 74,
        "keywords": ["multidrum", "drum", "carrier", "tak singkron", "sync", "telur pecah", "infeed side", "outfeed side"],
        "symptom": "Pembawa (carrier) MultiDrum tidak menyambut telur tepat pada roller infeed, mengakibatkan telur terhempas atau retak.",
        "root_cause": "Bolt gegancu (sprocket wheel) drum longgar atau jajaran aci drum terpusing (twisted).",
        "investigation": [
            "1. Tanggalkan 3 set carrier untuk mendedahkan dua aci drum.",
            "2. Letakkan tolok aras air (spirit level) pada kedua-dua aci untuk memastikan ia rata."
        ],
        "action": "Longgarkan bolt gear rantai. Laraskan jarak roller pertama Double Roll kepada tepat 360 mm dari aci MultiDrum pada bahagian infeed. Rujuk Bab 7.3.2 muka surat 74.",
        "specs": "Jarak Roller Infeed ke Aci Drum: Tepat 360 mm (Double Roll) / 364 mm (Single Roll)"
    },
    {
        "id": "loader_infeed_sync",
        "category": "Sinkronisasi Mesin",
        "title": "Sinkronisasi: Telur Mendarat Atas Roller (Bukan Antara Roller)",
        "doc": "Omnia_FT_Service.pdf",
        "page": 112,
        "keywords": ["singkron", "synchronisation", "mendarat", "roller", "landing", "pecah", "synchrobox", "transfer"],
        "symptom": "Cawan sedutan Loader melepaskan telur tepat di atas puncak roller, menyebabkan telur bergolek ganas atau pecah.",
        "root_cause": "Anjakan fasa (phase shift) antara motor Loader dan motor Infeed Grader pada unit Synchrobox MA19.",
        "investigation": [
            "1. Periksa lampu LED pada kad Synchro Control MA19 di kabinet Loader.",
            "2. Perhatikan kedudukan piring pelaras synchro pada Transfer unit."
        ],
        "action": "Longgarkan tombol pengunci piring synchro pada Transfer unit. Jika pelepasan terlalu awal, putar piring mengikut arah panah. Jika terlalu lewat, putar lawan arah panah (1 lubang = pergerakan 1 mm). Rujuk muka surat 112.",
        "specs": "Pergerakan 1 Lubang Piring Synchro = 1.0 mm Posisi Pelepasan Telur"
    },
    {
        "id": "weighing_loadcell_error",
        "category": "Penimbang Omnia",
        "title": "Penimbang: Bacaan Gram Telur Lari / Kalibrasi Loadcell Gagal",
        "doc": "Omnia_FT_Service.pdf",
        "page": 105,
        "keywords": ["timbang", "weighing", "loadcell", "berat", "gram", "lari", "carwgpc", "calibration", "kalibrasi"],
        "symptom": "Gred berat telur tidak tepat, peratusan telur off-grade tinggi, atau paparan 'PrEr' pada sistem kawalan.",
        "root_cause": "Sisa cecair telur mengering pada loadcell, pembawa bengkok, atau piring pemasaan (Main Timing Disk) lari.",
        "investigation": [
            "1. Tiup habuk dan sisa kotoran pada loadcell menggunakan udara termampat kering.",
            "2. Periksa jarak penderia pembawa loadcell 0 (Loadcell-carrier 0) menggunakan feeler gauge (mesti 1.0 mm)."
        ],
        "action": "Lancarkan perisian 'CarWgPc.exe' dari ServerPC. Jalankan 'Empty Carrier Calibration' (10 kitaran). Seterusnya kalibrasi pembawa menggunakan pemberat kalibrasi plastik MOBA 63 gram (Art. 80206980). Rujuk muka surat 105.",
        "specs": "Pemberat Kalibrasi Pembawa: 63 gram | Pemberat Ujian Statik: 130 gram | Jarak Sensor: 1 mm"
    },
    {
        "id": "uv_sanitizer_life",
        "category": "Sanitasi Infeed",
        "title": "UV-C Infeed: Tiub Lampu Malap / Amaran Tamat Hayat",
        "doc": "Philips_UV_Specs.pdf",
        "page": 1,
        "keywords": ["uv", "lampu", "disinfection", "kuman", "philips", "pl-l 55w", "sanitasi"],
        "symptom": "Lampu UV-C tidak menyala, berkelip-kelip, atau jam operasi mesin melebihi had hayat berkesan tiub.",
        "root_cause": "Tiub lampu telah mencapai had degradasi radiasi 15% selepas 9,000 jam operasi atau ballast elektronik rosak.",
        "investigation": [
            "1. Semak rekod jam operasi penjejak PM mesin.",
            "2. Pastikan suis keselamatan penutup UV mematikan litar secara automatik semasa dibuka."
        ],
        "action": "Gantikan dengan tiub rasmi: Philips TUV PL-L 55W/4P HF 1CT/25 (Pangkalan 2G11 4-Pin, Kod 927908704007). Pastikan LOTO dipatuhi dan elakkan sentuhan langsung dengan mata/kulit.",
        "specs": "Kuasa: 55 W | Radiasi UV-C: 17.0 W | Had Hayat: Tepat 9,000 Jam Operasi"
    }
]

# ----------------------------------------------------
# 3. SUSUN ATUR ANTARAMUKA STREAMLIT
# ----------------------------------------------------
tab_diag, tab_specs, tab_pm = st.tabs([
    "🔍 Diagnostik & Rujukan Dokumen Asal", 
    "📏 Parameter & Toleransi Kunci (Cheat Sheet)", 
    "🛠️ Penjejak PM & Jam Operasi"
])

# ====================================================
# TAB 1: DIAGNOSTIK & SEMAKAN MANUAL ASAL
# ====================================================
with tab_diag:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("1. Huraikan Simptom Kerosakan Mesin")
        user_query = st.text_input(
            "Taip masalah di lantai kilang (cth: loader tak sedut telur, infeed bergegar, timing belt kendur):",
            placeholder="Taip apa-apa simptom di sini..."
        )

        st.subheader("2. Atau Tapis Mengikut Bahagian Mesin")
        category_filter = st.selectbox(
            "Pilih sub-sistem berkaitan:",
            ["Semua Bahagian", "Loader FL 330", "Infeed FT 330", "Sinkronisasi Mesin", "Penimbang Omnia", "Sanitasi UV-C"]
        )

        # Penapis Carian
        matched_cases = []
        clean_query = user_query.lower() if user_query else ""

        for case in TROUBLESHOOTING_DB:
            # Tapis kategori
            if category_filter != "Semua Bahagian" and case["category"] != category_filter:
                continue
            
            # Padanan kata kunci
            if clean_query:
                # Padankan jika mana-mana kata kunci sepadan
                if any(k in clean_query for k in case["keywords"]) or any(word in case["title"].lower() for word in clean_query.split()):
                    matched_cases.append(case)
            else:
                matched_cases.append(case)

        st.markdown(f"**Ditemui {len(matched_cases)} Panduan Penyelesaian:**")
        st.markdown("---")

        if matched_cases:
            for c in matched_cases:
                with st.expander(f"🔴 {c['title']}", expanded=(len(matched_cases) == 1)):
                    st.markdown(f"**⚠️ Simptom:** {c['symptom']}")
                    st.markdown(f"**🔍 Punca Sebenar:** `{c['root_cause']}`")
                    st.markdown("**📋 Langkah Siasatan (Troubleshooting):**")
                    for inv in c["investigation"]:
                        st.write(inv)
                    st.success(f"**🛠️ Tindakan Pembaikan:** {c['action']}")
                    st.info(f"**📐 Nilai Toleransi Standard:** `{c['specs']}`")
                    
                    # Butang Buka Muka Surat Manual Asal
                    btn_label = f"📖 Buka Rajah Manual: {c['doc']} (Muka Surat {c['page']})"
                    if st.button(btn_label, key=f"btn_{c['id']}"):
                        st.session_state.target_doc = c["doc"]
                        st.session_state.target_page = c["page"]
                        st.rerun()
        else:
            st.warning("Tiada padanan masalah ditemui bagi carian anda.")
            st.info("Cuba gunakan kata kunci seperti: `sedut`, `vacuum`, `gegar`, `belt`, `timbang`, `dulang`, atau pilih 'Semua Bahagian'.")

    # Kolum Kanan: Paparan Halaman Dokumen Asal
    with col_right:
        st.subheader("📄 Keratan Rajah & Panduan Manual Asal")
        
        if st.session_state.target_doc:
            img_bytes, total = get_pdf_page_image(st.session_state.target_doc, st.session_state.target_page)
            if img_bytes:
                st.success(f"Fail: `{st.session_state.target_doc}` | Halaman {st.session_state.target_page} daripada {total}")
                
                # Butang Kawalan Muka Surat (Next / Prev)
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

                # Papar imej rajah skematik manual
                st.image(img_bytes, use_container_width=True)
            else:
                st.error(f"Gagal memuatkan fail '{st.session_state.target_doc}'. Pastikan fail PDF berada di root folder GitHub.")
        else:
            st.info("Pilih mana-mana masalah di sebelah kiri dan klik butang 'Buka Rajah Manual' untuk melihat dokumen teknikal asal.")

# ====================================================
# TAB 2: PARAMETER & TOLERANSI KUNCI (CHEAT SHEET)
# ====================================================
with tab_specs:
    st.subheader("Jadual Parameter & Toleransi Standard (Rujukan Poket Juruteknik)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🚜 Foodtec Loader FL 330")
        st.table(pd.DataFrame([
            {"Komponen": "Toothed Belt Suction Head", "Nilai Standard": "60 Hz", "Rujukan": "Bab 8.9.1 (m/s 112)"},
            {"Komponen": "Toothed Belt Gripper Head", "Nilai Standard": "46 – 47 Hz", "Rujukan": "Bab 8.10.4 (m/s 126)"},
            {"Komponen": "Toothed Belt Suction-Gripper", "Nilai Standard": "55 – 60 Hz", "Rujukan": "Bab 8.7.4 (m/s 101)"},
            {"Komponen": "Ketinggian Suction Cup atas Tray", "Nilai Standard": "30 – 33 mm", "Rujukan": "Bab 8.9.4 (m/s 116)"},
            {"Komponen": "Jarak Bukaan Grippers", "Nilai Standard": "290 mm", "Rujukan": "Bab 8.7.8 (m/s 106)"},
            {"Komponen": "Tekanan Udara Minimum (Trip)", "Nilai Standard": "4.0 bar (Trip) / 5.0 bar (Start)", "Rujukan": "Bab 8.13 (m/s 151)"},
            {"Komponen": "Lejang Meja Angkat (Lift Stroke)", "Nilai Standard": "260 mm (Maksimum)", "Rujukan": "Bab 8.6.6 (m/s 91)"}
        ]))
    with col2:
        st.markdown("#### 🥚 Omnia FT 330 Grader & Infeed")
        st.table(pd.DataFrame([
            {"Komponen": "Spring MultiDrum™ FT 330", "Nilai Standard": "110 mm (Min: 100 mm)", "Rujukan": "Bab 6.3.4 (m/s 58)"},
            {"Komponen": "Kelegaan Double Roll & Crack Section", "Nilai Standard": "0.5 – 1.0 mm", "Rujukan": "Bab 6.3.7 (m/s 61)"},
            {"Komponen": "Jarak Sensor Induktif (Steel)", "Nilai Standard": "2.0 mm", "Rujukan": "Bab 4.2 (m/s 35)"},
            {"Komponen": "Jarak Sensor Induktif (Stainless)", "Nilai Standard": "1.0 mm", "Rujukan": "Bab 4.2 (m/s 35)"},
            {"Komponen": "Jarak Sensor Loadcell-Carrier 0", "Nilai Standard": "1.0 mm", "Rujukan": "Bab 9.6 (m/s 104)"},
            {"Komponen": "Pemberat Kalibrasi Pembawa (Carrier)", "Nilai Standard": "63 gram (Art. 80206980)", "Rujukan": "Bab 9.7.3 (m/s 107)"},
            {"Komponen": "Pemberat Ujian Loadcell", "Nilai Standard": "130 gram", "Rujukan": "Bab 9.7.5 (m/s 109)"}
        ]))

# ====================================================
# TAB 3: PENJEJAK PM & JAM OPERASI
# ====================================================
with tab_pm:
    st.subheader("Penjejak Kitaran Hayat & Jadual Servis Berkala (PM)")
    hrs = st.number_input("Masukkan Jumlah Jam Operasi Mesin Terkini:", min_value=0, value=2400, step=100)

    st.markdown("#### 💡 Status Tiub Lampu UV-C Infeed (Philips TUV PL-L 55W)")
    uv_used = hrs % 9000
    st.write(f"Jam Terpakai: **{uv_used} / 9,000 Jam Operasi**")
    st.progress(min(uv_used / 9000.0, 1.0))
    if uv_used >= 8500:
        st.error("🚨 AMARAN: Lampu UV-C sudah melebihi 8,500 jam! Kadar nyahkuman merosot >15%. Sediakan tiub Philips 55W 2G11 gantian.")
    else:
        st.success("✅ Keadaan radiasi kuman UV-C memuaskan.")

    st.markdown("---")
    st.markdown("#### 📋 Senarai Semak Servis Berdasarkan Jam Operasi:")
    st.write("• **Setiap 8 Jam (Harian):** Bersihkan sisa cecair telur pada poket dan cuci pemantul sensor optik.")
    st.write("• **Setiap 40 Jam (Mingguan):** Buang kulit telur dan bulu ayam di kawasan dropset. Cuci penapis minyak EggInspector.")
    st.write("• **Setiap 200 Jam (Bulanan):** Minyakkan rantai infeed (Shell T 46) dan cuci penapis air semburan.")
    st.write("• **Setiap 1,200 Jam (6 Bulan):** Semak ketegangan tali sawat toothed belt (Hz) dan rantai pemacu.")
    st.write("• **Setiap 2,400 Jam (Tahunan):** Gantikan penapis udara dan uji semua litar Emergency Stop & suis pintu interlock.")
