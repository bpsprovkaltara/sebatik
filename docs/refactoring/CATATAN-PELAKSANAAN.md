# Catatan Pelaksanaan Refactoring

Berkas ini mencatat keputusan dan temuan yang muncul **saat** refactoring
dijalankan, termasuk hal-hal yang berbeda dari rencana di dokumen lain.
Dokumen rencana tidak diubah; perbedaannya dicatat di sini.

## Temuan 1 — Dua daftar indikator, bukan dua tabel untuk daftar yang sama

**Kapan:** Fase 2, saat menjalankan pemindahan data.

`model-data.md` §4 mengasumsikan `indikator` (jalur ETL) dan `beranda_indikator`
(jalur master) menyimpan 86 indikator yang sama sehingga dapat digabung menjadi
satu dimensi 86 baris. Pemeriksaan data sebenarnya membantah asumsi itu:

| Pemeriksaan | Hasil |
|---|---|
| Skema ID | `ISV-01`…`IUP-76` (ETL) vs `ISV-001`…`IUP-080` (master) |
| Irisan ID | **0** |
| Nama indikator yang identik | **23** dari 86 |
| Contoh | `ISV-01` = "GNI per kapita", `ISV-001` = "PDRB per Kapita" |

Keduanya adalah **dua versi daftar indikator yang berbeda**, bukan dua
representasi dari daftar yang sama. Menggabungkannya lewat `id_indikator`
menghasilkan 172 baris, bukan 86.

**Keputusan (pemilik produk, 19 Agustus 2026):** daftar **master** yang dipakai;
jalur ETL dibuang. Dimensi `indikator` berisi 86 baris dari `beranda_indikator`.

### Konsekuensi yang harus ditindaklanjuti

1. **`arah_baik` hilang untuk 63 indikator.** Kolom ini hanya ada di jalur ETL
   dan merupakan hasil verifikasi manual admin. Skrip migrasi membawanya untuk
   23 indikator yang namanya cocok; 63 sisanya kosong. Selama kosong,
   `/api/v1/capaian` mengembalikan `status_capaian = "BELUM_ADA_DATA"` untuk
   indikator tersebut — perilaku yang benar (tidak mengarang angka), tetapi
   perlu dilengkapi lewat `PUT /api/v1/arah-baik/{id}` yang sudah ada.
2. **`tim_pjk` hilang untuk 63 indikator.** Filter `tim` pada `/api/v1/indikator`
   dan `/api/v1/capaian` menjadi kurang berguna sampai diisi ulang.
3. **ID publik berubah** dari `ISV-04` menjadi `ISV-004` dan seterusnya untuk
   endpoint analitik/capaian. Bentuk respons tidak berubah, tetapi nilai
   `id_indikator` berubah. Frontend tidak menyimpan ID secara permanen sehingga
   tidak terpengaruh; pranala eksternal yang menyimpan ID lama akan 404.
4. **`penugasan_pic` (189 baris) dan `snapshot_ketersediaan` (63 baris) dibuang**
   karena memakai ID ETL tanpa padanan master. Keduanya tidak dipakai endpoint
   publik.

### Alternatif yang tidak diambil

- Menggabungkan 172 baris (lossless) — ditolak karena menyisakan dua daftar di
  satu tabel dan tidak memenuhi kriteria "satu entitas satu tabel".
- Memetakan 23 yang cocok lalu menyisakan 149 — ditolak dengan alasan yang sama.

## Temuan 2 — Fakta kembar akibat penulisan N-arah

**Kapan:** Fase 2, saat verifikasi jumlah baris.

`verify_submission` lama menulis satu nilai ke banyak tabel sekaligus. Akibatnya
`beranda_nilai` dan `beranda_nilai_wilayah` (dengan `wilayah_kode='65'`) memuat
fakta yang sama untuk `IUP-056` tahun 2022. Skrip migrasi **menggabungkan**,
bukan membuang salah satu: nilai diambil dari baris pertama, sedangkan jejak
usulan (`usulan_id`, `sumber`) diambil dari baris yang memilikinya, sehingga
riwayat verifikasi tidak putus. Bila dua sumber berbeda angka, skrip mencatat
peringatan alih-alih diam.

Verifikasi jumlah baris karena itu membandingkan **kunci alami yang berbeda**,
bukan jumlah baris mentah.

## Temuan 3 — Bug `/beranda` untuk kabupaten/kota

**Kapan:** Fase 0, saat merekam garis dasar kontrak API.

