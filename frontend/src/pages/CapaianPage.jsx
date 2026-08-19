import {RUTE} from '../lib/rute'
import * as endpoints from '../api/endpoints'
import {chartTheme, useTheme} from '../theme'
import {capaianColor, seriesColor} from '../tokens'
import {ChartSkeleton, CountUp, EmptyState, Panel, Reveal, SectionHead, TooltipCard, VizLegend} from '../ui'
import {Activity, AlertTriangle, Info, Sparkles} from 'lucide-react'
import {useEffect, useState} from 'react'
import {Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts'
import {AnnualChangeTooltip} from '../components/charts/AnnualChangeTooltip'
import {Shell} from '../components/layout/Shell'
import {softNumber, valueLabel} from '../lib/format'

export default function CapaianPage(){
  const [config,setConfig]=useState({indikator:[],kelompok:[],wilayah:[]}),[id,setId]=useState(''),
    [group,setGroup]=useState(''),[year,setYear]=useState(''),[region,setRegion]=useState('65'),
    [detail,setDetail]=useState(null),[search,setSearch]=useState(''),[error,setError]=useState('')
  const [theme]=useTheme()
  const ct=chartTheme(theme)

  useEffect(()=>{
    endpoints.capaianExplorer().then(x=>{
      setConfig(x)
      if(x.indikator.length)setId(x.indikator[0].id_indikator)
    }).catch(e=>setError(e.message))
  },[])

  useEffect(()=>{
    let cancelled=false
    if(id)endpoints.capaianExplorerDetail(id,{tahun:year,wilayah_kode:region}).then(x=>{
      if(cancelled)return
      setDetail(x)
      if(!year&&x.tahun)setYear(String(x.tahun))
    }).catch(e=>{if(!cancelled)setError(e.message)})
    return()=>{cancelled=true}
  },[id,year,region])

  const choices=config.indikator.filter(x=>
    (!group||x.kelompok===group)&&
    (!search||x.nama_indikator.toLowerCase().includes(search.toLowerCase())||x.kode_indikator.toLowerCase().includes(search.toLowerCase()))
  )
  const selectIndicator=value=>{setDetail(null);setId(value);setYear('')}
  const setGroupFilter=value=>{
    setGroup(value)
    const first=config.indikator.find(x=>
      (!value||x.kelompok===value)&&
      (!search||x.nama_indikator.toLowerCase().includes(search.toLowerCase())||x.kode_indikator.toLowerCase().includes(search.toLowerCase()))
    )
    selectIndicator(first?.id_indikator||'')
  }
  const setSearchFilter=value=>{
    setSearch(value)
    const query=value.toLowerCase()
    const first=config.indikator.find(x=>
      (!group||x.kelompok===group)&&
      (!query||x.nama_indikator.toLowerCase().includes(query)||x.kode_indikator.toLowerCase().includes(query))
    )
    if(first?.id_indikator!==id)selectIndicator(first?.id_indikator||'')
  }

  /* Cincin tracker mengukur jarak menuju target 2029, bukan 2045. Horizon
     lima tahun masih bisa ditindaklanjuti perencana tahun ini; pada horizon
     dua puluh tahun hampir semua indikator terbaca "baru sedikit" sehingga
     angkanya tidak membedakan apa pun. Target 2045 tetap ditampilkan sebagai
     tujuan akhir di kotak keterangan di bawah cincin. */
  const progress=detail?.progres_2029
  const donutRest=ct.dark?'#362A28':'#F0E4D5'
  const donut=[
    {name:'Progres',value:progress??0,color:seriesColor(0,theme)},
    {name:'Sisa',value:progress===null||progress===undefined?100:Math.max(0,100-progress),color:donutRest}
  ]
  const barData=(detail?.series||[]).map((x,index)=>({
    ...x,
    previousYear:index>0?detail.series[index-1].tahun:null,
    previousValue:index>0?detail.series[index-1].nilai:null
  })).filter(x=>x.growth!==null)
  const improvement=x=>detail?.arah_target==='TURUN'?x.growth<=0:x.growth>=0
  const upColor=capaianColor('TERCAPAI',theme),downColor=capaianColor('PERLU_PERHATIAN',theme)

  return <Shell
    active={RUTE.capaian}
    title="Capaian"
    subtitle="Pantau perubahan tahunan dan progres indikator terverifikasi menuju target Kalimantan Utara 2045."
  >
    {error&&<div className="error"><AlertTriangle size={18}/>{error}</div>}

    <Reveal as="section" className="panel achievement-filters">
      <label className="field">
        <span>Nama indikator</span>
        <input value={search} onChange={e=>setSearchFilter(e.target.value)} placeholder="Cari nama atau kode..."/>
      </label>
      <label className="field">
        <span>Kelompok</span>
        <select value={group} onChange={e=>setGroupFilter(e.target.value)}>
          <option value="">Semua kelompok</option>
          {config.kelompok.map(x=><option key={x}>{x}</option>)}
        </select>
      </label>
      <label className="field">
        <span>Indikator</span>
        <select value={id} onChange={e=>selectIndicator(e.target.value)}>
          {/* Tanpa awalan kode. Kodenya tidak menolong saat memilih dari
              daftar — ia menggeser semua nama sejauh lebar kode dan bikin
              mata sulit memindai. Kode indikator tetap tampil di kepala
              analisis begitu satu indikator terpilih. */}
          {choices.map(x=><option value={x.id_indikator} key={x.id_indikator}>{x.nama_indikator}</option>)}
        </select>
      </label>
      <label className="field">
        <span>Tahun analisis</span>
        <select value={year} onChange={e=>setYear(e.target.value)}>
          {(detail?.tahun_tersedia||[]).map(x=><option key={x}>{x}</option>)}
        </select>
      </label>
      <label className="field">
        <span>Wilayah</span>
        <select value={region} onChange={e=>{setDetail(null);setRegion(e.target.value);setYear('')}}>
          {config.wilayah.map(x=><option value={x.kode} key={x.kode}>{x.nama}</option>)}
        </select>
      </label>
    </Reveal>

    {detail&&<>
      <Reveal as="section" delay={60} className="panel achievement-overview">
        <div className="achievement-heading">
          <span>Indikator {detail.kategori}-{detail.kode_indikator}</span>
          <h2>{detail.nama_indikator}</h2>
          <p>{detail.kelompok} · {detail.arah_target==='TURUN'?'Semakin rendah semakin baik':detail.arah_target==='NAIK'?'Semakin tinggi semakin baik':'Arah target belum ditentukan'}</p>
        </div>
        {detail.catatan_wilayah&&<div className="notice warning"><Info size={17}/>{detail.catatan_wilayah}</div>}

        <div className="achievement-grid">
          <div className="growth-chart">
            <SectionHead
              level={3}
              kicker="Perubahan tahunan"
              title="Perubahan realisasi dibanding tahun sebelumnya"
              desc="Setiap batang membandingkan realisasi satu tahun dengan realisasi terakhir sebelumnya. Warna menunjukkan apakah pergerakannya searah dengan target 2045."
            />
            {barData.length?<>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={barData} margin={{top:15,right:15,left:18,bottom:5}}>
                  <CartesianGrid stroke={ct.grid} vertical={false}/>
                  <XAxis dataKey="tahun" tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
                  <YAxis tickFormatter={x=>`${x}%`} tick={{fontSize:11,fill:ct.axis}} axisLine={false} tickLine={false}
                    label={{value:'Perubahan (%)',angle:-90,position:'insideLeft',fill:ct.axis,fontSize:11}}/>
                  <ReferenceLine y={0} stroke={ct.baseline} strokeWidth={1.5}/>
                  <Tooltip cursor={{fill:ct.cursor}} content={<AnnualChangeTooltip arahTarget={detail.arah_target}/>}/>
                  <Bar dataKey="growth" name="Growth" radius={[6,6,0,0]} animationDuration={ct.motion}>
                    {barData.map(x=>
                      <Cell key={x.tahun} fill={improvement(x)?upColor:downColor} opacity={x.tahun===detail.tahun?1:.62}/>
                    )}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <VizLegend items={[
                {label:'Searah dengan target 2045',color:upColor},
                {label:'Berlawanan arah dengan target 2045',color:downColor}
              ]}/>
            </>:<EmptyState icon={Activity} title="Growth belum tersedia" desc="Diperlukan minimal dua tahun realisasi terverifikasi."/>}
          </div>

          <div className="tracker-card">
            <SectionHead level={3} kicker="Tracker 2029" title="Progres terhadap target"/>
            <div className="tracker-donut">
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={donut} dataKey="value" innerRadius={76} outerRadius={106} startAngle={90} endAngle={-270}
                    stroke={ct.surface} strokeWidth={2} animationDuration={ct.motion}>
                    {donut.map(x=><Cell key={x.name} fill={x.color}/>)}
                  </Pie>
                  <Tooltip content={<TooltipCard formatter={v=>`${v}%`}/>}/>
                </PieChart>
              </ResponsiveContainer>
              <div>
                <strong>{progress===null||progress===undefined?'—':<><CountUp value={progress} format={softNumber}/>%</>}</strong>
                <span>menuju 2029</span>
              </div>
            </div>
            <dl className="tracker-stats">
              <div><dt>Realisasi {detail.tahun||'-'}</dt><dd>{valueLabel(detail.nilai_tahun,detail.nilai_teks,detail.satuan)}</dd></div>
              <div><dt>Target 2029</dt><dd>{valueLabel(detail.target_2029,detail.target_2029_teks,detail.satuan)}</dd></div>
              <div><dt>Target 2045</dt><dd>{valueLabel(detail.target_2045,detail.target_2045_teks,detail.satuan)}</dd></div>
            </dl>
          </div>
        </div>
      </Reveal>

      <Panel
        delay={60}
        className="target-trajectory"
        kicker="Jalur menuju 2045"
        title="Realisasi tahun berjalan dan target akhir"
        desc="Garis putus-putus adalah jalur linear dari tahun analisis menuju target, bukan proyeksi resmi."
      >
        {detail.projection.some(x=>x.realisasi!==null)?<>
          <ResponsiveContainer width="100%" height={360}>
            <LineChart data={detail.projection} margin={{top:20,right:28,left:5,bottom:8}}>
              <CartesianGrid stroke={ct.grid} vertical={false}/>
              <XAxis dataKey="tahun" tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
              <YAxis tick={{fontSize:11,fill:ct.axis}} axisLine={false} tickLine={false}/>
              <Tooltip cursor={{stroke:ct.baseline,strokeWidth:1}} content={<TooltipCard formatter={v=>valueLabel(v,null,detail.satuan)}/>}/>
              <Line type="monotone" dataKey="realisasi" name="Realisasi terverifikasi"
                stroke={seriesColor(1,theme)} strokeWidth={2.5} connectNulls
                dot={{r:4,fill:ct.surface,stroke:seriesColor(1,theme),strokeWidth:2.5}}
                activeDot={{r:6,strokeWidth:2.5,stroke:ct.surface}} animationDuration={ct.motion}/>
              <Line type="linear" dataKey="jalur_target" name="Jalur linear ke target"
                stroke={seriesColor(2,theme)} strokeWidth={2} strokeDasharray="8 6" connectNulls
                dot={{r:3.5}} animationDuration={ct.motion}/>
            </LineChart>
          </ResponsiveContainer>
          <VizLegend items={[
            {label:'Realisasi terverifikasi',color:seriesColor(1,theme),shape:'line'},
            {label:'Jalur linear ke target',color:seriesColor(2,theme),shape:'line'}
          ]}/>
        </>:<EmptyState icon={Activity} title="Seri data belum tersedia" desc="Visualisasi akan muncul setelah data wilayah diverifikasi."/>}

        <div className="insight-box">
          <Sparkles size={20}/>
          <div><b>Insight otomatis</b><p>{detail.insight}</p></div>
        </div>
        <p className="method-note">
          Progres dihitung dari posisi realisasi tahun analisis terhadap perjalanan antara baseline pertama dan target 2045.
          Nilai dibatasi 0–100% agar mudah dibaca.
        </p>
      </Panel>
    </>}

    {!detail&&!error&&<div className="panel"><ChartSkeleton height={320}/></div>}
  </Shell>
}

/* ==========================================================================
   Detail indikator
   ========================================================================== */
