import {capaianVar} from '../../tokens'

export function CapaianBadge({status}){
  const key=status||'BELUM_ADA_DATA'
  return <span className="capaian-badge" style={{'--tone':capaianVar(key)}}>{key.replaceAll('_',' ')}</span>
}

/* ==========================================================================
   Kartu metrik
   ========================================================================== */
