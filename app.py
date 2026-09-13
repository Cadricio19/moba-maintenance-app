import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import os
import re

st.set_page_config(
    page_title="MOBA FT 330 & FL 330 Expert Maintenance System",
    page_icon="⚙️",
    layout="wide"
)

# ----------------------------------------------------
# 1. MEMORI STATE & FUNGSI RENDER PDF
# ----------------------------------------------------
if "target_doc" not in st.session_state:
    st.session_state.target_doc = "Omnia_FT_Service.pdf"
if "target_page" not in st.session_state:
    st.session_state.target_page = 156

def get_pdf_page_image(pdf_path, page_num):
    if os.path.exists(pdf_path):
        try:
            doc = fitz.open(pdf_path)
            actual_page = max(1, min(page_num, len(doc)))
            page = doc[actual_page - 1]
            pix = page.get_pixmap(dpi=150)
            return pix.tobytes("png"), len(doc)
        except Exception as e:
            st.error(f"Ralat memproses fail PDF: {e}")
            return None, 0
    return None, 0

# ----------------------------------------------------
# 2. PANGKALAN DATA DIAGNOSTIK KESELURUHAN SISTEM
# ----------------------------------------------------
TROUBLESHOOTING_DB = [
    # --- PACKING LANE & BUFFER CONVEYOR ---
    {
        "id": "packing_lane_pusher_chain",
        "category": "Packing Lane & Buffer",
        "zone": "Packing Lane: Pusher Chain & Penegang",
        "title": "Packing Lane: Rantai Bawah Bufferset Bergegar / Melambung (Flapping)",
        "doc": "Omnia_FT_Service.pdf",
        "page": 156,
        "keywords": ["bufferset", "buffer", "packing lane", "pusher", "pusher chain", "rantai bergegar", "rantai flapping", "spring tensioner", "rantai bawah", "dropset", "bawah buffer"],
        "symptom": "Rantai penolak (pusher chain) di bawah kawasan bufferset/dropset melambung, bergetar kasar semasa membawa dulang, atau kendur melepasi had.",
        "root_cause": "Unit penegang spring (spring-tensioner) rantai penolak melepasi tanda penunjuk had (mark 6), menyebabkan rantai kendur dan melantun.",
        "investigation": [
            "1. Semak kedudukan penegang spring rantai penolak di sebelah infeed packing conveyor.",
            "2. Perhatikan sama ada penegang berdiri di atas garisan tanda (mark 6).",
            "3. Pastikan rantai penolak tidak tersangkut pada loop wheels."
        ],
        "action": "1. Longgarkan bolt (3) pada plat had (limit-plate).\n2. Alihkan gear wheel (2) pada bahagian infeed packing conveyor ke bawah sebanyak 1 lubang sehingga penegang berada di bawah tanda.\n3. Pasang semula plat had pada jarak tepat 1 mm di bawah jalur penegang.\n4. Rujuk Bab 11.5.3 (m/s 156).",
        "specs": "Kelegaan Plat Had Penegang: 1.0 mm | Semakan Ketegangan: Setiap 400 jam operasi"
    },
    {
        "id": "packing_lane_planetary_gear",
        "category": "Packing Lane & Buffer",
        "zone": "Packing Lane: Transmisi Buffer",
        "title": "Packing Lane: Buffer Conveyor Tersentak / Gear Planetari Out-of-Sync",
        "doc": "Omnia_FT_Service.pdf",
        "page": 151,
        "keywords": ["planetary", "gear", "gearwheel", "buffer timing", "buffer conveyor", "sentak", "planetary gearwheel", "transmisi buffer"],
        "symptom": "Pergerakan rantai buffer tidak seragam, menghasilkan sentakan mekanikal berkala, atau telur tidak masuk tepat pada dropset.",
        "root_cause": "Penanda jajaran (markers) pada sprocket 56-gigi atau gear ring lari dari kedudukan alur kunci (key-way).",
        "investigation": [
            "1. Periksa 4 unit gearwheel dalam blok buffer berkaitan.",
            "2. Pastikan penanda jajaran (markers) pada gear selari dengan alur kunci (key-way)."
        ],
        "action": "Buka pemasangan gear planetari mengikut urutan Bab 11.4.5. Pasang semula dengan menjajarkan penanda pada gear 56-gigi dan gelang gear mengikut Rajah 177 (m/s 152).",
        "specs": "Komponen Transmisi: Sprocket 40T, lima unit 14T, satu unit 56T, dan Gear Ring"
    },
    {
        "id": "packing_lane_receiver_delay",
        "category": "Packing Lane & Buffer",
        "zone": "Packing Lane: Receiver Unit & Dropset",
        "title": "Packing Lane: Telur Pecah / Tak Masuk Tengah Kaki Buffer",
        "doc": "Omnia_FT_Service.pdf",
        "page": 146,
        "keywords": ["receiver", "delay", "tundaan", "dropset", "telur pecah packing", "timing buffer", "kaki buffer"],
        "symptom": "Telur dilepaskan dari carrier frame tetapi terhempas pada bucu kaki buffer atau jatuh senget ke dalam dulang.",
        "root_cause": "Kelegaan kaki receiver telah haus atau nilai masa tundaan (receiver unit time delay) dalam perisian MMI tidak tepat.",
        "investigation": [
            "1. Letakkan telur pelaras kecil (small adjustment egg) pada receiver unit.",
            "2. Ukur dimensi jarak jatuhan (dimensi 1 pada Rajah 168)."
        ],
        "action": "Dalam perisian MMI: Masuk ke Settings -> Login as Service -> Machine Settings -> Laneset -> Tab 2. Masukkan nilai milisaat (ms) berpandukan Jadual 6 (0mm = 290ms, 5mm = 295ms, 10mm = 300ms).",
        "specs": "Tundaan Perisian: 290 - 300 ms | Ketinggian Saluran Dropset: 163 mm"
    },
    {
        "id": "packing_lane_denester_jam",
        "category": "Packing Lane & Buffer",
        "zone": "Packing Lane: Denester",
        "title": "Denester: Bekas / Dulang Telur Tersangkut (Jamming)",
        "doc": "Omnia_FT_Service.pdf",
        "page": 134,
        "keywords": ["denester", "tray sangkut", "karton jam", "kotak tak turun", "pin conveyor", "pawl", "command pawl"],
        "symptom": "Dulang atau karton tidak jatuh ke pin conveyor, penggera bekalan bungkusan trip, atau dulang rosak dikepit.",
        "root_cause": "Ketinggian plateau lari, panduan tali sawat (belt guides) terlalu sempit, atau command pawl sangkut pada sesondol.",
        "investigation": [
            "1. Periksa ketinggian pemegang bungkusan (package-holders) berbanding permukaan atas plateau (mesti 60 mm).",
            "2. Semak jarak panduan tali sawat kod J (mesti tepat 130 mm)."
        ],
        "action": "1. Laraskan ketinggian plateau supaya plat atas berada 60 mm di bawah pemegang (m/s 135).\n2. Tetapkan jarak belt guide pada 130 mm (Kod J = 10).\n3. Laraskan spring retainer command pawl kepada 5 mm (m/s 137).",
        "specs": "Tinggi Plateau: 60 mm | Jarak Belt Guides (J=10): 130 mm | Kelegaan Pawl: 1.0 mm"
    },

    # --- LOADER FL 330 ---
    {
        "id": "loader_vacuum_loss",
        "category": "Loader FL 330",
        "zone": "Loader: Suction Head & Vakum",
        "title": "Loader: Telur Jatuh / Cawan Sedutan Hilang Vakum",
        "doc": "FL_Loader_Service.pdf",
        "page": 157,
        "keywords": ["sedut", "vacuum", "vakum", "suction", "drop", "jatuh", "tak sedut", "loader tak berfungsi", "suction cup"],
        "symptom": "Cawan sedutan gagal mengangkat telur daripada dulang atau telur terlepas semasa pemindahan ke infeed.",
        "root_cause": "Injap blow-back bocor/tersumbat, pemasaan piring lengkung lari, atau tekanan udara sistem bawah 5 bar.",
        "investigation": [
            "1. Periksa tolok tekanan pneumatik manifold (mesti min 5 bar untuk mula, 6 bar operasi).",
            "2. Pastikan injap blow-back ditekan rapat ke dudukannya semasa fasa sedutan.",
            "3. Cuci cawan getah hanya dengan air bersih suhu bilik (<30°C)."
        ],
        "action": "Laraskan pemasaan vakum menggunakan pin pelaras 15 mm melalui piring lengkung (curve disk). Buka muka surat 157 untuk talaan lejang injap blow-back.",
        "specs": "Tekanan Min: 5.0 bar | Tinggi Cawan atas Plateau: 30 - 33 mm"
    },
    {
        "id": "loader_belt_timing",
        "category": "Loader FL 330",
        "zone": "Loader: Drive Mechanism",
        "title": "Loader: Timing Lari / Tali Sawat Bunyi / Tersentak",
        "doc": "FL_Loader_Service.pdf",
        "page": 112,
        "keywords": ["timing loader", "belt loader", "tali sawat loader", "toothed belt", "frekuensi belt", "suction head belt"],
        "symptom": "Pergerakan Suction Head atau Gripper Head tersentak, bunyi ketukan tali sawat, atau kedudukan cawan sedutan lari.",
        "root_cause": "Ketegangan tali sawat toothed belt kendur atau terkeluar daripada julat frekuensi akustik standard.",
        "investigation": [
            "1. Periksa sama ada tali sawat baru ditukar (Wajib tegangkan semula selepas 2 jam operasi pertama).",
            "2. Pasang pin pelaras 15 mm untuk mengunci jajaran aci sebelum talaan."
        ],
        "action": "Gunakan meter frekuensi akustik. Putar bolt pelaras sehingga frekuensi mencapai nilai standard: Suction Head = 60 Hz, Gripper Head = 46-47 Hz. Rujuk m/s 112.",
        "specs": "Suction Head: Tepat 60 Hz | Gripper Head: 46 - 47 Hz | Suction-Gripper: 55 - 60 Hz"
    },
    {
        "id": "loader_stack_stop_jam",
        "category": "Loader FL 330",
        "zone": "Loader: Infeed & Lift",
        "title": "Loader: Dulang Bertindih / Stack Stop Meja Angkat Jamming",
        "doc": "FL_Loader_Service.pdf",
        "page": 84,
        "keywords": ["stack stop", "stack", "stop", "meja angkat", "lift bridge", "dulang jam", "dulang bertindih", "silinder loader"],
        "symptom": "Timbunan dulang telur tersangkut semasa masuk ke meja angkat (lift bridge) atau hentian dulang bising.",
        "root_cause": "Lejang silinder stack stop tidak berserenjang 90 darjah terhadap tali sawat atau getah penampan haus.",
        "investigation": [
            "1. Periksa kedudukan flap hentian: mesti tepat 90 darjah terhadap tali sawat apabila silinder ditarik masuk penuh.",
            "2. Pastikan penampan getah menyentuh flap."
        ],
        "action": "Laraskan kepala rod silinder sehingga flap tepat berserenjang. Laraskan penampan getah sehingga menyentuh flap kemudian tambah separuh putaran. Rujuk muka surat 84.",
        "specs": "Lejang Meja Angkat: Maks 260 mm | Jarak Pusat Lift-Transfer: 140 mm"
    },
    {
        "id": "loader_gripper_crash",
        "category": "Loader FL 330",
        "zone": "Loader: Gripper Head",
        "title": "Loader: Pencengkam (Gripper) Langgar Dulang / Tak Sentral",
        "doc": "FL_Loader_Service.pdf",
        "page": 106,
        "keywords": ["gripper", "pencengkam", "dulang gripper", "tray gripper", "gripper bengkok", "gripper tak lepas"],
        "symptom": "Pencengkam dulang berlanggar dengan bucu tray atau gagal memegang dulang kosong ke arah shedder unit.",
        "root_cause": "Jarak bukaan rod silinder pencengkam lari daripada spesifikasi kilang 290 mm.",
        "investigation": [
            "1. Tolak rod silinder keluar sepenuhnya secara manual.",
            "2. Ukur jarak bukaan antara kedua-dua hujung pencengkam."
        ],
        "action": "Longgarkan nat pengunci pada rod silinder. Laraskan rod head sehingga bukaan mencapai tepat 290 mm. Rujuk Bab 8.7.8 (m/s 106).",
        "specs": "Bukaan Standard: Tepat 290 mm | Kompresi Spring: 5.3 darjah (~30 mm)"
    },

    # --- INFEED & GRADER ---
    {
        "id": "infeed_shaking",
        "category": "Infeed FT 330",
        "zone": "Infeed: Double Roll & MultiDrum",
        "title": "Infeed: Rantai Masukan Bergegar Kasar / MultiDrum Trip",
        "doc": "Omnia_FT_Service.pdf",
        "page": 61,
        "keywords": ["infeed gegar", "infeed", "gegar infeed", "shaking", "rantai infeed", "drum trip", "multidrum trip", "double roll gegar"],
        "symptom": "Rantai Double Roll bergetar kuat, telur melompat keluar dari roller, atau suis keselamatan MultiDrum kerap trip Emergency Stop.",
        "root_cause": "Spring keselamatan MultiDrum kendur, rel sokongan rantai kembali terlalu rendah, atau kelegaan roller ketat.",
        "investigation": [
            "1. Ukur panjang spring keselamatan MultiDrum di kedua-dua belah.",
            "2. Periksa kelegaan sisi (play) setiap roller pada seksyen masukan (mesti 0.5 - 1.0 mm)."
        ],
        "action": "Tala panjang spring keselamatan MultiDrum kepada 110 mm (boleh dikurangkan ke 100 mm jika kerap trip). Tinggikan rel sokongan rantai kembali Double Roll setinggi mungkin. Rujuk Bab 6.3.7 (m/s 61).",
        "specs": "Spring MultiDrum FT 330: 110 mm (Min: 100 mm) | Kelegaan Roller: 0.5 - 1.0 mm"
    },
    {
        "id": "infeed_multidrum_sync",
        "category": "Infeed FT 330",
        "zone": "Infeed: MultiDrum",
        "title": "Infeed: MultiDrum™ Tak Singkron / Telur Retak Masuk Drum",
        "doc": "Omnia_FT_Service.pdf",
        "page": 74,
        "keywords": ["multidrum sync", "drum infeed", "carrier drum", "telur pecah infeed", "aci drum", "jajaran drum"],
        "symptom": "Pembawa (carrier) MultiDrum tidak menyambut telur tepat pada roller infeed, menyebabkan telur terhempas.",
        "root_cause": "Bolt gegancu drum longgar atau jajaran aci drum terpusing (twisted).",
        "investigation": [
            "1. Tanggalkan 3 set carrier untuk mendedahkan dua aci drum.",
            "2. Letakkan spirit level pada kedua-dua aci untuk memastikan ia rata."
        ],
        "action": "Longgarkan bolt gear rantai. Laraskan jarak roller pertama Double Roll kepada tepat 360 mm dari aci MultiDrum pada bahagian infeed. Rujuk Bab 7.3.2 (m/s 74).",
        "specs": "Jarak Roller Infeed ke Aci Drum: Tepat 360 mm (Double Roll) / 364 mm (Single Roll)"
    },
    {
        "id": "loader_infeed_sync",
        "category": "Infeed FT 330",
        "zone": "Pemindahan: Loader ke Infeed",
        "title": "Sinkronisasi: Telur Mendarat Atas Puncak Roller (Bukan Poket)",
        "doc": "Omnia_FT_Service.pdf",
        "page": 112,
        "keywords": ["singkron", "synchronisation", "mendarat roller", "synchrobox", "transfer loader infeed", "telur pecah landing"],
        "symptom": "Cawan sedutan Loader melepaskan telur tepat di atas puncak roller, menyebabkan telur terpelanting atau pecah.",
        "root_cause": "Anjakan fasa (phase shift) antara motor Loader dan motor Infeed Grader pada unit Synchrobox MA19.",
        "investigation": [
            "1. Periksa status lampu LED pada kad Synchro Control MA19 di kabinet Loader.",
            "2. Perhatikan kedudukan piring pelaras synchro pada Transfer unit."
        ],
        "action": "Longgarkan tombol pengunci piring synchro pada Transfer unit. Jika pelepasan terlalu awal, putar piring mengikut arah panah. Jika terlalu lewat, putar lawan arah panah (1 lubang = pergerakan 1 mm). Rujuk Bab 9.9.1 (m/s 112).",
        "specs": "Pergerakan 1 Lubang Piring Synchro = Tepat 1.0 mm Posisi Pelepasan Telur"
    },

    # --- WEIGHING & FRAME TIMING ---
    {
        "id": "weighing_loadcell_error",
        "category": "Grader: Weighing & Frame",
        "zone": "Grader: Unit Penimbang Loadcell",
        "title": "Penimbang: Bacaan Gram Telur Lari / Kalibrasi CarWgPc Gagal",
        "doc": "Omnia_FT_Service.pdf",
        "page": 105,
        "keywords": ["loadcell", "timbang", "berat lari", "gram lari", "weighing", "carwgpc", "prer", "prok", "kalibrasi timbang"],
        "symptom": "Gred berat telur tidak tepat, peratusan telur off-grade tinggi, atau paparan ralat 'PrEr' pada ServerPC.",
        "root_cause": "Sisa cecair telur mengering pada loadcell, pembawa bengkok, atau piring pemasaan utama lari.",
        "investigation": [
            "1. Tiup habuk pada loadcell menggunakan udara termampat bersih.",
            "2. Periksa jarak penderia pembawa loadcell 0 menggunakan feeler gauge (mesti 1.0 mm)."
        ],
        "action": "Lancarkan perisian 'CarWgPc.exe'. Jalankan Empty Carrier Calibration (10 kitaran). Seterusnya jalankan Carrier Calibration menggunakan pemberat plastik rasmi MOBA 63 gram (Art. 80206980). Rujuk Bab 9.7 (m/s 105).",
        "specs": "Pemberat Kalibrasi Pembawa: 63 gram | Pemberat Ujian Statik: 130 gram | Jarak Penderia: 1.0 mm"
    },
    {
        "id": "frame_timing_zero_carrier",
        "category": "Grader: Weighing & Frame",
        "zone": "Grader: Frame Timing & Penderia",
        "title": "Kerangka: 0-Carrier Sensor Tak Dikesan / Timing Disk Lari",
        "doc": "Omnia_FT_Service.pdf",
        "page": 124,
        "keywords": ["main timing disk", "0-carrier", "carrier 0", "mps97", "hireszero", "penderia kerangka", "timing frame"],
        "symptom": "Mesin tidak dapat menyegerakkan pembawa rantai utama atau lampu amaran pemasaan berkelip pada papan MPS97.",
        "root_cause": "Kedudukan Main Timing Disk pada aci pemacu infeed teranjak atau penderia magnet 0-carrier rosak/longgar.",
        "investigation": [
            "1. Putar mesin secara manual sehingga LED HIRESZERO menyala pada papan MPS97.",
            "2. Putar rantai pembawa sejauh 41 mm lagi (setengah senggatan)."
        ],
        "action": "Laraskan penderia 0-carrier supaya berada tepat 2.0 mm di atas magnet pembawa 0. Ketatkan bolt Main Timing Disk mengikut arah putaran panah. Rujuk Bab 10.4.4 & 10.4.5 (m/s 124 - 126).",
        "specs": "Jarak Sensor 0-Carrier: 2.0 mm atas magnet | Anjakan Rantai: 41 mm dari HIRESZERO"
    },

    # --- UV-C HYGIENE ---
    {
        "id": "uv_sanitizer_life",
        "category": "Sanitasi Infeed",
        "zone": "Sanitasi: Modul UV-C Infeed",
        "title": "UV-C Infeed: Tiub Lampu Malap / Amaran 9,000 Jam Operasi",
        "doc": "Philips_UV_Specs.pdf",
        "page": 1,
        "keywords": ["uv", "lampu uv", "disinfection", "nyahkuman", "philips", "pl-l 55w", "kuman"],
        "symptom": "Lampu UV-C tidak menyala, berkelip, atau meter jam operasi mesin melebihi had hayat 9,000 jam.",
        "root_cause": "Tiub lampu mencapai had hayat fizikal di mana sinaran radiasi UV-C merosot melebihi 15%.",
        "investigation": [
            "1. Semak rekod jam operasi penjejak PM mesin.",
            "2. Pastikan suis keselamatan pintu UV mematikan litar secara automatik semasa dibuka."
        ],
        "action": "Gantikan dengan tiub rasmi: Philips TUV PL-L 55W/4P HF 1CT/25 (Pangkalan 2G11 4-Pin, Kod Bahagian: 927908704007). Pastikan LOTO dipatuhi.",
        "specs": "Kuasa: 55 W | Radiasi UV-C: 17.0 W | Had Hayat Efektif: Tepat 9,000 Jam Operasi"
    }
]

