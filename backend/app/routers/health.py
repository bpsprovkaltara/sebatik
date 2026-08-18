"""Endpoint kesehatan aplikasi."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["sistem"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
