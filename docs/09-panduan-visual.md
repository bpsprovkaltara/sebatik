# Panduan Visual SEBATIK

Dokumen ini merangkum identitas visual dasbor SEBATIK. Seluruh keputusan di sini hanya menyentuh lapisan frontend; kontrak API dan skema basis data tidak berubah.

## Gagasan merek

SEBATIK meminjam nama Pulau Sebatik di Kabupaten Nunukan, Kalimantan Utara — pulau perbatasan yang dikenal sebagai beranda negeri. Gagasan itu dipakai secara harfiah: dasbor ini adalah beranda data provinsi, tempat mutu data dijaga sebelum dipakai untuk perencanaan.

- Nama panjang: **Sistem Evaluasi dan Basis Analitik Terpadu Indikator Kaltara**
- Tagline: **Beranda Data Kalimantan Utara**
- Kalimat pendamping: "Sebatik menjaga batas negeri; dasbor ini menjaga batas mutu datanya."

Nama SEBATIK juga bersinggungan dengan kata *batik*. Motif kawung yang disederhanakan dipakai sebagai lapisan latar bertransparansi rendah pada kepala halaman dan kartu identitas di sidebar. Motif dirender sebagai SVG inline (`src/Brand.jsx`), bukan berkas gambar, sehingga tetap tajam di layar mana pun dan tidak menambah permintaan jaringan.

## Warna

Palet resmi terdiri atas enam warna hangat — persik, mawar, dua netral pasir, karang, dan arang.

| Peran | Nilai | Pemakaian |
| --- | --- | --- |
| Primer (persik) | `#FEBE98` | Logo, judul, latar |
| Primer (mawar) | `#DF7F83` | Logo, judul, tombol, latar |
| Netral (pasir) | `#F0CFBA` | Latar |
| Netral (krem) | `#F2E9D9` | Latar halaman |
| Aksen (karang) | `#FA7472` | Tombol dan bagian yang harus menonjol |
| Teks (arang) | `#464646` | Seluruh teks |

Enam warna itu tidak cukup untuk seluruh sistem, dan sebagian tidak lolos ambang baca. Karena itu berlaku satu aturan turunan: **hanya kepekatan yang boleh diubah, rona tidak pernah ditambah.** Tidak ada biru, hijau, atau ungu di mana pun.

Contoh yang wajib diketahui: mawar `#DF7F83` hanya mencapai 2,9:1 di atas permukaan terang. Untuk peran yang memikul teks — `--brand`, kicker, tautan — ia dipekatkan menjadi `#B45360` (4,7:1). Di mode gelap warna palet dipakai apa adanya karena justru di sanalah ia paling terbaca, dan peran merek berpindah ke persik `#FEBE98`.

### Warna data

Ketersediaan memakai tangga ordinal satu keluarga; makin pekat berarti makin rinci.

| Status | Terang | Gelap |
| --- | --- | --- |
| Tersedia s.d Kabupaten/Kota | `#C4626B` | `#FEBE98` |
| Tersedia s.d Provinsi | `#DF7F83` | `#DF7F83` |
| Tersedia Nasional | `#FEBE98` | `#C4626B` |
| Tidak Tersedia | `#FA7472` | `#FA7472` |
| Belum Tersedia | `#A79C95` | `#8B7B73` |

Capaian: `TERCAPAI` mawar, `MENDEKATI` persik pekat, `PERLU_PERHATIAN` karang, `BELUM_ADA_DATA` abu hangat.

> **Peringatan yang tidak boleh dihapus.** Palet ini tidak memuat hijau, sehingga `TERCAPAI` dan `PERLU_PERHATIAN` hanya terpisah oleh kepekatan, bukan oleh rona. Pada penglihatan protanopia dan deuteranopia keduanya nyaris berimpit. Label teks pada `CapaianBadge`, `VizLegend`, dan posisi batang terhadap garis nol karena itu bukan pelengkap melainkan satu-satunya pembawa makna yang bertahan. Jangan pernah menyajikan status hanya dengan warna.

Ambang kontras yang dipenuhi seluruh token: teks 9,2:1, teks sekunder 4,9:1, warna merek 4,7:1, teks di atas hero 5,3:1, dan setiap seri grafik minimal 3,6:1 terhadap permukaannya.

Seluruh nilai terpusat di `frontend/src/tokens.js`. Warna permukaan, garis, dan teks berada di `frontend/src/styles.css` sebagai variabel CSS.

## Mode terang dan gelap

