import {DeltaPill, SkeletonCard} from '../../ui'
import {CardRail} from '../../components/home/CardRail'
import {valueLabel, valueTone} from '../../lib/format'

export function MacroCards({items,loading}){
  return <CardRail count={items.length} auto>
    {items.map((x,i)=>{
      const up=x.arah_perubahan==='NAIK',down=x.arah_perubahan==='TURUN'
      return <article className="macro-card" key={x.id_indikator} style={{'--tone':`var(--series-${(i%6)+1})`,'--i':i}}>
        <div className="macro-head"><span>{x.nama_indikator}</span><i>{x.kode_indikator}</i></div>
        <small className="macro-target">Target {x.tahun}: <b>{valueLabel(x.target,x.target_teks,x.satuan)}</b></small>
        <div className={`macro-value${valueTone(x.nilai)}`}>{valueLabel(x.nilai,x.nilai_teks,x.satuan)}</div>
        <div className="macro-change">
          <DeltaPill direction={up?'up':down?'down':'flat'}>
            {x.perubahan!==null
              ?`${valueLabel(Math.abs(x.perubahan),null,x.satuan)} dibanding tahun sebelumnya`
              :x.keterangan||'Perbandingan belum tersedia'}
          </DeltaPill>
        </div>
      </article>
    })}
    {loading&&[0,1,2,3,4].map(i=><SkeletonCard key={i}/>)}
  </CardRail>
}
