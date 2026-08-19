"""Potongan skema yang dipakai lintas domain."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WilayahSingkat(BaseModel):
    """Wilayah sebagaimana disematkan di dalam muatan halaman."""

    model_config = ConfigDict(from_attributes=True)

    kode: str
    nama: str
    tingkat: str


class StatusResponse(BaseModel):
    """Tanggapan tindakan yang hanya melaporkan hasilnya."""

    status: str
