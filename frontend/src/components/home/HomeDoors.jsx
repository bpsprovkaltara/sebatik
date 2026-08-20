import {RUTE, ke} from '../../lib/rute'
import {Compass, ShieldCheck, Sparkles, Target} from 'lucide-react'
import {Reveal} from '../../ui'
import {ArrowUpRight} from 'lucide-react'

/* Empat pintu masuk utama. Angka pada kartu diambil dari muatan beranda yang
   sama, jadi tidak ada permintaan tambahan ke backend. */
const HOME_DOORS=[
  [RUTE.indikator,'Indikator',Compass,'Telusuri seri realisasi, target, dan pertumbuhan tiap indikator'],
  [RUTE.capaian,'Capaian',Target,'Ukur jarak setiap indikator menuju target Kalimantan Utara 2045'],
  [RUTE.insight,'Insight',Sparkles,'Baca situasi indikator makro dan perbandingan antarwilayah'],
  [RUTE.validitas,'Validitas',ShieldCheck,'Periksa status verifikasi, pembaruan, dan metadata indikator']
]


export function HomeDoors(){
  return <Reveal as="nav" className="home-doors" aria-label="Pintu masuk utama">
    {HOME_DOORS.map(([jalur,label,Icon,desc],i)=>
      <a key={jalur} href={ke(jalur)} className="home-door" style={{'--tone':`var(--series-${(i%6)+1})`,'--i':i}}>
        <span className="home-door-band" aria-hidden="true"/>
        <span className="home-door-icon"><Icon size={20}/></span>
        <b>{label}</b>
        <ArrowUpRight className="home-door-go" size={16} aria-hidden="true"/>
        <small>{desc}</small>
      </a>
    )}
  </Reveal>
}
