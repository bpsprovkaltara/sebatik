/* ============================================================================
   SEBATIK — Satu pintu untuk semua permintaan ke API
   ----------------------------------------------------------------------------
   Sebelumnya `api.js` hanya membungkus `fetch` tanpa header autentikasi, jadi
   setiap tempat yang butuh token menyusun sendiri header dan penanganan 401-nya.
   Akibatnya sesi yang kedaluwarsa ditangani berbeda-beda di tiap halaman.

   Di sini token disisipkan sekali, dan 401 selalu berarti hal yang sama:
   sesinya sudah mati, bersihkan token supaya bilah atas tidak lagi menawarkan
   ruang kerja yang tak dapat dibuka.
   ========================================================================== */
import {clearToken, getToken, segarkanToken} from '../auth'

export class ApiError extends Error{
  constructor(status, pesan, detail){
    super(pesan)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export const qs = params => {
  const out = new URLSearchParams()
  Object.entries(params || {}).forEach(([key, value]) => {
    if(Array.isArray(value)) value.filter(Boolean).forEach(v => out.append(key, v))
    else if(value !== '' && value != null) out.set(key, value)
  })
  return out.toString()
}

async function bacaDetail(response){
  try{
    const isi = await response.json()
    return isi?.detail ?? isi
  }catch{
    return null
  }
}

const berkepala = (token, headers) => {
  const hasil = {...(headers || {})}
  if(token) hasil.Authorization = `Bearer ${token}`
  return hasil
}

/* `autentikasi:'wajib'` menandai permintaan yang memang butuh sesi; 401 di
   sana mencoba menyegarkan sesi lebih dulu, dan baru membersihkan token bila
   penyegaran pun gagal. Endpoint publik memakai 'opsional' sehingga token basi
   tidak membuat halaman publik ikut gagal.

   Penyegaran dicoba tepat sekali per permintaan: bila permintaan ulang dengan
   token baru masih 401, masalahnya bukan token kedaluwarsa. */
export async function request(path, {autentikasi = 'opsional', headers, ...options} = {}){
  const token = getToken()
  let response = await fetch(path, {...options, headers: berkepala(token, headers)})

  if(response.status === 401 && token){
    const baru = await segarkanToken()
    if(baru) response = await fetch(path, {...options, headers: berkepala(baru, headers)})
  }

  if(response.status === 401){
    if(getToken()) clearToken()
    if(autentikasi === 'wajib') throw new ApiError(401, 'Sesi berakhir. Silakan masuk kembali.', null)
    /* Ulangi tanpa token: endpoint publik tetap harus tampil bagi tamu. */
    const ulang = await fetch(path, options)
    if(ulang.ok) return ulang.json()
    throw new ApiError(ulang.status, `API gagal (${ulang.status})`, await bacaDetail(ulang))
  }
  if(!response.ok) throw new ApiError(response.status, `API gagal (${response.status})`, await bacaDetail(response))
  return response.json()
}

/* Untuk unduhan biner (bukti dukung): pemanggil butuh Response, bukan JSON. */
export async function requestMentah(path, options = {}){
  const token = getToken()
  const response = await fetch(path, {...options, headers: berkepala(token, options.headers)})
  if(response.status !== 401 || !token) return response
  const baru = await segarkanToken()
  if(!baru) return response
  return fetch(path, {...options, headers: berkepala(baru, options.headers)})
}
