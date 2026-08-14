import React from 'react'
import {createRoot} from 'react-dom/client'
/* Montserrat memikul antarmuka dan judul. Angka, kode indikator, dan isi tabel
   tidak memakainya — lihat --font-num di styles.css. */
import '@fontsource-variable/montserrat'
/* Hanya dipakai untuk kata SEBATIK di beranda — satu berat, satu tempat. */
import '@fontsource/yeseva-one'
import App from './App'
import './styles.css'
createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>)
