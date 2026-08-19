import {AuroraField, BatikLayer, WaveDivider, WaveEdge} from '../../Brand'
import {SiteFooter} from '../../components/layout/SiteFooter'
import {Topbar} from '../../components/layout/Topbar'
import {usePageTitle} from '../../hooks/usePageTitle'

export function Shell({active,title,subtitle,bare=false,children}){
  usePageTitle(title)

  if(bare)return <div className="app">
    <div className="shell">
      <Topbar active={active}/>
      <main className="bare-main">{children}</main>
    </div>
    <SiteFooter/>
  </div>

  return <div className="app">
    <div className="shell">
      <Topbar active={active}/>
      <header className="hero">
        <AuroraField/>
        <BatikLayer opacity={.09} drift/>
        {/* Kalimat ini adalah judul halaman yang sebenarnya — karena itu ia
            tetap <h1>, meski tampil sebagai kalimat pengantar, bukan label.
            `key` membuat React memasang ulang simpulnya tiap kali kalimatnya
            berganti, jadi animasi masuknya ikut berjalan lagi saat pindah
            halaman — sementara aurora dan batik di belakangnya tidak ikut
            direset karena berada di luar simpul ini. */}
        <h1 className="hero-lead" key={subtitle}>{subtitle}</h1>
        <WaveEdge/>
      </header>
      {/* Jeda berjalan antara pita kepala dan isi halaman, sama seperti yang
          memisahkan bagian-bagian di beranda — supaya kedua jenis halaman
          memakai bahasa peralihan yang sama. */}
      <WaveDivider tone="soft"/>
      <main>{children}</main>
    </div>
    <SiteFooter/>
  </div>
}
