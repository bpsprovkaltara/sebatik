/* ============================================================================
   SEBATIK — Daftar rute
   ----------------------------------------------------------------------------
   Satu tempat untuk semua jalur halaman. Sebelumnya string hash seperti
   '#capaian' tersebar di bilah atas, pintu beranda, dan setiap halaman; menamai
   ulang satu rute berarti mencarinya ke seluruh berkas.

   Aplikasi memakai HashRouter, bukan BrowserRouter: backend menyajikan SPA
   lewat StaticFiles(html=True) yang tidak mengembalikan index.html untuk jalur
   sembarang, sehingga BrowserRouter akan 404 pada tautan-dalam. Keputusan ini
   dicatat di sini sesuai catatan pada docs/refactoring/frontend.md §3.
   ========================================================================== */

export const RUTE = {
  beranda: '/',
  indikator: '/indikator',
  capaian: '/capaian',
  detail: '/detail',
  insight: '/insight',
  validitas: '/validitas',
  analitik: '/analitik',
  masuk: '/masuk',
}

/* Bentuk href untuk <a>. HashRouter membaca bagian setelah '#'. */
export const ke = jalur => `#${jalur}`
export const keDetail = id => `#${RUTE.detail}/${id}`

/* Tautan lama tanpa garis miring ('#capaian') masih beredar di penanda buku dan
   dokumen. Peta ini memindahkannya ke bentuk baru sekali di awal muat, supaya
   tautan yang sudah tersebar tidak mati. */
const TAUTAN_LAMA = {
  '#beranda': RUTE.beranda,
  '#indikator': RUTE.indikator,
  '#capaian': RUTE.capaian,
  '#insight': RUTE.insight,
  '#validitas': RUTE.validitas,
  '#analitik': RUTE.analitik,
  '#login': RUTE.masuk,
  '#admin': RUTE.masuk,
}

export function alihkanTautanLama(hash = location.hash){
  if(!hash || hash.startsWith('#/')) return null
  if(hash.startsWith('#detail/')) return `${RUTE.detail}/${hash.slice('#detail/'.length)}`
  return TAUTAN_LAMA[hash] ?? null
}
