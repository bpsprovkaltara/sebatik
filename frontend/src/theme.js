import {useEffect,useState} from 'react'

const KEY='sebatik_theme'
const listeners=new Set()
let current=document.documentElement.dataset.theme==='dark'?'dark':'light'

export function setTheme(next){
  current=next
  const root=document.documentElement
  /* Matikan transisi warna sesaat supaya pergantian tema tidak menimbulkan
     kilatan gradasi pada ratusan elemen sekaligus. */
  root.dataset.themeSwitching='1'
  root.dataset.theme=next
  try{localStorage.setItem(KEY,next)}catch{}
  listeners.forEach(fn=>fn(next))
  setTimeout(()=>{delete root.dataset.themeSwitching},240)
}

export function useTheme(){
  const [theme,set]=useState(current)
  useEffect(()=>{listeners.add(set);set(current);return()=>listeners.delete(set)},[])
  return [theme,()=>setTheme(theme==='dark'?'light':'dark')]
}

/* Kanvas grafik: warna sumbu, kisi, dan kartu tooltip mengikuti tema.
   Kisi dibuat sangat resesif agar mark data yang berbicara, bukan chrome-nya. */
export function chartTheme(theme){
  const dark=theme==='dark'
  return {
    dark,
    surface:dark?'#152835':'#FFFFFF',
    grid:dark?'#294658':'#D9E7F0',
    axis:dark?'#94ACBA':'#71818D',
    baseline:dark?'#3B6075':'#B8D4E5',
    cursor:dark?'rgba(66,184,240,.14)':'rgba(20,148,211,.10)',
    tooltip:{
      background:dark?'#1B3241':'#FFFFFF',
      border:`1px solid ${dark?'#3B6075':'#D9E7F0'}`,
      borderRadius:14,
      boxShadow:dark?'0 20px 48px rgba(0,0,0,.55)':'0 20px 48px rgba(94,60,54,.18)',
      color:dark?'#F2F8FC':'#263746',
      fontSize:12.5,
      fontFamily:'"Helvetica Neue",Helvetica,Arial,sans-serif',
      fontWeight:500,
      padding:'11px 13px',
      outline:'none'
    },
    /* Durasi animasi mark Recharts — cukup untuk terbaca sebagai gerakan,
       cukup singkat untuk tidak menghambat pembacaan angka. */
    motion:matchMedia('(prefers-reduced-motion: reduce)').matches?0:750
  }
}
