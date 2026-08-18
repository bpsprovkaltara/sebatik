"""Pemetaan nomor urut workbook menjadi identitas indikator."""

from __future__ import annotations

from typing import Any

from ..common import clean_text, indicator_id, parse_angka


def id_indikator(kategori: Any, nomor: Any) -> str | None:
    """`("ISV", 4)` -> `"ISV-04"`."""
    return indicator_id(kategori, nomor)


def kategori_dari_nomor(nomor: Any, isv_nomor_maksimum: int) -> str | None:
    """Sheet lama memakai penomoran menyambung: 1..N adalah ISV, sisanya IUP."""
    angka = parse_angka(nomor)
    if angka is None:
        return None
    return "ISV" if int(angka) <= isv_nomor_maksimum else "IUP"


def nomor_dalam_kategori(nomor: Any, kategori: Any, isv_nomor_maksimum: int) -> int | None:
    """Nomor urut di dalam kategorinya sendiri.

    Nomor IUP pada sheet lama melanjutkan penomoran ISV, jadi harus digeser
    mundur sebanyak batas ISV agar `IUP-01` benar-benar indikator IUP pertama.
    """
    angka = parse_angka(nomor)
    if angka is None:
        return None
    kategori_bersih = (clean_text(kategori) or "").upper()
    if kategori_bersih == "ISV":
        return int(angka)
    return int(angka) - isv_nomor_maksimum
