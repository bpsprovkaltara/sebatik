"""Skema wilayah."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WilayahRingkas(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kode: str
    nama: str
    tingkat: str
    parent_kode: str | None = None


class DaftarWilayah(BaseModel):
    data: list[WilayahRingkas]
