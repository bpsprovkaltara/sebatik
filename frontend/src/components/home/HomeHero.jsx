import {AuroraField, BatikLayer} from '../../Brand'
import {useState} from 'react'

/* Foto latar bersifat opsional. Bila berkasnya belum dipasang, gradasi laut
   dan motif kawung di belakangnya sudah berdiri sendiri, jadi tidak ada
   kotak gambar rusak yang terlihat pengguna. */
const HERO_PHOTO='/hero-beranda.jpg'


export function HomeHero(){
  const [photo,setPhoto]=useState(true)

  return <header className="home-hero">
    <div className="home-hero-media" aria-hidden="true">
      {photo&&<img src={HERO_PHOTO} alt="" onError={()=>setPhoto(false)}/>}
    </div>
    <div className="home-hero-veil" aria-hidden="true"/>
    <AuroraField/>
    <BatikLayer opacity={.08} drift/>

    <div className="home-hero-grid">
      <div className="home-hero-identity">
        <div className="home-hero-branding">
          <h1>SEBATIK</h1>
          <p className="home-hero-expand">Sistem Monitoring Berkelanjutan Capaian Indikator ISV-IUP Kalimantan Utara</p>
        </div>
      </div>

      <div className="home-hero-copy">
        <p>
          SEBATIK memantau ketersediaan dan capaian 86 indikator ISV-IUP Provinsi Kalimantan
          Utara dalam satu dasbor terpadu. Menghubungkan target RPJPD dengan realisasi tahunan
          menuju Indonesia Emas 2045.
        </p>
      </div>
    </div>
  </header>
}


/* Angka ringkasan di kaki kartu dilepas. Kartu ini pintu masuk, bukan papan
   angka — dan angka yang sama sudah muncul utuh di bagian-bagian di bawahnya.
   Panah naik ke baris judul supaya kartunya tinggal dua baris: nama fitur dan
   satu kalimat penjelas. */
