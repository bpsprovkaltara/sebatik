import {DeltaPill, SkeletonCard} from '../../ui'
import {CardRail} from '../../components/home/CardRail'
import {stripUnit, valueLabel, valueParts, valueTone} from '../../lib/format'
import {RUTE,ke} from '../../lib/rute'

export function MacroCards({items,loading}){
  return <CardRail count={items.length} auto>
    {items.map((x,i)=>{
      const up=x.arah_perubahan==='NAIK',down=x.arah_perubahan==='TURUN'
      /* Satuan hanya ditulis sekali, menempel pada angkanya. Judul kartu
         dilepas dari satuannya supaya baris judul tidak memakai dua barisnya
         hanya untuk mengulang "(Rp Juta)" yang sudah terbaca di bawah. */
      const nilai=valueParts(x.nilai,x.nilai_teks,x.satuan)
      return <a className="macro-card" href={ke(`${RUTE.indikator}?indikator=${encodeURIComponent(x.id_indikator)}`)} aria-label={`Buka indikator ${x.nama_indikator}`} key={x.id_indikator} style={{'--tone':`var(--series-${(i%6)+1})`,'--i':i}}>
        <div className="macro-head"><span>{stripUnit(x.nama_indikator)}</span><i>{x.kode_indikator}</i></div>
        <small className="macro-target">Target {x.tahun}: <b>{valueLabel(x.target,x.target_teks,x.satuan)}</b></small>
        {x.label_periode&&<small className="macro-period">Realisasi {x.label_periode}</small>}
        <div className={`macro-value${valueTone(x.nilai)}`}>
          {nilai.number}
          {nilai.unit&&<span className={`macro-unit${nilai.unit==='%'?' is-symbol':''}`}>{nilai.unit==='%'?nilai.unit:` ${nilai.unit}`}</span>}
        </div>
        <div className="macro-change">
          <DeltaPill direction={up?'up':down?'down':'flat'}>
            {x.perubahan!==null
              ?`${valueLabel(Math.abs(x.perubahan),null,x.satuan)} dibanding tahun sebelumnya`
              :x.keterangan||'Perbandingan belum tersedia'}
          </DeltaPill>
        </div>
      </a>
    })}
    {loading&&[0,1,2,3,4].map(i=><SkeletonCard key={i}/>)}
  </CardRail>
}
