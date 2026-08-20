"""Skema muatan beranda."""

from __future__ import annotations

from pydantic import BaseModel

from .umum import WilayahSingkat  # noqa: F401  (dipakai domain lain lewat modul ini)


class KelompokKerangka(BaseModel):
    nama: str
    jumlah_indikator: int
    id_indikator: list[str]


class KetersediaanKelompok(BaseModel):
    kode: str
    label: str
    jumlah_kelompok: int
    jumlah_indikator: int
    slot_terisi: int
    slot_total: int
    persentase: float
    kelompok: list[KelompokKerangka]


class RingkasanKategori(BaseModel):
    terisi: int
    total: int
    persentase: float


class KetersediaanTahunan(BaseModel):
    tahun: int
    terisi: int
    total: int
    persentase: float
    isv: RingkasanKategori
    iup: RingkasanKategori


class IndikatorMakro(BaseModel):
    id_indikator: str
    nama_indikator: str | None = None
    arah_pembangunan: str | None = None
    kode_indikator: str | None = None
    satuan: str | None = None
    tahun: int | None = None
    nilai: float | None = None
    nilai_teks: str | None = None
    target: float | None = None
    target_teks: str | None = None
    perubahan: float | None = None
    arah_perubahan: str | None = None
    keterangan: str | None = None
    label_periode: str | None = None


class SasaranVisi(BaseModel):
    id_indikator: str
    kode_indikator: str | None = None
    nama_indikator: str | None = None
    arah_pembangunan: str | None = None
    satuan: str | None = None
    tahun: int | None = None
    nilai: float | None = None
    nilai_teks: str | None = None
    target: float | None = None
    target_teks: str | None = None
    keterangan: str | None = None
    label_periode: str | None = None


class BerandaResponse(BaseModel):
    tahun: int | None = None
    wilayah_kode: str
    tahun_tersedia: list[int]
    indikator_makro: list[IndikatorMakro]
    sasaran_visi: list[SasaranVisi]
    ketersediaan_tahunan: list[KetersediaanTahunan]
    ketersediaan_kelompok: list[KetersediaanKelompok]
    status_data: str
