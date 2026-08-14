import {useEffect,useRef,useState} from 'react'
import {
  Activity,AlertTriangle,ArrowLeft,ArrowUpRight,Building2,CheckCircle2,ChevronDown,ChevronLeft,ChevronRight,
  Compass,Database,Download,Eye,EyeOff,FileWarning,Home,Info,ListChecks,LogOut,Mail,MapPin,Menu,Moon,Phone,
  KeyRound,Search,ShieldCheck,Sparkles,Sun,Target,UserRound,X
} from 'lucide-react'
import {
  Area,AreaChart,Bar,BarChart,CartesianGrid,Cell,ComposedChart,Line,LineChart,Pie,PieChart,
  ReferenceLine,ResponsiveContainer,Scatter,ScatterChart,Tooltip,XAxis,YAxis
} from 'recharts'
import {api,qs} from './api'
import {clearToken,roleLabel,setToken,useProfile,useToken} from './auth'
import {AuroraField,BatikLayer,WaveDivider,WaveEdge} from './Brand'
import {chartTheme,useTheme} from './theme'
import {capaianColor,capaianVar,seriesColor} from './tokens'
import {
  ChartSkeleton,CountUp,DeltaPill,EmptyState,Panel,Reveal,SECTION_REVEAL,ScrollProgress,SectionHead,
  SkeletonCard,TooltipCard,VizLegend,useScrolled
} from './ui'

const fmt=new Intl.NumberFormat('id-ID')
const changeNumber=new Intl.NumberFormat('id-ID',{minimumFractionDigits:2,maximumFractionDigits:2})
const displayedUnit=unit=>{
  if(!unit||/^indeks\b/i.test(unit))return ''
  if(/persen|\(%\)|% PDRB/i.test(unit))return '%'
  return unit
}
const valueLabel=(value,text,unit)=>{
  if(value===null||value===undefined)return text||'Belum tersedia'
  const suffix=displayedUnit(unit)
  return `${fmt.format(value)}${suffix==='%'?'%':suffix?` ${suffix}`:''}`
}

function AnnualChangeTooltip({active,payload,arahTarget}){
  if(!active||!payload?.length)return null
  const item=payload[0]?.payload
  if(!item||item.previousValue===null||item.previousValue===undefined)return null
  const pointChange=item.nilai-item.previousValue
  const movement=pointChange>0?'Naik':pointChange<0?'Turun':'Tetap'
  const targetRelation=(arahTarget==='TURUN'?item.growth<=0:item.growth>=0)
    ?'searah dengan target 2045'
    :'berlawanan arah dengan target 2045'
  const signedGrowth=`${item.growth>0?'+':item.growth<0?'−':''}${changeNumber.format(Math.abs(item.growth))}%`
  return <div className="viz-tooltip annual-change-tooltip" role="tooltip">
    <strong>{item.tahun} · realisasi {changeNumber.format(item.nilai)}</strong>
    <span>{movement} {changeNumber.format(Math.abs(pointChange))} poin dari {item.previousYear} ({changeNumber.format(item.previousValue)})</span>
    <span>{signedGrowth} · {targetRelation}</span>
  </div>
}
/* Ukuran angka sorotan dipasang untuk angka. Ketika yang tampil justru kalimat
   — "Belum tersedia" — ukuran itu membuatnya berteriak lebih keras daripada
   angka yang benar-benar ada di kartu sebelahnya. Penanda ini dipakai untuk
   menurunkan ukurannya, bukan untuk menyembunyikannya. */
const hasNumber=value=>value!==null&&value!==undefined
const valueTone=value=>hasNumber(value)?'':' is-empty'

/* Warna pertumbuhan pada kartu tahun: naik hijau, turun merah, datar netral.
   Perlu dicatat bahwa ini mewarnai ARAH ANGKA, bukan baik-buruknya keadaan.
   Pada indikator yang arah baiknya menurun — tingkat kemiskinan, pengangguran,
   rasio gini — kenaikan angka justru kabar buruk tetapi tetap tampil hijau.
   Basis data menyimpan `arah_baik`/`arah_target` bila suatu saat pewarnaan
   ingin diikatkan ke makna, bukan ke arah. */
const growthTone=growth=>growth===null||growth===0?'growth-flat':growth>0?'growth-up':'growth-down'
/* Format angka animasi: pertahankan satu desimal supaya nilai persen tidak
   kehilangan ketelitian saat dihitung naik. */
const softNumber=v=>fmt.format(Number(Number(v).toFixed(1)))

/* Peta rute -> label, ikon, dan deskripsi singkat untuk navigasi. */
const NAV_LINKS=[
  ['#beranda','Beranda',Home],
  ['#indikator','Indikator',Compass],
  ['#capaian','Capaian',Target],
  ['#insight','Insight',Sparkles],
  ['#validitas','Validitas',ShieldCheck]
]

/* Slot terakhir navigasi mengikuti status masuk.

   Sebelum ini slot tersebut memuat satu kendali saja: "Masuk" ketika belum
   masuk, "Keluar" ketika sudah. Penggabungan itu menutup satu-satunya jalan
   kembali — begitu pengguna yang sudah masuk membuka Beranda atau Indikator,
   tidak ada lagi tautan menuju ruang kerjanya, dan satu-satunya kendali yang
   tersisa justru mengakhiri sesinya. Ruang kerjanya masih hidup di #login,
   tetapi hanya bisa dicapai dengan mengetik sendiri di bilah alamat.

   Karena itu keadaan "sudah masuk" kini memuat dua kendali terpisah: jalan
   kembali ke ruang kerja, dan keluar. Keduanya perbuatan yang berbeda, jadi
   memang tidak sepantasnya berbagi satu tombol. */
/* Judul tab memuat nama fitur saja — "Beranda", "Indikator", "Login Admin".
   Sebelumnya ia merangkai nama fitur dengan nama panjang sistem, dan di lebar
   tab yang biasa hasilnya terpotong justru pada bagian yang membedakan satu
   tab dari tab lain. Nama sistem sudah dibawa favicon di sebelahnya.

   Judul dipasang oleh satu pemilik saja. `undefined` berarti "aku tidak
   mengatur judul", bukan "kosongkan judulnya" — tanpa pembedaan itu, <Shell>
   yang dipakai tanpa `title` akan menimpa judul yang baru saja dipasang
   halaman di atasnya, dan ruang kerja kehilangan sebutan perannya. */
function usePageTitle(title){
  useEffect(()=>{
    if(title===undefined)return
    document.title=title||'SEBATIK'
  },[title])
}

const authNavItems=(token,profile)=>token
  ? [
      {hash:'#login',label:roleLabel(profile?.peran),icon:UserRound,logout:false},
      {hash:'#beranda',label:'Keluar',icon:LogOut,logout:true}
    ]
  : [{hash:'#login',label:'Masuk',icon:UserRound,logout:false}]

function CapaianBadge({status}){
  const key=status||'BELUM_ADA_DATA'
  return <span className="capaian-badge" style={{'--tone':capaianVar(key)}}>{key.replaceAll('_',' ')}</span>
}

/* ==========================================================================
   Kartu metrik
   ========================================================================== */

function MetricCard({icon:Icon,label,value,note,tone='var(--series-1)',meter=null,index=0}){
  const [mounted,setMounted]=useState(false)
  useEffect(()=>{const timer=setTimeout(()=>setMounted(true),120+index*80);return()=>clearTimeout(timer)},[index])
  return <Reveal as="article" delay={index*70} className="metric-card" style={{'--tone':tone,'--i':index}}>
    <div className="metric-top"><span className="metric-icon"><Icon size={20}/></span></div>
    <p className="metric-label">{label}</p>
    <strong className="metric-value">
      {typeof value==='number'?<CountUp value={value} format={v=>fmt.format(Math.round(v))}/>:value}
    </strong>
    <span className="metric-note">{note}</span>
    {meter!==null&&<div className="metric-meter" role="presentation"><i style={{width:`${mounted?meter:0}%`}}/></div>}
  </Reveal>
}

/* ==========================================================================
   Kerangka halaman
   ========================================================================== */

