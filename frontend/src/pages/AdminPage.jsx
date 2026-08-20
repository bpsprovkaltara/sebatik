import {RUTE} from '../lib/rute'
import {clearToken, roleLabel, setToken, useToken} from '../auth'
import * as endpoints from '../api/endpoints'
import {EmptyState, Panel, Reveal, SectionHead} from '../ui'
import {SmartSelect} from '../components/ui/SmartSelect'
import {CheckCircle2, Eye, EyeOff, FileWarning, Info} from 'lucide-react'
import {useEffect, useState} from 'react'
import {OperatorFlow} from '../components/admin/OperatorFlow'
import {PasswordResetModal} from '../components/admin/PasswordResetModal'
import {SubmissionTable} from '../components/admin/SubmissionTable'
import {LoginShell} from '../components/layout/LoginShell'
import {Shell} from '../components/layout/Shell'
import {usePageTitle} from '../hooks/usePageTitle'
import {dateText} from '../lib/format'

export default function AdminPage(){
  const token=useToken()
  const [me,setMe]=useState(null),
    [regions,setRegions]=useState([]),[catalog,setCatalog]=useState([]),[users,setUsers]=useState([]),
    [submissions,setSubmissions]=useState([]),[logs,setLogs]=useState([]),[message,setMessage]=useState(''),
    [evidence,setEvidence]=useState(null),[accountRole,setAccountRole]=useState('OPERATOR'),
    [messageTone,setMessageTone]=useState('warning'),[showPassword,setShowPassword]=useState(false),[passwordUser,setPasswordUser]=useState(null),
    [draft,setDraft]=useState({id_indikator:'',tahun:new Date().getFullYear(),periode:'',nilai:'',sumber:'',catatan:''})

  /* Pesan ruang kerja punya dua nada. `warning` untuk yang perlu dibaca ulang —
     kegagalan, sesi habis, berkas tidak terbuka. `success` untuk tindakan yang
     benar-benar selesai, ditandai centang hijau supaya operator tahu kirimannya
     sudah masuk tanpa harus membaca kalimatnya. */
  const notify=(text,tone='warning')=>{setMessage(text);setMessageTone(tone)}
  const notifyOk=text=>notify(text,'success')

  /* Dipanggil di sini, sebelum cabang-cabang keluar di bawah, supaya urutan
     hook tetap sama pada tiap render — halaman ini punya tiga keadaan (belum
     masuk, memeriksa sesi, ruang kerja) dan ketiganya keluar lebih awal. */
  usePageTitle(token?`Login ${roleLabel(me?.peran)}`:'Login')

  const refresh=async()=>{
    if(!token)return
    try{
      const profile=await endpoints.profilSaya()
      const [regionData,catalogData]=await Promise.all([endpoints.wilayah(),endpoints.capaianExplorer()])
      setMe(profile);setRegions(regionData.data);setCatalog(catalogData.indikator)
      const queue=await endpoints.daftarUsulan()
      setSubmissions(queue.data||[])
      if(profile.peran==='ADMIN'){
        const [accountData,logData]=await Promise.all([endpoints.daftarPengguna(),endpoints.logAudit()])
        setUsers(accountData.data);setLogs(logData.data)
      }
    }catch{
      /* client.js sudah membersihkan token pada 401; halaman tinggal
         mengosongkan tampilannya. */
      notify('Sesi berakhir. Silakan login kembali.')
      clearToken();setMe(null)
    }
  }

  /* Keluar kini bisa dipicu dari bilah atas, jadi halaman ini harus ikut
     membersihkan dirinya saat token hilang — bukan hanya saat tombol di
     dalamnya yang ditekan. */
  useEffect(()=>{
    if(token)refresh()
    else{setMe(null);setSubmissions([]);setUsers([]);setLogs([]);setEvidence(null)}
  },[token])

  const login=async event=>{
    event.preventDefault()
    const form=new FormData(event.currentTarget)
    try{
      const result=await endpoints.login(
        new URLSearchParams({username:form.get('username'),password:form.get('password')})
      )
      setToken(result.access_token)
      notifyOk('Login berhasil.')
    }catch(error){
      /* 429 berarti pembatas laju; pesannya sudah jelas dari server. */
      notify(error.detail||error.message||'Login gagal')
    }
  }

  const loadEvidence=async submission=>{
    try{
      const result=await endpoints.buktiUsulan(submission.id)
      setEvidence({submission,files:result.data})
    }catch(error){notify(error.message)}
  }

  const openEvidence=async file=>{
    const response=await endpoints.berkasBukti(evidence.submission.id,file.id)
    if(!response.ok){notify('File bukti tidak dapat dibuka.');return}
    const url=URL.createObjectURL(await response.blob())
    window.open(url,'_blank','noopener,noreferrer')
    setTimeout(()=>URL.revokeObjectURL(url),60000)
  }

  const decide=async(submission,decision)=>{
    let reason=null
    if(decision==='DITOLAK'){reason=prompt('Tuliskan alasan penolakan');if(!reason)return}
    const body=new FormData()
    body.set('keputusan',decision)
    if(reason)body.set('alasan',reason)
    try{
      const result=await endpoints.verifikasiUsulan(submission.id,body)
      notifyOk(`Usulan ${result.status.toLowerCase()}.`)
      refresh()
    }catch(error){notify(error.message)}
  }

  if(!token)return <LoginShell>
    <form className="panel role-login" onSubmit={login}>
      <div className="login-head">
        <img className="login-logo" src="/logo-sebatik-monitoring.png" alt="Logo SEBATIK"/>
        <h1>Masuk ke SEBATIK</h1>
        <p>Dasbor Pemantauan Ketersediaan Data ISV-IUP</p>
        <p className="login-org">BPS Provinsi Kalimantan Utara</p>
      </div>

      {message&&<p className="form-error" role="alert">{message}</p>}

      <label className="login-field">
        <span>Nama Pengguna</span>
        <input name="username" autoComplete="username" placeholder="Nama pengguna terdaftar" required autoFocus/>
      </label>

      <label className="login-field">
        <span>Kata Sandi</span>
        {/* Tombol mata duduk di dalam bingkai isian, bukan di sebelahnya, supaya
            lebar kolomnya tetap sama dengan isian di atasnya. */}
        <span className="login-secret">
          <input
            name="password"
            type={showPassword?'text':'password'}
            autoComplete="current-password"
            placeholder="Kata sandi"
            required
          />
          <button
            type="button"
            className="login-peek"
            onClick={()=>setShowPassword(v=>!v)}
            title={showPassword?'Sembunyikan kata sandi':'Tampilkan kata sandi'}
            aria-label={showPassword?'Sembunyikan kata sandi':'Tampilkan kata sandi'}
            aria-pressed={showPassword}
          >
            {showPassword?<EyeOff size={18}/>:<Eye size={18}/>}
          </button>
        </span>
      </label>

      <button className="login-submit">Masuk</button>

      <div className="login-foot">
        <p>Akses terbatas untuk admin dan walidata.</p>
        <p>Belum punya akun? Hubungi Tim Nerwilis BPS Kaltara.</p>
      </div>
    </form>
  </LoginShell>

  if(!me)return <LoginShell>
    <div className="panel role-login session-loading">
      <b>Memeriksa sesi login</b>
      <span>Mohon tunggu sebentar...</span>
    </div>
  </LoginShell>


  const submitValue=async event=>{
    event.preventDefault()
    try{
      const result=await endpoints.kirimUsulan(new FormData(event.currentTarget))
      notifyOk(`Usulan #${result.id} dikirim untuk verifikasi.`)
      setDraft({id_indikator:'',tahun:new Date().getFullYear(),periode:'',nilai:'',sumber:'',catatan:''})
      event.currentTarget.reset()
      refresh()
    }catch(error){notify(error.message)}
  }

  const createAccount=async event=>{
    event.preventDefault()
    try{
      const result=await endpoints.buatPengguna(new FormData(event.currentTarget))
      notifyOk(`Akun ${result.username} dibuat.`)
      event.currentTarget.reset()
      refresh()
    }catch(error){notify(error.message)}
  }

  const toggleAccount=async user=>{
    const body=new FormData()
    body.set('aktif',String(!user.aktif))
    try{await endpoints.ubahStatusPengguna(user.id,body);refresh()}
    catch(error){notify(error.message)}
  }

  const resetPassword=async value=>{
    const body=new FormData()
    body.set('password_baru',value)
    try{
      await endpoints.resetPassword(passwordUser.id,body)
      setPasswordUser(null)
      notifyOk('Kata sandi direset dan wajib diganti saat login.')
    }catch(error){notify(error.message)}
  }

  /* Ruang kerja tidak memakai pita kepala halaman. Identitas dan peran sudah
     terbaca di bilah atas, dan pita biru setinggi 300px hanya mendorong isian
     yang justru jadi alasan orang membuka halaman ini. `bare` melewatinya. */
  /* Judul tab sudah dipasang usePageTitle di atas, jadi Shell tidak diberi
     `title` di sini — kalau diberi, ia akan menimpanya dengan nilai yang sama
     lewat jalur kedua. */
  return <Shell active={RUTE.masuk} bare>
    {message&&<div className={`notice ${messageTone}`}>
      {messageTone==='success'?<CheckCircle2 size={17}/>:<Info size={17}/>}
      {message}
    </div>}

    {me?.peran==='ADMIN'&&<>
      <section className="workspace-grid">
        <Reveal as="form" className="panel role-form" onSubmit={createAccount}>
          <SectionHead
            kicker="Manajemen akses"
            title="Tambahkan pengguna"
            desc="Operator dapat ditempatkan di provinsi atau kabupaten/kota. Verifikator hanya di provinsi."
          />
          <input name="username" placeholder="Username" required/>
          <input name="nama" placeholder="Nama lengkap" required/>
          <input name="password" type="password" placeholder="Kata sandi awal (min. 12 karakter)" required/>
          <select name="peran" value={accountRole} onChange={e=>setAccountRole(e.target.value)}>
            <option>OPERATOR</option><option>VERIFIKATOR</option><option>ADMIN</option>
          </select>
          {accountRole!=='ADMIN'&&(accountRole==='VERIFIKATOR'
            ?<><input type="hidden" name="wilayah_kode" value="65"/><div className="locked-field">Provinsi Kalimantan Utara</div></>
            :<SmartSelect
              name="wilayah_kode"
              options={regions.map(x=>({value:x.kode,label:x.nama}))}
              ariaLabel="Wilayah operator"
              placeholder="Pilih wilayah operator"
            />)}
          <button>Buat akun</button>
        </Reveal>

        <Reveal as="section" delay={60} className="panel role-summary">
          <span className="kicker">Ringkasan akses</span>
          <h2>{users.length} akun terdaftar</h2>
          <div className="role-counts">
            {['ADMIN','OPERATOR','VERIFIKATOR'].map(role=>
              <div key={role}><b>{users.filter(u=>u.peran===role).length}</b><span>{role}</span></div>
            )}
          </div>
          <p>Admin dapat membuat akun, mengubah status aktif, mereset kata sandi, melihat bukti, dan memantau antrean.</p>
        </Reveal>
      </section>

      <Panel delay={40} kicker="Pengguna" title="Daftar akun dan akses">
        <div className="table-scroll">
          <table className="workspace-table">
            <thead><tr><th>Pengguna</th><th>Role</th><th>Wilayah</th><th>Status</th><th>Aksi</th></tr></thead>
            <tbody>
              {users.map(user=>
                <tr key={user.id}>
                  <td><b>{user.nama}</b><small>{user.username}</small></td>
                  <td>{user.peran}</td>
                  <td>{user.wilayah||'Seluruh wilayah'}</td>
                  <td><span className={`indicator-state ${user.aktif?'tersedia':'belum-tersedia'}`}>{user.aktif?'Aktif':'Nonaktif'}</span></td>
                  <td>
                    <div className="row-actions">
                      <button onClick={()=>toggleAccount(user)}>{user.aktif?'Nonaktifkan':'Aktifkan'}</button>
                      <button onClick={()=>setPasswordUser(user)}>Reset password</button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </>}

    {me?.peran==='OPERATOR'&&
      <section className="workspace-grid operator-grid">
        <Reveal as="form" className="panel role-form" onSubmit={submitValue}>
          <SectionHead
            kicker="Input realisasi"
            title="Kirim data indikator"
            desc="Koreksi angka dibuat sebagai usulan baru agar riwayat lama tidak hilang."
          />
          <input type="hidden" name="jenis" value="realisasi"/>
          <SmartSelect
            name="id_indikator"
            value={draft.id_indikator}
            onChange={value=>setDraft({...draft,id_indikator:value})}
            options={catalog.map(x=>({value:x.id_indikator,label:x.nama_indikator,code:x.kode_indikator}))}
            ariaLabel="Indikator yang dikirim"
            placeholder="Pilih indikator"
            emptyText="Tidak ada indikator yang cocok"
          />
          <div className="form-pair">
            <input name="tahun" type="number" min="2000" max="2045" value={draft.tahun} onChange={e=>setDraft({...draft,tahun:e.target.value})} required/>
            <select name="periode" value={draft.periode} onChange={e=>setDraft({...draft,periode:e.target.value})}>
              <option value="">Tahunan / tidak berkala</option>
              <option value="1">Semester 1</option>
              <option value="2">Semester 2</option>
            </select>
          </div>
          <div className="form-pair">
            <input name="nilai" type="number" step="any" value={draft.nilai} onChange={e=>setDraft({...draft,nilai:e.target.value})} placeholder="Nilai realisasi" required/>
            <input name="sumber" value={draft.sumber} onChange={e=>setDraft({...draft,sumber:e.target.value})} placeholder="Sumber/instansi pemberi data" required/>
          </div>
          <small className="form-hint">Untuk indikator semesteran, kirim Semester 1 dan Semester 2 sebagai dua usulan. Dashboard otomatis memakai semester terakhir yang telah disetujui.</small>
          <textarea name="catatan" value={draft.catatan} onChange={e=>setDraft({...draft,catatan:e.target.value})} placeholder="Catatan atau alasan koreksi"/>
          <label className="file-field">
            <span>Bukti dukung wajib</span>
            <input name="bukti" type="file" accept=".pdf,.jpg,.jpeg,.png,.xlsx" multiple required/>
            <small>Surat permintaan, balasan OPD, publikasi, atau dokumen pendukung. Maksimal 10 MB/file.</small>
          </label>
          <button>Kirim untuk disetujui</button>
        </Reveal>

        <Reveal as="section" delay={60} className="panel role-summary">
          <span className="kicker">Alur operator</span>
          <h2>Input → bukti → verifikasi</h2>
          <OperatorFlow/>
        </Reveal>
      </section>}

    {(me?.peran==='VERIFIKATOR'||me?.peran==='ADMIN')&&
      <Panel
        delay={40}
        className="verification-queue"
        kicker="Antrean verifikasi"
        title="Data masuk dari seluruh wilayah"
        desc="Periksa angka, sumber, dan bukti sebelum mengambil keputusan."
        actions={<span className="count-pill">{submissions.filter(x=>x.status==='MENUNGGU_VERIFIKASI').length} menunggu</span>}
      >
        <SubmissionTable rows={submissions} canDecide={me?.peran==='VERIFIKATOR'} onEvidence={loadEvidence} onDecision={decide}/>
      </Panel>}

    {me?.peran==='OPERATOR'&&
      <Panel delay={40} kicker="Riwayat usulan" title="Status data yang pernah dikirim">
        <SubmissionTable
          rows={submissions}
          onEvidence={loadEvidence}
          onCorrect={row=>{
            setDraft({
              id_indikator:row.id_indikator,tahun:row.tahun,periode:row.periode||'',nilai:row.nilai,sumber:row.sumber,
              catatan:`Koreksi usulan #${row.id}: ${row.alasan_verifikasi||''}`
            })
            scrollTo({top:300,behavior:'smooth'})
          }}
        />
      </Panel>}

    {me?.peran==='ADMIN'&&
      <Panel delay={40} kicker="Audit nilai" title="Jejak perubahan terverifikasi">
        <div className="table-scroll">
          <table className="workspace-table">
            <thead>
              <tr><th>Waktu</th><th>Pengguna</th><th>Indikator</th><th>Nilai lama</th><th>Nilai baru</th><th>Sumber</th></tr>
            </thead>
            <tbody>
              {logs.map(row=>
                <tr key={row.id}>
                  <td>{dateText(row.waktu)}</td>
                  <td>{row.username||'sistem'}</td>
                  <td>{row.id_indikator}</td>
                  <td>{row.nilai_lama??'—'}</td>
                  <td>{row.nilai_baru??'—'}</td>
                  <td>{row.sumber_perubahan}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>}

    {evidence&&
      <div className="evidence-modal" role="dialog" aria-modal="true" onClick={()=>setEvidence(null)}>
        <div onClick={e=>e.stopPropagation()}>
          <header>
            <div>
              <span>Bukti dukung usulan #{evidence.submission.id}</span>
              <h3>{evidence.submission.id_indikator} · {evidence.submission.wilayah}</h3>
            </div>
            <button onClick={()=>setEvidence(null)} aria-label="Tutup">×</button>
          </header>
          {evidence.files.length
            ?evidence.files.map(file=>
              <button className="evidence-file" key={file.id} onClick={()=>openEvidence(file)}>
                <Eye size={18}/>
                <span><b>{file.nama_file}</b><small>{Math.ceil(file.ukuran/1024)} KB · {file.mime_type}</small></span>
              </button>)
            :<EmptyState icon={FileWarning} compact title="Belum ada bukti dukung"/>}
        </div>
      </div>}
    {passwordUser&&<PasswordResetModal user={passwordUser} onClose={()=>setPasswordUser(null)} onSubmit={resetPassword}/>}
  </Shell>
}

/* ==========================================================================
   Router
   ========================================================================== */
