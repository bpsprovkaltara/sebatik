import {RUTE} from '../lib/rute'
import * as endpoints from '../api/endpoints'
import {chartTheme, useTheme} from '../theme'
import {capaianColor, seriesColor} from '../tokens'
import {TooltipCard} from '../components/charts/TooltipCard'
import {Panel, VizLegend} from '../ui'
import {SmartSelect} from '../components/ui/SmartSelect'
import {AlertTriangle} from 'lucide-react'
import {useEffect, useState} from 'react'
import {Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis} from 'recharts'
import {Shell} from '../components/layout/Shell'

export default function AnalyticsPage(){
  /* Indikator terpilih sengaja tidak punya nilai bawaan berupa ID tertulis:
     ID seperti itu ikut basi setiap kali daftar indikator berganti versi, dan
     halaman akan meminta indikator yang sudah tidak ada. Pilihan awal diambil
     dari daftar yang benar-benar dimuat. */
  const [cards,setCards]=useState([]),[id,setId]=useState(''),[gap,setGap]=useState(null),
    [change,setChange]=useState(null),[rank,setRank]=useState(null),[x,setX]=useState(''),
    [y,setY]=useState(''),[corr,setCorr]=useState(null)
  const [theme]=useTheme()
  const ct=chartTheme(theme)

  useEffect(()=>{
    endpoints.capaian().then(r=>{
      const daftar=r.data||[]
      setCards(daftar)
      if(daftar.length){
        setId(sebelum=>sebelum||daftar[0].id_indikator)
        setX(sebelum=>sebelum||daftar[0].id_indikator)
        setY(sebelum=>sebelum||(daftar[1]||daftar[0]).id_indikator)
      }
    })
    endpoints.peringkat().then(setRank)
  },[])
  useEffect(()=>{
    if(!id)return
    endpoints.gap(id).then(setGap)
    endpoints.selisihTahunan(id).then(setChange)
  },[id])
  useEffect(()=>{
    if(!x||!y)return
    endpoints.korelasi(x,y).then(setCorr)
  },[x,y])

  const opts=cards.map(i=>({value:i.id_indikator,label:i.nama_indikator,code:i.id_indikator}))
  const upColor=capaianColor('TERCAPAI',theme),downColor=capaianColor('PERLU_PERHATIAN',theme)

  return <Shell
    active={RUTE.analitik}
    title="Dasbor Analitik"
    subtitle="Tren, gap target, perbandingan antar-indikator, dan korelasi"
  >
    <div className="notice warning">
      <AlertTriangle size={17}/> Required run-rate adalah ekstrapolasi linear sederhana, bukan proyeksi resmi.
    </div>

    <Panel
      kicker="Tren tahunan"
      title="Tren dan selisih tahunan"
      desc="Warna menunjukkan perbaikan sesuai arah indikator."
      actions={<SmartSelect value={id} onChange={setId} options={opts} ariaLabel="Pilih indikator" placeholder="Pilih indikator"/>}
    >
      <ResponsiveContainer width="100%" height={270}>
        <BarChart data={change?.data||[]} margin={{top:10,right:16,left:0,bottom:0}}>
          <CartesianGrid stroke={ct.grid} vertical={false}/>
          <XAxis dataKey="tahun" tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
          <YAxis tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
          <ReferenceLine y={0} stroke={ct.baseline} strokeWidth={1.5}/>
          <Tooltip cursor={{fill:ct.cursor}} content={<TooltipCard/>}/>
          <Bar dataKey="selisih" name="Selisih" radius={[6,6,0,0]} animationDuration={ct.motion}>
            {(change?.data||[]).map((v,i)=><Cell key={i} fill={v.membaik?upColor:downColor}/>)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <VizLegend items={[{label:'Membaik',color:upColor},{label:'Memburuk',color:downColor}]}/>
    </Panel>

    <div className="two-col">
      <Panel delay={40} kicker="Jarak ke target" title="Gap terhadap target">
        <div className="gap-cards">
          <div><span>Target 2029</span><b>{gap?.target_2029??'-'}</b><small>Gap {gap?.gap_2029??'-'}</small></div>
          <div><span>Target 2045</span><b>{gap?.target_2045??'-'}</b><small>Gap {gap?.gap_2045??'-'}</small></div>
          <div>
            <span>Status jalur</span>
            <b>{gap?.status_jalur?.replaceAll('_',' ')||'-'}</b>
            <small>Historis {gap?.laju_historis?.toFixed?.(3)??'-'} / tahun</small>
          </div>
        </div>
      </Panel>
      <Panel delay={80} kicker="Peringkat" title="Perbaikan terbesar">
        <ol className="ranking">
          {rank?.perbaikan_terbesar?.slice(0,5).map(item=>
            <li key={item.id_indikator}><span>{item.nama_indikator}</span><b>{item.skor_perbaikan.toFixed(2)}</b></li>
          )}
        </ol>
      </Panel>
    </div>

    <Panel
      delay={40}
      kicker="Hubungan"
      title="Korelasi antar-indikator"
      desc="Korelasi bukan sebab-akibat; seri pendek tidak layak ditafsirkan."
      actions={
        <div className="select-pair">
          <SmartSelect value={x} onChange={setX} options={opts} ariaLabel="Indikator sumbu X" placeholder="Sumbu X"/>
          <SmartSelect value={y} onChange={setY} options={opts} ariaLabel="Indikator sumbu Y" placeholder="Sumbu Y"/>
        </div>
      }
    >
      {corr?.n<4
        ?<div className="empty-state">Hasil disembunyikan: hanya {corr?.n||0} tahun berimpitan (minimal 4).</div>
        :<>
          <div className="stat-line">Pearson r = {corr?.pearson} · n = {corr?.n}</div>
          <ResponsiveContainer width="100%" height={290}>
            <ScatterChart margin={{top:10,right:16,left:0,bottom:0}}>
              <CartesianGrid stroke={ct.grid}/>
              <XAxis dataKey="x" name="X" tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
              <YAxis dataKey="y" name="Y" tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
              <Tooltip cursor={{strokeDasharray:'4 4',stroke:ct.baseline}} content={<TooltipCard/>}/>
              <Scatter data={corr?.data||[]} fill={seriesColor(0,theme)} animationDuration={ct.motion}/>
            </ScatterChart>
          </ResponsiveContainer>
        </>}
    </Panel>

  </Shell>
}

/* ==========================================================================
   Ruang kerja berbasis peran
   ========================================================================== */
