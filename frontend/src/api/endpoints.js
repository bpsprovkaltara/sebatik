/* Satu fungsi per endpoint. Halaman memanggil fungsi ini, bukan menyusun URL
   sendiri, supaya perubahan jalur API tidak perlu dicari ke seluruh halaman. */
import {qs, request, requestMentah} from './client'

const V1 = '/api/v1'
const denganQuery = (path, params) => {
  const query = qs(params)
  return query ? `${path}?${query}` : path
}

/* --- publik --------------------------------------------------------------- */
export const beranda = params => request(denganQuery(`${V1}/beranda`, params))
export const indikatorExplorer = () => request(`${V1}/indikator-explorer`)
export const indikatorExplorerDetail = (id, params) =>
  request(denganQuery(`${V1}/indikator-explorer/${id}`, params))
export const capaianExplorer = () => request(`${V1}/capaian-explorer`)
export const capaianExplorerDetail = (id, params) =>
  request(denganQuery(`${V1}/capaian-explorer/${id}`, params))
export const insight = params => request(denganQuery(`${V1}/insight`, params))
export const validitas = params => request(denganQuery(`${V1}/validitas`, params))
export const metadataIndikator = id => request(`${V1}/beranda-indikator/${id}/metadata`)
export const detailIndikator = id => request(`${V1}/indikator/${id}/detail`)
export const wilayah = () => request(`${V1}/wilayah`)
export const capaian = params => request(denganQuery(`${V1}/capaian`, params))

/* --- analitik ------------------------------------------------------------- */
export const peringkat = () => request(`${V1}/analitik/peringkat`)
export const gap = id => request(`${V1}/analitik/gap/${id}`)
export const selisihTahunan = id => request(`${V1}/analitik/selisih/${id}`)
export const korelasi = (x, y) => request(denganQuery(`${V1}/analitik/korelasi`, {x, y}))

/* --- autentikasi ---------------------------------------------------------- */
export const login = form =>
  request(`${V1}/auth/login`, {method: 'POST', body: form})
export const profilSaya = () => request(`${V1}/auth/saya`, {autentikasi: 'wajib'})
export const gantiPassword = form =>
  request(`${V1}/auth/ganti-password`, {method: 'POST', body: form, autentikasi: 'wajib'})

/* --- tata kelola ---------------------------------------------------------- */
const wajib = {autentikasi: 'wajib'}
export const daftarUsulan = params => request(denganQuery(`${V1}/admin/usulan`, params), wajib)
export const kirimUsulan = form =>
  request(`${V1}/admin/usulan`, {method: 'POST', body: form, ...wajib})
export const buktiUsulan = id => request(`${V1}/admin/usulan/${id}/bukti`, wajib)
export const berkasBukti = (usulanId, buktiId) =>
  requestMentah(`${V1}/admin/usulan/${usulanId}/bukti/${buktiId}`)
export const verifikasiUsulan = (id, form) =>
  request(`${V1}/admin/usulan/${id}/verifikasi`, {method: 'POST', body: form, ...wajib})
export const daftarPengguna = () => request(`${V1}/admin/pengguna`, wajib)
export const buatPengguna = form =>
  request(`${V1}/admin/pengguna`, {method: 'POST', body: form, ...wajib})
export const ubahStatusPengguna = (id, form) =>
  request(`${V1}/admin/pengguna/${id}/status`, {method: 'PATCH', body: form, ...wajib})
export const resetPassword = (id, form) =>
  request(`${V1}/admin/pengguna/${id}/reset-password`, {method: 'POST', body: form, ...wajib})
export const logAudit = () => request(`${V1}/admin/log`, wajib)
export const koreksiArahBaik = (id, form) =>
  request(`${V1}/arah-baik/${id}`, {method: 'PUT', body: form, ...wajib})
export const pratinjauUnggahan = form =>
  request(`${V1}/admin/unggah/pratinjau`, {method: 'POST', body: form, ...wajib})
export const setujuiUnggahan = id =>
  request(`${V1}/admin/unggah/${id}/setujui`, {method: 'POST', ...wajib})

export {qs}
