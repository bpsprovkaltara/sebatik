# Spesifikasi Refactoring SEBATIK

Dokumen induk untuk refactoring menyeluruh aplikasi SEBATIK agar lebih scalable,
mudah dipelihara, dan siap dioperasikan sebagai sistem multi-pengguna.

Dokumen ini disusun **dari umum ke detail**. Bagian awal menjelaskan gambaran besar
(mengapa, ke mana arahnya, prinsip apa yang dipakai), lalu rincian teknis dibagi ke
dalam dokumen pendamping di folder `docs/refactoring/`.

---

## Daftar isi dokumen pendamping

| Dokumen | Isi |
|---|---|
| [arsitektur-target.md](refactoring/arsitektur-target.md) | Struktur repo target, layering backend, struktur frontend, dan diagram arsitektur. |
| [model-data.md](refactoring/model-data.md) | Konsolidasi model data ganda, skema target, pemetaan tabel lama → baru, aturan migrasi skema. |
| [backend.md](refactoring/backend.md) | Pemecahan `features_api.py`/`main.py` menjadi router/service/repository/schema, daftar endpoint per modul, konvensi kode, dan penanganan kesalahan. |
| [auth-keamanan.md](refactoring/auth-keamanan.md) | Desain autentikasi/otorisasi, manajemen rahasia, dan perbaikan keamanan lain. |
| [frontend.md](refactoring/frontend.md) | Pemecahan `App.jsx`, routing, state management, struktur `pages/`/`components/`/`hooks/`. |
| [etl.md](refactoring/etl.md) | Menjadikan pipeline ETL data-driven, menghapus rentang hardcode, dan pemisahan ekstraksi/transformasi/load. |
| [migrasi-postgresql.md](refactoring/migrasi-postgresql.md) | Strategi migrasi SQLite → PostgreSQL, Alembic, migrasi data, dan perubahan deployment. |
| [testing-ci.md](refactoring/testing-ci.md) | Strategi pengujian, linting, type checking, dan pipeline CI. |
| [peta-jalan.md](refactoring/peta-jalan.md) | Urutan fase eksekusi, kriteria selesai (definition of done), dan strategi rollback. |

---

## 1. Ringkasan eksekutif

SEBATIK dibangun secara bertahap (Tahap 1–9, lihat `CHANGELOG.md`) sebagai satu
proses FastAPI yang menyajikan API dan build frontend sekaligus, dengan SQLite
sebagai satu-satunya penyimpanan. Pola ini bekerja untuk percontohan di server
internal, tetapi menyimpan sejumlah akumulasi utang teknis yang membatasi skalabilitas:

1. **Satu file API raksasa.** `backend/app/features_api.py` (636 baris) menampung
   hampir seluruh endpoint, helper, ekspor, dan logika bisnis. Sulit diuji dan
   di-review; setiap perubahan menyentuh satu titik panas.
2. **Dua keluarga tabel paralel.** Tabel ETL legacy (`indikator`, `nilai_indikator`,
   `metadata_indikator`) hidup berdampingan dengan tabel master `beranda_*`. Aksi
   verifikasi menulis ke banyak tabel sekaligus, menciptakan risiko inkonsistensi.
3. **Migrasi skema ad hoc.** Tidak ada Alembic; skema diubah lewat
   `ALTER TABLE ... ADD COLUMN` dan rebuild manual di `src/etl/features.py` dan
   `backend/app/master_seed.py`.
4. **SQL langsung (raw SQL) dominan.** Hampir semua query memakai `text()`, sehingga
   tidak ada satu sumber kebenaran untuk bentuk data dan tidak ada type safety.
5. **Frontend monolit.** `App.jsx` (2292 baris) memuat semua halaman dan komponen.
6. **Nilai hardcode tersebar.** Rentang baris/kolom ETL, tahun 2021–2030, jumlah 86
   indikator, kode wilayah `"65"`, daftar sheet, dan ID sorotan beranda dikodekan
   sebagai literal.
7. **SQLite sebagai penyimpanan produksi.** Cocok untuk pembacaan, tetapi rapuh untuk
   penulisan bersamaan banyak pengguna (operator/verifikator) dan tidak menyediakan
   migrasi skema yang andal.

Tujuan refactoring adalah mempertahankan seluruh kontrak publik yang ada (endpoint,
perilaku pengguna, alur tata kelola) sambil membangun ulang struktur internalnya agar
lebih modular, teruji, dan dapat dipindahkan ke PostgreSQL.

## 2. Tujuan refactoring

