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
