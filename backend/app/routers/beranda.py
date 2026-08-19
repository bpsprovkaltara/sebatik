"""Endpoint beranda: kartu makro, sasaran visi, dan ketersediaan data."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_session
from ..models import KODE_PROVINSI
from ..repositories import wilayah as repo_wilayah
from ..schemas.beranda import BerandaResponse
from ..services import beranda as svc

router = APIRouter(prefix="/api/v1", tags=["beranda"])


@router.get("/beranda", response_model=BerandaResponse)
def beranda(
    tahun: int | None = None,
    wilayah_kode: str = KODE_PROVINSI,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    if not repo_wilayah.ada_dan_aktif(session, wilayah_kode):
        raise HTTPException(422, "Wilayah tidak valid")
    return svc.susun(session, tahun=tahun, wilayah_kode=wilayah_kode)
