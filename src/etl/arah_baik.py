"""Heuristik awal arah perbaikan indikator; wajib diverifikasi manusia."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path

DOWN_PATTERNS = [
    (r"kemiskinan", "kemiskinan membaik ketika menurun"),
    (r"rasio\s+gini|ketimpangan", "ketimpangan membaik ketika menurun"),
    (r"kematian|mortalitas", "kematian membaik ketika menurun"),
    (r"stunting|prevalensi|insidensi", "prevalensi/insidensi umumnya membaik ketika menurun"),
    (r"pengangguran", "pengangguran membaik ketika menurun"),
    (r"intensitas\s+emisi|emisi\s+grk", "intensitas/emisi membaik ketika menurun"),
    (r"kehilangan|kerugian|konflik|kejahatan|korupsi", "beban/kejadian negatif membaik ketika menurun"),
    (r"ketidakcukupan|tidak\s+layak", "kondisi kekurangan membaik ketika menurun"),
]

UP_PATTERNS = [
    (
        r"indeks|kontribusi|proporsi|persentase|persen|rasio|cakupan|akses|harapan|produktivitas|pertumbuhan|pendapatan|pdrb|nilai|peringkat",
        "ukuran capaian/akses/produktivitas diasumsikan membaik ketika naik",
    ),
]


def infer_direction(name: str) -> tuple[str, str, str]:
    normalized = re.sub(r"\s+", " ", name.casefold()).strip()
    for pattern, reason in DOWN_PATTERNS:
        if re.search(pattern, normalized):
            return "TURUN", pattern, reason
    for pattern, reason in UP_PATTERNS:
        if re.search(pattern, normalized):
            return "NAIK", pattern, reason
    return "NAIK", "aturan_default", "belum ada kata kunci khusus; asumsi awal NAIK dan wajib ditinjau"


def ensure_columns(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(indikator)")}
    if "arah_baik" not in columns:
        conn.execute("ALTER TABLE indikator ADD COLUMN arah_baik TEXT CHECK(arah_baik IN ('NAIK','TURUN'))")
    if "arah_baik_terverifikasi" not in columns:
        conn.execute(
            "ALTER TABLE indikator ADD COLUMN arah_baik_terverifikasi INTEGER NOT NULL DEFAULT 0 CHECK(arah_baik_terverifikasi IN (0,1))"
        )


def run(db_path: Path, output_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    ensure_columns(conn)
    indicators = conn.execute(
        "SELECT id_indikator, nama_indikator, kategori, kelompok, arah_pembangunan FROM indikator ORDER BY CASE kategori WHEN 'ISV' THEN 0 ELSE 1 END, nomor"
    ).fetchall()
    rows = []
    for item in indicators:
        direction, keyword, reason = infer_direction(item["nama_indikator"])
        conn.execute(
            "UPDATE indikator SET arah_baik=?, arah_baik_terverifikasi=0 WHERE id_indikator=?",
            (direction, item["id_indikator"]),
        )
        rows.append(
            {
                "id_indikator": item["id_indikator"],
                "nama_indikator": item["nama_indikator"],
                "kategori": item["kategori"],
                "kelompok": item["kelompok"] or "",
                "arah_pembangunan": item["arah_pembangunan"] or "",
                "arah_baik_heuristik": direction,
                "kata_kunci": keyword,
                "alasan_heuristik": reason,
                "arah_baik_verifikasi": "",
                "status_verifikasi": "PERLU_VERIFIKASI",
                "catatan_verifikator": "",
            }
        )
    conn.commit()
    conn.close()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Heuristik arah_baik ditulis untuk {len(rows)} indikator: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/processed/sebatik.db"))
    parser.add_argument("--output", type=Path, default=Path("docs/05-arah-baik.csv"))
    args = parser.parse_args()
    run(args.db, args.output)
