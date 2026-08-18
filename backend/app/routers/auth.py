"""Endpoint autentikasi: masuk, profil, dan ganti kata sandi."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
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
from ..services.pembatas import kunci_percobaan, pembatas_login

router = APIRouter(prefix="/api/v1", tags=["auth"])
# Peristiwa auth dicatat tanpa kata sandi, hanya identitas dan hasilnya.
log = logging.getLogger("sebatik.auth")

PESAN_PASSWORD_PENDEK = f"Kata sandi minimal {PANJANG_PASSWORD_MINIMUM} karakter"


@router.post("/auth/login")
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    kunci = kunci_percobaan(request.client.host if request.client else None, form.username)
    keputusan = pembatas_login.periksa(kunci)
    if not keputusan.diizinkan:
        raise HTTPException(
            429,
            "Terlalu banyak percobaan masuk. Coba lagi beberapa saat lagi.",
            headers={"Retry-After": str(keputusan.sisa_detik)},
        )

    akun = repo_pengguna.ambil_untuk_login(session, form.username)
    # Pesan yang sama untuk username salah dan sandi salah, agar tidak
    # membocorkan username mana yang terdaftar.
    if akun is None or not verifikasi_password(form.password, akun.password_hash):
        log.warning("Percobaan masuk gagal untuk username=%s", form.username)
        raise HTTPException(401, "Username atau kata sandi salah")

    # Percobaan yang berhasil tidak boleh ikut menghabiskan jatah pengguna sah.
    pembatas_login.lupakan(kunci)
    log.info("Masuk berhasil untuk pengguna_id=%s peran=%s", akun.id, akun.peran)
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
