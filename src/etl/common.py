"""Fungsi bersama untuk audit dan ETL SEBATIK."""

from __future__ import annotations

import math
import re
from typing import Any

NON_NUMERIC = {"", "-", "–", "—", "n/a", "na", "none", "null", "tidak tersedia", "belum tersedia"}


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def parse_angka(value: Any) -> float | None:
    """Normalisasi angka Indonesia/internasional melalui satu pintu."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    text = str(value).strip().replace("\u00a0", "").replace(" ", "")
    if text.lower() in NON_NUMERIC:
        return None
    text = re.sub(r"[^0-9,\.\-+]", "", text)
    if not text or text in {"-", "+"}:
        return None
    if "," in text and "." in text:
        # Pemisah paling kanan dianggap desimal; lainnya pemisah ribuan.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        parts = text.split(",")
        text = "".join(parts[:-1]) + "." + parts[-1] if len(parts) > 1 else text
    elif text.count(".") > 1:
        parts = text.split(".")
        text = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(text)
    except ValueError:
        return None


def indicator_id(category: Any, number: Any) -> str | None:
    cat = (clean_text(category) or "").upper()
    num = parse_angka(number)
    if cat not in {"ISV", "IUP"} or num is None:
        return None
    return f"{cat}-{int(num):02d}"


def enum_rpjmd(value: Any) -> str:
    text = (clean_text(value) or "").lower()
    if not text:
        return "TIDAK_MASUK_RPJMD"
    if "dobel" in text or "double" in text or ("isv" in text and "iup" in text):
        return "DOBEL_ISV_IUP"
    if "masuk" in text and ("belum" in text or "tidak ada data" in text):
        return "MASUK_TAPI_BELUM_ADA_DATA"
    if "tidak masuk" in text or "tdk masuk" in text:
        return "TIDAK_MASUK_RPJMD"
    if "masuk" in text or "rpjmd" in text:
        return "MASUK_RPJMD"
    return "TIDAK_MASUK_RPJMD"