`GET /api/v1/beranda?wilayah_kode=6501` mengembalikan **500** karena query
memilih kolom `satuan_catatan` yang tidak ada di `beranda_nilai_wilayah`.
Ini akibat langsung model data ganda. Tes kontrak menandainya `xfail` dengan
alasan tertulis; tanda itu dilepas setelah konsolidasi (Fase 4) membuatnya lulus.

## Lingkungan pengembangan

- PostgreSQL **sudah diverifikasi terhadap server sungguhan** (PostgreSQL 16 di
  Docker). Selama sebagian besar pengerjaan Docker belum tersedia, sehingga
  verifikasinya bersandar pada mode offline Alembic dan SQLite target; setelah
  Docker tersedia, seluruh jalur diuji langsung. Ringkasannya di Temuan 10.
- CI juga menjalankan `alembic upgrade head` dan `downgrade base` terhadap
  PostgreSQL 16 pada setiap PR.
- Berkas `.venv-sebatik` dibuat ulang karena `.runtime-packages` yang ada di repo
  tidak lengkap (paket `sqlalchemy` hanya menyisakan direktori `cyextension`).

## Urutan cutover yang disarankan

```bash
# 1. Cadangkan basis data lama
python scripts/backup_sqlite.py

# 2. Siapkan PostgreSQL dan skema
docker compose up -d db
SEBATIK_DATABASE_URL=postgresql+psycopg://sebatik:SANDI@localhost:5432/sebatik \
  python -m alembic -c backend/alembic.ini upgrade head

# 3. Lihat rencana pemindahan lebih dulu
python scripts/migrasi_ke_skema_target.py --periksa

# 4. Pindahkan (satu transaksi; batal otomatis bila verifikasi gagal)
python scripts/migrasi_ke_skema_target.py --jalankan

# 5. Arahkan aplikasi ke PostgreSQL, lalu jalankan tes kontrak
docker compose up -d
```

Rollback: arahkan `SEBATIK_DATABASE_URL` kembali ke SQLite. Berkas lama tidak
disentuh skrip migrasi (dibuka mode `ro`). Data yang ditulis ke PostgreSQL
setelah cutover tidak otomatis kembali dan perlu dipindahkan manual.

## Temuan 4 — Mengeluarkan `data/` dari git akan melumpuhkan CI

**Kapan:** Fase 8.

Kriteria selesai meminta `data/raw` dan `data/processed/sebatik.db` dikeluarkan
dari version control. Menuruti itu apa adanya membuat seluruh tes kontrak API
melewatkan dirinya di CI, karena semuanya dibangun di atas salinan basis data
produksi — gerbang mutu yang paling penting justru menjadi tidak berbunyi.

Yang dilakukan: tes kontrak diberi **benih uji sendiri** yang ikut ter-commit
(`tests/api/conftest.py`). Benih itu ringkas tetapi menyentuh semua bentuk
respons: indikator makro dan non-makro, indikator belum terverifikasi, nilai
provinsi dan wilayah, nilai tahunan dan periodik, nilai berupa teks, target 2029
dan 2045, serta satu usulan berbukti.

Hasilnya, 350 dari 353 tes tetap berjalan tanpa direktori `data/`. Tiga tes yang
memang menguji data sungguhan — integrasi ETL dan dua regresi isi beranda —
melewatkan dirinya sendiri dengan pesan yang jelas.

## Temuan 5 — ID indikator lama tertinggal di frontend

**Kapan:** Fase 6, saat verifikasi di peramban.

`AnalyticsPage` memakai `'ISV-01'`, `'ISV-04'`, dan `'ISV-05'` sebagai nilai
bawaan pemilih indikator. Setelah konsolidasi Fase 2, ID itu tidak ada lagi dan
halaman meminta indikator yang tidak ditemukan (404) begitu dibuka.

Cacat ini lolos dari build, lolos dari lint, dan lolos dari tes — ia hanya
terlihat pada jejak jaringan peramban. Pilihan awal kini diambil dari daftar
yang benar-benar dimuat, sehingga tidak ikut basi saat daftar indikator berganti
versi lagi.

## Temuan 6 — Fase 3 belum selesai: muatan masih dirakit di router

**Kapan:** peninjauan ulang seluruh dokumen refactoring.

`features_api.py` memang sudah hilang dan semua endpoint sudah punya router,
tetapi pemindahannya berhenti di separuh jalan: penyusunan muatan ikut pindah
ke `routers/`, bukan ke `services/`. `routers/insight.py` merakit kartu makro,
seri, dan perbandingan wilayah sendiri (142 baris); `capaian.py` menghitung
progres dan proyeksi; `validitas.py` menentukan status dan pembaru terakhir.
Sembilan berkas service yang disebut backend.md §1.2 belum ada sama sekali
(`beranda`, `insight`, `explorer`, `validitas`, `indikator`, `auth`,
`pengguna`, serta penyusunan muatan pada `capaian` dan `analitik`).

