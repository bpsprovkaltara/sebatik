"""Endpoint penjelajah indikator: pengelompokan dan lini masa per indikator."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_session
from ..repositories import indikator as repo_indikator
from ..schemas.explorer import ExplorerDetailResponse, ExplorerResponse
from ..services import explorer as svc

router = APIRouter(prefix="/api/v1", tags=["explorer"])


@router.get("/indikator-explorer", response_model=ExplorerResponse)
def daftar_explorer(session: Session = Depends(get_session)) -> dict[str, Any]:
    return svc.daftar(session)


@router.get("/indikator-explorer/{id_indikator}", response_model=ExplorerDetailResponse)
def detail_explorer(
    id_indikator: str,
    tahun: int | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    indikator = repo_indikator.ambil_terverifikasi(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan atau belum diverifikasi")
    return svc.detail(session, indikator, tahun=tahun)
