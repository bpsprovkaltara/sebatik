# Diagram Sistem SEBATIK

Dokumen ini menggambarkan implementasi SEBATIK saat ini berdasarkan alur pada frontend, endpoint FastAPI, proses ETL, dan skema `data/processed/sebatik.db`.

## 1. Proses bisnis berbasis peran

```mermaid
flowchart LR
  subgraph PUB["Pengunjung"]
    direction TB
    P0([Mulai]) --> P1["Buka SEBATIK"]
    P1 --> P2["Lihat beranda, indikator, capaian, insight, dan validitas"]
    P2 --> P3["Pilih wilayah, tahun, indikator, dan filter"]
    P3 --> P4["Lihat hanya data yang telah disetujui"]
    P4 --> P5["Unduh CSV, XLSX, detail indikator, atau paket data"]
  end

  subgraph OPR["Operator Wilayah"]
    direction TB
    O0["Login dan ganti kata sandi awal"] --> O1["Pilih indikator dan tahun"]
    O1 --> O2["Isi nilai realisasi, sumber, dan catatan"]
    O2 --> O3["Unggah satu atau lebih bukti dukung"]
    O3 --> O4["Kirim usulan"]
    O4 --> O5["Status: MENUNGGU_VERIFIKASI"]
    O5 --> O6{"Keputusan verifikator"}
    O6 -->|Ditolak| O7["Lihat alasan dan ajukan koreksi baru"]
    O7 --> O1
    O6 -->|Disetujui| O8["Nilai wilayah menjadi data terverifikasi"]
  end

  subgraph VER["Verifikator"]
    direction TB
    V0["Login"] --> V1["Buka antrean seluruh wilayah"]
    V1 --> V2["Periksa nilai, sumber, catatan, dan bukti"]
    V2 --> V3{"Layak disetujui?"}
    V3 -->|Tidak| V4["Tolak dan isi alasan"]
    V3 -->|Ya| V5["Setujui usulan"]
    V5 --> V6["Perbarui nilai wilayah dan catat audit"]
  end

  subgraph ADM["Admin"]
    direction TB
    A0["Login"] --> A1{"Pilih fungsi administrasi"}
    A1 --> A2["Kelola akun, peran, status, wilayah, dan reset kata sandi"]
    A1 --> A3["Verifikasi usulan seperti Verifikator"]
    A1 --> A4["Koreksi arah baik indikator"]
    A1 --> A5["Unggah Excel massal"]
    A5 --> A6["Validasi file dan jalankan ETL pada database staging"]
    A6 --> A7["Tinjau pratinjau perubahan"]
    A7 --> A8{"Setujui perubahan?"}
    A8 -->|Belum| A9["Data produksi tidak berubah"]
    A8 -->|Ya| A10["Terapkan nilai dan status ke database produksi"]
    A10 --> A11["Simpan arsip, snapshot, dan log perubahan"]
    A1 --> A12["Pantau audit nilai dan aktivitas"]
  end

  O5 -. "masuk antrean" .-> V1
  V4 -. "status DITOLAK" .-> O6
  V6 -. "data publik diperbarui" .-> P4
  A3 -. "dapat mengambil keputusan" .-> V2
  A10 -. "data publik diperbarui" .-> P4
```

## 2. Arsitektur sistem

```mermaid
flowchart TB
  subgraph CLIENT["Lapisan pengguna"]
    M["Browser mobile"]
    D["Browser desktop/laptop"]
  end

  subgraph PROD["Server produksi · Docker"]
    direction TB
    APP["Container sebatik · port 8000"]
    STATIC["React SPA hasil build Vite\nHTML · CSS · JavaScript · Recharts"]
    API["FastAPI /api/v1\nREST API · validasi · ekspor"]
    AUTH["JWT + Argon2\nkontrol akses berbasis peran"]
    ORM["SQLAlchemy + SQL langsung"]
    ETL["ETL Excel/PDF\nopenpyxl · pdfplumber · staging"]
    FILES["Arsip unggahan dan bukti dukung"]
    DB[("SQLite\nsebatik.db")]
    APP --> STATIC
    APP --> API
    API --> AUTH
    API --> ORM
    API --> ETL
    API --> FILES
    ORM --> DB
    ETL --> DB
  end

  subgraph OPS["Operasional data"]
    SRC["Excel ISV-IUP · PDF metadata · GeoJSON"]
    BACKUP["Container backup harian\nretensi 30 salinan"]
    VOL1[("Volume sebatik_data")]
    VOL2[("Volume sebatik_backup")]
    SRC --> ETL
    DB --- VOL1
    FILES --- VOL1
    VOL1 --> BACKUP
    BACKUP --> VOL2
  end

  subgraph DEV["Lingkungan pengembangan"]
    VITE["Vite dev server · port 5173"]
    UVICORN["Uvicorn/FastAPI · port 8000"]
    VITE -->|"proxy /api"| UVICORN
  end

  M -->|"HTTP/HTTPS"| APP
  D -->|"HTTP/HTTPS"| APP
  STATIC -->|"fetch /api/v1"| API
  D -. "pengembangan" .-> VITE
  UVICORN -. "kode backend yang sama" .-> API
```

## 3. Diagram basis data

Diagram menampilkan seluruh tabel aplikasi. Atribut yang ditampilkan diprioritaskan pada primary key, foreign key, status, dan nilai bisnis agar relasi tetap terbaca.

