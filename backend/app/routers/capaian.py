"""Endpoint capaian: daftar ringkas dan penelusuran progres per indikator."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_session
from ..models import KODE_PROVINSI
from ..repositories import indikator as repo_indikator
from ..repositories import wilayah as repo_wilayah
from ..schemas.capaian import DaftarCapaianResponse, DetailCapaianResponse, PilihanCapaianResponse
from ..services import capaian as svc
from ..services import explorer as svc_explorer

router = APIRouter(prefix="/api/v1", tags=["capaian"])


@router.get("/capaian", response_model=DaftarCapaianResponse)
def daftar_capaian(
    kategori: str | None = None,
    kelompok: str | None = None,
    arah_pembangunan: str | None = None,
    tim: str | None = None,
    status_capaian: str | None = None,
    wilayah_kode: str | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    if wilayah_kode and not repo_wilayah.ada_dan_aktif(session, wilayah_kode):
        raise HTTPException(422, "Wilayah tidak valid")
    return svc.daftar(
        session,
        wilayah_kode=wilayah_kode or KODE_PROVINSI,
        kategori=kategori,
        kelompok=kelompok,
        arah_pembangunan=arah_pembangunan,
        tim=tim,
        status_capaian=status_capaian,
    )


@router.get("/capaian-explorer", response_model=PilihanCapaianResponse)
def pilihan_capaian(session: Session = Depends(get_session)) -> dict[str, Any]:
    return svc_explorer.pilihan_capaian(session)


@router.get("/capaian-explorer/{id_indikator}", response_model=DetailCapaianResponse)
def detail_capaian(
    id_indikator: str,
    tahun: int | None = None,
    wilayah_kode: str = KODE_PROVINSI,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    indikator = repo_indikator.ambil_terverifikasi(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan atau belum diverifikasi")
    wilayah = repo_wilayah.ambil_aktif(session, wilayah_kode)
    if wilayah is None:
        raise HTTPException(422, "Wilayah tidak valid")
    return svc.detail(session, indikator, wilayah, tahun=tahun)
