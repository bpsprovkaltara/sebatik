"""Aturan dan alur keputusan verifikasi usulan nilai.

Titik kritis refactoring (backend.md §3). Sebelumnya satu keputusan menulis ke
enam tabel sekaligus; sekarang satu keputusan menulis **satu** baris
`nilai_indikator` di dalam **satu** transaksi.

Aturan validasinya dipisah menjadi fungsi murni supaya dapat diuji tanpa basis
data dan tidak bisa terlewat oleh jalur pemanggilan baru.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ..models import KODE_PROVINSI, JenisNilai, Peran, StatusVerifikasi, UsulanNilai
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..repositories import tata_kelola as repo_tata_kelola
from . import Penolakan
from . import bukti as svc_bukti

KEPUTUSAN_SAH = (StatusVerifikasi.DISETUJUI, StatusVerifikasi.DITOLAK)


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
    if peran_verifikator != Peran.VERIFIKATOR:
        return Penolakan(403, "Keputusan hanya dapat dilakukan oleh verifikator")
    if verifikator_id is not None and pengusul_id == verifikator_id:
        return Penolakan(403, "Pengusul tidak boleh memverifikasi usulannya sendiri")
    if wilayah_verifikator != KODE_PROVINSI:
        return Penolakan(403, "Verifikator harus bertugas di tingkat provinsi")
    if keputusan == StatusVerifikasi.DITOLAK and not alasan:
        return Penolakan(422, "Alasan wajib untuk penolakan")
    return None


def label_periode(periode: int | None, periode_data: str | None = None) -> str | None:
    if not periode:
        return None
    jenis = "Triwulan" if periode_data and "triwulan" in periode_data.lower() else "Semester"
    return f"{jenis} {periode}"


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
        indikator = repo_indikator.ambil(session, usulan.id_indikator)
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
            label_periode=label_periode(usulan.periode, indikator.periode_data if indikator else None),
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


PERIODE_SAH = (None, 1, 2, 3, 4)


def periode_sah(periode: int | None) -> bool:
    return periode in PERIODE_SAH


def ajukan(
    session: Session,
    *,
    id_indikator: str,
    wilayah_kode: str | None,
    tahun: int,
    jenis: str,
    periode: int | None,
    nilai: float,
    sumber: str,
    catatan: str | None,
    pengusul_id: int,
    lampiran: Sequence[svc_bukti.Lampiran],
) -> UsulanNilai:
    """Simpan usulan beserta bukti dukungnya dalam satu transaksi.

    Pemanggil bertanggung jawab memvalidasi lampiran (`bukti.periksa_lampiran`)
    lebih dulu; di sini berkas sudah dianggap layak ditulis.
    """
    usulan = repo_tata_kelola.buat_usulan(
        session,
        id_indikator=id_indikator,
        wilayah_kode=wilayah_kode,
        tahun=tahun,
        jenis=jenis,
        periode=periode,
        nilai=nilai,
        sumber=sumber,
        catatan=catatan,
        pengusul_id=pengusul_id,
    )
    for berkas in lampiran:
        siap = svc_bukti.simpan(usulan.id, berkas.nama_file, berkas.isi, berkas.mime_type)
        repo_tata_kelola.catat_bukti(
            session,
            usulan_id=usulan.id,
            nama_file=siap.nama_file,
            path_file=str(siap.path_file),
            mime_type=siap.mime_type,
            ukuran=siap.ukuran,
            checksum_sha256=siap.checksum_sha256,
        )
    repo_tata_kelola.catat_aktivitas(
        session,
        pengguna_id=pengusul_id,
        aksi="KIRIM_USULAN",
        objek_tipe="usulan_nilai",
        objek_id=str(usulan.id),
        detail={
            "indikator": id_indikator,
            "tahun": tahun,
            "jenis": jenis,
            "wilayah": wilayah_kode,
            "jumlah_bukti": len(lampiran),
        },
    )
    session.commit()
    return usulan
