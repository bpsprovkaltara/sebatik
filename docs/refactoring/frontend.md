# Refactoring Frontend

Frontend tetap **JavaScript** (tidak migrasi TypeScript), tetapi dipecah dari satu
file `App.jsx` (2292 baris) menjadi struktur halaman/komponen yang modular, dengan
routing library dan state management terpusat.

## 1. Kondisi saat ini

- `App.jsx` memuat semua halaman dan komponen dalam satu file: halaman Beranda,
  IndicatorExplorer, Capaian, Detail, Insight, Validity, Analytics, OperatorFlow,
  AdminPage, serta komponen bersama (Topbar, Shell, SiteFooter, CardRail, MacroCards,
  KaltaraMap, MetadataModal, SubmissionTable, PasswordResetModal, dst.).
- Navigasi berbasis hash manual (bukan router).
- `api.js` hanya 2 baris (`api()` + `qs()`), tanpa header auth.
- State autentikasi/theme memakai pub/sub ad hoc (`auth.js`, `theme.js`).
- `ui.jsx`, `tokens.js`, `Brand.jsx`, `styles.css` relatif baik dan dipertahankan.

## 2. Target struktur

Lihat pohon lengkap di [arsitektur-target.md](arsitektur-target.md) §1. Ringkas:

```
frontend/src/
├── App.jsx                 # hanya router + Shell
├── main.jsx
├── api/
│   ├── client.js           # fetch + Authorization header + error handling
│   └── endpoints.js        # satu fungsi per endpoint (beranda, explorer, ...)
├── pages/                  # satu file per halaman
├── components/             # layout, charts, home, explorer, admin
├── hooks/                  # useFetch, useAuth, useTheme, usePageTitle
├── context/                # AuthProvider, ThemeProvider
├── lib/                    # formatter, geoPaths, nilai
└── auth.js theme.js tokens.js Brand.jsx ui.jsx styles.css
```

## 3. Routing

- Ganti hash manual dengan `react-router-dom` (tambah ke `package.json`).
- Rute:

| Hash saat ini | Path target |
|---|---|
| `#/` / beranda | `/` |
| `#/indikator` | `/indikator` |
| `#/capaian` | `/capaian` |
| `#/detail/{id}` | `/detail/:id` |
| `#/insight` | `/insight` |
| `#/validitas` | `/validitas` |
| `#/analitik` | `/analitik` |
| `#/masuk` | `/masuk` |
| `#/admin` | `/admin` |

- Karena backend menyajikan SPA via `StaticFiles(html=True)`, sertakan fallback ke
  `index.html` untuk semua rute (konfigurasi server atau `BrowserRouter` + fallback).
  Bila fallback sulit pada deploy saat ini, pertahankan `HashRouter` agar tidak ada
  perubahan server — keputusan dicatat saat implementasi.

## 4. Pemecahan `App.jsx`

Peta komponen → file target (berdasarkan simbol yang ada):

| Simbol saat ini | Tujuan |
|---|---|
| `App` | `App.jsx` (hanya router + providers). |
| `Shell`, `Topbar`, `SiteFooter`, `LoginShell` | `components/layout/`. |
| `HomeHero`, `HomeDoors`, `MacroCards`, `CardRail`, `YearPicker` | `components/home/`. |
| `KaltaraMap`, `geoPaths` | `components/maps/` + `lib/geo.js`. |
| `TooltipCard`, `AnnualChangeTooltip`, `MetricCard`, `CapaianBadge` | `components/charts/`. |
| `MetadataModal` | `components/explorer/`. |
| `SubmissionTable`, `PasswordResetModal`, `OperatorFlow` | `components/admin/`. |
| `HomePage` | `pages/HomePage.jsx`. |
| `IndicatorExplorerPage` | `pages/IndicatorExplorerPage.jsx`. |
| `CapaianPage` | `pages/CapaianPage.jsx`. |
| `DetailPage` | `pages/DetailPage.jsx`. |
| `InsightPage` | `pages/InsightPage.jsx`. |
| `ValidityPage` | `pages/ValidityPage.jsx`. |
| `AnalyticsPage` | `pages/AnalyticsPage.jsx`. |
| `AdminPage` | `pages/AdminPage.jsx`. |
| `usePageTitle`, `fmt`, `valueLabel`, `hasNumber`, `valueTone`, `growthTone`, `softNumber` | `hooks/usePageTitle.js`, `lib/format.js`. |

## 5. Layer API tersentralisasi

`api.js` saat ini tidak menyisipkan token. Buat `api/client.js`:

```js
export async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(path, { ...options, headers })
  if (response.status === 401) { clearToken(); /* arahkan ke /masuk */ }
  if (!response.ok) throw new ApiError(response.status, await response.text())
  return response.json()
}
```

`api/endpoints.js` mengelompokkan fungsi per domain agar halaman tidak memanggil
`fetch` langsung:

```js
export const beranda = (params) => request(`/api/v1/beranda?${qs(params)}`)
export const indikatorExplorer = () => request('/api/v1/indikator-explorer')
export const login = (form) => request('/api/v1/auth/login', { method: 'POST', body: form })
// ... semua endpoint
```

Setiap halaman memakai fungsi dari `endpoints.js`, bukan string URL langsung.

## 6. State management

- Ganti pub/sub ad hoc (`auth.js`, `theme.js`) dengan Context + hook (tetap bisa
  dipertahankan bila ingin minim perubahan, tetapi Context lebih idiomatis):
  - `AuthProvider` membungkus `useToken` + `useProfile` dan menyediakan `user`,
    `login`, `logout`.
  - `ThemeProvider` membungkus `theme.js`.
- Data per halaman tetap state lokal + hook `useFetch` (fetch + loading + error +
  cancel-on-unmount), menggantikan `useEffect` berulang yang ada.
- Tidak memakai Redux; skala aplikasi belum membutuhkannya.

## 7. Konsistensi & kualitas

- Pertahankan sistem desain (`tokens.js`, `styles.css`, `Brand.jsx`, `ui.jsx`) sebagai
  sumber kebenaran visual; jangan duplikasi warna/ukuran di halaman.
- Ekstrak helper format angka/nilai ke `lib/format.js` agar konsisten (saat ini
  `fmt`, `valueLabel`, dsb. didefinisikan di `App.jsx`).
- Tambah ESLint + Prettier (Prettier sudah ada di devDependencies) dan jalankan di CI
  (lihat testing-ci.md).
- Tulis test komponen untuk komponen murni (mis. `MetricCard`, `CapaianBadge`,
  `TooltipCard`) dengan Vitest + Testing Library (sudah tersedia).

## 8. Kriteria selesai

- `App.jsx` < ~150 baris (hanya router + providers).
- Tidak ada `fetch` langsung di komponen halaman (semua lewat `api/endpoints.js`).
- Tidak ada duplikasi formatter/warna lintas file.
- Navigasi hash lama diganti router (atau keputusan `HashRouter` terdokumentasi).
- Semua halaman tetap berfungsi dan uji UI yang ada tetap hijau.