# ----------------------------------------------------
# 3. ENJIN PEMARKAHAN PADANAN PINTAR (SMART SEARCH ENGINE)
# ----------------------------------------------------
BM_SYNONYMS = {
    "tali sawat": "belt toothed",
    "rantai": "chain",
    "penimbang": "loadcell weighing",
    "pencengkam": "gripper",
    "sedut": "suction vacuum",
    "bergegar": "shaking vibrate",
    "gegar": "shaking vibrate",
    "bawah": "bottom lower",
    "bekas": "tray package"
}

def calculate_match_score(query, case):
    score = 0
    query_clean = query.lower()
    for bm, syn in BM_SYNONYMS.items():
        if bm in query_clean:
            query_clean += f" {syn}"
            
    tokens = [t for t in re.findall(r'\b\w+\b', query_clean) if len(t) > 2]
    if not tokens:
        return 0

    # 1. Pemarkahan padanan kata kunci utama (Keywords)
    for kw in case["keywords"]:
        for token in tokens:
            if token in kw:
                score += 3
            if kw in query_clean:
                score += 5

    # 2. Pemarkahan padanan tajuk & simptom
    for token in tokens:
        if token in case["title"].lower():
            score += 4
        if token in case["symptom"].lower():
            score += 2
        if token in case["zone"].lower():
            score += 3

    return score

