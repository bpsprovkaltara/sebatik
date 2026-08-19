"""Integrasi ETL terhadap workbook asli."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import openpyxl
import pytest

from src.etl.config import bawaan
from src.etl.extract import baca_nilai
from src.etl.pipeline import run

SUMBER = Path("data/raw/ISV-IUP_Provinsi_Kalimantan_Utara.xlsx")


@pytest.fixture(scope="module")
def workbook():
    if not SUMBER.exists():
        pytest.skip(f"Workbook sumber tidak tersedia: {SUMBER}")
    wb = openpyxl.load_workbook(SUMBER, data_only=True)
    yield wb
    wb.close()


def test_etl_file_asli_tanpa_id_ganda_atau_fakta_hilang(tmp_path, workbook):
    if not SUMBER.exists():
        pytest.skip(f"Workbook sumber tidak tersedia: {SUMBER}")
    basis_data = tmp_path / "sebatik-test.db"
    run(SUMBER, basis_data, tmp_path / "report.md")

    conn = sqlite3.connect(basis_data)
    try:
        jumlah = conn.execute("SELECT COUNT(*) FROM indikator").fetchone()[0]
        unik = conn.execute("SELECT COUNT(DISTINCT id_indikator) FROM indikator").fetchone()[0]
        assert jumlah == bawaan().jumlah_indikator_diharapkan
        assert jumlah == unik

        diharapkan, _ = baca_nilai(workbook, bawaan())
        kunci_diharapkan = {(x["id_indikator"], x["tahun"], x["jenis"], x["nilai"]) for x in diharapkan}
        kunci_aktual = set(conn.execute("SELECT id_indikator,tahun,jenis,nilai FROM nilai_indikator"))
        assert kunci_aktual == kunci_diharapkan
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        conn.close()
