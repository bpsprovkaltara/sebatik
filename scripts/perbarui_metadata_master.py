"""Perbarui metadata dari workbook terklasifikasi yang diturunkan dari Buku 1."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


KOLOM = {
    "id_indikator": "ID Indikator",
    "definisi": "Definisi (RPJPD Provinsi)",
    "rumus_mentah": "Rumus Perhitungan (RPJPD Provinsi)",
    "interpretasi": "Interpretasi (RPJPD Provinsi)",
    "sumber_data": "Sumber Data (RPJPD Provinsi)",
    "frekuensi": "Frekuensi (RPJPD Provinsi)",
}


def jalankan(master_path: Path, db_path: Path) -> int:
    sumber = json.loads(master_path.read_text(encoding="utf-8"))
    tabel = sumber["sheets"]["Basis Data Indikator"]
    header = {nama: posisi for posisi, nama in enumerate(tabel[0])}
    posisi = {field: header[nama] for field, nama in KOLOM.items()}
    baris = []
    for sumber_baris in tabel[1:]:
        iid = sumber_baris[posisi["id_indikator"]]
        if not iid:
            continue
        baris.append(tuple(sumber_baris[posisi[field]] for field in KOLOM))

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """UPDATE metadata_indikator SET
            definisi=?, rumus_mentah=?, interpretasi=?, sumber_data=?, frekuensi=?,
            sumber_metadata='Buku 1 RPJPN-RPJPD 2025-2045', perlu_verifikasi_manual=1
            WHERE id_indikator=?""",
            [(definisi, rumus, interpretasi, sumber, frekuensi, iid) for iid, definisi, rumus, interpretasi, sumber, frekuensi in baris],
        )
    return len(baris)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, default=Path("data/raw/basis_data_indikator_isv_iup_kaltara.json"))
    parser.add_argument("--db", type=Path, default=Path("data/processed/sebatik.db"))
    args = parser.parse_args()
    print(f"Metadata diperbarui: {jalankan(args.master, args.db)} indikator")
