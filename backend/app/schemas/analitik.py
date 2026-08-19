"""Skema muatan analitik."""

from __future__ import annotations

from pydantic import BaseModel


class SelisihTahun(BaseModel):
    tahun: int
    selisih: float
    membaik: bool


class SelisihResponse(BaseModel):
    id_indikator: str
    arah_baik: str | None = None
    data: list[SelisihTahun]


class BarisPeringkat(BaseModel):
    id_indikator: str
    nama_indikator: str | None = None
    arah_baik: str | None = None
    tahun_awal: int
    tahun_akhir: int
    perubahan: float
    skor_perbaikan: float


class PeringkatResponse(BaseModel):
    perbaikan_terbesar: list[BarisPeringkat]
    pemburukan_terbesar: list[BarisPeringkat]


class RealisasiTerakhir(BaseModel):
    tahun: int
    nilai: float


class GapResponse(BaseModel):
    """Dua bentuk dalam satu skema.

    Saat indikator belum punya realisasi, endpoint hanya mengirim `status` dan
    `disclaimer`. Router memakai `response_model_exclude_unset` supaya bentuk
    ringkas itu tidak mendadak dipenuhi kunci bernilai null.
    """

    status: str | None = None
    id_indikator: str | None = None
    realisasi_terakhir: RealisasiTerakhir | None = None
    target_2029: float | None = None
    target_2045: float | None = None
    gap_2029: float | None = None
    gap_2045: float | None = None
    laju_historis: float | None = None
    required_run_rate: float | None = None
    status_jalur: str | None = None
    disclaimer: str


class TitikSeriMulti(BaseModel):
    tahun: int
    jenis: str
    nilai: float | None = None


class SeriIndikator(BaseModel):
    id_indikator: str
    nama: str | None = None
    seri: list[TitikSeriMulti]


class MultiResponse(BaseModel):
    data: list[SeriIndikator]


class TitikKorelasi(BaseModel):
    tahun: int
    x: float
    y: float


class KorelasiResponse(BaseModel):
    n: int
    pearson: float | None = None
    data: list[TitikKorelasi]
    peringatan: str
