# Refactoring Backend

Dokumen ini menjabarkan cara memecah `backend/app/features_api.py` (636 baris) dan
`backend/app/main.py` (83 baris) menjadi modul modular, serta aturan penulisan ulang
query SQL mentah menjadi ORM.

## 1. Inventaris endpoint saat ini dan tujuan modulnya

### 1.1 Dari `main.py`

| Endpoint | Pindah ke router |
|---|---|
| `GET /api/v1/health` | `routers/health.py` (atau `main.py`) |
| `GET /api/v1/indikator` | `routers/indikator.py` |
| `GET /api/v1/ekspor.csv` | `routers/ekspor.py` |
| `GET /api/v1/ekspor.xlsx` | `routers/ekspor.py` |

Helper `PUBLIC_FIELDS`, `serialize`, `filters`, `export_rows`, `EXPORT_HEADERS`
dipindah ke `repositories/indikator.py` dan `services/ekspor.py`.

### 1.2 Dari `features_api.py`

| Endpoint | Router | Service | Catatan |
|---|---|---|---|
| `GET /beranda` | `beranda.py` | `services/ketersediaan.py` + `beranda` | logika makro, visi, `latest_period_value` jadi repository. |
| `GET /indikator-explorer` | `explorer.py` | — | grouping jadi service murni. |
| `GET /indikator-explorer/{id}` | `explorer.py` | — | timeline/growth jadi helper service. |
| `GET /capaian-explorer` | `capaian.py` | — | |
| `GET /capaian-explorer/{id}` | `capaian.py` | `services/capaian.py` | `progress_towards`, insight jadi service. |
| `GET /insight` | `insight.py` | `services/insight.py` | |
| `GET /validitas` | `validitas.py` | — | perhitungan status/updater jadi service. |
| `GET /beranda-indikator/{id}/metadata` | `explorer.py`/`indikator.py` | — | |
| `POST /auth/login` | `auth.py` | `services/auth.py` | |
| `GET /auth/saya` | `auth.py` | — | |
| `POST /auth/ganti-password` | `auth.py` | `services/auth.py` | |
| `POST /admin/pengguna` | `admin.py` | `services/pengguna.py` | |
| `GET /wilayah` | `wilayah.py` | — | |
| `GET /admin/pengguna` | `admin.py` | `repositories/pengguna.py` | |
| `PATCH /admin/pengguna/{id}/status` | `admin.py` | `services/pengguna.py` | |
| `POST /admin/pengguna/{id}/reset-password` | `admin.py` | `services/pengguna.py` | |
| `PUT /arah-baik/{id}` | `indikator.py`/`admin.py` | `services/indikator.py` | |
| `GET /capaian` | `capaian.py` | `services/capaian.py` | `indicator_payload` jadi service. |
| `GET /indikator/{id}/detail` | `indikator.py` | `services/capaian.py` | |
| `GET /indikator/{id}/unduh.csv` | `ekspor.py` | `services/ekspor.py` | |
| `GET /analitik/selisih/{id}` | `analitik.py` | `services/analitik.py` | |
| `GET /analitik/peringkat` | `analitik.py` | `services/analitik.py` | |
| `GET /analitik/gap/{id}` | `analitik.py` | `services/analitik.py` | |
| `GET /analitik/multi` | `analitik.py` | `services/analitik.py` | |
| `GET /analitik/korelasi` | `analitik.py` | `services/analitik.py` | Pearson jadi fungsi murni. |
| `POST /admin/usulan` | `usulan.py` | `services/verifikasi.py` | unggah bukti jadi service terpisah. |
| `GET /admin/usulan` | `usulan.py` | `repositories/tata_kelola.py` | |
| `GET /admin/usulan/{id}/bukti` | `usulan.py` | `repositories/tata_kelola.py` | |
| `GET /admin/usulan/{id}/bukti/{eid}` | `usulan.py` | `services/bukti.py` | |
| `POST /admin/usulan/{id}/verifikasi` | `usulan.py` | `services/verifikasi.py` | **titik kritis** — lihat §3. |
| `GET /admin/log` | `admin.py` | `repositories/tata_kelola.py` | |
| `POST /admin/unggah/pratinjau` | `unggahan.py` | `services/unggahan.py` | |
| `POST /admin/unggah/{id}/setujui` | `unggahan.py` | `services/unggahan.py` | |
| `GET /download/paket.zip` | `ekspor.py` | `services/ekspor.py` | |

## 2. Pola penulisan ulang query SQL mentah → ORM

Semua pemanggilan `rows(db, "...")` / `one(db, "...")` dihapus. Contoh transformasi:

**Sebelum (di `features_api.py`):**

```python
def latest_period_value(db, indicator_id, year, wilayah_kode="65"):
    if wilayah_kode == "65":
        return one(db, "SELECT nilai,periode,label_periode FROM beranda_nilai_periode WHERE ...")
    return one(db, "SELECT ... FROM beranda_nilai_wilayah_periode WHERE ...")
```

**Sesudah (di `repositories/nilai.py`):**

```python
def latest_period_value(session, indicator_id, year, wilayah_kode):
    stmt = (
        select(NilaiIndikator)
        .where(
            NilaiIndikator.id_indikator == indicator_id,
            NilaiIndikator.wilayah_kode == wilayah_kode,
            NilaiIndikator.tahun == year,
            NilaiIndikator.jenis == "realisasi",
            NilaiIndikator.status_verifikasi == "DISETUJUI",
            NilaiIndikator.periode.is_not(None),
        )
        .order_by(NilaiIndikator.periode.desc())
        .limit(1)
    )
    return session.scalars(stmt).first()
```

