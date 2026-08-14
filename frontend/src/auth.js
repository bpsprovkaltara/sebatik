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
    /* Token kedaluwarsa dibersihkan di sini juga. Tanpa ini, seseorang yang
       membuka Beranda dengan sesi yang sudah mati akan melihat bilah atas
       menawarkan ruang kerja yang tidak lagi bisa ia buka. */
    if(response.status===401){setToken('');return}
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
