# Arsitektur Target

Dokumen ini menjabarkan bentuk akhir repo dan tanggung jawab tiap modul setelah
refactoring. Tujuannya: satu tempat untuk memahami "di mana kode seharusnya berada".

## 1. Struktur repo target

```
sebatik/
├── backend/
│   ├── app/
│   │   ├── main.py                 # factory app, middleware, mount static, include router
│   │   ├── config.py               # Settings (pydantic-settings) — satu-satunya sumber konfigurasi
│   │   ├── database.py             # engine, SessionLocal, get_db, get_session context manager
│   │   ├── db/
│   │   │   └── base.py             # DeclarativeBase + mixin id/waktu bila diperlukan
│   │   ├── models/                 # SEMUA model ORM (satu file per agregat)
│   │   │   ├── __init__.py
│   │   │   ├── indikator.py        # Indikator, NilaiIndikator, MetadataIndikator (konsolidasi)
│   │   │   ├── wilayah.py          # Wilayah
│   │   │   ├── pengguna.py         # Pengguna
│   │   │   ├── tata_kelola.py      # UsulanNilai, BuktiDukung, LogPerubahan, LogAktivitas, UnggahanExcel
│   │   │   └── master.py           # BerandaIndikator, BerandaNilai, dst. (jika tabel master dipertahankan)
│   │   ├── schemas/                # Skema Pydantic request/response per domain
│   │   │   ├── __init__.py
│   │   │   ├── indikator.py
│   │   │   ├── beranda.py
│   │   │   ├── capaian.py
│   │   │   ├── insight.py
│   │   │   ├── validitas.py
│   │   │   ├── analitik.py
│   │   │   ├── auth.py
│   │   │   └── admin.py
│   │   ├── routers/                # Lapisan HTTP tipis; tanpa logika bisnis
│   │   │   ├── __init__.py
│   │   │   ├── indikator.py
│   │   │   ├── beranda.py
│   │   │   ├── explorer.py
│   │   │   ├── capaian.py
│   │   │   ├── insight.py
│   │   │   ├── validitas.py
│   │   │   ├── analitik.py
│   │   │   ├── auth.py
│   │   │   ├── admin.py
│   │   │   ├── usulan.py
│   │   │   ├── unggahan.py
│   │   │   └── ekspor.py
│   │   ├── services/               # Logika bisnis murni (tanpa HTTP)
│   │   │   ├── __init__.py
│   │   │   ├── capaian.py          # achievement(), progres tracker
│   │   │   ├── insight.py
│   │   │   ├── analitik.py         # korelasi, gap, run-rate, peringkat
│   │   │   ├── ketersediaan.py     # availability_dimensions
│   │   │   ├── verifikasi.py       # alur MENUNGGU_VERIFIKASI -> DISETUJUI/DITOLAK (satu jalur tulis)
│   │   │   ├── ekspor.py           # CSV/XLSX/PDF/ZIP
│   │   │   └── unggahan.py         # staging + diff + persetujuan massal
│   │   ├── repositories/           # Akses data; satu fungsi per bentuk query
│   │   │   ├── __init__.py
│   │   │   ├── indikator.py
│   │   │   ├── nilai.py
│   │   │   ├── beranda.py
│   │   │   ├── wilayah.py
│   │   │   ├── pengguna.py
│   │   │   └── tata_kelola.py
│   │   ├── security.py             # hashing password, encode/decode JWT, dependencies require()
│   │   └── deps.py                 # current_user, require_roles, get_session
│   ├── alembic/                    # migrasi skema (env.py, versions/)
│   └── alembic.ini
├── src/
│   └── etl/                        # dipertahankan, di-refactor data-driven (lihat etl.md)
├── frontend/
│   └── src/
│       ├── main.jsx
│       ├── App.jsx                 # hanya routing + layout shell
│       ├── api/                    # layer API tersentralisasi
│       │   ├── client.js           # fetch wrapper + auth header
│       │   └── endpoints.js        # fungsi per endpoint
│       ├── pages/                  # satu file per halaman
│       │   ├── HomePage.jsx
│       │   ├── IndicatorExplorerPage.jsx
│       │   ├── CapaianPage.jsx
│       │   ├── DetailPage.jsx
│       │   ├── InsightPage.jsx
│       │   ├── ValidityPage.jsx
│       │   ├── AnalyticsPage.jsx
│       │   └── AdminPage.jsx
│       ├── components/             # komponen bersama & per halaman
│       │   ├── layout/             # Shell, Topbar, SiteFooter, LoginShell
│       │   ├── charts/             # TooltipCard, wrapper recharts
│       │   ├── home/               # Hero, Doors, MacroCards, CardRail
│       │   ├── explorer/           # subkomponen explorer/capaian/insight
│       │   └── admin/              # SubmissionTable, PasswordResetModal, dst.
│       ├── hooks/                  # useToken, useTheme, usePageTitle, useFetch
│       ├── lib/                    # formatter, nilai, geoPaths, warna
│       ├── context/                # AuthContext, ThemeContext (menggantikan pub/sub ad hoc)
│       ├── auth.js  theme.js tokens.js Brand.jsx ui.jsx styles.css  # dipertahankan/rapikan
├── scripts/                        # dipertahankan, disesuaikan ke PostgreSQL
├── tools/
├── tests/                          # backend
│   ├── unit/                       # service murni
│   ├── api/                        # kontrak endpoint
│   └── etl/
├── data/raw/
├── data/processed/
└── docs/
```

