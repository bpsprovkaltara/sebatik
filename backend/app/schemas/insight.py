"""Skema muatan insight."""

from __future__ import annotations

from pydantic import BaseModel

from .umum import WilayahSingkat


class KartuInsight(BaseModel):
    id_indikator: str
    kode_indikator: str | None = None
    nama_indikator: str | None = None
    kelompok: str | None = None
    satuan: str | None = None
    sumber_data: str | None = None
    opd_pengampu: str | None = None
    tahun: int | None = None
    label_periode: str | None = None
    nilai: float | None = None
    nilai_teks: str | None = None
    perubahan: float | None = None
    status: str


class TitikSeriInsight(BaseModel):
    tahun: int
    nilai: float | None = None
    nilai_teks: str | None = None
    growth: float | None = None


class PerbandinganWilayah(WilayahSingkat):
    nilai: float | None = None
    nilai_teks: str | None = None
    status: str


class InsightResponse(BaseModel):
    tahun_sistem: int
    wilayah: WilayahSingkat
    wilayah_opsi: list[WilayahSingkat]
    indikator_makro: list[KartuInsight]
    indikator_aktif: KartuInsight | None = None
    series: list[TitikSeriInsight]
    perbandingan_wilayah: list[PerbandinganWilayah]
    status_data: str
    catatan_wilayah: str | None = None
