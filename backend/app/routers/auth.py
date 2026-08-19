"""Endpoint autentikasi: masuk, segarkan sesi, keluar, profil, ganti sandi."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import get_session, id_terautentikasi, pengguna_saat_ini, wajib_peran
from ..repositories import pengguna as repo_pengguna
from ..repositories.pengguna import ProfilPengguna
from ..schemas.auth import ProfilResponse, TokenResponse
from ..schemas.umum import StatusResponse
from ..security import PERAN_INTERNAL
from ..services import auth as svc

router = APIRouter(prefix="/api/v1", tags=["auth"])


def _pasang_cookie_segar(response: Response, token_segar: str) -> None:
    """Token segar hanya hidup di cookie httpOnly, tidak pernah di JavaScript."""
    response.set_cookie(
        svc.NAMA_COOKIE_SEGAR,
        token_segar,
        max_age=settings.refresh_token_ttl_hours * 3600,
        httponly=True,
        samesite="strict",
        secure=settings.is_production,
        path=svc.JALUR_COOKIE_SEGAR,
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(
    request: Request,
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    hasil = svc.masuk(
        session,
        username=form.username,
        password=form.password,
        ip=request.client.host if request.client else None,
    )
    if isinstance(hasil, svc.Ditolak):
        raise HTTPException(hasil.kode, hasil.pesan, headers=hasil.header)
    _pasang_cookie_segar(response, hasil.token_segar)
    return hasil.muatan


@router.post("/auth/refresh", response_model=TokenResponse)
def segarkan(request: Request, response: Response, session: Session = Depends(get_session)) -> dict[str, Any]:
    hasil = svc.segarkan(session, request.cookies.get(svc.NAMA_COOKIE_SEGAR))
    if isinstance(hasil, svc.Ditolak):
        # Cookie yang tidak lagi berlaku dibersihkan supaya peramban tidak
        # terus mengirimkannya pada setiap percobaan berikutnya.
        response.delete_cookie(svc.NAMA_COOKIE_SEGAR, path=svc.JALUR_COOKIE_SEGAR)
        raise HTTPException(hasil.kode, hasil.pesan)
    _pasang_cookie_segar(response, hasil.token_segar)
    return hasil.muatan


@router.post("/auth/logout", response_model=StatusResponse)
def keluar(response: Response, pengguna: ProfilPengguna = Depends(pengguna_saat_ini)) -> dict[str, str]:
    response.delete_cookie(svc.NAMA_COOKIE_SEGAR, path=svc.JALUR_COOKIE_SEGAR)
    svc.catat_peristiwa("keluar", pengguna_id=pengguna.id, hasil="berhasil")
    return {"status": "KELUAR"}


@router.get("/auth/saya", response_model=ProfilResponse)
def profil_saya(pengguna: ProfilPengguna = Depends(pengguna_saat_ini)) -> dict[str, Any]:
    return pengguna._asdict()


@router.post("/auth/ganti-password", response_model=StatusResponse)
def ganti_password(
    password_baru: str = Form(...),
    pengguna: ProfilPengguna = Depends(wajib_peran(*PERAN_INTERNAL)),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    if not svc.password_layak(password_baru):
        raise HTTPException(422, svc.PESAN_PASSWORD_PENDEK)
    akun = repo_pengguna.ambil(session, id_terautentikasi(pengguna))
    if akun is None:
        raise HTTPException(401, "Pengguna tidak aktif")
    return svc.ganti_password(session, akun, password_baru)
