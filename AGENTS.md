# AGENTS.md — SEBATIK

Panduan kerja untuk agent AI dan developer yang mengerjakan repositori ini.

## Ringkasan proyek

SEBATIK adalah dasbor pemantauan **ketersediaan dan capaian data indikator ISV-IUP** untuk BPS Provinsi Kalimantan Utara. Aplikasi membaca basis data indikator dari file Excel/PDF, memuatnya ke database, dan menyajikannya lewat API serta antarmuka web dengan alur tata kelola berbasis peran.

- **Backend**: FastAPI + SQLAlchemy + SQLite (`backend/`), API di `/api/v1`, dokumen OpenAPI di `/api/docs`.
- **Frontend**: React + Vite + Tailwind + Recharts (`frontend/`), tanpa router library (navigasi berbasis hash), tanpa TypeScript.
- **ETL**: openpyxl + pdfplumber (`src/etl/`).
- **Domain**: indikator ISV (Indikator Sasaran Visi) dan IUP (Indikator Utama Pembangunan), 86 indikator, provinsi + 5 kabupaten/kota (kode wilayah `65`, `6501`–`6504`, `6571`).

## Perintah utama

Dijalankan dari root repositori (PowerShell pada Windows sesuai panduan; macOS/Linux pakai setara).

```powershell
# Pasang & jalankan (skrip otomatis)
.\pasang-sebatik.ps1
.\jalankan-sebatik.ps1

# Jalankan backend langsung
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Pengembangan frontend (proxy /api ke port 8000)
cd frontend
pnpm dev        # atau: npm run dev
pnpm build      # atau: npm run build

# ETL (urutan penting: audit -> pipeline -> metadata)
python -m src.etl.audit data/raw/ISV-IUP_Provinsi_Kalimantan_Utara.xlsx
python -m src.etl.pipeline data/raw/ISV-IUP_Provinsi_Kalimantan_Utara.xlsx
python -m src.etl.metadata_pdf data/raw/BUKU_1_RPJPN_RPJPD_2025-2045.pdf

# Tes
python -m pytest -q
cd frontend && pnpm test

# Backup SQLite sekali jalan
python scripts/backup_sqlite.py
```

Dokumentasi API: `http://localhost:8000/api/docs`.

## Struktur direktori

| Path | Tanggung jawab |
|---|---|
| `backend/app/main.py` | Aplikasi FastAPI, CORS, endpoint `/api/v1/indikator` + ekspor CSV/XLSX, mount build frontend. |
| `backend/app/features_api.py` | Router `/api/v1` berisi HAMPIR SEMUA endpoint lain (auth, beranda, explorer, capaian, insight, validitas, analitik, usulan/verifikasi, admin, unggahan, unduhan). |
| `backend/app/models.py` | Model ORM SQLAlchemy (hanya 3 tabel legacy: `indikator`, `nilai_indikator`, `metadata_indikator`). |
| `backend/app/database.py` | Engine, session, `get_db`, dan pemicu migrasi/seed otomatis saat import. |
| `backend/app/master_seed.py` | Skema + seed tabel `beranda_*` dari `data/raw/basis_data_indikator_isv_iup_kaltara.json`. |
| `src/etl/` | Pipeline ETL: `audit.py`, `pipeline.py`, `metadata_pdf.py`, `features.py` (migrasi fitur/governance), `common.py`, `arah_baik.py`, `units.py`. |
| `frontend/src/` | `App.jsx` (2292 baris, SEMUA halaman+komponen), `api.js`, `auth.js`, `theme.js`, `tokens.js`, `Brand.jsx`, `ui.jsx`, `styles.css`. |
| `scripts/` | `backup_sqlite.py`, `run_local_server.py`, `seed_master_dashboard.py`, `generate_system_diagrams.py`. |
| `tools/` | Utilitas impor/verifikasi workbook klasifikasi. |
| `tests/` | pytest (backend + ETL). |
| `data/raw/` | Sumber: Excel ISV-IUP, PDF metadata, JSON basis data, GeoJSON. |
| `data/processed/` | `sebatik.db` + cadangan CSV + arsip unggahan + bukti dukung. |
| `docs/` | Dokumentasi nomor 01–10 + kamus data, keterbatasan, panduan. |

