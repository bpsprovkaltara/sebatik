"""Perhitungan analitik: korelasi, selisih tahunan, peringkat, dan gap target.

Semua fungsi murni. Batas kehati-hatian statistik (mis. menyembunyikan korelasi
seri pendek) ada di sini, bukan di router, supaya tidak bisa terlewat.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, NamedTuple

from ..models import ArahBaik

# Di bawah empat titik, koefisien korelasi lebih menyesatkan daripada berguna.
MINIMUM_TITIK_KORELASI = 4

PERINGATAN_SERI_PENDEK = (
    "Hasil disembunyikan karena n < 4. Korelasi bukan sebab-akibat; seri pendek tidak layak ditafsirkan."
)
PERINGATAN_KORELASI = "Korelasi bukan sebab-akibat; seri tahunan pendek harus ditafsirkan dengan sangat hati-hati."
DISCLAIMER_PROYEKSI = "Ekstrapolasi linear sederhana, bukan proyeksi resmi."

TAHUN_TARGET_ANTARA = 2029
TAHUN_TARGET_AKHIR = 2045


class HasilKorelasi(NamedTuple):
    n: int
    pearson: float | None
    titik: list[dict[str, float | int]]
    peringatan: str


def korelasi(seri_x: dict[int, float], seri_y: dict[int, float]) -> HasilKorelasi:
    """Pearson atas tahun yang dimiliki kedua seri."""
    tahun_bersama = sorted(set(seri_x) & set(seri_y))
    titik = [{"tahun": t, "x": seri_x[t], "y": seri_y[t]} for t in tahun_bersama]
    if len(titik) < MINIMUM_TITIK_KORELASI:
        return HasilKorelasi(len(titik), None, titik, PERINGATAN_SERI_PENDEK)

    xs = [float(p["x"]) for p in titik]
    ys = [float(p["y"]) for p in titik]
    rata_x, rata_y = sum(xs) / len(xs), sum(ys) / len(ys)
    penyebut = math.sqrt(sum((a - rata_x) ** 2 for a in xs) * sum((b - rata_y) ** 2 for b in ys))
    if not penyebut:
        # Salah satu seri konstan; korelasinya tidak terdefinisi, bukan nol.
        return HasilKorelasi(len(titik), None, titik, PERINGATAN_KORELASI)
    nilai = sum((a - rata_x) * (b - rata_y) for a, b in zip(xs, ys, strict=True)) / penyebut
    return HasilKorelasi(len(titik), round(nilai, 4), titik, PERINGATAN_KORELASI)


def selisih_tahunan(seri: Sequence[tuple[int, float]], arah_baik: str | None) -> list[dict[str, Any]]:
    """Perubahan antar tahun berurutan beserta penilaian membaik/tidak."""
    hasil = []
    for (_, nilai_awal), (tahun, nilai_akhir) in zip(seri, seri[1:], strict=False):
        beda = nilai_akhir - nilai_awal
        perbaikan = beda if arah_baik == ArahBaik.NAIK else -beda
        hasil.append({"tahun": tahun, "selisih": beda, "membaik": perbaikan >= 0})
    return hasil


def skor_perbaikan(beda: float, arah_baik: str | None) -> float:
    """Perubahan diterjemahkan menjadi skor yang selalu 'makin besar makin baik'."""
    return beda if arah_baik == ArahBaik.NAIK else -beda


def laju_historis(seri: Sequence[tuple[int, float]]) -> float | None:
    """Rata-rata perubahan per tahun antara titik pertama dan terakhir."""
    if len(seri) < 2:
        return None
    (tahun_awal, nilai_awal), (tahun_akhir, nilai_akhir) = seri[0], seri[-1]
    if tahun_akhir == tahun_awal:
        return None
    return (nilai_akhir - nilai_awal) / (tahun_akhir - tahun_awal)


def laju_dibutuhkan(
    nilai_terakhir: float, tahun_terakhir: int, target: float | None, tahun_target: int
) -> float | None:
    if target is None or tahun_terakhir >= tahun_target:
        return None
    return (target - nilai_terakhir) / (tahun_target - tahun_terakhir)


def status_jalur(historis: float | None, dibutuhkan: float | None, arah_baik: str | None, terverifikasi: bool) -> str:
    """Apakah laju perbaikan saat ini cukup untuk mencapai target."""
    if historis is None or dibutuhkan is None or not terverifikasi or not arah_baik:
        return "BELUM_ADA_DATA"
    di_jalur = historis >= dibutuhkan if arah_baik == ArahBaik.NAIK else historis <= dibutuhkan
    return "DI_JALUR" if di_jalur else "PERLU_AKSELERASI"