Tes arsitektur yang ada tidak menangkapnya karena hanya melarang SQL mentah
dan pemanggilan `select()` — bukan perhitungan.

**Yang dilakukan:** seluruh penyusunan muatan dipindah ke `services/`; router
tinggal memvalidasi masukan dan menerjemahkan penolakan. Total baris `routers/`
turun dari 1.807 menjadi 892. Aturan §8 kemudian diikat menjadi tes: router
tidak boleh memuat perulangan maupun dict respons berkunci banyak, dan setiap
domain endpoint wajib punya berkas service-nya.

Karena service tidak boleh mengimpor FastAPI, penolakan dikembalikan sebagai
nilai (`services.Penolakan`) dan router yang mengubahnya menjadi
`HTTPException`. Pola ini sudah dipakai `verifikasi.py` sejak Fase 4; sekarang
dinaikkan ke `services/__init__.py` supaya dipakai seragam.

## Temuan 7 — Lapisan `schemas/` praktis tidak ada

**Kapan:** peninjauan ulang seluruh dokumen refactoring.

arsitektur-target.md §1 mendaftar delapan berkas skema per domain dan
backend.md §4 mensyaratkan setiap endpoint memakai skema respons eksplisit.
Yang ada hanya `schemas/wilayah.py`: **1 dari 42 endpoint** punya
`response_model`. Akibatnya kontrak JSON hanya hidup di
`tests/api/test_kontrak.py` dan tidak muncul di `/api/docs` sama sekali.

**Yang dilakukan:** dibuat dua belas berkas skema (`umum`, `sistem`, `beranda`,
`explorer`, `capaian`, `insight`, `validitas`, `analitik`, `indikator`, `auth`,
`admin`, `usulan`, `unggahan`) dan dipasang pada semua endpoint JSON. Lima
endpoint unduhan berkas sengaja tidak memakainya karena tidak mengirim JSON.

Dua hal yang perlu diketahui:

- `/beranda` dulu punya **dua bentuk respons**: saat belum ada data sama sekali,
  kunci `wilayah_kode` dan `status_data` tidak ikut dikirim. Bentuknya kini
  selalu sama, sesuai `BerandaResponse` di backend.md §4.
- `/analitik/gap/{id}` memang punya dua bentuk yang sah — indikator tanpa
  realisasi hanya mengirim `status` dan `disclaimer`. Endpoint itu memakai
  `response_model_exclude_unset=True` supaya bentuk ringkasnya tidak mendadak
  dipenuhi kunci bernilai null.

## Temuan 8 — Sisa checklist keamanan yang tercatat "selesai"

**Kapan:** peninjauan ulang seluruh dokumen refactoring.

Tiga butir auth-keamanan.md belum ada kodenya: rotasi kunci (§2.4), klaim `jti`
dan token segar (§3 Opsi A), serta log auth terstruktur (§7). TTL akses juga
masih 8 jam, padahal §3 meminta 1–2 jam.

**Yang dilakukan:**

- `SEBATIK_SECRET_KEYS` menampung kunci lama; token diverifikasi terhadap kunci
  aktif lalu kunci lama, tetapi selalu ditandatangani kunci aktif.
- Token membawa `jti`, dan klaim `tipe` memisahkan token akses dari token segar
  sehingga cookie yang bocor tidak dapat dipakai sebagai bearer. Token terbitan
  versi lama (tanpa klaim `tipe`) tetap diterima sebagai token akses agar
  pembaruan aplikasi tidak memaksa semua orang masuk ulang.
- TTL akses menjadi 2 jam; sesi disambung `POST /auth/refresh` dengan token
  segar 24 jam di cookie httpOnly, `SameSite=Strict`, `Path=/api/v1/auth`, dan
  `Secure` di produksi. `POST /auth/logout` menghapusnya.
- `frontend/src/api/client.js` menyegarkan sekali saat 401 lalu mengulang
  permintaan; penyegaran berjalan satu per satu supaya beberapa 401 serentak
  tidak saling menimpa token hasilnya.
- Peristiwa auth (masuk, gagal, dibatasi, segarkan, keluar, ganti sandi, reset,
  akun dibuat) dicatat sebagai JSON satu baris tanpa kata sandi maupun token.

Opsi B (token akses ikut pindah ke cookie httpOnly) tetap menjadi tindak
lanjut: token akses masih disimpan di `localStorage`, tetapi kini berumur
2 jam, bukan 8.

