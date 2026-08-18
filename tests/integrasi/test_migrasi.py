"""Tes bahwa migrasi Alembic dan model ORM tidak saling menyimpang."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from backend.app.models import Base

REPO_ROOT = Path(__file__).resolve().parents[2]

TABEL_TARGET = {
    "indikator",
    "metadata_indikator",
    "nilai_indikator",
    "wilayah",
    "pengguna",
    "usulan_nilai",
    "bukti_dukung",
    "log_perubahan",
    "log_aktivitas",
    "unggahan_excel",
    "snapshot_ketersediaan",
    "penugasan_pic",
}

# Tabel yang harus hilang setelah konsolidasi (model-data.md §4).
TABEL_LAMA_YANG_HILANG = {
    "beranda_indikator",
    "beranda_metadata",
    "beranda_nilai",
    "beranda_nilai_periode",
    "beranda_nilai_wilayah",
    "beranda_nilai_wilayah_periode",
    "nilai_indikator_wilayah",
}


def _config(url: str) -> Config:
    config = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    return config


@pytest.fixture
def db_kosong(tmp_path: Path) -> str:
    return f"sqlite:///{(tmp_path / 'migrasi.db').as_posix()}"


def test_skema_hasil_migrasi_hanya_berisi_tabel_target(engine_uji):
    tabel = set(inspect(engine_uji).get_table_names()) - {"alembic_version"}
    assert tabel == TABEL_TARGET
    assert tabel & TABEL_LAMA_YANG_HILANG == set()


def test_model_dan_migrasi_tidak_menyimpang(engine_uji):
    """Autogenerate terhadap skema hasil migrasi harus menghasilkan nol beda."""
    with engine_uji.connect() as koneksi:
        konteks = MigrationContext.configure(koneksi, opts={"compare_type": True})
        beda = compare_metadata(konteks, Base.metadata)
    assert beda == [], f"model dan migrasi berbeda: {beda}"


def test_upgrade_lalu_downgrade_bersih(db_kosong: str):
    """Migrasi harus dapat dibatalkan sepenuhnya (kriteria testing-ci.md §8)."""
    config = _config(db_kosong)
    lama = os.environ.get("SEBATIK_DATABASE_URL")
    os.environ["SEBATIK_DATABASE_URL"] = db_kosong
    try:
        command.upgrade(config, "head")
        mesin = create_engine(db_kosong)
        assert set(inspect(mesin).get_table_names()) - {"alembic_version"} == TABEL_TARGET

        command.downgrade(config, "base")
        assert set(inspect(mesin).get_table_names()) - {"alembic_version"} == set()
        mesin.dispose()
    finally:
        if lama is None:
            os.environ.pop("SEBATIK_DATABASE_URL", None)
        else:
            os.environ["SEBATIK_DATABASE_URL"] = lama


def test_nilai_indikator_menggantikan_enam_tabel_lama(engine_uji):
    """Satu tabel fakta harus punya semua kolom yang dulu tersebar."""
    kolom = {c["name"] for c in inspect(engine_uji).get_columns("nilai_indikator")}
    assert {
        "id_indikator",
        "wilayah_kode",
        "tahun",
        "jenis",
        "periode",
        "nilai",
        "nilai_teks",
        "label_periode",
        "satuan_catatan",
        "sumber",
        "usulan_id",
        "status_verifikasi",
        "diverifikasi_pada",
    } <= kolom


def test_indikator_memakai_nama_kolom_baku(engine_uji):
    """`opd_pengampu` menggantikan `opd_penanggung_jawab` yang lama."""
    kolom = {c["name"] for c in inspect(engine_uji).get_columns("indikator")}
    assert "opd_pengampu" in kolom
    assert "opd_penanggung_jawab" not in kolom
    # Kolom master dan kolom ETL kini hidup berdampingan di satu dimensi.
    assert {"sasaran_visi", "kelompok_makro", "kode_indikator"} <= kolom
    assert {"nomor", "nama_asli", "status_rpjmd", "arah_baik"} <= kolom
