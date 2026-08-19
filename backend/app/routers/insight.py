"""Endpoint insight: kartu makro terbaru dan perbandingan antarwilayah."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_session
from ..models import KODE_PROVINSI
from ..repositories import wilayah as repo_wilayah
from ..schemas.insight import InsightResponse
from ..services import insight as svc

router = APIRouter(prefix="/api/v1", tags=["insight"])


@router.get("/insight", response_model=InsightResponse)
def insight(
    indikator_id: str | None = None,
    wilayah_kode: str = KODE_PROVINSI,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    wilayah = repo_wilayah.ambil_aktif(session, wilayah_kode)
    if wilayah is None:
        raise HTTPException(422, "Wilayah tidak valid")
    return svc.susun(session, wilayah, indikator_id=indikator_id)
