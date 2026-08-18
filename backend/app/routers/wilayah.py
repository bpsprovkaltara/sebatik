"""Endpoint daftar wilayah."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_session
from ..repositories import wilayah as repo_wilayah
from ..schemas.wilayah import DaftarWilayah, WilayahRingkas

router = APIRouter(prefix="/api/v1", tags=["wilayah"])


@router.get("/wilayah", response_model=DaftarWilayah)
def daftar_wilayah(session: Session = Depends(get_session)) -> DaftarWilayah:
    return DaftarWilayah(data=[WilayahRingkas.model_validate(w) for w in repo_wilayah.daftar_aktif(session)])
