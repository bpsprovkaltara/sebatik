"""Query terhadap akun pengguna.

Aturan penting: `password_hash` tidak pernah ikut dalam proyeksi yang berujung
ke respons API. Fungsi yang memerlukannya (`ambil_untuk_login`) diberi nama
eksplisit agar pemakaiannya mudah diaudit.
"""

from __future__ import annotations

from typing import NamedTuple

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from ..models import Pengguna, Wilayah


class ProfilPengguna(NamedTuple):
    """Bentuk aman untuk dikirim ke klien — tanpa hash kata sandi."""

    # None hanya untuk profil tamu (lihat deps.TAMU); akun nyata selalu punya id.
    id: int | None
    username: str
    nama: str
    peran: str
    tim_pjk: str | None
    wilayah_kode: str | None
    harus_ganti_password: bool


def _aktif(stmt: Select) -> Select:
    return stmt.where(Pengguna.aktif.is_(True))


def ambil(session: Session, pengguna_id: int) -> Pengguna | None:
    return session.get(Pengguna, pengguna_id)


def ambil_aktif(session: Session, pengguna_id: int) -> Pengguna | None:
    stmt = _aktif(select(Pengguna).where(Pengguna.id == pengguna_id))
    return session.scalars(stmt).first()


def ambil_untuk_login(session: Session, username: str) -> Pengguna | None:
    """Satu-satunya jalur yang sengaja membaca `password_hash`."""
    stmt = _aktif(select(Pengguna).where(Pengguna.username == username))
    return session.scalars(stmt).first()


def profil(pengguna: Pengguna) -> ProfilPengguna:
    return ProfilPengguna(
        id=pengguna.id,
        username=pengguna.username,
        nama=pengguna.nama,
        peran=pengguna.peran,
        tim_pjk=pengguna.tim_pjk,
        wilayah_kode=pengguna.wilayah_kode,
        harus_ganti_password=pengguna.harus_ganti_password,
    )


def daftar_dengan_wilayah(session: Session) -> list[tuple[Pengguna, str | None]]:
    """Daftar akun untuk panel admin, disertai nama wilayahnya."""
    stmt = (
        select(Pengguna, Wilayah.nama)
        .join(Wilayah, Wilayah.kode == Pengguna.wilayah_kode, isouter=True)
        .order_by(Pengguna.peran, Wilayah.kode, Pengguna.username)
    )
    return [(baris[0], baris[1]) for baris in session.execute(stmt)]


def buat(
    session: Session,
    *,
    username: str,
    nama: str,
    password_hash: str,
    peran: str,
    tim_pjk: str | None = None,
    wilayah_kode: str | None = None,
) -> Pengguna:
    pengguna = Pengguna(
        username=username,
        nama=nama,
        password_hash=password_hash,
        peran=peran,
        tim_pjk=tim_pjk,
        wilayah_kode=wilayah_kode,
        harus_ganti_password=True,
    )
    session.add(pengguna)
    return pengguna


def ganti_password(pengguna: Pengguna, password_hash: str, *, wajib_ganti: bool) -> None:
    pengguna.password_hash = password_hash
    pengguna.harus_ganti_password = wajib_ganti
