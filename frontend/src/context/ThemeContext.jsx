import {createContext, useContext} from 'react'

import {useTheme} from '../theme'

/* Tema tetap disimpan oleh theme.js (satu sumber, termasuk sinkronisasi
   localStorage antar-tab). Context ini hanya menyediakannya lewat satu jalur
   idiomatis sehingga komponen tidak perlu tahu ada pola langganan di baliknya. */
const KonteksTema = createContext(null)

export function ThemeProvider({children}){
  const [tema, alihkan] = useTheme()
  return <KonteksTema.Provider value={{tema, alihkan}}>{children}</KonteksTema.Provider>
}

export function useThemeContext(){
  const nilai = useContext(KonteksTema)
  if(!nilai) throw new Error('useThemeContext harus dipakai di dalam ThemeProvider')
  return nilai
}