Aturan:
- Query filter yang diulang (mis. `status_verifikasi == "DISETUJUI"`) diekstrak ke
  fungsi helper repo (`_verified(stmt)`) atau `selectinload`/`where` bersama.
- Enum (jenis, status, peran) dinyatakan sebagai konstanta modul, bukan literal
  tersebar.
- Paginasi distandarkan (helper `paginate` bersama) untuk endpoint yang mengembalikan
  daftar; saat ini `validitas` mengembalikan semua baris tanpa batas — diberi paginasi
  atau batas aman.

## 3. Titik kritis: `verify_submission`

Saat ini fungsi ini menulis ke banyak tabel (lihat model-data.md §2.3). Setelah
konsolidasi, alurnya menjadi:

```python
# services/verifikasi.py (pseudocode)
def putuskan(session, submission_id, keputusan, alasan, verifikator):
    usulan = repo.get_usulan_menunggu(session, submission_id)
    validasi_keputusan(usulan, keputusan, alasan, verifikator)  # aturan bisnis murni
    if keputusan == "DISETUJUI":
        nilai = hitung_nilai_terbit(usulan)             # nilai + periode + wilayah
        repo.upsert_nilai(session, nilai)               # SATU tabel: nilai_indikator
    repo.ubah_status_usulan(session, usulan, keputusan, alasan, verifikator)
    repo.catat_log_perubahan(session, usulan, nilai_lama=...)
    repo.catat_log_aktivitas(session, verifikator, keputusan)
    session.commit()
```

Seluruh proses berjalan dalam **satu transaksi** (`session.commit()` sekali). Tidak
ada lagi `db.execute` terpisah-pisah.

Aturan bisnis yang harus dipindah ke service murni (diuji tanpa DB):
- Validasi: operator hanya realisasi; verifikator harus di provinsi; tidak boleh
  memverifikasi usulan sendiri; alasan wajib untuk penolakan.
- Perhitungan `published_value` (periode terbaru menggantikan nilai tahunan).
- Aturan `achievement()` dan `progress_towards()` (sudah ada, tinggal dipindah).

## 4. Skema Pydantic

Setiap endpoint memakai skema respons eksplisit (atau minimal `response_model`) agar
kontrak JSON terdokumentasi di OpenAPI. Contoh `schemas/beranda.py`:

```python
class KetersediaanKelompok(BaseModel):
    kode: str
    label: str
    jumlah_kelompok: int
    jumlah_indikator: int
    slot_terisi: int
    slot_total: int
    persentase: float

class BerandaResponse(BaseModel):
    tahun: int | None
    wilayah_kode: str
    tahun_tersedia: list[int]
    indikator_makro: list[IndikatorMakro]
    sasaran_visi: list[SasaranVisi]
    ketersediaan_kelompok: list[KetersediaanKelompok]
    status_data: str
```

Form `Form(...)` saat ini (pada login, pembuatan pengguna, usulan, verifikasi)
sebaiknya tetap `Form` bila frontend mengirim `multipart/form-data`, tetapi dibungkus
skema Pydantic untuk validasi yang konsisten.

## 5. Konfigurasi terpusat (`config.py`)

Menggantikan `os.getenv` yang tersebar di `features_api.py`, `main.py`, `database.py`.

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SEBATIK_")

    database_url: str
    secret_key: str
    archive_dir: Path
    evidence_dir: Path
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    access_token_ttl_hours: int = 8
    kode_provinsi: str = "65"
    max_bukti_bytes: int = 10 * 1024 * 1024
    max_unggah_bytes: int = 30 * 1024 * 1024
```

- Nama env saat ini `SEBATIK_DATABASE_URL`, `SEBATIK_ARCHIVE_DIR`, dst. dipertahankan
  agar `.env` produksi tidak berubah.
- `secret_key` wajib ada di produksi; aplikasi menolak mulai bila masih default
  (lihat auth-keamanan.md).

## 6. Penanganan kesalahan

- Pakai `HTTPException` dengan kode yang sudah dipakai (401/403/404/409/410/413/422)
  agar kontrak error tidak berubah.
- Ganti `except Exception` yang terlalu luas (mis. saat login → `409`, saat pratinjau
  → `422`) dengan penanganan spesifik:
  - pelanggaran unik → `IntegrityError` → 409;
  - file tidak valid → `ValueError`/`WorkbookError` → 422.
- Tambah exception handler global untuk mencatat stack trace ke log dan mengembalikan
  500 generik tanpa membocorkan detail.

## 7. Penghapusan efek samping impor

Saat ini `database.py` menjalankan `migrate_governance()` dan `seed_verified_master()`
pada saat import. Ini dihapus:

- Skema → dikelola Alembic (lihat migrasi-postgresql.md).
- Seed data awal (wilayah, admin, operator) → perintah CLI/script eksplisit
  (`python -m backend.app.cli seed`) atau langkah Alembic data migration.

## 8. Kriteria selesai per modul

- Router tidak berisi SQL atau perhitungan.
- Setiap service punya unit test murni.
- Setiap repository punya test integrasi terhadap database uji.
- Tidak ada `text("...")` tersisa di `routers/` dan `services/`.
- Semua endpoint lama lolos uji kontrak (lihat testing-ci.md).
