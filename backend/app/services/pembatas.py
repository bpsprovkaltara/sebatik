"""Pembatas laju percobaan masuk.

Menahan tebak-sandi beruntun pada `/auth/login`. Jendela geser sederhana di
memori proses: cukup untuk pemasangan satu instans seperti SEBATIK, dan tidak
menambah ketergantungan Redis. Bila kelak dijalankan multi-instans, penyimpanan
hitungannya perlu dipindah ke Redis/PostgreSQL — antarmukanya sudah siap.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import NamedTuple


class Keputusan(NamedTuple):
    diizinkan: bool
    sisa_detik: int


class PembatasLaju:
    """Izinkan paling banyak `maksimum` percobaan per `jendela_detik` per kunci."""

    def __init__(self, maksimum: int, jendela_detik: int) -> None:
        self.maksimum = maksimum
        self.jendela_detik = jendela_detik
        self._percobaan: dict[str, deque[float]] = defaultdict(deque)
        # Uvicorn melayani permintaan dari beberapa thread; hitungannya dikunci.
        self._kunci = threading.Lock()

    def _bersihkan(self, riwayat: deque[float], sekarang: float) -> None:
        batas = sekarang - self.jendela_detik
        while riwayat and riwayat[0] <= batas:
            riwayat.popleft()

    def periksa(self, kunci: str, sekarang: float | None = None) -> Keputusan:
        """Catat satu percobaan dan putuskan apakah masih diizinkan."""
        saat = time.monotonic() if sekarang is None else sekarang
        with self._kunci:
            riwayat = self._percobaan[kunci]
            self._bersihkan(riwayat, saat)
            if len(riwayat) >= self.maksimum:
                sisa = self.jendela_detik - (saat - riwayat[0])
                return Keputusan(False, max(1, int(sisa) + 1))
            riwayat.append(saat)
            return Keputusan(True, 0)

    def lupakan(self, kunci: str) -> None:
        """Bersihkan riwayat setelah percobaan berhasil."""
        with self._kunci:
            self._percobaan.pop(kunci, None)

    def kosongkan(self) -> None:
        """Hanya dipakai tes agar antar-tes tidak saling mewarisi hitungan."""
        with self._kunci:
            self._percobaan.clear()


def kunci_percobaan(ip: str | None, username: str) -> str:
    """Kunci gabungan IP dan username.

    Menggabungkan keduanya membuat satu penyerang tidak dapat mengunci akun
    orang lain hanya dengan membanjiri percobaan dari IP berbeda.
    """
    return f"{ip or 'tidak-diketahui'}|{username.casefold()}"


# Lima percobaan gagal per menit per (IP, username) — sesuai auth-keamanan.md §5.
pembatas_login = PembatasLaju(maksimum=5, jendela_detik=60)
