/* @vitest-environment jsdom */
/* Berkas ini perlu DOM, sementara berkas uji lain di proyek ini murni logika.
   Lingkungannya disebut di sini, per berkas, supaya `vitest run` tetap berjalan
   apa adanya tanpa memaksa seluruh proyek memuat jsdom.

   Reveal memakai IntersectionObserver, yang tidak ada di jsdom. Pengamat itu
   diganti tiruan supaya yang diperiksa adalah hal yang benar-benar bisa salah:
   apakah ambang yang diminta pemanggil benar-benar sampai ke pengamat, dan
   apakah kelas `is-in` dipasang saat elemen dinyatakan masuk layar. */
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest'
import {createRoot} from 'react-dom/client'
import {act} from 'react'
import {Panel,Reveal,SECTION_REVEAL} from './ui'

let observed
class FakeObserver{
  constructor(callback,options){
    this.callback=callback
    observed.push({options,targets:[]})
    this.entry=observed[observed.length-1]
  }
  observe(node){this.entry.targets.push(node)}
  unobserve(){}
  disconnect(){}
  enter(){this.callback(this.entry.targets.map(target=>({isIntersecting:true,target})))}
}

let container,root
beforeEach(()=>{
  observed=[]
  FakeObserver.instances=[]
  globalThis.IntersectionObserver=class extends FakeObserver{
    constructor(...args){super(...args);FakeObserver.instances.push(this)}
  }
  globalThis.matchMedia=globalThis.matchMedia||(()=>({matches:false,addEventListener(){},removeEventListener(){}}))
  container=document.createElement('div')
  document.body.appendChild(container)
  root=createRoot(container)
})
afterEach(()=>{act(()=>root.unmount());container.remove();vi.restoreAllMocks()})

const render=element=>act(()=>root.render(element))

describe('Reveal',()=>{
  it('memakai ambang bawaan bila pemanggil tidak meminta apa-apa',()=>{
    render(<Reveal>isi</Reveal>)
    expect(observed).toHaveLength(1)
    expect(observed[0].options.rootMargin).toBe('0px 0px -8% 0px')
  })

  it('meneruskan ambang khusus dari prop `observe` ke pengamat',()=>{
    render(<Reveal observe={SECTION_REVEAL}>isi</Reveal>)
    expect(observed[0].options.rootMargin).toBe(SECTION_REVEAL.rootMargin)
    expect(observed[0].options.threshold).toBe(SECTION_REVEAL.threshold)
  })

  it('Panel ikut meneruskan `observe`, bukan menelannya',()=>{
    render(<Panel title="Judul" observe={SECTION_REVEAL}>isi</Panel>)
    expect(observed[0].options.rootMargin).toBe(SECTION_REVEAL.rootMargin)
  })

  it('menahan isi sampai dinyatakan masuk layar, lalu melepasnya',()=>{
    render(<Reveal observe={SECTION_REVEAL}>isi</Reveal>)
    const node=container.firstElementChild
    expect(node.className).toContain('reveal')
    expect(node.classList.contains('is-in')).toBe(false)
    act(()=>FakeObserver.instances[0].enter())
    expect(node.classList.contains('is-in')).toBe(true)
  })
})
