# Panduan Operasional SEBATIK

Panduan ini ditujukan bagi pegawai yang terbiasa memakai terminal, tetapi tidak harus memahami pemrograman.

## Pemasangan lokal

1. Pasang Python 3.11 atau lebih baru dan Node.js 20 atau lebih baru. Skrip memakai pnpm jika tersedia, atau npm sebagai fallback.
2. Buka PowerShell di folder SEBATIK.
3. Jalankan:

```powershell
python -m venv .venv-sebatik
.\.venv-sebatik\Scripts\python.exe -m pip install -r requirements.txt
Set-Location frontend
npm install
npm run build
Set-Location ..
.\.venv-sebatik\Scripts\python.exe -m src.etl.features
```

Nama `.venv-sebatik` sengaja dipisahkan dari virtual environment lama yang mungkin rusak.

## Menjalankan

```powershell
.\.venv-sebatik\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Buka `http://localhost:8000`. Dokumentasi API ada di `/api/docs`.

## Menghentikan

Kembali ke jendela PowerShell yang menjalankan SEBATIK, lalu tekan `Ctrl+C` satu kali.

## Akun awal

- Username: `admin`
- Kata sandi: `Sebatik-Ganti-Segera-2026!`

Kredensial tersebut hanya untuk pemasangan awal dan **wajib diganti sebelum sistem dipakai di lingkungan kerja**. Ganti juga `SEBATIK_SECRET_KEY` di `.env`.

## Backup dan pemulihan

Backup sekali jalan:

```powershell
.\.venv-sebatik\Scripts\python.exe scripts\backup_sqlite.py
```

Untuk memulihkan, hentikan aplikasi, simpan database bermasalah, salin file backup terpilih menjadi `data/processed/sebatik.db`, lalu jalankan aplikasi kembali.
