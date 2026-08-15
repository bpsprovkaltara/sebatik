# Konsolidasi Model Data

Ini adalah dokumen paling menentukan dalam refactoring: hampir seluruh utang teknis
lain berasal dari model data ganda. Konsolidasi harus selesai sebelum (atau bersamaan
dengan) pemindahan endpoint ke lapisan service/repository.

## 1. Inventaris tabel saat ini

Ada tiga kelompok tabel yang sebagian besar menyimpan hal yang sama:

### 1.1 Tabel ETL legacy (sumber: `src/etl/pipeline.py`)

| Tabel | Isi | Konsumen |
|---|---|---|
| `indikator` | Dimensi indikator hasil ETL Excel (86 baris). | Endpoint analitik lama (`/capaian`, `/indikator/{id}/detail`, `/analitik/*`, `/arah-baik`). |
| `nilai_indikator` | Fakta nilai provinsi `(id, tahun, jenis)` + `sumber_sheet`. | Endpoint analitik lama. |
| `metadata_indikator` | Metadata per indikator (definisi, rumus, dsb.) dari PDF. | `/indikator/{id}/detail`. |
| `penugasan_pic` | Nama PIC perorangan (privat). | Tidak dipakai endpoint publik. |
| `snapshot_ketersediaan` | Riwayat status ketersediaan per tanggal. | Analitik/snapshot. |

### 1.2 Tabel master/beranda (sumber: `backend/app/master_seed.py`)

| Tabel | Isi | Konsumen |
|---|---|---|
| `beranda_indikator` | Dimensi indikator "terverifikasi" (dari JSON basis data). | `/beranda`, `/indikator-explorer`, `/capaian-explorer`, `/insight`, `/validitas`, metadata. |
| `beranda_nilai` | Fakta provinsi terverifikasi + `nilai_teks` + `satuan_catatan`. | Semua halaman beranda/explorer/capaian/insight. |
| `beranda_nilai_periode` | Fakta periode (semester) provinsi. | `latest_period_value`. |
| `beranda_nilai_wilayah` | Fakta wilayah terverifikasi + `usulan_id`. | Beranda/explorer/insight/validitas per wilayah. |
| `beranda_nilai_wilayah_periode` | Fakta periode wilayah. | `latest_period_value` wilayah. |
| `beranda_metadata` | Metadata master per indikator. | `/beranda-indikator/{id}/metadata`. |

### 1.3 Tabel tata kelola (sumber: `src/etl/features.py`)

| Tabel | Isi |
|---|---|
| `wilayah` | Provinsi + 5 kab/kota. |
| `pengguna` | Akun, hash, peran, wilayah, status. |
| `usulan_nilai` | Antrean verifikasi nilai. |
| `bukti_dukung` | Metadata berkas bukti. |
| `nilai_indikator_wilayah` | Fakta wilayah (jalur lama). |
| `log_perubahan` | Jejak audit perubahan nilai/field. |
| `log_aktivitas` | Jejak audit tindakan admin. |
| `unggahan_excel` | Arsip unggahan massal + diff. |

## 2. Masalah yang ditimbulkan

1. **Dua dimensi indikator.** `indikator` dan `beranda_indikator` saling tumpang
   tindih: keduanya menyimpan `id_indikator`, `kategori`, `kelompok`,
   `arah_pembangunan`, `satuan`, `status_ketersediaan`, `periode_data`. Namun
   `beranda_indikator` menyimpan kolom master (`sasaran_visi`, `misi_agenda`,
   `arah_ie`, `indikator_induk`, `kelompok_makro`, `kode_indikator`, `sumber_data`,
   `frekuensi`) yang tidak ada di `indikator`, dan `indikator` menyimpan kolom ETL
   (`nomor`, `nama_asli`, `penghasil`, `kl_pengampu`, `tim_pjk`, `status_rpjmd`,
   `arah_baik`, `arah_baik_terverifikasi`, `kode_sdgs`, `link_*`, `catatan_teknis`).
2. **Empat fakta nilai.** `nilai_indikator`, `beranda_nilai`, `beranda_nilai_wilayah`,
   `nilai_indikator_wilayah` menyimpan nilai realisasi/target yang sama pada jalur
   berbeda.
3. **Penulisan N-arah.** Fungsi `verify_submission` di `features_api.py` menulis ke
   `beranda_nilai_wilayah_periode`, `beranda_nilai_wilayah`, `beranda_nilai_periode`,
   `beranda_nilai`, `nilai_indikator_wilayah`, dan `nilai_indikator` sekaligus.
   Ini sumber utama bug inkonsistensi dan menyulitkan transaksi.
