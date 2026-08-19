import {ArrowLeft} from 'lucide-react'

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


export function OperatorFlow(){
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
