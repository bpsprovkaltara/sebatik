export function geoPaths(geo,width=560,height=390){
  const points=[]
  const collect=x=>Array.isArray(x?.[0])?x.forEach(collect):points.push(x)
  geo.features.forEach(f=>collect(f.geometry.coordinates))
  const xs=points.map(p=>p[0]),ys=points.map(p=>p[1])
  const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),pad=18
  const scale=Math.min((width-pad*2)/(maxX-minX),(height-pad*2)/(maxY-minY))
  const offX=(width-(maxX-minX)*scale)/2,offY=(height-(maxY-minY)*scale)/2
  const project=p=>[offX+(p[0]-minX)*scale,offY+(maxY-p[1])*scale]
  const ringPath=ring=>ring.map((p,i)=>{const [x,y]=project(p);return `${i?'L':'M'}${x.toFixed(1)},${y.toFixed(1)}`}).join('')+'Z'
  return geo.features.map(f=>{
    const polys=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates
    return {
      name:f.properties.wadmkk||f.properties.namobj,
      code:String(f.properties.kdpkab||'').replace('.',''),
      d:polys.flatMap(p=>p).map(ringPath).join('')
    }
  })
}
