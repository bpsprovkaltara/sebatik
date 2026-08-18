"""Load the verified initial dashboard snapshot from the audited workbook extract."""

import sqlite3
from pathlib import Path

from backend.app.master_seed import seed_verified_master

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "processed" / "sebatik.db"


if __name__ == "__main__":
    seed_verified_master(DEFAULT_DB)
    conn = sqlite3.connect(DEFAULT_DB)
    indicators = conn.execute("SELECT COUNT(*) FROM beranda_indikator WHERE status_verifikasi='DISETUJUI'").fetchone()[0]
    values = conn.execute("SELECT COUNT(*) FROM beranda_nilai WHERE status_verifikasi='DISETUJUI'").fetchone()[0]
    years = [row[0] for row in conn.execute("SELECT DISTINCT tahun FROM beranda_nilai WHERE jenis='realisasi' ORDER BY tahun")]
    availability = {
        year: conn.execute("SELECT COUNT(DISTINCT id_indikator) FROM beranda_nilai WHERE jenis='realisasi' AND tahun=? AND status_verifikasi='DISETUJUI' AND (nilai IS NOT NULL OR nilai_teks IS NOT NULL)", (year,)).fetchone()[0]
        for year in years
    }
    groups = conn.execute("SELECT COUNT(DISTINCT kelompok) FROM beranda_indikator WHERE status_verifikasi='DISETUJUI'").fetchone()[0]
    sources = conn.execute("SELECT COUNT(*) FROM beranda_indikator WHERE status_verifikasi='DISETUJUI' AND sumber_data IS NOT NULL AND trim(sumber_data)<>''").fetchone()[0]
    conn.close()
    print(f"Verified dashboard seed loaded: {indicators} indicators, {values} values, groups={groups}, sources={sources}, years={years}, availability={availability}")
