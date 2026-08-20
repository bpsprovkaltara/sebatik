import {Cell, CartesianGrid, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts'
import {Database} from 'lucide-react'
import {EmptyState} from '../../ui'
import {TooltipCard} from '../charts/TooltipCard'
import {fmt} from '../../lib/format'

const COLORS=['var(--brand)','var(--surface-3)']

export function AvailabilityTracker({items,year}){
  const selected=items.find(x=>String(x.tahun)===String(year))||items.at(-1)
  if(!items.length)return <EmptyState icon={Database} title="Ketersediaan belum dapat dihitung" desc="Data realisasi tahunan belum tersedia."/>

  const pie=[
    {name:'Terisi',value:selected?.terisi||0},
    {name:'Belum terisi',value:Math.max(0,(selected?.total||0)-(selected?.terisi||0))},
  ]
  return <div className="availability-layout">
    <div className="availability-line">
      <h3>Perkembangan Persentase Ketersediaan Data</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={items} margin={{top:28,right:28,left:12,bottom:10}}>
          <CartesianGrid stroke="var(--line)" vertical={false}/>
          <XAxis dataKey="tahun" tickLine={false} axisLine={false} tickMargin={12}/>
          <YAxis domain={[0,100]} tickFormatter={x=>`${x}%`} tickLine={false} axisLine={false} tickMargin={12} width={58}/>
          <Tooltip content={<TooltipCard unit="%"/>}/>
          <Line type="monotone" dataKey="persentase" name="Ketersediaan" stroke="var(--brand)" strokeWidth={3} dot={{r:5,fill:'var(--brand)'}} activeDot={{r:7}}/>
        </LineChart>
      </ResponsiveContainer>
    </div>
    <div className="availability-pie">
      <h3>Ketersediaan Data Tahun {selected?.tahun}</h3>
      <div className="pie-stack">
        <ResponsiveContainer width="100%" height={190}>
          <PieChart>
            <Pie data={pie} dataKey="value" innerRadius={58} outerRadius={80} startAngle={90} endAngle={-270} stroke="none">
              {pie.map((entry,index)=><Cell key={entry.name} fill={COLORS[index]}/>) }
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pie-center"><strong>{fmt.format(selected?.persentase||0)}%</strong><span>{selected?.terisi||0} dari {selected?.total||0}</span></div>
      </div>
      {/* Nama kelompok dan persentasenya berdampingan sebagai satu satuan baca,
          bukan didorong ke dua ujung kotak. Dipisah selebar kotak, keduanya
          terbaca sebagai dua keterangan yang kebetulan sebaris; berdampingan,
          "ISV 70%" langsung terbaca sebagai satu pernyataan. */}
      <div className="availability-breakdown">
        {['isv','iup'].map(key=><div key={key}>
          <p className="availability-breakdown-head">
            <span>{key.toUpperCase()}</span>
            <b>{fmt.format(selected?.[key]?.persentase||0)}%</b>
          </p>
          <small>{selected?.[key]?.terisi||0} dari {selected?.[key]?.total||0} indikator telah tersedia</small>
        </div>)}
      </div>
    </div>
  </div>
}
