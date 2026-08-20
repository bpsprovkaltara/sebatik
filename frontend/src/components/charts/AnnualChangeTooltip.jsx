import {changeNumber} from '../../lib/format'

export function AnnualChangeTooltip({active,payload,arahTarget}){
  if(!active||!payload?.length)return null
  const item=payload[0]?.payload
  if(!item||item.previousValue===null||item.previousValue===undefined)return null
  const pointChange=item.nilai-item.previousValue
  const movement=pointChange>0?'Naik':pointChange<0?'Turun':'Tetap'
  const targetRelation=(arahTarget==='TURUN'?item.growth<=0:item.growth>=0)
    ?'searah dengan target 2029'
    :'berlawanan arah dengan target 2029'
  const signedGrowth=`${item.growth>0?'+':item.growth<0?'−':''}${changeNumber.format(Math.abs(item.growth))}%`
  return <div className="viz-tooltip annual-change-tooltip" role="tooltip">
    <strong>{item.tahun} · realisasi {changeNumber.format(item.nilai)}</strong>
    <span>{movement} {changeNumber.format(Math.abs(pointChange))} poin dari {item.previousYear} ({changeNumber.format(item.previousValue)})</span>
    <span>{signedGrowth} · {targetRelation}</span>
  </div>
}
