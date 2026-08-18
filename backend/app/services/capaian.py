"""Aturan perhitungan capaian dan progres menuju target.

Semua fungsi di sini murni: menerima angka, mengembalikan angka. Tidak menyentuh
basis data dan tidak tahu apa-apa tentang HTTP.
"""

from __future__ import annotations

from typing import NamedTuple

from ..models import ArahBaik

STATUS_BELUM_ADA_DATA = "BELUM_ADA_DATA"
STATUS_TERCAPAI = "TERCAPAI"
STATUS_MENDEKATI = "MENDEKATI"
STATUS_PERLU_PERHATIAN = "PERLU_PERHATIAN"

# Ambang yang memisahkan ketiga status capaian, dalam persen.
AMBANG_TERCAPAI = 100
AMBANG_MENDEKATI = 90


class HasilCapaian(NamedTuple):
    persentase: float | None
    status: str


def capaian(
    realisasi: float | None,
    target: float | None,
    arah_baik: str | None,
    terverifikasi: bool,
) -> HasilCapaian:
    """Persentase capaian terhadap target, sesuai arah baik indikator.

    Arah yang belum diverifikasi admin sengaja tidak dihitung: menghitungnya
    berarti menebak apakah naik itu baik atau buruk, dan tebakan yang salah
    membalik makna angka di dasbor.
    """
    if realisasi is None or target is None or not arah_baik or not terverifikasi:
        return HasilCapaian(None, STATUS_BELUM_ADA_DATA)

    if arah_baik == ArahBaik.NAIK:
        persen = (realisasi / target * 100) if target else None
    else:
        # Arah TURUN: makin kecil realisasi makin baik, jadi rasionya dibalik.
        persen = (target / realisasi * 100) if realisasi else None

    if persen is None:
        return HasilCapaian(None, STATUS_BELUM_ADA_DATA)
    return HasilCapaian(round(persen, 2), status_capaian(persen))


def status_capaian(persen: float) -> str:
    if persen >= AMBANG_TERCAPAI:
        return STATUS_TERCAPAI
    if persen >= AMBANG_MENDEKATI:
        return STATUS_MENDEKATI
    return STATUS_PERLU_PERHATIAN


def progres_menuju(
    nilai_sekarang: float | None,
    nilai_baseline: float | None,
    target: float | None,
) -> float | None:
    """Bagian jalan yang sudah ditempuh dari baseline menuju satu target.

    Dijepit ke 0–100 supaya cincin tracker tidak pernah tergambar melebihi
    lingkaran penuh atau berbalik arah ketika realisasi melewati target atau
    bergerak menjauh dari baseline.
    """
    if nilai_sekarang is None or nilai_baseline is None or target is None:
        return None
    pembagi = target - nilai_baseline
    if pembagi == 0:
        # Baseline sudah sama dengan target: hanya "sudah" atau tidak terdefinisi.
        return 100 if nilai_sekarang == target else None
    return max(0, min(100, round((nilai_sekarang - nilai_baseline) / pembagi * 100, 1)))


def arah_target(nilai_baseline: float | None, target: float | None) -> str | None:
    """Arah yang tersirat dari posisi target terhadap baseline."""
    if nilai_baseline is None or target is None:
        return None
    return ArahBaik.NAIK if target >= nilai_baseline else ArahBaik.TURUN


def membaik(nilai_sekarang: float | None, nilai_sebelumnya: float | None, arah: str | None) -> bool | None:
    if nilai_sekarang is None or nilai_sebelumnya is None or not arah:
        return None
    if arah == ArahBaik.NAIK:
        return nilai_sekarang >= nilai_sebelumnya
    return nilai_sekarang <= nilai_sebelumnya


def kebutuhan_per_tahun(gap: float | None, tahun_sekarang: int | None, tahun_target: int) -> float | None:
    """Laju perbaikan per tahun yang dibutuhkan untuk menutup gap."""
    if gap is None or tahun_sekarang is None or tahun_sekarang >= tahun_target:
        return None
    return round(gap / (tahun_target - tahun_sekarang), 4)


def kalimat_insight(
    *,
    nama_wilayah: str,
    tahun: int | None,
    ada_nilai: bool,
    tahun_baseline: int | None,
    progres_2029: float | None,
    progres_2045: float | None,
    target_2029: float | None,
    target_2045: float | None,
    sedang_membaik: bool | None,
) -> str:
    """Kalimat ringkas di halaman capaian.

    Sengaja mengikuti angka yang digambar cincin tracker — target 2029 — supaya
    angka yang dibaca dan angka yang dilihat tidak bercerita beda.
    """
    if not ada_nilai:
        return f"Data realisasi terverifikasi untuk {nama_wilayah} pada tahun yang dipilih belum tersedia."
    if target_2029 is None and target_2045 is None:
        return "Target 2029 dan 2045 belum tersedia sehingga progres belum dapat dihitung."

    tren = (
        "membaik"
        if sedang_membaik is True
        else "menjauh dari arah target"
        if sedang_membaik is False
        else "belum dapat dibandingkan dengan tahun sebelumnya"
    )
    if progres_2029 is not None:
        kalimat = (
            f"Capaian {tahun} berada pada {progres_2029}% perjalanan dari baseline "
            f"{tahun_baseline} menuju target 2029 dan trennya {tren}."
        )
        if target_2045 is not None:
            kalimat += f" Target akhir 2045 berada di {target_2045:g}."
        return kalimat
    if progres_2045 is not None:
        return (
            f"Target 2029 belum tersedia. Terhadap target akhir 2045, capaian {tahun} "
            f"berada pada {progres_2045}% perjalanan dari baseline {tahun_baseline} "
            f"dan trennya {tren}."
        )
    return f"Capaian {tahun} tersedia, tetapi progres belum dapat dihitung lengkap."
