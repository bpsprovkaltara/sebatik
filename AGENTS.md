# AGENTS.md — SEBATIK

Panduan kerja untuk agent AI dan developer yang mengerjakan repositori ini.

## Ringkasan proyek

SEBATIK adalah dasbor pemantauan **ketersediaan dan capaian data indikator ISV-IUP** untuk BPS Provinsi Kalimantan Utara. Aplikasi membaca basis data indikator dari file Excel/PDF, memuatnya ke database, dan menyajikannya lewat API serta antarmuka web dengan alur tata kelola berbasis peran.

- **Backend**: FastAPI + SQLAlchemy 2.0 + Alembic (`backend/`), API di `/api/v1`, dokumen OpenAPI di `/api/docs`. SQLite untuk pemasangan tunggal, PostgreSQL untuk pemakaian bersama.
- **Frontend**: React + Vite + Tailwind + Recharts (`frontend/`), routing `react-router-dom` (HashRouter), tanpa TypeScript.
- **ETL**: openpyxl + pdfplumber (`src/etl/`), data-driven lewat `src/etl/config/workbook.yaml`.
- **Domain**: indikator ISV (Indikator Sasaran Visi) dan IUP (Indikator Utama Pembangunan), 86 indikator, provinsi + 5 kabupaten/kota (kode wilayah `65`, `6501`–`6504`, `6571`).

## Perintah utama

Dijalankan dari root repositori (PowerShell pada Windows; macOS/Linux pakai setara).

```powershell
# Pasang & jalankan (skrip otomatis)
.\pasang-sebatik.ps1
.\jalankan-sebatik.ps1

# Basis data
python -m alembic -c backend/alembic.ini upgrade head
python -m alembic -c backend/alembic.ini downgrade -1
python -m backend.app.cli seed --tampilkan-sandi
python -m backend.app.cli periksa

# Pindahkan data dari pemasangan SQLite lama
python scripts/migrasi_ke_skema_target.py --periksa
python scripts/migrasi_ke_skema_target.py --jalankan

# Jalankan backend langsung
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Pengembangan frontend (proxy /api ke port 8000)
cd frontend
pnpm dev

# ETL (urutan penting: audit -> pipeline -> metadata)
python -m src.etl.audit data/raw/ISV-IUP_Provinsi_Kalimantan_Utara.xlsx
python -m src.etl.pipeline data/raw/ISV-IUP_Provinsi_Kalimantan_Utara.xlsx
python -m src.etl.metadata_pdf data/raw/BUKU_1_RPJPN_RPJPD_2025-2045.pdf

# Mutu kode
python -m pytest
python -m pytest --cov=backend/app --cov=src --cov-fail-under=80
ruff check . ; ruff format --check . ; mypy backend src
cd frontend ; pnpm lint ; pnpm test ; pnpm build
```

Dokumentasi API: `http://localhost:8000/api/docs`.

## Struktur direktori