## 2. Aturan pemisahan lapisan

```
routers  ->  schemas  ->  services  ->  repositories  ->  models
 (HTTP)     (validasi)    (bisnis)      (query/data)      (ORM)
```

- **routers** hanya: menerima parameter, memanggil dependency, memanggil service,
  mengembalikan respons. Tidak boleh berisi SQL, perhitungan, atau aturan bisnis.
- **schemas** (Pydantic) adalah kontrak permintaan/tanggapan; menjadi sumber kebenaran
  bentuk JSON yang dikirim ke frontend.
- **services** berisi aturan bisnis murni (mis. `achievement`, `progress_towards`,
  perhitungan korelasi). Menerima nilai biasa (bukan objek `Request`), sehingga mudah
  diuji.
- **repositories** berisi query terhadap model ORM. Tidak boleh berisi aturan bisnis.
- **models** memodelkan tabel; tidak berisi logika query.

Aturan arah ketergantungan: `routers -> services -> repositories -> models`. Tidak
boleh ada impor ke arah sebaliknya (mis. `models` mengimpor `services`).

## 3. Factory aplikasi

`main.py` berubah menjadi factory sehingga dapat diuji tanpa efek samping impor.

```python
def create_app() -> FastAPI:
    app = FastAPI(title="API SEBATIK", docs_url="/api/docs", ...)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, ...)
    app.include_router(indikator.router)
    app.include_router(beranda.router)
    # ... semua router
    return app

app = create_app()
```

Migrasi/seed yang saat ini dijalankan saat import `database.py` (efek samping impor)
dipindah ke mekanisme eksplisit: Alembic untuk skema, perintah/script seed terpisah
untuk data awal. Tidak ada lagi mutasi database pada saat import modul.

## 4. Dependency injection

```python
# deps.py
def get_session():
    with SessionLocal() as session:
        yield session

def get_current_user(token=Depends(bearer), db=Depends(get_session)) -> Pengguna: ...
def require_roles(*roles):
    def dep(user=Depends(get_current_user)) -> Pengguna: ...
    return dep
```

Semua endpoint memakai `Depends(get_session)`; helper `rows()`/`one()` yang memakai
SQL mentah dihapus setelah semua query dipindah ke repository ORM.

## 5. Diagram arsitektur target

```
┌──────────────────────────────────────────────────────────────┐
│ Frontend (React + Vite, JS)                                   │
│  App.jsx (routing) → pages/ → components/ → api/endpoints     │
└───────────────────────────────┬──────────────────────────────┘
                                │ fetch /api/v1
┌───────────────────────────────▼──────────────────────────────┐
│ FastAPI                                                        │
│  routers (HTTP) ─► schemas (Pydantic)                         │
│       │                                                       │
│       ▼                                                       │
│  services (bisnis murni)                                      │
│       │                                                       │
│       ▼                                                       │
│  repositories (query ORM) ─► models (SQLAlchemy)              │
└───────────────────────────────┬──────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │ PostgreSQL             │
                    │ dikelola Alembic       │
                    └───────────────────────┘

ETL (src/etl, data-driven) ─► menulis via models/repository yang sama
```

## 6. Pertimbangan migrasi bertahap (strangler)

- Tahap awal, `models` dan `repositories` baru ditulis berdampingan dengan endpoint
  lama yang masih memakai SQL mentah; keduanya menunjuk tabel yang sama.
- Router baru dipindahkan satu per satu, diuji terhadap kontrak lama, lalu endpoint
  lama dihapus dari `features_api.py` hingga file tersebut kosong dan dihapus.
- Konsolidasi tabel (lihat model-data.md) dilakukan setelah lapisan repository
  tersedia, sehingga pemindahan query lebih aman.
