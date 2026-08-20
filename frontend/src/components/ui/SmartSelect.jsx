import {createPortal} from 'react-dom'
import {Check, ChevronDown, Search} from 'lucide-react'
import {useEffect, useLayoutEffect, useMemo, useRef, useState} from 'react'

/* Jumlah pilihan minimum sebelum kotak pencarian ikut ditampilkan. */
const SEARCH_FROM = 7
const POPUP_MIN = 220
const POPUP_MAX = 340
/* Jarak aman dari tepi layar. */
const EDGE = 10

const terms = (query) => query.trim().toLowerCase().split(/\s+/).filter(Boolean)
const haystack = (option) => `${option.label} ${option.code || ''} ${option.hint || ''}`.toLowerCase()
const escapeRe = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

/* Bagian yang cocok ditebalkan supaya mata tahu mengapa satu baris tersisa
   setelah disaring — tanpa penanda ini daftar hasil terbaca seperti daftar
   acak yang lebih pendek. */
function Highlight({text, query}) {
  const words = terms(query)
  if (!words.length) return text
  const parts = String(text).split(new RegExp(`(${words.map(escapeRe).join('|')})`, 'ig'))
  return parts.map((part, i) => (words.includes(part.toLowerCase()) ? <mark key={i}>{part}</mark> : part))
}

