/* ============================================================================
   SEBATIK — Elemen identitas visual
   ----------------------------------------------------------------------------
   Tiga lapis identitas Kalimantan Utara:
   1. Laut Sulawesi   -> gradasi biru pada logo dan aura latar
   2. Fajar perbatasan-> aksen amber pada garis ombak
   3. Motif kawung    -> tekstur batik bertingkat opacity rendah
   ========================================================================== */

let uid = 0
const nextId = (prefix) => `${prefix}-${++uid}`

export function Logo({size = 40, animated = true}) {
  const g = nextId('logo'), s = nextId('shine')
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      role="img"
      aria-label="Logo SEBATIK"
      className={animated ? 'brand-logo is-animated' : 'brand-logo'}
    >
      <defs>
        <linearGradient id={g} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#FEBE98" />
          <stop offset=".55" stopColor="#DF7F83" />
          <stop offset="1" stopColor="#7E3F49" />
        </linearGradient>
        <linearGradient id={s} x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#fff" stopOpacity=".35" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="13" fill={`url(#${g})`} />
      <rect width="40" height="40" rx="13" fill={`url(#${s})`} />
      <g fill="#5E2E36" fillOpacity=".82">
        <rect className="logo-bar" x="10" y="20" width="4.4" height="8" rx="2.2" />
        <rect className="logo-bar" x="17.8" y="15" width="4.4" height="13" rx="2.2" />
      </g>
      <rect className="logo-bar" x="25.6" y="10" width="4.4" height="18" rx="2.2" fill="#FFFFFF" fillOpacity=".95" />
      <path
        className="logo-wave"
        d="M8 31.4c3-1.9 5.4 1.4 8.2-.2 2.8-1.6 4.6 1.5 7.4.1 2.8-1.4 4.6 1.3 8.4-.6"
        stroke="#F0CFBA"
        strokeWidth="2.1"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  )
}

/* Motif kawung. Dipakai hanya pada permukaan hero dan panggung login supaya
   tetap terbaca sebagai identitas, bukan derau visual di seluruh halaman. */
