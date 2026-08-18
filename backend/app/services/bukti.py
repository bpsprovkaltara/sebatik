"""Penanganan berkas bukti dukung.

Nama berkas dari pengguna tidak pernah dipakai apa adanya, dan setiap path yang
akan dibaca diperiksa berada di dalam direktori bukti — path absolut yang
tersimpan di basis data tidak boleh menjadi jalan keluar ke berkas lain.
"""

from __future__ import annotations

import uuid
from hashlib import sha256
from pathlib import Path
from typing import NamedTuple

from ..config import settings

MIME_DIIZINKAN = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
)


class BuktiSiap(NamedTuple):
    nama_file: str
    path_file: Path
    mime_type: str | None
    ukuran: int
    checksum_sha256: str


def format_didukung(mime_type: str | None) -> bool:
    return mime_type in MIME_DIIZINKAN


def ukuran_wajar(jumlah_byte: int) -> bool:
    return jumlah_byte <= settings.max_bukti_bytes


def direktori_usulan(usulan_id: int) -> Path:
    return Path(settings.evidence_dir) / str(usulan_id)


def simpan(usulan_id: int, nama_asli: str | None, isi: bytes, mime_type: str | None) -> BuktiSiap:
    """Tulis satu berkas bukti dengan nama yang tidak dapat dikendalikan pengunggah."""
    tujuan = direktori_usulan(usulan_id)
    tujuan.mkdir(parents=True, exist_ok=True)
    # Prefiks uuid mencegah tabrakan nama; `Path(...).name` membuang komponen
    # direktori sehingga "../../etc/passwd" menjadi "passwd".
    nama_aman = f"{uuid.uuid4().hex}-{Path(nama_asli or 'bukti').name}"
    path = tujuan / nama_aman
    path.write_bytes(isi)
    return BuktiSiap(
        nama_file=nama_asli or "bukti",
        path_file=path,
        mime_type=mime_type,
        ukuran=len(isi),
        checksum_sha256=sha256(isi).hexdigest(),
    )


def path_boleh_dibaca(path_tersimpan: str) -> Path | None:
    """Path bukti yang aman dibaca, atau None bila di luar direktori bukti."""
    akar = Path(settings.evidence_dir).resolve()
    try:
        path = Path(path_tersimpan).resolve()
        path.relative_to(akar)
    except (ValueError, OSError):
        return None
    return path
