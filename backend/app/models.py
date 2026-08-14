from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Indikator(Base):
    __tablename__ = "indikator"
    id_indikator: Mapped[str] = mapped_column(String, primary_key=True)
    kategori: Mapped[str] = mapped_column(String)
    nomor: Mapped[int] = mapped_column(Integer)
    nama_indikator: Mapped[str] = mapped_column(Text)
    nama_asli: Mapped[str | None] = mapped_column(Text)
    kelompok: Mapped[str | None] = mapped_column(Text)
    arah_pembangunan: Mapped[str | None] = mapped_column(Text)
    satuan: Mapped[str | None] = mapped_column(String)
    penghasil: Mapped[str | None] = mapped_column(Text)
    kl_pengampu: Mapped[str | None] = mapped_column(Text)
    opd_penanggung_jawab: Mapped[str | None] = mapped_column(Text)
    tim_pjk: Mapped[str | None] = mapped_column(String)
    status_ketersediaan: Mapped[str | None] = mapped_column(String)
    status_metadata: Mapped[str | None] = mapped_column(String)
    periode_data: Mapped[str | None] = mapped_column(String)
    tahun_terakhir: Mapped[int | None] = mapped_column(Integer)
    is_proxy: Mapped[bool] = mapped_column(Boolean)
    nama_proxy: Mapped[str | None] = mapped_column(Text)
    status_rpjmd: Mapped[str] = mapped_column(String)
    arah_baik: Mapped[str | None] = mapped_column(String)
    arah_baik_terverifikasi: Mapped[bool] = mapped_column(Boolean)
    kode_sdgs: Mapped[str | None] = mapped_column(String)
    link_metadata: Mapped[str | None] = mapped_column(Text)
    link_publikasi: Mapped[str | None] = mapped_column(Text)
    link_data: Mapped[str | None] = mapped_column(Text)
    catatan_teknis: Mapped[str | None] = mapped_column(Text)


class NilaiIndikator(Base):
    __tablename__ = "nilai_indikator"
    id_indikator: Mapped[str] = mapped_column(ForeignKey("indikator.id_indikator"), primary_key=True)
    tahun: Mapped[int] = mapped_column(Integer, primary_key=True)
    jenis: Mapped[str] = mapped_column(String, primary_key=True)
    nilai: Mapped[float | None] = mapped_column(Float)
    sumber_sheet: Mapped[str] = mapped_column(String)


class MetadataIndikator(Base):
    __tablename__ = "metadata_indikator"
    id_indikator: Mapped[str] = mapped_column(ForeignKey("indikator.id_indikator"), primary_key=True)
    definisi: Mapped[str | None] = mapped_column(Text)
    rumus: Mapped[str | None] = mapped_column(Text)
    rumus_mentah: Mapped[str | None] = mapped_column(Text)
    interpretasi: Mapped[str | None] = mapped_column(Text)
    sumber_data: Mapped[str | None] = mapped_column(Text)
    frekuensi: Mapped[str | None] = mapped_column(Text)
    halaman_sumber: Mapped[str | None] = mapped_column(String)
    perlu_verifikasi_manual: Mapped[bool] = mapped_column(Boolean)
    sumber_metadata: Mapped[str | None] = mapped_column(String)
    nama_di_buku1: Mapped[str | None] = mapped_column(Text)
