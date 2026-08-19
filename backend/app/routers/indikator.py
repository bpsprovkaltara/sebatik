"""Endpoint daftar indikator, detail, metadata, dan koreksi arah baik."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlalchemy.orm import Session

from ..deps import get_session, wajib_peran
from ..models import Peran
from ..repositories import indikator as repo_indikator
from ..repositories.pengguna import ProfilPengguna
from ..schemas.indikator import (
    ArahBaikResponse,
    DaftarIndikatorResponse,
    DetailIndikatorResponse,
    MetadataResponse,
)
from ..services import indikator as svc

router = APIRouter(prefix="/api/v1", tags=["indikator"])


@router.get("/indikator", response_model=DaftarIndikatorResponse)
def daftar_indikator(
    q: str | None = None,
    kategori: list[str] | None = Query(None),
    kelompok: list[str] | None = Query(None),
    tim: list[str] | None = Query(None),
    metadata: list[str] | None = Query(None),
    sort: str = "id_indikator",
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    return svc.cari(
        session,
        q=q,
        kategori=kategori,
        kelompok=kelompok,
        tim=tim,
        status_metadata=metadata,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )


@router.get("/indikator/{id_indikator}/detail", response_model=DetailIndikatorResponse)
def detail_indikator(id_indikator: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    indikator = repo_indikator.ambil(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan")
    return svc.detail(session, indikator)


@router.get("/beranda-indikator/{id_indikator}/metadata", response_model=MetadataResponse)
def metadata_indikator(id_indikator: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    indikator = repo_indikator.ambil_terverifikasi(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan")
    return svc.metadata_lengkap(session, indikator)


@router.put("/arah-baik/{id_indikator}", response_model=ArahBaikResponse)
def koreksi_arah_baik(
    id_indikator: str,
    arah_baik: str = Form(...),
    pengguna: ProfilPengguna = Depends(wajib_peran(Peran.ADMIN)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    if not svc.arah_baik_sah(arah_baik):
        raise HTTPException(422, "Arah harus NAIK atau TURUN")
    indikator = repo_indikator.ambil(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan")
    return svc.koreksi_arah_baik(session, indikator, arah_baik=arah_baik, pengguna_id=pengguna.id)
