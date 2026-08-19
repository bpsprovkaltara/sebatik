/* @vitest-environment jsdom */
/* useFetch menggantikan pola useEffect yang dulu ditulis ulang di tiap halaman.
   Yang paling mudah salah pada pola itu — dan karena itu diuji di sini — adalah
   pembaruan state setelah komponen dilepas, dan jawaban permintaan lama yang
   datang belakangan lalu menimpa jawaban permintaan baru. */
import {afterEach, describe, expect, it, vi} from 'vitest'
import {createRoot} from 'react-dom/client'
import {act} from 'react'

import {useFetch} from './useFetch'

/* Tanpa penanda ini React memperingatkan lewat console.error bahwa lingkungan
   belum disiapkan untuk act(); peringatan itu akan mengaburkan tes di bawah
   yang justru memeriksa kesunyian console. */
globalThis.IS_REACT_ACT_ENVIRONMENT = true

let root
let wadah

function render(element) {
  wadah = document.createElement('div')
  document.body.appendChild(wadah)
  root = createRoot(wadah)
  act(() => root.render(element))
}

function Penampil({muat, deps = [], opsi}) {
  const {data, galat, memuat} = useFetch(muat, deps, opsi)
  return (
    <div>
      <span data-uji="memuat">{String(memuat)}</span>
      <span data-uji="data">{data ? JSON.stringify(data) : ''}</span>
      <span data-uji="galat">{galat}</span>
    </div>
  )
}

const teks = kunci => wadah.querySelector(`[data-uji="${kunci}"]`).textContent

afterEach(() => {
  if (root) act(() => root.unmount())
  wadah?.remove()
  root = undefined
  vi.restoreAllMocks()
})

describe('useFetch', () => {
  it('memuat dulu, lalu menyimpan hasilnya', async () => {
    let selesaikan
    const muat = () => new Promise(resolve => (selesaikan = resolve))
    render(<Penampil muat={muat} />)
    expect(teks('memuat')).toBe('true')

    await act(async () => selesaikan({tahun: 2025}))
    expect(teks('memuat')).toBe('false')
    expect(teks('data')).toBe('{"tahun":2025}')
    expect(teks('galat')).toBe('')
  })

  it('menyimpan pesan galat dan berhenti memuat saat permintaan gagal', async () => {
    render(<Penampil muat={() => Promise.reject(new Error('API gagal (500)'))} />)
    await act(async () => {})
    expect(teks('galat')).toBe('API gagal (500)')
    expect(teks('memuat')).toBe('false')
  })

  it('tidak memuat apa pun saat dinonaktifkan', async () => {
    const muat = vi.fn(() => Promise.resolve({}))
    render(<Penampil muat={muat} opsi={{aktif: false}} />)
    await act(async () => {})
    expect(muat).not.toHaveBeenCalled()
    expect(teks('memuat')).toBe('false')
  })

  it('tidak memperbarui state setelah komponen dilepas', async () => {
    let selesaikan
    const galatKonsol = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(<Penampil muat={() => new Promise(resolve => (selesaikan = resolve))} />)

    act(() => root.unmount())
    root = undefined
    await act(async () => selesaikan({tahun: 2025}))

    /* React memperingatkan lewat console.error bila state komponen mati
       disentuh; sunyinya console itulah buktinya. */
    expect(galatKonsol).not.toHaveBeenCalled()
  })

  it('jawaban permintaan lama tidak menimpa hasil permintaan baru', async () => {
    let selesaikanLama
    const lama = () => new Promise(resolve => (selesaikanLama = resolve))
    const baru = () => Promise.resolve({versi: 'baru'})

    render(<Penampil muat={lama} deps={['a']} />)
    act(() => root.render(<Penampil muat={baru} deps={['b']} />))
    await act(async () => {})
    expect(teks('data')).toBe('{"versi":"baru"}')

    await act(async () => selesaikanLama({versi: 'lama'}))
    expect(teks('data')).toBe('{"versi":"baru"}')
  })
})
