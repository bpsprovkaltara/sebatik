"""Skema unggahan Excel massal."""

from __future__ import annotations

from pydantic import BaseModel


class NilaiBerubah(BaseModel):
    id: str
    tahun: int
    jenis: str
    lama: float | None = None
    baru: float | None = None


class DiffUnggahan(BaseModel):
    indikator_baru: list[str]
    indikator_hilang: list[str]
    nilai_berubah: list[NilaiBerubah]


class PratinjauResponse(BaseModel):
    id: int
    diff: DiffUnggahan
