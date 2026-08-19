import {useEffect, useState} from 'react'
import {valueLabel} from '../../lib/format'
import {geoPaths} from '../../lib/geo'

/* Nama wilayah dari GeoJSON dan dari API tidak selalu sama persis
   ("Kota Tarakan" vs "Tarakan"); kunci ini menyamakan keduanya. */
const regionKey=name=>String(name||'')
  .replace(/^Kota\s+/i,'').replace(/^Kabupaten\s+/i,'').trim().toLowerCase()


export function KaltaraMap({regions,selected,onSelect,unit}){
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
