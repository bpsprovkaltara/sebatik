"""Logika bisnis murni.

Menerima nilai biasa (bukan objek `Request`) dan mengembalikan nilai biasa,
sehingga dapat diuji tanpa HTTP maupun basis data. Tidak mengimpor `routers`.
"""

from __future__ import annotations

from typing import NamedTuple


class Penolakan(NamedTuple):
    """Alasan sebuah tindakan tidak diizinkan, beserta kode HTTP-nya.

    Service tidak boleh mengimpor FastAPI, jadi penolakan dikembalikan sebagai
    nilai biasa dan router yang menerjemahkannya menjadi `HTTPException`.
    """

    kode: int
    pesan: str


__all__ = ["Penolakan"]
