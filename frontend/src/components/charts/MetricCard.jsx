import {CountUp, Reveal} from '../../ui'
import {useEffect, useState} from 'react'
import {fmt} from '../../lib/format'

export function MetricCard({icon:Icon,label,value,note,tone='var(--series-1)',meter=null,index=0}){
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
