"""Skema muatan penjelajah indikator."""

from __future__ import annotations

from pydantic import BaseModel

from .umum import WilayahSingkat


class IndikatorRingkas(BaseModel):
    id_indikator: str
    kategori: str | None = None
    kelompok: str | None = None
    arah_pembangunan: str | None = None
    kode_indikator: str | None = None
    nama_indikator: str | None = None
    satuan: str | None = None


class KelompokIndikator(BaseModel):
    kelompok: str
    jumlah: int
    indikator: list[IndikatorRingkas]


class ExplorerResponse(BaseModel):
    data: list[KelompokIndikator]
    total_indikator: int
    status_data: str


class TitikLiniMasa(BaseModel):
    tahun: int
    realisasi: float | None = None
    realisasi_teks: str | None = None
    target: float | None = None
    target_teks: str | None = None
    growth: float | None = None
    label_periode: str | None = None


class NilaiWilayah(WilayahSingkat):
    tahun: int | None = None
    nilai: float | None = None
    nilai_teks: str | None = None
    target: float | None = None
    target_teks: str | None = None
    status: str


class ExplorerDetailResponse(IndikatorRingkas):
    sumber_data: str | None = None
    frekuensi: str | None = None
    opd_pengampu: str | None = None
    tahun: int | None = None
    tahun_tersedia: list[int]
    series: list[TitikLiniMasa]
    wilayah: list[NilaiWilayah]
    status_data: str
    catatan_wilayah: str | None = None
