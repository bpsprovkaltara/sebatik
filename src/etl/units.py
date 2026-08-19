"""Satuan baku untuk 86 indikator ISV-IUP.

Nilai ``None`` dipakai untuk dua baris sumber yang duplikat/tidak lengkap.
Label indeks tetap disimpan sebagai metadata, tetapi lapisan presentasi tidak
menempelkannya setelah angka.
"""

ISV_UNITS = [
    "Juta Rupiah",
    "Indeks (0–100)",
    "Persen (%)",
    "Persen (%)",
    "Indeks (0–1)",
    "Persen (%)",
    "Indeks (skala 1–5)",
    "Indeks (0–1)",
    "Persen (%)",
    "Indeks / Poin (0–100)",
]

IUP_UNITS = [
    "Tahun",
    "Per 100.000 kelahiran hidup",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    None,
    None,
    "Tahun",
    "Tahun",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Ribu Orang",
    "Rupiah",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Indeks (0–100)",
    "Indeks (0–100)",
    "Persen (%)",
    "Indeks (0–10)",
    "Persen (%)",
    "Persen terhadap PDRB (%)",
    "Persen terhadap PDRB (%)",
    "Persen (%)",
    "Persen (%)",
    "Indeks / Nilai (0–100)",
    "Indeks (0–5)",
    "Indeks (0–5)",
    "Indeks (0–100)",
    "Persen (%)",
    "Persen (%)",
    "Persen (%)",
    "Indeks (0–100)",
    "Persen (%)",
    "Persen (%) y-on-y",
    "Persen (%)",
    "Persen (%)",
    "Rupiah",
    "Persen (%)",
    "Persen (%)",
    "Kerja sama (dokumen)",
    "Indeks (1–5)",
    "Indeks (0–100)",
    "Indeks (0–100)",
    "Indeks (0–100)",
    "Indeks (0–1)",
    "Indeks (0–1)",
    "Indeks / Poin (0–100)",
    "Indeks / Poin (0–100)",
    "Indeks / Poin (0–100)",
    "Indeks / Poin (0–100)",
    "Persen (%)",
    "Persen (%)",
    "Persen RT (%)",
    "kWh/kapita/tahun",
    "SBM per Rp Milyar",
    "Persen (%)",
    "m³/detik",
    "Persen (%)",
    "Indeks / Skor (0–300)",
    "Persen (%)",
    "Persen (%)",
]

IUP_IDS = [
    *range(1, 43),
    44,
    45,
    46,
    47,
    48,
    49,
    50,
    52,
    53,
    54,
    55,
    56,
    57,
    59,
    60,
    61,
    62,
    63,
    64,
    65,
    66,
    68,
    69,
    70,
    71,
    72,
    73,
    74,
    75,
    76,
    77,
    78,
    79,
    80,
]

INDICATOR_UNITS = {
    **{f"ISV-{number:03d}": unit for number, unit in enumerate(ISV_UNITS, 1)},
    **{f"IUP-{number:03d}": unit for number, unit in zip(IUP_IDS, IUP_UNITS, strict=True)},
}


def indicator_unit(indicator_id: str | None) -> str | None:
    raw = str(indicator_id or "").strip().upper()
    try:
        category, number = raw.split("-", 1)
        # Tabel ETL lama memakai urutan rapat dua digit (IUP-01..IUP-76),
        # sedangkan master beranda mempertahankan nomor sumber yang berlubang.
        if len(number) <= 2:
            units = ISV_UNITS if category == "ISV" else IUP_UNITS if category == "IUP" else []
            position = int(number) - 1
            return units[position] if 0 <= position < len(units) else None
        key = f"{category}-{int(number):03d}"
    except (TypeError, ValueError):
        key = raw
    return INDICATOR_UNITS.get(key)
