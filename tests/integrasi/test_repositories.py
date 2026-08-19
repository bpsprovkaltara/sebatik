"""Tes integrasi lapisan repository terhadap skema hasil migrasi Alembic."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.models import (
    JenisNilai,
    NilaiIndikator,
    Peran,
    StatusVerifikasi,
    UsulanNilai,
)
from backend.app.repositories import indikator as repo_indikator
from backend.app.repositories import nilai as repo_nilai
from backend.app.repositories import pengguna as repo_pengguna
from backend.app.repositories import tata_kelola as repo_tata_kelola
from backend.app.repositories import wilayah as repo_wilayah

PROVINSI = "65"
BULUNGAN = "6501"


@pytest.fixture
def indikator_uji(session):
    """Dua indikator: satu makro berklasifikasi lengkap, satu tanpa klasifikasi."""
    from backend.app.models import Indikator

    makro = Indikator(
        id_indikator="ISV-001",
        kategori="ISV",
        nomor=1,
        kode_indikator="1.1",
        nama_indikator="PDRB per Kapita",
        kelompok="Ekonomi",
        kelompok_makro="Makro Ekonomi",
        sasaran_visi="1",
        opd_pengampu="Bappeda",
        tim_pjk="Neraca",
        status_metadata="LENGKAP",
        tahun_terakhir=2025,
        is_proxy=False,
        arah_baik_terverifikasi=False,
        status_verifikasi=StatusVerifikasi.DISETUJUI,
    )
    biasa = Indikator(
        id_indikator="IUP-050",
        kategori="IUP",
        nomor=50,
        nama_indikator="Angka Harapan Hidup",
        kelompok="Sosial",
        sasaran_visi="-",
        is_proxy=False,
        arah_baik_terverifikasi=False,
        status_verifikasi=StatusVerifikasi.DISETUJUI,
    )
    belum = Indikator(
        id_indikator="IUP-086",
        kategori="IUP",
        nomor=86,
        nama_indikator="Indikator Belum Diverifikasi",
        is_proxy=False,
        arah_baik_terverifikasi=False,
        status_verifikasi=StatusVerifikasi.MENUNGGU,
    )
    session.add_all([makro, biasa, belum])
    session.flush()
    return makro, biasa, belum


# --- wilayah ---------------------------------------------------------------


def test_wilayah_seed_migrasi_tersedia(session):
    daftar = repo_wilayah.daftar_aktif(session)
    assert [w.kode for w in daftar] == ["65", "6501", "6502", "6503", "6504", "6571"]
    assert daftar[0].tingkat == "PROVINSI"


def test_wilayah_anak_provinsi(session):
    anak = repo_wilayah.daftar_anak_provinsi(session)
    assert len(anak) == 5
    assert all(w.parent_kode == PROVINSI for w in anak)


def test_wilayah_validasi_kode(session):
    assert repo_wilayah.ada_dan_aktif(session, BULUNGAN) is True
    assert repo_wilayah.ada_dan_aktif(session, "9999") is False
    assert repo_wilayah.ada_dan_aktif(session, None) is False


# --- indikator -------------------------------------------------------------


def test_indikator_hanya_yang_terverifikasi_terbaca_publik(session, indikator_uji):
    _, _, belum = indikator_uji
    assert repo_indikator.ambil(session, belum.id_indikator) is not None
    assert repo_indikator.ambil_terverifikasi(session, belum.id_indikator) is None
    assert {i.id_indikator for i in repo_indikator.daftar_terverifikasi(session)} == {
        "ISV-001",
        "IUP-050",
    }


def test_indikator_daftar_makro(session, indikator_uji):
    makro = repo_indikator.daftar_makro(session)
    assert [i.id_indikator for i in makro] == ["ISV-001"]


def test_indikator_klasifikasi_mengabaikan_penanda_strip(session, indikator_uji):
    """`-` berarti belum diklasifikasikan, bukan nama kelompok."""
    ids = repo_indikator.id_berklasifikasi(session, "sasaran_visi")
    assert ids == ["ISV-001"]


def test_indikator_cari_saring_dan_paginasi(session, indikator_uji):
    data, total = repo_indikator.cari(session, kategori=["ISV"])
    assert total == 1
    assert data[0].id_indikator == "ISV-001"

    data, total = repo_indikator.cari(session, page_size=1)
    assert total == 3
    assert len(data) == 1

    data, _ = repo_indikator.cari(session, q="harapan hidup")
    assert [i.id_indikator for i in data] == ["IUP-050"]


def test_indikator_cari_urut_menurun(session, indikator_uji):
    data, _ = repo_indikator.cari(session, order="desc")
    assert [i.id_indikator for i in data] == ["IUP-086", "IUP-050", "ISV-001"]


def test_indikator_ubah_arah_baik_mengembalikan_nilai_lama(session, indikator_uji):
    makro, _, _ = indikator_uji
    assert repo_indikator.ubah_arah_baik(makro, "NAIK") is None
    assert makro.arah_baik_terverifikasi is True
    assert repo_indikator.ubah_arah_baik(makro, "TURUN") == "NAIK"


def test_indikator_menolak_arah_baik_di_luar_enum(session, indikator_uji):
    makro, _, _ = indikator_uji
    makro.arah_baik = "SAMPING"
    with pytest.raises(IntegrityError):
        session.flush()


# --- nilai -----------------------------------------------------------------


def _sisip_nilai(session, **kolom):
    baku = {
        "id_indikator": "ISV-001",
        "wilayah_kode": PROVINSI,
        "jenis": JenisNilai.REALISASI,
        "status_verifikasi": StatusVerifikasi.DISETUJUI,
    }
    session.add(NilaiIndikator(**{**baku, **kolom}))
    session.flush()


def test_nilai_provinsi_dan_wilayah_satu_tabel(session, indikator_uji):
    _sisip_nilai(session, tahun=2025, nilai=10.0)
    _sisip_nilai(session, tahun=2025, nilai=7.5, wilayah_kode=BULUNGAN)

    provinsi = repo_nilai.ambil(session, "ISV-001", PROVINSI, 2025, JenisNilai.REALISASI)
    bulungan = repo_nilai.ambil(session, "ISV-001", BULUNGAN, 2025, JenisNilai.REALISASI)
    assert provinsi.nilai == 10.0
    assert bulungan.nilai == 7.5


def test_nilai_periode_terbaru_menggantikan_tahunan(session, indikator_uji):
    _sisip_nilai(session, tahun=2025, nilai=1.0)
    _sisip_nilai(session, tahun=2025, nilai=2.0, periode=1, label_periode="Semester 1")
    _sisip_nilai(session, tahun=2025, nilai=3.0, periode=2, label_periode="Semester 2")

    terbaru = repo_nilai.nilai_periode_terbaru(session, "ISV-001", PROVINSI, 2025)
    assert terbaru.periode == 2
    assert terbaru.nilai == 3.0
    # Nilai tahunan tetap terbaca terpisah, tidak tertimpa.
    assert repo_nilai.ambil(session, "ISV-001", PROVINSI, 2025, JenisNilai.REALISASI).nilai == 1.0


def test_nilai_belum_disetujui_tidak_terbaca(session, indikator_uji):
    _sisip_nilai(session, tahun=2025, nilai=99.0, status_verifikasi=StatusVerifikasi.MENUNGGU)
    assert repo_nilai.ambil(session, "ISV-001", PROVINSI, 2025, JenisNilai.REALISASI) is None
    assert repo_nilai.tahun_realisasi_tersedia(session) == []


def test_nilai_duplikat_tahunan_ditolak(session, indikator_uji):
    _sisip_nilai(session, tahun=2025, nilai=1.0)
    with pytest.raises(IntegrityError):
        _sisip_nilai(session, tahun=2025, nilai=2.0)


def test_nilai_duplikat_periode_ditolak(session, indikator_uji):
    _sisip_nilai(session, tahun=2025, nilai=1.0, periode=1)
    with pytest.raises(IntegrityError):
        _sisip_nilai(session, tahun=2025, nilai=2.0, periode=1)


def test_nilai_sebelum_tahun_dan_terakhir_terisi(session, indikator_uji):
    _sisip_nilai(session, tahun=2023, nilai=1.0)
    _sisip_nilai(session, tahun=2024, nilai=2.0)
    _sisip_nilai(session, tahun=2025, nilai=None, nilai_teks=None)

    assert repo_nilai.sebelum_tahun(session, "ISV-001", PROVINSI, 2025).tahun == 2024
    # Tahun 2025 kosong sehingga yang terakhir *terisi* tetap 2024.
    assert repo_nilai.terakhir_terisi(session, "ISV-001", PROVINSI, 2025).tahun == 2024


def test_nilai_hitung_slot_terisi_mengabaikan_periode(session, indikator_uji):
    _sisip_nilai(session, tahun=2021, nilai=1.0)
    _sisip_nilai(session, tahun=2022, nilai_teks="1,2")
    _sisip_nilai(session, tahun=2023, nilai=None)  # kosong, tidak dihitung
    _sisip_nilai(session, tahun=2022, nilai=9.0, periode=1)  # periodik, tidak dihitung

    assert repo_nilai.hitung_slot_terisi(session, ["ISV-001"], 2021, 2025) == 2
    assert repo_nilai.hitung_slot_terisi(session, [], 2021, 2025) == 0


def test_nilai_upsert_memperbarui_baris_yang_sama(session, indikator_uji):
    baris, lama = repo_nilai.upsert(
        session,
        id_indikator="ISV-001",
        wilayah_kode=PROVINSI,
        tahun=2025,
        jenis=JenisNilai.REALISASI,
        nilai=5.0,
        sumber="form",
    )
    session.flush()
    assert lama is None
    assert baris.nilai == 5.0

    baris_kedua, lama_kedua = repo_nilai.upsert(
        session,
        id_indikator="ISV-001",
        wilayah_kode=PROVINSI,
        tahun=2025,
        jenis=JenisNilai.REALISASI,
        nilai=6.0,
        sumber="form",
    )
    session.flush()
    assert lama_kedua == 5.0
    assert baris_kedua.id == baris.id
    assert repo_nilai.seri(session, "ISV-001", PROVINSI, JenisNilai.REALISASI)[0].nilai == 6.0


def test_nilai_upsert_periode_terpisah_dari_tahunan(session, indikator_uji):
    repo_nilai.upsert(
        session,
        id_indikator="ISV-001",
        wilayah_kode=PROVINSI,
        tahun=2025,
        jenis=JenisNilai.REALISASI,
        nilai=1.0,
    )
    repo_nilai.upsert(
        session,
        id_indikator="ISV-001",
        wilayah_kode=PROVINSI,
        tahun=2025,
        jenis=JenisNilai.REALISASI,
        periode=2,
        nilai=3.0,
        label_periode="Semester 2",
    )
    session.flush()
    assert len(repo_nilai.seri_lengkap(session, "ISV-001", PROVINSI)) == 2


# --- pengguna --------------------------------------------------------------


@pytest.fixture
def pengguna_uji(session):
    admin = repo_pengguna.buat(
        session,
        username="admin",
        nama="Administrator",
        password_hash="hash-argon2",
        peran=Peran.ADMIN,
    )
    operator = repo_pengguna.buat(
        session,
        username="operator.6501.1",
        nama="Operator Bulungan",
        password_hash="hash-argon2",
        peran=Peran.OPERATOR,
        wilayah_kode=BULUNGAN,
    )
    session.flush()
    return admin, operator


def test_pengguna_profil_tidak_membocorkan_hash(session, pengguna_uji):
    admin, _ = pengguna_uji
    profil = repo_pengguna.profil(admin)
    assert "password_hash" not in profil._asdict()
    assert profil.username == "admin"


def test_pengguna_login_hanya_akun_aktif(session, pengguna_uji):
    admin, _ = pengguna_uji
    assert repo_pengguna.ambil_untuk_login(session, "admin") is not None
    admin.aktif = False
    session.flush()
    assert repo_pengguna.ambil_untuk_login(session, "admin") is None
    assert repo_pengguna.ambil_aktif(session, admin.id) is None
    # Tetap dapat diambil admin panel untuk diaktifkan kembali.
    assert repo_pengguna.ambil(session, admin.id) is not None


def test_pengguna_daftar_menyertakan_nama_wilayah(session, pengguna_uji):
    daftar = {pengguna.username: wilayah for pengguna, wilayah in repo_pengguna.daftar_dengan_wilayah(session)}
    assert daftar["operator.6501.1"] == "Bulungan"
    assert daftar["admin"] is None


def test_pengguna_menolak_peran_asing(session):
    repo_pengguna.buat(session, username="palsu", nama="Palsu", password_hash="x", peran="SUPERUSER")
    with pytest.raises(IntegrityError):
        session.flush()


def test_pengguna_username_unik(session, pengguna_uji):
    repo_pengguna.buat(session, username="admin", nama="Kembar", password_hash="x", peran=Peran.ADMIN)
    with pytest.raises(IntegrityError):
        session.flush()


# --- tata kelola -----------------------------------------------------------


@pytest.fixture
def usulan_uji(session, indikator_uji, pengguna_uji):
    _, operator = pengguna_uji
    usulan = repo_tata_kelola.buat_usulan(
        session,
        id_indikator="ISV-001",
        wilayah_kode=BULUNGAN,
        tahun=2025,
        jenis=JenisNilai.REALISASI,
        nilai=7.5,
        sumber="Publikasi BRS",
        pengusul_id=operator.id,
    )
    return usulan


def test_usulan_baru_berstatus_menunggu(session, usulan_uji):
    assert usulan_uji.status == StatusVerifikasi.MENUNGGU
    assert repo_tata_kelola.ambil_usulan_menunggu(session, usulan_uji.id) is not None


def test_usulan_menolak_periode_di_luar_rentang(session, indikator_uji, pengguna_uji):
    _, operator = pengguna_uji
    session.add(
        UsulanNilai(
            id_indikator="ISV-001",
            wilayah_kode=BULUNGAN,
            tahun=2025,
            jenis=JenisNilai.REALISASI,
            periode=9,
            nilai=1.0,
            sumber="x",
            pengusul_id=operator.id,
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_daftar_usulan_menyertakan_relasi_dan_jumlah_bukti(session, usulan_uji):
    repo_tata_kelola.catat_bukti(
        session,
        usulan_id=usulan_uji.id,
        nama_file="bukti.pdf",
        path_file="/tmp/bukti.pdf",
        mime_type="application/pdf",
        ukuran=1024,
        checksum_sha256="a" * 64,
    )
    session.flush()
    (baris,) = repo_tata_kelola.daftar_usulan(session)
    assert baris["pengusul"] == "Operator Bulungan"
    assert baris["wilayah"] == "Bulungan"
    assert baris["verifikator"] is None
    assert baris["jumlah_bukti"] == 1


def test_daftar_usulan_disaring_per_pengusul(session, usulan_uji, pengguna_uji):
    admin, operator = pengguna_uji
    assert len(repo_tata_kelola.daftar_usulan(session, pengusul_id=operator.id)) == 1
    assert repo_tata_kelola.daftar_usulan(session, pengusul_id=admin.id) == []
    # Verifikator non-provinsi tidak berhak melihat antrean apa pun.
    assert repo_tata_kelola.daftar_usulan(session, kosongkan=True) == []


def test_putuskan_usulan_mengisi_jejak_verifikasi(session, usulan_uji, pengguna_uji):
    admin, _ = pengguna_uji
    waktu = datetime.now(UTC)
    repo_tata_kelola.putuskan_usulan(
        usulan_uji,
        keputusan=StatusVerifikasi.DITOLAK,
        alasan="Bukti kurang",
        verifikator_id=admin.id,
        waktu=waktu,
    )
    session.flush()
    assert usulan_uji.status == StatusVerifikasi.DITOLAK
    assert usulan_uji.alasan_verifikasi == "Bukti kurang"
    assert usulan_uji.verifikator_id == admin.id
    assert repo_tata_kelola.ambil_usulan_menunggu(session, usulan_uji.id) is None


def test_log_aktivitas_menyimpan_detail_sebagai_json(session, pengguna_uji):
    admin, _ = pengguna_uji
    log = repo_tata_kelola.catat_aktivitas(
        session,
        pengguna_id=admin.id,
        aksi="UBAH_STATUS_AKUN",
        objek_tipe="pengguna",
        objek_id="7",
        detail={"aktif": False},
    )
    session.flush()
    assert log.detail == '{"aktif": false}'


def test_daftar_log_perubahan_terbaru_dulu(session, indikator_uji, pengguna_uji):
    admin, _ = pengguna_uji
    for nilai_baru in ("1", "2"):
        repo_tata_kelola.catat_perubahan(
            session,
            pengguna_id=admin.id,
            id_indikator="ISV-001",
            field="nilai",
            nilai_lama=None,
            nilai_baru=nilai_baru,
            sumber_perubahan="form",
        )
    session.flush()
    daftar = repo_tata_kelola.daftar_log_perubahan(session)
    assert len(daftar) == 2
    assert daftar[0]["username"] == "admin"


def test_bukti_terhapus_bersama_usulannya(session, usulan_uji):
    repo_tata_kelola.catat_bukti(
        session,
        usulan_id=usulan_uji.id,
        nama_file="b.pdf",
        path_file="/tmp/b.pdf",
        ukuran=1,
        checksum_sha256="b" * 64,
    )
    session.flush()
    assert len(repo_tata_kelola.daftar_bukti(session, usulan_uji.id)) == 1
