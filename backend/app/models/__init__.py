"""Model ORM skema konsolidasi.

Mengimpor seluruh model di satu tempat supaya `Base.metadata` lengkap ketika
Alembic melakukan autogenerate dan ketika tes membangun skema.
"""

from __future__ import annotations

from ..db.base import Base
from .enums import (
    JENIS_NILAI,
    PERAN,
    STATUS_VERIFIKASI,
    ArahBaik,
    JenisNilai,
    Peran,
    StatusRpjmd,
    StatusUnggahan,
    StatusVerifikasi,
    TingkatWilayah,
)
from .indikator import Indikator, MetadataIndikator, NilaiIndikator
from .pengguna import Pengguna
from .tata_kelola import (
    BuktiDukung,
    LogAktivitas,
    LogPerubahan,
    PenugasanPic,
    SnapshotKetersediaan,
    UnggahanExcel,
    UsulanNilai,
)
from .wilayah import KODE_PROVINSI, Wilayah

__all__ = [
    "JENIS_NILAI",
    "KODE_PROVINSI",
    "PERAN",
    "STATUS_VERIFIKASI",
    "ArahBaik",
    "Base",
    "BuktiDukung",
    "Indikator",
    "JenisNilai",
    "LogAktivitas",
    "LogPerubahan",
    "MetadataIndikator",
    "NilaiIndikator",
    "Pengguna",
    "PenugasanPic",
    "Peran",
    "SnapshotKetersediaan",
    "StatusRpjmd",
    "StatusUnggahan",
    "StatusVerifikasi",
    "TingkatWilayah",
    "UnggahanExcel",
    "UsulanNilai",
    "Wilayah",
]