4. **Nama kolom tidak konsisten.** `indikator.opd_penanggung_jawab` vs
   `beranda_indikator.opd_pengampu`; `nilai_indikator.sumber_sheet` vs
   `beranda_nilai.sumber_master` vs `beranda_nilai_wilayah.sumber`.
5. **Pemisahan tabel periode.** Nilai semester dipisah ke tabel `*_periode`, padahal
   cukup berupa kolom `periode` yang boleh NULL pada tabel fakta utama.

## 3. Skema target (konsolidasi)

Prinsip: **satu entitas = satu tabel**, dikelola ORM dan Alembic.

### 3.1 `indikator` (dimensi tunggal, gabungan `indikator` + `beranda_indikator`)

| Kolom | Tipe | Asal | Catatan |
|---|---|---|---|
| `id_indikator` | text PK | gabungan | `ISV-001` … `IUP-086`. |
| `kategori` | text | gabungan | `ISV` / `IUP`. |
| `nomor` | int | `indikator` | nomor urut dalam kategori. |
| `kode_indikator` | text | `beranda_indikator` | kode resmi RPJPD. |
| `nama_indikator` | text | gabungan | nama tampil. |
| `nama_asli` | text | `indikator` | nama asli workbook. |
| `kelompok` | text | gabungan | kelompok/pilar. |
| `arah_pembangunan` | text | gabungan | arah IE. |
| `sasaran_visi`, `misi_agenda`, `arah_ie`, `indikator_induk`, `kelompok_makro` | text | `beranda_indikator` | klasifikasi master. |
| `satuan` | text | gabungan | |
| `penghasil`, `kl_pengampu` | text | `indikator` | |
| `opd_pengampu` | text | `beranda_indikator.opd_pengampu` | **rename** dari `opd_penanggung_jawab`. |
| `tim_pjk` | text | `indikator` | |
| `sumber_data`, `frekuensi` | text | `beranda_indikator` | |
| `status_ketersediaan`, `status_metadata`, `periode_data`, `tahun_terakhir` | — | gabungan | |
| `is_proxy`, `nama_proxy` | — | gabungan | |
| `status_rpjmd` | text | `indikator` | enum `MASUK_RPJMD` dsb. |
| `arah_baik`, `arah_baik_terverifikasi` | — | `indikator` | |
| `kode_sdgs`, `link_metadata`, `link_publikasi`, `link_data`, `catatan_teknis` | text | `indikator` | |
| `sumber_master` | text | `beranda_indikator` | sumber basis data. |
| `status_verifikasi` | text | `beranda_indikator` | default `DISETUJUI`. |
| `diverifikasi_pada` | timestamptz | `beranda_indikator` | |

### 3.2 `metadata_indikator` (gabungan `metadata_indikator` + `beranda_metadata`)

| Kolom | Tipe | Asal |
|---|---|---|
| `id_indikator` | text PK/FK | gabungan |
| `definisi`, `interpretasi`, `sumber_data`, `frekuensi` | text | gabungan |
| `rumus` | text | `metadata_indikator` |
| `rumus_mentah` | text | gabungan |
| `rumus_latex` | text | `beranda_metadata` |
| `halaman_sumber` | text | `metadata_indikator` |
| `perlu_verifikasi_manual` | bool | `metadata_indikator` |
| `sumber_metadata` | text | gabungan |
| `nama_di_buku1` | text | `metadata_indikator` |
| `status_metadata` | text | `beranda_metadata` |

### 3.3 `nilai_indikator` (satu tabel fakta untuk semua nilai)

Menggabungkan `nilai_indikator`, `nilai_indikator_wilayah`, `beranda_nilai`,
`beranda_nilai_periode`, `beranda_nilai_wilayah`, `beranda_nilai_wilayah_periode`.

| Kolom | Tipe | Catatan |
|---|---|---|
| `id_indikator` | text FK | |
| `wilayah_kode` | text FK, NOT NULL | selalu terisi; `65` untuk provinsi (bukan NULL, agar indeks/UNIQUE sederhana). |
| `tahun` | int | |
| `jenis` | text | `realisasi` / `target`. |
| `periode` | int, nullable | NULL untuk nilai tahunan; `1`/`2` untuk semester. |
| `nilai` | numeric, nullable | |
| `nilai_teks` | text, nullable | teks asli dari master. |
| `label_periode` | text, nullable | mis. `Semester 2`. |
| `satuan_catatan` | text, nullable | |
| `sumber` | text | gabungan `sumber_sheet`/`sumber_master`/`sumber`. |
| `usulan_id` | int FK, nullable | referensi usulan yang menerbitkan nilai wilayah. |
| `status_verifikasi` | text | default `DISETUJUI`; menyerap `status_verifikasi` master. |
| `diverifikasi_pada` | timestamptz, nullable | |

