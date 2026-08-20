"""Skema daftar indikator, detail, dan metadata."""

from __future__ import annotations

from pydantic import BaseModel

from .capaian import MuatanCapaian


class IndikatorPublik(BaseModel):
    """Kolom yang boleh keluar lewat daftar publik.

    `opd_penanggung_jawab` adalah nama lama `opd_pengampu` yang dipertahankan
    demi kontrak; lihat `services/indikator.NAMA_LAMA`.
    """

    id_indikator: str
    nama_indikator: str | None = None
    kategori: str | None = None
    kelompok: str | None = None
    satuan: str | None = None
    tim_pjk: str | None = None
    opd_penanggung_jawab: str | None = None
    status_metadata: str | None = None
    tahun_terakhir: int | None = None
    is_proxy: bool | None = None


class DaftarIndikatorResponse(BaseModel):
    data: list[IndikatorPublik]
    total: int
    page: int
    page_size: int


class NilaiRingkas(BaseModel):
    tahun: int
    jenis: str
    nilai: float | None = None
    # Nama lama `sumber_sheet` dipertahankan demi kontrak frontend.
    sumber_sheet: str | None = None


class MetadataTeknis(BaseModel):
    definisi: str | None = None
    rumus_mentah: str | None = None
    interpretasi: str | None = None
    sumber_data: str | None = None
    frekuensi: str | None = None
    halaman_sumber: str | None = None
    sumber_metadata: str | None = None
    perlu_verifikasi_manual: bool | None = None


class DetailIndikatorResponse(MuatanCapaian):
    nilai: list[NilaiRingkas]
    metadata: MetadataTeknis | None = None


class MetadataMaster(BaseModel):
    definisi: str | None = None
    rumus_mentah: str | None = None
    rumus_latex: str | None = None
    # Keterangan notasi rumus: daftar "simbol = arti" yang di Buku 1 tercetak
    # persis di bawah rumusnya. Disimpan satu baris per notasi.
    keterangan_rumus: list[str] = []
    perlu_verifikasi_rumus: bool = False
    halaman_sumber: str | None = None
    interpretasi: str | None = None
    sumber_data: str | None = None
    frekuensi: str | None = None
    status_metadata: str | None = None
    sumber_metadata: str | None = None


class NilaiMaster(BaseModel):
    tahun: int
    jenis: str
    nilai: float | None = None
    nilai_teks: str | None = None
    satuan_catatan: str | None = None


class MetadataResponse(BaseModel):
    id_indikator: str
    kategori: str | None = None
    kode_indikator: str | None = None
    nama_indikator: str | None = None
    kelompok: str | None = None
    arah_pembangunan: str | None = None
    satuan: str | None = None
    opd_pengampu: str | None = None
    status_ketersediaan: str | None = None
    periode_data: str | None = None
    metadata: MetadataMaster | None = None
    metadata_tersedia: bool
    nilai: list[NilaiMaster]


class ArahBaikResponse(BaseModel):
    status: str
    id_indikator: str
    arah_baik: str