# ----------------------------------------------------
# 4. SUSUN ATUR ANTARAMUKA STREAMLIT
# ----------------------------------------------------
tab_map, tab_diag, tab_specs, tab_pm = st.tabs([
    "🗺️ Pelan Susun Atur Mesin (Top-Down)",
    "🔍 Diagnostik Kerosakan & Manual", 
    "📏 Parameter & Toleransi Kunci (Cheat Sheet)", 
    "🛠️ Penjejak PM & Jam Operasi"
])

# ====================================================
# TAB 1: PELAN PANDANGAN ATAS (TOP-DOWN VIEW)
# ====================================================
with tab_map:
    st.subheader("🗺️ Pelan Pandangan Atas Mesin (Pilih Bahagian Fizikal)")
    st.caption("Pilih pelan unit untuk mengenal pasti modul dan memuatkan dokumen rujukan serta-merta.")

    col_map_sel, col_map_view = st.columns([1, 2])

    with col_map_sel:
        st.markdown("### 1. Pilih Pandangan Sistem:")
        plan_choice = st.radio(
            "Pelan Skematik:",
            [
                "Foodtec Loader FL 330 (13 Modul Penuh)", 
                "Omnia FT 330 Grader (Susun Atur Penuh)",
                "Packing Lane & Buffer Conveyor (Bab 11)"
            ]
        )

        st.markdown("---")
        st.markdown("### 2. Pintasan Diagnostik Pantas:")

        if plan_choice == "Packing Lane & Buffer Conveyor (Bab 11)":
            st.markdown("""
            **Komponen Kritikal Packing Lane:**
            * **Pusher Chain & Penegang Spring** (Bab 11.5)
            * **Transmisi Gear Planetari Buffer** (Bab 11.4.5)
            * **Dropset & Receiver Timing** (Bab 11.4.1)
            * **Denester & Pin Conveyor** (Bab 11.1 - 11.2)
            """)
            if st.button("🔧 Rantai Penolak Bawah Bufferset Bergegar"):
                st.session_state.target_doc = "Omnia_FT_Service.pdf"
                st.session_state.target_page = 156
                st.rerun()
            if st.button("🔧 Transmisi Gear Planetari Buffer"):
                st.session_state.target_doc = "Omnia_FT_Service.pdf"
                st.session_state.target_page = 151
                st.rerun()
            if st.button("🔧 Denester Bungkusan Jamming"):
                st.session_state.target_doc = "Omnia_FT_Service.pdf"
                st.session_state.target_page = 134
                st.rerun()

        elif plan_choice == "Foodtec Loader FL 330 (13 Modul Penuh)":
            st.markdown("""
            **Komponen Kritikal Loader FL 330:**
            * **[1 - 3]**: Infeed Belts & Stack Stop
            * **[4]**: Meja Angkat (Lift Bridge)
            * **[7]**: Cawan Sedutan (Suction Head 60 Hz)
            * **[8]**: Pencengkam Dulang (Gripper Head 290 mm)
            """)
            if st.button("🔧 Suction Head Hilang Vakum / Belt Kendur"):
                st.session_state.target_doc = "FL_Loader_Service.pdf"
                st.session_state.target_page = 112
                st.rerun()
            if st.button("🔧 Meja Angkat / Dulang Bertindih Jamming"):
                st.session_state.target_doc = "FL_Loader_Service.pdf"
                st.session_state.target_page = 84
                st.rerun()
            if st.button("🔧 Pencengkam Dulang Langgar Bucu"):
                st.session_state.target_doc = "FL_Loader_Service.pdf"
                st.session_state.target_page = 106
                st.rerun()

        else:
            st.markdown("""
            **Komponen Kritikal Grader FT 330:**
            * **Infeed & MultiDrum™** (Bab 6 & 7)
            * **Synchrobox Pemindahan Telur** (Bab 9.9)
            * **Unit Penimbang Loadcell & CarWgPc** (Bab 9.7)
            * **Frame Timing & 0-Carrier Sensor** (Bab 10.4)
            """)
            if st.button("🔧 Infeed / Double Roll Rantai Bergegar"):
                st.session_state.target_doc = "Omnia_FT_Service.pdf"
                st.session_state.target_page = 61
                st.rerun()
            if st.button("🔧 Telur Mendarat Atas Puncak Roller"):
                st.session_state.target_doc = "Omnia_FT_Service.pdf"
                st.session_state.target_page = 112
                st.rerun()
            if st.button("🔧 Kalibrasi Loadcell / Gram Telur Lari"):
                st.session_state.target_doc = "Omnia_FT_Service.pdf"
                st.session_state.target_page = 105
                st.rerun()

    with col_map_view:
        if plan_choice == "Packing Lane & Buffer Conveyor (Bab 11)":
            st.markdown("#### 📐 Rajah Susun Atur Packing Lane (Omnia FT M/S 133)")
            img, _ = get_pdf_page_image("Omnia_FT_Service.pdf", 133)
            if img:
                st.image(img, use_container_width=True)
        elif plan_choice == "Foodtec Loader FL 330 (13 Modul Penuh)":
            st.markdown("#### 📐 Rajah Pelan Atas 13 Modul: Loader FL 330 (FL M/S 57)")
            img, _ = get_pdf_page_image("FL_Loader_Service.pdf", 57)
            if img:
                st.image(img, use_container_width=True)
        else:
            st.markdown("#### 📐 Rajah Pelan Atas Keseluruhan Grader: Omnia FT (M/S 188)")
            img, _ = get_pdf_page_image("Omnia_FT_Service.pdf", 188)
            if img:
                st.image(img, use_container_width=True)

