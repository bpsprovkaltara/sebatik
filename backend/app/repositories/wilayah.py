"""Query terhadap dimensi wilayah."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import KODE_PROVINSI, Wilayah


def daftar_aktif(session: Session) -> list[Wilayah]:
    """Semua wilayah aktif, provinsi lebih dulu lalu kab/kota menurut kode."""
    stmt = select(Wilayah).where(Wilayah.aktif.is_(True)).order_by(func.length(Wilayah.kode), Wilayah.kode)
    return list(session.scalars(stmt))


def daftar_anak_provinsi(session: Session) -> list[Wilayah]:
    """Lima kabupaten/kota di bawah provinsi."""
    stmt = select(Wilayah).where(Wilayah.parent_kode == KODE_PROVINSI, Wilayah.aktif.is_(True)).order_by(Wilayah.kode)
    return list(session.scalars(stmt))


def ambil_aktif(session: Session, kode: str) -> Wilayah | None:
    stmt = select(Wilayah).where(Wilayah.kode == kode, Wilayah.aktif.is_(True))
    return session.scalars(stmt).first()


def ada_dan_aktif(session: Session, kode: str | None) -> bool:
    return bool(kode) and ambil_aktif(session, str(kode)) is not None
