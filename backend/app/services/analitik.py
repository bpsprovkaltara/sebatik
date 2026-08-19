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


# ---------------------------------------------------------------------------
# Penyusunan muatan analitik.
#
# Bagian di atas murni angka. Bagian ini membaca seri dari repository lalu
# merangkainya menjadi muatan endpoint — tetap di luar router karena isinya
# perhitungan, bukan HTTP (backend.md §1.2).
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session  # noqa: E402

from ..models import KODE_PROVINSI, JenisNilai  # noqa: E402
from ..repositories import indikator as repo_indikator  # noqa: E402
from ..repositories import nilai as repo_nilai  # noqa: E402
from . import Penolakan  # noqa: E402

MAKSIMUM_INDIKATOR_MULTI = 4
BATAS_PERINGKAT = 10
# Peringkat butuh minimal dua titik untuk punya arti "berubah".
MINIMUM_TITIK_PERINGKAT = 2


def seri_realisasi(session: Session, id_indikator: str) -> list[tuple[int, float]]:
    """Pasangan (tahun, nilai) realisasi tahunan yang benar-benar berangka."""
    return [
        (baris.tahun, float(baris.nilai))
        for baris in repo_nilai.seri(session, id_indikator, KODE_PROVINSI, JenisNilai.REALISASI)
        if baris.nilai is not None
    ]


def muatan_selisih(session: Session, id_indikator: str) -> dict[str, Any]:
    indikator = repo_indikator.ambil(session, id_indikator)
    arah = indikator.arah_baik if indikator else None
    return {
        "id_indikator": id_indikator,
        "arah_baik": arah,
        "data": selisih_tahunan(seri_realisasi(session, id_indikator), arah),
    }


def muatan_peringkat(session: Session) -> dict[str, Any]:
    """Indikator dengan perbaikan dan pemburukan terbesar tahun terakhir."""
    hasil: list[dict[str, Any]] = []
    for indikator in repo_indikator.daftar_arah_terverifikasi(session):
        seri = seri_realisasi(session, indikator.id_indikator)
        if len(seri) < MINIMUM_TITIK_PERINGKAT:
            continue
        (tahun_awal, nilai_awal), (tahun_akhir, nilai_akhir) = seri[-2], seri[-1]
        perubahan = nilai_akhir - nilai_awal
        hasil.append(
            {
                "id_indikator": indikator.id_indikator,
                "nama_indikator": indikator.nama_indikator,
                "arah_baik": indikator.arah_baik,
                "tahun_awal": tahun_awal,
                "tahun_akhir": tahun_akhir,
                "perubahan": perubahan,
                "skor_perbaikan": skor_perbaikan(perubahan, indikator.arah_baik),
            }
        )
    hasil.sort(key=lambda x: float(x["skor_perbaikan"]), reverse=True)
    return {
        "perbaikan_terbesar": hasil[:BATAS_PERINGKAT],
        "pemburukan_terbesar": list(reversed(hasil[-BATAS_PERINGKAT:])),
    }


def muatan_gap(session: Session, indikator: Any) -> dict[str, Any]:
    """Jarak realisasi terakhir terhadap target 2029 dan 2045."""
    id_indikator = indikator.id_indikator
    realisasi = seri_realisasi(session, id_indikator)
    if not realisasi:
        return {"status": "BELUM_ADA_DATA", "disclaimer": DISCLAIMER_PROYEKSI}

    target = {
        baris.tahun: baris.nilai
        for baris in repo_nilai.seri(session, id_indikator, KODE_PROVINSI, JenisNilai.TARGET)
        if baris.tahun in (TAHUN_TARGET_ANTARA, TAHUN_TARGET_AKHIR) and baris.nilai is not None
    }
    tahun_terakhir, nilai_terakhir = realisasi[-1]
    target_2029 = target.get(TAHUN_TARGET_ANTARA)
    target_2045 = target.get(TAHUN_TARGET_AKHIR)

    historis = laju_historis(realisasi)
    dibutuhkan = laju_dibutuhkan(nilai_terakhir, tahun_terakhir, target_2045, TAHUN_TARGET_AKHIR)
    return {
        "id_indikator": id_indikator,
        "realisasi_terakhir": {"tahun": tahun_terakhir, "nilai": nilai_terakhir},
        "target_2029": target_2029,
        "target_2045": target_2045,
        "gap_2029": None if target_2029 is None else target_2029 - nilai_terakhir,
        "gap_2045": None if target_2045 is None else target_2045 - nilai_terakhir,
        "laju_historis": historis,
        "required_run_rate": dibutuhkan,
        "status_jalur": status_jalur(
            historis, dibutuhkan, indikator.arah_baik, bool(indikator.arah_baik_terverifikasi)
        ),
        "disclaimer": DISCLAIMER_PROYEKSI,
    }


def muatan_multi(session: Session, ids: Sequence[str]) -> dict[str, Any] | Penolakan:
    """Beberapa seri berdampingan untuk dibandingkan dalam satu grafik."""
    if len(ids) > MAKSIMUM_INDIKATOR_MULTI:
        return Penolakan(422, "Maksimal empat indikator")

    terpilih = []
    for id_indikator in ids:
        indikator = repo_indikator.ambil(session, id_indikator)
        if indikator is None:
            return Penolakan(404, f"Indikator tidak ditemukan: {id_indikator}")
        terpilih.append(indikator)

    return {
        "data": [
            {
                "id_indikator": indikator.id_indikator,
                "nama": indikator.nama_indikator,
                "seri": [
                    {"tahun": baris.tahun, "jenis": baris.jenis, "nilai": baris.nilai}
                    for baris in repo_nilai.seri(session, indikator.id_indikator, KODE_PROVINSI)
                    if baris.nilai is not None
                ],
            }
            for indikator in terpilih
        ]
    }


def muatan_korelasi(session: Session, x: str, y: str) -> dict[str, Any]:
    hasil = korelasi(dict(seri_realisasi(session, x)), dict(seri_realisasi(session, y)))
    return {
        "n": hasil.n,
        "pearson": hasil.pearson,
        "data": hasil.titik,
        "peringatan": hasil.peringatan,
    }
