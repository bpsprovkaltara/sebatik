import {CheckCircle2, Eye, EyeOff, KeyRound, X} from 'lucide-react'
import {useEffect, useState} from 'react'

export function PasswordResetModal({user,onClose,onSubmit}){
  const [value,setValue]=useState(''),[visible,setVisible]=useState(false),[saving,setSaving]=useState(false)
  const valid=value.length>=12

  useEffect(()=>{
    const close=event=>event.key==='Escape'&&!saving&&onClose()
    addEventListener('keydown',close)
    return()=>removeEventListener('keydown',close)
  },[onClose,saving])

  const submit=async event=>{
    event.preventDefault()
    if(!valid)return
    setSaving(true)
    try{await onSubmit(value)}finally{setSaving(false)}
  }

  return <div className="password-modal-backdrop" onMouseDown={event=>event.target===event.currentTarget&&!saving&&onClose()}>
    <form className="password-modal" role="dialog" aria-modal="true" aria-labelledby="password-modal-title" onSubmit={submit}>
      <header>
        <span className="password-modal-icon"><KeyRound size={21}/></span>
        <div>
          <small>Keamanan akun</small>
          <h2 id="password-modal-title">Atur ulang kata sandi</h2>
          <p>Buat kata sandi awal baru untuk <b>{user.nama}</b> ({user.username}). Pengguna wajib menggantinya saat login.</p>
        </div>
        <button type="button" className="password-modal-close" onClick={onClose} disabled={saving} aria-label="Tutup"><X size={19}/></button>
      </header>
      <label className="password-modal-field">
        <span>Kata sandi baru</span>
        <span className="password-modal-secret">
          <input autoFocus type={visible?'text':'password'} value={value} onChange={event=>setValue(event.target.value)} minLength={12} autoComplete="new-password" placeholder="Minimal 12 karakter" required/>
          <button type="button" onClick={()=>setVisible(current=>!current)} aria-label={visible?'Sembunyikan kata sandi':'Tampilkan kata sandi'}>{visible?<EyeOff size={18}/>:<Eye size={18}/>}</button>
        </span>
      </label>
      <div className={`password-rule ${valid?'is-valid':''}`}><CheckCircle2 size={15}/><span>{valid?'Kata sandi memenuhi syarat':`${value.length}/12 karakter minimum`}</span></div>
      <footer>
        <button type="button" className="password-cancel" onClick={onClose} disabled={saving}>Batal</button>
        <button type="submit" className="password-save" disabled={!valid||saving}>{saving?'Menyimpan...':'Simpan kata sandi'}</button>
      </footer>
    </form>
  </div>
}