function Topbar({active}){
  const [theme,toggle]=useTheme()
  const [open,setOpen]=useState(false)
  const scrolled=useScrolled()
  const token=useToken()
  const profile=useProfile()
  const authItems=authNavItems(token,profile)
  const onAuth=item=>{if(item.logout)clearToken();setOpen(false)}
  /* Hanya tautan yang benar-benar menuju sebuah halaman yang boleh ditandai
     aktif. "Keluar" adalah tindakan, bukan tujuan — ia tidak pernah aktif. */
  const isAuthActive=item=>!item.logout&&active===item.hash

  useEffect(()=>{
    const close=()=>setOpen(false)
    addEventListener('hashchange',close)
    return()=>removeEventListener('hashchange',close)
  },[])

  useEffect(()=>{
    if(!open)return
    const onKey=event=>{if(event.key==='Escape')setOpen(false)}
    addEventListener('keydown',onKey)
    document.body.style.overflow='hidden'
    return()=>{removeEventListener('keydown',onKey);document.body.style.overflow=''}
  },[open])

  return <>
    <header className="topbar" data-scrolled={String(scrolled)}>
      <a className="brand" href="#beranda" aria-label="SEBATIK — kembali ke beranda">
        <span className="brand-mark"><img src="/logo-sebatik-monitoring.png" alt=""/></span>
        <span className="brand-name"><b>SEBATIK</b><small>BPS Provinsi Kalimantan Utara</small></span>
      </a>

      <nav className="nav-desktop" aria-label="Navigasi utama">
        {NAV_LINKS.map(([hash,label])=>
          <a key={hash} href={hash} className={active===hash?'active':''} aria-current={active===hash?'page':undefined}>
            {label}
          </a>
        )}
        {authItems.map(item=>
          <a
            key={item.label}
            href={item.hash}
            onClick={()=>onAuth(item)}
            className={`nav-auth${item.logout?' is-out':''}${isAuthActive(item)?' active':''}`}
            aria-current={isAuthActive(item)?'page':undefined}
          >
            <item.icon size={16} aria-hidden="true"/>{item.label}
          </a>
        )}
      </nav>

      <div className="topbar-tools">
        <button
          className="icon-btn"
          onClick={toggle}
          title={theme==='dark'?'Beralih ke mode terang':'Beralih ke mode gelap'}
          aria-label={theme==='dark'?'Beralih ke mode terang':'Beralih ke mode gelap'}
        >
          {theme==='dark'?<Sun size={18}/>:<Moon size={18}/>}
        </button>
        <button
          className="icon-btn nav-toggle"
          onClick={()=>setOpen(v=>!v)}
          aria-label={open?'Tutup menu':'Buka menu'}
          aria-expanded={open}
        >
          {open?<X size={19}/>:<Menu size={19}/>}
        </button>
      </div>

      <ScrollProgress/>
    </header>

    <div className="nav-drawer" data-open={String(open)} aria-hidden={!open}>
      <div className="nav-drawer-scrim" onClick={()=>setOpen(false)}/>
      <nav className="nav-drawer-panel" aria-label="Navigasi seluler">
        {NAV_LINKS.map(([hash,label,Icon],index)=>
          <a
            key={hash}
            href={hash}
            style={{'--i':index}}
            className={active===hash?'active':''}
            aria-current={active===hash?'page':undefined}
            onClick={()=>setOpen(false)}
          >
            <span><Icon size={18}/>{label}</span>
            <ChevronRight size={16}/>
          </a>
        )}
        {authItems.map((item,i)=>
          <a
            key={item.label}
            href={item.hash}
            style={{'--i':NAV_LINKS.length+i}}
            className={`nav-auth${item.logout?' is-out':''}${isAuthActive(item)?' active':''}`}
            aria-current={isAuthActive(item)?'page':undefined}
            onClick={()=>onAuth(item)}
          >
            <span><item.icon size={18}/>{item.label}</span>
            <ChevronRight size={16}/>
          </a>
        )}
        <p className="nav-drawer-note">
          Dasbor pemantauan capaian indikator ISV–IUP, RPJPN 2025–2045.
        </p>
      </nav>
    </div>
  </>
}

/* Peta kantor. Sengaja memakai sematan Google tanpa kunci API supaya tidak
   ada rahasia yang perlu disimpan di frontend. Alamat dan tautan di bawahnya
   berdiri sendiri, jadi ketika jaringan kantor memblokir domain Google
   informasinya tetap lengkap — bingkai kosong, isi tidak hilang. */
const OFFICE_QUERY='Badan Pusat Statistik Provinsi Kalimantan Utara, Jl. Jelarai Raya, Tanjung Selor Hilir'
const OFFICE_EMBED=`https://maps.google.com/maps?q=${encodeURIComponent(OFFICE_QUERY)}&z=16&output=embed`
const OFFICE_LINK=`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(OFFICE_QUERY)}`

const FOOTER_CONTACT=[
  [MapPin,'Alamat','Jl. Jelarai Raya RT 75 RW 28, Tanjung Selor Hilir, Bulungan 77212'],
  [Phone,'Telepon','(0552) 2033254 · WhatsApp 0822-5442-6005']
]

/* Panel alamat dan peta hanya dipasang di beranda — di sana ia berperan sebagai
   penutup identitas. Halaman lain cukup memakai satu baris hak cipta supaya
   kaki halaman tidak mengulang informasi yang sama di setiap layar. */
function SiteFooter({office=false}){
  return <footer className={`site-footer${office?'':' is-slim'}`}>
    {office&&<div className="footer-panel">
      <div className="footer-info">
        <h2>Badan Pusat Statistik<em>Provinsi Kalimantan Utara</em></h2>

        <dl className="footer-contact">
          {FOOTER_CONTACT.map(([Icon,label,value])=>
            <div key={label}>
              <dt><Icon size={17}/><span>{label}</span></dt>
              <dd>{value}</dd>
            </div>
          )}
          <div>
            <dt><Mail size={17}/><span>Surel</span></dt>
            <dd><a href="mailto:bps6500@bps.go.id">bps6500@bps.go.id</a></dd>
          </div>
        </dl>
      </div>

      <div className="footer-map">
        <iframe
          src={OFFICE_EMBED}
          title="Peta lokasi kantor BPS Provinsi Kalimantan Utara"
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          allowFullScreen
        />
        <a className="footer-map-link" href={OFFICE_LINK} target="_blank" rel="noreferrer">
          <span><b>Kantor BPS Kalimantan Utara</b><small>Tanjung Selor, Bulungan</small></span>
          <ArrowUpRight size={17}/>
        </a>
      </div>
    </div>}

    <div className="footer-base">
      <small>© {new Date().getFullYear()} Tim Kerja ISV-IUP BPS Provinsi Kalimantan Utara · Hak Cipta Dilindungi.</small>
    </div>
  </footer>
}

/* Kepala halaman sengaja hanya memuat satu kalimat. Nama fiturnya sudah
   terbaca di navigasi dan di judul tab, jadi mengulangnya sebagai judul besar
   cuma menambah tinggi tanpa menambah keterangan. Yang tersisa adalah kalimat
   yang benar-benar menjelaskan isi halaman, diberi ruang untuk bernapas.
   Properti `title` tetap diterima karena dipakai untuk judul dokumen. */
function Shell({active,title,subtitle,bare=false,children}){
  usePageTitle(title)

  if(bare)return <div className="app">
    <div className="shell">
      <Topbar active={active}/>
      <main className="bare-main">{children}</main>
    </div>
    <SiteFooter/>
  </div>

  return <div className="app">
    <div className="shell">
      <Topbar active={active}/>
      <header className="hero">
        <AuroraField/>
        <BatikLayer opacity={.09} drift/>
        {/* Kalimat ini adalah judul halaman yang sebenarnya — karena itu ia
            tetap <h1>, meski tampil sebagai kalimat pengantar, bukan label.
            `key` membuat React memasang ulang simpulnya tiap kali kalimatnya
            berganti, jadi animasi masuknya ikut berjalan lagi saat pindah
            halaman — sementara aurora dan batik di belakangnya tidak ikut
            direset karena berada di luar simpul ini. */}
        <h1 className="hero-lead" key={subtitle}>{subtitle}</h1>
        <WaveEdge/>
      </header>
      {/* Jeda berjalan antara pita kepala dan isi halaman, sama seperti yang
          memisahkan bagian-bagian di beranda — supaya kedua jenis halaman
          memakai bahasa peralihan yang sama. */}
      <WaveDivider tone="soft"/>
      <main>{children}</main>
    </div>
    <SiteFooter/>
  </div>
}

function LoginShell({children}){
  return <div className="app login-app">
    <div className="shell">
      <Topbar active="#login"/>
      <main className="login-stage">
        <AuroraField/>
        <BatikLayer opacity={.05}/>
        {children}
      </main>
    </div>
    <SiteFooter/>
  </div>
}

/* ==========================================================================
   Beranda
   --------------------------------------------------------------------------
   Halaman ini memakai kepala halaman sendiri (bukan <Shell>) karena perannya
   berbeda: bukan judul bagian, melainkan panggung identitas — logo besar,
   nama panjang, dan kalimat pendamping — dengan foto perbatasan sebagai latar.
   ========================================================================== */

/* Foto latar bersifat opsional. Bila berkasnya belum dipasang, gradasi laut
   dan motif kawung di belakangnya sudah berdiri sendiri, jadi tidak ada
   kotak gambar rusak yang terlihat pengguna. */
const HERO_PHOTO='/hero-beranda.jpg'

/* Pemilih tahun tinggal di kepala bagian "Indikator makro", bukan di hero.
   Ia mengendalikan angka, jadi tempatnya berdampingan dengan angka pertama
   yang dipengaruhinya — bukan di panggung identitas yang tidak memuat angka
   apa pun. Bentuknya kotak bersudut lengkung, sama seperti isian lain di
   halaman ini, supaya terbaca sebagai kendali dan bukan lencana. */
function YearPicker({data,year,onYearChange}){
  const years=data?.tahun_tersedia||[]
  /* Tanpa label "Tahun data" di sebelahnya. Isinya sudah berupa tahun, dan
     kicker "Outlook 2025" tepat di seberangnya sudah menyebut tahun yang
     sedang berlaku — labelnya hanya mengulang. */
  return <label className="year-picker" aria-label="Tahun data">
    <span className="year-picker-field">
      <select
        value={year||''}
        onChange={event=>onYearChange(event.target.value)}
        disabled={!years.length}
        aria-label="Pilih tahun data yang ditampilkan"
      >
        {years.length
          ?years.map(option=><option key={option} value={option}>{option}</option>)
          :<option value="">Memuat...</option>}
      </select>
      <ChevronDown size={16} aria-hidden="true"/>
    </span>
  </label>
}