| Path | Tanggung jawab |
|---|---|
| `backend/app/main.py` | Factory `create_app()`: middleware, exception handler, daftar router, mount build frontend. Tidak ada logika endpoint. |
| `backend/app/config.py` | `Settings` (pydantic-settings) — satu-satunya sumber konfigurasi, semua env berawalan `SEBATIK_`. |
| `backend/app/routers/` | Lapisan HTTP tipis, satu berkas per domain. Tanpa SQL, tanpa perhitungan, tanpa perulangan. |
| `backend/app/schemas/` | Skema Pydantic respons per domain. Setiap endpoint JSON memakainya sebagai `response_model`, sehingga kontraknya terdokumentasi di OpenAPI. |
| `backend/app/services/` | Aturan bisnis dan penyusunan muatan: beranda, explorer, capaian, insight, validitas, analitik, indikator, auth, pengguna, verifikasi, ketersediaan, ekspor, unggahan, bukti, pembatas laju. |
| `backend/app/repositories/` | Query ORM, satu fungsi per bentuk query. Satu-satunya tempat SQL boleh ada. |
| `backend/app/models/` | Model ORM skema konsolidasi + enum domain. |
| `backend/app/deps.py`, `security.py`, `middleware.py` | Dependency FastAPI, token/kata sandi, header keamanan. |
| `backend/app/cli.py` | Perintah `seed` dan `periksa`. |
| `backend/alembic/` | Migrasi skema. |
| `src/etl/` | `config/` (workbook.yaml + loader), `extract/`, `transform/`, `load/`, `pipeline.py` (orkestrator), `audit.py`, `metadata_pdf.py`. |
| `frontend/src/` | `App.jsx` (router saja), `api/` (client + endpoints), `pages/`, `components/` (`layout/`, `charts/`, `home/`, `explorer/`, `admin/`, `maps/`), `context/`, `hooks/`, `lib/`, `ui.jsx`, `tokens.js`, `Brand.jsx`, `styles.css`. |
| `scripts/` | `migrasi_ke_skema_target.py`, `backup_sqlite.py`, `run_local_server.py`, `generate_system_diagrams.py`. |
| `tools/` | `import_classified_workbook.py` (workbook klasifikasi → JSON master). |
| `tests/` | `unit/` (service murni, keamanan, aturan arsitektur), `api/` (kontrak), `integrasi/` (repository, migrasi, alur verifikasi), `etl/`. |
| `data/raw/`, `data/processed/` | **Tidak ter-commit.** Salin dari berbagi pakai kantor. |
| `docs/` | Dokumentasi 01–10, kamus data, dan `docs/refactoring/`. |

## Aturan arsitektur

```
routers  ->  services  ->  repositories  ->  models
 (HTTP)      (bisnis)       (query)          (ORM)
```

Arah ketergantungan tidak boleh berbalik. Aturan ini ditegakkan sebagai tes di
`tests/unit/test_arsitektur.py`, bukan sekadar konvensi:

- router tidak boleh memanggil `select()`, tidak boleh memuat perulangan, dan
  tidak boleh merakit dict respons lebih dari lima kunci — itu tanda muatan
  disusun di lapisan HTTP;
- service tidak boleh mengimpor FastAPI (penolakan dikembalikan sebagai
  `services.Penolakan`, router yang menerjemahkannya menjadi `HTTPException`);
- tidak boleh ada `text("...")` di luar `repositories/`;
- setiap domain endpoint harus punya berkas service-nya sendiri.

`tests/api/test_kontrak_openapi.py` melengkapinya dari sisi kontrak: setiap
endpoint JSON wajib punya `response_model`, dan skemanya harus berupa komponen
bernama di OpenAPI — bukan objek anonim.

## Konvensi kode

- Komentar dan pesan commit berbahasa Indonesia.
- Komentar menjelaskan **mengapa**, bukan sekadar mengulang kode.
- Backend: `from __future__ import annotations`, tipe `Mapped[...]` pada model SQLAlchemy 2.0, nama fungsi berbahasa Indonesia pada modul baru.
- Frontend: komponen fungsi, tanpa `class`. Halaman memanggil `api/endpoints.js`, tidak pernah `fetch` langsung.
- Nama tabel/kolom `snake_case`; nilai enum `SCREAMING_SNAKE_CASE` (mis. `MENUNGGU_VERIFIKASI`).
- Konstanta domain memakai enum di `backend/app/models/enums.py`, bukan literal string. Kode provinsi memakai `KODE_PROVINSI`, bukan `"65"`.

## Alur data & tata kelola

```
OPERATOR (wilayah) -> MENUNGGU_VERIFIKASI -> VERIFIKATOR/ADMIN -> DISETUJUI / DITOLAK
```

- Operator hanya mengirim nilai **realisasi** untuk wilayahnya dan wajib mengunggah bukti dukung.
- Verifikator bertugas di tingkat provinsi (`65`); tidak seorang pun boleh memverifikasi usulannya sendiri.
- Satu keputusan verifikasi menulis **satu** baris `nilai_indikator` dalam **satu** transaksi.
- Nilai wilayah baru muncul di dasbor publik setelah **DISETUJUI**; penolakan tidak mengubah angka publik.
- Admin mengelola akun, status akses, koreksi `arah_baik`, unggahan Excel massal (staging + diff + persetujuan), dan audit.

