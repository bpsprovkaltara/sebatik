# Refactoring Pipeline ETL

Dokumen ini menjabarkan cara menjadikan pipeline ETL data-driven sehingga rentang
baris/kolom dan nama sheet tidak lagi hardcode di kode.

## 1. Kondisi saat ini

`src/etl/pipeline.py` menyimpan banyak nilai hardcode:

| Nilai hardcode | Lokasi | Risiko |
|---|---|---|
| Daftar sheet `VALUE_SOURCES` (4 nama sheet). | `pipeline.py:19-24` | Berubah bila workbook berganti versi. |
| `range(2, 88)` untuk membaca 86 indikator. | `pipeline.py:62` | Gagal bila jumlah berubah. |
| `range(3, 165)`, `range(3, 200)`, `range(3, ...)` untuk nilai. | `pipeline.py:145,157,167,...` | Rentang tidak eksplisit. |
| Kolom tahun `range(5,14)`, `range(6,11)`, dst. | `pipeline.py:151,...` | Posisi kolom diasumsikan tetap. |
| Tahun `range(2021, 2030)`, `2025..2029`, `2045`. | `pipeline.py` | Kaku pada horizon RPJPD. |
| `if len(indicators) != 86` (validasi keras). | `pipeline.py:228` | Menolak workbook valid dengan jumlah berbeda. |
| Label kolom hardcode (`"Kategori"`, `"Indikator"`, dst.). | `pipeline.py:60-96` | Fragile terhadap rename header. |

`audit.py` dan `metadata_pdf.py` juga punya asumsi serupa.

## 2. Prinsip target

1. **Konfigurasi terpisah dari kode.** Semua pemetaan sheet/kolom/tahun dinyatakan
   dalam satu berkas konfigurasi (YAML/TOML/JSON) yang di-versi, mis.
   `src/etl/config/`. Perubahan format workbook cukup mengubah konfigurasi.
2. **Parsing berbasis header.** Gunakan `header_index()` (sudah ada) sebagai satu
   pintu pemetaan nama kolom → indeks, bukan indeks angka ajaib.
3. **Pemisahan ekstraksi/transformasi/load** yang jelas, dengan setiap tahap dapat
   diuji terpisah.
4. **Validasi eksplisit dan dapat diatur.** Jumlah indikator yang diharapkan menjadi
   nilai konfigurasi (`expected_indicator_count`), bukan konstanta 86.

## 3. Rancangan konfigurasi

Contoh `src/etl/config/workbook.yaml`:

```yaml
workbook:
  sheets:
    master:
      name: "form provinsi"
      rows:
        start: 2
        end: null        # null = sampai habis / bertemu baris kosong
      columns:            # nama header -> field
        kategori: "Kategori"
        indikator: "Indikator"
        perbaikan_nama: "Perbaikan Nama Indikator"
        indikator_proxy: "Indikator Proxy"
        catatan_teknis: "Catatan Teknis"
        tahun_terakhir: "Tahun Terakhir Data"
        # ... semua kolom master
    values:
      - name: "Rakor ISV IUP Kaltara 202607"
        format: pasangan          # target/realisasi berpasangan
        rows:
          start: 3
          end: null
        category_column: 1
        number_column: 2
        kind_column: 4
        year_columns:
          start: 5
          end: 14               # inklusif
          first_year: 2021
        special_target_year: 2045
      - name: "Rakor ISV IUP Kaltara 2026"
        format: kolom_ganda       # realisasi lalu target
        # ...
  expected:
    indicator_count: 86
    categories: ["ISV", "IUP"]
```

Konfigurasi dimuat sekali oleh loader (`src/etl/config.py`) dan dijadikan struktur
data yang diteruskan ke fungsi ekstraksi.

## 4. Pemisahan tahapan

```
src/etl/
├── config/            # workbook.yaml + loader
├── extract/           # pembacaan workbook -> dict mentah
│   ├── master.py      # master_rows() (tanpa rentang hardcode)
│   ├── values.py      # extract_values() (berbasis config)
│   └── metadata.py    # metadata_pdf
├── transform/         # normalisasi, mapping ID, provenans
│   ├── normalize.py   # clean_text, parse_angka (dari common.py)
│   ├── ids.py         # indicator_id()
│   └── units.py       # indicator_unit
├── load/              # penulisan ke database (via ORM/repository)
│   └── writer.py
├── common.py          # dipertahankan (murni, sudah baik)
└── arah_baik.py
```

- `pipeline.py` tetap sebagai orkestrator (`run()`), tetapi isinya memanggil
  `extract` → `transform` → `load` dan menghasilkan laporan.
- `audit.py` memakai konfigurasi yang sama agar audit dan pipeline tidak menyimpang.
- Fungsi murni (`parse_angka`, `clean_text`, `indicator_id`, `enum_rpjmd`,
  `extract_proxy`) sudah baik dan dipertahankan di `transform/`.

## 5. Menghapus rentang hardcode

- **Master**: loop berhenti saat kategori/indikator kosong (atau sampai `rows.end`),
  bukan `range(2, 88)`.
- **Nilai**: pakai `year_columns` + `first_year` dari config; kolom kategori/nomor
  dibaca lewat `header_index` atau kolom yang dikonfigurasi.
- **Jumlah indikator**: validasi memakai `expected.indicator_count` dari config;
  bila berbeda, gagal dengan pesan yang menyebut nilai ekspektasi vs aktual (bukan
  angka 86 yang dikodekan).

## 6. Load ke PostgreSQL

Setelah migrasi DB (lihat migrasi-postgresql.md), ETL menulis ke tabel target
`indikator`, `metadata_indikator`, `nilai_indikator` melalui repository/ORM yang sama
dengan aplikasi, atau tetap via SQLAlchemy Core. Selama transisi, ETL boleh tetap
menulis SQLite staging untuk fitur pratinjau unggahan; kemudian dipindah.

## 7. Kriteria selesai

- Tidak ada `range(...)` numerik yang bermakna bisnis di `pipeline.py`/`audit.py`
  selain yang berasal dari config.
- Menambah versi workbook baru = mengubah `workbook.yaml` tanpa menyentuh kode.
- Test ETL memakai file asli tetap hijau (lihat testing-ci.md).
- Audit dan pipeline membaca konfigurasi yang sama.