function HomeHero({data}){
  const [photo,setPhoto]=useState(true)

  return <header className="home-hero">
    <div className="home-hero-media" aria-hidden="true">
      {photo&&<img src={HERO_PHOTO} alt="" onError={()=>setPhoto(false)}/>}
    </div>
    <div className="home-hero-veil" aria-hidden="true"/>
    <AuroraField/>
    <BatikLayer opacity={.08} drift/>

    <div className="home-hero-grid">
      <div className="home-hero-identity">
        <div className="home-hero-branding">
          <h1>SEBATIK</h1>
          <p className="home-hero-expand">Sistem Monitoring Berkelanjutan Capaian Indikator ISV-IUP Kalimantan Utara</p>
        </div>
      </div>

      <div className="home-hero-copy">
        <p>
          SEBATIK memantau ketersediaan dan capaian 86 indikator ISV-IUP Provinsi Kalimantan
          Utara dalam satu dasbor terpadu. Menghubungkan target RPJPD dengan realisasi tahunan
          menuju Indonesia Emas 2045.
        </p>
      </div>
    </div>
  </header>
}

/* Empat pintu masuk utama. Angka pada kartu diambil dari muatan beranda yang
   sama, jadi tidak ada permintaan tambahan ke backend. */
const HOME_DOORS=[
  ['#indikator','Indikator',Compass,'Telusuri seri realisasi, target, dan pertumbuhan tiap indikator.'],
  ['#capaian','Capaian',Target,'Ukur jarak setiap indikator menuju target Kalimantan Utara 2045.'],
  ['#insight','Insight',Sparkles,'Baca situasi indikator makro dan perbandingan antarwilayah.'],
  ['#validitas','Validitas',ShieldCheck,'Periksa status verifikasi, pembaruan, dan metadata indikator.']
]

/* Angka ringkasan di kaki kartu dilepas. Kartu ini pintu masuk, bukan papan
   angka — dan angka yang sama sudah muncul utuh di bagian-bagian di bawahnya.
   Panah naik ke baris judul supaya kartunya tinggal dua baris: nama fitur dan
   satu kalimat penjelas. */
function HomeDoors(){
  return <Reveal as="nav" className="home-doors" aria-label="Pintu masuk utama">
    {HOME_DOORS.map(([hash,label,Icon,desc],i)=>
      <a key={hash} href={hash} className="home-door" style={{'--tone':`var(--series-${(i%6)+1})`,'--i':i}}>
        <span className="home-door-band" aria-hidden="true"/>
        <span className="home-door-icon"><Icon size={20}/></span>
        <b>{label}</b>
        <ArrowUpRight className="home-door-go" size={16} aria-hidden="true"/>
        <small>{desc}</small>
      </a>
    )}
  </Reveal>
}

/* Rel kartu mendatar yang dipakai dua tempat: korsel indikator makro di
   beranda dan pemilih indikator di halaman Insight. Keduanya memuat kartu
   selebar satu per lima layar, bergeser satu halaman penuh, dan memutar di
   ujung — yang berbeda hanya isi kartunya dan apakah ia berjalan sendiri.

   `auto` sengaja tidak dinyalakan di halaman Insight: kartu di sana adalah
   kendali yang diklik, dan kartu yang bergerak sendiri akan kabur tepat saat
   hendak ditunjuk. Di beranda kartu hanya dibaca, jadi putarannya aman.

   Rel ini tetap bisa digeser tangan; begitu kursor masuk atau ada yang
   menerima fokus papan tik, putarannya berhenti supaya tidak menarik kartu
   pergi saat sedang dibaca. */
const MACRO_INTERVAL=3000

function CardRail({count,auto=false,className='',children}){
  const railRef=useRef(null)
  /* Nomor halaman disimpan dua kali: sebagai state untuk menggambar titik
     penanda, dan sebagai ref supaya pengatur waktu membaca nilai terkini tanpa
     harus dipasang ulang tiap kali halaman berganti. */
  const pageRef=useRef(0),strideRef=useRef({stride:0,perPage:1})
  const [pages,setPages]=useState(1),[page,setPage]=useState(0),[paused,setPaused]=useState(false)

  const land=index=>{pageRef.current=index;setPage(index)}

  /* Ukuran halaman dihitung dari kartunya, bukan dari `scrollWidth` dibagi
     lebar rel. Sebabnya: satu halaman selebar rel memuat lima kartu dan empat
     sela, sedangkan melompat lima kartu berarti bergerak sejauh lima kartu dan
     lima sela — selisih satu sela tiap halaman. Pada layar lebar selisih itu
     tertelan oleh scroll-snap, tetapi di layar sempit ia menumpuk sampai
     melahirkan satu halaman hantu di deretan titik penanda. */
  const metrics=()=>{
    const rail=railRef.current
    const first=rail?.firstElementChild
    if(!rail||!rail.clientWidth||!first||!count)return null
    const gap=parseFloat(getComputedStyle(rail).columnGap)||0
    const stride=first.getBoundingClientRect().width+gap
    if(!stride)return null
    const perPage=Math.max(1,Math.round((rail.clientWidth+gap)/stride))
    return {rail,stride,perPage,total:Math.max(1,Math.ceil(count/perPage))}
  }

  const measure=()=>{
    const m=metrics()
    if(!m)return
    strideRef.current={stride:m.stride,perPage:m.perPage}
    setPages(m.total)
    /* Halaman penutup selalu mentok di ujung rel, jadi posisinya lebih pendek
       daripada kelipatan lebar halaman. Ia ditandai lewat pemeriksaan ujung,
       bukan pembagian, supaya titiknya tidak tertinggal satu langkah. */
    const atEnd=m.rail.scrollLeft+m.rail.clientWidth>=m.rail.scrollWidth-4
    land(atEnd?m.total-1:Math.min(m.total-1,Math.round(m.rail.scrollLeft/(m.perPage*m.stride))))
  }

  /* Tiap perpindahan menuju posisi mutlak halaman tujuan, bukan "geser sejauh
     satu layar dari tempat sekarang". Bedanya terasa ketika satu penggeseran
     gagal berjalan — dengan posisi mutlak, langkah berikutnya kembali ke jalur
     yang benar; dengan penambahan relatif, selisihnya menumpuk. */
  const scrollToPage=(index,behavior)=>{
    const rail=railRef.current
    const {stride,perPage}=strideRef.current
    if(!rail||!stride)return
    land(index)
    rail.scrollTo({left:index*perPage*stride,behavior})
  }

  /* Lebar rel diamati langsung, bukan lebar jendela — ia juga berubah ketika
     bilah sisi atau papan tik di layar muncul. Peristiwa `resize` tetap
     didengarkan sebagai jaring pengaman bila pengamat ukuran tidak tersedia. */
  useEffect(()=>{
    const rail=railRef.current
    if(!rail)return
    measure()
    const observer=new ResizeObserver(measure)
    observer.observe(rail)
    addEventListener('resize',measure)
    return()=>{observer.disconnect();removeEventListener('resize',measure)}
  },[count])

  useEffect(()=>{
    if(!auto||paused||pages<2)return
    const still=matchMedia('(prefers-reduced-motion: reduce)').matches
    const timer=setInterval(()=>{
      scrollToPage(pageRef.current+1>=pages?0:pageRef.current+1,still?'auto':'smooth')
    },MACRO_INTERVAL)
    return()=>clearInterval(timer)
  },[auto,paused,pages])

  const goto=index=>scrollToPage(index,'smooth')

  /* Tombol panah memutar seperti putaran otomatisnya: dari halaman terakhir
     "berikutnya" kembali ke awal, dan sebaliknya. Tidak ada tombol yang mati
     supaya kendalinya tidak pernah terasa buntu di ujung. */
  const step=arah=>goto((page+arah+pages)%pages)

  return <div
    className={`macro-rail ${className}`.trim()}
    onMouseEnter={()=>setPaused(true)}
    onMouseLeave={()=>setPaused(false)}
    onFocusCapture={()=>setPaused(true)}
    onBlurCapture={()=>setPaused(false)}
  >
    {/* Lapisan ini hanya membungkus rel kartunya, tanpa titik penanda di
        bawahnya, supaya kedua panah bisa duduk tepat di tengah tinggi kartu. */}
    <div className="macro-viewport">
      {pages>1&&<button
        type="button"
        className="macro-nav is-prev"
        onClick={()=>step(-1)}
        aria-label="Indikator sebelumnya"
      ><ChevronLeft size={20}/></button>}

      <div className="macro-track" ref={railRef} onScroll={measure}>{children}</div>

      {pages>1&&<button
        type="button"
        className="macro-nav is-next"
        onClick={()=>step(1)}
        aria-label="Indikator berikutnya"
      ><ChevronRight size={20}/></button>}
    </div>

    {pages>1&&<div className="macro-dots" role="tablist" aria-label="Halaman indikator makro">
      {Array.from({length:pages},(_,i)=>
        <button
          key={i}
          role="tab"
          className={i===page?'is-active':''}
          aria-selected={i===page}
          aria-label={`Halaman ${i+1} dari ${pages}`}
          onClick={()=>goto(i)}
        />
      )}
    </div>}
  </div>
}

