"""Aturan pengelolaan akun: pembuatan, status aktif, dan reset kata sandi.

Aturan penempatan peran (verifikator harus provinsi, operator wajib punya
wilayah) dan larangan admin menonaktifkan dirinya sendiri adalah aturan bisnis,
jadi diuji tanpa HTTP dan tidak tinggal di router (backend.md §1.2).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..models import KODE_PROVINSI, PERAN, Pengguna, Peran
from ..repositories import pengguna as repo_pengguna
from ..repositories import tata_kelola as repo_tata_kelola
from ..repositories import wilayah as repo_wilayah
from ..security import PANJANG_PASSWORD_MINIMUM, hash_password, password_memenuhi_syarat
from . import Penolakan

PESAN_PASSWORD_PENDEK = f"Kata sandi minimal {PANJANG_PASSWORD_MINIMUM} karakter"
# Peran yang terikat pada satu wilayah kerja.
PERAN_BERWILAYAH = (Peran.OPERATOR, Peran.VERIFIKATOR)


def periksa_pembuatan(*, peran: str, wilayah_aktif: bool, wilayah_kode: str | None, password: str) -> Penolakan | None:
    """Semua aturan yang membatasi akun seperti apa yang boleh dibuat."""
    if peran not in tuple(PERAN):
        return Penolakan(422, "Peran tidak valid")
    if peran in PERAN_BERWILAYAH and not wilayah_aktif:
        return Penolakan(422, "Wilayah wajib dan harus aktif")
    if peran == Peran.VERIFIKATOR and wilayah_kode != KODE_PROVINSI:
        return Penolakan(422, "Verifikator hanya dapat ditempatkan pada Provinsi Kalimantan Utara")
    if not password_memenuhi_syarat(password):
        return Penolakan(422, PESAN_PASSWORD_PENDEK)
    return None


def periksa_ubah_status(*, pengguna_id: int, admin_id: int | None, aktif: bool) -> Penolakan | None:
    if pengguna_id == admin_id and not aktif:
        return Penolakan(422, "Admin tidak dapat menonaktifkan akunnya sendiri")
    return None


def buat(
    session: Session,
    *,
    username: str,
    nama: str,
    password: str,
    peran: str,
    wilayah_kode: str | None,
    tim_pjk: str | None,
) -> None:
    """Menyiapkan akun baru; pemanggil yang menjalankan commit dan menangani 409."""
    repo_pengguna.buat(
        session,
        username=username,
        nama=nama,
        password_hash=hash_password(password),
        peran=peran,
        tim_pjk=tim_pjk,
        wilayah_kode=wilayah_kode,
    )


def wilayah_penempatan_sah(session: Session, wilayah_kode: str | None) -> bool:
    return repo_wilayah.ada_dan_aktif(session, wilayah_kode)


def daftar(session: Session) -> dict[str, Any]:
    """Daftar akun untuk panel admin — tanpa hash kata sandi."""
    return {
        "data": [
            {
                "id": akun.id,
                "username": akun.username,
                "nama": akun.nama,
                "peran": akun.peran,
                "wilayah_kode": akun.wilayah_kode,
                "wilayah": nama_wilayah,
                "tim_pjk": akun.tim_pjk,
                "aktif": akun.aktif,
                "harus_ganti_password": akun.harus_ganti_password,
            }
            for akun, nama_wilayah in repo_pengguna.daftar_dengan_wilayah(session)
        ]
    }


def ubah_status(session: Session, akun: Pengguna, *, aktif: bool, admin_id: int) -> dict[str, str]:
    akun.aktif = aktif
    repo_tata_kelola.catat_aktivitas(
        session,
        pengguna_id=admin_id,
        aksi="UBAH_STATUS_AKUN",
        objek_tipe="pengguna",
        objek_id=str(akun.id),
        detail={"aktif": aktif},
    )
    session.commit()
    return {"status": "AKTIF" if aktif else "NONAKTIF"}


def reset_password(session: Session, akun: Pengguna, *, password_baru: str, admin_id: int) -> dict[str, str]:
    # Reset oleh admin selalu memaksa ganti sandi pada login berikutnya.
    repo_pengguna.ganti_password(akun, hash_password(password_baru), wajib_ganti=True)
    repo_tata_kelola.catat_aktivitas(
        session,
        pengguna_id=admin_id,
        aksi="RESET_PASSWORD",
        objek_tipe="pengguna",
        objek_id=str(akun.id),
        detail="Kata sandi direset oleh admin",
    )
    session.commit()
    return {"status": "PASSWORD_DIRESET"}