Tema tersimpan di `localStorage` dengan kunci `sebatik_theme`. Kunjungan pertama mengikuti `prefers-color-scheme` sistem. Skrip kecil di `index.html` menetapkan `data-theme` sebelum React dimuat sehingga tidak ada kedipan warna. Tombol pengubah tema berada di bilah atas.

Warna status dipilih agar kontras memadai pada kedua permukaan sehingga grafik tidak perlu palet terpisah.

## Tipografi

| Peran | Huruf |
| --- | --- |
| Antarmuka dan judul | Plus Jakarta Sans Variable |
| Angka, ID indikator, tabel | JetBrains Mono Variable |

Plus Jakarta Sans dipilih karena dirancang di Indonesia dan memberi karakter lokal tanpa mengorbankan keterbacaan pada ukuran kecil. JetBrains Mono dipakai untuk angka karena lebarnya tetap, sehingga kolom metrik dan tabel tetap lurus.

Kedua huruf dipasang sebagai dependensi npm (`@fontsource-variable/*`) dan ikut dibundel saat build. Tidak ada permintaan ke server luar, sehingga dasbor tetap tampil benar di jaringan kantor yang tertutup.

Serif Georgia pada versi sebelumnya dilepas seluruhnya.

## Logo

Logo SEBATIK berupa cakram: peta Kalimantan Utara bermotif Dayak berwarna biru, diapit batang statistik dan anak panah menanjak berwarna amber. Berkas sumber ada di `logo/logo.png`; turunan yang dipakai aplikasi dibangkitkan ke `frontend/public/`:

| Berkas | Ukuran | Pemakaian |
| --- | --- | --- |
| `logo-sebatik.png` | 384 px | Bilah atas, kepala beranda, kaki halaman |
| `apple-touch-icon.png` | 180 px | Ikon layar utama iOS |
| `favicon.png` | 64 px | Ikon tab peramban |

Wadah logo pada bilah atas berbentuk lingkaran berlatar putih di kedua mode. Piringan putih dipertahankan pada mode gelap supaya peta biru tua di dalam logo tidak lebur dengan latar bilah.

## Kepala halaman Beranda

Beranda memakai kepala halaman tersendiri (`.home-hero`), bukan kartu `<Shell>` seperti halaman lain, karena perannya memperkenalkan sistem alih-alih menamai bagian. Susunannya: logo besar dan nama sistem di kiri, kalimat pengantar beserta tagline amber di kanan, lalu empat kartu pintu masuk berlatar putih yang menumpuk di tepi bawahnya.

Foto latar bersifat **opsional**. Letakkan berkas di `frontend/public/hero-beranda.jpg` dan ia akan otomatis terpakai di bawah lapisan kabut biru. Bila berkas tidak ada, elemen gambar dilepas sendiri oleh React sehingga yang tampil hanyalah gradasi laut, aura, dan motif kawung — tanpa kotak gambar rusak. Ukuran anjuran 2400×1200 piksel dengan titik perhatian di sepertiga atas, karena `object-position` disetel ke `center 38%`.

## Struktur halaman

- **Sidebar** menggantikan navigasi horizontal. Lebar penuh di atas 1240 px, menyusut menjadi rel ikon di bawahnya, dan berubah menjadi bilah bawah pada layar di bawah 820 px.
- **Bilah atas** bersifat lengket dengan latar kaca (`backdrop-filter`), berisi remah navigasi, pengubah tema, tautan dokumentasi API, tombol unduh paket, dan penanda unit kerja.
- **Kepala halaman** berupa kartu gradien bermotif kawung dengan dua ringkasan angka di sisi kanan.
- **Konten** memakai tata letak bento: kartu metrik empat kolom, panel lebar untuk sebaran status, dua kolom untuk matriks dan indikator rawan, lalu tabel penuh.

## Gerak

Gerakan dijaga tipis dan hanya untuk orientasi: kartu muncul dengan jeda bertingkat melalui variabel `--i`, kartu terangkat sedikit saat disorot, dan sel matriks membesar saat siap diklik. Seluruh animasi dimatikan otomatis bila pengguna mengaktifkan `prefers-reduced-motion`.

Keadaan memuat memakai kerangka berkilau, bukan teks "Memuat", agar tata letak tidak melompat saat data tiba.

## Berkas terkait

| Berkas | Isi |
| --- | --- |
| `frontend/src/tokens.js` | Warna status, capaian, dan aksen tim |
| `frontend/src/theme.js` | Penyimpanan tema dan warna grafik Recharts |
| `frontend/src/Brand.jsx` | Logo dan lapisan motif kawung |
| `frontend/src/styles.css` | Variabel desain dan seluruh gaya komponen |
| `frontend/index.html` | Penetapan tema awal dan metadata halaman |