export function BatikLayer({opacity = .14, scale = 54, drift = false}) {
  const p = nextId('batik')
  return (
    <svg
      className={drift ? 'batik-layer is-drifting' : 'batik-layer'}
      style={{opacity}}
      aria-hidden="true"
    >
      <defs>
        <pattern id={p} width={scale} height={scale} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <g fill="none" stroke="currentColor" strokeWidth="1.15">
            <ellipse cx={scale * .25} cy={scale * .5} rx={scale * .222} ry={scale * .137} />
            <ellipse cx={scale * .75} cy={scale * .5} rx={scale * .222} ry={scale * .137} />
            <ellipse cx={scale * .5} cy={scale * .25} rx={scale * .137} ry={scale * .222} />
            <ellipse cx={scale * .5} cy={scale * .75} rx={scale * .137} ry={scale * .222} />
          </g>
          <circle cx={scale * .5} cy={scale * .5} r="1.7" fill="currentColor" />
          <circle cx="0" cy="0" r="1.7" fill="currentColor" />
          <circle cx={scale} cy={scale} r="1.7" fill="currentColor" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${p})`} />
    </svg>
  )
}

/* Aura gradasi yang bergerak sangat lambat di belakang hero — memberi kesan
   arus laut tanpa mengganggu keterbacaan teks di atasnya. */
export function AuroraField() {
  return (
    <div className="aurora" aria-hidden="true">
      <span className="aurora-orb orb-a" />
      <span className="aurora-orb orb-b" />
      <span className="aurora-orb orb-c" />
    </div>
  )
}

/* Pembatas ombak antara hero dan badan halaman. Dua lapis dengan fase
   berbeda supaya tepinya terbaca sebagai gelombang bertumpuk, bukan satu
   garis lengkung datar. */
export function WaveEdge() {
  return (
    <svg className="wave-edge" viewBox="0 0 1440 56" preserveAspectRatio="none" aria-hidden="true">
      <path
        className="wave-back"
        d="M0 30c150-20 300-18 450 2s300 18 450-2 270-16 420 4 120 12 120 12V56H0Z"
      />
      <path
        className="wave-front"
        d="M0 34c140-22 280-22 420 0s280 22 420 0 280-22 420 0 180 22 180 22V56H0Z"
      />
    </svg>
  )
}

/* Pembatas ombak berjalan di antara bagian halaman.

   Bedanya dengan WaveEdge di atas: yang itu menutup tepi bawah hero dan diam;
   yang ini berdiri sendiri sebagai pemisah antar-bagian dan bergerak terus.
   Tiap lapis digambar dua kali berdampingan lalu digeser sejauh separuh
   lebarnya — begitu geseran selesai, gambarnya kembali persis seperti semula,
   jadi putarannya tidak pernah terlihat menyambung.

   Dua lapis dipakai dengan laju dan arah berlawanan supaya puncaknya saling
   silang; satu lapis saja akan terbaca sebagai gambar yang digeser, bukan air
   yang bergerak.

   Dua ragam pemakaian, karena tiap bentuk punya masalah tepi sendiri:

   `band`  — ombak menjadi batas warna sungguhan. Sisi terisinya memakai warna
             bidang yang menyusul di baliknya, jadi lengkungan itulah tepi
             bidang tersebut; tidak ada garis lurus tersisa karena memang tidak
             ada apa pun di bawah lengkungan selain bidang yang sama.

   `soft`  — ombak hias yang mengambang di atas latar halaman. Di sini sisi
             terisinya justru masalah: ia berakhir rata di kaki bingkai dan
             terbaca sebagai pita lurus. Karena itu ragam ini diluruhkan dengan
             mask gradasi sehingga isinya menghilang sebelum sampai ke tepi. */
/* Bentuk ombaknya dibangkitkan, bukan digambar tangan.

   Versi tangan sebelumnya memakai satu deret kurva dengan panjang gelombang
   yang hampir seragam dan amplitudo kecil di dalam bingkai setinggi 40px:
   hasilnya lengkungan sopan yang terbaca sebagai garis berlekuk, bukan air.
   Yang membuat air terlihat hidup adalah beberapa gelombang berbeda panjang
   yang saling menumpuk — jadi di sini tiga lapis dibangkitkan dari setengah
   gelombang yang sama-sama membagi habis 1440, masing-masing dengan panjang,
   tinggi, dan garis dasar sendiri.

   `q` disusul rangkaian `t`: tiap `t` mencerminkan titik kendali sebelumnya,
   sehingga puncak dan lembahnya menyambung mulus seperti sinus, bukan patah di
   titik temu. Karena setengah gelombangnya membagi habis lebar bingkai, dua
   salinan berdampingan tetap menyambung saat digeser separuh — itulah yang
   membuat putarannya tidak pernah terlihat menyambung. */
const wavePath = (half, amp, base) => {
  const steps = 1440 / half
  let d = `M0 ${base} q ${half / 2} ${-amp} ${half} 0`
  for (let i = 1; i < steps; i++) d += ` t ${half} 0`
  return `${d} V120 H0 Z`
}

/* Panjang gelombang mengecil dari belakang ke depan supaya lapis terdepan
   terbaca sebagai riak yang lebih dekat ke mata. */
const WAVE_LAYERS = [
  {key: 'back', d: wavePath(240, 34, 48)},
  {key: 'mid', d: wavePath(180, 26, 62)},
  {key: 'front', d: wavePath(144, 20, 76)}
]

export function WaveDivider({flip = false, tone = 'soft'}) {
  return (
    <div className={`wave-divider${flip ? ' is-flipped' : ''}`} data-tone={tone} aria-hidden="true">
      <svg viewBox="0 0 1440 120" preserveAspectRatio="none">
        {WAVE_LAYERS.map((layer) => (
          <g className={`wave-layer wave-layer-${layer.key}`} key={layer.key}>
            {/* Lapis dalam mengayun naik-turun pelan. Ia dipisahkan dari lapis
                luar yang menggeser mendatar karena keduanya sama-sama memakai
                `transform` — ditumpuk pada satu elemen, yang belakangan akan
                membatalkan yang pertama. */}
            <g className="wave-sway">
              <path d={layer.d} />
              <path d={layer.d} transform="translate(1440 0)" />
            </g>
          </g>
        ))}
      </svg>
    </div>
  )
}
