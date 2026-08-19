"""Skema alur usulan nilai dan bukti dukung."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .validitas import BuktiRingkas


class UsulanDibuatResponse(BaseModel):
    status: str
    id: int
    jumlah_bukti: int


class BarisUsulan(BaseModel):
    id: int
    id_indikator: str
    wilayah_kode: str | None = None
    tahun: int
    jenis: str
    periode: int | None = None
    nilai: float | None = None
    sumber: str | None = None
    catatan: str | None = None
    status: str
    pengusul_id: int | None = None
    verifikator_id: int | None = None
    alasan_verifikasi: str | None = None
    dibuat_pada: datetime | None = None
    dikirim_pada: datetime | None = None
    diverifikasi_pada: datetime | None = None
    pengusul: str | None = None
    peran_pengusul: str | None = None
    wilayah: str | None = None
    verifikator: str | None = None
    jumlah_bukti: int


class DaftarUsulanResponse(BaseModel):
    data: list[BarisUsulan]


class BuktiLengkap(BuktiRingkas):
    checksum_sha256: str | None = None


class DaftarBuktiResponse(BaseModel):
    data: list[BuktiLengkap]
