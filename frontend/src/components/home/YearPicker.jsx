import {SmartSelect} from '../ui/SmartSelect'

export function YearPicker({data,year,onYearChange}){
  const years=data?.tahun_tersedia||[]
  /* Tanpa label "Tahun data" di sebelahnya. Isinya sudah berupa tahun, dan
     kicker "Outlook 2025" tepat di seberangnya sudah menyebut tahun yang
     sedang berlaku — labelnya hanya mengulang. */
  return <SmartSelect
    className="year-picker"
    value={year||''}
    onChange={onYearChange}
    options={years.map(x=>({value:String(x),label:String(x)}))}
    ariaLabel="Tahun data yang ditampilkan"
    placeholder={years.length?'Tahun':'Memuat...'}
    disabled={!years.length}
  />
}
