"""Tes skrip pemindahan data dari skema SQLite lama ke skema konsolidasi.

Memakai basis data sumber sintetis yang meniru bentuk asli (dua keluarga tabel
paralel dengan skema ID berbeda), sehingga kasus sulitnya dapat diuji tanpa
bergantung pada isi `data/processed/sebatik.db`.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app.models import Indikator, MetadataIndikator, NilaiIndikator, PenugasanPic
from scripts.migrasi_ke_skema_target import Laporan, jalankan, petakan_etl_ke_master

REPO_ROOT = Path(__file__).resolve().parents[2]

SKEMA_LAMA = """
CREATE TABLE indikator (
 id_indikator TEXT PRIMARY KEY, kategori TEXT NOT NULL, nomor INTEGER NOT NULL,
 nama_indikator TEXT NOT NULL, nama_asli TEXT, kelompok TEXT, arah_pembangunan TEXT,
 satuan TEXT, penghasil TEXT, kl_pengampu TEXT, opd_penanggung_jawab TEXT, tim_pjk TEXT,
 status_ketersediaan TEXT, status_metadata TEXT, periode_data TEXT, tahun_terakhir INTEGER,
 is_proxy INTEGER NOT NULL DEFAULT 0, nama_proxy TEXT, status_rpjmd TEXT NOT NULL,
 kode_sdgs TEXT, link_metadata TEXT, link_publikasi TEXT, link_data TEXT, catatan_teknis TEXT,
 arah_baik TEXT, arah_baik_terverifikasi INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE nilai_indikator (
 id_indikator TEXT, tahun INTEGER, jenis TEXT, nilai REAL, sumber_sheet TEXT,
 PRIMARY KEY(id_indikator,tahun,jenis)
);
CREATE TABLE metadata_indikator (
 id_indikator TEXT PRIMARY KEY, definisi TEXT, rumus TEXT, rumus_mentah TEXT,
 interpretasi TEXT, sumber_data TEXT, frekuensi TEXT, halaman_sumber TEXT,
 perlu_verifikasi_manual INTEGER NOT NULL DEFAULT 0, sumber_metadata TEXT, nama_di_buku1 TEXT
);
CREATE TABLE beranda_indikator (
 id_indikator TEXT PRIMARY KEY, kategori TEXT NOT NULL, kelompok TEXT, arah_pembangunan TEXT,
 kode_indikator TEXT, nama_indikator TEXT NOT NULL, is_proxy INTEGER NOT NULL DEFAULT 0,
 nama_proxy TEXT, satuan TEXT, sumber_data TEXT, frekuensi TEXT, opd_pengampu TEXT,
 status_ketersediaan TEXT, periode_data TEXT, sasaran_visi TEXT, misi_agenda TEXT,
 arah_ie TEXT, indikator_induk TEXT, kelompok_makro TEXT, sumber_master TEXT NOT NULL,
 status_verifikasi TEXT NOT NULL DEFAULT 'DISETUJUI',
 diverifikasi_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE beranda_metadata (
 id_indikator TEXT PRIMARY KEY, definisi TEXT, rumus_mentah TEXT, rumus_latex TEXT,
 interpretasi TEXT, sumber_data TEXT, frekuensi TEXT, status_metadata TEXT,
 sumber_metadata TEXT NOT NULL DEFAULT 'RPJPD Provinsi'
);
CREATE TABLE beranda_nilai (
 id_indikator TEXT, tahun INTEGER, jenis TEXT, nilai REAL, nilai_teks TEXT,
 satuan_catatan TEXT, sumber_master TEXT NOT NULL,
 status_verifikasi TEXT NOT NULL DEFAULT 'DISETUJUI', diverifikasi_pada TEXT,
 PRIMARY KEY(id_indikator,tahun,jenis)
);
CREATE TABLE beranda_nilai_periode (
 id_indikator TEXT, tahun INTEGER, jenis TEXT, periode INTEGER, nilai REAL,
 label_periode TEXT, sumber_master TEXT NOT NULL,
 status_verifikasi TEXT NOT NULL DEFAULT 'DISETUJUI', diverifikasi_pada TEXT,
 PRIMARY KEY(id_indikator,tahun,jenis,periode)
);
CREATE TABLE beranda_nilai_wilayah (
 id_indikator TEXT, wilayah_kode TEXT, tahun INTEGER, jenis TEXT, nilai REAL,
 nilai_teks TEXT, sumber TEXT NOT NULL, usulan_id INTEGER,
 status_verifikasi TEXT NOT NULL DEFAULT 'DISETUJUI', diverifikasi_pada TEXT,
 PRIMARY KEY(id_indikator,wilayah_kode,tahun,jenis)
);
CREATE TABLE beranda_nilai_wilayah_periode (
 id_indikator TEXT, wilayah_kode TEXT, tahun INTEGER, jenis TEXT, periode INTEGER,
 nilai REAL, label_periode TEXT, sumber TEXT NOT NULL, usulan_id INTEGER,
 status_verifikasi TEXT NOT NULL DEFAULT 'DISETUJUI', diverifikasi_pada TEXT,
 PRIMARY KEY(id_indikator,wilayah_kode,tahun,jenis,periode)
);
CREATE TABLE wilayah (
 kode TEXT PRIMARY KEY, nama TEXT NOT NULL, tingkat TEXT NOT NULL,
 parent_kode TEXT, aktif INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE pengguna (
 id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, nama TEXT NOT NULL,
 password_hash TEXT NOT NULL, peran TEXT NOT NULL, tim_pjk TEXT, wilayah_kode TEXT,
 aktif INTEGER NOT NULL DEFAULT 1, harus_ganti_password INTEGER NOT NULL DEFAULT 1,
 dibuat_pada TEXT
);
CREATE TABLE usulan_nilai (
 id INTEGER PRIMARY KEY, id_indikator TEXT NOT NULL, tahun INTEGER NOT NULL,
 jenis TEXT NOT NULL, nilai REAL NOT NULL, sumber TEXT NOT NULL, catatan TEXT,
 status TEXT NOT NULL, pengusul_id INTEGER NOT NULL, verifikator_id INTEGER,
 dibuat_pada TEXT, diverifikasi_pada TEXT, wilayah_kode TEXT, dikirim_pada TEXT,
 alasan_verifikasi TEXT, periode INTEGER
);
CREATE TABLE bukti_dukung (
 id INTEGER PRIMARY KEY, usulan_id INTEGER NOT NULL, nama_file TEXT NOT NULL,
 path_file TEXT NOT NULL, mime_type TEXT, ukuran INTEGER NOT NULL,
 checksum_sha256 TEXT NOT NULL, diunggah_pada TEXT
);
CREATE TABLE log_perubahan (
 id INTEGER PRIMARY KEY, waktu TEXT, pengguna_id INTEGER, id_indikator TEXT,
 field TEXT NOT NULL, nilai_lama TEXT, nilai_baru TEXT, sumber_perubahan TEXT NOT NULL,
 referensi_id TEXT, catatan TEXT
);
CREATE TABLE log_aktivitas (
 id INTEGER PRIMARY KEY, waktu TEXT, pengguna_id INTEGER, aksi TEXT NOT NULL,
 objek_tipe TEXT, objek_id TEXT, detail TEXT
);
CREATE TABLE unggahan_excel (
 id INTEGER PRIMARY KEY, nama_file_asli TEXT NOT NULL, path_arsip TEXT NOT NULL,
 checksum_sha256 TEXT NOT NULL, status TEXT NOT NULL, ringkasan_diff TEXT,
 pengguna_id INTEGER, dibuat_pada TEXT, disetujui_pada TEXT
);
CREATE TABLE snapshot_ketersediaan (
 id_indikator TEXT, tanggal_snapshot TEXT, status TEXT NOT NULL,
 PRIMARY KEY(id_indikator,tanggal_snapshot)
);
CREATE TABLE penugasan_pic (
 id INTEGER PRIMARY KEY, id_indikator TEXT NOT NULL, jenis_pic TEXT NOT NULL,
 nama_pic TEXT NOT NULL
);
"""

WILAYAH = [
    ("65", "Kalimantan Utara", "PROVINSI", None, 1),
    ("6501", "Bulungan", "KABUPATEN", "65", 1),
]


@pytest.fixture
def db_lama(tmp_path: Path) -> Path:
    """Sumber sintetis: 2 indikator ETL, 2 master, 1 nama cocok di antaranya."""
    path = tmp_path / "lama.db"
    c = sqlite3.connect(path)
    c.executescript(SKEMA_LAMA)
    c.executemany("INSERT INTO wilayah VALUES (?,?,?,?,?)", WILAYAH)

    # ETL: ISV-01 punya padanan nama di master (ISV-002); ISV-02 tidak.
    c.execute(
        "INSERT INTO indikator(id_indikator,kategori,nomor,nama_indikator,tim_pjk,"
        "status_rpjmd,arah_baik,arah_baik_terverifikasi,nama_asli,opd_penanggung_jawab) "
        "VALUES ('ISV-01','ISV',7,'Tingkat kemiskinan','Sosial','MASUK_RPJMD','TURUN',1,"
        "'Tingkat Kemiskinan Asli','Dinas Sosial')"
    )
    c.execute(
        "INSERT INTO indikator(id_indikator,kategori,nomor,nama_indikator,tim_pjk,"
        "status_rpjmd,arah_baik,arah_baik_terverifikasi) "
        "VALUES ('ISV-02','ISV',2,'GNI per kapita','Neraca','MASUK_RPJMD','NAIK',1)"
    )
    c.execute("INSERT INTO nilai_indikator VALUES ('ISV-01',2024,'realisasi',6.5,'sheet lama')")
    c.execute(
        "INSERT INTO metadata_indikator(id_indikator,definisi,rumus,halaman_sumber,"
        "perlu_verifikasi_manual) VALUES ('ISV-01','Definisi ETL','P0 = ...','hal 12',1)"
    )

    # Master: ISV-001 tanpa padanan, ISV-002 bernama sama dengan ISV-01.
    for id_indikator, nama in (("ISV-001", "PDRB per Kapita"), ("ISV-002", "Tingkat kemiskinan")):
        c.execute(
            "INSERT INTO beranda_indikator(id_indikator,kategori,nama_indikator,kode_indikator,"
            "satuan,opd_pengampu,sasaran_visi,kelompok_makro,sumber_master) "
            "VALUES (?,'ISV',?,?,'Persen','Bappeda','1','Makro Ekonomi','basis.xlsx')",
            (id_indikator, nama, id_indikator.replace("ISV-", "1.")),
        )
        c.execute(
            "INSERT INTO beranda_metadata(id_indikator,definisi,status_metadata,sumber_metadata) "
            "VALUES (?,?,'LENGKAP','RPJPD Provinsi')",
            (id_indikator, f"Definisi master {id_indikator}"),
        )

    c.execute(
        "INSERT INTO beranda_nilai VALUES ('ISV-001',2024,'realisasi',12.3,NULL,'Rp juta',"
        "'basis.xlsx','DISETUJUI','2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO beranda_nilai VALUES ('ISV-002',2024,'realisasi',6.5,NULL,NULL,"
        "'basis.xlsx','DISETUJUI','2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO beranda_nilai_periode VALUES ('ISV-001',2025,'realisasi',2,13.1,"
        "'Semester 2','basis.xlsx','DISETUJUI','2026-01-01 00:00:00')"
    )
    # Fakta yang sama dengan beranda_nilai ISV-002 — hasil penulisan N-arah lama.
    c.execute(
        "INSERT INTO beranda_nilai_wilayah VALUES ('ISV-002','65',2024,'realisasi',6.5,NULL,"
        "'BPS Kaltara',1,'DISETUJUI','2026-01-02 00:00:00')"
    )
    c.execute(
        "INSERT INTO beranda_nilai_wilayah VALUES ('ISV-002','6501',2024,'realisasi',7.1,NULL,"
        "'Operator Bulungan',NULL,'DISETUJUI','2026-01-02 00:00:00')"
    )

    c.execute(
        "INSERT INTO pengguna VALUES (1,'admin','Administrator','argon2-hash','ADMIN',NULL,"
        "NULL,1,1,'2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO usulan_nilai(id,id_indikator,tahun,jenis,nilai,sumber,status,pengusul_id,"
        "wilayah_kode,dibuat_pada) VALUES (1,'ISV-002',2024,'realisasi',6.5,'BPS Kaltara',"
        "'DISETUJUI',1,'65','2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO bukti_dukung VALUES (1,1,'b.pdf','/data/b.pdf','application/pdf',10,'aa','2026-01-01 00:00:00')"
    )
    c.execute(
        "INSERT INTO log_perubahan VALUES (1,'2026-01-01 00:00:00',1,'ISV-01','nilai',NULL,'6.5','form','1',NULL)"
    )
    c.execute("INSERT INTO log_aktivitas VALUES (1,'2026-01-01 00:00:00',1,'MASUK',NULL,NULL,NULL)")
    c.execute(
        "INSERT INTO unggahan_excel VALUES (1,'a.xlsx','/arsip/a.xlsx','bb','DISETUJUI',"
        "'{}',1,'2026-01-01 00:00:00',NULL)"
    )
    # Dua tabel berbasis id ETL: ISV-01 terpetakan, ISV-02 tidak.
    c.executemany(
        "INSERT INTO snapshot_ketersediaan VALUES (?,?,?)",
        [("ISV-01", "2026-01-01", "TERSEDIA"), ("ISV-02", "2026-01-01", "BELUM")],
    )
    c.executemany(
        "INSERT INTO penugasan_pic VALUES (?,?,?,?)",
        [(1, "ISV-01", "PROVINSI", "Budi"), (2, "ISV-02", "PROVINSI", "Sari")],
    )
    c.commit()
    c.close()
    return path


@pytest.fixture
def db_baru(tmp_path: Path) -> str:
    """Basis data tujuan kosong dengan skema hasil migrasi Alembic."""
    url = f"sqlite:///{(tmp_path / 'baru.db').as_posix()}"
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
    return url


@pytest.fixture
def hasil(db_lama: Path, db_baru: str):
    assert jalankan(db_lama, db_baru, kosongkan=False) == 0
    mesin = create_engine(db_baru)
    sesi = sessionmaker(bind=mesin)()
    yield sesi
    sesi.close()
    mesin.dispose()


def test_pemetaan_nama_hanya_yang_cocok(db_lama: Path):
    koneksi = sqlite3.connect(db_lama)
    koneksi.row_factory = sqlite3.Row
    pemetaan = petakan_etl_ke_master(koneksi, Laporan())
    koneksi.close()
    assert pemetaan == {"ISV-01": "ISV-002"}


def test_dimensi_berasal_dari_daftar_master(hasil):
    daftar = hasil.scalars(select(Indikator).order_by(Indikator.id_indikator)).all()
    assert [i.id_indikator for i in daftar] == ["ISV-001", "ISV-002"]
    # ID ETL lama tidak boleh ikut terbawa.
    assert hasil.get(Indikator, "ISV-01") is None


def test_atribut_verifikasi_manual_terbawa_untuk_yang_cocok(hasil):
    cocok = hasil.get(Indikator, "ISV-002")
    assert cocok.arah_baik == "TURUN"
    assert cocok.arah_baik_terverifikasi is True
    assert cocok.tim_pjk == "Sosial"
    assert cocok.nama_asli == "Tingkat Kemiskinan Asli"
    # Kolom master tetap menang untuk yang dimiliki keduanya.
    assert cocok.opd_pengampu == "Bappeda"
    assert cocok.kode_indikator == "1.002"


def test_indikator_tanpa_padanan_kehilangan_arah_baik(hasil):
    """Konsekuensi keputusan 'master saja' yang harus terlihat, bukan tersembunyi."""
    tanpa_padanan = hasil.get(Indikator, "ISV-001")
    assert tanpa_padanan.arah_baik is None
    assert tanpa_padanan.arah_baik_terverifikasi is False
    assert tanpa_padanan.tim_pjk is None


def test_nomor_diturunkan_dari_id_saat_master_tak_punya(hasil):
    """Master tidak punya kolom `nomor`, padahal urutan ekspor membutuhkannya."""
    # Tanpa padanan: diturunkan dari akhiran ID (ISV-001 -> 1).
    assert hasil.get(Indikator, "ISV-001").nomor == 1
    # Dengan padanan: nomor asli dari ETL yang dipakai, bukan hasil turunan (2).
    assert hasil.get(Indikator, "ISV-002").nomor == 7


def test_tahun_terakhir_diturunkan_dari_realisasi_yang_ada(hasil):
    # ISV-001 punya realisasi tahunan 2024 (yang 2025 hanya periodik).
    assert hasil.get(Indikator, "ISV-001").tahun_terakhir == 2024
    assert hasil.get(Indikator, "ISV-002").tahun_terakhir == 2024


def test_metadata_master_menang_etl_melengkapi(hasil):
    metadata = hasil.get(MetadataIndikator, "ISV-002")
    assert metadata.definisi == "Definisi master ISV-002"
    assert metadata.rumus == "P0 = ..."  # hanya ada di ETL
    assert metadata.halaman_sumber == "hal 12"
    assert metadata.perlu_verifikasi_manual is True
    assert metadata.status_metadata == "LENGKAP"


def test_fakta_ganda_digabung_dan_jejak_usulan_dipertahankan(hasil):
    """Penulisan N-arah lama menghasilkan fakta kembar; migrasi menyatukannya."""
    baris = hasil.scalars(
        select(NilaiIndikator).where(
            NilaiIndikator.id_indikator == "ISV-002",
            NilaiIndikator.wilayah_kode == "65",
            NilaiIndikator.tahun == 2024,
        )
    ).all()
    assert len(baris) == 1
    assert baris[0].nilai == 6.5
    assert baris[0].usulan_id == 1
    assert baris[0].sumber == "BPS Kaltara"


def test_nilai_provinsi_dan_wilayah_hidup_di_satu_tabel(hasil):
    semua = hasil.scalars(select(NilaiIndikator)).all()
    wilayah = {baris.wilayah_kode for baris in semua}
    assert wilayah == {"65", "6501"}
    # Nilai provinsi master memakai kode '65', bukan NULL.
    assert all(baris.wilayah_kode is not None for baris in semua)


def test_nilai_periodik_menjadi_baris_dengan_periode(hasil):
    periodik = hasil.scalars(select(NilaiIndikator).where(NilaiIndikator.periode.is_not(None))).all()
    assert len(periodik) == 1
    assert (periodik[0].tahun, periodik[0].periode) == (2025, 2)
    assert periodik[0].label_periode == "Semester 2"


def test_nilai_jalur_etl_tidak_ikut(hasil):
    """`nilai_indikator` lama (sumber_sheet) tidak boleh masuk skema baru."""
    sumber = {baris.sumber for baris in hasil.scalars(select(NilaiIndikator)).all()}
    assert "sheet lama" not in sumber


def test_tabel_berbasis_id_etl_dipetakan_atau_dibuang(hasil):
    pic = hasil.scalars(select(PenugasanPic)).all()
    assert [(p.id_indikator, p.nama_pic) for p in pic] == [("ISV-002", "Budi")]


def test_log_audit_ikut_dipetakan(hasil):
    from backend.app.models import LogPerubahan

    (log,) = hasil.scalars(select(LogPerubahan)).all()
    assert log.id_indikator == "ISV-002"  # semula ISV-01


def test_menolak_jalan_dua_kali_tanpa_kosongkan(db_lama: Path, db_baru: str):
    assert jalankan(db_lama, db_baru, kosongkan=False) == 0
    assert jalankan(db_lama, db_baru, kosongkan=False) == 1


def test_kosongkan_membuat_migrasi_ulang_idempoten(db_lama: Path, db_baru: str):
    assert jalankan(db_lama, db_baru, kosongkan=False) == 0
    assert jalankan(db_lama, db_baru, kosongkan=True) == 0
    mesin = create_engine(db_baru)
    sesi = sessionmaker(bind=mesin)()
    assert len(sesi.scalars(select(Indikator)).all()) == 2
    sesi.close()
    mesin.dispose()
