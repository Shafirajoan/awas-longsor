# Awas Longsor · Sistem Peringatan Dini Lereng Lempongsari

## 1. Masalah & Ide

Lempongsari (Gajahmungkur) merupakan wilayah yang pernah mengalami pergerakan tanah/longsor. Sistem **Awas Longsor** dibangun untuk memantau pergeseran lambat (*creep*) pada lereng menggunakan sensor akselerometer dan giroskop pada perangkat HP, yang dikombinasikan dengan data curah hujan real-time.

Pada versi perbaikan ini ditambahkan **komponen AI (machine learning)** yang mengklasifikasikan level risiko dan berjalan berdampingan dengan logika rule-based.

## 2. Arsitektur Sistem

- **Edge 1 (HP A):** Dipasang di titik lereng (mengirim telemetri getaran dan kemiringan).
- **Edge 2 (HP B):** Dipasang di pos RT/RW sebagai pembanding (referensi gerakan umum).
- Namun, HP A dan B masih kita simulasikan mandiri di rumah. Belum dipraktikkan secara nyata di daerah Lempongsari.
- **MQTT Broker:** Menggunakan HiveMQ Publik via protokol TLS.
- **Detector & Dashboard:** Berjalan di laptop/server lokal untuk menghitung skor risiko (Aman, Waspada, Siaga, Awas) serta menampilkan status secara *real-time*.
- **Komponen AI (di Detector):** Model Random Forest memprediksi level risiko dari data yang sama, sebagai pembanding hasil rule-based.

## Gambarannya

```
[ HP A: Lereng (Edge 1) ]  --\
                              +--> [ MQTT Broker (HiveMQ TLS:8883) ] <--> [ Dashboard Web ]
[ HP B: Pos RT/RW (Edge 2) ] -/                  ^
                                                 |
                                       [ Detector / Server ]
                                        |- rules.py       (rule-based)
                                        |- ml_predictor.py (Random Forest)
                                                 |
                                       [ Open-Meteo API (Hujan 24 jam) ]
```


## 3. Struktur Repository

```
awas-longsor/
├── config.py            # Konfigurasi MQTT Broker & Koordinat Lempongsari
├── sensors.py           # Modul pembaca sensor Termux & Simulator
├── processing.py        # Pengolahan data (RMS getaran, kemiringan, rotasi)
├── rules.py             # Logika keputusan skor risiko 4 level (rule-based)
├── ml_predictor.py      # [AI] Prediksi level risiko dengan model Random Forest
├── generate_data.py     # [AI] Pembuat data latih simulasi
├── train_model.py       # [AI] Pelatihan & evaluasi model
├── edge.py              # Script pengirim data telemetri edge device
├── detector.py          # Engine utama: rule-based + AI + integrasi API Hujan
├── dashboard/
│   └── index.html       # Dashboard pemantauan status real-time (WebSocket)
├── data/                # [AI] training.csv (dibuat oleh generate_data.py)
├── model/               # [AI] risk_model.pkl (dibuat oleh train_model.py)
├── tests/
│   ├── test_rules.py    # Unit test logika aturan keputusan
│   └── test_ml.py       # [AI] Unit test komponen ML
├── requirements.txt     # Daftar dependensi Python
├── .env.example         # Template variabel lingkungan
└── .gitignore           # Daftar file yang diabaikan oleh Git
```

## 4. Komponen AI (Machine Learning)

**Tujuan:** mengklasifikasikan level risiko longsor (AMAN, WASPADA, SIAGA, AWAS) dengan model machine learning, sebagai pembanding logika rule-based di `rules.py`.

| Aspek    | Keterangan |
|:---------|:-----------|
| Model    | Random Forest Classifier (scikit-learn), 100 pohon, kedalaman maksimum 8 |
| Input (5 fitur) | Kemiringan dari baseline (°), laju kemiringan (°/menit), getaran RMS lereng (m/s²), getaran RMS pos referensi (m/s²), curah hujan 24 jam (mm) |
| Output   | Level risiko (4 kelas) dan nilai *confidence* (probabilitas) |
| Data latih | 4.000 baris data simulasi dari 5 skenario (normal, getaran umum, creep, hujan lebat, acak) |
| Hasil    | Akurasi sekitar 97% pada data uji (20% dari data) |

**Cara kerja:** `detector.py` menjalankan `rules.py` dan `ml_predictor.py` pada data yang sama. Hasil keduanya dikirim lewat MQTT (`level` dari rule-based, `ml_level` dan `ml_confidence` dari model). Peringatan SIAGA/AWAS tetap memakai hasil rule-based. Jika file model tidak ada, sistem otomatis berjalan dengan rule-based saja.

**Cara melatih ulang:**

```bash
python generate_data.py   # membuat data/training.csv
python train_model.py     # melatih, mengevaluasi, menyimpan model/risk_model.pkl
```

### Keterbatasan

- Model dilatih dengan **data simulasi** yang labelnya berasal dari aturan di `rules.py`. Karena itu model ini pada dasarnya **meniru aturan tersebut**; akurasi tinggi belum membuktikan kemampuan memprediksi longsor nyata.
- Belum ada data dari kejadian longsor sungguhan.
- **Rencana lanjutan:** mengumpulkan data sensor nyata dari lereng Lempongsari dengan label hasil pengamatan lapangan, lalu melatih ulang model.

## 5. Cara Menjalankan

1. Clone repository ini dan masuk ke direktori proyek:
   ```bash
   git clone https://github.com/Shafirajoan/awas-longsor.git
   cd awas-longsor
   ```
2. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Salin file environment dan sesuaikan `PROJECT_ID`:
   ```bash
   cp .env.example .env
   ```
4. Latih model AI (membutuhkan `scikit-learn`, `pandas`, `joblib`):
   ```bash
   python generate_data.py
   python train_model.py
   ```
5. Jalankan pengujian dengan membuka 3 terminal di VS Code:
   - Terminal 1 (Detector): `python detector.py`
   - Terminal 2 (Edge 2 / Ref): `python edge.py --role ref --source simulator --scenario still`
   - Terminal 3 (Edge 1 / Slope): `python edge.py --role slope --source simulator --scenario creep`
6. Jalankan unit test:
   ```bash
   python -m pytest tests/
   ```

## 6. Hasil Pengujian Skenario

1. **Kondisi Normal:** bila kedua perangkat diam dan rata, hasil yang diharapkan AMAN.
2. **Kemiringan Lambat:** bila HP lereng dimiringkan perlahan lebih dari 5 derajat, hasil yang diharapkan WASPADA → SIAGA.
3. **Getaran Umum:** meja diguncang (kedua HP bergetar bersamaan), hasil yang diharapkan AMAN (`common_motion: true`).
4. **Kalibrasi Ulang:** posisi diratakan kembali, tekan tombol kalibrasi, hasil yang diharapkan kembali ke AMAN.

Pada setiap skenario, `detector.py` juga menampilkan `ml_level` dan `ml_confidence` sebagai pembanding hasil rule-based. Karena rule-based memakai *debounce* (level baru harus muncul 2 kali berturut-turut), `ml_level` bisa berubah sedikit lebih cepat daripada `level`.
