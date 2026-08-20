"""Fungsi murni untuk menafsirkan nilai indikator.

Sebagian nilai master tersimpan sebagai teks (mis. `"3,85"`, `"7,1; 7,4"`)
karena itulah bentuk aslinya di workbook. Modul ini memusatkan aturan
penafsirannya agar beranda, explorer, capaian, dan insight tidak masing-masing
menafsirkan dengan cara sendiri.
"""

from __future__ import annotations

import re

ANGKA = re.compile(r"-?\d+(?:[.,]\d+)?")


def angka_terakhir(nilai: float | None, nilai_teks: str | None = None) -> float | None:
    """Angka yang mewakili satu sel nilai.

    Nilai numerik dipakai apa adanya. Bila hanya ada teks, angka **terakhir**
    yang diambil: teks berformat `"7,1; 7,4"` berarti rilis per periode, dan
    yang paling mutakhir ada di belakang.
    """
    if nilai is not None:
        return float(nilai)
    if not nilai_teks:
        return None
    cocok = ANGKA.findall(str(nilai_teks))
    if not cocok:
        return None
    try:
        return float(cocok[-1].replace(",", "."))
    except ValueError:
        return None


def pertumbuhan(sekarang: float | None, sebelumnya: float | None) -> float | None:
    """Pertumbuhan persen terhadap tahun sebelumnya.

    None bila salah satu tidak ada, atau bila pembandingnya nol — pertumbuhan
    dari nol tidak terdefinisi dan tidak boleh dilaporkan sebagai angka.
    """
    if sekarang is None or sebelumnya in (None, 0):
        return None
    return round((sekarang - float(sebelumnya)) / abs(float(sebelumnya)) * 100, 2)


def selisih(sekarang: float | None, sebelumnya: float | None, digit: int = 2) -> float | None:
    if sekarang is None or sebelumnya is None:
        return None
    return round(sekarang - sebelumnya, digit)


def arah_perubahan(sekarang: float | None, sebelumnya: float | None) -> str:
    if sekarang is None or sebelumnya is None:
        return "TIDAK_ADA_DATA"
    if sekarang > sebelumnya:
        return "NAIK"
    if sekarang < sebelumnya:
        return "TURUN"
    return "TETAP"


def label_periode_tampil(nama_indikator: str, label_periode: str | None, tahun: int) -> str | None:
    """Label waktu yang lebih bermakna daripada sekadar nomor semester."""
    if not label_periode:
        return None
    nama = nama_indikator.lower()
    label = label_periode.lower()
    nomor = next((angka for angka in (1, 2, 3, 4) if str(angka) in label), None)
    if "kemiskinan" in nama and nomor in (1, 2):
        return f"Maret {tahun}" if nomor == 1 else f"September {tahun}"
    if "pengangguran" in nama and nomor in (1, 2):
        return f"Februari {tahun}" if nomor == 1 else f"Agustus {tahun}"
    return f"{label_periode} {tahun}"