## Konvensi kode

- Komentar dan pesan commit berbahasa Indonesia.
- Komentar menjelaskan **mengapa**, bukan sekadar mengulang kode.
- Backend: gaya ringkas, gunakan `from __future__ import annotations`, tipe `Mapped[...]` pada model SQLAlchemy 2.0.
- Frontend: komponen fungsi, tidak ada `class`, state lokal + pola pub/sub sederhana (`auth.js`, `theme.js`).
- Nama tabel/kolom database memakai `snake_case`; nilai enum memakai `SCREAMING_SNAKE_CASE` (mis. `MENUNGGU_VERIFIKASI`, `DISETUJUI`, `DITOLAK`).

## Alur data & tata kelola

```
OPERATOR (wilayah) -> MENUNGGU_VERIFIKASI -> VERIFIKATOR/ADMIN -> DISETUJUI / DITOLAK
```

- Operator hanya mengirim nilai **realisasi** untuk wilayahnya dan wajib mengunggah bukti dukung.
- Verifikator bertugas di tingkat provinsi (`65`).
- Nilai wilayah baru muncul di dasbor publik setelah **DISETUJUI**; penolakan tidak mengubah angka publik.
- Admin mengelola akun, status akses, wilayah, koreksi `arah_baik`, unggahan Excel massal (staging + diff + persetujuan), dan audit.

## Gotcha penting

- **Dua keluarga tabel paralel**: legacy ETL (`indikator`, `nilai_indikator`, `metadata_indikator`) dan master `beranda_*`. Endpoint analitik lama membaca tabel legacy; beranda/explorer membaca `beranda_*`. Verifikasi usulan menulis ke BANYAK tabel sekaligus. Jangan menambah tabel baru tanpa memahami keduanya.
- **Migrasi tanpa Alembic**: `backend/app/database.py` memanggil `migrate_governance()` + `seed_verified_master()` saat import. Skema diubah lewat `ALTER TABLE ... ADD COLUMN` dan rebuild manual. Lihat `docs/refactoring/` untuk rencana migrasi ke PostgreSQL + Alembic.
- **86 indikator**: `pipeline.py` menolak workbook yang tidak menghasilkan tepat 86 indikator.
- **Kode wilayah `"65"`** adalah provinsi (akar), tersebar sebagai literal string di banyak tempat.
- **`SEBATIK_SECRET_KEY`** wajib diganti sebelum produksi (default `GANTI-SECRET-INI-...` ada di `features_api.py`). Akun awal `admin` / `Sebatik-Ganti-Segera-2026!`.
- **File mentah ter-commit ke git**: `data/raw/*` dan `data/processed/sebatik.db` ada di repo. Pertimbangkan mengecualikannya dari version control.
- **CORS hardcoded** hanya untuk `localhost:5173` di `main.py`.

## Pengujian

- Backend: `python -m pytest -q` (lihat `tests/`). Tes ETL memakai file asli `data/raw/ISV-IUP_Provinsi_Kalimantan_Utara.xlsx`.
- Frontend: `pnpm test` (Vitest) di `frontend/`.
- Cakupan saat ini tipis — lihat `docs/refactoring/testing-ci.md` untuk target yang diinginkan.

## Refactoring yang sedang berjalan

Proyek ini sedang direncanakan untuk refactoring menyeluruh (migrasi ke PostgreSQL, pemisahan backend/frontend/ETL, konsolidasi model data). Spesifikasi lengkap ada di `docs/refactoring.md` beserta dokumen pendukung di `docs/refactoring/`. Bacalah dokumen tersebut sebelum melakukan perubahan struktural besar.
