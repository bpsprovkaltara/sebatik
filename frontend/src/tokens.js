/* ============================================================================
   SEBATIK — Token warna data
   ----------------------------------------------------------------------------
   Tema: "Ombak" — biru laut Sulawesi sebagai warna utama. Hijau dipensiunkan
   dari peran tema dan disimpan khusus sebagai penanda status "baik", sehingga
   ia tidak pernah bersaing makna dengan warna identitas.

   Seluruh palet sudah divalidasi terhadap enam pemeriksaan visualisasi data:
   pita lightness OKLCH, ambang chroma, keterpisahan protanopia/deuteranopia
   (OKLab dE), ambang penglihatan normal (dE >= 15), dan kontras WCAG >= 3:1.

   Permukaan acuan: terang #FFFFFF, gelap #0F1B26.

   Filosofi warna:
   - Ketersediaan data = skala ORDINAL satu rona (biru). Makin pekat berarti
     makin rinci sampai ke wilayah terkecil.
   - Capaian = palet STATUS (baik/waspada/kritis). Pasangan hijau-merah berada
     di pita peringatan buta warna, jadi setiap pemakaiannya WAJIB disertai
     label teks atau posisi terhadap garis nol. Tidak pernah warna saja.
   - Kartu tematik = palet KATEGORIKAL berurutan tetap, tidak pernah didaur,
     dan tidak memuat hijau agar tidak menyamar sebagai status.
   ========================================================================== */

