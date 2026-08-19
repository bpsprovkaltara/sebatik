"""Skema administrasi akun dan audit."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AkunRingkas(BaseModel):
    id: int
    username: str
    nama: str
    peran: str
    wilayah_kode: str | None = None
    wilayah: str | None = None
    tim_pjk: str | None = None
    aktif: bool
    harus_ganti_password: bool


class DaftarAkunResponse(BaseModel):
    data: list[AkunRingkas]


class BarisLogPerubahan(BaseModel):
    id: int
    waktu: datetime | None = None
    pengguna_id: int | None = None
    id_indikator: str | None = None
    field: str | None = None
    nilai_lama: str | None = None
    nilai_baru: str | None = None
    sumber_perubahan: str | None = None
    referensi_id: str | None = None
    catatan: str | None = None
    username: str | None = None


class LogResponse(BaseModel):
    data: list[BarisLogPerubahan]


class PenggunaDibuatResponse(BaseModel):
    status: str
    username: str
