"""Dimensi indikator, metadatanya, dan satu-satunya tabel fakta nilai.

Konsolidasi sesuai docs/refactoring/model-data.md §3:

- `indikator`          ← `indikator` + `beranda_indikator`
- `metadata_indikator` ← `metadata_indikator` + `beranda_metadata`
- `nilai_indikator`    ← `nilai_indikator` + `nilai_indikator_wilayah`
                         + `beranda_nilai` + `beranda_nilai_periode`
                         + `beranda_nilai_wilayah` + `beranda_nilai_wilayah_periode`
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base
from .enums import JENIS_NILAI, STATUS_VERIFIKASI, JenisNilai, StatusVerifikasi


class Indikator(Base):
    """Satu baris per indikator ISV/IUP (86 baris pada basis data saat ini)."""

    __tablename__ = "indikator"

    id_indikator: Mapped[str] = mapped_column(String(16), primary_key=True)
    kategori: Mapped[str] = mapped_column(String(8), nullable=False)
    nomor: Mapped[int | None] = mapped_column(Integer)
    kode_indikator: Mapped[str | None] = mapped_column(String(32))
    nama_indikator: Mapped[str] = mapped_column(Text, nullable=False)
    nama_asli: Mapped[str | None] = mapped_column(Text)

    # Klasifikasi
    kelompok: Mapped[str | None] = mapped_column(Text)
    arah_pembangunan: Mapped[str | None] = mapped_column(Text)
    sasaran_visi: Mapped[str | None] = mapped_column(Text)
    misi_agenda: Mapped[str | None] = mapped_column(Text)
    arah_ie: Mapped[str | None] = mapped_column(Text)
    indikator_induk: Mapped[str | None] = mapped_column(Text)
    kelompok_makro: Mapped[str | None] = mapped_column(Text)

    satuan: Mapped[str | None] = mapped_column(String(120))

    # Kepemilikan. `opd_pengampu` adalah nama baku, menggantikan
    # `indikator.opd_penanggung_jawab` yang lama.
    penghasil: Mapped[str | None] = mapped_column(Text)
    kl_pengampu: Mapped[str | None] = mapped_column(Text)
    opd_pengampu: Mapped[str | None] = mapped_column(Text)
    tim_pjk: Mapped[str | None] = mapped_column(String(120))

    sumber_data: Mapped[str | None] = mapped_column(Text)
    frekuensi: Mapped[str | None] = mapped_column(Text)

    status_ketersediaan: Mapped[str | None] = mapped_column(String(60))
    status_metadata: Mapped[str | None] = mapped_column(String(60))
    periode_data: Mapped[str | None] = mapped_column(String(60))
    tahun_terakhir: Mapped[int | None] = mapped_column(Integer)

    is_proxy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    nama_proxy: Mapped[str | None] = mapped_column(Text)

    status_rpjmd: Mapped[str | None] = mapped_column(String(40))
    arah_baik: Mapped[str | None] = mapped_column(String(10))
    arah_baik_terverifikasi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Sumber lama tidak hanya menyimpan kode singkat; beberapa baris memuat
    # uraian indikator SDGs lengkap (hingga ratusan karakter).
    kode_sdgs: Mapped[str | None] = mapped_column(Text)
    link_metadata: Mapped[str | None] = mapped_column(Text)
    link_publikasi: Mapped[str | None] = mapped_column(Text)
    link_data: Mapped[str | None] = mapped_column(Text)
    catatan_teknis: Mapped[str | None] = mapped_column(Text)

    sumber_master: Mapped[str | None] = mapped_column(Text)
    status_verifikasi: Mapped[str] = mapped_column(String(24), nullable=False, default=StatusVerifikasi.DISETUJUI)
    diverifikasi_pada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("arah_baik IS NULL OR arah_baik IN ('NAIK','TURUN')", name="ck_indikator_arah_baik"),
        Index("ix_indikator_kategori", "kategori"),
        Index("ix_indikator_kelompok_makro", "kelompok_makro"),
        Index("ix_indikator_status_verifikasi", "status_verifikasi"),
    )

    def __repr__(self) -> str:  # pragma: no cover - bantuan debug
        return f"<Indikator {self.id_indikator}>"


class MetadataIndikator(Base):
    """Kartu metadata per indikator (definisi, rumus, interpretasi)."""

    __tablename__ = "metadata_indikator"

    id_indikator: Mapped[str] = mapped_column(
        ForeignKey("indikator.id_indikator", ondelete="CASCADE"), primary_key=True
    )
    definisi: Mapped[str | None] = mapped_column(Text)
    interpretasi: Mapped[str | None] = mapped_column(Text)
    sumber_data: Mapped[str | None] = mapped_column(Text)
    frekuensi: Mapped[str | None] = mapped_column(Text)
    rumus: Mapped[str | None] = mapped_column(Text)
    rumus_mentah: Mapped[str | None] = mapped_column(Text)
    rumus_latex: Mapped[str | None] = mapped_column(Text)
    halaman_sumber: Mapped[str | None] = mapped_column(String(40))
    perlu_verifikasi_manual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sumber_metadata: Mapped[str | None] = mapped_column(String(120))
    nama_di_buku1: Mapped[str | None] = mapped_column(Text)
    status_metadata: Mapped[str | None] = mapped_column(String(60))


class NilaiIndikator(Base):
    """Satu tabel fakta untuk seluruh nilai indikator.

    Aturan yang membuat enam tabel lama menyatu di sini:

    - `wilayah_kode` selalu terisi; nilai provinsi memakai `'65'`, bukan NULL,
      agar indeks unik tidak perlu memperlakukan NULL secara khusus.
    - `periode` NULL berarti nilai tahunan; 1/2 berarti semester. Nilai periode
      terbaru yang disetujui menggantikan nilai tahunan saat ditampilkan.
    - `usulan_id` terisi bila nilai berasal dari alur verifikasi operator, dan
      NULL bila berasal dari basis data master/ETL.
    """

    __tablename__ = "nilai_indikator"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_indikator: Mapped[str] = mapped_column(ForeignKey("indikator.id_indikator", ondelete="CASCADE"), nullable=False)
    wilayah_kode: Mapped[str] = mapped_column(ForeignKey("wilayah.kode"), nullable=False)
    tahun: Mapped[int] = mapped_column(Integer, nullable=False)
    jenis: Mapped[str] = mapped_column(String(12), nullable=False)
    periode: Mapped[int | None] = mapped_column(Integer)

    # NUMERIC di basis data (presisi eksak sesuai model-data.md §7), tetapi
    # dibaca sebagai float: mengembalikan Decimal akan mengubah bentuk JSON yang
    # sudah dipakai frontend menjadi string.
    nilai: Mapped[float | None] = mapped_column(Numeric(20, 6, asdecimal=False))
    nilai_teks: Mapped[str | None] = mapped_column(Text)
    label_periode: Mapped[str | None] = mapped_column(String(40))
    satuan_catatan: Mapped[str | None] = mapped_column(Text)

    sumber: Mapped[str | None] = mapped_column(Text)
    usulan_id: Mapped[int | None] = mapped_column(ForeignKey("usulan_nilai.id", ondelete="SET NULL"))
    status_verifikasi: Mapped[str] = mapped_column(String(24), nullable=False, default=StatusVerifikasi.DISETUJUI)
    diverifikasi_pada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # Kunci alami dipecah menjadi dua indeks unik parsial, bukan satu
        # UNIQUE biasa: pada SQL, NULL tidak pernah sama dengan NULL, sehingga
        # UNIQUE(..., periode) akan membiarkan nilai tahunan (periode NULL)
        # terduplikasi dan membuat upsert tidak menemukan baris yang ada.
        Index(
            "uq_nilai_indikator_tahunan",
            "id_indikator",
            "wilayah_kode",
            "tahun",
            "jenis",
            unique=True,
            sqlite_where=text("periode IS NULL"),
            postgresql_where=text("periode IS NULL"),
        ),
        Index(
            "uq_nilai_indikator_periodik",
            "id_indikator",
            "wilayah_kode",
            "tahun",
            "jenis",
            "periode",
            unique=True,
            sqlite_where=text("periode IS NOT NULL"),
            postgresql_where=text("periode IS NOT NULL"),
        ),
        CheckConstraint(
            "jenis IN (" + ",".join(f"'{item}'" for item in JENIS_NILAI) + ")",
            name="ck_nilai_indikator_jenis",
        ),
        CheckConstraint(
            "status_verifikasi IN (" + ",".join(f"'{item}'" for item in STATUS_VERIFIKASI) + ")",
            name="ck_nilai_indikator_status",
        ),
        CheckConstraint("periode IS NULL OR periode BETWEEN 1 AND 4", name="ck_nilai_indikator_periode"),
        # Jalur baca terpanas: seri satu indikator untuk satu wilayah.
        Index("ix_nilai_indikator_seri", "id_indikator", "wilayah_kode", "jenis", "tahun"),
        Index("ix_nilai_indikator_tahun", "tahun", "jenis", "status_verifikasi"),
        Index("ix_nilai_indikator_usulan", "usulan_id"),
    )

    @property
    def is_periode(self) -> bool:
        return self.periode is not None

    def __repr__(self) -> str:  # pragma: no cover - bantuan debug
        return (
            f"<NilaiIndikator {self.id_indikator} {self.wilayah_kode} {self.tahun} {self.jenis} periode={self.periode}>"
        )


JENIS_REALISASI = JenisNilai.REALISASI
JENIS_TARGET = JenisNilai.TARGET
