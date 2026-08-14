# Laporan ETL SEBATIK

## Ringkasan tabel

| Tabel | Jumlah baris |
|---|---:|
| indikator | 86 |
| nilai_indikator | 666 |
| metadata_indikator | 86 |
| penugasan_pic | 258 |

## Validasi parsing nilai

- Berhasil di-parse: **1934** sel sumber.
- Gagal di-parse: **3** sel sumber nonkosong.
- Kosong dan dipertahankan sebagai NULL/tidak dibuat: **1710** sel sumber.
- Fakta unik setelah prioritas sumber: **666** baris.
- Cadangan Parquet: **tidak dibuat (pyarrow tidak tersedia)**; CSV selalu dibuat.
- Pelanggaran foreign key: **0**.

## Indikator tanpa satu pun nilai realisasi (42)

- ISV-08
- IUP-02
- IUP-04
- IUP-05
- IUP-11
- IUP-12
- IUP-13
- IUP-18
- IUP-19
- IUP-20
- IUP-21
- IUP-22
- IUP-24
- IUP-27
- IUP-28
- IUP-29
- IUP-30
- IUP-35
- IUP-38
- IUP-39
- IUP-42
- IUP-44
- IUP-45
- IUP-46
- IUP-47
- IUP-49
- IUP-50
- IUP-55
- IUP-61
- IUP-62
- IUP-64
- IUP-65
- IUP-67
- IUP-68
- IUP-69
- IUP-70
- IUP-71
- IUP-72
- IUP-73
- IUP-74
- IUP-75
- IUP-76

## Aturan provenans

Urutan prioritas: `Rakor ISV IUP Kaltara 202607` -> `Rakor ISV IUP Kaltara 2026` -> `ISV IUP Kaltara 2026` -> `ISV IUP Kaltara`. Sumber lama hanya mengisi kombinasi indikator-tahun-jenis yang masih kosong.
