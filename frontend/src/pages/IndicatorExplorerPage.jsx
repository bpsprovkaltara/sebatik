import {RUTE} from '../lib/rute'
import * as endpoints from '../api/endpoints'
import {chartTheme, useTheme} from '../theme'
import {seriesColor} from '../tokens'
import {TooltipCard} from '../components/charts/TooltipCard'
import {ChartSkeleton, EmptyState, Panel, Reveal, VizLegend} from '../ui'
import {AlertTriangle, Building2, Database} from 'lucide-react'
import {useEffect, useState} from 'react'
import {Area, Bar, BarChart, CartesianGrid, ComposedChart, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts'
import {Shell} from '../components/layout/Shell'
import {KaltaraMap} from '../components/maps/KaltaraMap'
import {growthTone, valueLabel} from '../lib/format'

export default function IndicatorExplorerPage(){
  const [groups,setGroups]=useState([]),[group,setGroup]=useState(''),[indicator,setIndicator]=useState(''),
    [detail,setDetail]=useState(null),[year,setYear]=useState(''),[region,setRegion]=useState(''),[error,setError]=useState('')
  const [theme]=useTheme()
  const ct=chartTheme(theme)

  useEffect(()=>{
    endpoints.indikatorExplorer().then(x=>{
      setGroups(x.data)
      /* Kelompok pembuka adalah Sasaran Visi, bukan kelompok pertama menurut
         abjad. Ia yang jadi rujukan utama dasbor ini; kelompok IUP lainnya
         adalah penjabaran di bawahnya. Dicari lewat kategori ISV, bukan lewat
         nama kelompok, supaya tidak putus kalau namanya diubah di basis data. */
      const opening=x.data.find(g=>g.indikator.some(i=>i.kategori==='ISV'))||x.data[0]
      if(opening){setGroup(opening.kelompok);setIndicator(opening.indikator[0]?.id_indikator||'')}
    }).catch(e=>setError(e.message))
  },[])

  useEffect(()=>{
    if(indicator)endpoints.indikatorExplorerDetail(indicator,{tahun:year}).then(x=>{
      setDetail(x)
      if(!year&&x.tahun)setYear(String(x.tahun))
      if(!region&&x.wilayah?.length)setRegion(x.wilayah[0].kode)
    }).catch(e=>setError(e.message))
  },[indicator,year])

  const currentGroup=groups.find(x=>x.kelompok===group)
  const selectedRegion=detail?.wilayah?.find(x=>x.kode===region)
  const chooseGroup=value=>{
    setGroup(value)
    const g=groups.find(x=>x.kelompok===value)
    setIndicator(g?.indikator[0]?.id_indikator||'')
    setYear('')
  }
  const hasRegional=detail?.wilayah?.some(x=>x.nilai!==null||x.nilai_teks)

  return <Shell
    active={RUTE.indikator}
    title="Indikator"
    subtitle="Telusuri indikator berdasarkan kelompok, seri realisasi terverifikasi, target, dan pertumbuhan."
  >
    {error&&<div className="error"><AlertTriangle size={18}/>{error}</div>}

    <Reveal as="section" className="panel indicator-browser">
      <div className="browser-toolbar">
        <label className="field">
          <span>Kelompok indikator</span>
          <select value={group} onChange={e=>chooseGroup(e.target.value)}>
            {groups.map(x=><option key={x.kelompok}>{x.kelompok}</option>)}
          </select>
        </label>
        <label className="field">
          <span>Tahun wilayah</span>
          <select value={year} onChange={e=>setYear(e.target.value)}>
            {(detail?.tahun_tersedia||[]).map(x=><option key={x}>{x}</option>)}
          </select>
        </label>
      </div>

      <div className="browser-layout">
        <aside className="indicator-picker">
          <header>
            <b>{group||'Memuat kelompok...'}</b>
            <span>{currentGroup?.jumlah||0} indikator</span>
          </header>
          <div>
            {currentGroup?.indikator.map(x=>
              <button
                key={x.id_indikator}
                className={indicator===x.id_indikator?'active':''}
                onClick={()=>{setIndicator(x.id_indikator);setYear('')}}
                aria-pressed={indicator===x.id_indikator}
              >
                <i>{x.kode_indikator}</i>
                <span>{x.nama_indikator}<small>{x.kategori}</small></span>
              </button>
            )}
          </div>
        </aside>

        <div className="indicator-content">
          {detail?<>
            <header className="indicator-hero">
              <div>
                <span>{detail.kategori} · {detail.kode_indikator}</span>
                <h2>{detail.nama_indikator}</h2>
                <p>{detail.arah_pembangunan}</p>
              </div>
              <div className="source-chip">
                <Database size={17}/>
                <span><small>Sumber data</small>{detail.sumber_data||'Belum dicatat'}</span>
              </div>
            </header>

            <div className="series-cards">
              {detail.series.filter(x=>x.realisasi!==null||x.realisasi_teks).map(x=>
                <div className={x.tahun===detail.tahun?'selected':''} key={x.tahun}>
                  <span>{x.tahun}</span>
                  <b>{valueLabel(x.realisasi,x.realisasi_teks,detail.satuan)}</b>
                  <small className={growthTone(x.growth)}>
                    {x.growth===null?'Growth —':`${x.growth>0?'↑':x.growth<0?'↓':'—'} ${Math.abs(x.growth)}%`}
                  </small>
                </div>
              )}
            </div>

            {/* Realisasi memakai bidang bergradasi, target memakai garis utuh
                yang lebih tipis. Sebelumnya keduanya garis dan target dibedakan
                dengan putus-putus — padahal target adalah angka tercatat, sama
                nyatanya dengan realisasi; putus-putus lazimnya berarti "belum
                terjadi" dan itu menyesatkan di sini. Yang membedakan sekarang
                bobot dan isian: yang berisi adalah capaian, yang tipis adalah
                acuan. */}
            <div className="main-series">
              <ResponsiveContainer width="100%" height={340}>
                <ComposedChart data={detail.series} margin={{top:18,right:22,left:0,bottom:5}}>
                  <defs>
                    <linearGradient id="grad-realisasi" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={seriesColor(1,theme)} stopOpacity={.26}/>
                      <stop offset="100%" stopColor={seriesColor(1,theme)} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={ct.grid} vertical={false}/>
                  <XAxis dataKey="tahun" tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
                  <YAxis tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
                  <Tooltip cursor={{stroke:ct.baseline,strokeWidth:1}} content={<TooltipCard formatter={v=>valueLabel(v,null,detail.satuan)}/>}/>
                  <Line type="monotone" dataKey="target" name="Target"
                    stroke={seriesColor(2,theme)} strokeWidth={1.75} connectNulls
                    dot={{r:2.5,fill:ct.surface,stroke:seriesColor(2,theme),strokeWidth:1.75}}
                    activeDot={{r:5,strokeWidth:2,stroke:ct.surface}} animationDuration={ct.motion}/>
                  <Area type="monotone" dataKey="realisasi" name="Realisasi Kaltara"
                    stroke={seriesColor(1,theme)} strokeWidth={2.75} fill="url(#grad-realisasi)" connectNulls
                    dot={{r:4,fill:ct.surface,stroke:seriesColor(1,theme),strokeWidth:2.5}}
                    activeDot={{r:6,strokeWidth:2.5,stroke:ct.surface}} animationDuration={ct.motion}/>
                </ComposedChart>
              </ResponsiveContainer>
              <VizLegend items={[
                {label:'Realisasi Kaltara',color:seriesColor(1,theme),shape:'line'},
                {label:'Target',color:seriesColor(2,theme),shape:'line'}
              ]}/>
            </div>
          </>:<ChartSkeleton height={340}/>}
        </div>
      </div>
    </Reveal>

    {detail&&
      <Panel
        delay={60}
        className="regional-section"
        kicker={`Sebaran wilayah · ${detail.tahun||'-'}`}
        title="Perbandingan kabupaten/kota dan Provinsi Kalimantan Utara"
        desc={detail.catatan_wilayah}
        actions={
          <select className="select" value={region} onChange={e=>setRegion(e.target.value)} aria-label="Pilih wilayah">
            {detail.wilayah.map(x=><option value={x.kode} key={x.kode}>{x.nama}</option>)}
          </select>
        }
      >
        <div className="regional-layout">
          <div className="map-panel">
            <h3>Peta Kalimantan Utara</h3>
            <KaltaraMap regions={detail.wilayah} selected={region} onSelect={setRegion} unit={detail.satuan}/>
            <div className="selected-region">
              <span>{selectedRegion?.nama}</span>
              <b>{valueLabel(selectedRegion?.nilai,selectedRegion?.nilai_teks,detail.satuan)}</b>
              <small>{selectedRegion?.status==='TERSEDIA'?'Data terverifikasi':'Belum ada data terverifikasi'}</small>
            </div>
          </div>

          <div className="regional-charts">
            <div>
              <h3>Perbandingan kabupaten/kota</h3>
              {hasRegional
                ?<ResponsiveContainer width="100%" height={250}>
                  <BarChart data={detail.wilayah} layout="vertical" margin={{top:4,right:16,left:0,bottom:0}}>
                    <CartesianGrid stroke={ct.grid} horizontal={false}/>
                    <XAxis type="number" tick={{fontSize:11,fill:ct.axis}} axisLine={false} tickLine={false}/>
                    <YAxis type="category" dataKey="nama" width={92} tick={{fontSize:11,fill:ct.axis}} axisLine={false} tickLine={false}/>
                    <Tooltip cursor={{fill:ct.cursor}} content={<TooltipCard formatter={v=>valueLabel(v,null,detail.satuan)}/>}/>
                    <Bar dataKey="nilai" name="Nilai" fill={seriesColor(0,theme)} radius={[0,6,6,0]} barSize={16} animationDuration={ct.motion}/>
                  </BarChart>
                </ResponsiveContainer>
                :<EmptyState icon={Building2} title="Data kabupaten/kota belum tersedia" desc="Grafik akan terisi setelah data wilayah diverifikasi."/>}
            </div>
            <div>
              <h3>Tren Provinsi Kalimantan Utara</h3>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={detail.series.filter(x=>x.realisasi!==null)} margin={{top:8,right:16,left:0,bottom:0}}>
                  <CartesianGrid stroke={ct.grid} vertical={false}/>
                  <XAxis dataKey="tahun" tick={{fontSize:11,fill:ct.axis}} axisLine={false} tickLine={false}/>
                  <YAxis tick={{fontSize:11,fill:ct.axis}} axisLine={false} tickLine={false}/>
                  <Tooltip cursor={{stroke:ct.baseline,strokeWidth:1}} content={<TooltipCard formatter={v=>valueLabel(v,null,detail.satuan)}/>}/>
                  <Line type="monotone" dataKey="realisasi" name="Realisasi" stroke={seriesColor(1,theme)}
                    strokeWidth={2.5} dot={{r:3.5,fill:ct.surface,stroke:seriesColor(1,theme),strokeWidth:2}}
                    animationDuration={ct.motion}/>
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </Panel>}
  </Shell>
}

/* ==========================================================================
   Capaian menuju 2045
   ========================================================================== */
