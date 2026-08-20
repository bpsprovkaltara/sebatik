"""Skema muatan capaian."""

from __future__ import annotations

from pydantic import BaseModel

from .explorer import IndikatorRingkas
from .umum import WilayahSingkat


class TitikTren(BaseModel):
    tahun: int
    nilai: float | None = None


class MuatanCapaian(BaseModel):
    """Ringkasan capaian satu indikator; dipakai daftar capaian dan detail."""

    id_indikator: str
    nama_indikator: str | None = None
    kategori: str | None = None
    kelompok: str | None = None
    arah_pembangunan: str | None = None
    tim_pjk: str | None = None
    satuan: str | None = None
    arah_baik: str | None = None
    arah_baik_terverifikasi: bool | None = None
    nilai_terakhir: float | None = None
    tahun_terakhir_realisasi: int | None = None
    target_tahun_sama: float | None = None
    persentase_capaian: float | None = None
    status_capaian: str
    tren: list[TitikTren]


class DaftarCapaianResponse(BaseModel):
    data: list[MuatanCapaian]
    total: int
    # Selama `arah_baik` sebagian indikator belum diverifikasi admin, angka
    # capaian di daftar ini belum boleh dibaca sebagai final.
    arah_bersifat_sementara: bool


class PilihanCapaianResponse(BaseModel):
    indikator: list[IndikatorRingkas]
    kelompok: list[str]
    wilayah: list[WilayahSingkat]
    status_data: str


class TitikSeriCapaian(BaseModel):
    tahun: int
    nilai: float | None = None
    nilai_asli: float | None = None
    nilai_teks: str | None = None
    growth: float | None = None
    target: float | None = None
    label_periode: str | None = None


class TitikProyeksi(BaseModel):
    tahun: int
    realisasi: float | None = None
    jalur_target: float | None = None


class DetailCapaianResponse(IndikatorRingkas):
    sumber_data: str | None = None
    frekuensi: str | None = None
    opd_pengampu: str | None = None
    wilayah: WilayahSingkat
    tahun: int | None = None
    tahun_tersedia: list[int]
    series: list[TitikSeriCapaian]
    projection: list[TitikProyeksi]
    nilai_tahun: float | None = None
    nilai_teks: str | None = None
    label_periode: str | None = None
    target_2045: float | None = None
    target_2045_teks: str | None = None
    target_2029: float | None = None
    target_2029_teks: str | None = None
    arah_target: str | None = None
    tahun_target_analisis: int
    progres_2045: float | None = None
    progres_2029: float | None = None
    gap_2045: float | None = None
    gap_2029: float | None = None
    kebutuhan_per_tahun: float | None = None
    insight: str
    status_data: str
    catatan_wilayah: str | None = None