```mermaid
erDiagram
  WILAYAH {
    text kode PK
    text nama
    text tingkat
    text parent_kode
    integer aktif
  }
  PENGGUNA {
    integer id PK
    text username UK
    text password_hash
    text peran
    text tim_pjk
    text wilayah_kode FK
    integer aktif
  }
  INDIKATOR {
    text id_indikator PK
    text kategori
    integer nomor
    text nama_indikator
    text tim_pjk
    text status_ketersediaan
    text status_metadata
    integer tahun_terakhir
    text arah_baik
  }
  NILAI_INDIKATOR {
    text id_indikator PK,FK
    integer tahun PK
    text jenis PK
    real nilai
    text sumber_sheet
  }
  METADATA_INDIKATOR {
    text id_indikator PK,FK
    text definisi
    text rumus
    text interpretasi
    text sumber_data
    text frekuensi
  }
  PENUGASAN_PIC {
    integer id PK
    text id_indikator FK
    text jenis_pic
    text nama_pic
  }
  SNAPSHOT_KETERSEDIAAN {
    text id_indikator PK,FK
    text tanggal_snapshot PK
    text status
  }
  USULAN_NILAI {
    integer id PK
    text id_indikator FK
    text wilayah_kode FK
    integer pengusul_id FK
    integer verifikator_id FK
    integer tahun
    text jenis
    real nilai
    text status
    text alasan_verifikasi
  }
  BUKTI_DUKUNG {
    integer id PK
    integer usulan_id FK
    text nama_file
    text path_file
    text mime_type
    integer ukuran
    text checksum_sha256
  }
  NILAI_INDIKATOR_WILAYAH {
    text id_indikator PK,FK
    text wilayah_kode PK,FK
    integer tahun PK
    text jenis PK
    real nilai
    integer usulan_id FK
  }
  LOG_PERUBAHAN {
    integer id PK
    integer pengguna_id FK
    text id_indikator FK
    text field
    text nilai_lama
    text nilai_baru
    text sumber_perubahan
  }
  LOG_AKTIVITAS {
    integer id PK
    integer pengguna_id FK
    text aksi
    text objek_tipe
    text objek_id
    text detail
  }
  UNGGAHAN_EXCEL {
    integer id PK
    integer pengguna_id FK
    text nama_file_asli
    text path_arsip
    text checksum_sha256
    text status
    text ringkasan_diff
  }
  BERANDA_INDIKATOR {
    text id_indikator PK
    text kode_indikator
    text nama_indikator
    text kategori
    text status_ketersediaan
    text status_verifikasi
  }
  BERANDA_NILAI {
    text id_indikator PK,FK
    integer tahun PK
    text jenis PK
    real nilai
    text nilai_teks
    text status_verifikasi
  }
  BERANDA_NILAI_WILAYAH {
    text id_indikator PK,FK
    text wilayah_kode PK,FK
    integer tahun PK
    text jenis PK
    real nilai
    integer usulan_id FK
    text status_verifikasi
  }

  WILAYAH ||--o{ WILAYAH : "parent dari"
  WILAYAH ||--o{ PENGGUNA : "wilayah akun"
  INDIKATOR ||--o{ NILAI_INDIKATOR : "memiliki"
  INDIKATOR ||--o| METADATA_INDIKATOR : "memiliki"
  INDIKATOR ||--o{ PENUGASAN_PIC : "ditugaskan"
  INDIKATOR ||--o{ SNAPSHOT_KETERSEDIAAN : "dipantau"
  INDIKATOR ||--o{ USULAN_NILAI : "diusulkan"
  WILAYAH ||--o{ USULAN_NILAI : "berasal dari"
  PENGGUNA ||--o{ USULAN_NILAI : "mengusulkan"
  PENGGUNA o|--o{ USULAN_NILAI : "memverifikasi"
  USULAN_NILAI ||--o{ BUKTI_DUKUNG : "dilampiri"
  INDIKATOR ||--o{ NILAI_INDIKATOR_WILAYAH : "memiliki nilai wilayah"
  WILAYAH ||--o{ NILAI_INDIKATOR_WILAYAH : "memiliki"
  USULAN_NILAI ||--o| NILAI_INDIKATOR_WILAYAH : "menghasilkan"
  PENGGUNA o|--o{ LOG_PERUBAHAN : "mencatat"
  INDIKATOR o|--o{ LOG_PERUBAHAN : "diubah"
  PENGGUNA o|--o{ LOG_AKTIVITAS : "melakukan"
  PENGGUNA o|--o{ UNGGAHAN_EXCEL : "mengunggah"
  BERANDA_INDIKATOR ||--o{ BERANDA_NILAI : "memiliki"
  BERANDA_INDIKATOR ||--o{ BERANDA_NILAI_WILAYAH : "memiliki"
  WILAYAH ||--o{ BERANDA_NILAI_WILAYAH : "mencakup"
  USULAN_NILAI o|--o| BERANDA_NILAI_WILAYAH : "menerbitkan"
```

### Catatan struktur data

- `indikator`, `nilai_indikator`, dan `metadata_indikator` adalah dataset utama hasil ETL.
- `usulan_nilai` menyimpan workflow; persetujuan menghasilkan atau memperbarui `nilai_indikator_wilayah` dan tampilan publik wilayah.
- `beranda_*` adalah tabel baca terverifikasi yang menyokong beranda dan explorer, termasuk nilai teks serta data wilayah.
- `bukti_dukung` menyimpan metadata berkas; isi berkas berada pada penyimpanan arsip, bukan sebagai BLOB di SQLite.
- `log_perubahan` merekam perubahan nilai/field, sedangkan `log_aktivitas` merekam tindakan administratif.
