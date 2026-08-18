# Catatan Pelaksanaan Refactoring

Berkas ini mencatat keputusan dan temuan yang muncul **saat** refactoring
dijalankan, termasuk hal-hal yang berbeda dari rencana di dokumen lain.
Dokumen rencana tidak diubah; perbedaannya dicatat di sini.

## Temuan 1 — Dua daftar indikator, bukan dua tabel untuk daftar yang sama

**Kapan:** Fase 2, saat menjalankan pemindahan data.

`model-data.md` §4 mengasumsikan `indikator` (jalur ETL) dan `beranda_indikator`
(jalur master) menyimpan 86 indikator yang sama sehingga dapat digabung menjadi
satu dimensi 86 baris. Pemeriksaan data sebenarnya membantah asumsi itu:

| Pemeriksaan | Hasil |
|---|---|
| Skema ID | `ISV-01`…`IUP-76` (ETL) vs `ISV-001`…`IUP-080` (master) |
| Irisan ID | **0** |
| Nama indikator yang identik | **23** dari 86 |
| Contoh | `ISV-01` = "GNI per kapita", `ISV-001` = "PDRB per Kapita" |

Keduanya adalah **dua versi daftar indikator yang berbeda**, bukan dua
representasi dari daftar yang sama. Menggabungkannya lewat `id_indikator`
menghasilkan 172 baris, bukan 86.

**Keputusan (pemilik produk, 19 Agustus 2026):** daftar **master** yang dipakai;
jalur ETL dibuang. Dimensi `indikator` berisi 86 baris dari `beranda_indikator`.

### Konsekuensi yang harus ditindaklanjuti

1. **`arah_baik` hilang untuk 63 indikator.** Kolom ini hanya ada di jalur ETL
   dan merupakan hasil verifikasi manual admin. Skrip migrasi membawanya untuk
   23 indikator yang namanya cocok; 63 sisanya kosong. Selama kosong,
   `/api/v1/capaian` mengembalikan `status_capaian = "BELUM_ADA_DATA"` untuk
   indikator tersebut — perilaku yang benar (tidak mengarang angka), tetapi
   perlu dilengkapi lewat `PUT /api/v1/arah-baik/{id}` yang sudah ada.
2. **`tim_pjk` hilang untuk 63 indikator.** Filter `tim` pada `/api/v1/indikator`
   dan `/api/v1/capaian` menjadi kurang berguna sampai diisi ulang.
3. **ID publik berubah** dari `ISV-04` menjadi `ISV-004` dan seterusnya untuk
   endpoint analitik/capaian. Bentuk respons tidak berubah, tetapi nilai
   `id_indikator` berubah. Frontend tidak menyimpan ID secara permanen sehingga
   tidak terpengaruh; pranala eksternal yang menyimpan ID lama akan 404.
4. **`penugasan_pic` (189 baris) dan `snapshot_ketersediaan` (63 baris) dibuang**
   karena memakai ID ETL tanpa padanan master. Keduanya tidak dipakai endpoint
   publik.

### Alternatif yang tidak diambil

- Menggabungkan 172 baris (lossless) — ditolak karena menyisakan dua daftar di
  satu tabel dan tidak memenuhi kriteria "satu entitas satu tabel".
- Memetakan 23 yang cocok lalu menyisakan 149 — ditolak dengan alasan yang sama.

## Temuan 2 — Fakta kembar akibat penulisan N-arah

**Kapan:** Fase 2, saat verifikasi jumlah baris.

`verify_submission` lama menulis satu nilai ke banyak tabel sekaligus. Akibatnya
`beranda_nilai` dan `beranda_nilai_wilayah` (dengan `wilayah_kode='65'`) memuat
fakta yang sama untuk `IUP-056` tahun 2022. Skrip migrasi **menggabungkan**,
bukan membuang salah satu: nilai diambil dari baris pertama, sedangkan jejak
usulan (`usulan_id`, `sumber`) diambil dari baris yang memilikinya, sehingga
riwayat verifikasi tidak putus. Bila dua sumber berbeda angka, skrip mencatat
peringatan alih-alih diam.

Verifikasi jumlah baris karena itu membandingkan **kunci alami yang berbeda**,
bukan jumlah baris mentah.

## Temuan 3 — Bug `/beranda` untuk kabupaten/kota

**Kapan:** Fase 0, saat merekam garis dasar kontrak API.

`GET /api/v1/beranda?wilayah_kode=6501` mengembalikan **500** karena query
memilih kolom `satuan_catatan` yang tidak ada di `beranda_nilai_wilayah`.
Ini akibat langsung model data ganda. Tes kontrak menandainya `xfail` dengan
alasan tertulis; tanda itu dilepas setelah konsolidasi (Fase 4) membuatnya lulus.

## Lingkungan pengembangan

- PostgreSQL **belum dapat diuji di mesin lokal** (Docker Desktop tidak berjalan
  saat pengerjaan). Yang dilakukan sebagai gantinya:
  - DDL PostgreSQL diverifikasi lewat mode offline Alembic (`upgrade head --sql`).
  - Migrasi dan pemindahan data dijalankan penuh terhadap SQLite target.
  - CI menjalankan `alembic upgrade head` dan `downgrade base` terhadap
    PostgreSQL 16 sungguhan pada setiap PR.
- Berkas `.venv-sebatik` dibuat ulang karena `.runtime-packages` yang ada di repo
  tidak lengkap (paket `sqlalchemy` hanya menyisakan direktori `cyextension`).

## Urutan cutover yang disarankan

```bash
# 1. Cadangkan basis data lama
python scripts/backup_sqlite.py

# 2. Siapkan PostgreSQL dan skema
docker compose up -d db
SEBATIK_DATABASE_URL=postgresql+psycopg://sebatik:SANDI@localhost:5432/sebatik \
  python -m alembic -c backend/alembic.ini upgrade head

# 3. Lihat rencana pemindahan lebih dulu
python scripts/migrasi_ke_skema_target.py --periksa

# 4. Pindahkan (satu transaksi; batal otomatis bila verifikasi gagal)
python scripts/migrasi_ke_skema_target.py --jalankan

# 5. Arahkan aplikasi ke PostgreSQL, lalu jalankan tes kontrak
docker compose up -d
```

Rollback: arahkan `SEBATIK_DATABASE_URL` kembali ke SQLite. Berkas lama tidak
disentuh skrip migrasi (dibuka mode `ro`). Data yang ditulis ke PostgreSQL
setelah cutover tidak otomatis kembali dan perlu dipindahkan manual.
