/* @vitest-environment jsdom */
/* Komponen grafik yang murni tampilan. Yang diuji di sini adalah keputusan
   yang benar-benar bisa salah — kapan tooltip menolak tampil, bagaimana nilai
   nol diperlakukan, dan status apa yang dipakai saat data belum ada — bukan
   kelas CSS-nya. */
import {afterEach, describe, expect, it} from 'vitest'
import {createRoot} from 'react-dom/client'
import {act} from 'react'

import {CapaianBadge} from './CapaianBadge'
import {TooltipCard} from './TooltipCard'
import {MetricCard} from './MetricCard'

let root
let wadah

function render(element) {
  wadah = document.createElement('div')
  document.body.appendChild(wadah)
  root = createRoot(wadah)
  act(() => root.render(element))
  return wadah
}

afterEach(() => {
  if (root) act(() => root.unmount())
  wadah?.remove()
  root = undefined
})

describe('CapaianBadge', () => {
  it('menampilkan status dengan garis bawah diganti spasi', () => {
    expect(render(<CapaianBadge status="PERLU_PERHATIAN" />).textContent).toBe('PERLU PERHATIAN')
  })

  it('status kosong dibaca sebagai belum ada data, bukan dibiarkan hampa', () => {
    expect(render(<CapaianBadge status={null} />).textContent).toBe('BELUM ADA DATA')
  })
})

describe('TooltipCard', () => {
  const isi = [{dataKey: 'nilai', name: 'Realisasi', value: 12.5, color: '#123456'}]

  it('tidak menggambar apa pun saat kursor tidak di atas grafik', () => {
    expect(render(<TooltipCard active={false} payload={isi} label={2024} />).textContent).toBe('')
  })

  it('tidak menggambar apa pun saat seluruh seri kosong pada titik itu', () => {
    const kosong = [{dataKey: 'nilai', name: 'Realisasi', value: null}]
    expect(render(<TooltipCard active payload={kosong} label={2024} />).textContent).toBe('')
  })

  it('menampilkan label, nama seri, dan nilainya', () => {
    const teks = render(<TooltipCard active payload={isi} label={2024} />).textContent
    expect(teks).toContain('2024')
    expect(teks).toContain('Realisasi')
    expect(teks).toContain('12.5')
  })

  it('menyisipkan satuan dan awalan label bila diminta', () => {
    const teks = render(<TooltipCard active payload={isi} label={2024} unit="%" labelPrefix="Tahun " />).textContent
    expect(teks).toContain('Tahun 2024')
    expect(teks).toContain('12.5%')
  })

  it('formatter pemanggil mengalahkan satuan bawaan', () => {
    const teks = render(<TooltipCard active payload={isi} label={2024} unit="%" formatter={v => `${v} jiwa`} />)
      .textContent
    expect(teks).toContain('12.5 jiwa')
    expect(teks).not.toContain('12.5%')
  })

  it('nilai nol tetap ditampilkan, bukan dianggap kosong', () => {
    const nol = [{dataKey: 'nilai', name: 'Realisasi', value: 0}]
    expect(render(<TooltipCard active payload={nol} label={2024} />).textContent).toContain('0')
  })
})

describe('MetricCard', () => {
  const Ikon = () => <svg />

  it('menampilkan label dan catatan apa adanya', () => {
    const teks = render(<MetricCard icon={Ikon} label="Indikator" value="86" note="dari basis data" />).textContent
    expect(teks).toContain('Indikator')
    expect(teks).toContain('dari basis data')
  })

  it('meter hanya digambar bila pemanggil memberi angkanya', () => {
    expect(render(<MetricCard icon={Ikon} label="A" value="1" note="n" />).querySelector('.metric-meter')).toBeNull()
    act(() => root.unmount())
    root = undefined
    wadah.remove()
    expect(
      render(<MetricCard icon={Ikon} label="A" value="1" note="n" meter={40} />).querySelector('.metric-meter'),
    ).not.toBeNull()
  })

  it('meter bernilai nol tetap digambar sebagai batang kosong', () => {
    expect(
      render(<MetricCard icon={Ikon} label="A" value="1" note="n" meter={0} />).querySelector('.metric-meter'),
    ).not.toBeNull()
  })
})
