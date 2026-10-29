# Awas Longsor · Sistem Peringatan Dini Lereng Lempongsari

## 1. Masalah & Ide
Lempongsari (Gajahmungkur) merupakan wilayah yang pernah mengalami pergerakan tanah/longsor. Sistem **Awas Longsor** dibangun untuk memantau pergeseran lambat (*creep*) pada lereng menggunakan sensor akselerometer dan giroskop pada perangkat HP, yang dikombinasikan dengan data curah hujan real-time.

## 2. Arsitektur Sistem
- **Edge 1 (HP A):** Dipasang di titik lereng (mengirim telemetri getaran dan kemiringan).
- **Edge 2 (HP B):** Dipasang di pos RT/RW sebagai pembanding (referensi gerakan umum).
- Namun, HP A dan B masih kita simulasikan mandiri dirumah. Belum untuk di praktekan secara nyata di daerah Lempongsari.
- **MQTT Broker:** Menggunakan HiveMQ Publik via protokol TLS.
- **Detector & Dashboard:** Berjalan di laptop/server lokal untuk menghitung skor risiko (Aman, Waspada, Siaga, Awas) serta menampilkan status secara *real-time*.

## Gambarannya
[ HP A: Lereng (Edge 1) ] --

+--> [ MQTT Broker (HiveMQ TLS:8883) ] <--> [ Dashboard Web ]
[ HP B: Pos RT/RW (Edge 2) ] --/                  ^
|
[ Detector / Server ]
|
[ Open-Meteo API (Hujan 24 jam) ]

### Kesesuaian Ketentuan Tugas:
| Ketentuan Praktikum | Implementasi pada Awas Longsor |
| :--- | :--- |
| **2 Edge Devices** | Edge 1 (`edge1` / Lereng) & Edge 2 (`edge2` / Pos RT/RW) |
| **2 Sensor Perangkat** | Accelerometer & Gyroscope |
| **2 Jenis Data Processing** | RMS Getaran ($m/s^2$), Sudut Kemiringan ($^\circ$), dan Total Rotasi ($rad$) |
| **Algoritma Risk Scoring** | *Rule-based sensor fusion*, filter guncangan umum, dan integrasi data hujan |
| **Protokol Cloud** | MQTT over TLS (HiveMQ Public, Port 8883) |
| **Komunikasi 2 Arah** | Telemetri dari Edge ke Cloud $\rightarrow$ Alert dari Cloud ke Edge 2 |

## 3. Struktur Repository

awas-longsor/
├── config.py           # Konfigurasi MQTT Broker & Koordinat Lempongsari
├── sensors.py          # Modul pembaca sensor Termux & Simulator
├── processing.py       # Pengolahan data (RMS getaran, kemiringan, rotasi)
├── rules.py            # Logika keputusan skor risiko 4 level
├── edge.py             # Script pengirim data telemetri edge device
├── detector.py         # Engine utama pemrosesan data & integrasi API Hujan
├── dashboard/
│   └── index.html      # Dashboard pemantauan status real-time (WebSocket)
├── tests/
│   └── test_rules.py   # Unit testing logika aturan keputusan
├── requirements.txt    # Daftar dependensi Python
├── .env.example        # Template variabel lingkungan
├── .gitignore          # Daftar file yang diabaikan oleh Git
└── Catatan.md           # Dokumentasi utama proyek

## 4. Cara Menjalankan
1. Clone repository ini dan masuk ke direktori proyek: 
git clone [https://github.com/USERNAME/awas-longsor.git](https://github.com/USERNAME/awas-longsor.git)
cd awas-longsor
2. Install dependensi:
pip install -r requirements.txt
3. Salin file environment dan sesuaikan PROJECT_ID:
cp .env.example .env
4. Jalankan Testing dengan
Membuka 3 terminal di VS Code:
- Terminal 1 (Detector): python detector.py
- Terminal 2 (Edge 2 / Ref): python edge.py --role ref --source simulator --scenario still
- Terminal 3 (Edge 1 / Slope): python edge.py --role slope --source simulator --scenario creep

## 5. Hasil Pengujian Skenario
1. Kondisi Normal : bila Kedua perangkat posisi diam rata, hasil yang diharapkan AMAN
2. Kemiringan Lambat : bila HP Lereng dimiringkan perlahan lebih dari 5 derajat, hasil yang diharapkan WASPADA -> SIAGA
3. Getaran Umum : Meja diguncang (kedua HP bergetar bersamaan), hasil yang diharapkan AMAN (common_motion: true)
4. Kalibrasi Ulang : Posisi diratakan kembali, tekan tombol kalibrasi, hasil yang diharapkan Kembali ke AMAN
