import {RUTE} from '../../lib/rute'
import {roleLabel} from '../../auth'
import {Compass, Home, LogOut, ShieldCheck, Sparkles, Target, UserRound} from 'lucide-react'

/* Peta rute -> label, ikon, dan deskripsi singkat untuk navigasi. */
export const NAV_LINKS=[
  [RUTE.beranda,'Beranda',Home],
  [RUTE.indikator,'Indikator',Compass],
  [RUTE.capaian,'Capaian',Target],
  [RUTE.insight,'Insight',Sparkles],
  [RUTE.validitas,'Validitas',ShieldCheck]
]

/* Slot terakhir navigasi mengikuti status masuk.

   Sebelum ini slot tersebut memuat satu kendali saja: "Masuk" ketika belum
   masuk, "Keluar" ketika sudah. Penggabungan itu menutup satu-satunya jalan
   kembali — begitu pengguna yang sudah masuk membuka Beranda atau Indikator,
   tidak ada lagi tautan menuju ruang kerjanya, dan satu-satunya kendali yang
   tersisa justru mengakhiri sesinya. Ruang kerjanya masih hidup di /masuk,
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

export const authNavItems=(token,profile)=>token
  ? [
      {jalur:RUTE.masuk,label:roleLabel(profile?.peran),icon:UserRound,logout:false},
      {jalur:RUTE.beranda,label:'Keluar',icon:LogOut,logout:true}
    ]
  : [{jalur:RUTE.masuk,label:'Masuk',icon:UserRound,logout:false}]
