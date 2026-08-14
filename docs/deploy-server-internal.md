# Deployment Server Internal

1. Salin proyek ke server yang memiliki Docker Engine dan Docker Compose.
2. Salin `.env.production.example` menjadi `.env`.
3. Ganti `SEBATIK_SECRET_KEY` dengan string acak kuat.
4. Jalankan `docker compose up -d --build`.
5. Periksa `docker compose ps`; layanan harus berstatus sehat.
6. Akses `http://alamat-server:8000`.
7. Masuk memakai akun awal dan segera ganti kata sandinya.

Menghentikan: `docker compose down`. Data tidak hilang karena berada di volume. Mengikuti log: `docker compose logs -f sebatik`.

Service `backup` membuat salinan SQLite setiap 24 jam dan menyimpan 30 backup terbaru pada volume `sebatik_backup`. Uji pemulihan secara berkala; backup yang tidak pernah diuji belum dapat dianggap aman.
