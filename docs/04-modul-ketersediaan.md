# Tahap 4 - Modul Ketersediaan Data

## Implementasi

- Backend FastAPI + SQLAlchemy membaca `data/processed/sebatik.db`.
- Frontend React + Vite + Tailwind + Recharts menggunakan seluruh angka dari API.
- Build frontend dilayani FastAPI sehingga produksi dapat berjalan dalam satu proses.
- Design token warna status didefinisikan sekali di `frontend/src/tokens.js`.
- Nama PIC perorangan tidak masuk serialisasi atau ekspor publik.

## Endpoint

| Endpoint | Fungsi |
|---|---|
| `/api/v1/health` | Pemeriksaan layanan |
| `/api/v1/ringkasan` | Kartu ringkasan dan status |
| `/api/v1/matriks-ketersediaan` | Matriks kelompok x status |
| `/api/v1/indikator` | Pencarian, filter, urut, dan paginasi |
| `/api/v1/indikator-rawan` | Prioritas indikator rawan |
| `/api/v1/tim-pjk` | Beban empat Tim PJK |
| `/api/v1/ekspor.csv` | Ekspor CSV publik |
| `/api/v1/ekspor.xlsx` | Ekspor XLSX publik |
| `/api/docs` | Dokumentasi OpenAPI interaktif |

## Validasi

- Delapan test Python lulus, termasuk agregasi API, urutan kerawanan, parsing, dan privasi PIC.
- Test token warna frontend lulus.
- Build produksi Vite berhasil.
