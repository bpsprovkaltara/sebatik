"""Aturan dan alur keputusan verifikasi usulan nilai.

Titik kritis refactoring (backend.md §3). Sebelumnya satu keputusan menulis ke
enam tabel sekaligus; sekarang satu keputusan menulis **satu** baris
`nilai_indikator` di dalam **satu** transaksi.

Aturan validasinya dipisah menjadi fungsi murni supaya dapat diuji tanpa basis
data dan tidak bisa terlewat oleh jalur pemanggilan baru.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import NamedTuple

from sqlalchemy.orm import Session

from ..models import KODE_PROVINSI, JenisNilai, Peran, StatusVerifikasi, UsulanNilai
from ..repositories import nilai as repo_nilai
from ..repositories import tata_kelola as repo_tata_kelola

KEPUTUSAN_SAH = (StatusVerifikasi.DISETUJUI, StatusVerifikasi.DITOLAK)


class Penolakan(NamedTuple):
    """Alasan sebuah tindakan tidak diizinkan, beserta kode HTTP-nya."""

    kode: int
    pesan: str


def periksa_pengusulan(
    *, peran: str, jenis: str, wilayah_operator: str | None, wilayah_diminta: str | None
) -> Penolakan | None:
    """Aturan siapa boleh mengusulkan apa."""
    if jenis not in tuple(JenisNilai):
        return Penolakan(422, "Jenis tidak valid")
    if peran == Peran.OPERATOR and jenis != JenisNilai.REALISASI:
        return Penolakan(403, "Operator hanya dapat mengusulkan nilai realisasi")
    lingkup = wilayah_operator if peran == Peran.OPERATOR else wilayah_diminta
    if not lingkup:
        return Penolakan(422, "Wilayah tidak valid")
    return None


def lingkup_wilayah(*, peran: str, wilayah_operator: str | None, wilayah_diminta: str | None) -> str | None:
    """Wilayah yang berlaku untuk usulan: operator selalu terkunci ke wilayahnya."""
    return wilayah_operator if peran == Peran.OPERATOR else wilayah_diminta


def periksa_keputusan(
    *,
    keputusan: str,
    alasan: str | None,
    peran_verifikator: str,
    wilayah_verifikator: str | None,
    pengusul_id: int,
    verifikator_id: int | None,
) -> Penolakan | None:
    """Semua aturan yang membatasi siapa boleh memutuskan apa."""
    if keputusan not in KEPUTUSAN_SAH:
        return Penolakan(422, "Keputusan tidak valid")
    if verifikator_id is not None and pengusul_id == verifikator_id:
        return Penolakan(403, "Pengusul tidak boleh memverifikasi usulannya sendiri")
    if peran_verifikator == Peran.VERIFIKATOR and wilayah_verifikator != KODE_PROVINSI:
        return Penolakan(403, "Verifikator harus bertugas di tingkat provinsi")
    if keputusan == StatusVerifikasi.DITOLAK and not alasan:
        return Penolakan(422, "Alasan wajib untuk penolakan")
    return None


def label_periode(periode: int | None) -> str | None:
    return f"Semester {periode}" if periode else None


def putuskan(
    session: Session,
    usulan: UsulanNilai,
    *,
    keputusan: str,
    alasan: str | None,
    verifikator_id: int,
) -> None:
    """Terapkan keputusan verifikasi dalam satu transaksi.

    Pemanggil bertanggung jawab menjalankan validasi (`periksa_keputusan`)
    lebih dulu; fungsi ini hanya menulis.
    """
    waktu = datetime.now(UTC)

    if keputusan == StatusVerifikasi.DISETUJUI:
        # Satu tabel, satu baris. Nilai semester dan nilai tahunan menempati
        # baris berbeda karena `periode` ikut dalam kunci alaminya.
        _, nilai_lama = repo_nilai.upsert(
            session,
            id_indikator=usulan.id_indikator,
            wilayah_kode=usulan.wilayah_kode or KODE_PROVINSI,
            tahun=usulan.tahun,
            jenis=usulan.jenis,
            periode=usulan.periode,
            nilai=float(usulan.nilai),
            label_periode=label_periode(usulan.periode),
            sumber=usulan.sumber,
            usulan_id=usulan.id,
            status_verifikasi=StatusVerifikasi.DISETUJUI,
            diverifikasi_pada=waktu,
        )
        repo_tata_kelola.catat_perubahan(
            session,
            pengguna_id=verifikator_id,
            id_indikator=usulan.id_indikator,
            field="nilai",
            nilai_lama=None if nilai_lama is None else str(nilai_lama),
            nilai_baru=str(usulan.nilai),
            sumber_perubahan="form",
            referensi_id=str(usulan.id),
            catatan=usulan.catatan,
        )

    repo_tata_kelola.putuskan_usulan(
        usulan,
        keputusan=keputusan,
        alasan=alasan,
        verifikator_id=verifikator_id,
        waktu=waktu,
    )
    repo_tata_kelola.catat_aktivitas(
        session,
        pengguna_id=verifikator_id,
        aksi="SETUJUI_USULAN" if keputusan == StatusVerifikasi.DISETUJUI else "TOLAK_USULAN",
        objek_tipe="usulan_nilai",
        objek_id=str(usulan.id),
        detail={
            "keputusan": keputusan,
            "alasan": alasan,
            "indikator": usulan.id_indikator,
            "wilayah": usulan.wilayah_kode,
        },
    )
    session.commit()
