"""Penafsiran penanda indikator proxy."""

from __future__ import annotations

import re
from typing import Any

from ..common import clean_text

# Nilai yang berarti "bukan proxy" meski kolomnya terisi.
BUKAN_PROXY = {"tidak", "tidak ada", "-"}
# Nilai penanda yang tidak layak dipakai sebagai nama proxy.
PENANDA_SAJA = {"ya", "proxy"}

POLA_NAMA_PROXY = re.compile(r"indikator\s+proxy\s*:\s*([^;\n]+)", flags=re.I)


def ekstrak_proxy(penanda: Any, catatan: Any) -> tuple[int, str | None]:
    """Status proxy (0/1) beserta nama indikator proxy bila disebutkan."""
    bendera = clean_text(penanda)
    nota = clean_text(catatan)
    gabungan = " ".join(x for x in (bendera, nota) if x)

    adalah_proxy = bool(bendera and bendera.casefold() not in BUKAN_PROXY) or ("proxy" in gabungan.casefold())
    cocok = POLA_NAMA_PROXY.search(str(catatan or ""))
    if cocok:
        return int(adalah_proxy), clean_text(cocok.group(1))
    # Bila kolom penanda berisi nama, bukan sekadar "ya", pakai sebagai nama.
    layak = adalah_proxy and bendera and bendera.casefold() not in PENANDA_SAJA
    return int(adalah_proxy), bendera if layak else None