export function SmartSelect({
  value,
  defaultValue = '',
  options = [],
  onChange,
  name,
  placeholder = 'Pilih...',
  ariaLabel,
  searchPlaceholder = 'Ketik untuk mencari...',
  emptyText = 'Tidak ada yang cocok',
  className = '',
  searchable,
  disabled = false
}) {
  /* Dua cara pakai: terkendali (halaman menyimpan nilainya) dan mandiri
     (formulir membacanya lewat <input type="hidden">). */
  const managed = value !== undefined
  const [own, setOwn] = useState(defaultValue)
  const current = managed ? value : own

  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const [box, setBox] = useState(null)

  const rootRef = useRef(null)
  const popupRef = useRef(null)
  const inputRef = useRef(null)
  const buttonRef = useRef(null)
  const typeBufferRef = useRef('')
  const typedAtRef = useRef(0)

  const selected = options.find((x) => String(x.value) === String(current))
  const withSearch = searchable ?? options.length >= SEARCH_FROM

  const list = useMemo(() => {
    const words = terms(query)
    if (!words.length) return options
    const hits = options.filter((option) => words.every((word) => haystack(option).includes(word)))
    /* Yang diawali kata kuncinya naik ke atas: mengetik "pdrb" seharusnya
       memunculkan "PDRB per Kapita" lebih dulu, bukan indikator lain yang
       kebetulan menyebut PDRB di ekor namanya. */
    const head = words[0]
    return hits.sort(
      (a, b) =>
        Number(String(b.label).toLowerCase().startsWith(head)) -
        Number(String(a.label).toLowerCase().startsWith(head))
    )
  }, [options, query])

  const place = () => {
    const node = rootRef.current
    if (!node) return
    const rect = node.getBoundingClientRect()
    const below = innerHeight - rect.bottom - 14
    const above = rect.top - 14
    /* Menu jatuh ke atas hanya kalau ruang di bawah benar-benar sempit dan
       ruang di atas lebih lega — bukan setiap kali ada sedikit kekurangan. */
    const up = below < POPUP_MIN && above > below
    /* Menu selalu selebar pemicunya, tetapi tidak pernah lebih sempit dari
       POPUP_MIN — nama indikator tidak muat pada kotak selebar "2025". Pada
       pemicu sempit di tepi kanan halaman, pelebaran itu membuat menunya
       menjulur keluar layar; karena itu tepi kirinya ditarik masuk secukupnya
       sehingga ia berakhir rata kanan dengan pemicunya, bukan terpotong. */
    const width = Math.max(rect.width, POPUP_MIN)
    setBox({
      left: Math.max(EDGE, Math.min(rect.left, innerWidth - width - EDGE)),
      width,
      top: up ? undefined : rect.bottom + 6,
      bottom: up ? innerHeight - rect.top + 6 : undefined,
      height: Math.min(POPUP_MAX, Math.max(POPUP_MIN, (up ? above : below) - 6))
    })
  }

  useLayoutEffect(() => {
    if (open) place()
  }, [open])

  useEffect(() => {
    if (!open) return
    const outside = (event) => {
      if (!rootRef.current?.contains(event.target) && !popupRef.current?.contains(event.target)) setOpen(false)
    }
    addEventListener('scroll', place, true)
    addEventListener('resize', place)
    addEventListener('pointerdown', outside)
    return () => {
      removeEventListener('scroll', place, true)
      removeEventListener('resize', place)
      removeEventListener('pointerdown', outside)
    }
  }, [open])

  /* Saat menu dibuka, sorotan berdiri di pilihan yang sedang berlaku supaya
     panah bawah melanjutkan dari sana, bukan mengulang dari puncak daftar. */
  useEffect(() => {
    if (!open) return
    setActive(Math.max(0, list.findIndex((x) => String(x.value) === String(current))))
    const target = withSearch ? inputRef.current : popupRef.current
    target?.focus({preventScroll: true})
  }, [open])

  useEffect(() => {
    if (open) setActive(0)
  }, [query])

  useEffect(() => {
    if (open) popupRef.current?.querySelector('[data-active="true"]')?.scrollIntoView({block: 'nearest'})
  }, [active, open])

  const close = () => {
    setOpen(false)
    setQuery('')
    typeBufferRef.current = ''
    buttonRef.current?.focus({preventScroll: true})
  }

  const choose = (next) => {
    if (!managed) setOwn(next)
    onChange?.(next)
    close()
  }

  /* Type-ahead untuk menu tanpa kotak pencarian. Ketikan yang berjarak dekat
     dirangkai (I lalu N menjadi "in"); setelah jeda, huruf berikutnya memulai
     pencarian baru. Daftarnya menyempit tanpa menambah isian pencarian. */
  const typeAhead = (key) => {
    const now = Date.now()
    const next = now - typedAtRef.current < 900 ? `${typeBufferRef.current}${key}` : key
    typedAtRef.current = now
    typeBufferRef.current = next
    setQuery(next)
    setOpen(true)
  }

  const onPopupKey = (event) => {
    const step = event.key === 'ArrowDown' ? 1 : event.key === 'ArrowUp' ? -1 : 0
    if (step) {
      event.preventDefault()
      if (list.length) setActive((i) => (i + step + list.length) % list.length)
    } else if (event.key === 'Home') {
      event.preventDefault()
      setActive(0)
    } else if (event.key === 'End') {
      event.preventDefault()
      setActive(Math.max(0, list.length - 1))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      if (list[active]) choose(list[active].value)
    } else if (event.key === 'Escape') {
      event.preventDefault()
      close()
    } else if (event.key === 'Tab') {
      setOpen(false)
    } else if (!withSearch && event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault()
      typeAhead(event.key)
    }
  }

  /* Dari tombol yang masih tertutup: huruf apa pun langsung membuka menu dan
     menjadi ketikan pertama — kebiasaan <select> bawaan, tetapi menyaring
     daftarnya alih-alih melompat ke huruf awal. */
  const onControlKey = (event) => {
    if (open) return
    if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      setOpen(true)
    } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      typeAhead(event.key)
    }
  }

  const popup = (
    <div
      className="smart-select-popup"
      ref={popupRef}
      tabIndex={-1}
      onKeyDown={onPopupKey}
      style={{
        left: box?.left,
        width: box?.width,
        top: box?.top,
        bottom: box?.bottom,
        '--popup-height': `${box?.height || POPUP_MAX}px`
      }}
    >
      {withSearch && (
        <div className="smart-select-search">
          <Search size={15} aria-hidden="true" />
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={searchPlaceholder}
            aria-label={`Cari pada ${ariaLabel || 'daftar pilihan'}`}
          />
        </div>
      )}

      <ul className="smart-select-list" role="listbox" aria-label={ariaLabel}>
        {list.map((option, i) => (
          <li key={option.value}>
            <button
              type="button"
              role="option"
              aria-selected={String(option.value) === String(current)}
              data-active={i === active}
              className={String(option.value) === String(current) ? 'is-selected' : ''}
              onMouseMove={() => setActive(i)}
              onClick={() => choose(option.value)}
            >
              {option.code && <i>{option.code}</i>}
              <span>
                <Highlight text={option.label} query={query} />
                {option.hint && <small>{option.hint}</small>}
              </span>
              <Check size={15} aria-hidden="true" />
            </button>
          </li>
        ))}
        {!list.length && <li className="smart-select-empty">{emptyText}</li>}
      </ul>
    </div>
  )

  return (
    <div className={`smart-select${open ? ' is-open' : ''} ${className}`.trim()} ref={rootRef}>
      {name && <input type="hidden" name={name} value={current ?? ''} />}
      <button
        type="button"
        ref={buttonRef}
        className="smart-select-control"
        onClick={() => setOpen((x) => !x)}
        onKeyDown={onControlKey}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        disabled={disabled || !options.length}
      >
        <span className={selected ? '' : 'is-placeholder'}>{selected ? selected.label : placeholder}</span>
        <ChevronDown size={16} aria-hidden="true" />
      </button>
      {open && typeof document !== 'undefined' && createPortal(popup, document.body)}
    </div>
  )
}