## Temuan 9 — Tes frontend belum menyentuh yang paling mudah salah

**Kapan:** peninjauan ulang seluruh dokumen refactoring.

testing-ci.md §4 meminta tes untuk `api/client.js` (penyisipan header auth dan
penanganan 401), untuk hook, dan untuk komponen murni. Tidak satu pun ada —
padahal `client.js` justru satu-satunya tempat 401 ditangani.

**Yang dilakukan:** ditambahkan `api/client.test.js`, `hooks/useFetch.test.jsx`,
dan `components/charts/charts.test.jsx`. Tes frontend naik dari 22 menjadi 50.
`TooltipCard` juga dipindah dari `ui.jsx` ke `components/charts/` sesuai
frontend.md §4.

Tiruan `fetch` pada tes klien menjawab berdasarkan URL, bukan urutan panggilan:
menyegarkan token ikut memicu pemuatan ulang profil, jadi jumlah panggilan
bukan sesuatu yang layak dikunci di tes.

## Urutan fase yang dijalankan

Fase 7 (keamanan) dikerjakan sebelum Fase 6 (frontend), bukan sesudahnya seperti
di peta jalan. Alasannya: pemecahan `App.jsx` menyentuh seluruh jalur
autentikasi di frontend, jadi lebih murah menulisnya sekali di atas kontrak auth
yang sudah final daripada menulis ulang setelahnya.

## Status kriteria selesai

| Kriteria | Status |
|---|---|
| Aplikasi berjalan di PostgreSQL dengan Alembic; tidak ada migrasi ad hoc | Skema dan compose siap; cutover menunggu server PostgreSQL kantor |
| Satu model data konsolidasi; verifikasi menulis satu tabel | Selesai, dengan tes yang membuktikannya |
| `features_api.py` dihapus; endpoint terpetakan ke router/service/repository | Selesai — termasuk penyusunan muatan (lihat Temuan 6) |
| Skema respons eksplisit per endpoint di OpenAPI | Selesai (lihat Temuan 7) |
| `App.jsx` < 150 baris; router + layer API terpusat | Selesai (59 baris) |
| ETL data-driven; tidak ada rentang hardcode | Selesai |
| Test kontrak API membuktikan kontrak publik tidak berubah | Selesai |
| CI hijau: lint + type + test backend + test/build frontend | Selesai |
| Checklist keamanan terpenuhi | Selesai (lihat Temuan 8), kecuali dua butir operasional di bawah |
| Dokumentasi diperbarui | Selesai |

Dua butir keamanan yang harus dikerjakan operator, bukan kode:

- `SEBATIK_SECRET_KEY` acak ≥32 karakter dipasang di `.env` produksi.
- Akun seed mengganti sandi awalnya setelah pemasangan.

## Tindak lanjut yang belum dikerjakan

1. **Cutover PostgreSQL di lingkungan kantor** belum dijalankan — itu keputusan
   operasional, bukan pekerjaan kode. Seluruh jalurnya sudah diverifikasi
   terhadap PostgreSQL 16 sungguhan (lihat Temuan 10), termasuk migrasi,
   pemindahan data, penyelarasan sequence, dan alur verifikasi.
2. **`arah_baik` untuk 63 indikator** perlu diisi lewat panel admin sebelum
   halaman capaian menampilkan angka untuk indikator tersebut.
3. **Pembatas laju login** disimpan di memori proses. Cukup untuk satu instans;
   perlu dipindah ke Redis/PostgreSQL bila kelak dijalankan multi-instans.
4. **Opsi B auth-keamanan.md §3** — token akses ikut pindah ke cookie httpOnly —
   belum dikerjakan. Token akses masih di `localStorage`, tetapi kini berumur
   2 jam dan sesinya disambung token segar httpOnly (lihat Temuan 8).
5. **Basis data lokal `data/processed/sebatik.db` masih berskema lama.** Berkas
   itu belum pernah dipindahkan ke skema konsolidasi, sehingga menjalankan
   aplikasi langsung di atasnya menghasilkan 500 (`no such column:
   nilai_indikator.status_verifikasi`). Jalankan urutan cutover di atas lebih
   dulu, atau arahkan `SEBATIK_DATABASE_URL` ke salinan hasil migrasi.

## Temuan 10 — Verifikasi penuh terhadap PostgreSQL sungguhan

**Kapan:** setelah Docker tersedia di mesin pengerjaan.

Sebelumnya PostgreSQL hanya dapat diverifikasi lewat DDL mode offline. Setelah
Docker berjalan, seluruh jalur diuji langsung terhadap PostgreSQL 16:

