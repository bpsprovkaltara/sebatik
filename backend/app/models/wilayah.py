"""Dimensi wilayah: provinsi Kalimantan Utara dan lima kabupaten/kota."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base

# Satu-satunya definisi kode akar. Menggantikan literal "65" yang tersebar di
# router, service, dan query lama.
KODE_PROVINSI = "65"


class Wilayah(Base):
    __tablename__ = "wilayah"

    kode: Mapped[str] = mapped_column(String(10), primary_key=True)
    nama: Mapped[str] = mapped_column(String(120), nullable=False)
    tingkat: Mapped[str] = mapped_column(String(20), nullable=False)
    # Provinsi menjadi akar hierarki sehingga parent_kode-nya NULL.
    parent_kode: Mapped[str | None] = mapped_column(ForeignKey("wilayah.kode"))
    aktif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:  # pragma: no cover - bantuan debug
        return f"<Wilayah {self.kode} {self.nama}>"