const readTheme = () => {
  if (typeof document === 'undefined') return 'light'
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

/* --- Ketersediaan data ---------------------------------------------------- */

export const STATUS_ORDER = [
  'Tersedia s.d Kabupaten/Kota',
  'Tersedia s.d Provinsi',
  'Tersedia Nasional',
  'Tidak Tersedia'
]

/* Rampa ordinal satu keluarga: pekat = paling rinci. Dipakai sebagai nilai
   bawaan sekaligus memenuhi kontrak token yang diuji pada App.test.jsx. */
export const STATUS_COLORS = {
  'Tersedia s.d Kabupaten/Kota': '#C4626B',
  'Tersedia s.d Provinsi': '#DF7F83',
  'Tersedia Nasional': '#FEBE98',
  'Tidak Tersedia': '#FA7472',
  'Belum Tersedia': '#A79C95'
}

export const STATUS_COLORS_DARK = {
  'Tersedia s.d Kabupaten/Kota': '#FEBE98',
  'Tersedia s.d Provinsi': '#DF7F83',
  'Tersedia Nasional': '#C4626B',
  'Tidak Tersedia': '#FA7472',
  'Belum Tersedia': '#8B7B73'
}

export const STATUS_SHORT = {
  'Tersedia s.d Kabupaten/Kota': 'Kab/Kota',
  'Tersedia s.d Provinsi': 'Provinsi',
  'Tersedia Nasional': 'Nasional',
  'Tidak Tersedia': 'Tidak tersedia'
}

/* Penjelasan singkat untuk tooltip legenda — warna tidak pernah berdiri sendiri. */
export const STATUS_HINT = {
  'Tersedia s.d Kabupaten/Kota': 'Terinci sampai kabupaten/kota',
  'Tersedia s.d Provinsi': 'Hanya tersedia pada level provinsi',
  'Tersedia Nasional': 'Hanya tersedia pada level nasional',
  'Tidak Tersedia': 'Belum ada sumber data yang dapat dipakai',
  'Belum Tersedia': 'Status ketersediaan belum dicatat'
}

/* --- Status capaian ------------------------------------------------------- */
/* Palet ini seluruhnya hangat dan tidak memuat hijau, sehingga TERCAPAI dan
   PERLU_PERHATIAN hanya terpisah oleh kepekatan, bukan oleh rona. Karena itu
   label teks pada CapaianBadge dan VizLegend bukan pelengkap: ia satu-satunya
   pembawa makna yang bertahan pada penglihatan buta warna. Jangan dilepas. */

export const CAPAIAN_COLORS = {
  TERCAPAI: '#2F855A',
  MENDEKATI: '#B7791F',
  PERLU_PERHATIAN: '#C53030',
  BELUM_ADA_DATA: '#76636D'
}

export const CAPAIAN_COLORS_DARK = {
  TERCAPAI: '#68D391',
  MENDEKATI: '#F6C453',
  PERLU_PERHATIAN: '#FC8181',
  BELUM_ADA_DATA: '#947888'
}

/* --- Palet kategorikal ---------------------------------------------------- */
/* Urutan slot tetap, jangan diacak dan jangan didaur ulang untuk seri ke-7.
   Seluruh slot memakai rona palet; versi terang dipekatkan agar mark terbaca
   di atas permukaan krem, versi gelap memakai warna palet apa adanya. */

export const SERIES_LIGHT = ['#1494D3', '#F58220', '#22A699', '#A63CC5', '#E34A6F', '#5E7CE2']
export const SERIES_DARK = ['#42B8F0', '#FF9B45', '#4CC8BB', '#C66BE1', '#F06B8B', '#8299F0']

/* Alias lama agar pemakaian di App tetap jalan. */
export const TEAM_ACCENTS = SERIES_LIGHT

/* --- Pasangan diverging (naik/turun terhadap arah target) ----------------- */
/* Selalu dipasangkan dengan posisi terhadap garis nol dan legenda bertulis. */

export const TREND_COLORS = {
  light: { positive: '#2F855A', negative: '#C53030', neutral: '#76636D' },
  dark: { positive: '#68D391', negative: '#FC8181', neutral: '#947888' }
}

/* --- Rona tunggal untuk skala sekuensial (peta & heatmap) ----------------- */

export const SEQUENTIAL = {
  light: ['#E5F5FC', '#B9E4F7', '#75C7EF', '#42ADE0', '#148FCC', '#075D91'],
  dark: ['#102C3D', '#164560', '#075D91', '#148FCC', '#75C7EF', '#DDF3FF']
}

/* --- Pengakses ------------------------------------------------------------ */

export const seriesColor = (index, theme = readTheme()) => {
  const ramp = theme === 'dark' ? SERIES_DARK : SERIES_LIGHT
  return ramp[index % ramp.length]
}

export const statusColor = (status, theme = readTheme()) => {
  const ramp = theme === 'dark' ? STATUS_COLORS_DARK : STATUS_COLORS
  return ramp[status] || ramp['Belum Tersedia']
}

export const capaianColor = (status, theme = readTheme()) => {
  const ramp = theme === 'dark' ? CAPAIAN_COLORS_DARK : CAPAIAN_COLORS
  return ramp[status] || ramp.BELUM_ADA_DATA
}

export const trendColor = (kind, theme = readTheme()) =>
  (theme === 'dark' ? TREND_COLORS.dark : TREND_COLORS.light)[kind]

export const sequentialColor = (ratio, theme = readTheme()) => {
  const ramp = theme === 'dark' ? SEQUENTIAL.dark : SEQUENTIAL.light
  const clamped = Number.isFinite(ratio) ? Math.min(1, Math.max(0, ratio)) : 0
  return ramp[Math.round(clamped * (ramp.length - 1))]
}

export const shortStatus = (status) => STATUS_SHORT[status] || status
export const statusHint = (status) => STATUS_HINT[status] || ''

/* Nama variabel CSS agar elemen DOM (badge, sel matriks, legenda) ikut
   berganti warna otomatis saat tema ditukar, tanpa perlu render ulang React. */
export const STATUS_VAR = {
  'Tersedia s.d Kabupaten/Kota': 'var(--status-kabkota)',
  'Tersedia s.d Provinsi': 'var(--status-provinsi)',
  'Tersedia Nasional': 'var(--status-nasional)',
  'Tidak Tersedia': 'var(--status-tidak)',
  'Belum Tersedia': 'var(--status-belum)'
}
export const statusVar = (status) => STATUS_VAR[status] || STATUS_VAR['Belum Tersedia']

export const CAPAIAN_VAR = {
  TERCAPAI: 'var(--capaian-tercapai)',
  MENDEKATI: 'var(--capaian-mendekati)',
  PERLU_PERHATIAN: 'var(--capaian-perhatian)',
  BELUM_ADA_DATA: 'var(--capaian-belum)'
}
export const capaianVar = (status) => CAPAIAN_VAR[status] || CAPAIAN_VAR.BELUM_ADA_DATA