# ====================================================
# TAB 2: DIAGNOSTIK KEROSAKAN & MANUAL
# ====================================================
with tab_diag:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("1. Carian Masalah Kerosakan (Semantic Search)")
        user_query = st.text_input(
            "Taip aduan juruteknik di lantai kilang:",
            placeholder="cth: chain bergegar bawah bufferset, loader hilang vakum, denester jam"
        )

        st.subheader("2. Tapis Mengikut Kategori Sistem")
        cat_filter = st.selectbox(
            "Pilih Bahagian Mesin:",
            ["Semua Bahagian", "Packing Lane & Buffer", "Loader FL 330", "Infeed FT 330", "Grader: Weighing & Frame", "Sanitasi Infeed"]
        )

        # Enjin Pemilihan & Susunan Berdasarkan Skor
        scored_cases = []
        for case in TROUBLESHOOTING_DB:
            if cat_filter != "Semua Bahagian" and case["category"] != cat_filter:
                continue
            
            if user_query:
                s = calculate_match_score(user_query, case)
                if s > 0:
                    scored_cases.append((s, case))
            else:
                scored_cases.append((1, case))

        # Susun keputusan mengikut markah tertinggi
        scored_cases.sort(key=lambda x: x[0], reverse=True)

        st.markdown(f"**Ditemui {len(scored_cases)} Prosedur Berkaitan:**")
        st.markdown("---")

        if scored_cases:
            for score, c in scored_cases:
                with st.expander(f"🔴 [{c['category']}] {c['title']}", expanded=(len(scored_cases) == 1 or score >= 8)):
                    st.write(f"**Zon Terlibat:** `{c['zone']}`")
                    st.write(f"**Simptom:** {c['symptom']}")
                    st.write(f"**Punca:** `{c['root_cause']}`")
                    st.markdown("**Siasatan Langkah Demi Langkah:**")
                    for step in c["investigation"]:
                        st.write(step)
                    st.success(f"**Tindakan:** {c['action']}")
                    st.info(f"**Nilai Toleransi:** `{c['specs']}`")
                    if st.button(f"📖 Buka Manual {c['doc']} (Muka Surat {c['page']})", key=f"btn_diag_{c['id']}"):
                        st.session_state.target_doc = c["doc"]
                        st.session_state.target_page = c["page"]
                        st.rerun()
        else:
            st.warning("Tiada panduan ditemui bagi kata kunci tersebut.")
            st.info("Cuba gunakan istilah khusus seperti: `bufferset`, `pusher`, `infeed`, `suction`, `loadcell`, `denester`, atau `belt`.")

    with col_right:
        st.subheader("📄 Dokumen Servis Rasmi MOBA")
        if st.session_state.target_doc:
            img_bytes, total = get_pdf_page_image(st.session_state.target_doc, st.session_state.target_page)
            if img_bytes:
                st.success(f"Memaparkan: `{st.session_state.target_doc}` | Muka Surat {st.session_state.target_page} daripada {total}")
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
            else:
                st.error(f"Fail '{st.session_state.target_doc}' tiada di direktori root.")
        else:
            st.info("Pilih masalah di sebelah kiri untuk membuka rajah manual berkaitan di sini.")

