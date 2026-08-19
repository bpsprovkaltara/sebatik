"""Dependency FastAPI: sesi basis data, pengguna saat ini, dan pembatas peran."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Peran
from .repositories import pengguna as repo_pengguna
from .repositories.pengguna import ProfilPengguna
from .security import TokenTidakValid, baca_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# Profil untuk permintaan tanpa token. Endpoint publik memakai ini agar tetap
# dapat membedakan tamu dari pengguna terautentikasi tanpa menolak permintaan.
TAMU = ProfilPengguna(
    id=None,
    username="pengunjung",
    nama="Pengunjung",
    peran=Peran.PENGUNJUNG,
    tim_pjk=None,
    wilayah_kode=None,
    harus_ganti_password=False,
)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def pengguna_saat_ini(
    token: str | None = Depends(oauth2),
    session: Session = Depends(get_session),
) -> ProfilPengguna:
    """Profil pengguna, atau TAMU bila tidak ada token.

    Hanya membuktikan token sah dan akun masih aktif. Keputusan otorisasi
    ditangani `wajib_peran` agar keduanya tidak bercampur.
    """
    if not token:
        return TAMU
    try:
        muatan = baca_token(token)
    except TokenTidakValid as exc:
        raise HTTPException(401, "Token tidak valid") from exc

    akun = repo_pengguna.ambil_aktif(session, int(muatan["sub"]))
    if akun is None:
        raise HTTPException(401, "Pengguna tidak aktif")
    return repo_pengguna.profil(akun)


def wajib_peran(*peran: str):
    """Dependency yang menolak 403 bila peran pengguna tidak termasuk."""

    def dependency(pengguna: ProfilPengguna = Depends(pengguna_saat_ini)) -> ProfilPengguna:
        if pengguna.peran not in peran:
            raise HTTPException(403, "Akses tidak diizinkan")
        return pengguna

    return dependency


def id_terautentikasi(pengguna: ProfilPengguna) -> int:
    """Id pengguna yang dijamin terautentikasi.

    `wajib_peran` sudah menolak tamu, tetapi jaminan itu tidak terlihat pemeriksa
    tipe karena TAMU memakai id None. Fungsi ini membuatnya eksplisit sekaligus
    menjadi jaring pengaman bila ada dependency baru yang lupa membatasi peran.
    """
    if pengguna.id is None:
        raise HTTPException(401, "Perlu autentikasi")
    return pengguna.id
