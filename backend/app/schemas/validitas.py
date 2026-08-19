"""Skema muatan validitas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .umum import WilayahSingkat


class BuktiRingkas(BaseModel):
    id: int
    nama_file: str | None = None
    mime_type: str | None = None
    ukuran: int | None = None
    diunggah_pada: datetime | None = None


class BarisValiditas(BaseModel):
    id_indikator: str
    kode_indikator: str | None = None
    nama_indikator: str | None = None
    satuan: str | None = None
    instansi_pengampu: str
    validasi: str
    terverifikasi_pada: datetime | None = None
    update: str
    update_oleh: str | None = None
    peran_update: str | None = None
    status_indikator: str
    metadata_tersedia: bool
    usulan_id: int | None = None
    bukti_dukung_jumlah: int
    bukti_dukung: list[BuktiRingkas]


class ValiditasResponse(BaseModel):
    wilayah: WilayahSingkat
    wilayah_opsi: list[WilayahSingkat]
    data: list[BarisValiditas]
    total: int
    status_data: str
