/* Lapisan API adalah satu-satunya tempat token disisipkan dan 401 ditangani.
   Kalau bagian ini salah, gejalanya muncul jauh dari sini: halaman publik ikut
   gagal, atau sesi yang masih bisa disambung malah dibuang.

   Tiruan `fetch` di sini menjawab berdasarkan URL, bukan berdasarkan urutan
   panggilan. Sebabnya: menyegarkan token ikut memicu pemuatan ulang profil di
   auth.js, jadi jumlah panggilan bukan sesuatu yang layak dikunci di tes ini. */
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'

import {ApiError, qs, request, requestMentah} from './client'
import {getToken, setToken} from '../auth'

const SEGARKAN = '/api/v1/auth/refresh'
const PROFIL = '/api/v1/auth/saya'

const jawaban = (isi, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => isi,
  text: async () => JSON.stringify(isi),
})

/** Rute tiruan: URL -> daftar jawaban berurutan (yang terakhir dipakai ulang). */
function pasangFetch(rute) {
  globalThis.fetch = vi.fn(async (url, options) => {
    const antrean = rute[url]
    if (!antrean) throw new Error(`URL tak terduga di tes: ${url}`)
    const berikut = antrean.length > 1 ? antrean.shift() : antrean[0]
    return typeof berikut === 'function' ? berikut(options) : berikut
  })
}

const panggilanKe = url => fetch.mock.calls.filter(([alamat]) => alamat === url)
const kepala = panggilan => panggilan?.[1]?.headers || {}

beforeEach(() => {
  setToken('')
})

afterEach(() => {
  setToken('')
  vi.restoreAllMocks()
})

describe('request', () => {
  it('tidak menyisipkan Authorization saat tamu', async () => {
    pasangFetch({'/api/v1/beranda': [jawaban({data: []})]})
    await request('/api/v1/beranda')
    expect(kepala(panggilanKe('/api/v1/beranda')[0]).Authorization).toBeUndefined()
  })

  it('menyisipkan Bearer saat ada token', async () => {
    pasangFetch({'/api/v1/beranda': [jawaban({data: []})], [PROFIL]: [jawaban({peran: 'ADMIN'})]})
    setToken('token-abc')
    await request('/api/v1/beranda')
    expect(kepala(panggilanKe('/api/v1/beranda')[0]).Authorization).toBe('Bearer token-abc')
  })

  it('mempertahankan header pemanggil sambil menambahkan token', async () => {
    pasangFetch({'/api/v1/x': [jawaban({})], [PROFIL]: [jawaban({})]})
    setToken('token-abc')
    await request('/api/v1/x', {headers: {'X-Uji': '1'}})
    expect(kepala(panggilanKe('/api/v1/x')[0])).toMatchObject({'X-Uji': '1', Authorization: 'Bearer token-abc'})
  })

  it('menyegarkan sesi lalu mengulang permintaan saat token kedaluwarsa', async () => {
    pasangFetch({
      '/api/v1/admin/log': [
        options => (kepala([null, options]).Authorization === 'Bearer token-baru' ? jawaban({data: [1]}) : jawaban({}, 401)),
      ],
      [SEGARKAN]: [jawaban({access_token: 'token-baru'})],
      [PROFIL]: [jawaban({peran: 'ADMIN'})],
    })
    setToken('token-lama')

    await expect(request('/api/v1/admin/log', {autentikasi: 'wajib'})).resolves.toEqual({data: [1]})
    expect(panggilanKe(SEGARKAN)).toHaveLength(1)
    expect(getToken()).toBe('token-baru')
  })

  it('membuang token dan melempar 401 bila penyegaran ikut gagal', async () => {
    pasangFetch({'/api/v1/admin/log': [jawaban({}, 401)], [SEGARKAN]: [jawaban({}, 401)], [PROFIL]: [jawaban({}, 401)]})
    setToken('token-lama')

    await expect(request('/api/v1/admin/log', {autentikasi: 'wajib'})).rejects.toMatchObject({
      name: 'ApiError',
      status: 401,
    })
    expect(getToken()).toBe('')
  })

  it('endpoint publik tetap tampil bagi tamu meski token basi', async () => {
    pasangFetch({
      '/api/v1/beranda': [options => (kepala([null, options]).Authorization ? jawaban({}, 401) : jawaban({tahun: 2025}))],
      [SEGARKAN]: [jawaban({}, 401)],
      [PROFIL]: [jawaban({}, 401)],
    })
    setToken('token-basi')

    await expect(request('/api/v1/beranda')).resolves.toEqual({tahun: 2025})
    /* Percobaan terakhir sengaja tanpa header: itu yang membuat halaman publik
       tetap terbuka setelah sesi mati. */
    const terakhir = panggilanKe('/api/v1/beranda').at(-1)
    expect(kepala(terakhir).Authorization).toBeUndefined()
  })

  it('tidak mencoba menyegarkan bila memang belum pernah masuk', async () => {
    pasangFetch({'/api/v1/beranda': [jawaban({}, 401), jawaban({ok: true})]})
    await request('/api/v1/beranda')
    expect(panggilanKe(SEGARKAN)).toHaveLength(0)
  })

  it('galat non-401 dibungkus ApiError beserta detailnya', async () => {
    pasangFetch({'/api/v1/beranda': [jawaban({detail: 'Wilayah tidak valid'}, 422)]})
    const galat = await request('/api/v1/beranda').catch(e => e)
    expect(galat).toBeInstanceOf(ApiError)
    expect(galat.status).toBe(422)
    expect(galat.detail).toBe('Wilayah tidak valid')
  })
})

describe('requestMentah', () => {
  it('mengembalikan Response apa adanya untuk unduhan biner', async () => {
    const response = jawaban({})
    pasangFetch({'/api/v1/bukti/1': [response], [PROFIL]: [jawaban({})]})
    setToken('token-abc')
    await expect(requestMentah('/api/v1/bukti/1')).resolves.toBe(response)
  })

  it('ikut menyegarkan sesi sebelum menyerah', async () => {
    const berhasil = jawaban({isi: 'pdf'})
    pasangFetch({
      '/api/v1/bukti/1': [
        options => (kepala([null, options]).Authorization === 'Bearer token-baru' ? berhasil : jawaban({}, 401)),
      ],
      [SEGARKAN]: [jawaban({access_token: 'token-baru'})],
      [PROFIL]: [jawaban({})],
    })
    setToken('token-lama')
    await expect(requestMentah('/api/v1/bukti/1')).resolves.toBe(berhasil)
  })
})

describe('qs', () => {
  it('membuang nilai kosong supaya URL tidak berisi parameter hampa', () => {
    expect(qs({a: 1, b: '', c: null, d: undefined})).toBe('a=1')
  })

  it('mengulang kunci untuk nilai berupa daftar', () => {
    expect(qs({kategori: ['ISV', 'IUP']})).toBe('kategori=ISV&kategori=IUP')
  })
})
