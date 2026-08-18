"""Lapisan akses data.

Satu fungsi per bentuk query terhadap model ORM. Tidak berisi aturan bisnis dan
tidak pernah mengimpor `routers` atau `services` (lihat arsitektur-target.md §2).
"""

from __future__ import annotations

from . import indikator, nilai, pengguna, tata_kelola, wilayah

__all__ = ["indikator", "nilai", "pengguna", "tata_kelola", "wilayah"]
