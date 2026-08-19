import {EmptyState} from '../../ui'
import {Eye, ListChecks} from 'lucide-react'
import {dateText, fmt} from '../../lib/format'

export function SubmissionTable({rows,canDecide=false,onEvidence,onDecision,onCorrect}){
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

