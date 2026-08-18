"""Hashing kata sandi dan token akses.

Dipisah dari router supaya aturan otentikasi dapat diuji tanpa HTTP dan tidak
tersebar di beberapa modul seperti sebelumnya.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from .config import settings
from .models import Peran

ALGORITMA = "HS256"

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


def buat_token(pengguna_id: int, peran: str) -> str:
    """Token bearer HS256 dengan klaim sub, peran, iat, dan exp."""
    sekarang = datetime.now(UTC)
    muatan = {
        "sub": str(pengguna_id),
        "peran": str(peran),
        "iat": sekarang,
        "exp": sekarang + timedelta(hours=settings.access_token_ttl_hours),
    }
    return jwt.encode(muatan, settings.secret_key, algorithm=ALGORITMA)


def baca_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITMA])
    except jwt.PyJWTError as exc:
        raise TokenTidakValid(str(exc)) from exc


def peran_diizinkan(peran: str, diizinkan: tuple[str, ...]) -> bool:
    return peran in diizinkan


PERAN_INTERNAL: tuple[str, ...] = (Peran.ADMIN, Peran.OPERATOR, Peran.VERIFIKATOR)
