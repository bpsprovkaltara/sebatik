# Pengujian & CI

Dokumen ini menjabarkan strategi pengujian, linting/type checking, dan pipeline CI
untuk memastikan refactoring tidak merusak perilaku.

## 1. Kondisi saat ini

- Backend: `python -m pytest -q` (5 file tes, cakupan tipis). `test_api.py` hanya 2
  tes; `test_etl_integration.py` menguji pipeline asli; `test_common.py`,
  `test_arah_baik.py`, `test_features.py` menguji fungsi kecil.
- Frontend: `pnpm test` (Vitest). `ui.test.jsx` (70 baris) dan `App.test.jsx` (3 baris).
- Tidak ada linting/type check backend (ruff/mypy) maupun frontend (eslint) yang
  terpasang di CI. Tidak ada pipeline CI.

## 2. Piramida pengujian target

```
        ┌──────────────┐
        │  E2E (sedikit)│   alur kunci: login -> usulan -> verifikasi -> tampil
        ├──────────────┤
        │  Integrasi   │   endpoint kontrak, repository, migrasi
        ├──────────────┤
        │  Unit (banyak)│   service murni, transform ETL, komponen UI
        └──────────────┘
```

## 3. Backend

### 3.1 Unit test (service murni, tanpa DB)

- `services/capaian.py`: `achievement()`, `progress_towards()` (kasus NAIK/TURUN,
  denominator 0, clamp 0–100), penyusunan kalimat `insight`.
- `services/analitik.py`: korelasi Pearson (n<4, n cukup), `gap`, `required_run_rate`,
  `peringkat`.
- `services/verifikasi.py`: semua aturan validasi keputusan (operator hanya realisasi,
  tidak verifikasi sendiri, alasan wajib untuk tolak, verifikator harus provinsi).
- `transform/normalize.py` (`parse_angka`, `clean_text`, `indicator_id`,
  `enum_rpjmd`) — sudah ada tes, pertahankan.

### 3.2 Integrasi (repository + endpoint kontrak)

- Uji repository terhadap PostgreSQL uji (atau SQLite in-memory sebagai fallback
  cepat bila perbedaan dialek tidak relevan).
- Uji kontrak endpoint: pertahankan bentuk respons publik. Rekam `response_model`
  dan tulis tes yang memanggil setiap endpoint dengan TestClient dan membandingkan
  kunci/bentuk JSON terhadap skema.

### 3.3 Test kontrak API (anti-regresi saat refactor)

Karena target refactoring menjaga kontrak publik, buat tes yang menegaskan:
- `GET /api/v1/indikator` mengembalikan `data`, `total`, `page`, `page_size`.
- `GET /api/v1/beranda` mengembalikan kunci `indikator_makro`, `sasaran_visi`,
  `ketersediaan_kelompok`, `status_data`.
- `POST /api/v1/auth/login` mengembalikan `access_token`, `token_type`, `peran`.
- dst. untuk setiap endpoint yang ada. Tes ini memastikan migrasi internal tidak
  mengubah API.

## 4. Frontend

- Unit test komponen murni: `MetricCard`, `CapaianBadge`, `TooltipCard`, `format.js`.
- Test hook: `useToken`/`useProfile`, `useTheme`, `useFetch` (dengan mock fetch).
- Test layer API: `api/client.js` menyisipkan header auth dan menangani 401.

## 5. Linting & type checking

- Backend: `ruff check` + `ruff format` (ganti gaya ad hoc), `mypy` (bertahap).
  Tambah konfigurasi `pyproject.toml`.
- Frontend: `eslint` + `prettier` (Prettier sudah di devDependencies). Tambah config.
- Aturan dijalankan di CI dan di-*enforce* pada pull request.

## 6. Pipeline CI (GitHub Actions)

Berkas `.github/workflows/ci.yml`:

```yaml
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_USER: sebatik, POSTGRES_PASSWORD: sebatik, POSTGRES_DB: sebatik_test }
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check .
      - run: mypy backend src
      - run: pytest -q
        env: { SEBATIK_DATABASE_URL: postgresql+psycopg://sebatik:sebatik@localhost:5432/sebatik_test }

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - run: pnpm install --frozen-lockfile
        working-directory: frontend
      - run: pnpm test
        working-directory: frontend
      - run: pnpm build
        working-directory: frontend
```

Tambahan:
- `requirements-dev.txt` berisi `ruff`, `mypy`, `pytest`, `httpx` (test), `alembic`.
- Jalankan `alembic upgrade head` pada DB uji sebelum `pytest` agar migrasi terverifikasi.

## 7. Metrik target

| Aspek | Target |
|---|---|
| Cakupan unit service murni | 100% untuk fungsi perhitungan/validasi kritis. |
| Cakupan endpoint kontrak | setiap endpoint punya minimal 1 tes bentuk respons. |
| Cakupan keseluruhan backend | ≥ 80% (bertahap dari saat ini). |
| Frontend | test komponen & hook utama; build selalu hijau. |
| Lint/type | `ruff`, `eslint`, `prettier` bersih di CI. |

## 8. Kriteria selesai

- CI hijau untuk setiap PR.
- Test kontrak API membuktikan tidak ada perubahan bentuk respons publik.
- Tidak ada file kode baru tanpa test yang relevan.
- Migrasi Alembic dapat `upgrade` dan `downgrade` di lingkungan uji.
