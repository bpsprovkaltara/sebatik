"""Tabel alur tata kelola: usulan, bukti, audit, unggahan massal, snapshot."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base
from .enums import JENIS_NILAI, STATUS_VERIFIKASI, StatusVerifikasi


class UsulanNilai(Base):
    """Antrean verifikasi: OPERATOR/ADMIN mengirim, VERIFIKATOR memutuskan."""

    __tablename__ = "usulan_nilai"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_indikator: Mapped[str] = mapped_column(ForeignKey("indikator.id_indikator"), nullable=False)
    wilayah_kode: Mapped[str | None] = mapped_column(ForeignKey("wilayah.kode"))
    tahun: Mapped[int] = mapped_column(Integer, nullable=False)
    jenis: Mapped[str] = mapped_column(String(12), nullable=False)
    periode: Mapped[int | None] = mapped_column(Integer)
    nilai: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    sumber: Mapped[str] = mapped_column(Text, nullable=False)
    catatan: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(24), nullable=False, default=StatusVerifikasi.MENUNGGU)
    pengusul_id: Mapped[int] = mapped_column(ForeignKey("pengguna.id"), nullable=False)
    verifikator_id: Mapped[int | None] = mapped_column(ForeignKey("pengguna.id"))
    alasan_verifikasi: Mapped[str | None] = mapped_column(Text)

    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    dikirim_pada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    diverifikasi_pada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "jenis IN (" + ",".join(f"'{item}'" for item in JENIS_NILAI) + ")",
            name="ck_usulan_jenis",
        ),
        CheckConstraint(
            "status IN (" + ",".join(f"'{item}'" for item in STATUS_VERIFIKASI) + ")",
            name="ck_usulan_status",
        ),
        CheckConstraint("periode IS NULL OR periode BETWEEN 1 AND 4", name="ck_usulan_periode"),
        Index("ix_usulan_status", "status"),
        Index("ix_usulan_wilayah", "wilayah_kode"),
        Index("ix_usulan_pengusul", "pengusul_id"),
    )


class BuktiDukung(Base):
    """Metadata berkas bukti; isinya tersimpan di filesystem, bukan di basis data."""

    __tablename__ = "bukti_dukung"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usulan_id: Mapped[int] = mapped_column(ForeignKey("usulan_nilai.id", ondelete="CASCADE"), nullable=False)
    nama_file: Mapped[str] = mapped_column(Text, nullable=False)
    path_file: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120))
    ukuran: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    diunggah_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (Index("ix_bukti_usulan", "usulan_id"),)


class LogPerubahan(Base):
    """Jejak audit perubahan nilai/field indikator (append-only)."""

    __tablename__ = "log_perubahan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    waktu: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    pengguna_id: Mapped[int | None] = mapped_column(ForeignKey("pengguna.id"))
    id_indikator: Mapped[str | None] = mapped_column(ForeignKey("indikator.id_indikator"))
    field: Mapped[str] = mapped_column(String(80), nullable=False)
    nilai_lama: Mapped[str | None] = mapped_column(Text)
    nilai_baru: Mapped[str | None] = mapped_column(Text)
    sumber_perubahan: Mapped[str] = mapped_column(String(40), nullable=False)
    referensi_id: Mapped[str | None] = mapped_column(String(40))
    catatan: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_log_perubahan_waktu", "waktu"),)


class LogAktivitas(Base):
    """Jejak audit tindakan administratif (append-only)."""

    __tablename__ = "log_aktivitas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    waktu: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    pengguna_id: Mapped[int | None] = mapped_column(ForeignKey("pengguna.id"))
    aksi: Mapped[str] = mapped_column(String(60), nullable=False)
    objek_tipe: Mapped[str | None] = mapped_column(String(60))
    objek_id: Mapped[str | None] = mapped_column(String(60))
    detail: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_log_aktivitas_waktu", "waktu"),)


class UnggahanExcel(Base):
    """Arsip unggahan Excel massal beserta ringkasan diff-nya."""

    __tablename__ = "unggahan_excel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nama_file_asli: Mapped[str] = mapped_column(Text, nullable=False)
    path_arsip: Mapped[str] = mapped_column(Text, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    ringkasan_diff: Mapped[str | None] = mapped_column(Text)
    pengguna_id: Mapped[int | None] = mapped_column(ForeignKey("pengguna.id"))
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    disetujui_pada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SnapshotKetersediaan(Base):
    """Riwayat status ketersediaan per indikator per tanggal."""

    __tablename__ = "snapshot_ketersediaan"

    id_indikator: Mapped[str] = mapped_column(
        ForeignKey("indikator.id_indikator", ondelete="CASCADE"), primary_key=True
    )
    tanggal_snapshot: Mapped[str] = mapped_column(String(10), primary_key=True)
    status: Mapped[str] = mapped_column(String(60), nullable=False)


class PenugasanPic(Base):
    """Nama PIC perorangan. Data pribadi — tidak pernah diekspos endpoint publik."""

    __tablename__ = "penugasan_pic"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_indikator: Mapped[str] = mapped_column(ForeignKey("indikator.id_indikator", ondelete="CASCADE"), nullable=False)
    jenis_pic: Mapped[str] = mapped_column(String(40), nullable=False)
    nama_pic: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (Index("ix_penugasan_pic_indikator", "id_indikator"),)
