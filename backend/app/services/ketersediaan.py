"""Perhitungan kelengkapan slot data pada empat lapis klasifikasi."""

from __future__ import annotations

from typing import NamedTuple

from sqlalchemy.orm import Session

from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai

# Rentang tahun realisasi yang dihitung sebagai "slot" ketersediaan.
TAHUN_AWAL = 2021
TAHUN_AKHIR = 2025
JUMLAH_SLOT_PER_INDIKATOR = TAHUN_AKHIR - TAHUN_AWAL + 1

# (kolom klasifikasi, label tampil, jumlah kelompok menurut dokumen RPJPD).
DIMENSI: tuple[tuple[str, str, int], ...] = (
    ("sasaran_visi", "Sasaran Visi", 5),
    ("misi_agenda", "Misi/Agenda Pembangunan", 8),
    ("arah_ie", "Arah Pembangunan", 17),
    ("indikator_induk", "Indikator Utama Induk", 45),
)


class Kelompok(NamedTuple):
    kode: str
    label: str
    jumlah_kelompok: int
    jumlah_indikator: int
    slot_terisi: int
    slot_total: int
    persentase: float


def ketersediaan_kelompok(session: Session) -> list[dict[str, object]]:
    """Kelengkapan slot realisasi per dimensi klasifikasi."""
    hasil = []
    for kolom, label, jumlah_kelompok in DIMENSI:
        id_indikator = repo_indikator.id_berklasifikasi(session, kolom)
        terisi = repo_nilai.hitung_slot_terisi(session, id_indikator, TAHUN_AWAL, TAHUN_AKHIR)
        total = len(id_indikator) * JUMLAH_SLOT_PER_INDIKATOR
        hasil.append(
            Kelompok(
                kode=kolom,
                label=label,
                jumlah_kelompok=jumlah_kelompok,
                jumlah_indikator=len(id_indikator),
                slot_terisi=terisi,
                slot_total=total,
                persentase=round(terisi / total * 100, 1) if total else 0,
            )._asdict()
        )
    return hasil
