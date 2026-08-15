# Peta Jalan Eksekusi & Kriteria Selesai

Dokumen ini mengurutkan fase eksekusi refactoring agar setiap fase berakhir dalam
keadaan aplikasi masih dapat dijalankan (strangler pattern), dengan rollback yang
jelas.

## 1. Prinsip urutan

1. Fondasi terlebih dahulu (settings, model, repository) sebelum memindahkan endpoint.
2. Konsolidasi data sebelum menyentuh alur verifikasi.
3. Setiap fase disertai tes; tidak ada fase yang "membekukan" fungsionalitas.

## 2. Fase eksekusi

### Fase 0 — Fondasi & pengukuran (tanpa perubahan perilaku)

- Pasang dependensi baru (`pydantic-settings`, `alembic`, `psycopg`), `pyproject.toml`
  (ruff/mypy), `requirements-dev.txt`.
- Buat `config.py` (Settings) dan arahkan `main.py`/`database.py` ke sana (nilai
  default sama seperti sekarang).
- Tambah test kontrak API (rekam bentuk respons saat ini) sebagai garis dasar.
- Tambah CI dasar (lint + test + build) — lihat testing-ci.md.
- **Selesai:** CI hijau; aplikasi jalan tanpa perubahan perilaku.

### Fase 1 — Model ORM lengkap + skema target

- Tulis model ORM untuk semua tabel target (model-data.md §3) di `models/`.
- Siapkan Alembic `baseline` untuk skema konsolidasi (belum memindahkan data).
- Tulis repository awal untuk query yang akan dipakai endpoint.
- **Selesai:** model + migrasi dapat dibuat pada database uji; test integrasi repo hijau.

### Fase 2 — Migrasi PostgreSQL + data

- Siapkan layanan PostgreSQL di compose; tulis `scripts/migrate_sqlite_to_postgres.py`.
- Jalankan ETL ulang data master + salin tabel tata kelola (migrasi-postgresql.md §4).
- Uji cutover di lingkungan uji; verifikasi jumlah baris & sampel nilai.
- **Selesai:** aplikasi berjalan di PostgreSQL dengan data lengkap; SQLite disimpan
  sebagai arsip.

### Fase 3 — Pemindahan endpoint ke router/service/repository

- Pindahkan endpoint per domain (backend.md §1) satu per satu, dimulai dari yang
  paling tidak berisiko (health, wilayah, indikator, ekspor), lalu beranda/explorer/
  capaian/insight/validitas, kemudian analitik, terakhir auth/admin/usulan/unggahan.
- Setiap pemindahan: hapus SQL mentah dari router; gunakan repository ORM; jalankan
  test kontrak.
- **Selesai:** `features_api.py` kosong dan dihapus; `main.py` hanya factory + router.

### Fase 4 — Konsolidasi alur verifikasi & unggahan

- Implementasikan `services/verifikasi.py` yang menulis ke **satu** `nilai_indikator`
  (backend.md §3).
- Pindahkan logika unggahan massal (staging + diff + persetujuan) ke service.
- **Selesai:** verifikasi tidak lagi menulis ke banyak tabel; uji alur end-to-end hijau.

### Fase 5 — Refactoring ETL data-driven

- Terapkan `workbook.yaml` + pemisahan extract/transform/load (etl.md).
- Pastikan test ETL dengan file asli tetap hijau.
- **Selesai:** tidak ada rentang hardcode bermakna bisnis.

### Fase 6 — Refactoring frontend

- Pecah `App.jsx` ke `pages/` + `components/` + `hooks/` + `api/` (frontend.md).
- Terapkan routing + Context auth/theme + layer API tersentralisasi.
- **Selesai:** `App.jsx` tipis; build + test UI hijau.

### Fase 7 — Keamanan & pengerasan

- Terapkan perbaikan auth-keamanan.md (secret wajib, rate limiting, proyeksi tanpa
  `password_hash`, CORS dari settings, header keamanan).
- Ganti backup SQLite → `pg_dump` dengan retensi.
- **Selesai:** checklist keamanan terpenuhi.

### Fase 8 — Pembersihan

- Hapus `features.py`, `master_seed.py`, dan kompatibilitas SQLite yang tidak terpakai.
- Perbarui dokumentasi (`README.md`, `docs/`, `AGENTS.md`) agar mencerminkan arsitektur
  baru.
- Keluarkan `data/raw` dan `data/processed/sebatik.db` dari version control.

## 3. Kriteria selesai (Definition of Done) keseluruhan

- [ ] Aplikasi berjalan di PostgreSQL dengan Alembic; tidak ada migrasi ad hoc.
- [ ] Satu model data konsolidasi (tidak ada tabel ganda); verifikasi menulis satu tabel.
- [ ] `features_api.py` dihapus; semua endpoint terpetakan ke router/service/repository.
- [ ] `App.jsx` < 150 baris; frontend memakai router + layer API terpusat.
- [ ] ETL data-driven; tidak ada rentang hardcode.
- [ ] Test kontrak API membuktikan kontrak publik tidak berubah.
- [ ] CI hijau: lint + type + test backend + test/build frontend.
- [ ] Checklist keamanan terpenuhi (auth-keamanan.md §8).
- [ ] Dokumentasi diperbarui.

## 4. Strategi rollback per fase

| Fase | Rollback |
|---|---|
| 0 | `git revert` (tidak ada perubahan perilaku). |
| 1–3 | Arahkan `SEBATIK_DATABASE_URL` kembali ke SQLite; kode lama masih ada sampai fase selesai. |
| 4–5 | Fitur gate/flag atau `git revert` modul; data konsolidasi dapat dibangun ulang dari ETL. |
| 6 | `git revert` frontend; backend tidak terpengaruh. |
| 7–8 | `git revert` + pulihkan `.env`; data PostgreSQL dipertahankan. |

## 5. Catatan akhir

Refactoring ini besar, tetapi dirancang agar dapat dihentikan dan dilanjutkan kapan
pun tanpa merusak sistem yang sedang berjalan. Prioritaskan Fase 0–3 (fondasi,
migrasi DB, pemindahan endpoint) sebagai pengembalian investasi tertinggi, dan lakukan
Fase 4 (verifikasi satu-tabel) sesegera mungkin karena merupakan sumber bug utama saat ini.
