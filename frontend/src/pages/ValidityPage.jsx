import {RUTE} from '../lib/rute'
import {useToken} from '../auth'
import * as endpoints from '../api/endpoints'
import {ChartSkeleton, EmptyState, Reveal} from '../ui'
import {SmartSelect} from '../components/ui/SmartSelect'
import {AlertTriangle, Eye, Search} from 'lucide-react'
import {useEffect, useState} from 'react'
import {MetadataModal} from '../components/explorer/MetadataModal'
import {Shell} from '../components/layout/Shell'
import {dateText} from '../lib/format'

export default function ValidityPage(){
  const [data,setData]=useState(null),[region,setRegion]=useState('65'),[query,setQuery]=useState(''),[error,setError]=useState(''),[metadata,setMetadata]=useState(null)
  /* Dibaca dari sumber bersama, bukan langsung dari localStorage: saat pengguna
     menekan Keluar di bilah atas, tabel ini ikut dimuat ulang sebagai tamu. */
  const token=useToken()

  useEffect(()=>{
    let cancelled=false
    const timer=setTimeout(async()=>{
      try{
        /* Bukti dukung hanya tampil bagi yang berhak; token disisipkan client,
           dan 401 ditangani di sana — halaman ini tidak perlu tahu caranya. */
        const result=await endpoints.validitas({wilayah_kode:region,q:query})
        if(!cancelled){setData(result);setError('')}
      }catch(e){if(!cancelled)setError(e.message)}
    },180)
    return()=>{cancelled=true;clearTimeout(timer)}
  },[region,query,token])

  const viewMetadata=async row=>{
    try{setMetadata({id_indikator:row.id_indikator,nama_indikator:row.nama_indikator,loading:true});setMetadata(await endpoints.metadataIndikator(row.id_indikator))}
    catch(e){setMetadata(null);setError(`Metadata tidak dapat dimuat: ${e.message}`)}
  }

  return <Shell
    active={RUTE.validitas}
    title="Validitas"
    subtitle="Status verifikasi, pembaruan, dan metadata setiap indikator menurut wilayah"
  >
    {error&&<div className="error"><AlertTriangle size={18}/>{error}</div>}

    <Reveal as="section" className="panel validity-panel">
      <div className="validity-toolbar">
        <div className="field">
          <span>Wilayah</span>
          <SmartSelect
            value={region}
            onChange={setRegion}
            options={(data?.wilayah_opsi||[]).map(x=>({value:x.kode,label:x.nama}))}
            ariaLabel="Wilayah"
            placeholder="Pilih wilayah"
          />
        </div>
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
