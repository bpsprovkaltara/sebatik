/* ============================================================================
   SEBATIK — Primitif tampilan bersama
   ----------------------------------------------------------------------------
   Berkas ini murni lapisan presentasi. Tidak ada pemanggilan API, tidak ada
   aturan bisnis. Tujuannya membuat setiap halaman memakai kerangka, ritme
   spasi, dan bahasa gerak yang sama.
   ========================================================================== */

import {useEffect,useMemo,useRef,useState} from 'react'
import {Inbox} from 'lucide-react'

const reduceMotion = () =>
  typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

/* --- Reveal saat masuk viewport ------------------------------------------ */
/* Konten muncul saat benar-benar dilihat, bukan sekaligus ketika halaman
   dimuat. Ini menurunkan beban kognitif pada halaman yang panjang. */

/* Ambang bawaan sengaja longgar: sebagian besar blok kecil sebaiknya sudah
   tampil begitu tepinya tersentuh layar. Blok besar — bagian utuh sebuah
   halaman — memakai ambang `SECTION_REVEAL` di bawah, yang menunggu sampai
   bagian itu benar-benar dimasuki, bukan sekadar mengintip di tepi bawah. */
const REVEAL_DEFAULT = {rootMargin: '0px 0px -8% 0px', threshold: 0.06}
export const SECTION_REVEAL = {rootMargin: '0px 0px -22% 0px', threshold: 0}

export function useReveal(options) {
  const ref = useRef(null)
  /* Opsi dibekukan pada pemasangan pertama: ia selalu berupa konstanta modul
     atau literal tetap, dan memasang ulang pengamat tiap render hanya akan
     mengulang animasi yang sudah selesai. */
  const optionsRef = useRef(options)
  useEffect(() => {
    const node = ref.current
    if (!node) return
    if (reduceMotion() || typeof IntersectionObserver === 'undefined') {
      node.classList.add('is-in')
      return
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-in')
            observer.unobserve(entry.target)
          }
        })
      },
      {...REVEAL_DEFAULT, ...optionsRef.current}
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [])
  return ref
}

export function Reveal({as: Tag = 'div', delay = 0, className = '', style, observe, children, ...rest}) {
  const ref = useReveal(observe)
  return (
    <Tag
      ref={ref}
      className={`reveal ${className}`.trim()}
      style={{'--reveal-delay': `${delay}ms`, ...style}}
      {...rest}
    >
      {children}
    </Tag>
  )
}

/* --- Angka yang dihitung naik -------------------------------------------- */
/* Hanya untuk angka sorotan. Tabel dan sumbu tetap statis supaya bisa dibaca
   dan disalin tanpa menunggu animasi selesai. */

export function CountUp({value, duration = 900, decimals = 0, format}) {
  const numeric = typeof value === 'number' && Number.isFinite(value) ? value : null
  const [shown, setShown] = useState(numeric === null ? null : reduceMotion() ? numeric : 0)
  const ref = useRef(null)

  useEffect(() => {
    if (numeric === null) return
    if (reduceMotion()) {
      setShown(numeric)
      return
    }
    let frame = 0
    let started = false
    const run = () => {
      const start = performance.now()
      const step = (now) => {
        const progress = Math.min(1, (now - start) / duration)
        const eased = 1 - Math.pow(1 - progress, 3)
        setShown(numeric * eased)
        if (progress < 1) frame = requestAnimationFrame(step)
      }
      frame = requestAnimationFrame(step)
    }
    const node = ref.current
    if (!node || typeof IntersectionObserver === 'undefined') {
      run()
      return () => cancelAnimationFrame(frame)
    }
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !started) {
          started = true
          run()
          observer.unobserve(entry.target)
        }
      })
    })
    observer.observe(node)
    return () => {
      observer.disconnect()
      cancelAnimationFrame(frame)
    }
  }, [numeric, duration])

  if (numeric === null) return <span ref={ref}>{value}</span>
  const rendered = format
    ? format(shown)
    : shown.toLocaleString('id-ID', {minimumFractionDigits: decimals, maximumFractionDigits: decimals})
  return <span ref={ref}>{rendered}</span>
}

/* --- Kerangka panel ------------------------------------------------------- */

export function SectionHead({kicker, kickerTone, title, desc, actions, level = 2}) {
  const Heading = `h${level}`
  return (
    <div className="section-head">
      <div className="section-head-text">
        {kicker && <span className={`kicker${kickerTone ? ` ${kickerTone}` : ''}`}>{kicker}</span>}
        <Heading>{title}</Heading>
        {desc && <p>{desc}</p>}
      </div>
      {actions && <div className="section-head-actions">{actions}</div>}
    </div>
  )
}

export function Panel({
  kicker,
  kickerTone,
  title,
  desc,
  actions,
  headingLevel = 2,
  className = '',
  bleed = false,
  delay = 0,
  observe,
  children,
  ...rest
}) {
  return (
    <Reveal as="section" delay={delay} observe={observe} className={`panel${bleed ? ' panel-bleed' : ''} ${className}`.trim()} {...rest}>
      {title && (
        <SectionHead
          kicker={kicker}
          kickerTone={kickerTone}
          title={title}
          desc={desc}
          actions={actions}
          level={headingLevel}
        />
      )}
      {children}
    </Reveal>
  )
}

