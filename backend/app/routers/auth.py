"""Endpoint autentikasi: masuk, profil, dan ganti kata sandi."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..deps import get_session, id_terautentikasi, pengguna_saat_ini, wajib_peran
from ..repositories import pengguna as repo_pengguna
from ..repositories.pengguna import ProfilPengguna
from ..security import (
    PANJANG_PASSWORD_MINIMUM,
    PERAN_INTERNAL,
    buat_token,
    hash_password,
    password_memenuhi_syarat,
    verifikasi_password,
)

router = APIRouter(prefix="/api/v1", tags=["auth"])

PESAN_PASSWORD_PENDEK = f"Kata sandi minimal {PANJANG_PASSWORD_MINIMUM} karakter"


@router.post("/auth/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    akun = repo_pengguna.ambil_untuk_login(session, form.username)
    # Pesan yang sama untuk username salah dan sandi salah, agar tidak
    # membocorkan username mana yang terdaftar.
    if akun is None or not verifikasi_password(form.password, akun.password_hash):
        raise HTTPException(401, "Username atau kata sandi salah")
    return {
        "access_token": buat_token(akun.id, akun.peran),
        "token_type": "bearer",
        "peran": akun.peran,
        "harus_ganti_password": bool(akun.harus_ganti_password),
    }


@router.get("/auth/saya")
def profil_saya(pengguna: ProfilPengguna = Depends(pengguna_saat_ini)) -> dict[str, Any]:
    return pengguna._asdict()


@router.post("/auth/ganti-password")
def ganti_password(
    password_baru: str = Form(...),
    pengguna: ProfilPengguna = Depends(wajib_peran(*PERAN_INTERNAL)),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    if not password_memenuhi_syarat(password_baru):
        raise HTTPException(422, PESAN_PASSWORD_PENDEK)
    akun = repo_pengguna.ambil(session, id_terautentikasi(pengguna))
    if akun is None:
        raise HTTPException(401, "Pengguna tidak aktif")
    repo_pengguna.ganti_password(akun, hash_password(password_baru), wajib_ganti=False)
    session.commit()
    return {"status": "PASSWORD_DIUBAH"}
