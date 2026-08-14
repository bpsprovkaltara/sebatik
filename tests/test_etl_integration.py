from pathlib import Path
import sqlite3

import openpyxl

from src.etl.pipeline import extract_values, run


SOURCE = Path("data/raw/ISV-IUP_Provinsi_Kalimantan_Utara.xlsx")


def test_etl_file_asli_tanpa_id_ganda_atau_fakta_hilang(tmp_path):
    database = tmp_path / "sebatik-test.db"
    report = tmp_path / "report.md"
    run(SOURCE, database, report)
    conn = sqlite3.connect(database)
    assert conn.execute("SELECT COUNT(*) FROM indikator").fetchone()[0] == 86
    assert conn.execute("SELECT COUNT(*) FROM indikator").fetchone()[0] == conn.execute("SELECT COUNT(DISTINCT id_indikator) FROM indikator").fetchone()[0]

    workbook = openpyxl.load_workbook(SOURCE, data_only=True)
    expected, _ = extract_values(workbook)
    expected_keys = {(x["id_indikator"], x["tahun"], x["jenis"], x["nilai"]) for x in expected}
    actual_keys = set(conn.execute("SELECT id_indikator,tahun,jenis,nilai FROM nilai_indikator"))
    assert actual_keys == expected_keys
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    conn.close()