# ====================================================
# TAB 3: PARAMETER & TOLERANSI KUNCI (CHEAT SHEET)
# ====================================================
with tab_specs:
    st.subheader("Jadual Toleransi & Parameter Standard (Rujukan Poket)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🚜 Foodtec Loader FL 330")
        st.table(pd.DataFrame([
            {"Komponen": "Toothed Belt Suction Head", "Nilai": "60 Hz", "Rujukan": "Bab 8.9.1 (m/s 112)"},
            {"Komponen": "Toothed Belt Gripper Head", "Nilai": "46 – 47 Hz", "Rujukan": "Bab 8.10.4 (m/s 126)"},
            {"Komponen": "Toothed Belt Suction-Gripper", "Nilai": "55 – 60 Hz", "Rujukan": "Bab 8.7.4 (m/s 101)"},
            {"Komponen": "Tinggi Cawan Suction atas Tray", "Nilai": "30 – 33 mm", "Rujukan": "Bab 8.9.4 (m/s 116)"},
            {"Komponen": "Bukaan Gripper Dulang", "Nilai": "290 mm", "Rujukan": "Bab 8.7.8 (m/s 106)"},
            {"Komponen": "Tekanan Minima Pneumatik", "Nilai": "4.0 bar (Trip) / 5.0 bar", "Rujukan": "Bab 8.13 (m/s 151)"}
        ]))
    with col2:
        st.markdown("#### 🥚 Omnia FT 330 Grader & Packing Lane")
        st.table(pd.DataFrame([
            {"Komponen": "Penegang Spring Pusher Bawah Buffer", "Nilai": "1.0 mm bawah strip", "Rujukan": "Bab 11.5.3 (m/s 156)"},
            {"Komponen": "Ketinggian Saluran Dropset", "Nilai": "163 mm", "Rujukan": "Bab 11.4.7 (m/s 153)"},
            {"Komponen": "Kelegaan Pin Conveyor ke Plat", "Nilai": "15 mm", "Rujukan": "Bab 11.2.1 (m/s 140)"},
            {"Komponen": "Spring MultiDrum™ FT 330", "Nilai": "110 mm (Min: 100 mm)", "Rujukan": "Bab 6.3.4 (m/s 58)"},
            {"Komponen": "Kelegaan Double Roll Infeed", "Nilai": "0.5 – 1.0 mm", "Rujukan": "Bab 6.3.7 (m/s 61)"},
            {"Komponen": "Pemberat Kalibrasi Pembawa", "Nilai": "63 gram (Art. 80206980)", "Rujukan": "Bab 9.7.3 (m/s 107)"}
        ]))

