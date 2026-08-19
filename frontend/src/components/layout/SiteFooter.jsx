import {ArrowUpRight, Mail, MapPin, Phone} from 'lucide-react'

/* Peta kantor. Sengaja memakai sematan Google tanpa kunci API supaya tidak
   ada rahasia yang perlu disimpan di frontend. Alamat dan tautan di bawahnya
   berdiri sendiri, jadi ketika jaringan kantor memblokir domain Google
   informasinya tetap lengkap — bingkai kosong, isi tidak hilang. */
const OFFICE_QUERY='Badan Pusat Statistik Provinsi Kalimantan Utara, Jl. Jelarai Raya, Tanjung Selor Hilir'

const OFFICE_EMBED=`https://maps.google.com/maps?q=${encodeURIComponent(OFFICE_QUERY)}&z=16&output=embed`

const OFFICE_LINK=`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(OFFICE_QUERY)}`

const FOOTER_CONTACT=[
  [MapPin,'Alamat','Jl. Jelarai Raya RT 75 RW 28, Tanjung Selor Hilir, Bulungan 77212'],
  [Phone,'Telepon','(0552) 2033254 · WhatsApp 0822-5442-6005']
]


export function SiteFooter({office=false}){
  return <footer className={`site-footer${office?'':' is-slim'}`}>
    {office&&<div className="footer-panel">
      <div className="footer-info">
        <h2>Badan Pusat Statistik<em>Provinsi Kalimantan Utara</em></h2>

        <dl className="footer-contact">
          {FOOTER_CONTACT.map(([Icon,label,value])=>
            <div key={label}>
              <dt><Icon size={17}/><span>{label}</span></dt>
              <dd>{value}</dd>
            </div>
          )}
          <div>
            <dt><Mail size={17}/><span>Surel</span></dt>
            <dd><a href="mailto:bps6500@bps.go.id">bps6500@bps.go.id</a></dd>
          </div>
        </dl>
      </div>

      <div className="footer-map">
        <iframe
          src={OFFICE_EMBED}
          title="Peta lokasi kantor BPS Provinsi Kalimantan Utara"
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          allowFullScreen
        />
        <a className="footer-map-link" href={OFFICE_LINK} target="_blank" rel="noreferrer">
          <span><b>Kantor BPS Kalimantan Utara</b><small>Tanjung Selor, Bulungan</small></span>
          <ArrowUpRight size={17}/>
        </a>
      </div>
    </div>}

    <div className="footer-base">
      <small>© {new Date().getFullYear()} Tim Kerja ISV-IUP BPS Provinsi Kalimantan Utara · Hak Cipta Dilindungi.</small>
    </div>
  </footer>
}

/* Kepala halaman sengaja hanya memuat satu kalimat. Nama fiturnya sudah
   terbaca di navigasi dan di judul tab, jadi mengulangnya sebagai judul besar
   cuma menambah tinggi tanpa menambah keterangan. Yang tersisa adalah kalimat
   yang benar-benar menjelaskan isi halaman, diberi ruang untuk bernapas.
   Properti `title` tetap diterima karena dipakai untuk judul dokumen. */
