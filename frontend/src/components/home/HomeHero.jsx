import {AuroraField, BatikLayer, WaveEdge} from '../../Brand'
import {useState} from 'react'

const HERO_PHOTO='/hero-beranda.jpg'

/* Logotipe dipecah per huruf supaya tiap huruf bisa datang menyusul, bukan
   seluruh kata muncul sekaligus. `aria-label` pada judulnya menjaga pembaca
   layar tetap mendengar satu kata utuh, bukan tujuh huruf terpisah. */
const WORDMARK=[...'SEBATIK']


export function HomeHero(){
  const [photo,setPhoto]=useState(true)

  return <header className="home-hero">
    <div className="home-hero-media" aria-hidden="true">
      {photo&&<img src={HERO_PHOTO} alt="" onError={()=>setPhoto(false)}/>}
    </div>
    <div className="home-hero-veil" aria-hidden="true"/>
    <AuroraField/>
    <BatikLayer opacity={.08} drift/>

    {/* Dua kolom, rata kiri. Sebelumnya nama, tagline, dan paragraf bertumpuk
        di satu lajur tengah: pita selebar layar hanya terpakai sepertiga
        tengahnya, dan ketiganya berebut satu sumbu baca yang sama. Dipisah
        begini, sisi kiri memegang identitas dan sisi kanan memegang penjelasan
        — pitanya terpakai penuh dan mata punya dua tempat berhenti. */}
    <div className="home-hero-grid">
      <div className="home-hero-identity">
        <h1 aria-label="SEBATIK">
          {WORDMARK.map((huruf,i)=>
            <span key={i} style={{'--i':i}} aria-hidden="true">{huruf}</span>
          )}
        </h1>
        <p className="home-hero-expand">
          Sistem Monitoring Berkelanjutan Capaian Indikator ISV–IUP Kalimantan Utara
        </p>
      </div>

      <div className="home-hero-copy">
        <p>
          SEBATIK memantau ketersediaan dan capaian indikator ISV-IUP Provinsi Kalimantan
          Utara dalam satu dasbor terpadu, menghubungkan target RPJPD dengan realisasi tahunan
          menuju Indonesia Emas 2045.
        </p>
      </div>
    </div>
    <WaveEdge />
  </header>
}