# ====================================================
# TAB 4: PENJEJAK PM & JAM OPERASI
# ====================================================
with tab_pm:
    st.subheader("Penjejak Kitaran Hayat & Jadual PM Berjadual")
    hrs = st.number_input("Masukkan Jumlah Jam Operasi Mesin Terkini:", min_value=0, value=2400, step=100)

    st.markdown("#### 💡 Status Tiub Lampu UV-C Infeed (Philips TUV PL-L 55W)")
    uv_used = hrs % 9000
    st.write(f"Jam Terpakai: **{uv_used} / 9,000 Jam Operasi**")
    st.progress(min(uv_used / 9000.0, 1.0))
    if uv_used >= 8500:
        st.error("🚨 AMARAN: Lampu UV-C melebihi 8,500 jam! Tukar tiub Philips TUV 55W (Kod: 927908704007).")
    else:
        st.success("✅ Keadaan radiasi kuman UV-C memuaskan.")

    st.markdown("---")
    st.markdown("#### 📋 Senarai Semak Rutin Berdasarkan Jam Operasi:")
    st.write("• **Setiap 8 Jam:** Bersihkan cecair telur pada poket dan cuci cermin/pemantul penderia optik.")
    st.write("• **Setiap 40 Jam:** Buang kulit telur dan bulu ayam di kawasan dropset. Cuci sarung penapis minyak.")
    st.write("• **Setiap 200 Jam:** Minyakkan rantai infeed & packing conveyor (Shell T 46) dan cuci penapis semburan.")
    st.write("• **Setiap 400 Jam:** Periksa kedudukan penegang spring rantai penolak (pusher chain) di packing lane.")
    st.write("• **Setiap 1,200 Jam:** Semak ketegangan tali sawat toothed belt (Hz) dan rantai pemacu.")
    st.write("• **Setiap 2,400 Jam:** Gantikan penapis udara dan uji semua litar Emergency Stop & suis interlock.")