| Yang diuji | Hasil |
|---|---|
| `alembic upgrade head` (3 revisi) | Berhasil |
| Pemindahan data dari SQLite lama | 86 indikator, 670 fakta; verifikasi lolos |
| Sebelas endpoint publik dan admin | Semua 200 |
| Penyelarasan sequence setelah sisipan id eksplisit | Kelima sequence selaras |
| `kode_sdgs` 634 karakter | Tersimpan utuh sebagai `text` |
| Indeks unik parsial pada `nilai_indikator` | Duplikat tahunan dan periodik ditolak |
| `alembic downgrade base` | Nol tabel tersisa |
| Alur verifikasi usulan | Menambah tepat satu baris fakta |

Dua hal yang **hanya** dapat ditemukan di PostgreSQL, dan lolos sepenuhnya dari
pengujian SQLite:

1. **`kode_sdgs` terlalu pendek.** Kolomnya dideklarasikan `String(40)`, padahal
   11 dari 19 baris terisi melebihi batas itu dan yang terpanjang mencapai 634
   karakter — sebagian sumber lama menyimpan uraian indikator SDGs lengkap,
   bukan kode singkat. SQLite mengabaikan panjang `VARCHAR` sehingga tidak
   pernah mengeluh; PostgreSQL menegakkannya dan akan menggagalkan cutover.
   Diperbaiki oleh migrasi `0003_kode_sdgs_text`. Downgrade-nya sengaja
   dibiarkan gagal bila sudah ada uraian panjang, supaya kembali ke revisi lama
   tidak memotong data diam-diam.
2. **Penyelarasan sequence** (`selaraskan_urutan`) tidak pernah benar-benar
   berjalan sebelumnya karena SQLite tidak punya sequence. Tanpa itu, INSERT
   pertama setelah cutover akan memakai id 1 dan langsung bentrok. Kini
   terverifikasi selaras pada kelima tabel ber-sequence.

## Temuan 11 — Migrasi `0003` jalan di PostgreSQL, gagal di SQLite

**Kapan:** saat memverifikasi ulang setelah migrasi `0003_kode_sdgs_text` dibuat.

Migrasi itu ditulis dengan `op.alter_column` biasa. PostgreSQL menerimanya,
tetapi SQLite tidak punya `ALTER COLUMN` sama sekali dan seluruh tes integrasi
gagal dengan `near "ALTER": syntax error`.

Jebakannya halus: `env.py` sudah menyetel `render_as_batch=True` untuk SQLite,
tetapi setelan itu hanya memengaruhi **hasil autogenerate** — ia tidak membuat
operasi yang ditulis tangan berjalan dalam batch mode. Perbaikannya membungkus
perubahan tipe dengan `op.batch_alter_table`, sehingga Alembic membangun ulang
tabelnya di SQLite dan tetap memakai `ALTER` biasa di PostgreSQL.

Diverifikasi pada keduanya: kolomnya menjadi `TEXT` di SQLite dan `text` di
PostgreSQL, dan `downgrade base` bersih di kedua dialek.

## Temuan 12 — Suite tes ikut membaca `.env` pengembang

**Kapan:** saat menyiapkan `.env` untuk cutover PostgreSQL.

`Settings` membaca `.env`, dan `.env` yang dibuat untuk cutover memuat
`SEBATIK_ENVIRONMENT=production`. Akibatnya cookie sesi dipasang bertanda
`Secure`, yang tidak dikirim balik lewat `http://testserver`, sehingga tes alur
token segar gagal — **hanya di mesin yang punya `.env`**. CI, yang tidak punya
berkas itu, tetap hijau.

Divergensi semacam ini yang paling mahal: gejalanya muncul jauh dari sebabnya,
dan "di CI hijau, kok" menyesatkan. `tests/conftest.py` kini memaku
`SEBATIK_ENVIRONMENT`, `SEBATIK_SECRET_KEY`, `SEBATIK_SECRET_KEYS`, dan
`SEBATIK_DATABASE_URL` lewat variabel lingkungan — yang menang atas `.env` —
sehingga suite berperilaku sama di mana pun.

Sebagai pasangannya, `tests/unit/test_config.py` justru **membuang** seluruh
variabel `SEBATIK_*` sebelum tiap tes: berkas itu menguji nilai bawaan, yang
hanya bermakna bila tidak ada setelan yang membayanginya.

Pelajaran yang sama berlaku untuk pembatas laju login: ia keadaan bersama satu
proses, jadi `tests/api/conftest.py` mengosongkannya di sekitar setiap tes agar
modul yang sengaja menghabiskan jatah tidak menjatuhkan modul lain.
