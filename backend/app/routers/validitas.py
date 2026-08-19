"""Endpoint validitas: status verifikasi dan jejak pembaruan tiap indikator."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..deps import get_session, pengguna_saat_ini
from ..models import KODE_PROVINSI
from ..repositories import wilayah as repo_wilayah
from ..repositories.pengguna import ProfilPengguna
from ..schemas.validitas import ValiditasResponse
from ..services import validitas as svc

router = APIRouter(prefix="/api/v1", tags=["validitas"])


@router.get("/validitas", response_model=ValiditasResponse)
def validitas(
    wilayah_kode: str = KODE_PROVINSI,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(svc.BATAS_MAKSIMUM, ge=1, le=svc.BATAS_MAKSIMUM),
    pengguna: ProfilPengguna = Depends(pengguna_saat_ini),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    wilayah = repo_wilayah.ambil_aktif(session, wilayah_kode)
    if wilayah is None:
        raise HTTPException(422, "Wilayah tidak valid")
    return svc.susun(
        session,
        wilayah,
        q=q,
        page=page,
        page_size=page_size,
        peran=pengguna.peran,
        pengguna_id=pengguna.id,
    )
