import {createContext, useCallback, useContext, useMemo} from 'react'

import {keluarSesi, roleLabel, setToken, useProfile, useToken} from '../auth'
import * as endpoints from '../api/endpoints'

/* Status masuk tetap dikelola auth.js supaya tab lain ikut tersinkron. Context
   ini menyatukan token, profil, dan dua perbuatan (masuk/keluar) menjadi satu
   antarmuka, sehingga komponen tidak lagi merangkai ketiganya sendiri. */
const KonteksAuth = createContext(null)

export function AuthProvider({children}){
  const token = useToken()
  const profil = useProfile()

  const masuk = useCallback(async (username, password) => {
    const hasil = await endpoints.login(new URLSearchParams({username, password}))
    setToken(hasil.access_token)
    return hasil
  }, [])

  /* Keluar juga menghapus cookie segar di server; kalau hanya token lokal yang
     dibuang, permintaan berikutnya akan menyegarkan sesi yang baru ditutup. */
  const keluar = useCallback(() => keluarSesi(), [])

  const nilai = useMemo(() => ({
    token,
    profil,
    peran: profil?.peran ?? null,
    labelPeran: roleLabel(profil?.peran),
    sudahMasuk: Boolean(token),
    masuk,
    keluar,
  }), [token, profil, masuk, keluar])

  return <KonteksAuth.Provider value={nilai}>{children}</KonteksAuth.Provider>
}

export function useAuth(){
  const nilai = useContext(KonteksAuth)
  if(!nilai) throw new Error('useAuth harus dipakai di dalam AuthProvider')
  return nilai
}
