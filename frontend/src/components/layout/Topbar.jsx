import {useAuth} from '../../context/AuthContext'
import {RUTE, ke} from '../../lib/rute'
import {useTheme} from '../../theme'
import {ScrollProgress, useScrolled} from '../../ui'
import {ChevronRight, Menu, Moon, Sun, X} from 'lucide-react'
import {useEffect, useState} from 'react'
import {NAV_LINKS, authNavItems} from '../../components/layout/navigasi'

export function Topbar({active}){
  const [theme,toggle]=useTheme()
  const [open,setOpen]=useState(false)
  const scrolled=useScrolled()
  const {token,profil,keluar}=useAuth()
  const authItems=authNavItems(token,profil)
  const onAuth=item=>{if(item.logout)keluar();setOpen(false)}
  /* Hanya tautan yang benar-benar menuju sebuah halaman yang boleh ditandai
     aktif. "Keluar" adalah tindakan, bukan tujuan — ia tidak pernah aktif. */
  const isAuthActive=item=>!item.logout&&active===item.jalur

  useEffect(()=>{
    /* Menu seluler menutup sendiri saat pindah halaman; HashRouter tetap
       memancarkan hashchange, jadi satu pendengar ini cukup. */
    const close=()=>setOpen(false)
    addEventListener('hashchange',close)
    return()=>removeEventListener('hashchange',close)
  },[])

  useEffect(()=>{
    if(!open)return
    const onKey=event=>{if(event.key==='Escape')setOpen(false)}
    addEventListener('keydown',onKey)
    document.body.style.overflow='hidden'
    return()=>{removeEventListener('keydown',onKey);document.body.style.overflow=''}
  },[open])

  return <>
    <header className="topbar" data-scrolled={String(scrolled)}>
      <a className="brand" href={ke(RUTE.beranda)} aria-label="SEBATIK — kembali ke beranda">
        <span className="brand-mark"><img src="/logo-sebatik-monitoring.png" alt=""/></span>
        <span className="brand-name"><b>SEBATIK</b><small>BPS Provinsi Kalimantan Utara</small></span>
      </a>

      <nav className="nav-desktop" aria-label="Navigasi utama">
        {NAV_LINKS.map(([jalur,label])=>
          <a key={jalur} href={ke(jalur)} className={active===jalur?'active':''} aria-current={active===jalur?'page':undefined}>
            {label}
          </a>
        )}
        {authItems.map(item=>
          <a
            key={item.label}
            href={ke(item.jalur)}
            onClick={()=>onAuth(item)}
            className={`nav-auth${item.logout?' is-out':''}${isAuthActive(item)?' active':''}`}
            aria-current={isAuthActive(item)?'page':undefined}
          >
            <item.icon size={16} aria-hidden="true"/>{item.label}
          </a>
        )}
      </nav>

      <div className="topbar-tools">
        <button
          className="icon-btn"
          onClick={toggle}
          title={theme==='dark'?'Beralih ke mode terang':'Beralih ke mode gelap'}
          aria-label={theme==='dark'?'Beralih ke mode terang':'Beralih ke mode gelap'}
        >
          {theme==='dark'?<Sun size={18}/>:<Moon size={18}/>}
        </button>
        <button
          className="icon-btn nav-toggle"
          onClick={()=>setOpen(v=>!v)}
          aria-label={open?'Tutup menu':'Buka menu'}
          aria-expanded={open}
        >
          {open?<X size={19}/>:<Menu size={19}/>}
        </button>
      </div>

      <ScrollProgress/>
    </header>

    <div className="nav-drawer" data-open={String(open)} aria-hidden={!open}>
      <div className="nav-drawer-scrim" onClick={()=>setOpen(false)}/>
      <nav className="nav-drawer-panel" aria-label="Navigasi seluler">
        {NAV_LINKS.map(([jalur,label,Icon],index)=>
          <a
            key={jalur}
            href={ke(jalur)}
            style={{'--i':index}}
            className={active===jalur?'active':''}
            aria-current={active===jalur?'page':undefined}
            onClick={()=>setOpen(false)}
          >
            <span><Icon size={18}/>{label}</span>
            <ChevronRight size={16}/>
          </a>
        )}
        {authItems.map((item,i)=>
          <a
            key={item.label}
            href={ke(item.jalur)}
            style={{'--i':NAV_LINKS.length+i}}
            className={`nav-auth${item.logout?' is-out':''}${isAuthActive(item)?' active':''}`}
            aria-current={isAuthActive(item)?'page':undefined}
            onClick={()=>onAuth(item)}
          >
            <span><item.icon size={18}/>{item.label}</span>
            <ChevronRight size={16}/>
          </a>
        )}
        <p className="nav-drawer-note">
          Dasbor pemantauan capaian indikator ISV–IUP, RPJPN 2025–2045.
        </p>
      </nav>
    </div>
  </>
}



/* Panel alamat dan peta hanya dipasang di beranda — di sana ia berperan sebagai
   penutup identitas. Halaman lain cukup memakai satu baris hak cipta supaya
   kaki halaman tidak mengulang informasi yang sama di setiap layar. */
