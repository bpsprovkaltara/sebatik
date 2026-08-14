export default {
  content:['./index.html','./src/**/*.{js,jsx}'],
  darkMode:['class','[data-theme="dark"]'],
  theme:{extend:{
    fontFamily:{
      sans:['"Plus Jakarta Sans Variable"','ui-sans-serif','system-ui'],
      mono:['"JetBrains Mono Variable"','ui-monospace','monospace']
    },
    colors:{
      /* Tema "Ombak": biru laut sebagai warna utama. Hijau sengaja tidak
         didaftarkan di sini karena statusnya khusus penanda capaian. */
      ocean:{DEFAULT:'#2A78D6',deep:'#16468C',shallow:'#7FB4EC'},
      surf:'#0B8AC0',amber:'#C98200',coral:'#D93F4C',violet:'#6B4BC9',rose:'#E0709B'
    },
    borderRadius:{xl:'18px','2xl':'24px'}
  }},
  plugins:[]
}