## Yang perlu diketahui sebelum mengubah

- **Satu tabel fakta.** `nilai_indikator` menampung nilai provinsi maupun wilayah, tahunan maupun periodik. `wilayah_kode` selalu terisi (`65` untuk provinsi, bukan NULL); `periode` NULL berarti nilai tahunan. Kunci alaminya dijaga **dua indeks unik parsial**, bukan satu UNIQUE — sebab NULL tidak pernah sama dengan NULL di SQL.
- **Satu daftar indikator.** Jalur ETL lama (`ISV-01`) sudah dibuang; yang berlaku adalah daftar master (`ISV-001`). Latar keputusannya di `docs/refactoring/CATATAN-PELAKSANAAN.md`.
- **`arah_baik` belum lengkap.** 63 dari 86 indikator belum punya arah baik terverifikasi, sehingga capaiannya berstatus `BELUM_ADA_DATA`. Diisi lewat `PUT /api/v1/arah-baik/{id}`. Ini kondisi data, bukan bug.
- **Skema hanya lewat Alembic.** Tidak ada migrasi atau seed yang berjalan saat modul diimpor. Jangan menambahkannya kembali.
- **ETL data-driven.** Jangan menambahkan nomor baris/kolom atau rentang tahun ke kode; tempatnya di `src/etl/config/workbook.yaml`.
- **Kontrak API.** `tests/api/test_kontrak.py` menjaga bentuk respons publik. Bila kontrak memang perlu berubah, ubah tesnya dalam commit yang sama beserta alasannya.
- **Tautan frontend.** Rute didefinisikan di `frontend/src/lib/rute.js`. Tautan hash lama (`#capaian`) masih dialihkan otomatis; jangan membuat tautan baru dalam bentuk itu.
- **Sesi dua token.** Token akses berumur 2 jam dan dikirim di header `Authorization`; sesi disambung token segar berumur 24 jam yang hidup sebagai cookie httpOnly di `/api/v1/auth`. `api/client.js` menyegarkan sekali saat 401 lalu mengulang permintaan — jangan menambahkan penanganan 401 sendiri di halaman. Keluar harus lewat `keluarSesi()` supaya cookie segar ikut dihapus.
- **Rotasi rahasia.** `SEBATIK_SECRET_KEYS` menampung kunci lama yang masih diterima saat memverifikasi token. Token baru selalu ditandatangani `SEBATIK_SECRET_KEY` yang aktif.

## Pengujian

- Backend: `python -m pytest` (427 tes, cakupan 82%). Tes kontrak berjalan di atas benih uji sendiri sehingga tidak memerlukan `data/`.
- CI menjalankan `pytest --cov=backend/app --cov=src --cov-fail-under=80`; menurunkan cakupan di bawah 80% membuat CI merah.
- Tiga tes memerlukan berkas nyata dan melewatkan dirinya bila `data/` kosong: integrasi ETL dan dua regresi isi beranda.
- Frontend: `pnpm test` (Vitest) dan `pnpm lint` di `frontend/`.
- CI (`.github/workflows/ci.yml`) menjalankan ruff, mypy, migrasi Alembic naik-turun terhadap PostgreSQL sungguhan, pytest, serta lint/test/build frontend.

## Riwayat refactoring

Refactoring menyeluruh (Fase 0–8) sudah dijalankan: konsolidasi model data,
Alembic, pemisahan router/service/repository, ETL data-driven, pemecahan
`App.jsx`, dan pengerasan keamanan. Rencananya ada di `docs/refactoring/`;
keputusan dan temuan yang berbeda dari rencana dicatat di
`docs/refactoring/CATATAN-PELAKSANAAN.md`. Baca berkas itu lebih dulu sebelum
melakukan perubahan struktural besar.
