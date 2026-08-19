import {useEffect, useState} from 'react'

/* ============================================================================
   Pengambilan data per halaman
   ----------------------------------------------------------------------------
   Menggantikan pola useEffect berulang yang sebelumnya ditulis ulang di tiap
   halaman, termasuk penanganan "komponen sudah dilepas sebelum jawaban datang"
   yang mudah terlupa dan menimbulkan pembaruan state pada komponen mati.
   ========================================================================== */
export function useFetch(muat, deps = [], {aktif = true} = {}){
  const [data, setData] = useState(null)
  const [galat, setGalat] = useState('')
  const [memuat, setMemuat] = useState(aktif)

  useEffect(() => {
    if(!aktif){setMemuat(false); return}
    let dibatalkan = false
    setMemuat(true)
    muat()
      .then(hasil => {if(!dibatalkan){setData(hasil); setGalat('')}})
      .catch(error => {if(!dibatalkan) setGalat(error.message)})
      .finally(() => {if(!dibatalkan) setMemuat(false)})
    return () => {dibatalkan = true}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return {data, galat, memuat, setData, setGalat}
}
