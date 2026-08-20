# Changelog

## Belum Dirilis

### Tahap 1 - Audit sumber data

- Menambahkan audit otomatis lima sheet, termasuk deteksi header/merged cell, tipe data, sel kosong, anomali angka dan teks, serta pemetaan indikator antar-sheet.
- Menambahkan laporan `docs/01-audit-data.md` dan test fungsi normalisasi dasar.

### Tahap 2 - Pipeline ETL

- Menambahkan pipeline lima sheet ke SQLite dengan 86 indikator, fakta long berprovenans, metadata kosong untuk Tahap 3, dan tabel PIC privat.
- Menambahkan cadangan CSV, upaya ekspor Parquet, laporan validasi parsing/integritas, serta test transformasi.

### Tahap 3 - Metadata Buku 1

- Menambahkan ekstraksi teks per halaman, pemisahan bagian sebelum sub-bab 2.3, parser kartu enam field, dan pencocokan fuzzy satu-ke-satu.
- Mengisi metadata resmi/fallback BPS Kaltara, menyimpan rumus mentah untuk verifikasi manual, serta menghasilkan laporan cakupan dan CSV review.

### Tahap 4 - Modul Ketersediaan Data

- Menambahkan API FastAPI/SQLAlchemy, dokumentasi `/api/docs`, ekspor CSV/XLSX, agregasi matriks, indikator rawan, dan beban Tim PJK.
- Menambahkan dashboard React/Vite/Tailwind/Recharts yang responsif dengan token warna status terpusat serta filter interaktif.
- Menambahkan test backend/frontend, build produksi, panduan instalasi, dan satu proses produksi untuk API serta frontend.

### Tahap 5A - Heuristik arah capaian

- Menambahkan kolom `arah_baik` dan pengaman `arah_baik_terverifikasi` pada dimensi indikator.
- Menghasilkan `docs/05-arah-baik.csv` untuk verifikasi manual 86 indikator; status capaian belum dihitung sebelum verifikasi selesai.
- Menambahkan test heuristik arah NAIK/TURUN untuk indikator contoh.

### Tahap 5B - Modul capaian

- Menambahkan daftar kartu, sparkline, detail realisasi-target, metadata, tata kelola, tabel nilai, unduhan per indikator, dan status capaian yang tidak mengubah data kosong menjadi 0%.
- Mengaktifkan arah heuristik sebagai nilai sementara yang dapat dikoreksi dan diaudit.

### Tahap 6 - Analitik lanjutan

- Menambahkan analitik YoY, peringkat, gap target, required run-rate, multi-seri, korelasi Pearson dengan batas n, serta snapshot ketersediaan.
- Menambahkan disclaimer ekstrapolasi dan korelasi pada API/UI.

### Tahap 7 - Jalur masuk data

- Menambahkan autentikasi Argon2/JWT berbasis peran, koreksi arah, pengguna PIC per tim, form usulan dan persetujuan nilai, audit log, serta unggah Excel berarsip dengan staging/diff/persetujuan.
- Menambahkan paket ekspor ZIP berisi CSV dan katalog metadata XLSX/PDF.

### Tahap 8 - Serah terima

- Memperluas test kontrak API dan aturan analitik, menambahkan dokumentasi pengguna/operasional/kamus/keterbatasan/deployment, serta tangkapan layar.
- Menambahkan Dockerfile, Docker Compose, health check, backup SQLite harian dengan retensi, dan ringkasan paparan satu halaman.

### Tahap 9 - Identitas visual dan redesain frontend

- Membangun ulang antarmuka sebagai app shell bersidebar dengan bilah atas berlatar kaca, kepala halaman bermotif kawung, dan tata letak bento; seluruh endpoint serta kontrak API tidak berubah.
- Menetapkan identitas SEBATIK sebagai "Beranda Data Kalimantan Utara" beserta logo SVG, palet laut-fajar, dan tangga warna status yang ordinal.
- Mengganti Georgia dengan Plus Jakarta Sans dan JetBrains Mono yang dibundel lokal sehingga tampilan tetap benar tanpa akses internet.
- Menambahkan mode terang/gelap dengan preferensi tersimpan, kerangka muat berkilau, dan penghormatan pada `prefers-reduced-motion`.
- Menambahkan `docs/09-panduan-visual.md` sebagai acuan token warna, tipografi, dan struktur halaman.

### Rumus metadata dalam bentuk LaTeX

- Menambahkan `data/processed/rumus_latex_buku1.json`: bentuk LaTeX dan keterangan notasi rumus untuk 86 indikator, diturunkan dari Bagian 2.3 Buku 1. 68 indikator memperoleh rumus; 18 sisanya memang tidak memuat rumus tertutup di buku, dan 12 di antara yang berumus disusun dari kalimat definisi karena formula aslinya tercetak sebagai gambar sehingga ditandai perlu verifikasi manual.
- Menambahkan `scripts/perbarui_rumus_latex.py` yang memasang berkas itu ke `metadata_indikator`. Teks hasil ekstraksi PDF tetap tersimpan di `rumus_mentah` sebagai jejak audit; kolom `rumus` kini menampung keterangan notasi.
- Melepas daftar rumus bawaan yang ditulis langsung di `services/indikator.py` - ia hanya menutup lima indikator dan tidak punya rujukan halaman.
- Menampilkan rumus di modal metadata sebagai rumus matematis KaTeX beserta keterangan notasi, rujukan halaman buku, dan penanda bagi rumus yang masih perlu diverifikasi.

### Perapian beranda, insight, dan kartu tren

- Angka realisasi pada kartu sasaran visi memakai perlakuan angka kartu makro — ukuran, tracking rapat, angka tabular — dengan berat diturunkan agar tidak menenggelamkan nama indikator; lebar lajurnya dikunci supaya desimal antarbaris sejajar, dan "Belum tersedia" tidak lagi tampil sebesar angka.
- Menambahkan kartu target akhir 2045 pada tracker halaman Capaian, berdampingan dengan realisasi dan target 2029 sehingga cincin progres lima tahunan punya konteks tujuan akhirnya.
- Mengganti label kelompok `indikator_induk` dari "Indikator Utama Induk" menjadi "Indikator Utama Pembangunan".
- Rincian ISV/IUP pada tracker ketersediaan dibaca sebagai satu pernyataan: nama kelompok berdampingan dengan persentasenya yang ditebalkan, disusul "7 dari 10 indikator telah tersedia".
- Insight otomatis memisahkan interpretasi indikator ke paragrafnya sendiri, bukan menyambungkannya ke cerita angka.
- Satuan pada kartu tahun tren Insight turun ke barisnya sendiri dengan ukuran keterangan, sehingga lima kartu tahun muat tanpa perlu digeser mendatar.

### Perapian kepala halaman dan label

- Kalimat kepala halaman kini satu baris rata tengah dengan jarak antarkata normal, menggantikan blok sempit 44ch yang patah jadi dua-tiga baris di tengah bidang yang masih lapang. Ukurannya dikunci agar kalimat terpanjang di antara semua halaman tetap muat satu baris. Titik penutup dilepas dari kelima kalimatnya.
- Halaman Insight: kalimat ajakan "Pilih kartu untuk melihat tren dan perbandingan wilayah" dilepas, dan keterangan sumber diringkas jadi "Sumber Data: ..." tanpa pengampu.
- Judul cincin ketersediaan beranda menjadi "Ketersediaan Data Tahun ...".
