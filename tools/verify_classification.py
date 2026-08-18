import json
import sqlite3

db = sqlite3.connect("data/processed/sebatik.db")
dimensions = [
    ("sasaran_visi", "Sasaran Visi", 5),
    ("misi_agenda", "Misi/Agenda", 8),
    ("arah_ie", "Arah", 17),
    ("indikator_induk", "Induk", 45),
]
result = []
for column, label, total in dimensions:
    ids = [
        row[0]
        for row in db.execute(
            f"SELECT id_indikator FROM beranda_indikator WHERE status_verifikasi='DISETUJUI' "
            f"AND {column} IS NOT NULL AND trim({column})<>'' AND {column} NOT LIKE '-%'"
        )
    ]
    placeholders = ",".join("?" for _ in ids)
    filled = db.execute(
        f"SELECT COUNT(*) FROM beranda_nilai WHERE id_indikator IN ({placeholders}) "
        "AND jenis='realisasi' AND tahun BETWEEN 2021 AND 2025 "
        "AND status_verifikasi='DISETUJUI' AND (nilai IS NOT NULL OR nilai_teks IS NOT NULL)",
        ids,
    ).fetchone()[0] if ids else 0
    possible = len(ids) * 5
    result.append([label, total, len(ids), filled, possible, round(filled / possible * 100, 1) if possible else 0])

macro = db.execute(
    "SELECT COUNT(*) FROM beranda_indikator WHERE kelompok_makro LIKE 'Makro%' AND status_verifikasi='DISETUJUI'"
).fetchone()[0]
macro_rows = db.execute(
    "SELECT id_indikator, kode_indikator, nama_indikator, kelompok_makro FROM beranda_indikator "
    "WHERE kelompok_makro LIKE 'Makro%' ORDER BY id_indikator"
).fetchall()
focus_values = db.execute(
    "SELECT id_indikator,tahun,jenis,nilai,nilai_teks,satuan_catatan FROM beranda_nilai "
    "WHERE id_indikator IN ('ISV-001','IUP-050','ISV-004','ISV-005','IUP-028') "
    "AND tahun BETWEEN 2021 AND 2025 ORDER BY id_indikator,tahun,jenis"
).fetchall()
period_values = db.execute(
    "SELECT id_indikator,tahun,periode,nilai,label_periode FROM beranda_nilai_periode "
    "WHERE id_indikator='IUP-028' ORDER BY tahun,periode"
).fetchall()
print(json.dumps({"dimensions": result, "macro": macro, "macro_rows": macro_rows, "focus_values": focus_values, "period_values": period_values}, ensure_ascii=False))
