# SEBATIK: Dari Pencarian Manual ke Pemantauan Satu Layar

## Masalah

Data 86 indikator ISV-IUP tersebar dalam lima sheet dengan header bertingkat, angka bertipe teks, nama berbeda, dan banyak kekosongan. Menjawab pertanyaan sederhana seperti “indikator mana yang belum memiliki data?” sebelumnya memerlukan pemeriksaan dan penyaringan Excel secara manual.

## Yang dibangun

SEBATIK menyatukan sumber tersebut ke basis data yang dapat ditelusuri, menampilkan ketersediaan, capaian, metadata, tren, target, dan beban Tim PJK. Sistem menyediakan unggah Excel dengan pratinjau, form usulan nilai dan verifikasi, audit log, autentikasi berbasis peran, serta paket unduhan data.

## Perubahan proses

**Sebelum:** membuka beberapa sheet, memahami struktur, menyaring status, dan memeriksa tahun satu per satu.
**Sesudah:** daftar indikator rawan dan filter ketersediaan tersedia sekali klik. Tidak dicantumkan angka penghematan waktu yang belum pernah diukur; pengukuran baseline dan waktu penggunaan nyata disarankan pada uji coba operasional.

## Angka utama

- 86 indikator: 10 ISV dan 76 IUP.
- 666 fakta nilai unik pada ETL awal.
- 42 indikator belum memiliki satu pun realisasi pada sumber awal.
- 64 metadata cocok otomatis dengan Buku 1; sisanya memerlukan fallback/review.

## Keberlanjutan

Tetapkan admin data, verifikator tiap Tim PJK, jadwal pembaruan, koreksi `arah_baik`, pemeriksaan indikator proxy, backup harian, uji pemulihan berkala, dan evaluasi integrasi SSO bila sistem diperluas.
