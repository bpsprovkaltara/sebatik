# Migrasi SQLite → PostgreSQL

Dokumen ini menjabarkan strategi memindahkan penyimpanan dari SQLite ke PostgreSQL,
mengelola skema dengan Alembic, dan memindahkan data secara aman.

## 1. Alasan migrasi

- Penulisan bersamaan banyak operator/verifikator (SQLite mengunci seluruh file saat
  menulis dan memakai `check_same_thread=False`).
- Migrasi skema yang dapat di-*upgrade*/*downgrade* (Alembic) menggantikan
  `ALTER TABLE ... ADD COLUMN` ad hoc.
- Tipe data lebih ketat (`timestamptz`, `numeric`, enum, indeks parsial).

## 2. Persiapan dependensi & pengaturan

- Tambah dependensi: `psycopg[binary]` (atau `psycopg2-binary`), `alembic`,
  `pydantic-settings`. Perbarui `requirements.txt`.
- Konfigurasi `database_url` memakai format `postgresql+psycopg://user:pass@host:port/db`.
- `docker-compose.yml` menambah layanan `db` (PostgreSQL) dengan volume persistensi;
  layanan `sebatik` menunggu `db` sehat sebelum mulai.

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: sebatik
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: sebatik
    volumes: [sebatik_pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sebatik"]
      interval: 10s
      timeout: 5s
      retries: 5
  sebatik:
    environment:
      SEBATIK_DATABASE_URL: postgresql+psycopg://sebatik:${POSTGRES_PASSWORD}@db:5432/sebatik
    depends_on:
      db: { condition: service_healthy }
volumes:
  sebatik_pgdata:
```

## 3. Alembic

- `alembic init backend/alembic` dengan `script_location = backend/alembic`.
- `env.py` membaca `database_url` dari `config.py` (bukan hardcode).
- Migrasi awal (`baseline`) membuat skema konsolidasi sesuai model-data.md.
- Setiap perubahan model berikutnya menghasilkan migrasi via `alembic revision
  --autogenerate` (atau tulis manual untuk migrasi data).

Perintah:

```powershell
python -m alembic -c backend/alembic.ini upgrade head
python -m alembic -c backend/alembic.ini downgrade -1
```

- Di produksi, migrasi dijalankan saat deploy (bukan saat import seperti sekarang).

## 4. Migrasi data (SQLite → PostgreSQL)

Pendekatan: **ETL ulang + ekspor/impor**, bukan dump mentah, karena skema target
berubah (konsolidasi).

Sumber data yang perlu dipindahkan:

| Data | Sumber | Cara |
|---|---|---|
| Indikator + nilai master (provinsi) | `data/raw/*` (workbook/JSON) | Jalankan ulang pipeline ETL ke PostgreSQL (sumber kebenaran asli). |
| Wilayah | `WILAYAH_KALTARA` | Seed via data migration (sudah statis). |
| Pengguna | `pengguna` di SQLite | Salin; hash Argon2 tetap valid. |
| Usulan & bukti dukung | `usulan_nilai`, `bukti_dukung` | Salin baris + pindahkan file bukti ke volume. |
| Log audit | `log_perubahan`, `log_aktivitas`, `unggahan_excel` | Salin (append-only). |
| Snapshot ketersediaan | `snapshot_ketersediaan` | Salin. |
| Penugasan PIC | `penugasan_pic` | Salin. |

Alur yang disarankan:

1. Tulis skrip migrasi sekali jalan `scripts/migrate_sqlite_to_postgres.py` yang
   membaca SQLite dan menulis ke PostgreSQL lewat model ORM/repository baru.
2. Jalankan ETL ulang untuk data master (indikator + nilai provinsi) agar konsisten
   dengan skema target.
3. Salin tabel tata kelola (pengguna, usulan, bukti, log) dengan pemetaan kolom lama
   → baru yang eksplisit.
4. Verifikasi: bandingkan jumlah baris dan beberapa nilai sampel antar kedua sumber.
5. Simpan `sebatik.db` sebagai arsip read-only; jangan hapus sebelum verifikasi selesai.

## 5. Strategi transisi (zero-downtime / rollback)

1. **Fase paralel**: aplikasi masih menulis SQLite; proses migrasi mengisi PostgreSQL
   secara berkala (atau sekali). Kedua DB berisi data sama.
2. **Cutover**: arahkan `SEBATIK_DATABASE_URL` ke PostgreSQL, jalankan `alembic upgrade
   head`, lalu alihkan trafik.
3. **Rollback**: bila bermasalah, arahkan kembali ke SQLite (data lama masih utuh)
   karena tidak ada skema yang dihapus. Catatan: data yang ditulis ke PostgreSQL
   setelah cutover tidak otomatis kembali ke SQLite; dokumentasikan langkah rekonstruksi.

Untuk instalasi internal sederhana, cutover langsung + backup SQLite penuh sudah
memadai; tidak perlu replikasi berjalan.

## 6. Perubahan kode yang terkait

- `backend/app/database.py`: hapus `migrate_governance()` + `seed_verified_master()`
  pada import; engine memakai `database_url` dari settings; hilangkan
  `check_same_thread`.
- `features.py` / `master_seed.py`: logika skema/seed dipindah ke migrasi Alembic dan
  perintah seed; file dapat dihapus setelah semua endpoint pindah.
- `scripts/backup_sqlite.py`: diganti dengan strategi backup PostgreSQL
  (`pg_dump`) dengan retensi serupa (lihat peta-jalan.md).

## 7. Catatan risiko

- Hash Argon2 (`pwdlib`) tidak bergantung DB; dapat disalin langsung.
- Kolom `nilai` yang semula REAL/SQLite menjadi `numeric`; perhatikan pembulatan saat
  membandingkan hasil.
- File bukti dukung tersimpan di filesystem (`path_file` absolut); saat pindah ke
  container PostgreSQL, pastikan path mengacu volume `bukti-dukung` yang sama.
