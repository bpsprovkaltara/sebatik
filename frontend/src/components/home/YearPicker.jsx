import {ChevronDown} from 'lucide-react'

export function YearPicker({data,year,onYearChange}){
  const years=data?.tahun_tersedia||[]
  /* Tanpa label "Tahun data" di sebelahnya. Isinya sudah berupa tahun, dan
     kicker "Outlook 2025" tepat di seberangnya sudah menyebut tahun yang
     sedang berlaku — labelnya hanya mengulang. */
  return <label className="year-picker" aria-label="Tahun data">
    <span className="year-picker-field">
      <select
        value={year||''}
        onChange={event=>onYearChange(event.target.value)}
        disabled={!years.length}
        aria-label="Pilih tahun data yang ditampilkan"
      >
        {years.length
          ?years.map(option=><option key={option} value={option}>{option}</option>)
          :<option value="">Memuat...</option>}
      </select>
      <ChevronDown size={16} aria-hidden="true"/>
    </span>
  </label>
}
