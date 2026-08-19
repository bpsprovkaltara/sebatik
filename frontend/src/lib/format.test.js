import {describe, expect, it} from 'vitest'

import {dateText, growthTone, hasNumber, softNumber, valueLabel, valueTone} from './format'

describe('valueLabel', () => {
  it('menampilkan kalimat ketika nilai belum ada', () => {
    expect(valueLabel(null, null, 'Persen (%)')).toBe('Belum tersedia')
    expect(valueLabel(undefined, 'Data dirahasiakan', '%')).toBe('Data dirahasiakan')
  })

  it('menempelkan persen tanpa spasi', () => {
    expect(valueLabel(7.5, null, 'Persen (%)')).toBe('7,5%')
  })

  it('menghilangkan satuan indeks yang tidak perlu dibaca', () => {
    expect(valueLabel(72, null, 'Indeks (0–100)')).toBe('72')
  })

  it('memberi spasi untuk satuan lain', () => {
    expect(valueLabel(12, null, 'Tahun')).toBe('12 Tahun')
  })
})

describe('penanda nilai kosong', () => {
  it('membedakan angka dari ketiadaan angka', () => {
    expect(hasNumber(0)).toBe(true)
    expect(hasNumber(null)).toBe(false)
    expect(hasNumber(undefined)).toBe(false)
  })

  it('menurunkan ukuran hanya saat nilai kosong', () => {
    expect(valueTone(3.2)).toBe('')
    expect(valueTone(null)).toBe(' is-empty')
  })
})

describe('growthTone', () => {
  it('mewarnai arah angka, bukan baik-buruknya', () => {
    expect(growthTone(2)).toBe('growth-up')
    expect(growthTone(-2)).toBe('growth-down')
    expect(growthTone(0)).toBe('growth-flat')
    expect(growthTone(null)).toBe('growth-flat')
  })
})

describe('softNumber', () => {
  it('mempertahankan satu desimal', () => {
    expect(softNumber(3.85)).toBe('3,9')
    expect(softNumber(12)).toBe('12')
  })
})

describe('dateText', () => {
  it('memberi tanda pisah ketika tanggal tidak ada', () => {
    expect(dateText(null)).toBe('—')
    expect(dateText('')).toBe('—')
  })

  it('membaca stempel waktu tanpa zona sebagai UTC', () => {
    expect(dateText('2026-08-19 03:00:00')).toContain('2026')
  })

  it('mengembalikan apa adanya bila bukan tanggal', () => {
    expect(dateText('bukan tanggal')).toBe('bukan tanggal')
  })
})
