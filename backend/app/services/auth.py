"""Aturan masuk, penyegaran sesi, dan pencatatan peristiwa auth.

Dua hal yang sebelumnya tersebar di router dikumpulkan di sini:

- **Keputusan masuk** — pembatas laju, pencocokan kredensial, dan penerbitan
  token — supaya jalur yang paling sensitif punya satu tempat untuk dibaca.
- **Jejak audit auth** (auth-keamanan.md §7). Peristiwa dicatat sebagai JSON
  satu baris agar dapat disaring pengumpul log, dan tidak pernah memuat kata
  sandi maupun token; yang disimpan hanya identitas, hasil, dan `jti`.
"""

from __future__ import annotations

import json
import logging
from typing import Any, NamedTuple

from sqlalchemy.orm import Session

from ..models import Pengguna
from ..repositories import pengguna as repo_pengguna
from ..security import (
    PANJANG_PASSWORD_MINIMUM,
    TIPE_SEGAR,
    TokenTidakValid,
    baca_token,
    buat_token,
    buat_token_segar,
    hash_password,
    password_memenuhi_syarat,
    verifikasi_password,
)
from .pembatas import kunci_percobaan, pembatas_login

log = logging.getLogger("sebatik.auth")

PESAN_PASSWORD_PENDEK = f"Kata sandi minimal {PANJANG_PASSWORD_MINIMUM} karakter"
# Pesan yang sama untuk username salah dan sandi salah, agar tidak
# membocorkan username mana yang terdaftar.
PESAN_KREDENSIAL_SALAH = "Username atau kata sandi salah"
PESAN_TERLALU_SERING = "Terlalu banyak percobaan masuk. Coba lagi beberapa saat lagi."
NAMA_COOKIE_SEGAR = "sebatik_segar"
# Cookie hanya dikirim ke jalur yang benar-benar memakainya.
JALUR_COOKIE_SEGAR = "/api/v1/auth"


def catat_peristiwa(peristiwa: str, **rincian: Any) -> None:
    """Satu baris JSON per peristiwa auth, tanpa kata sandi maupun token."""
    log.info(json.dumps({"peristiwa": peristiwa, **rincian}, default=str, ensure_ascii=False))


def password_layak(password: str) -> bool:
    return password_memenuhi_syarat(password)


class Ditolak(NamedTuple):
    kode: int
    pesan: str
    header: dict[str, str] | None = None


class Sesi(NamedTuple):
    """Muatan yang dikembalikan endpoint masuk, plus token segar untuk cookie."""

    muatan: dict[str, Any]
    token_segar: str


def _sesi(akun: Pengguna) -> Sesi:
    return Sesi(
        muatan={
            "access_token": buat_token(akun.id, akun.peran),
            "token_type": "bearer",
            "peran": akun.peran,
            "harus_ganti_password": bool(akun.harus_ganti_password),
        },
        token_segar=buat_token_segar(akun.id, akun.peran),
    )


def masuk(session: Session, *, username: str, password: str, ip: str | None) -> Sesi | Ditolak:
    """Alur masuk lengkap: pembatas laju, kredensial, lalu penerbitan token."""
    kunci = kunci_percobaan(ip, username)
    keputusan = pembatas_login.periksa(kunci)
    if not keputusan.diizinkan:
        catat_peristiwa("masuk", username=username, hasil="dibatasi", ip=ip)
        return Ditolak(429, PESAN_TERLALU_SERING, {"Retry-After": str(keputusan.sisa_detik)})

    akun = repo_pengguna.ambil_untuk_login(session, username)
    if akun is None or not verifikasi_password(password, akun.password_hash):
        catat_peristiwa("masuk", username=username, hasil="gagal", ip=ip)
        return Ditolak(401, PESAN_KREDENSIAL_SALAH)

    # Percobaan yang berhasil tidak boleh ikut menghabiskan jatah pengguna sah.
    pembatas_login.lupakan(kunci)
    catat_peristiwa("masuk", pengguna_id=akun.id, peran=akun.peran, hasil="berhasil", ip=ip)
    return _sesi(akun)


def segarkan(session: Session, token_segar: str | None) -> Sesi | Ditolak:
    """Tukar token segar dengan token akses baru, bila akunnya masih aktif."""
    if not token_segar:
        return Ditolak(401, "Tidak ada sesi untuk disegarkan")
    try:
        muatan = baca_token(token_segar, tipe=TIPE_SEGAR)
    except TokenTidakValid:
        catat_peristiwa("segarkan", hasil="gagal")
        return Ditolak(401, "Sesi tidak dapat disegarkan")

    akun = repo_pengguna.ambil_aktif(session, int(muatan["sub"]))
    if akun is None:
        catat_peristiwa("segarkan", pengguna_id=muatan.get("sub"), hasil="akun_nonaktif")
        return Ditolak(401, "Pengguna tidak aktif")

    catat_peristiwa("segarkan", pengguna_id=akun.id, hasil="berhasil", jti_lama=muatan.get("jti"))
    return _sesi(akun)


def ganti_password(session: Session, akun: Pengguna, password_baru: str) -> dict[str, str]:
    repo_pengguna.ganti_password(akun, hash_password(password_baru), wajib_ganti=False)
    session.commit()
    catat_peristiwa("ganti_password", pengguna_id=akun.id, hasil="berhasil")
    return {"status": "PASSWORD_DIUBAH"}
