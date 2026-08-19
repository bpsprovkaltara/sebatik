import {useEffect} from 'react'
import {HashRouter, Navigate, Route, Routes, useLocation} from 'react-router-dom'

import {AuthProvider} from './context/AuthContext'
import {ThemeProvider} from './context/ThemeContext'
import {RUTE, alihkanTautanLama} from './lib/rute'
import AdminPage from './pages/AdminPage'
import AnalyticsPage from './pages/AnalyticsPage'
import CapaianPage from './pages/CapaianPage'
import DetailPage from './pages/DetailPage'
import HomePage from './pages/HomePage'
import IndicatorExplorerPage from './pages/IndicatorExplorerPage'
import InsightPage from './pages/InsightPage'
import ValidityPage from './pages/ValidityPage'

/* Pindah halaman selalu kembali ke puncak. Tanpa ini, membuka indikator dari
   posisi gulir tengah membuat halaman baru terbuka di tengah badannya. */
function GulirKeAtas(){
  const {pathname} = useLocation()
  useEffect(() => {scrollTo({top: 0})}, [pathname])
  return null
}

export default function App(){
  /* Tautan lama ('#capaian') dialihkan ke bentuk baru supaya penanda buku yang
     sudah tersebar tidak berujung halaman kosong. Pendengar hashchange ikut
     dipasang karena tautan semacam itu juga bisa diklik dari dalam aplikasi,
     dan pengalihan sekali saat mount tidak akan menangkapnya. */
  useEffect(() => {
    const alihkan = () => {
      const tujuan = alihkanTautanLama()
      if(tujuan) location.replace(`#${tujuan}`)
    }
    alihkan()
    addEventListener('hashchange', alihkan)
    return () => removeEventListener('hashchange', alihkan)
  }, [])

  return (
    <ThemeProvider>
      <AuthProvider>
        <HashRouter>
          <GulirKeAtas/>
          <Routes>
            <Route path={RUTE.beranda} element={<HomePage/>}/>
            <Route path={RUTE.indikator} element={<IndicatorExplorerPage/>}/>
            <Route path={RUTE.capaian} element={<CapaianPage/>}/>
            <Route path={`${RUTE.detail}/:id`} element={<DetailPage/>}/>
            <Route path={RUTE.insight} element={<InsightPage/>}/>
            <Route path={RUTE.validitas} element={<ValidityPage/>}/>
            <Route path={RUTE.analitik} element={<AnalyticsPage/>}/>
            <Route path={RUTE.masuk} element={<AdminPage/>}/>
            <Route path="*" element={<Navigate to={RUTE.beranda} replace/>}/>
          </Routes>
        </HashRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