function MacroCards({items,loading}){
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

function HomePage(){
  const [year,setYear]=useState(''),[data,setData]=useState(null),[error,setError]=useState('')
  /* Beranda memakai kerangkanya sendiri, bukan <Shell>, jadi judul tabnya
     dipasang di sini — tanpa ini ia mewarisi judul halaman sebelumnya. */
  usePageTitle('Beranda')

  useEffect(()=>{
    api('/api/v1/beranda'+(year?`?tahun=${year}`:''))
      .then(x=>{setData(x);if(!year)setYear(String(x.tahun))})
      .catch(e=>setError(e.message))
  },[year])

  const groups=(data?.sasaran_visi||[]).reduce((acc,x)=>{(acc[x.arah_pembangunan]??=[]).push(x);return acc},{})

  return <div className="app home-app">
    <div className="shell">
      <Topbar active="#beranda"/>
      <HomeHero data={data}/>
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

const regionKey=name=>String(name||'')
  .replace(/^Kota\s+/i,'').replace(/^Kabupaten\s+/i,'').trim().toLowerCase()

function geoPaths(geo,width=560,height=390){
  const points=[]
  const collect=x=>Array.isArray(x?.[0])?x.forEach(collect):points.push(x)
  geo.features.forEach(f=>collect(f.geometry.coordinates))
  const xs=points.map(p=>p[0]),ys=points.map(p=>p[1])
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),pad=18
  const scale=Math.min((width-pad*2)/(maxX-minX),(height-pad*2)/(maxY-minY))
  const offX=(width-(maxX-minX)*scale)/2,offY=(height-(maxY-minY)*scale)/2
  const project=p=>[offX+(p[0]-minX)*scale,offY+(maxY-p[1])*scale]
  const ringPath=ring=>ring.map((p,i)=>{const [x,y]=project(p);return `${i?'L':'M'}${x.toFixed(1)},${y.toFixed(1)}`}).join('')+'Z'
  return geo.features.map(f=>{
    const polys=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates
    return {
      name:f.properties.wadmkk||f.properties.namobj,
      code:String(f.properties.kdpkab||'').replace('.',''),
      d:polys.flatMap(p=>p).map(ringPath).join('')
    }
  })
}

function KaltaraMap({regions,selected,onSelect,unit}){
  const [paths,setPaths]=useState([])
  useEffect(()=>{fetch('/kaltara-kabkota.geojson').then(r=>r.json()).then(x=>setPaths(geoPaths(x)))},[])
  const byCode=Object.fromEntries((regions||[]).map(x=>[x.kode,x]))

  return <div className="kaltara-map">
    <svg viewBox="0 0 560 390" role="img" aria-label="Peta kabupaten dan kota Kalimantan Utara">
      {paths.map(x=>{
        const item=byCode[x.code]||(regions||[]).find(r=>regionKey(r.nama)===regionKey(x.name))
        const active=selected===item?.kode
        return <path
          key={x.code||x.name}
          d={x.d}
          className={active?'active':''}
          data-status={item?.status||'BELUM_ADA_DATA'}
          tabIndex={item?0:-1}
          role={item?'button':undefined}
          aria-label={item?`${item.nama}: ${valueLabel(item.nilai,item.nilai_teks,unit)}`:undefined}
          onClick={()=>item&&onSelect(item.kode)}
          onKeyDown={e=>{if(item&&(e.key==='Enter'||e.key===' ')){e.preventDefault();onSelect(item.kode)}}}
        >
          <title>{item?.nama||x.name}: {valueLabel(item?.nilai,item?.nilai_teks,unit)}</title>
        </path>
      })}
    </svg>
    <div className="map-legend">
      <span><i className="has"/>Tersedia</span>
      <span><i/>Belum ada data</span>
    </div>
  </div>
}

/* ==========================================================================
   Penjelajah indikator
   ========================================================================== */

function IndicatorExplorerPage(){
  const [groups,setGroups]=useState([]),[group,setGroup]=useState(''),[indicator,setIndicator]=useState(''),
    [detail,setDetail]=useState(null),[year,setYear]=useState(''),[region,setRegion]=useState(''),[error,setError]=useState('')
  const [theme]=useTheme()
  const ct=chartTheme(theme)

  useEffect(()=>{
    api('/api/v1/indikator-explorer').then(x=>{
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
    if(indicator)api(`/api/v1/indikator-explorer/${indicator}${year?`?tahun=${year}`:''}`).then(x=>{
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
    active="#indikator"
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

function CapaianPage(){
  const [config,setConfig]=useState({indikator:[],kelompok:[],wilayah:[]}),[id,setId]=useState(''),
    [group,setGroup]=useState(''),[year,setYear]=useState(''),[region,setRegion]=useState('65'),
    [detail,setDetail]=useState(null),[search,setSearch]=useState(''),[error,setError]=useState('')
  const [theme]=useTheme()
  const ct=chartTheme(theme)

  useEffect(()=>{
    api('/api/v1/capaian-explorer').then(x=>{
      setConfig(x)
      if(x.indikator.length)setId(x.indikator[0].id_indikator)
    }).catch(e=>setError(e.message))
  },[])

  useEffect(()=>{
    let cancelled=false
    if(id)api(`/api/v1/capaian-explorer/${id}?${qs({tahun:year,wilayah_kode:region})}`).then(x=>{
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
    active="#capaian"
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

function DetailPage({id}){
  const [item,setItem]=useState(null)
  const [theme]=useTheme()
  const ct=chartTheme(theme)

  useEffect(()=>{api(`/api/v1/indikator/${id}/detail`).then(setItem)},[id])

  if(!item)return <Shell active="#capaian" title="Detail Indikator" subtitle="Memuat rincian indikator...">
    <div className="panel"><ChartSkeleton height={300}/></div>
  </Shell>

  const years=[...new Set(item.nilai.map(x=>x.tahun))].sort()
  const chart=years.map(t=>({
    tahun:t,
    realisasi:item.nilai.find(x=>x.tahun===t&&x.jenis==='realisasi')?.nilai,
    target:item.nilai.find(x=>x.tahun===t&&x.jenis==='target')?.nilai
  }))

  return <Shell
    active="#capaian"
    title="Detail Indikator"
    subtitle={`${item.id_indikator} · ${item.nama_indikator}`}
  >
    <a href="#capaian" className="back"><ArrowLeft size={15}/> Kembali ke daftar</a>

    <Reveal as="section" className="panel detail-head">
      <div>
        <span className={`category ${item.kategori.toLowerCase()}`}>{item.kategori}</span>
        <h2>{item.nama_indikator}</h2>
        <p>{item.kelompok} · Arah baik {item.arah_baik}</p>
      </div>
      <CapaianBadge status={item.status_capaian}/>
    </Reveal>

    <Panel delay={60} kicker="Seri waktu" title="Realisasi dan target">
      <ResponsiveContainer width="100%" height={340}>
        {/* Perlakuan sama dengan grafik utama di penjelajah indikator: capaian
            berisi, acuan tipis, tidak ada garis putus-putus. */}
        <ComposedChart data={chart} margin={{top:12,right:20,left:0,bottom:4}}>
          <defs>
            <linearGradient id="grad-detail" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={seriesColor(0,theme)} stopOpacity={.26}/>
              <stop offset="100%" stopColor={seriesColor(0,theme)} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid stroke={ct.grid} vertical={false}/>
          <XAxis dataKey="tahun" tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
          <YAxis tick={{fontSize:11.5,fill:ct.axis}} axisLine={false} tickLine={false}/>
          <Tooltip cursor={{stroke:ct.baseline,strokeWidth:1}} content={<TooltipCard formatter={v=>valueLabel(v,null,item.satuan)}/>}/>
          <Line dataKey="target" name="Target" type="monotone" stroke={seriesColor(2,theme)}
            strokeWidth={1.75} dot={{r:2.5,fill:ct.surface,stroke:seriesColor(2,theme),strokeWidth:1.75}}
            activeDot={{r:5,strokeWidth:2,stroke:ct.surface}} animationDuration={ct.motion}/>
          <Area dataKey="realisasi" name="Realisasi" type="monotone" stroke={seriesColor(0,theme)} strokeWidth={2.75}
            fill="url(#grad-detail)"
            dot={{r:3.5,fill:ct.surface,stroke:seriesColor(0,theme),strokeWidth:2}}
            activeDot={{r:6,strokeWidth:2.5,stroke:ct.surface}} animationDuration={ct.motion}/>
        </ComposedChart>
      </ResponsiveContainer>
      <VizLegend items={[
        {label:'Realisasi',color:seriesColor(0,theme),shape:'line'},
        {label:'Target',color:seriesColor(2,theme),shape:'line'}
      ]}/>
    </Panel>

    <div className="detail-columns">
      <Panel delay={40} kicker="Dokumentasi" title="Metadata indikator">
        {[
          ['Definisi',item.metadata?.definisi],
          ['Rumus perhitungan',item.metadata?.rumus_mentah],
          ['Interpretasi',item.metadata?.interpretasi],
          ['Sumber data',item.metadata?.sumber_data],
          ['Frekuensi',item.metadata?.frekuensi]
        ].map(([k,v])=><details key={k}><summary>{k}</summary><p>{v||'Belum tersedia'}</p></details>)}
      </Panel>

      <Panel delay={80} className="governance" kicker="Tanggung jawab" title="Tata kelola">
        <dl>
          <dt>Penghasil</dt><dd>{item.penghasil||'-'}</dd>
          <dt>K/L pengampu</dt><dd>{item.kl_pengampu||'-'}</dd>
          <dt>OPD penanggung jawab</dt><dd>{item.opd_penanggung_jawab||'-'}</dd>
          <dt>Tim PJK</dt><dd>{item.tim_pjk||'-'}</dd>
        </dl>
        {[
          ['Metadata',item.link_metadata],
          ['Publikasi',item.link_publikasi],
          ['Data mentah',item.link_data]
        ].filter(x=>x[1]).map(x=>
          <a key={x[0]} href={x[1]} target="_blank" rel="noreferrer">{x[0]} (tautan luar)</a>
        )}
      </Panel>
    </div>

    <Panel
      delay={40}
      kicker="Rincian angka"
      title="Tabel nilai"
      actions={<a className="button-link" href={`/api/v1/indikator/${id}/unduh.csv`}><Download size={15}/> Unduh indikator</a>}
    >
      <div className="table-scroll">
        <table className="value-table">
          <thead><tr><th>Tahun</th><th>Jenis</th><th>Nilai</th><th>Sumber</th></tr></thead>
          <tbody>
            {item.nilai.map((x,i)=>
              <tr key={i}>
                <td className="mono">{x.tahun}</td>
                <td>{x.jenis}</td>
                <td className="mono">{x.nilai??'Belum Tersedia'}</td>
                <td>{x.sumber_sheet}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  </Shell>
}

/* ==========================================================================
   Insight makro
   ========================================================================== */

function InsightPage(){
  const [data,setData]=useState(null),[indicator,setIndicator]=useState(''),[region,setRegion]=useState('65'),
    [mapRegion,setMapRegion]=useState(''),[error,setError]=useState('')
  const [theme]=useTheme()
  const ct=chartTheme(theme)

  useEffect(()=>{
    let cancelled=false
    api('/api/v1/insight?'+qs({indikator_id:indicator,wilayah_kode:region})).then(x=>{
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
    active="#insight"
    title="Insight"
    subtitle="Situasi indikator makro Kalimantan Utara berdasarkan tahun berjalan atau data terverifikasi terakhir yang tersedia."
  >
    {error&&<div className="error"><AlertTriangle size={18}/>{error}</div>}

    <Reveal as="section" className="insight-toolbar">
      <div>
        <span className="kicker">Indikator makro pembangunan</span>
        <h2>Pilih kartu untuk melihat tren dan perbandingan wilayah</h2>
      </div>
      {/* Tanpa label "Wilayah" di sampingnya: isian ini sudah berisi nama
          wilayah, jadi labelnya hanya mengulang sambil mendorong kotaknya
          menjauh dari tepi kanan. Nama tetap ada untuk pembaca layar. */}
      <label className="year-picker" aria-label="Wilayah">
        <span className="year-picker-field">
          <select value={region} onChange={e=>{setRegion(e.target.value);setIndicator('')}}>
            {(data?.wilayah_opsi||[]).map(x=><option value={x.kode} key={x.kode}>{x.nama}</option>)}
          </select>
          <ChevronDown size={16} aria-hidden="true"/>
        </span>
      </label>
    </Reveal>

    {/* Kartu pemilih memakai rel yang sama dengan korsel beranda, tetapi tanpa
        putaran otomatis — lihat catatan di CardRail. Isi kartu dan aksinya
        tidak berubah: satu klik tetap memuat tren dan perbandingan wilayah
        untuk indikator itu. */}
    <Reveal as="div" delay={60}>
      <CardRail count={data?.indikator_makro?.length||0} className="macro-selector">
        {(data?.indikator_makro||[]).map((x,i)=>
          <button
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
            <strong className={valueTone(x.nilai).trim()}>{valueLabel(x.nilai,x.nilai_teks,x.satuan)}</strong>
            <b>{x.nama_indikator}</b>
            <small className={growthTone(x.perubahan)}>
              {x.perubahan===null
                ?'Perbandingan belum tersedia'
                :`${x.perubahan>0?'↑':x.perubahan<0?'↓':'—'} ${valueLabel(Math.abs(x.perubahan),null,x.satuan)} dari tahun sebelumnya`}
            </small>
          </button>
        )}
      </CardRail>
    </Reveal>

    {data?.indikator_aktif&&
      <Panel
        delay={60}
        className="insight-analysis"
        kicker={`${data.indikator_aktif.kode_indikator} · ${data.indikator_aktif.tahun||'Belum ada data'}`}
        title={data.indikator_aktif.nama_indikator}
        desc={`Sumber: ${data.indikator_aktif.sumber_data||'Belum dicatat'} · Pengampu: ${data.indikator_aktif.opd_pengampu||'Belum ditetapkan'}`}
      >
        <div className="insight-layout">
          <div className="macro-trend">
            <h3>Tren Provinsi Kalimantan Utara</h3>
            {data.series.length?<>
              <div className="series-cards">
                {data.series.map(x=>
                  <div className={x.tahun===data.indikator_aktif.tahun?'selected':''} key={x.tahun}>
                    <span>{x.tahun}</span>
                    <b>{valueLabel(x.nilai,null,data.indikator_aktif.satuan)}</b>
                    <small className={growthTone(x.growth)}>
                      {x.growth===null?'—':`${x.growth>0?'↑':x.growth<0?'↓':'—'} ${Math.abs(x.growth)}%`}
                    </small>
                  </div>
                )}
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

const dateText=value=>{
  if(!value)return '—'
  const parsed=new Date(value.includes('T')?value:value.replace(' ','T')+'Z')
  return Number.isNaN(parsed.getTime())?value:parsed.toLocaleDateString('id-ID',{day:'2-digit',month:'long',year:'numeric'})
}

function MetadataModal({item,onClose}){
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

function ValidityPage(){
  const [data,setData]=useState(null),[region,setRegion]=useState('65'),[query,setQuery]=useState(''),[error,setError]=useState(''),[metadata,setMetadata]=useState(null)
  /* Dibaca dari sumber bersama, bukan langsung dari localStorage: saat pengguna
     menekan Keluar di bilah atas, tabel ini ikut dimuat ulang sebagai tamu. */
  const token=useToken()

  useEffect(()=>{
    let cancelled=false
    const timer=setTimeout(async()=>{
      try{
        const path='/api/v1/validitas?'+qs({wilayah_kode:region,q:query})
        let response=await fetch(path,{headers:token?{Authorization:`Bearer ${token}`}:{}})
        if(response.status===401&&token){clearToken();response=await fetch(path)}
        if(!response.ok)throw new Error(`API gagal (${response.status})`)
        const result=await response.json()
        if(!cancelled){setData(result);setError('')}
      }catch(e){if(!cancelled)setError(e.message)}
    },180)
    return()=>{cancelled=true;clearTimeout(timer)}
  },[region,query,token])

  const viewMetadata=async row=>{
    try{setMetadata({id_indikator:row.id_indikator,nama_indikator:row.nama_indikator,loading:true});setMetadata(await api(`/api/v1/beranda-indikator/${row.id_indikator}/metadata`))}
    catch(e){setMetadata(null);setError(`Metadata tidak dapat dimuat: ${e.message}`)}
  }

  return <Shell
    active="#validitas"
    title="Validitas"
    subtitle="Status verifikasi, pembaruan, dan metadata setiap indikator menurut wilayah."
  >
    {error&&<div className="error"><AlertTriangle size={18}/>{error}</div>}

    <Reveal as="section" className="panel validity-panel">
      <div className="validity-toolbar">
        <label className="field">
          <span>Wilayah</span>
          <select value={region} onChange={e=>setRegion(e.target.value)}>
            {(data?.wilayah_opsi||[]).map(x=><option value={x.kode} key={x.kode}>{x.nama}</option>)}
          </select>
        </label>
        <label className="search">
          <Search size={17}/>
          <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Cari nama atau kode indikator..." aria-label="Cari indikator"/>
        </label>
      </div>

      <div className="table-scroll">
        <table className="validity-table">
          <thead>
            <tr>
              <th>Nama indikator</th><th>Instansi pengampu</th><th>Validasi</th><th>Update</th>
              <th>Status indikator</th><th>Metadata</th>
            </tr>
          </thead>
          <tbody>
            {(data?.data||[]).map(x=>
              <tr key={x.id_indikator}>
                <td><b>{x.nama_indikator}</b><small>{x.id_indikator}</small></td>
                <td>{x.instansi_pengampu}</td>
                <td>
                  <span className={`validation-state ${x.terverifikasi_pada?'verified':'waiting'}`}>
                    <i/>
                    {x.terverifikasi_pada
                      ?<span>Terverifikasi<small>{dateText(x.terverifikasi_pada)}</small></span>
                      :<span>Belum diverifikasi<small>Menunggu data wilayah</small></span>}
                  </span>
                </td>
                <td>
                  <span className="update-cell">
                    {x.terverifikasi_pada
                      ?<>Terakhir diperbarui {dateText(x.terverifikasi_pada)}<small>oleh {x.update_oleh}</small></>
                      :'Belum ada pembaruan'}
                  </span>
                </td>
                <td>
                  <span className={`indicator-state ${x.status_indikator.toLowerCase().replaceAll(' ','-')}`}>
                    {x.status_indikator}
                  </span>
                </td>
                <td>
                  <button className="metadata-eye" onClick={()=>viewMetadata(x)} title={x.metadata_tersedia?'Lihat metadata dan tabel nilai':'Metadata belum tersedia'} aria-label={`Lihat metadata ${x.nama_indikator}`}>
                    <Eye size={17}/>
                  </button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
        {data&&!data.data?.length&&
          <EmptyState icon={Search} compact title="Tidak ada indikator yang cocok" desc="Ubah kata kunci atau pilih wilayah lain."/>}
      </div>
    </Reveal>
    {metadata?.loading&&<div className="metadata-modal-backdrop"><div className="metadata-loading"><ChartSkeleton height={180}/></div></div>}
    {metadata&&!metadata.loading&&<MetadataModal item={metadata} onClose={()=>setMetadata(null)}/>}
  </Shell>
}

/* ==========================================================================
   Dasbor analitik
   ========================================================================== */

function AnalyticsPage(){
  const [cards,setCards]=useState([]),[id,setId]=useState('ISV-01'),[gap,setGap]=useState(null),
    [change,setChange]=useState(null),[rank,setRank]=useState(null),[x,setX]=useState('ISV-04'),
    [y,setY]=useState('ISV-05'),[corr,setCorr]=useState(null)
  const [theme]=useTheme()
  const ct=chartTheme(theme)

  useEffect(()=>{
    api('/api/v1/capaian').then(r=>setCards(r.data))
    api('/api/v1/analitik/peringkat').then(setRank)
  },[])
  useEffect(()=>{
    api(`/api/v1/analitik/gap/${id}`).then(setGap)
    api(`/api/v1/analitik/selisih/${id}`).then(setChange)
  },[id])
  useEffect(()=>{api(`/api/v1/analitik/korelasi?x=${x}&y=${y}`).then(setCorr)},[x,y])

  const opts=cards.map(i=><option key={i.id_indikator} value={i.id_indikator}>{i.id_indikator} · {i.nama_indikator}</option>)
  const upColor=capaianColor('TERCAPAI',theme),downColor=capaianColor('PERLU_PERHATIAN',theme)

  return <Shell
    active="#analitik"
    title="Dasbor Analitik"
    subtitle="Tren, gap target, perbandingan antar-indikator, dan korelasi."
  >
    <div className="notice warning">
      <AlertTriangle size={17}/> Required run-rate adalah ekstrapolasi linear sederhana, bukan proyeksi resmi.
    </div>

    <Panel
      kicker="Tren tahunan"
      title="Tren dan selisih tahunan"
      desc="Warna menunjukkan perbaikan sesuai arah indikator."
      actions={<select className="select" value={id} onChange={e=>setId(e.target.value)} aria-label="Pilih indikator">{opts}</select>}
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
          <select className="select" value={x} onChange={e=>setX(e.target.value)} aria-label="Indikator sumbu X">{opts}</select>
          <select className="select" value={y} onChange={e=>setY(e.target.value)} aria-label="Indikator sumbu Y">{opts}</select>
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

function SubmissionTable({rows,canDecide=false,onEvidence,onDecision,onCorrect}){
  return <div className="table-scroll">
    <table className="workspace-table">
      <thead>
        <tr>
          <th>Indikator</th><th>Wilayah / pengusul</th><th>Realisasi</th><th>Bukti</th><th>Status</th><th>Keputusan / aksi</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(row=>
          <tr key={row.id}>
            <td><b>{row.id_indikator}</b><small>Usulan #{row.id} · {dateText(row.dibuat_pada)}</small></td>
            <td>{row.wilayah}<small>{row.pengusul}</small></td>
            <td><b>{fmt.format(row.nilai)}</b><small>{row.tahun} · {row.sumber}</small></td>
            <td>
              <button className="evidence-button" onClick={()=>onEvidence(row)}>
                <Eye size={14}/>{row.jumlah_bukti} file
              </button>
            </td>
            <td>
              <span className={`submission-status ${row.status.toLowerCase()}`}>{row.status.replaceAll('_',' ')}</span>
              {row.alasan_verifikasi&&<small>Alasan: {row.alasan_verifikasi}</small>}
            </td>
            <td>
              {canDecide&&row.status==='MENUNGGU_VERIFIKASI'
                ?<div className="row-actions">
                  <button className="approve" onClick={()=>onDecision(row,'DISETUJUI')}>Setujui</button>
                  <button className="reject" onClick={()=>onDecision(row,'DITOLAK')}>Tolak</button>
                </div>
                :onCorrect&&row.status!=='MENUNGGU_VERIFIKASI'
                  ?<button onClick={()=>onCorrect(row)}>Ajukan koreksi</button>
                  :<small>{row.verifikator?`Oleh ${row.verifikator}`:'Menunggu verifikator'}</small>}
            </td>
          </tr>
        )}
      </tbody>
    </table>
    {!rows.length&&<EmptyState icon={ListChecks} compact title="Belum ada usulan" desc="Usulan yang dikirim operator akan tampil di sini."/>}
  </div>
}

/* Bagan alur operator. Mengalir ke bawah, bukan ke samping, karena ia menempati
   kolom sempit di sebelah borang — dan karena membaca langkah dari atas ke
   bawah lebih dekat dengan cara orang membaca daftar tugas.

   Lima langkah berurutan, lalu bercabang dua di ujungnya. Cabang "Ditolak"
   ditutup catatan yang menunjuk balik ke langkah 02, sebab di situlah koreksi
   dimulai — itu satu-satunya bagian alur yang tidak berjalan lurus, jadi ia
   ditandai terpisah dan tidak dibiarkan tersirat. */
const OPERATOR_STEPS=[
  ['Pilih indikator','Tentukan indikator dan tahun data.'],
  ['Isi realisasi','Masukkan nilai dan sumber datanya.'],
  ['Lampirkan bukti','Unggah dokumen pendukung.'],
  ['Kirim','Kirim ke verifikator, lalu pantau status.'],
  ['Verifikasi','Verifikator menilai isian dan bukti.']
]

function OperatorFlow(){
  return <ol className="flow">
    {OPERATOR_STEPS.map(([title,desc],i)=>
      <li className={`flow-step${i===OPERATOR_STEPS.length-1?' is-last':''}`} key={title}>
        <span className="flow-no">{String(i+1).padStart(2,'0')}</span>
        <b>{title}</b>
        <small>{desc}</small>
      </li>
    )}

    <li className="flow-fork">
      <div className="flow-outcome is-rejected">
        <b>Ditolak</b>
        <small>Catatan verifikator terbit.</small>
      </div>
      <div className="flow-outcome is-approved">
        <b>Disetujui</b>
        <small>Data terkunci, tampil di dasbor.</small>
      </div>
    </li>

    <li className="flow-loop">
      <ArrowLeft size={14} aria-hidden="true"/>
      <span>Jika ditolak, ajukan koreksi baru mulai dari langkah <b>02</b>.</span>
    </li>
  </ol>
}

function PasswordResetModal({user,onClose,onSubmit}){
  const [value,setValue]=useState(''),[visible,setVisible]=useState(false),[saving,setSaving]=useState(false)
  const valid=value.length>=12

  useEffect(()=>{
    const close=event=>event.key==='Escape'&&!saving&&onClose()
    addEventListener('keydown',close)
    return()=>removeEventListener('keydown',close)
  },[onClose,saving])

  const submit=async event=>{
    event.preventDefault()
    if(!valid)return
    setSaving(true)
    try{await onSubmit(value)}finally{setSaving(false)}
  }

  return <div className="password-modal-backdrop" onMouseDown={event=>event.target===event.currentTarget&&!saving&&onClose()}>
    <form className="password-modal" role="dialog" aria-modal="true" aria-labelledby="password-modal-title" onSubmit={submit}>
      <header>
        <span className="password-modal-icon"><KeyRound size={21}/></span>
        <div>
          <small>Keamanan akun</small>
          <h2 id="password-modal-title">Atur ulang kata sandi</h2>
          <p>Buat kata sandi awal baru untuk <b>{user.nama}</b> ({user.username}). Pengguna wajib menggantinya saat login.</p>
        </div>
        <button type="button" className="password-modal-close" onClick={onClose} disabled={saving} aria-label="Tutup"><X size={19}/></button>
      </header>
      <label className="password-modal-field">
        <span>Kata sandi baru</span>
        <span className="password-modal-secret">
          <input autoFocus type={visible?'text':'password'} value={value} onChange={event=>setValue(event.target.value)} minLength={12} autoComplete="new-password" placeholder="Minimal 12 karakter" required/>
          <button type="button" onClick={()=>setVisible(current=>!current)} aria-label={visible?'Sembunyikan kata sandi':'Tampilkan kata sandi'}>{visible?<EyeOff size={18}/>:<Eye size={18}/>}</button>
        </span>
      </label>
      <div className={`password-rule ${valid?'is-valid':''}`}><CheckCircle2 size={15}/><span>{valid?'Kata sandi memenuhi syarat':`${value.length}/12 karakter minimum`}</span></div>
      <footer>
        <button type="button" className="password-cancel" onClick={onClose} disabled={saving}>Batal</button>
        <button type="submit" className="password-save" disabled={!valid||saving}>{saving?'Menyimpan...':'Simpan kata sandi'}</button>
      </footer>
    </form>
  </div>
}

function AdminPage(){
  const token=useToken()
  const [me,setMe]=useState(null),
    [regions,setRegions]=useState([]),[catalog,setCatalog]=useState([]),[users,setUsers]=useState([]),
    [submissions,setSubmissions]=useState([]),[logs,setLogs]=useState([]),[message,setMessage]=useState(''),
    [evidence,setEvidence]=useState(null),[accountRole,setAccountRole]=useState('OPERATOR'),
    [messageTone,setMessageTone]=useState('warning'),[showPassword,setShowPassword]=useState(false),[passwordUser,setPasswordUser]=useState(null),
    [draft,setDraft]=useState({id_indikator:'',tahun:new Date().getFullYear(),periode:'',nilai:'',sumber:'',catatan:''})

  /* Pesan ruang kerja punya dua nada. `warning` untuk yang perlu dibaca ulang —
     kegagalan, sesi habis, berkas tidak terbuka. `success` untuk tindakan yang
     benar-benar selesai, ditandai centang hijau supaya operator tahu kirimannya
     sudah masuk tanpa harus membaca kalimatnya. */
  const notify=(text,tone='warning')=>{setMessage(text);setMessageTone(tone)}
  const notifyOk=text=>notify(text,'success')

  /* Dipanggil di sini, sebelum cabang-cabang keluar di bawah, supaya urutan
     hook tetap sama pada tiap render — halaman ini punya tiga keadaan (belum
     masuk, memeriksa sesi, ruang kerja) dan ketiganya keluar lebih awal. */
  usePageTitle(token?`Login ${roleLabel(me?.peran)}`:'Login')

  const authFetch=async(path,options={})=>{
    const response=await fetch(path,{...options,headers:{...(options.headers||{}),Authorization:`Bearer ${token}`}})
    if(response.status===401){
      clearToken();setMe(null)
      throw new Error('Sesi berakhir. Silakan login kembali.')
    }
    if(!response.ok)throw new Error(await response.text())
    return response.json()
  }

  const refresh=async(activeToken=token)=>{
    if(!activeToken)return
    const headers={Authorization:`Bearer ${activeToken}`}
    try{
      const profileResponse=await fetch('/api/v1/auth/saya',{headers})
      if(!profileResponse.ok)throw new Error(`AUTH_${profileResponse.status}`)
      const profile=await profileResponse.json()
      const [regionData,catalogData]=await Promise.all([api('/api/v1/wilayah'),api('/api/v1/capaian-explorer')])
      setMe(profile);setRegions(regionData.data);setCatalog(catalogData.indikator)
      const queueResponse=await fetch('/api/v1/admin/usulan',{headers})
      if(!queueResponse.ok)throw new Error(`QUEUE_${queueResponse.status}`)
      const queue=await queueResponse.json()
      setSubmissions(queue.data||[])
      if(profile.peran==='ADMIN'){
        const [accountResponse,logResponse]=await Promise.all([
          fetch('/api/v1/admin/pengguna',{headers}),
          fetch('/api/v1/admin/log',{headers})
        ])
        if(!accountResponse.ok||!logResponse.ok)throw new Error('ADMIN_DATA')
        const accountData=await accountResponse.json(),logData=await logResponse.json()
        setUsers(accountData.data);setLogs(logData.data)
      }
    }catch(error){
      notify('Sesi berakhir. Silakan login kembali.')
      clearToken();setMe(null)
    }
  }

  /* Keluar kini bisa dipicu dari bilah atas, jadi halaman ini harus ikut
     membersihkan dirinya saat token hilang — bukan hanya saat tombol di
     dalamnya yang ditekan. */
  useEffect(()=>{
    if(token)refresh()
    else{setMe(null);setSubmissions([]);setUsers([]);setLogs([]);setEvidence(null)}
  },[token])

  const login=async event=>{
    event.preventDefault()
    const form=new FormData(event.currentTarget)
    const response=await fetch('/api/v1/auth/login',{
      method:'POST',
      headers:{'Content-Type':'application/x-www-form-urlencoded'},
      body:new URLSearchParams({username:form.get('username'),password:form.get('password')})
    })
    const result=await response.json()
    if(!response.ok){notify(result.detail||'Login gagal');return}
    setToken(result.access_token)
    notifyOk('Login berhasil.')
  }

  const loadEvidence=async submission=>{
    try{
      const result=await authFetch(`/api/v1/admin/usulan/${submission.id}/bukti`)
      setEvidence({submission,files:result.data})
    }catch(error){notify(error.message)}
  }

  const openEvidence=async file=>{
    const response=await fetch(`/api/v1/admin/usulan/${evidence.submission.id}/bukti/${file.id}`,{headers:{Authorization:`Bearer ${token}`}})
    if(!response.ok){notify('File bukti tidak dapat dibuka.');return}
    const url=URL.createObjectURL(await response.blob())
    window.open(url,'_blank','noopener,noreferrer')
    setTimeout(()=>URL.revokeObjectURL(url),60000)
  }

  const decide=async(submission,decision)=>{
    let reason=null
    if(decision==='DITOLAK'){reason=prompt('Tuliskan alasan penolakan');if(!reason)return}
    const body=new FormData()
    body.set('keputusan',decision)
    if(reason)body.set('alasan',reason)
    try{
      const result=await authFetch(`/api/v1/admin/usulan/${submission.id}/verifikasi`,{method:'POST',body})
      notifyOk(`Usulan ${result.status.toLowerCase()}.`)
      refresh()
    }catch(error){notify(error.message)}
  }

  if(!token)return <LoginShell>
    <form className="panel role-login" onSubmit={login}>
      <div className="login-head">
        <img className="login-logo" src="/logo-sebatik-monitoring.png" alt="Logo SEBATIK"/>
        <h1>Masuk ke SEBATIK</h1>
        <p>Dasbor Pemantauan Ketersediaan Data ISV-IUP</p>
        <p className="login-org">BPS Provinsi Kalimantan Utara</p>
      </div>

      {message&&<p className="form-error" role="alert">{message}</p>}

      <label className="login-field">
        <span>Nama Pengguna</span>
        <input name="username" autoComplete="username" placeholder="Nama pengguna terdaftar" required autoFocus/>
      </label>

      <label className="login-field">
        <span>Kata Sandi</span>
        {/* Tombol mata duduk di dalam bingkai isian, bukan di sebelahnya, supaya
            lebar kolomnya tetap sama dengan isian di atasnya. */}
        <span className="login-secret">
          <input
            name="password"
            type={showPassword?'text':'password'}
            autoComplete="current-password"
            placeholder="Kata sandi"
            required
          />
          <button
            type="button"
            className="login-peek"
            onClick={()=>setShowPassword(v=>!v)}
            title={showPassword?'Sembunyikan kata sandi':'Tampilkan kata sandi'}
            aria-label={showPassword?'Sembunyikan kata sandi':'Tampilkan kata sandi'}
            aria-pressed={showPassword}
          >
            {showPassword?<EyeOff size={18}/>:<Eye size={18}/>}
          </button>
        </span>
      </label>

      <button className="login-submit">Masuk</button>

      <div className="login-foot">
        <p>Akses terbatas untuk admin dan walidata.</p>
        <p>Belum punya akun? Hubungi Tim Nerwilis BPS Kaltara.</p>
      </div>
    </form>
  </LoginShell>

  if(!me)return <LoginShell>
    <div className="panel role-login session-loading">
      <b>Memeriksa sesi login</b>
      <span>Mohon tunggu sebentar...</span>
    </div>
  </LoginShell>


  const submitValue=async event=>{
    event.preventDefault()
    try{
      const result=await authFetch('/api/v1/admin/usulan',{method:'POST',body:new FormData(event.currentTarget)})
      notifyOk(`Usulan #${result.id} dikirim untuk verifikasi.`)
      setDraft({id_indikator:'',tahun:new Date().getFullYear(),periode:'',nilai:'',sumber:'',catatan:''})
      event.currentTarget.reset()
      refresh()
    }catch(error){notify(error.message)}
  }

  const createAccount=async event=>{
    event.preventDefault()
    try{
      const result=await authFetch('/api/v1/admin/pengguna',{method:'POST',body:new FormData(event.currentTarget)})
      notifyOk(`Akun ${result.username} dibuat.`)
      event.currentTarget.reset()
      refresh()
    }catch(error){notify(error.message)}
  }

  const toggleAccount=async user=>{
    const body=new FormData()
    body.set('aktif',String(!user.aktif))
    try{await authFetch(`/api/v1/admin/pengguna/${user.id}/status`,{method:'PATCH',body});refresh()}
    catch(error){notify(error.message)}
  }

  const resetPassword=async value=>{
    const body=new FormData()
    body.set('password_baru',value)
    try{
      await authFetch(`/api/v1/admin/pengguna/${passwordUser.id}/reset-password`,{method:'POST',body})
      setPasswordUser(null)
      notifyOk('Kata sandi direset dan wajib diganti saat login.')
    }catch(error){notify(error.message)}
  }

  /* Ruang kerja tidak memakai pita kepala halaman. Identitas dan peran sudah
     terbaca di bilah atas, dan pita biru setinggi 300px hanya mendorong isian
     yang justru jadi alasan orang membuka halaman ini. `bare` melewatinya. */
  /* Judul tab sudah dipasang usePageTitle di atas, jadi Shell tidak diberi
     `title` di sini — kalau diberi, ia akan menimpanya dengan nilai yang sama
     lewat jalur kedua. */
  return <Shell active="#login" bare>
    {message&&<div className={`notice ${messageTone}`}>
      {messageTone==='success'?<CheckCircle2 size={17}/>:<Info size={17}/>}
      {message}
    </div>}

    {me?.peran==='ADMIN'&&<>
      <section className="workspace-grid">
        <Reveal as="form" className="panel role-form" onSubmit={createAccount}>
          <SectionHead
            kicker="Manajemen akses"
            title="Tambahkan pengguna"
            desc="Operator dapat ditempatkan di provinsi atau kabupaten/kota. Verifikator hanya di provinsi."
          />
          <input name="username" placeholder="Username" required/>
          <input name="nama" placeholder="Nama lengkap" required/>
          <input name="password" type="password" placeholder="Kata sandi awal (min. 12 karakter)" required/>
          <select name="peran" value={accountRole} onChange={e=>setAccountRole(e.target.value)}>
            <option>OPERATOR</option><option>VERIFIKATOR</option><option>ADMIN</option>
          </select>
          {accountRole!=='ADMIN'&&(accountRole==='VERIFIKATOR'
            ?<><input type="hidden" name="wilayah_kode" value="65"/><div className="locked-field">Provinsi Kalimantan Utara</div></>
            :<select name="wilayah_kode" required>
              <option value="">Pilih wilayah operator</option>
              {regions.map(x=><option value={x.kode} key={x.kode}>{x.nama}</option>)}
            </select>)}
          <button>Buat akun</button>
        </Reveal>

        <Reveal as="section" delay={60} className="panel role-summary">
          <span className="kicker">Ringkasan akses</span>
          <h2>{users.length} akun terdaftar</h2>
          <div className="role-counts">
            {['ADMIN','OPERATOR','VERIFIKATOR'].map(role=>
              <div key={role}><b>{users.filter(u=>u.peran===role).length}</b><span>{role}</span></div>
            )}
          </div>
          <p>Admin dapat membuat akun, mengubah status aktif, mereset kata sandi, melihat bukti, dan memantau antrean.</p>
        </Reveal>
      </section>

      <Panel delay={40} kicker="Pengguna" title="Daftar akun dan akses">
        <div className="table-scroll">
          <table className="workspace-table">
            <thead><tr><th>Pengguna</th><th>Role</th><th>Wilayah</th><th>Status</th><th>Aksi</th></tr></thead>
            <tbody>
              {users.map(user=>
                <tr key={user.id}>
                  <td><b>{user.nama}</b><small>{user.username}</small></td>
                  <td>{user.peran}</td>
                  <td>{user.wilayah||'Seluruh wilayah'}</td>
                  <td><span className={`indicator-state ${user.aktif?'tersedia':'belum-tersedia'}`}>{user.aktif?'Aktif':'Nonaktif'}</span></td>
                  <td>
                    <div className="row-actions">
                      <button onClick={()=>toggleAccount(user)}>{user.aktif?'Nonaktifkan':'Aktifkan'}</button>
                      <button onClick={()=>setPasswordUser(user)}>Reset password</button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </>}

    {me?.peran==='OPERATOR'&&
      <section className="workspace-grid operator-grid">
        <Reveal as="form" className="panel role-form" onSubmit={submitValue}>
          <SectionHead
            kicker="Input realisasi"
            title="Kirim data indikator"
            desc="Koreksi angka dibuat sebagai usulan baru agar riwayat lama tidak hilang."
          />
          <input type="hidden" name="jenis" value="realisasi"/>
          <select name="id_indikator" value={draft.id_indikator} onChange={e=>setDraft({...draft,id_indikator:e.target.value})} required>
            <option value="">Pilih indikator</option>
            {catalog.map(x=><option value={x.id_indikator} key={x.id_indikator}>{x.kode_indikator} · {x.nama_indikator}</option>)}
          </select>
          <div className="form-pair">
            <input name="tahun" type="number" min="2000" max="2045" value={draft.tahun} onChange={e=>setDraft({...draft,tahun:e.target.value})} required/>
            <select name="periode" value={draft.periode} onChange={e=>setDraft({...draft,periode:e.target.value})}>
              <option value="">Tahunan / tidak berkala</option>
              <option value="1">Semester 1</option>
              <option value="2">Semester 2</option>
            </select>
          </div>
          <div className="form-pair">
            <input name="nilai" type="number" step="any" value={draft.nilai} onChange={e=>setDraft({...draft,nilai:e.target.value})} placeholder="Nilai realisasi" required/>
            <input name="sumber" value={draft.sumber} onChange={e=>setDraft({...draft,sumber:e.target.value})} placeholder="Sumber/instansi pemberi data" required/>
          </div>
          <small className="form-hint">Untuk indikator semesteran, kirim Semester 1 dan Semester 2 sebagai dua usulan. Dashboard otomatis memakai semester terakhir yang telah disetujui.</small>
          <textarea name="catatan" value={draft.catatan} onChange={e=>setDraft({...draft,catatan:e.target.value})} placeholder="Catatan atau alasan koreksi"/>
          <label className="file-field">
            <span>Bukti dukung wajib</span>
            <input name="bukti" type="file" accept=".pdf,.jpg,.jpeg,.png,.xlsx" multiple required/>
            <small>Surat permintaan, balasan OPD, publikasi, atau dokumen pendukung. Maksimal 10 MB/file.</small>
          </label>
          <button>Kirim untuk disetujui</button>
        </Reveal>

        <Reveal as="section" delay={60} className="panel role-summary">
          <span className="kicker">Alur operator</span>
          <h2>Input → bukti → verifikasi</h2>
          <OperatorFlow/>
        </Reveal>
      </section>}

    {(me?.peran==='VERIFIKATOR'||me?.peran==='ADMIN')&&
      <Panel
        delay={40}
        className="verification-queue"
        kicker="Antrean verifikasi"
        title="Data masuk dari seluruh wilayah"
        desc="Periksa angka, sumber, dan bukti sebelum mengambil keputusan."
        actions={<span className="count-pill">{submissions.filter(x=>x.status==='MENUNGGU_VERIFIKASI').length} menunggu</span>}
      >
        <SubmissionTable rows={submissions} canDecide onEvidence={loadEvidence} onDecision={decide}/>
      </Panel>}

    {me?.peran==='OPERATOR'&&
      <Panel delay={40} kicker="Riwayat usulan" title="Status data yang pernah dikirim">
        <SubmissionTable
          rows={submissions}
          onEvidence={loadEvidence}
          onCorrect={row=>{
            setDraft({
              id_indikator:row.id_indikator,tahun:row.tahun,periode:row.periode||'',nilai:row.nilai,sumber:row.sumber,
              catatan:`Koreksi usulan #${row.id}: ${row.alasan_verifikasi||''}`
            })
            scrollTo({top:300,behavior:'smooth'})
          }}
        />
      </Panel>}

    {me?.peran==='ADMIN'&&
      <Panel delay={40} kicker="Audit nilai" title="Jejak perubahan terverifikasi">
        <div className="table-scroll">
          <table className="workspace-table">
            <thead>
              <tr><th>Waktu</th><th>Pengguna</th><th>Indikator</th><th>Nilai lama</th><th>Nilai baru</th><th>Sumber</th></tr>
            </thead>
            <tbody>
              {logs.map(row=>
                <tr key={row.id}>
                  <td>{dateText(row.waktu)}</td>
                  <td>{row.username||'sistem'}</td>
                  <td>{row.id_indikator}</td>
                  <td>{row.nilai_lama??'—'}</td>
                  <td>{row.nilai_baru??'—'}</td>
                  <td>{row.sumber_perubahan}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>}

    {evidence&&
      <div className="evidence-modal" role="dialog" aria-modal="true" onClick={()=>setEvidence(null)}>
        <div onClick={e=>e.stopPropagation()}>
          <header>
            <div>
              <span>Bukti dukung usulan #{evidence.submission.id}</span>
              <h3>{evidence.submission.id_indikator} · {evidence.submission.wilayah}</h3>
            </div>
            <button onClick={()=>setEvidence(null)} aria-label="Tutup">×</button>
          </header>
          {evidence.files.length
            ?evidence.files.map(file=>
              <button className="evidence-file" key={file.id} onClick={()=>openEvidence(file)}>
                <Eye size={18}/>
                <span><b>{file.nama_file}</b><small>{Math.ceil(file.ukuran/1024)} KB · {file.mime_type}</small></span>
              </button>)
            :<EmptyState icon={FileWarning} compact title="Belum ada bukti dukung"/>}
        </div>
      </div>}
    {passwordUser&&<PasswordResetModal user={passwordUser} onClose={()=>setPasswordUser(null)} onSubmit={resetPassword}/>}
  </Shell>
}

/* ==========================================================================
   Router
   ========================================================================== */

export default function App(){
  const [hash,setHash]=useState(location.hash||'#beranda')
  useEffect(()=>{
    const fn=()=>{setHash(location.hash||'#beranda');scrollTo({top:0})}
    addEventListener('hashchange',fn)
    return()=>removeEventListener('hashchange',fn)
  },[])
  if(hash.startsWith('#detail/'))return <DetailPage id={hash.split('/')[1]}/>
  if(hash==='#beranda')return <HomePage/>
  if(hash==='#indikator')return <IndicatorExplorerPage/>
  if(hash==='#capaian')return <CapaianPage/>
  if(hash==='#insight')return <InsightPage/>
  if(hash==='#validitas')return <ValidityPage/>
  if(hash==='#analitik')return <AnalyticsPage/>
  if(hash==='#admin'||hash==='#login')return <AdminPage/>
  return <HomePage/>
}
