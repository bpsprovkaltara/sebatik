import {AlertTriangle, Info, X} from 'lucide-react'
import {useEffect} from 'react'
import {valueLabel} from '../../lib/format'
import {ProseText} from '../../ui'
import {BlockMath} from 'react-katex'
import 'katex/dist/katex.min.css'

/* Definisi dan interpretasi ditulis panjang di basis data dan kerap memuat
   daftar bernomor di tengah paragraf — "a. Sangat pendek ... b. Pendek ...",
   "1. Kekurangan Gizi: ... 2. Akses Pelayanan Kesehatan: ...". Sebagai satu
   blok rata kiri selebar setengah layar, daftar itu tidak kelihatan sebagai
   daftar dan paragrafnya jadi dinding teks. `ProseText` memulihkannya jadi
   baris menurun; yang memang kalimat biasa tetap tampil apa adanya. */
const FIELDS=[
  ['Definisi','definisi'],
  ['Interpretasi','interpretasi'],
  ['Sumber data','sumber_data'],
  ['Frekuensi','frekuensi']
]

/* Sebagian pemasangan lama menyimpan rumus PDRB per kapita dari ekstraksi PDF
   tanpa kurung kurawal LaTeX. Bentuknya dikenali dari isi, lalu dipulihkan
   sebelum diberikan ke KaTeX; basis data baru sudah mengirim bentuk benar. */
const readableLatex=value=>{
  if(!value)return value
  if(value.includes('PDRBperkapita')||value.includes('PDRB per kapita')){
    return String.raw`\text{PDRB per kapita}_t = \dfrac{\text{PDRB}_{\text{ADHB},\,t}}{\text{populasi}_t}`
  }
  return value
}

/* Kartu rumus punya dua wujud, dan bedanya bukan sekadar tampilan.

   Bila indikatornya punya rumus, yang tampil adalah rumus itu sendiri dalam
   bentuk matematis lewat KaTeX, disusul keterangan notasinya — persis susunan
   yang dipakai Buku 1. Sebelumnya yang tampil adalah kolom `rumus_mentah`:
   hasil ekstraksi teks PDF yang pecahannya terurai jadi baris terpisah dan
   sebagian hurufnya tertukar, sehingga pembaca melihat "𝑃𝐷𝑅𝐵!"#$ 𝑃𝐷𝑅𝐵 𝑝𝑒𝑟
   𝑘𝑎𝑝𝑖𝑡𝑎 = 𝑝𝑜𝑝𝑢𝑙𝑎𝑠𝑖" alih-alih sebuah pecahan.

   Bila Buku 1 memang tidak memuat rumus tertutup — indeks komposit yang
   dihitung lewat survei, PCA, atau penilaian ahli — yang tampil adalah uraian
   metodenya, bukan kotak rumus kosong. */
function FormulaCard({meta}){
  const keterangan=meta.keterangan_rumus||[]
  const uraian=meta.rumus_mentah&&!meta.rumus_latex?meta.rumus_mentah:null
  const latex=readableLatex(meta.rumus_latex)

  return <article className="formula-card">
    <div className="formula-head">
      <small>Rumus perhitungan</small>
    </div>

    {latex
      ?<div className="formula-latex"><BlockMath math={latex} errorColor="var(--danger)"/></div>
      :uraian
        ?<ProseText text={uraian} className="formula-prose"/>
        :<p className="formula-empty">Buku 1 tidak memuat rumus tertutup untuk indikator ini.</p>}

    {!!keterangan.length&&<div className="formula-notes">
      <small>Keterangan</small>
      <ul>{keterangan.map((baris,i)=><li key={i}>{baris}</li>)}</ul>
    </div>}

    {meta.perlu_verifikasi_rumus&&<p className="formula-flag">
      <AlertTriangle size={15} aria-hidden="true"/>
      Rumus ini disusun dari kalimat definisi Buku 1 karena formula aslinya tercetak sebagai gambar. Perlu diverifikasi terhadap dokumen sumber.
    </p>}

    <em>Sumber metadata: {meta.sumber_metadata||'Belum tersedia'}</em>
  </article>
}

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
        {FIELDS.map(([label,key])=>
          <article key={label}>
            <small>{label}</small>
            <ProseText text={meta[key]}/>
          </article>
        )}
      </div>
      <FormulaCard meta={meta}/>
      <div className="table-scroll metadata-values"><table className="value-table"><thead><tr><th>Tahun</th><th>Realisasi</th><th>Target</th><th>Satuan/catatan</th></tr></thead>
        <tbody>{years.map(year=>{const actual=value(year,'realisasi'),target=value(year,'target');return <tr key={year}><td>{year}</td><td>{valueLabel(actual?.nilai,actual?.nilai_teks,item.satuan)}</td><td>{valueLabel(target?.nilai,target?.nilai_teks,item.satuan)}</td><td>{item.satuan||actual?.satuan_catatan||target?.satuan_catatan||'—'}</td></tr>})}</tbody>
      </table>{!years.length&&<p className="empty-inline">Data angka realisasi dan target belum tersedia.</p>}</div>
    </section>
  </div>
}