/* --- Keadaan kosong dan memuat -------------------------------------------- */

export function EmptyState({icon: Icon = Inbox, title, desc, compact = false}) {
  return (
    <div className={`empty${compact ? ' is-compact' : ''}`}>
      <span className="empty-icon">
        <Icon size={compact ? 20 : 26} />
      </span>
      <b>{title}</b>
      {desc && <span>{desc}</span>}
    </div>
  )
}

export function Skeleton({height = 16, width = '100%', radius = 8, className = '', style}) {
  return (
    <span
      className={`skeleton ${className}`.trim()}
      style={{height, width, borderRadius: radius, ...style}}
      aria-hidden="true"
    />
  )
}

export function SkeletonCard({lines = 3, height}) {
  return (
    <div className="skeleton-card" aria-hidden="true" style={height ? {height} : undefined}>
      <Skeleton height={38} width={38} radius={12} />
      <Skeleton height={11} width="52%" />
      <Skeleton height={30} width="38%" radius={10} />
      {Array.from({length: Math.max(0, lines - 2)}).map((_, i) => (
        <Skeleton key={i} height={9} width={i % 2 ? '64%' : '78%'} />
      ))}
    </div>
  )
}

export function ChartSkeleton({height = 280}) {
  return (
    <div className="chart-skeleton" style={{height}} aria-hidden="true">
      {[38, 62, 46, 78, 55, 88, 70].map((h, i) => (
        <span key={i} style={{'--h': `${h}%`, '--i': i}} />
      ))}
    </div>
  )
}

/* --- Kartu tooltip Recharts ----------------------------------------------- */
/* Satu bentuk tooltip untuk semua grafik: label periode di atas, lalu tiap
   seri sebagai baris swatch + nama + nilai rata kanan. */

export function TooltipCard({active, payload, label, unit = '', formatter, labelPrefix = ''}) {
  if (!active || !payload || !payload.length) return null
  const rows = payload.filter((row) => row.value !== null && row.value !== undefined)
  if (!rows.length) return null
  return (
    <div className="viz-tooltip" role="tooltip">
      {label !== undefined && label !== null && (
        <span className="viz-tooltip-label">
          {labelPrefix}
          {label}
        </span>
      )}
      <ul>
        {rows.map((row, index) => {
          const rendered = formatter ? formatter(row.value, row) : `${row.value}${unit}`
          return (
            <li key={`${row.dataKey}-${index}`}>
              <i style={{background: row.color || row.stroke || row.fill}} />
              <span>{row.name || row.dataKey}</span>
              <b>{rendered}</b>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

/* --- Legenda ---------------------------------------------------------------
   Untuk >= 2 seri legenda selalu ada, sehingga identitas tidak pernah hanya
   ditanggung warna. */

export function VizLegend({items, className = ''}) {
  return (
    <ul className={`viz-legend ${className}`.trim()}>
      {items.map((item) => (
        <li key={item.label} title={item.hint || undefined}>
          <i style={{background: item.color}} data-shape={item.shape || 'block'} />
          <span>{item.label}</span>
          {item.value !== undefined && <b>{item.value}</b>}
        </li>
      ))}
    </ul>
  )
}

/* --- Gradasi isi area ------------------------------------------------------ */
/* Recharts perlu id unik per gradasi; hook ini menjaganya stabil antar render. */

let gradientSeq = 0
export function useGradientId(prefix = 'grad') {
  return useMemo(() => `${prefix}-${++gradientSeq}`, [prefix])
}

/* --- Chip & pil ------------------------------------------------------------ */

export function Chip({tone = 'neutral', children, ...rest}) {
  return (
    <span className={`chip chip-${tone}`} {...rest}>
      {children}
    </span>
  )
}

export function DeltaPill({direction, children}) {
  const tone = direction === 'up' ? 'up' : direction === 'down' ? 'down' : 'flat'
  const glyph = tone === 'up' ? '▲' : tone === 'down' ? '▼' : '■'
  return (
    <span className={`delta delta-${tone}`}>
      <i aria-hidden="true">{glyph}</i>
      {children}
    </span>
  )
}

/* --- Progress bar baca halaman -------------------------------------------- */

export function ScrollProgress() {
  const [progress, setProgress] = useState(0)
  useEffect(() => {
    const update = () => {
      const scrollable = document.documentElement.scrollHeight - window.innerHeight
      setProgress(scrollable > 0 ? Math.min(1, window.scrollY / scrollable) : 0)
    }
    update()
    window.addEventListener('scroll', update, {passive: true})
    window.addEventListener('resize', update)
    return () => {
      window.removeEventListener('scroll', update)
      window.removeEventListener('resize', update)
    }
  }, [])
  return <span className="scroll-progress" style={{transform: `scaleX(${progress})`}} aria-hidden="true" />
}

/* --- Deteksi halaman tergulir (untuk topbar yang menyusut) ----------------- */

export function useScrolled(threshold = 12) {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const update = () => setScrolled(window.scrollY > threshold)
    update()
    window.addEventListener('scroll', update, {passive: true})
    return () => window.removeEventListener('scroll', update)
  }, [threshold])
  return scrolled
}
