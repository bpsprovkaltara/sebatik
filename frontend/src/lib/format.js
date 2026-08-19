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
