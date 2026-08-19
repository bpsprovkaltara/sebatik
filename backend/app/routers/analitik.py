"""Endpoint analitik: selisih tahunan, peringkat, gap target, multi-seri, korelasi."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..deps import get_session
from ..repositories import indikator as repo_indikator
from ..schemas.analitik import (
    GapResponse,
    KorelasiResponse,
    MultiResponse,
    PeringkatResponse,
    SelisihResponse,
)
from ..services import Penolakan
from ..services import analitik as svc

router = APIRouter(prefix="/api/v1", tags=["analitik"])


@router.get("/analitik/selisih/{id_indikator}", response_model=SelisihResponse)
def selisih_tahunan(id_indikator: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    return svc.muatan_selisih(session, id_indikator)


@router.get("/analitik/peringkat", response_model=PeringkatResponse)
def peringkat(session: Session = Depends(get_session)) -> dict[str, Any]:
    return svc.muatan_peringkat(session)


@router.get(
    "/analitik/gap/{id_indikator}",
    response_model=GapResponse,
    # Indikator tanpa realisasi hanya mengirim status dan disclaimer;
    # kunci lain tidak boleh mendadak muncul bernilai null.
    response_model_exclude_unset=True,
)
def gap(id_indikator: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    indikator = repo_indikator.ambil(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan")
    return svc.muatan_gap(session, indikator)


@router.get("/analitik/multi", response_model=MultiResponse)
def multi(ids: list[str] = Query(...), session: Session = Depends(get_session)) -> dict[str, Any]:
    hasil = svc.muatan_multi(session, ids)
    if isinstance(hasil, Penolakan):
        raise HTTPException(hasil.kode, hasil.pesan)
    return hasil


@router.get("/analitik/korelasi", response_model=KorelasiResponse)
def korelasi(x: str, y: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    return svc.muatan_korelasi(session, x, y)
