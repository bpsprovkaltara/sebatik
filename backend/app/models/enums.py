"""Nilai enum domain.

Menggantikan literal string yang tersebar (`"DISETUJUI"`, `"realisasi"`, `"65"`,
…). Semua memakai `str` sebagai basis agar perbandingan dengan nilai kolom dan
serialisasi JSON tetap apa adanya.
"""

from __future__ import annotations

from enum import StrEnum


class Peran(StrEnum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VERIFIKATOR = "VERIFIKATOR"
    PENGUNJUNG = "PENGUNJUNG"


class JenisNilai(StrEnum):
    # Huruf kecil: bentuk ini sudah menjadi bagian kontrak API publik.
    REALISASI = "realisasi"
    TARGET = "target"


class StatusVerifikasi(StrEnum):
    MENUNGGU = "MENUNGGU_VERIFIKASI"
    DISETUJUI = "DISETUJUI"
    DITOLAK = "DITOLAK"


class StatusUnggahan(StrEnum):
    MENUNGGU_PERSETUJUAN = "MENUNGGU_PERSETUJUAN"
    DISETUJUI = "DISETUJUI"
    DITOLAK = "DITOLAK"


class TingkatWilayah(StrEnum):
    PROVINSI = "PROVINSI"
    KABUPATEN = "KABUPATEN"
    KOTA = "KOTA"


class ArahBaik(StrEnum):
    NAIK = "NAIK"
    TURUN = "TURUN"


class StatusRpjmd(StrEnum):
    """Nilai yang dihasilkan `src.etl.common.enum_rpjmd`."""

    MASUK_RPJMD = "MASUK_RPJMD"
    TIDAK_MASUK_RPJMD = "TIDAK_MASUK_RPJMD"
    MASUK_TAPI_BELUM_ADA_DATA = "MASUK_TAPI_BELUM_ADA_DATA"
    DOBEL_ISV_IUP = "DOBEL_ISV_IUP"


PERAN = tuple(Peran)
JENIS_NILAI = tuple(JenisNilai)
STATUS_VERIFIKASI = tuple(StatusVerifikasi)
