# Keterbatasan SEBATIK

- Data saat ini berfokus pada tingkat Provinsi Kalimantan Utara; belum tersedia seri lengkap kabupaten/kota.
- Sebagian indikator menggunakan proxy. Dasbor tidak menganggap proxy sama dengan indikator asli.
- `arah_baik` saat ini berasal dari heuristik yang disetujui sementara dan masih dapat dikoreksi admin. Status capaian berubah bila arah diperbaiki.
- Status capaian hanya dihitung jika realisasi dan target pada tahun yang sama tersedia. Kekosongan tidak diubah menjadi nol.
- Required run-rate memakai ekstrapolasi linear sederhana, bukan proyeksi resmi.
- Korelasi tidak membuktikan sebab-akibat dan disembunyikan saat pasangan tahun kurang dari empat.
- Riwayat monev ketersediaan baru terbentuk sejak snapshot mulai dicatat; sistem tidak mengarang riwayat masa lalu.
- Parser rumus PDF mempertahankan teks ekstraksi yang mungkin rusak dan menandainya untuk verifikasi manual.
- Autentikasi lokal cocok untuk server internal sederhana, bukan pengganti SSO organisasi.
