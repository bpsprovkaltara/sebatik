"""Skema autentikasi."""

from __future__ import annotations

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Hanya token akses yang keluar lewat badan respons.

    Token segar dikirim sebagai cookie httpOnly dan sengaja tidak muncul di
    sini (auth-keamanan.md §3 Opsi A).
    """

    access_token: str
    token_type: str
    peran: str
    harus_ganti_password: bool


class ProfilResponse(BaseModel):
    """Profil pengguna — tidak pernah memuat `password_hash`."""

    id: int | None = None
    username: str
    nama: str
    peran: str
    tim_pjk: str | None = None
    wilayah_kode: str | None = None
    harus_ganti_password: bool
