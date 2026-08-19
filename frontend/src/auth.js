import {useEffect,useState} from 'react'

/* ============================================================================
   SEBATIK — Status masuk yang dipakai bersama
   ----------------------------------------------------------------------------
   Sebelumnya token hanya hidup sebagai state lokal di dalam AdminPage, sehingga
   bilah atas tidak pernah tahu pengguna sudah masuk: ia terus menampilkan
   "Masuk" sementara tombol "Keluar" berdiri terpisah di badan ruang kerja.

   Berkas ini memindahkan token ke satu tempat dengan pola langganan yang sama
   seperti theme.js. Bilah atas, halaman validitas, dan ruang kerja berlangganan
   ke sumber yang sama, jadi ketiganya tidak pernah menampilkan keadaan berbeda.
   ========================================================================== */

const KEY='sebatik_token'
const listeners=new Set()

const read=()=>{try{return localStorage.getItem(KEY)||''}catch{return ''}}

let current=read()

export const getToken=()=>current

export function setToken(next){
  current=next||''
  try{
    if(current)localStorage.setItem(KEY,current)
    else localStorage.removeItem(KEY)
  }catch{}
  listeners.forEach(fn=>fn(current))
}

export const clearToken=()=>setToken('')

/* ----------------------------------------------------------------------------
   Menyegarkan sesi
   ----------------------------------------------------------------------------
   Token akses sengaja berumur pendek (auth-keamanan.md §3). Yang menjaga sesi
   tetap hidup adalah cookie httpOnly yang dipasang saat masuk dan hanya dikirim
   ke /api/v1/auth — JavaScript tidak pernah dapat membacanya.

   Penyegaran dijalankan satu per satu: bila beberapa permintaan sama-sama kena
   401, semuanya menunggu satu penyegaran yang sedang berjalan, bukan memicu
   penyegaran masing-masing dan saling menimpa token hasilnya.
   -------------------------------------------------------------------------- */
let permintaanSegar=null

/* Permintaan penyegaran disimpan terpisah dari penerapan hasilnya. Menerapkan
   token di dalam promise yang sama akan membuat pendengar yang ikut memicu
   penyegaran menunggu promise yang sedang berjalan itu sendiri. */
async function ambilTokenSegar(){
  if(!permintaanSegar){
    permintaanSegar=(async()=>{
      try{
        const response=await fetch('/api/v1/auth/refresh',{method:'POST'})
        if(!response.ok)return ''
        return (await response.json())?.access_token||''
      }catch{
        /* Gangguan jaringan bukan bukti sesi berakhir; token dibiarkan. */
        return null
      }
    })()
  }
  try{return await permintaanSegar}finally{permintaanSegar=null}
}

export async function segarkanToken(){
  const token=await ambilTokenSegar()
  if(token===null)return ''
  setToken(token)
  return token
}

export async function keluarSesi(){
  try{await fetch('/api/v1/auth/logout',{method:'POST',headers:current?{Authorization:`Bearer ${current}`}:{}})}catch{}
  setToken('')
}

export function useToken(){
  const [token,set]=useState(current)
  useEffect(()=>{
    listeners.add(set)
    /* Tab lain bisa masuk atau keluar; ikuti perubahannya supaya bilah atas
       di tab ini tidak menampilkan keadaan yang sudah basi. */
    const sync=event=>{if(event.key===KEY){current=read();listeners.forEach(fn=>fn(current))}}
    addEventListener('storage',sync)
    set(current)
    return()=>{listeners.delete(set);removeEventListener('storage',sync)}
  },[])
  return token
}

/* ----------------------------------------------------------------------------
   Profil pengguna yang sedang masuk
   ----------------------------------------------------------------------------
   Bilah atas dan judul tab perlu tahu peran pengguna, bukan sekadar tahu ada
   token. Peran itu hanya diketahui setelah bertanya ke /auth/saya, jadi
   jawabannya disimpan di sini — satu permintaan untuk satu token, dipakai
   bersama semua yang membutuhkannya.

   Ruang kerja tetap memuat profilnya sendiri karena ia juga butuh wilayah dan
   data lain; yang di sini sengaja dibatasi pada apa yang dipakai kerangka
   halaman, supaya kedua bagian tidak saling menunggu.
   -------------------------------------------------------------------------- */

let profile=null
const profileListeners=new Set()
const emitProfile=()=>profileListeners.forEach(fn=>fn(profile))

async function loadProfile(){
  if(!current){profile=null;emitProfile();return}
  const asked=current
  try{
    const response=await fetch('/api/v1/auth/saya',{headers:{Authorization:`Bearer ${asked}`}})
    /* Sesi yang baru kedaluwarsa masih bisa disambung lewat cookie segar; yang
       benar-benar mati dibersihkan di sini juga. Tanpa itu, seseorang yang
       membuka Beranda dengan sesi mati akan melihat bilah atas menawarkan
       ruang kerja yang tidak lagi bisa ia buka. */
    if(response.status===401){
      const baru=await segarkanToken()
      /* Bila berhasil, setToken sudah memicu pemuatan ulang profil di sini. */
      if(!baru){profile=null;emitProfile()}
      return
    }
    if(asked!==current)return
    profile=response.ok?await response.json():null
  }catch{profile=null}
  emitProfile()
}

listeners.add(loadProfile)
loadProfile()

export function useProfile(){
  const [value,set]=useState(profile)
  useEffect(()=>{
    profileListeners.add(set)
    set(profile)
    return()=>{profileListeners.delete(set)}
  },[])
  return value
}

/* Label peran untuk dibaca manusia. Nama pengguna sengaja tidak dipakai:
   "Operator Kalimantan Utara 1" tidak memberi keterangan lebih daripada
   "Operator", tetapi jauh lebih panjang di bilah atas dan judul tab. */
export const roleLabel=peran=>({
  ADMIN:'Admin',
  VERIFIKATOR:'Verifikator',
  OPERATOR:'Operator'
}[peran]||'Ruang Kerja')
