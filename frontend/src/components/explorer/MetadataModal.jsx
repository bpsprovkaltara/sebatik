import {Info, X} from 'lucide-react'
import {useEffect} from 'react'
import {valueLabel} from '../../lib/format'

export function MetadataModal({item,onClose}){
  useEffect(()=>{
    const close=e=>e.key==='Escape'&&onClose()
    addEventListener('keydown',close)
    return()=>removeEventListener('keydown',close)
  },[onClose])
  if(!item)return null
  const meta=item.metadata||{}
  const years=[...new Set((item.nilai||[]).map(x=>x.tahun))].sort((a,b)=>a-b)
  const value=(year,kind)=>item.nilai.find(x=>x.tahun===year&&x.jenis===kind)
  return <div className="metadata-modal-backdrop" role="presentation" onMouseDown={e=>e.target===e.currentTarget&&onClose()}>
    <section className="metadata-modal" role="dialog" aria-modal="true" aria-labelledby="metadata-title">
      <header>
        <div><span>{item.kategori} · {item.id_indikator}</span><h2 id="metadata-title">{item.nama_indikator}</h2></div>
        <button onClick={onClose} aria-label="Tutup metadata"><X size={20}/></button>
      </header>
      {!item.metadata_tersedia&&<div className="notice warning"><Info size={17}/>Metadata RPJPD belum tersedia untuk indikator ini.</div>}
      <div className="metadata-grid">
        {[
          ['Definisi',meta.definisi],['Interpretasi',meta.interpretasi],
          ['Sumber data',meta.sumber_data],['Frekuensi',meta.frekuensi]
        ].map(([label,text])=><article key={label}><small>{label}</small><p>{text||'Belum tersedia'}</p></article>)}
      </div>
      <article className="formula-card"><small>Rumus perhitungan</small>
        {meta.rumus_latex?<div className="formula-latex">{meta.rumus_latex}</div>:<pre>{meta.rumus_mentah||'Belum tersedia'}</pre>}
        <em>Sumber metadata: {meta.sumber_metadata||'Belum tersedia'}</em>
      </article>
      <div className="table-scroll metadata-values"><table className="value-table"><thead><tr><th>Tahun</th><th>Realisasi</th><th>Target</th><th>Satuan/catatan</th></tr></thead>
        <tbody>{years.map(year=>{const actual=value(year,'realisasi'),target=value(year,'target');return <tr key={year}><td>{year}</td><td>{valueLabel(actual?.nilai,actual?.nilai_teks,item.satuan)}</td><td>{valueLabel(target?.nilai,target?.nilai_teks,item.satuan)}</td><td>{item.satuan||actual?.satuan_catatan||target?.satuan_catatan||'—'}</td></tr>})}</tbody>
      </table>{!years.length&&<p className="empty-inline">Data angka realisasi dan target belum tersedia.</p>}</div>
    </section>
  </div>
}
