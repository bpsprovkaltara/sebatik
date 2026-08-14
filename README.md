# SEBATIK

Dasbor Pemantauan Ketersediaan dan Capaian Data Indikator ISV-IUP untuk BPS Provinsi Kalimantan Utara.

## Menjalankan aplikasi

Persyaratan: Python 3.11+ dan Node.js 20+. `pnpm` bersifat opsional; skrip otomatis memakai `npm` jika pnpm tidak tersedia.

```powershell
.\pasang-sebatik.ps1
.\jalankan-sebatik.ps1
```

Buka `http://localhost:8000`. Dokumentasi API tersedia di `http://localhost:8000/api/docs`. Hentikan dengan `Ctrl+C`.

Akun awal adalah `admin` / `Sebatik-Ganti-Segera-2026!`. Ganti segera sebelum dipakai di lingkungan kerja.

## Tata kelola data

Backend menggunakan alur `OPERATOR -> MENUNGGU_VERIFIKASI -> VERIFIKATOR -> DISETUJUI/DITOLAK`.
Operator hanya dapat mengirim data wilayahnya dan wajib mengunggah bukti dukung. Nilai per wilayah
baru tersedia untuk dashboard setelah disetujui; penolakan tidak mengubah angka publik. Admin
mengelola akun, status akses, wilayah, unggahan massal, dan audit.

Wilayah awal mencakup Provinsi Kalimantan Utara, Bulungan, Malinau, Nunukan, Tana Tidung, dan
Tarakan. Migrasi menyiapkan dua akun operator per wilayah dengan pola `operator.<kode>.<1|2>`.
Kata sandi awal akun seed adalah `Sebatik-Operator-Ganti-2026!` dan wajib diganti saat login pertama.

Untuk pengembangan frontend, jalankan `pnpm dev` di folder `frontend`; permintaan `/api` akan diteruskan ke FastAPI pada port 8000.

## Memperbarui data

```powershell
python -m src.etl.audit data/raw/ISV-IUP_Provinsi_Kalimantan_Utara.xlsx
python -m src.etl.pipeline data/raw/ISV-IUP_Provinsi_Kalimantan_Utara.xlsx
python -m src.etl.metadata_pdf data/raw/BUKU_1_RPJPN_RPJPD_2025-2045.pdf
```

Urutan tersebut penting karena Tahap 3 mengisi tabel metadata yang dibuat ulang oleh Tahap 2. File sumber tidak dimodifikasi.

## Pengujian

```powershell
python -m pytest -q
Set-Location frontend
pnpm test
pnpm build
```

Data PIC perorangan tersimpan di tabel privat `penugasan_pic` dan tidak tersedia melalui endpoint publik.
