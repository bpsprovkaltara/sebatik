# Panduan Operasional SEBATIK

Panduan ini ditujukan bagi pegawai yang terbiasa memakai terminal, tetapi tidak harus memahami pemrograman.

## Pemasangan lokal

1. Pasang Python 3.11 atau lebih baru dan Node.js 20 atau lebih baru. Skrip memakai pnpm jika tersedia, atau npm sebagai fallback.
2. Salin isi `data/raw/` dari berbagi pakai kantor (berkas mentah tidak disertakan di repositori).
3. Buka PowerShell di folder SEBATIK.
4. Jalankan:

```powershell
.\pasang-sebatik.ps1
```

Skrip itu membuat virtual environment, memasang dependensi, membangun frontend,
menerapkan skema basis data, lalu membuat akun awal.

Nama `.venv-sebatik` sengaja dipisahkan dari virtual environment lama yang mungkin rusak.

## Menjalankan

```powershell
.\jalankan-sebatik.ps1
```

Buka `http://localhost:8000`. Dokumentasi API ada di `/api/docs`.

## Menghentikan

Kembali ke jendela PowerShell yang menjalankan SEBATIK, lalu tekan `Ctrl+C` satu kali.

## Akun awal

`pasang-sebatik.ps1` mencetak daftar akun beserta sandinya **satu kali saja**.
Sandi itu dibuat acak dan tidak tersimpan di mana pun dalam bentuk terbaca, jadi
catat saat itu juga dan bagikan lewat kanal aman.

Bila sandi terlanjur hilang, admin dapat mereset lewat panel Manajemen Akses,
atau akun dibuat ulang dengan menghapusnya lebih dulu. Semua akun awal wajib
mengganti sandi saat login pertama.

Ganti juga `SEBATIK_SECRET_KEY` di `.env`. Pada `SEBATIK_ENVIRONMENT=production`,
aplikasi menolak berjalan bila kuncinya masih bawaan atau lebih pendek dari 32 karakter.

Untuk melihat akun apa saja yang ada:

```powershell
.\.venv-sebatik\Scripts\python.exe -m backend.app.cli periksa
```

## Backup dan pemulihan

### PostgreSQL (dianjurkan untuk pemakaian bersama)

`docker compose up -d` sudah menjalankan `pg_dump` harian ke volume `sebatik_backup`
dengan retensi 30 berkas. Memulihkan satu berkas dump:

```powershell
docker compose exec db pg_restore -U sebatik -d sebatik --clean /backup/sebatik-YYYYMMDD-HHMMSS.dump
```

### SQLite (pemasangan tunggal)

```powershell
.\.venv-sebatik\Scripts\python.exe scripts\backup_sqlite.py
```

Untuk memulihkan, hentikan aplikasi, simpan database bermasalah, salin file backup terpilih menjadi `data/processed/sebatik.db`, lalu jalankan aplikasi kembali.

## Pindah ke PostgreSQL

Lihat langkah lengkap beserta urutan cutover dan cara rollback di
[refactoring/CATATAN-PELAKSANAAN.md](refactoring/CATATAN-PELAKSANAAN.md).
