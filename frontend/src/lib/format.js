export const fmt=new Intl.NumberFormat('id-ID')
export const changeNumber=new Intl.NumberFormat('id-ID',{minimumFractionDigits:2,maximumFractionDigits:2})
export const displayedUnit=unit=>{
  if(!unit||/^indeks\b/i.test(unit))return ''
  if(/persen|\(%\)|% PDRB/i.test(unit))return '%'
  return unit
}
export const valueLabel=(value,text,unit)=>{
  if(value===null||value===undefined)return text||'Belum tersedia'
  const suffix=displayedUnit(unit)
  return `${fmt.format(value)}${suffix==='%'?'%':suffix?` ${suffix}`:''}`
}

/* Angka tanpa satuan. Dipakai di tempat yang satuannya sudah tertulis sekali
   di judul — mengulanginya pada tiap kotak tahun hanya menambah panjang teks
   tanpa menambah keterangan. */
export const plainValue=(value,text)=>value===null||value===undefined?(text||'Belum tersedia'):fmt.format(value)

/* Angka sorotan dipecah jadi bilangan dan satuannya supaya keduanya bisa
   diberi ukuran berbeda. Tanpa pemisahan ini "208,21 Juta Rupiah" dan "2,57%"
   memakai ukuran yang sama persis, sehingga kartu bersatuan panjang terbaca
   dua kali lebih besar daripada tetangganya padahal angkanya sepadan. */
export const valueParts=(value,text,unit)=>value===null||value===undefined
  ?{number:text||'Belum tersedia',unit:''}
  :{number:fmt.format(value),unit:displayedUnit(unit)}

/* Nama indikator kerap sudah membawa satuannya di ekor — "(%)", "(Rp Juta)",
   "(Ribu Orang)". Yang dipotong hanya kurung penutup yang isinya memang kata
   satuan; akronim seperti "(IBEI)" atau "(IKM)" tidak mengandung kata itu
   sehingga tetap utuh. */
const UNIT_TAIL=/\s*\((?=[^()]*(?:%|persen|rupiah|juta|miliar|milyar|triliun|ribu|orang|jiwa|tahun|poin|skor|indeks|peringkat|per\s))[^()]*\)\s*$/i
export const stripUnit=name=>(name||'').trim().replace(UNIT_TAIL,'').trim()

/* Judul indikator memikul satuannya sendirian. Bila namanya sudah menyebut
   satuan, rumusan aslinya dipertahankan — "(% PDRB)" menyimpan keterangan
   yang tidak tertampung oleh "%" saja. Bila belum, satuan dari basis data
   ditempelkan; satuan indeks sengaja tidak ditempelkan karena `displayedUnit`
   menganggapnya bukan satuan yang perlu dibaca. */
export const indicatorTitle=(name,unit)=>{
  const bare=stripUnit(name)
  if(bare!==(name||'').trim())return (name||'').trim()
  const suffix=displayedUnit(unit)
  return suffix?`${bare} (${suffix})`:bare
}


/* Ukuran angka sorotan dipasang untuk angka. Ketika yang tampil justru kalimat
   — "Belum tersedia" — ukuran itu membuatnya berteriak lebih keras daripada
   angka yang benar-benar ada di kartu sebelahnya. Penanda ini dipakai untuk
   menurunkan ukurannya, bukan untuk menyembunyikannya. */
export const hasNumber=value=>value!==null&&value!==undefined
export const valueTone=value=>hasNumber(value)?'':' is-empty'

/* Warna pertumbuhan pada kartu tahun: naik hijau, turun merah, datar netral.
   Perlu dicatat bahwa ini mewarnai ARAH ANGKA, bukan baik-buruknya keadaan.
   Pada indikator yang arah baiknya menurun — tingkat kemiskinan, pengangguran,
   rasio gini — kenaikan angka justru kabar buruk tetapi tetap tampil hijau.
   Basis data menyimpan `arah_baik`/`arah_target` bila suatu saat pewarnaan
   ingin diikatkan ke makna, bukan ke arah. */
export const growthTone=growth=>growth===null||growth===0?'growth-flat':growth>0?'growth-up':'growth-down'
/* Format angka animasi: pertahankan satu desimal supaya nilai persen tidak
   kehilangan ketelitian saat dihitung naik. */
export const softNumber=v=>fmt.format(Number(Number(v).toFixed(1)))

/* Tanggal ISO dari API ditampilkan dalam bentuk lokal yang pendek.
   Dipakai bersama halaman Insight, Validitas, dan ruang kerja admin. */
export const dateText=value=>{
  if(!value)return '—'
  const parsed=new Date(value.includes('T')?value:value.replace(' ','T')+'Z')
  return Number.isNaN(parsed.getTime())?value:parsed.toLocaleDateString('id-ID',{day:'2-digit',month:'long',year:'numeric'})
}

/* ---------------------------------------------------------------------------
   Daftar bernomor yang telanjur ditulis memanjang
   ---------------------------------------------------------------------------
   Kolom metadata di basis data menyimpan daftar sebagai satu paragraf:
   "1. Penurunan Emisi ...; 2. Produk Domestik ..." atau "a. Sangat pendek ...
   b. Pendek ...". Dibiarkan apa adanya, penomorannya tenggelam di tengah
   kalimat dan pembaca harus memburu angkanya sendiri.

   Penandanya dikenali dengan syarat ketat supaya kalimat biasa tidak ikut
   terpotong: penanda harus BERURUTAN mulai dari 1 atau a. Tanpa syarat itu,
   "Nomor : 1995/MENKES/SK/XII/2010." atau "standar WHO 2005. Data tinggi"
   berpeluang terbaca sebagai awal daftar. Kalau syaratnya tidak terpenuhi,
   fungsi ini mengembalikan null dan pemanggilnya menampilkan teks aslinya. */
const LIST_MARK=/(^|[\s;:])((?:\d{1,2}|[a-z])[.)])\s+(?=\S)/g

const nextMark=label=>{
  const body=label.slice(0,-1)
  return /^\d+$/.test(body)
    ?String(Number(body)+1)+label.slice(-1)
    :String.fromCharCode(body.charCodeAt(0)+1)+label.slice(-1)
}

export const enumeratedParts=text=>{
  const raw=(text||'').toString().trim()
  if(!raw)return null

  const found=[]
  for(const match of raw.matchAll(LIST_MARK)){
    const label=match[2]
    found.push({label,at:match.index+match[1].length,after:match.index+match[0].length})
  }

  /* Rantai terpanjang yang benar-benar berurutan. Penanda yang tidak menyambung
     — "2010." di tengah kalimat — dilewati begitu saja. */
  let chain=[]
  for(let i=0;i<found.length;i++){
    if(!/^(1|a)[.)]$/.test(found[i].label))continue
    const run=[found[i]]
    for(let j=i+1;j<found.length;j++){
      if(found[j].label===nextMark(run[run.length-1].label))run.push(found[j])
    }
    if(run.length>chain.length)chain=run
  }
  if(chain.length<2)return null

  const lead=raw.slice(0,chain[0].at).trim()
  const items=chain.map((mark,i)=>({
    label:mark.label.slice(0,-1),
    text:raw.slice(mark.after,i+1<chain.length?chain[i+1].at:raw.length).trim().replace(/[;,]$/,'')
  }))
  return {lead,items}
}