| Tujuan | Ukuran keberhasilan |
|---|---|
| Pindah ke PostgreSQL + Alembic | Skema dikelola versi; migrasi dapat di-*upgrade*/*downgrade*; tidak ada lagi `ALTER TABLE` manual. |
| Konsolidasi model data | Satu sumber kebenaran per entitas; verifikasi menulis melalui satu jalur service. |
| Backend modular | Tidak ada file > ~300 baris; setiap endpoint punya unit test; logika bisnis terpisah dari HTTP. |
| Frontend terstruktur | `App.jsx` terpecah ke `pages/` dan `components/`; navigasi lewat router; state terpusat. |
| ETL data-driven | Tidak ada rentang baris/kolom hardcode; konfigurasi pembacaan workbook terpisah dari kode. |
| Pengujian & CI | Cakupan meningkat; lint/type check berjalan di CI; build otomatis. |
| Kontrak API tidak berubah | Semua endpoint `/api/v1/*` dan bentuk respons publik tetap kompatibel. |

## 3. Prinsip refactoring

1. **Strangler pattern.** Migrasi dilakukan bertahap per modul tanpa mematikan
   fungsionalitas lama. Sistem lama dan baru boleh hidup berdampingan selama transisi.
2. **Kontrak publik adalah batas suci.** Nama endpoint, parameter, dan bentuk JSON yang
   dipakai frontend tidak berubah kecuali benar-benar diperlukan; perubahan kontrak
   dicatat eksplisit.
3. **Satu sumber kebenaran.** Setiap entitas data punya satu tabel dan satu model;
   tidak ada lagi penulisan nilai yang sama ke banyak tabel dari handler HTTP.
4. **Logika bisnis bebas HTTP.** Semua aturan (perhitungan capaian, progres, korelasi,
   alur verifikasi) dipindah ke service murni yang dapat diuji tanpa menjalankan server.
5. **Konfigurasi terpusat dan terverifikasi.** Semua pengaturan lewat satu modul
   settings; tidak ada nilai penting yang hardcode di dalam fungsi.
6. **Perubahan kecil, terverifikasi, dapat di-rollback.** Setiap fase berakhir dalam
   keadaan aplikasi masih dapat dijalankan.

## 4. Gambaran besar target

```
Client (React SPA, tetap JavaScript)
        │  fetch /api/v1
        ▼
FastAPI ── routers ── services ── repositories ── SQLAlchemy ORM ── PostgreSQL
   │            (HTTP)    (bisnis)     (data)            │
   │                                                    ▼
   └── settings (pydantic-settings) ────────── Alembic migrations
```

- **Backend** memisahkan HTTP (`routers`), aturan bisnis (`services`), akses data
  (`repositories`), dan model ORM (`models`). Skema permintaan/tanggapan memakai
  Pydantic. Semua tabel dimodelkan ORM.
- **Frontend** memakai router library, struktur `pages/` + `components/`, layer API
  tersentralisasi, dan state management ringan. Tetap JavaScript (tidak ke TypeScript).
- **ETL** memisahkan ekstraksi, transformasi, dan load, dengan konfigurasi pembacaan
  workbook eksternal (tidak ada rentang hardcode).
- **Database** PostgreSQL dikelola Alembic; SQLite hanya dipakai untuk pengujian/ETL
  lokal jika diperlukan.

## 5. Cara membaca dokumen ini

1. Mulai dari [arsitektur-target.md](refactoring/arsitektur-target.md) untuk melihat
   bentuk akhir repo dan modul.
2. Baca [model-data.md](refactoring/model-data.md) karena hampir semua keputusan lain
   bergantung pada konsolidasi data.
3. Lanjut ke [backend.md](refactoring/backend.md) dan [frontend.md](refactoring/frontend.md)
   untuk detail per sisi.
4. Gunakan [migrasi-postgresql.md](refactoring/migrasi-postgresql.md) dan
   [peta-jalan.md](refactoring/peta-jalan.md) saat mulai eksekusi.

---

## Lampiran: pemetaan singkat masalah → solusi

| Masalah saat ini | Lokasi | Solusi yang diusulkan |
|---|---|---|
| Semua endpoint dalam satu file | `backend/app/features_api.py` | Pecah ke `routers/*` per domain (lihat backend.md). |
| Raw SQL di mana-mana | `features_api.py`, `main.py` | Model ORM lengkap + repository (lihat model-data.md, backend.md). |
| Tabel ganda legacy vs beranda | `master_seed.py`, `features.py` | Konsolidasi ke satu skema (lihat model-data.md). |
| Migrasi tanpa Alembic | `database.py`, `features.py` | Alembic + PostgreSQL (lihat migrasi-postgresql.md). |
| `App.jsx` 2292 baris | `frontend/src/App.jsx` | Pecah ke `pages/` + `components/` (lihat frontend.md). |
| Rentang hardcode ETL | `src/etl/pipeline.py` | Konfigurasi data-driven (lihat etl.md). |
| Secret default & CORS hardcode | `features_api.py`, `main.py` | Settings terpusat + validasi env (lihat auth-keamanan.md). |
| Pengujian tipis | `tests/`, `frontend/src/*.test.jsx` | Strategi pengujian + CI (lihat testing-ci.md). |
