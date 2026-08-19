"""Fixture aplikasi untuk tes kontrak API.

Skema selalu dibangun oleh migrasi Alembic yang sama dengan produksi. Isinya
berasal dari benih uji yang ringkas dan ikut ter-commit, sehingga tes kontrak
tetap berjalan di CI setelah `data/` dikeluarkan dari version control.

Berkas produksi (`data/processed/sebatik.db`) tidak dibutuhkan di sini. Tes yang
memang menguji *isi* data sungguhan berdiri terpisah di `test_beranda_makro.py`
dan melewatkan dirinya sendiri bila berkas itu tidak ada.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
SUMBER_SQLITE = REPO_ROOT / "data" / "processed" / "sebatik.db"

SANDI_ADMIN = "Sebatik-Uji-Kontrak-2026!"
KODE_PROVINSI = "65"
BULUNGAN = "6501"


def _bangun_skema(url: str) -> None:
    config = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    lama = os.environ.get("SEBATIK_DATABASE_URL")
    os.environ["SEBATIK_DATABASE_URL"] = url
    try:
        command.upgrade(config, "head")
    finally:
        if lama is None:
            os.environ.pop("SEBATIK_DATABASE_URL", None)
        else:
            os.environ["SEBATIK_DATABASE_URL"] = lama


def _isi_benih(sesi: Session) -> None:
    """Data seminimal mungkin yang tetap menyentuh semua bentuk respons.

    Yang perlu terwakili: indikator makro dan non-makro, indikator belum
    terverifikasi, nilai provinsi dan wilayah, nilai tahunan dan periodik,
    nilai berupa teks, target 2029 dan 2045, serta satu usulan berbukti.
    """
    from backend.app.models import (
        BuktiDukung,
        Indikator,
        JenisNilai,
        MetadataIndikator,
        NilaiIndikator,
        Peran,
        StatusVerifikasi,
        UsulanNilai,
    )
    from backend.app.security import hash_password

    sekarang = datetime.now(UTC)

    def indikator(id_indikator: str, nama: str, **ubah):
        baku = {
            "kategori": id_indikator.split("-")[0],
            "nomor": int(id_indikator.split("-")[1]),
            "kode_indikator": id_indikator.split("-")[1].lstrip("0") or "0",
            "nama_indikator": nama,
            "kelompok": "Transformasi Ekonomi",
            "arah_pembangunan": "Peningkatan produktivitas",
            "sasaran_visi": "1",
            "misi_agenda": "2",
            "arah_ie": "IE3",
            "indikator_induk": "4",
            "satuan": "Persen (%)",
            "opd_pengampu": "BPS",
            "tim_pjk": "Neraca",
            "status_metadata": "LENGKAP",
            "tahun_terakhir": 2025,
            "is_proxy": False,
            "arah_baik": "NAIK",
            "arah_baik_terverifikasi": True,
            "status_verifikasi": StatusVerifikasi.DISETUJUI,
            "diverifikasi_pada": sekarang,
        }
        return Indikator(id_indikator=id_indikator, **{**baku, **ubah})

    sesi.add_all(
        [
            indikator("ISV-001", "PDRB per Kapita", kelompok_makro="Makro Ekonomi"),
            indikator("ISV-002", "Tingkat kemiskinan", arah_baik="TURUN", kelompok_makro="Makro Sosial"),
            indikator("ISV-005", "Rasio gini", arah_baik="TURUN", is_proxy=True),
            indikator("IUP-001", "Usia Harapan Hidup", kelompok="Transformasi Sosial"),
            # Belum terverifikasi: harus tidak pernah muncul di endpoint publik.
            indikator(
                "IUP-002",
                "Indikator Belum Diverifikasi",
                status_verifikasi=StatusVerifikasi.MENUNGGU,
                sasaran_visi="-",
            ),
        ]
    )
    sesi.flush()

    for id_indikator in ("ISV-001", "ISV-002", "ISV-005", "IUP-001"):
        sesi.add(
            MetadataIndikator(
                id_indikator=id_indikator,
                definisi=f"Definisi {id_indikator}.",
                rumus_mentah="a / b × 100",
                interpretasi="Makin tinggi makin baik.",
                sumber_data="Susenas",
                frekuensi="Tahunan",
                status_metadata="LENGKAP",
                sumber_metadata="RPJPD Provinsi",
                perlu_verifikasi_manual=False,
            )
        )

    def nilai(id_indikator, tahun, jenis, angka, **ubah):
        baku = {
            "wilayah_kode": KODE_PROVINSI,
            "sumber": "benih uji",
            "status_verifikasi": StatusVerifikasi.DISETUJUI,
            "diverifikasi_pada": sekarang,
        }
        return NilaiIndikator(id_indikator=id_indikator, tahun=tahun, jenis=jenis, nilai=angka, **{**baku, **ubah})

    baris = []
    for tahun, angka in enumerate(range(2021, 2026)):
        _ = tahun
        for id_indikator, dasar in (("ISV-001", 100.0), ("ISV-002", 8.0), ("ISV-005", 0.3), ("IUP-001", 70.0)):
            baris.append(nilai(id_indikator, angka, JenisNilai.REALISASI, dasar + (angka - 2021)))
            baris.append(nilai(id_indikator, angka, JenisNilai.TARGET, dasar + (angka - 2021) + 1))
    # Target horizon jangka panjang: dibutuhkan tracker capaian dan endpoint gap.
    for id_indikator, akhir in (("ISV-001", 200.0), ("ISV-002", 3.0), ("ISV-005", 0.2), ("IUP-001", 80.0)):
        baris.append(nilai(id_indikator, 2029, JenisNilai.TARGET, akhir * 0.6))
        baris.append(nilai(id_indikator, 2045, JenisNilai.TARGET, akhir))
    # Rilis semester: harus menggantikan angka tahunan saat ditampilkan.
    baris.append(nilai("ISV-001", 2025, JenisNilai.REALISASI, 106.5, periode=2, label_periode="Semester 2"))
    # Nilai berupa teks asli dari master.
    baris.append(
        nilai("IUP-001", 2020, JenisNilai.REALISASI, None, nilai_teks="70,5", satuan_catatan="angka sementara")
    )
    sesi.add_all(baris)
    sesi.flush()

    admin = None
    for username, nama, peran, wilayah in (
        ("admin", "Administrator Uji", Peran.ADMIN, KODE_PROVINSI),
        ("verifikator.65", "Verifikator Provinsi", Peran.VERIFIKATOR, KODE_PROVINSI),
        ("operator.6501.1", "Operator Bulungan", Peran.OPERATOR, BULUNGAN),
    ):
        from backend.app.models import Pengguna

        akun = Pengguna(
            username=username,
            nama=nama,
            password_hash=hash_password(SANDI_ADMIN),
            peran=peran,
            wilayah_kode=wilayah,
            harus_ganti_password=False,
        )
        sesi.add(akun)
        if username == "admin":
            admin = akun
    sesi.flush()

    operator = sesi.query(type(admin)).filter_by(username="operator.6501.1").one()
    usulan = UsulanNilai(
        id_indikator="ISV-001",
        wilayah_kode=BULUNGAN,
        tahun=2025,
        jenis=JenisNilai.REALISASI,
        nilai=95.0,
        sumber="Publikasi BRS",
        status=StatusVerifikasi.DISETUJUI,
        pengusul_id=operator.id,
        verifikator_id=admin.id,
        diverifikasi_pada=sekarang,
    )
    sesi.add(usulan)
    sesi.flush()
    sesi.add(
        BuktiDukung(
            usulan_id=usulan.id,
            nama_file="bukti.pdf",
            path_file="/tmp/bukti.pdf",
            mime_type="application/pdf",
            ukuran=1024,
            checksum_sha256="a" * 64,
        )
    )
    # Nilai wilayah yang terbit dari usulan itu.
    sesi.add(
        nilai(
            "ISV-001",
            2025,
            JenisNilai.REALISASI,
            95.0,
            wilayah_kode=BULUNGAN,
            usulan_id=usulan.id,
        )
    )
    sesi.commit()


@pytest.fixture(scope="session")
def db_uji(tmp_path_factory: pytest.TempPathFactory) -> str:
    berkas = tmp_path_factory.mktemp("api") / "sebatik-kontrak.db"
    url = f"sqlite:///{berkas.as_posix()}"
    _bangun_skema(url)

    mesin = create_engine(url)
    pabrik = sessionmaker(bind=mesin, autoflush=False)
    with pabrik() as sesi:
        _isi_benih(sesi)
    mesin.dispose()
    return url


@pytest.fixture(scope="session")
def client(db_uji: str) -> Iterator[TestClient]:
    from backend.app.deps import get_session
    from backend.app.main import create_app

    mesin = create_engine(db_uji)

    @event.listens_for(mesin, "connect")
    def _nyalakan_foreign_key(koneksi_dbapi, _catatan):  # pragma: no cover - hook
        kursor = koneksi_dbapi.cursor()
        kursor.execute("PRAGMA foreign_keys=ON")
        kursor.close()

    pabrik = sessionmaker(bind=mesin, autoflush=False, autocommit=False)

    def sesi_uji():
        sesi = pabrik()
        try:
            yield sesi
        finally:
            sesi.close()

    app = create_app()
    app.dependency_overrides[get_session] = sesi_uji
    # raise_server_exceptions=False supaya galat server terlihat sebagai 500
    # pada tes, sama seperti yang dilihat klien sungguhan.
    with TestClient(app, raise_server_exceptions=False) as klien:
        yield klien
    mesin.dispose()


@pytest.fixture(autouse=True)
def bersihkan_pembatas_login():
    """Kosongkan hitungan percobaan masuk sebelum dan sesudah setiap tes.

    `pembatas_login` adalah keadaan bersama satu proses. Tanpa pembersihan ini,
    tes yang sengaja menghabiskan jatah (test_keamanan_http.py) membuat login di
    modul lain balas 429, dan kegagalannya muncul di tempat yang sama sekali
    tidak berhubungan — bergantung urutan tes.
    """
    from backend.app.services.pembatas import pembatas_login

    pembatas_login.kosongkan()
    yield
    pembatas_login.kosongkan()


@pytest.fixture(scope="session")
def auth(client: TestClient) -> dict[str, str]:
    """Header Authorization untuk akun admin uji."""
    response = client.post("/api/v1/auth/login", data={"username": "admin", "password": SANDI_ADMIN})
    assert response.status_code == 200, "akun admin benih harus dapat masuk"
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="session")
def client_produksi(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    """Aplikasi di atas salinan data produksi yang sudah dipindahkan.

    Dipakai hanya oleh tes regresi tingkat data. Melewatkan diri bila berkas
    SQLite lama tidak tersedia — misalnya di CI, yang tidak memuat `data/`.
    """
    if not SUMBER_SQLITE.exists():
        pytest.skip(f"Basis data produksi tidak tersedia: {SUMBER_SQLITE}")

    from backend.app.deps import get_session
    from backend.app.main import create_app
    from scripts.migrasi_ke_skema_target import jalankan

    berkas = tmp_path_factory.mktemp("produksi") / "sebatik-produksi.db"
    url = f"sqlite:///{berkas.as_posix()}"
    _bangun_skema(url)
    if jalankan(SUMBER_SQLITE, url, kosongkan=False) != 0:
        pytest.fail("Pemindahan data produksi untuk tes regresi gagal")

    mesin = create_engine(url)
    pabrik = sessionmaker(bind=mesin, autoflush=False, autocommit=False)

    def sesi_uji():
        sesi = pabrik()
        try:
            yield sesi
        finally:
            sesi.close()

    app = create_app()
    app.dependency_overrides[get_session] = sesi_uji
    with TestClient(app, raise_server_exceptions=False) as klien:
        yield klien
    mesin.dispose()
