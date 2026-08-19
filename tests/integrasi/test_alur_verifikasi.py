"""Alur verifikasi end-to-end terhadap basis data sungguhan.

Fokusnya satu klaim yang menjadi alasan utama refactoring ini: satu keputusan
verifikasi menulis **satu** baris `nilai_indikator`, bukan menyebar ke enam
tabel seperti `verify_submission` lama.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from backend.app.models import (
    Indikator,
    JenisNilai,
    LogAktivitas,
    LogPerubahan,
    NilaiIndikator,
    Peran,
    StatusVerifikasi,
)
from backend.app.repositories import nilai as repo_nilai
from backend.app.repositories import pengguna as repo_pengguna
from backend.app.repositories import tata_kelola as repo_tata_kelola
from backend.app.services import verifikasi as svc

PROVINSI = "65"
BULUNGAN = "6501"


@pytest.fixture
def dunia(session):
    """Satu indikator, satu operator, satu verifikator."""
    session.add(
        Indikator(
            id_indikator="ISV-001",
            kategori="ISV",
            nama_indikator="Tingkat kemiskinan",
            is_proxy=False,
            arah_baik_terverifikasi=False,
            status_verifikasi=StatusVerifikasi.DISETUJUI,
        )
    )
    operator = repo_pengguna.buat(
        session,
        username="operator.6501.1",
        nama="Operator Bulungan",
        password_hash="x",
        peran=Peran.OPERATOR,
        wilayah_kode=BULUNGAN,
    )
    verifikator = repo_pengguna.buat(
        session,
        username="verifikator.65",
        nama="Verifikator Provinsi",
        password_hash="x",
        peran=Peran.VERIFIKATOR,
        wilayah_kode=PROVINSI,
    )
    session.flush()
    return operator, verifikator


def _usulan(session, operator, **ubah):
    kolom = {
        "id_indikator": "ISV-001",
        "wilayah_kode": BULUNGAN,
        "tahun": 2025,
        "jenis": JenisNilai.REALISASI,
        "nilai": 7.5,
        "sumber": "Publikasi BRS",
        "pengusul_id": operator.id,
    }
    return repo_tata_kelola.buat_usulan(session, **{**kolom, **ubah})


def _jumlah_nilai(session) -> int:
    return session.scalar(select(func.count()).select_from(NilaiIndikator)) or 0


def test_persetujuan_menulis_tepat_satu_baris(session, dunia):
    """Klaim inti refactoring: satu keputusan, satu baris fakta."""
    operator, verifikator = dunia
    usulan = _usulan(session, operator)
    assert _jumlah_nilai(session) == 0

    svc.putuskan(
        session,
        usulan,
        keputusan=StatusVerifikasi.DISETUJUI,
        alasan=None,
        verifikator_id=verifikator.id,
    )

    assert _jumlah_nilai(session) == 1
    baris = session.scalars(select(NilaiIndikator)).one()
    assert (baris.id_indikator, baris.wilayah_kode, baris.tahun) == ("ISV-001", BULUNGAN, 2025)
    assert baris.nilai == 7.5
    assert baris.periode is None
    assert baris.usulan_id == usulan.id
    assert baris.status_verifikasi == StatusVerifikasi.DISETUJUI
    assert baris.diverifikasi_pada is not None


def test_penolakan_tidak_menyentuh_angka_publik(session, dunia):
    operator, verifikator = dunia
    usulan = _usulan(session, operator)

    svc.putuskan(
        session,
        usulan,
        keputusan=StatusVerifikasi.DITOLAK,
        alasan="Bukti tidak memadai",
        verifikator_id=verifikator.id,
    )

    assert _jumlah_nilai(session) == 0
    assert usulan.status == StatusVerifikasi.DITOLAK
    assert usulan.alasan_verifikasi == "Bukti tidak memadai"
    # Penolakan tetap tercatat di audit tindakan, tetapi bukan di log nilai.
    assert session.scalar(select(func.count()).select_from(LogPerubahan)) == 0
    assert session.scalar(select(func.count()).select_from(LogAktivitas)) == 1


def test_persetujuan_kedua_memperbarui_baris_yang_sama(session, dunia):
    """Revisi nilai tidak boleh menumpuk baris fakta."""
    operator, verifikator = dunia
    pertama = _usulan(session, operator, nilai=7.5)
    svc.putuskan(
        session,
        pertama,
        keputusan=StatusVerifikasi.DISETUJUI,
        alasan=None,
        verifikator_id=verifikator.id,
    )
    kedua = _usulan(session, operator, nilai=7.1)
    svc.putuskan(
        session,
        kedua,
        keputusan=StatusVerifikasi.DISETUJUI,
        alasan=None,
        verifikator_id=verifikator.id,
    )

    assert _jumlah_nilai(session) == 1
    baris = session.scalars(select(NilaiIndikator)).one()
    assert baris.nilai == 7.1
    assert baris.usulan_id == kedua.id
    # Nilai lama terekam di log perubahan, bukan hilang tanpa jejak.
    log = session.scalars(select(LogPerubahan).order_by(LogPerubahan.id)).all()
    assert [(x.nilai_lama, x.nilai_baru) for x in log] == [(None, "7.5"), ("7.5", "7.1")]


def test_nilai_semester_dan_tahunan_berdampingan(session, dunia):
    """Periode ikut dalam kunci alami, jadi keduanya baris terpisah."""
    operator, verifikator = dunia
    for periode, nilai in ((None, 7.5), (1, 7.8), (2, 7.2)):
        usulan = _usulan(session, operator, periode=periode, nilai=nilai)
        svc.putuskan(
            session,
            usulan,
            keputusan=StatusVerifikasi.DISETUJUI,
            alasan=None,
            verifikator_id=verifikator.id,
        )

    assert _jumlah_nilai(session) == 3
    terbaru = repo_nilai.nilai_periode_terbaru(session, "ISV-001", BULUNGAN, 2025)
    assert (terbaru.periode, terbaru.nilai, terbaru.label_periode) == (2, 7.2, "Semester 2")
    # Angka tahunan tetap utuh dan tidak tertimpa rilis semester.
    tahunan = repo_nilai.ambil(session, "ISV-001", BULUNGAN, 2025, JenisNilai.REALISASI)
    assert tahunan.nilai == 7.5


def test_nilai_provinsi_dan_wilayah_tidak_saling_menimpa(session, dunia):
    """Bug lama: satu persetujuan menulis provinsi sekaligus wilayah."""
    operator, verifikator = dunia
    for wilayah, nilai in ((BULUNGAN, 7.5), (PROVINSI, 6.1)):
        usulan = _usulan(session, operator, wilayah_kode=wilayah, nilai=nilai)
        svc.putuskan(
            session,
            usulan,
            keputusan=StatusVerifikasi.DISETUJUI,
            alasan=None,
            verifikator_id=verifikator.id,
        )

    assert repo_nilai.ambil(session, "ISV-001", BULUNGAN, 2025, JenisNilai.REALISASI).nilai == 7.5
    assert repo_nilai.ambil(session, "ISV-001", PROVINSI, 2025, JenisNilai.REALISASI).nilai == 6.1


def test_usulan_yang_sudah_diputus_tidak_dapat_diputus_ulang(session, dunia):
    operator, verifikator = dunia
    usulan = _usulan(session, operator)
    svc.putuskan(
        session,
        usulan,
        keputusan=StatusVerifikasi.DISETUJUI,
        alasan=None,
        verifikator_id=verifikator.id,
    )
    assert repo_tata_kelola.ambil_usulan_menunggu(session, usulan.id) is None