- **Unique key**: `(id_indikator, wilayah_kode, tahun, jenis, periode)`.
- Nilai provinsi master punya `wilayah_kode = '65'`, `usulan_id = NULL`.
- Nilai wilayah dari operator punya `usulan_id` terisi.
- Perilaku `latest_period_value` (memilih periode terbaru yang disetujui) menjadi
  satu query repository dengan `ORDER BY periode DESC NULLS LAST`.

### 3.4 Tabel tata kelola (dipertahankan, di-ORM-kan)

`wilayah`, `pengguna`, `usulan_nilai`, `bukti_dukung`, `log_perubahan`,
`log_aktivitas`, `unggahan_excel`, `snapshot_ketersediaan`, `penugasan_pic` tetap,
dengan perbaikan kecil:

- Semua kolom waktu memakai `timestamptz` (PostgreSQL) dan disimpan UTC.
- `usulan_nilai.periode` dan `usulan_nilai.wilayah_kode` tetap.
- Tambah `created_at`/`updated_at` standar bila berguna untuk audit (opsional).
- Enum kolom `jenis`, `status`, `peran` dinyatakan sebagai PostgreSQL enum atau
  `text` + `CHECK` (konsisten dengan konvensi `SCREAMING_SNAKE_CASE`).

## 4. Pemetaan tabel lama → baru

| Tabel lama | Nasib |
|---|---|
| `indikator` + `beranda_indikator` | digabung → `indikator` (lihat §3.1). |
| `metadata_indikator` + `beranda_metadata` | digabung → `metadata_indikator` (lihat §3.2). |
| `nilai_indikator` + `beranda_nilai` | → `nilai_indikator` dengan `wilayah_kode='65'`. |
| `nilai_indikator_wilayah` + `beranda_nilai_wilayah` | → `nilai_indikator` dengan `wilayah_kode` kab/kota. |
| `beranda_nilai_periode` + `beranda_nilai_wilayah_periode` | → `nilai_indikator` dengan `periode` terisi. |
| `wilayah`, `pengguna`, `usulan_nilai`, `bukti_dukung`, `log_*`, `unggahan_excel`, `snapshot_ketersediaan`, `penugasan_pic` | dipertahankan. |

## 5. Dampak terhadap kode

1. **`verify_submission`** menulis ke **satu** baris `nilai_indikator` (upsert), lalu
   `UPDATE usulan_nilai` dan sisipan ke `log_*`. Semua dalam satu transaksi.
2. Endpoint analitik lama (yang membaca `nilai_indikator` provinsi) dan beranda
   (yang membaca `beranda_*`) menyatu: keduanya membaca `nilai_indikator` dengan
   filter `wilayah_kode` dan `status_verifikasi`.
3. Konstanta `KODE_PROVINSI = "65"` dibuat satu-satunya di `config.py` atau
   `models/wilayah.py` untuk menggantikan literal `"65"` yang tersebar.
4. Helper `indicator_payload` dan `latest_period_value` menjadi method repository.

## 6. Strategi migrasi skema

- Buat skema baru di PostgreSQL via Alembic (bukan memodifikasi tabel SQLite).
- Tulis migrasi data satu arah: dari SQLite `sebatik.db` ke skema PostgreSQL baru
  (lihat [migrasi-postgresql.md](migrasi-postgresql.md)).
- Selama masa transisi, pertahankan tabel `beranda_*` hanya sebagai **view** di
  PostgreSQL yang menunjuk tabel baru, sehingga endpoint lama tetap berjalan sampai
  dipindahkan. Setelah semua endpoint pindah, view dihapus.

## 7. Konvensi penamaan & tipe

- Tabel/kolom `snake_case`; enum `SCREAMING_SNAKE_CASE`.
- Primary key: `id` untuk tabel tata kelola; `id_indikator` untuk dimensi; gabungan
  untuk fakta.
- Foreign key selalu eksplisit; `ON DELETE` dipilih sengaja (mis. `bukti_dukung`
  `ON DELETE CASCADE` dari `usulan_nilai`).
- Kolom waktu memakai `timestamptz`; aplikasi menyimpan UTC dan frontend menampilkan
  waktu lokal (perilaku ini perlu dicatat sebagai perubahan kecil pada serialisasi).
