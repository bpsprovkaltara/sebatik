# Autentikasi & Keamanan

Dokumen ini merinci perbaikan keamanan dan desain autentikasi/otorisasi target.
Kontrak endpoint auth saat ini (`/auth/login`, `/auth/saya`, `/auth/ganti-password`,
`/admin/pengguna*`, `OAuth2PasswordRequestForm`) dipertahankan sebisanya agar frontend
tidak perlu berubah besar.

## 1. Masalah saat ini

| Masalah | Lokasi |
|---|---|
| `SECRET` default hardcode `GANTI-SECRET-INI-SEBELUM-PRODUKSI-SEBATIK`. | `features_api.py:28` |
| CORS hardcode hanya `localhost:5173`. | `main.py:22` |
| Token disimpan di `localStorage` (rentan XSS). | `frontend/src/auth.js` |
| Tidak ada refresh token/rotasi; TTL 8 jam. | `features_api.py:337` |
| Akun seed dengan kata sandi default (`Sebatik-Ganti-Segera-2026!`, `Sebatik-Operator-Ganti-2026!`). | `features.py`, `master_seed.py` |
| `current_user` mengembalikan `PENGUNJUNG` saat token kosong (pencampuran tamu/terautentikasi). | `features_api.py:57-58` |
| Peran dibandingkan string langsung. | `require()` |
| Hash password Argon2 sudah benar (`pwdlib`), tetapi verifikasi `login` mengembalikan `SELECT *` termasuk `password_hash`. | `features_api.py:335` |
| Tidak ada rate limiting pada login (brute-force). | — |

## 2. Manajemen rahasia

1. `secret_key` diwajibkan dari environment; aplikasi menolak mulai (raise di
   `create_app`) bila nilainya masih default atau lebih pendek dari 32 karakter,
   kecuali pada mode `ENVIRONMENT=development`/pengujian.
2. Tambah `SEBATIK_SECRET_KEY` dan kredensial DB ke `.env` yang **tidak** ter-commit;
   `.env.example` tetap berisi placeholder.
3. Semua rahasia dibaca lewat `config.py` (pydantic-settings), tidak pernah
   `os.getenv` langsung di kode bisnis.
4. Rotasi kunci: mendukung variabel cadangan `SEBATIK_SECRET_KEYS` (daftar) agar
   rotasi tidak menolak token lama secara paksa; token diverifikasi terhadap kunci
   aktif lalu kunci lama.

## 3. Desain token

Dua pilihan, dengan rekomendasi:

- **Opsi A (rekomendasi bertahap):** tetap JWT bearer (HS256) di header
  `Authorization: Bearer`, sama seperti sekarang, agar frontend tidak berubah.
  Tambahan: klaim `sub`, `peran`, `exp`, `iat`, `jti` (ID unik). TTL lebih pendek
  (mis. 1–2 jam) + refresh token httpOnly.
- **Opsi B (jangka panjang):** simpan access token di cookie httpOnly + Secure +
  SameSite=Strict, dan refresh token di cookie terpisah, untuk menutup risiko XSS
  terhadap `localStorage`.

Karena target refactoring ini menjaga frontend tetap JavaScript tanpa perubahan
besar, **Opsi A diterapkan lebih dulu**, Opsi B dicatat sebagai tindak lanjut.

Detail Opsi A:
- `login` mengembalikan `access_token` + `refresh_token`.
- `refresh_token` disimpan httpOnly (`/auth/refresh` endpoint baru) atau, sebagai
  langkah minimum, `access_token` diperpendek TTL-nya dan `harus_ganti_password`
  tetap dipertahankan.
- Tambah klaim `peran` di dalam JWT sehingga `current_user` tidak perlu query DB
  untuk keputusan otorisasi ringan; namun data pengguna tetap dibaca dari DB untuk
  memastikan akun masih aktif.

## 4. Otorisasi berbasis peran

- Definisikan enum `Peran` (`ADMIN`, `OPERATOR`, `VERIFIKATOR`, `PENGUNJUNG`) di
  `security.py`; ganti perbandingan string dengan enum.
- `current_user` (autentikasi) dipisah dari `require_roles` (otorisasi):
  - `current_user`: hanya membuktikan token valid dan akun aktif; bila token tidak
    ada, endpoint publik tetap boleh berjalan tanpa user (jangan paksa menjadi
    `PENGUNJUNG` bila endpoint memang publik).
  - `require_roles(*roles)`: memastikan `peran` termasuk yang diizinkan, jika tidak
    → 403.
- Pertahankan aturan domain: operator hanya wilayahnya, verifikator hanya provinsi,
  operator tidak memverifikasi usulannya sendiri (validasi di service, lihat
  backend.md §3).

## 5. Kata sandi & akun

- Tetap Argon2 via `pwdlib` (sudah benar).
- Login tidak mengembalikan `password_hash`; proyeksikan hanya kolom yang diperlukan.
- Kebijakan minimal 12 karakter (sudah ada) dipertahankan; tambah penolakan kata sandi
  umum bila memungkinkan (opsional).
- Akun seed: buat kata sandi seed dihasilkan acak saat migrasi data dan dicetak sekali
  ke operator/`admin`, atau tetap memakai kata sandi awal yang wajib diganti
  (`harus_ganti_password=1` sudah ada) — pertahankan perilaku wajib ganti.
- Tambah rate limiting pada `/auth/login` (mis. 5 percobaan/menit per IP+username)
  untuk menahan brute-force. Implementasi dapat memakai middleware sederhana berbasis
  Redis/PostgreSQL, atau library yang tersedia.

## 6. Keamanan HTTP & deployment

- CORS dibaca dari `settings.cors_origins` (bukan hardcode); produksi diatur lewat env.
- Tambah header keamanan (`X-Content-Type-Options`, `X-Frame-Options`/CSP untuk iframe
  peta bila perlu, `Referrer-Policy`) via middleware.
- Pastikan jalur `bukti_dukung` tidak dapat diekspos melalui traversal path: saat ini
  `path_file` disimpan absolut dan dibaca langsung. Refactor: validasi bahwa path yang
  diminta berada di dalam `evidence_dir`, dan hindari nama file dari input tanpa
  sanitasi (sudah memakai `uuid` prefix — pertahankan, tambah verifikasi ekstensi).
- Batas ukuran unggahan sudah ada (10 MB bukti, 30 MB Excel) — pindahkan ke settings
  dan pertahankan.

## 7. Audit & logging

- Pertahankan `log_perubahan` (nilai/field) dan `log_aktivitas` (tindakan admin) —
  keduanya sudah baik.
- Tambah log terstruktur (JSON) untuk peristiwa auth (login berhasil/gagal, logout,
  perubahan password, reset) dengan `pengguna_id`, bukan menyimpan kata sandi.

## 8. Checklist keamanan sebelum produksi

- [ ] `SEBATIK_SECRET_KEY` acak ≥32 karakter, tidak default.
- [ ] Akun `admin` dan operator seed sudah ganti kata sandi.
- [ ] `.env` tidak ter-commit; hanya `.env.example` di repo.
- [ ] CORS dibatasi ke origin produksi.
- [ ] Rate limiting login aktif.
- [ ] Tidak ada `password_hash` yang bocor di respons API.
- [ ] `data/raw` dan `sebatik.db` dikeluarkan dari version control (lihat gotcha di
  AGENTS.md).
