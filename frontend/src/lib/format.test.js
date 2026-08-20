import {describe, expect, it} from 'vitest'

import {dateText, enumeratedParts, growthTone, hasNumber, softNumber, valueLabel, valueTone} from './format'

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

describe('enumeratedParts', () => {
  it('memecah daftar bernomor yang ditulis memanjang', () => {
    const hasil = enumeratedParts(
      '1. Penurunan Emisi Gas Rumah Kaca (GRK): Laporan AKSARA, Kementerian PPN/Bappenas; ' +
        '2. Produk Domestik Regional Bruto (Harga Konstan 2010): BPS.'
    )
    expect(hasil.items).toHaveLength(2)
    expect(hasil.items[0].label).toBe('1')
    expect(hasil.items[1].text).toContain('Produk Domestik Regional Bruto')
    expect(hasil.lead).toBe('')
  })

  it('menyimpan kalimat pembuka sebelum penanda pertama', () => {
    const hasil = enumeratedParts(
      'Klasifikasi menurut Keputusan Menteri Kesehatan RI Nomor 1995/MENKES/SK/XII/2010. ' +
        'a. Sangat pendek: Zscore < -3,0 b. Pendek: Zscore >= -3,0'
    )
    expect(hasil.items.map((x) => x.label)).toEqual(['a', 'b'])
    expect(hasil.lead).toContain('1995/MENKES')
  })

  it('mengikuti rantai sampai butir terakhir', () => {
    const hasil = enumeratedParts(
      'Prevalensi tinggi menggambarkan beberapa masalah, termasuk: ' +
        '1. Kekurangan gizi kronis. 2. Akses pelayanan kesehatan terbatas. ' +
        '3. Kemiskinan rumah tangga. 4. Pendidikan orang tua. 5. Faktor lingkungan.'
    )
    expect(hasil.items.map((x) => x.label)).toEqual(['1', '2', '3', '4', '5'])
    expect(hasil.items[4].text).toBe('Faktor lingkungan.')
  })

  it('membiarkan kalimat biasa apa adanya', () => {
    expect(enumeratedParts('Badan Pusat Statistik')).toBeNull()
    expect(enumeratedParts('Laporan tahun 2010. Data diolah kembali.')).toBeNull()
    expect(enumeratedParts('')).toBeNull()
    expect(enumeratedParts(null)).toBeNull()
  })
})
