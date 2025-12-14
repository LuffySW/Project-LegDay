# 🏋️ Smart Biomechanical Squat Assistant (Tubes PCD)

Sistem analisis gerakan Squat cerdas menggunakan **Computer Vision (MediaPipe)** dan **Depth Sensor (OpenNI/Orbbec)**. Sistem ini mendeteksi postur tubuh, menghitung repetisi squat yang valid, dan memberikan feedback koreksi postur (anti-bungkuk & anti-cheat) secara real-time.

Sistem ini dirancang **Modular** dan **Cross-Platform**, sehingga dapat dikembangkan di Windows (Fitur Lengkap) maupun MacOS/Linux (Mode UI Development).

---

## 📂 Struktur Project

Pastikan struktur folder Anda terlihat seperti ini agar driver terbaca dengan benar:

```text
Tubes_PCD_Squat/
│
├── drivers/                  # [WINDOWS ONLY] Driver OpenNI2 & Konfigurasi Hardware
│   ├── OpenNI2.dll           # Library utama OpenNI
│   ├── OpenNI.ini            # Config file
│   └── OpenNI2/
│       └── Drivers/          # DLL Driver spesifik (Orbbec/PS1080)
│
├── core/                     # [BRAIN] Logika Utama (Backend Logic)
│   ├── __init__.py
│   └── squat_logic.py        # Class SquatAnalyzer (Matematika sudut, counter, logic)
│
├── main_desktop.py           # Aplikasi Desktop (Full Feature: Depth + Suara + CV2 Window)
├── main_web.py               # Aplikasi Web Dashboard (Streamlit UI - Cross Platform)
├── requirements.txt          # Daftar library Python
└── README.md                 # Dokumentasi Project

```

---

## ⚙️ Prasyarat (Requirements)

### 🖥️ Untuk Windows (Full Feature - Luthfi)
1. **Python 3.8 - 3.10** (Disarankan 3.10).
2. **Hardware:** Kamera Orbbec Astra Pro terhubung via USB.
3. **OS:** Windows 10/11 (Wajib untuk fitur Suara & Depth).

### 🍎 Untuk Mac M-Series / Linux (UI Dev - Adrian & Fanza)
1. **Python 3.9 - 3.11**.
2. **Hardware:** Webcam Laptop Standar (Fitur Depth akan otomatis non-aktif).
3. **OS:** MacOS / Linux.

---

## 🚀 Instalasi & Setup

### 1. Clone Repository
```bash
git clone <repository_url>
cd Tubes_PCD_Squat

```

### 2. Setup Virtual Environment (Disarankan)
Agar library tidak bentrok dengan project lain.

**Windows:**

```bash
python -m venv PCDvenv
.\PCDvenv\Scripts\activate

```

**Mac / Linux:**

```bash
python3 -m venv PCDvenv
source PCDvenv/bin/activate

```

### 3. Install Dependencies
⚠️ **PERHATIAN:** Cara install berbeda tergantung OS!

**A. Pengguna Windows (Luthfi):**
Install semua library termasuk driver suara dan OpenNI.

```bash
pip install -r requirements.txt

```

**B. Pengguna Mac/Linux (Adrian & Fanza):**
**JANGAN** jalankan `requirements.txt` penuh karena `pywin32` dan `openni` akan error di Mac. Install manual saja:

```bash
pip install opencv-python-headless numpy mediapipe streamlit pyttsx3

```

---

## ▶️ Cara Menjalankan

### 1. Aplikasi Desktop (Windows Only)
Menjalankan aplikasi native dengan performa maksimal, fitur suara (Text-to-Speech), dan deteksi jarak (Depth).

```bash
python main_desktop.py

```

* **Kontrol:** Tekan `q` pada window kamera untuk keluar.
* **Fitur:** Depth Safety Check, Voice Feedback (Threaded), Anti-Crash.

### 2. Aplikasi Web Streamlit (Cross-Platform)
Digunakan untuk pengembangan UI Dashboard dan Presentasi. Aman dijalankan di Mac (Mode RGB Only).

```bash
streamlit run main_web.py

```

* **Akses:** Buka browser di `http://localhost:8501`
* **Fitur Windows:** Depth Sensor ON, Suara ON.
* **Fitur Mac:** Depth Sensor OFF (Disabled), Suara OFF (Silent Mode), tapi logika squat tetap jalan.

---

## 👨‍💻 Panduan Pengembangan (Dev Guide)

### Core Logic (`core/squat_logic.py`)
Ini adalah "Otak" matematika aplikasi. Berisi perhitungan sudut dan *State Machine*.

* **Input:** Landmarks MediaPipe.
* **Output:** Dictionary berisi `{reps, feedback, angle, color, voice_command}`.
* **Catatan:** File ini **Platform Agnostic** (Bisa jalan di mana saja). Jika ingin mengubah sensitivitas squat, ubah `SMOOTHING_FACTOR` atau `HIP_DROP_THRESHOLD` di file ini.

### User Interface (`main_web.py`)
Tim UI (Adrian & Fanza) fokus mengembangkan file ini.

* Gunakan variabel `data` yang dikembalikan oleh `analyzer.analyze()` untuk menampilkan metrik.
* Kalian bebas mempercantik tampilan Streamlit (CSS, Grafik, Layout).
* **Jangan ubah folder `drivers/`** karena hanya bisa dites di Windows.

---

## 🛠️ Troubleshooting

1. **Error `OpenNI2.dll not found` (Windows):**
* Pastikan folder `drivers/` ada di root project dan strukturnya benar.
* Pastikan Python architecture (64-bit) cocok dengan DLL.


2. **Error `ModuleNotFoundError: pywin32` (Mac):**
* Abaikan atau uninstall pywin32. Mac tidak butuh ini. Kode `main_web.py` sudah otomatis mendeteksi OS dan mematikan fitur suara jika bukan Windows.


3. **Kamera Blank / Hitam / Error:**
* Ubah index kamera di sidebar Streamlit (pilih 0, 1, atau 2).
* Di `main_desktop.py`, ubah variabel `WEBCAM_INDEX`.



---

## 👥 Credits
**Tugas Besar Pengolahan Citra Digital (PCD)**

* **Logic & Hardware Integration:** Luthfi Satrio Wicaksono
* **UI/UX Dashboard:** Adrian & Fanza
