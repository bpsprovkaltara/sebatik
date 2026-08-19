import {describe, expect, it} from 'vitest'

import {RUTE, alihkanTautanLama, ke, keDetail} from './rute'

describe('bentuk href', () => {
  it('menambahkan pagar di depan jalur', () => {
    expect(ke(RUTE.capaian)).toBe('#/capaian')
    expect(keDetail('ISV-001')).toBe('#/detail/ISV-001')
  })
})

describe('tautan lama', () => {
  it('memindahkan hash lama ke jalur baru', () => {
    expect(alihkanTautanLama('#capaian')).toBe('/capaian')
    expect(alihkanTautanLama('#beranda')).toBe('/')
  })

  it('memetakan dua pintu masuk ruang kerja ke satu rute', () => {
    expect(alihkanTautanLama('#login')).toBe('/masuk')
    expect(alihkanTautanLama('#admin')).toBe('/masuk')
  })

  it('mempertahankan id pada tautan detail', () => {
    expect(alihkanTautanLama('#detail/IUP-050')).toBe('/detail/IUP-050')
  })

  it('membiarkan tautan yang sudah berbentuk baru', () => {
    expect(alihkanTautanLama('#/capaian')).toBeNull()
    expect(alihkanTautanLama('')).toBeNull()
  })

  it('mengabaikan hash yang tidak dikenal', () => {
    expect(alihkanTautanLama('#entah')).toBeNull()
  })
})
