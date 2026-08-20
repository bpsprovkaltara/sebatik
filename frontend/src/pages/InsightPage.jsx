import {RUTE} from '../lib/rute'
import * as endpoints from '../api/endpoints'
import {chartTheme, useTheme} from '../theme'
import {seriesColor} from '../tokens'
import {TooltipCard} from '../components/charts/TooltipCard'
import {ChartSkeleton, EmptyState, Panel, Reveal} from '../ui'
import {SmartSelect} from '../components/ui/SmartSelect'
import {Activity, AlertTriangle, Building2, Info} from 'lucide-react'
import {useEffect, useState} from 'react'
import {Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts'
import {CardRail} from '../components/home/CardRail'
import {Shell} from '../components/layout/Shell'
import {KaltaraMap} from '../components/maps/KaltaraMap'
import {growthTone, stripUnit, valueLabel, valueParts, valueTone} from '../lib/format'

export default function InsightPage(){
  const [data,setData]=useState(null),[indicator,setIndicator]=useState(''),[region,setRegion]=useState('65'),
    [mapRegion,setMapRegion]=useState(''),[error,setError]=useState('')
  const [theme]=useTheme()
  const ct=chartTheme(theme)

  useEffect(()=>{
    let cancelled=false
    endpoints.insight({indikator_id:indicator,wilayah_kode:region}).then(x=>{
      if(cancelled)return
      setData(x)
      if(!indicator&&x.indikator_aktif)setIndicator(x.indikator_aktif.id_indikator)
      if(!mapRegion&&x.perbandingan_wilayah?.length)setMapRegion(x.perbandingan_wilayah[0].kode)
    }).catch(e=>{if(!cancelled)setError(e.message)})
    return()=>{cancelled=true}
  },[indicator,region])

  const activeRegion=data?.perbandingan_wilayah?.find(x=>x.kode===mapRegion)
  const hasRegional=data?.perbandingan_wilayah?.some(x=>x.nilai!==null||x.nilai_teks)

  return <Shell
    active={RUTE.insight}
    title="Insight"
    subtitle="Situasi indikator makro Kalimantan Utara berdasarkan tahun berjalan atau data terverifikasi terakhir yang tersedia"
  >
    {error&&<div className="error"><AlertTriangle size={18}/>{error}</div>}

    <Reveal as="section" className="insight-toolbar">
      <div>
        <span className="kicker">Indikator makro pembangunan</span>
      </div>
      {/* Tanpa label "Wilayah" di sampingnya: isian ini sudah berisi nama
          wilayah, jadi labelnya hanya mengulang sambil mendorong kotaknya
          menjauh dari tepi kanan. Nama tetap ada untuk pembaca layar. */}
      <SmartSelect
        className="year-picker"
        value={region}
        onChange={value=>{setRegion(value);setIndicator('')}}
        options={(data?.wilayah_opsi||[]).map(x=>({value:x.kode,label:x.nama}))}
        ariaLabel="Wilayah"
        placeholder="Pilih wilayah"
      />
    </Reveal>

    {/* Kartu pemilih memakai rel yang sama dengan korsel beranda, tetapi tanpa
        putaran otomatis — lihat catatan di CardRail. Isi kartu dan aksinya
        tidak berubah: satu klik tetap memuat tren dan perbandingan wilayah
        untuk indikator itu. */}
    <Reveal as="div" delay={60}>
      <CardRail count={data?.indikator_makro?.length||0} className="macro-selector">
        {(data?.indikator_makro||[]).map((x,i)=>{
          const nilai=valueParts(x.nilai,x.nilai_teks,x.satuan)
          return <button
            key={x.id_indikator}
            className={data?.indikator_aktif?.id_indikator===x.id_indikator?'active':''}
            style={{'--tone':`var(--series-${(i%6)+1})`}}
            onClick={()=>setIndicator(x.id_indikator)}
            aria-pressed={data?.indikator_aktif?.id_indikator===x.id_indikator}
          >
            {/* Label periode memakai keterangan terperinci dari backend bila
                ada — "Semester 2 2025", "Triwulan II 2025" — sebab nilai yang
                ditampilkan memang diambil dari periode terakhir yang disetujui,
                bukan dari tahunnya secara utuh. Menulis "2025" saja membuat
                angka semesteran terbaca seolah angka setahun penuh. */}
            <span>{x.label_periode||x.tahun||'Belum ada tahun'}</span>
            <strong className={valueTone(x.nilai).trim()}>
              <span>{nilai.number}</span>
              {nilai.unit&&<small className={`selector-unit${nilai.unit==='%'?' is-symbol':''}`}>{nilai.unit}</small>}
            </strong>
            <b>{stripUnit(x.nama_indikator)}</b>
            <small className={growthTone(x.perubahan)}>
              {x.perubahan===null
                ?'Perbandingan belum tersedia'
                :`${x.perubahan>0?'↑':x.perubahan<0?'↓':'—'} ${valueLabel(Math.abs(x.perubahan),null,x.satuan)} dari tahun sebelumnya`}
            </small>
          </button>
        })}
      </CardRail>
    </Reveal>

    {data?.indikator_aktif&&
      <Panel
        delay={60}
        className="insight-analysis"
        kicker={`${data.indikator_aktif.kode_indikator} · ${data.indikator_aktif.tahun||'Belum ada data'}`}
        title={stripUnit(data.indikator_aktif.nama_indikator)}
        desc={`Sumber Data: ${data.indikator_aktif.sumber_data||'Belum dicatat'}`}
      >
        <div className="insight-layout">
          <div className="macro-trend">
            <h3>Tren Provinsi Kalimantan Utara</h3>
            {data.series.length?<>
              {/* Satuan dipisah dari angkanya dan turun ke barisnya sendiri
                  dengan ukuran lebih kecil. Sebagai satu untai — "157,09 Juta
                  Rupiah" — tiap kartu tahun jadi selebar nama satuannya, dan
                  lima kartu berderet melampaui lebar panel sehingga deretnya
                  harus digeser mendatar hanya untuk membaca tahun terakhir. */}
              <div className="series-cards">
                {data.series.map(x=>{
                  const nilai=valueParts(x.nilai,null,data.indikator_aktif.satuan)
                  return <div className={x.tahun===data.indikator_aktif.tahun?'selected':''} key={x.tahun}>
                    <span>{x.tahun}</span>
                    <b>
                      {nilai.number}
                      {nilai.unit&&<i className={nilai.unit==='%'?'is-symbol':''}>{nilai.unit}</i>}
                    </b>
                    <small className={growthTone(x.growth)}>
                      {x.growth===null?'—':`${x.growth>0?'↑':x.growth<0?'↓':'—'} ${Math.abs(x.growth)}%`}
                    </small>
                  </div>
                })}
              </div>
              <ResponsiveContainer width="100%" height={330}>
                <AreaChart data={data.series} margin={{top:18,right:22,left:0,bottom:5}}>
                  <defs>
                    <linearGradient id="grad-insight" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={seriesColor(1,theme)} stopOpacity={.3}/>
                      <stop offset="100%" stopColor={seriesColor(1,theme)} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={ct.grid} vertical={false}/>
                  <XAxis dataKey="tahun" tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
                  <YAxis tick={{fontSize:11,fill:ct.axis}} axisLine={false} tickLine={false}/>
                  <Tooltip cursor={{stroke:ct.baseline,strokeWidth:1}} content={<TooltipCard formatter={v=>valueLabel(v,null,data.indikator_aktif.satuan)}/>}/>
                  <Area type="monotone" dataKey="nilai" name="Nilai" stroke={seriesColor(1,theme)} strokeWidth={2.5}
                    fill="url(#grad-insight)" dot={{r:4,fill:ct.surface,stroke:seriesColor(1,theme),strokeWidth:2.5}}
                    activeDot={{r:6,strokeWidth:2.5,stroke:ct.surface}} animationDuration={ct.motion}/>
                </AreaChart>
              </ResponsiveContainer>
            </>:<EmptyState icon={Activity} title="Data makro wilayah belum tersedia" desc="Nilai akan muncul setelah diverifikasi."/>}
          </div>

          <div className="macro-regional">
            <div className="macro-map">
              <h3>Peta kabupaten/kota</h3>
              <KaltaraMap regions={data.perbandingan_wilayah} selected={mapRegion} onSelect={setMapRegion} unit={data.indikator_aktif.satuan}/>
              <div className="selected-region">
                <span>{activeRegion?.nama}</span>
                <b>{valueLabel(activeRegion?.nilai,activeRegion?.nilai_teks,data.indikator_aktif.satuan)}</b>
                <small>{activeRegion?.status==='TERSEDIA'?'Data terverifikasi':'Belum ada data'}</small>
              </div>
            </div>
            <div className="macro-bars">
              <h3>Perbandingan kabupaten/kota</h3>
              {hasRegional
                ?<ResponsiveContainer width="100%" height={230}>
                  <BarChart data={data.perbandingan_wilayah} layout="vertical" margin={{top:4,right:16,left:0,bottom:0}}>
                    <CartesianGrid stroke={ct.grid} horizontal={false}/>
                    <XAxis type="number" tick={{fontSize:11,fill:ct.axis}} axisLine={false} tickLine={false}/>
                    <YAxis type="category" dataKey="nama" width={90} tick={{fontSize:11,fill:ct.axis}} axisLine={false} tickLine={false}/>
                    <Tooltip cursor={{fill:ct.cursor}} content={<TooltipCard formatter={v=>valueLabel(v,null,data.indikator_aktif.satuan)}/>}/>
                    <Bar dataKey="nilai" name="Nilai" fill={seriesColor(0,theme)} radius={[0,6,6,0]} barSize={15} animationDuration={ct.motion}/>
                  </BarChart>
                </ResponsiveContainer>
                :<EmptyState icon={Building2} compact title="Belum ada data kabupaten/kota" desc="Grafik akan terisi setelah verifikasi wilayah."/>}
            </div>
          </div>
        </div>
        {data.catatan_wilayah&&<div className="notice warning"><Info size={17}/>{data.catatan_wilayah}</div>}
      </Panel>}

    {!data&&!error&&<div className="panel"><ChartSkeleton height={300}/></div>}
  </Shell>
}

/* ==========================================================================
   Validitas
   ========================================================================== */
