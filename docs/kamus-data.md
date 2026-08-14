# Kamus Data SEBATIK

## indikator

Satu baris per indikator. Kunci utama `id_indikator`. Kolom utama meliputi kategori, nomor, nama, kelompok, arah pembangunan, satuan, penghasil, pengampu, OPD, Tim PJK, status ketersediaan/metadata, periode, tahun terakhir, proxy, tautan, `arah_baik`, dan penanda verifikasi arah.

## nilai_indikator

Fakta format long dengan kunci `id_indikator + tahun + jenis`. `jenis` adalah `realisasi` atau `target`; `nilai` boleh NULL; `sumber_sheet` menyimpan provenans.

## metadata_indikator

Definisi, rumus mentah, interpretasi, sumber data, frekuensi, halaman, sumber metadata, dan penanda verifikasi manual.

## penugasan_pic

Nama PIC perorangan. Tabel privat; tidak tersedia melalui API publik.

## snapshot_ketersediaan

Status setiap indikator pada `tanggal_snapshot`. Kunci gabungan indikator dan tanggal.

## pengguna

Akun, hash kata sandi, peran, Tim PJK, status aktif, dan kewajiban mengganti kata sandi awal. Tidak menyimpan kata sandi polos.

## usulan_nilai

Antrean isian PIC: indikator, tahun, jenis, nilai, sumber, catatan, pengusul, verifikator, dan status persetujuan.

## log_perubahan

Jejak audit append-only: waktu, pengguna, indikator, field, nilai lama/baru, sumber perubahan, referensi, dan catatan.

## unggahan_excel

Arsip unggahan, checksum SHA-256, status proses, ringkasan diff, pengunggah, dan waktu persetujuan.
