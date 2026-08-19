"""Backup konsisten berkas SQLite dengan retensi harian.

Dipakai untuk pemasangan tunggal yang masih memakai SQLite, dan untuk
mengarsipkan basis data lama sebelum cutover ke PostgreSQL. Pemasangan yang
sudah memakai PostgreSQL memakai `pg_dump` lewat layanan `backup` di
docker-compose.yml, bukan skrip ini.
"""

from __future__ import annotations

import argparse
import sqlite3
import time
from datetime import datetime
from pathlib import Path


def backup(source: Path, destination: Path, retention: int):
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / f"sebatik-{datetime.now():%Y%m%d-%H%M%S}.db"
    with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
        src.backup(dst)
    files = sorted(destination.glob("sebatik-*.db"), reverse=True)
    for old in files[retention:]:
        old.unlink()
    print(f"Backup selesai: {target}", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=Path("data/processed/sebatik.db"))
    p.add_argument("--destination", type=Path, default=Path("backup"))
    p.add_argument("--retention", type=int, default=30)
    p.add_argument("--interval", type=int, default=86400)
    p.add_argument("--watch", action="store_true")
    a = p.parse_args()
    while True:
        backup(a.source, a.destination, a.retention)
        if not a.watch:
            break
        time.sleep(a.interval)
