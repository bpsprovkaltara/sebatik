"""Hashing kata sandi dan token akses.

Dipisah dari router supaya aturan otentikasi dapat diuji tanpa HTTP dan tidak
tersebar di beberapa modul seperti sebelumnya.

Dua hal yang perlu diketahui pembaca berikutnya:

- **Rotasi kunci** (auth-keamanan.md §2.4). Token selalu ditandatangani dengan
  `secret_key` yang aktif, tetapi diverifikasi terhadap kunci aktif lalu kunci
  lama di `secret_keys`. Dengan begitu mengganti rahasia tidak memutus sesi
  semua orang seketika.
- **Dua jenis token** (auth-keamanan.md §3 Opsi A). Token akses berumur pendek
  dipakai di header `Authorization`; token segar berumur lebih panjang hanya
  dipakai endpoint `/auth/refresh` dan disimpan sebagai cookie httpOnly.
  Klaim `tipe` memisahkan keduanya agar token segar tidak bisa dipakai sebagai
  token akses.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from .config import settings
from .models import Peran

ALGORITMA = "HS256"

TIPE_AKSES = "akses"
TIPE_SEGAR = "segar"

_hasher = PasswordHash.recommended()

# Kebijakan yang sudah berlaku sebelumnya; dipusatkan agar tidak diulang di
# tiga endpoint yang mengubah kata sandi.
PANJANG_PASSWORD_MINIMUM = 12


class TokenTidakValid(Exception):
    """Token tidak dapat dibaca, kedaluwarsa, atau tidak dipercaya."""


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verifikasi_password(password: str, hash_tersimpan: str) -> bool:
    return _hasher.verify(password, hash_tersimpan)


def password_memenuhi_syarat(password: str) -> bool:
    return len(password) >= PANJANG_PASSWORD_MINIMUM


def kunci_verifikasi() -> tuple[str, ...]:
    """Kunci aktif lebih dulu, lalu kunci lama yang masih diterima."""
    return (settings.secret_key, *settings.secret_keys)


def _buat(pengguna_id: int, peran: str, *, tipe: str, berlaku: timedelta) -> str:
    sekarang = datetime.now(UTC)
    muatan = {
        "sub": str(pengguna_id),
        "peran": str(peran),
        "tipe": tipe,
        # `jti` membuat setiap token dapat dirujuk satu per satu di log audit.
        "jti": uuid4().hex,
        "iat": sekarang,
        "exp": sekarang + berlaku,
    }
    return jwt.encode(muatan, settings.secret_key, algorithm=ALGORITMA)


def buat_token(pengguna_id: int, peran: str) -> str:
    """Token akses HS256 dengan klaim sub, peran, tipe, jti, iat, dan exp."""
    return _buat(pengguna_id, peran, tipe=TIPE_AKSES, berlaku=timedelta(hours=settings.access_token_ttl_hours))


def buat_token_segar(pengguna_id: int, peran: str) -> str:
    """Token yang hanya boleh ditukar menjadi token akses baru."""
    return _buat(pengguna_id, peran, tipe=TIPE_SEGAR, berlaku=timedelta(hours=settings.refresh_token_ttl_hours))


def baca_token(token: str, *, tipe: str = TIPE_AKSES) -> dict[str, Any]:
    """Baca token dan pastikan jenisnya sesuai yang diharapkan pemanggil.

    Token lama yang terbit sebelum klaim `tipe` ada tetap diterima sebagai
    token akses, supaya pemasangan yang sudah berjalan tidak memaksa semua
    orang masuk ulang saat aplikasi diperbarui.
    """
    galat: Exception | None = None
    for kunci in kunci_verifikasi():
        try:
            muatan = jwt.decode(token, kunci, algorithms=[ALGORITMA])
        except jwt.ExpiredSignatureError as exc:
            # Kunci lain tidak akan menolong token yang sudah lewat masanya.
            raise TokenTidakValid(str(exc)) from exc
        except jwt.PyJWTError as exc:
            galat = exc
            continue
        if muatan.get("tipe", TIPE_AKSES) != tipe:
            raise TokenTidakValid("Jenis token tidak sesuai")
        return muatan
    raise TokenTidakValid(str(galat) if galat else "Token tidak dapat diverifikasi")


def peran_diizinkan(peran: str, diizinkan: tuple[str, ...]) -> bool:
    return peran in diizinkan


PERAN_INTERNAL: tuple[str, ...] = (Peran.ADMIN, Peran.OPERATOR, Peran.VERIFIKATOR)
