import {ChevronLeft, ChevronRight} from 'lucide-react'
import {useEffect, useRef, useState} from 'react'

/* Jeda putaran korsel kartu makro, dalam milidetik. */
const MACRO_INTERVAL=5000


export function CardRail({count,auto=false,className='',children}){
  const railRef=useRef(null)
  /* Nomor halaman disimpan dua kali: sebagai state untuk menggambar titik
     penanda, dan sebagai ref supaya pengatur waktu membaca nilai terkini tanpa
     harus dipasang ulang tiap kali halaman berganti. */
  const pageRef=useRef(0),strideRef=useRef({stride:0,perPage:1})
  const [pages,setPages]=useState(1),[page,setPage]=useState(0),[paused,setPaused]=useState(false)

  const land=index=>{pageRef.current=index;setPage(index)}

  /* Ukuran halaman dihitung dari kartunya, bukan dari `scrollWidth` dibagi
     lebar rel. Sebabnya: satu halaman selebar rel memuat lima kartu dan empat
     sela, sedangkan melompat lima kartu berarti bergerak sejauh lima kartu dan
     lima sela — selisih satu sela tiap halaman. Pada layar lebar selisih itu
     tertelan oleh scroll-snap, tetapi di layar sempit ia menumpuk sampai
     melahirkan satu halaman hantu di deretan titik penanda. */
  const metrics=()=>{
    const rail=railRef.current
    const first=rail?.firstElementChild
    if(!rail||!rail.clientWidth||!first||!count)return null
    const gap=parseFloat(getComputedStyle(rail).columnGap)||0
    const stride=first.getBoundingClientRect().width+gap
    if(!stride)return null
    const perPage=Math.max(1,Math.round((rail.clientWidth+gap)/stride))
    return {rail,stride,perPage,total:Math.max(1,Math.ceil(count/perPage))}
  }

  const measure=()=>{
    const m=metrics()
    if(!m)return
    strideRef.current={stride:m.stride,perPage:m.perPage}
    setPages(m.total)
    /* Halaman penutup selalu mentok di ujung rel, jadi posisinya lebih pendek
       daripada kelipatan lebar halaman. Ia ditandai lewat pemeriksaan ujung,
       bukan pembagian, supaya titiknya tidak tertinggal satu langkah. */
    const atEnd=m.rail.scrollLeft+m.rail.clientWidth>=m.rail.scrollWidth-4
    land(atEnd?m.total-1:Math.min(m.total-1,Math.round(m.rail.scrollLeft/(m.perPage*m.stride))))
  }

  /* Tiap perpindahan menuju posisi mutlak halaman tujuan, bukan "geser sejauh
     satu layar dari tempat sekarang". Bedanya terasa ketika satu penggeseran
     gagal berjalan — dengan posisi mutlak, langkah berikutnya kembali ke jalur
     yang benar; dengan penambahan relatif, selisihnya menumpuk. */
  const scrollToPage=(index,behavior)=>{
    const rail=railRef.current
    const {stride,perPage}=strideRef.current
    if(!rail||!stride)return
    land(index)
    rail.scrollTo({left:index*perPage*stride,behavior})
  }

  /* Lebar rel diamati langsung, bukan lebar jendela — ia juga berubah ketika
     bilah sisi atau papan tik di layar muncul. Peristiwa `resize` tetap
     didengarkan sebagai jaring pengaman bila pengamat ukuran tidak tersedia. */
  useEffect(()=>{
    const rail=railRef.current
    if(!rail)return
    measure()
    const observer=new ResizeObserver(measure)
    observer.observe(rail)
    addEventListener('resize',measure)
    return()=>{observer.disconnect();removeEventListener('resize',measure)}
  },[count])

  useEffect(()=>{
    if(!auto||paused||pages<2)return
    const still=matchMedia('(prefers-reduced-motion: reduce)').matches
    const timer=setInterval(()=>{
      scrollToPage(pageRef.current+1>=pages?0:pageRef.current+1,still?'auto':'smooth')
    },MACRO_INTERVAL)
    return()=>clearInterval(timer)
  },[auto,paused,pages])

  const goto=index=>scrollToPage(index,'smooth')

  /* Tombol panah memutar seperti putaran otomatisnya: dari halaman terakhir
     "berikutnya" kembali ke awal, dan sebaliknya. Tidak ada tombol yang mati
     supaya kendalinya tidak pernah terasa buntu di ujung. */
  const step=arah=>goto((page+arah+pages)%pages)

  return <div
    className={`macro-rail ${className}`.trim()}
    onMouseEnter={()=>setPaused(true)}
    onMouseLeave={()=>setPaused(false)}
    onFocusCapture={()=>setPaused(true)}
    onBlurCapture={()=>setPaused(false)}
  >
    {/* Lapisan ini hanya membungkus rel kartunya, tanpa titik penanda di
        bawahnya, supaya kedua panah bisa duduk tepat di tengah tinggi kartu. */}
    <div className="macro-viewport">
      {pages>1&&<button
        type="button"
        className="macro-nav is-prev"
        onClick={()=>step(-1)}
        aria-label="Indikator sebelumnya"
      ><ChevronLeft size={20}/></button>}

      <div className="macro-track" ref={railRef} onScroll={measure}>{children}</div>

      {pages>1&&<button
        type="button"
        className="macro-nav is-next"
        onClick={()=>step(1)}
        aria-label="Indikator berikutnya"
      ><ChevronRight size={20}/></button>}
    </div>

    {pages>1&&<div className="macro-dots" role="tablist" aria-label="Halaman indikator makro">
      {Array.from({length:pages},(_,i)=>
        <button
          key={i}
          role="tab"
          className={i===page?'is-active':''}
          aria-selected={i===page}
          aria-label={`Halaman ${i+1} dari ${pages}`}
          onClick={()=>goto(i)}
        />
      )}
    </div>}
  </div>
}
