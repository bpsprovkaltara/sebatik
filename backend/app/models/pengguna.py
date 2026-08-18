"""Akun pengguna dan perannya dalam alur tata kelola."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base
from .enums import PERAN


class Pengguna(Base):
    __tablename__ = "pengguna"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    nama: Mapped[str] = mapped_column(String(160), nullable=False)
    # Argon2 lewat pwdlib. Tidak pernah masuk ke respons API — repository
    # memproyeksikan kolom secara eksplisit, bukan SELECT *.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    peran: Mapped[str] = mapped_column(String(20), nullable=False)
    tim_pjk: Mapped[str | None] = mapped_column(String(120))
    wilayah_kode: Mapped[str | None] = mapped_column(ForeignKey("wilayah.kode"))
    aktif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    harus_ganti_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "peran IN (" + ",".join(f"'{item}'" for item in PERAN) + ")",
            name="ck_pengguna_peran",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - bantuan debug
        return f"<Pengguna {self.username} ({self.peran})>"
