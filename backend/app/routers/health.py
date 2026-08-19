"""Endpoint kesehatan aplikasi."""

from __future__ import annotations

from fastapi import APIRouter

from ..schemas.sistem import KesehatanResponse

router = APIRouter(prefix="/api/v1", tags=["sistem"])


@router.get("/health", response_model=KesehatanResponse)
def health() -> dict[str, str]:
    return {"status": "ok"}
