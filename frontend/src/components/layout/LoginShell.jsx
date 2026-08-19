import {AuroraField, BatikLayer} from '../../Brand'
import {SiteFooter} from '../../components/layout/SiteFooter'
import {Topbar} from '../../components/layout/Topbar'

export function LoginShell({children}){
  return <div className="app login-app">
    <div className="shell">
      <Topbar active="#login"/>
      <main className="login-stage">
        <AuroraField/>
        <BatikLayer opacity={.05}/>
        {children}
      </main>
    </div>
    <SiteFooter/>
  </div>
}

/* ==========================================================================
   Beranda
   --------------------------------------------------------------------------
   Halaman ini memakai kepala halaman sendiri (bukan <Shell>) karena perannya
   berbeda: bukan judul bagian, melainkan panggung identitas — logo besar,
   nama panjang, dan kalimat pendamping — dengan foto perbatasan sebagai latar.
   ========================================================================== */


/* Pemilih tahun tinggal di kepala bagian "Indikator makro", bukan di hero.
   Ia mengendalikan angka, jadi tempatnya berdampingan dengan angka pertama
   yang dipengaruhinya — bukan di panggung identitas yang tidak memuat angka
   apa pun. Bentuknya kotak bersudut lengkung, sama seperti isian lain di
   halaman ini, supaya terbaca sebagai kendali dan bukan lencana. */
