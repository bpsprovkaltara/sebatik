import {RUTE} from '../lib/rute'
import {WaveDivider} from '../Brand'
import * as endpoints from '../api/endpoints'
import {EmptyState, Panel, Reveal, SECTION_REVEAL, SectionHead} from '../ui'
import {AlertTriangle, Database, Target} from 'lucide-react'
import {useEffect, useState} from 'react'
import {HomeDoors} from '../components/home/HomeDoors'
import {HomeHero} from '../components/home/HomeHero'
import {MacroCards} from '../components/home/MacroCards'
import {YearPicker} from '../components/home/YearPicker'
import {SiteFooter} from '../components/layout/SiteFooter'
import {Topbar} from '../components/layout/Topbar'
import {usePageTitle} from '../hooks/usePageTitle'
import {fmt, valueLabel} from '../lib/format'

export default function HomePage(){
  const [year,setYear]=useState(''),[data,setData]=useState(null),[error,setError]=useState('')
  /* Beranda memakai kerangkanya sendiri, bukan <Shell>, jadi judul tabnya
     dipasang di sini — tanpa ini ia mewarisi judul halaman sebelumnya. */
  usePageTitle('Beranda')

  useEffect(()=>{
    endpoints.beranda({tahun:year})
      .then(x=>{setData(x);if(!year)setYear(String(x.tahun))})
      .catch(e=>setError(e.message))
  },[year])

  const groups=(data?.sasaran_visi||[]).reduce((acc,x)=>{(acc[x.arah_pembangunan]??=[]).push(x);return acc},{})

  return <div className="app home-app">
    <div className="shell">
      <Topbar active={RUTE.beranda}/>
      <HomeHero/>
      <main>
        <HomeDoors/>
        {error&&<div className="error"><AlertTriangle size={18}/>{error}</div>}

        {/* Ketiga bagian di bawah ini memakai ambang `SECTION_REVEAL`: masing-
            masing baru muncul setelah benar-benar dimasuki pembaca, bukan saat
            tepi atasnya baru mengintip. Kepalanya pun seragam — kicker, judul
            tebal, tanpa kalimat penjelas — supaya turun halaman terasa sebagai
            satu irama yang sama. */}
        <Reveal as="section" className="home-section" delay={60} observe={SECTION_REVEAL}>
          <SectionHead
            kicker={`Outlook ${data?.tahun||''}`}
            title="Indikator makro Kalimantan Utara"
            actions={<YearPicker data={data} year={year} onYearChange={setYear}/>}
          />
          <MacroCards items={data?.indikator_makro||[]} loading={!data}/>
        </Reveal>

        {/* Bagian Sasaran Visi duduk di atas bidang biru yang diapit dua
            pembatas ombak. Bidangnya sewarna dengan lapis depan ombak, jadi
            pertemuan keduanya tidak menyisakan garis lurus — yang memisahkan
            bagian ini dari tetangganya adalah lengkungan ombak itu sendiri. */}
        <WaveDivider tone="band"/>
        <div className="wave-band">
        <Reveal as="section" className="home-section" delay={60} observe={SECTION_REVEAL}>
          <SectionHead
            kicker="Sasaran visi"
            title="Capaian Indikator Sasaran Visi (ISV) Indonesia Emas 2045"
          />
          <div className="vision-grid">
            {Object.entries(groups).map(([group,items],i)=>
              <article className="vision-card" style={{'--tone':`var(--series-${(i%6)+1})`}} key={group}>
                <header>
                  <span>{String(i+1).padStart(2,'0')}</span>
                  <div><h3>{group}</h3><small>{items.length} indikator</small></div>
                </header>
                <div className="vision-list">
                  {items.map(x=>
                    <div key={x.id_indikator}>
                      <i>{x.kode_indikator}</i>
                      <span>{x.nama_indikator}</span>
                      <strong>
                        {valueLabel(x.nilai,x.nilai_teks,x.satuan)}
                        <small>{x.nilai===null&&x.nilai_teks===null?'Belum tersedia':`Target ${valueLabel(x.target,x.target_teks,x.satuan)}`}</small>
                      </strong>
                    </div>
                  )}
                </div>
              </article>
            )}
          </div>
          {data&&!Object.keys(groups).length&&
            <EmptyState icon={Target} title="Sasaran visi belum tersedia" desc="Data akan muncul setelah indikator sasaran visi diverifikasi."/>}
        </Reveal>
        </div>
        <WaveDivider flip tone="band"/>

        <Panel
          delay={80}
          className="availability-section"
          kicker="Kelengkapan realisasi"
          title="Ketersediaan data menurut kerangka pembangunan"
          desc="Persentase menunjukkan berapa banyak nilai realisasi 2021–2025 yang sudah terisi dari yang seharusnya tersedia."
          observe={SECTION_REVEAL}
        >
          <div className="availability-grid">
            {(data?.ketersediaan_kelompok||[]).map((x,i)=>
              <article className="availability-card" style={{'--tone':`var(--series-${(i%6)+1})`}} key={x.kode}>
                <div className="availability-card-head">
                  <span><b>{x.jumlah_kelompok}</b> kelompok</span>
                  <strong>{fmt.format(x.persentase)}%</strong>
                </div>
                <h3>{x.label}</h3>
                <div className="availability-track" aria-label={`${x.persentase}% data tersedia`}>
                  <i style={{width:`${Math.max(0,Math.min(100,x.persentase))}%`}}/>
                </div>
                {/* Kelompok yang sama sekali kosong tidak ditulis "Terisi 0 dari
                    380" — angka nol berjajar begitu terbaca seperti kegagalan
                    hitung. Ia diberi kalimatnya sendiri yang menyebut sebabnya. */}
                <p>
                  {x.slot_terisi
                    ?`Terisi ${fmt.format(x.slot_terisi)} dari ${fmt.format(x.slot_total)} data tahunan · ${fmt.format(x.jumlah_indikator)} indikator, periode 2021–2025`
                    :`Belum ada data — ${fmt.format(x.jumlah_indikator)} indikator pada kelompok ini belum memiliki realisasi 2021–2025.`}
                </p>
              </article>
            )}
          </div>
          {data&&!data.ketersediaan_kelompok?.length&&
            <EmptyState icon={Database} title="Ketersediaan belum dapat dihitung" desc="Klasifikasi indikator atau data realisasi belum tersedia."/>}
        </Panel>
      </main>
    </div>
    <SiteFooter office/>
  </div>
}

/* ==========================================================================
   Peta Kalimantan Utara
   ========================================================================== */

