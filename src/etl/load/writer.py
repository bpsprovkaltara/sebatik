"""Penulisan hasil ETL ke basis data staging dan cadangan tabular.

Basis data yang ditulis di sini adalah **staging**: bentuknya sengaja tetap
sederhana karena hanya dipakai untuk menyusun diff sebelum admin menyetujui
unggahan. Skema aplikasi yang sebenarnya dikelola Alembic.
"""

from __future__ import annotations

import csv
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

SKEMA_STAGING = """
PRAGMA foreign_keys=ON;
CREATE TABLE indikator (
 id_indikator TEXT PRIMARY KEY, kategori TEXT NOT NULL CHECK(kategori IN ('ISV','IUP')), nomor INTEGER NOT NULL,
 nama_indikator TEXT NOT NULL, nama_asli TEXT, kelompok TEXT, arah_pembangunan TEXT, satuan TEXT,
 penghasil TEXT, kl_pengampu TEXT, opd_penanggung_jawab TEXT, tim_pjk TEXT,
 status_ketersediaan TEXT, status_metadata TEXT, periode_data TEXT, tahun_terakhir INTEGER,
 is_proxy INTEGER NOT NULL DEFAULT 0 CHECK(is_proxy IN (0,1)), nama_proxy TEXT,
 status_rpjmd TEXT NOT NULL CHECK(status_rpjmd IN ('MASUK_RPJMD','TIDAK_MASUK_RPJMD','MASUK_TAPI_BELUM_ADA_DATA','DOBEL_ISV_IUP')),
 arah_baik TEXT CHECK(arah_baik IN ('NAIK','TURUN')),
 arah_baik_terverifikasi INTEGER NOT NULL DEFAULT 0 CHECK(arah_baik_terverifikasi IN (0,1)),
 kode_sdgs TEXT, link_metadata TEXT, link_publikasi TEXT, link_data TEXT, catatan_teknis TEXT,
 UNIQUE(kategori, nomor)
);
CREATE TABLE nilai_indikator (
 id_indikator TEXT NOT NULL REFERENCES indikator(id_indikator), tahun INTEGER NOT NULL,
 jenis TEXT NOT NULL CHECK(jenis IN ('realisasi','target')), nilai REAL, sumber_sheet TEXT NOT NULL,
 PRIMARY KEY(id_indikator,tahun,jenis)
);
CREATE TABLE metadata_indikator (
 id_indikator TEXT PRIMARY KEY REFERENCES indikator(id_indikator), definisi TEXT, rumus TEXT,
 rumus_mentah TEXT, interpretasi TEXT, sumber_data TEXT, frekuensi TEXT, halaman_sumber TEXT,
 perlu_verifikasi_manual INTEGER NOT NULL DEFAULT 0, sumber_metadata TEXT, nama_di_buku1 TEXT
);
CREATE TABLE penugasan_pic (
 id INTEGER PRIMARY KEY AUTOINCREMENT, id_indikator TEXT NOT NULL REFERENCES indikator(id_indikator),
 jenis_pic TEXT NOT NULL, nama_pic TEXT NOT NULL
);
CREATE TABLE snapshot_ketersediaan (
 id_indikator TEXT NOT NULL REFERENCES indikator(id_indikator), tanggal_snapshot TEXT NOT NULL,
 status TEXT NOT NULL, PRIMARY KEY(id_indikator,tanggal_snapshot)
);
"""

TABEL_DIHITUNG = ("indikator", "nilai_indikator", "metadata_indikator", "penugasan_pic")
STATUS_BAWAAN = "Belum Tersedia"


def _sisip(conn: sqlite3.Connection, tabel: str, baris: list[dict[str, Any]]) -> None:
    if not baris:
        return
    kolom = list(baris[0])
    tanya = ",".join("?" for _ in kolom)
    conn.executemany(
        f"INSERT INTO {tabel} ({','.join(kolom)}) VALUES ({tanya})",
        [[item[k] for k in kolom] for item in baris],
    )


def tulis_basis_data(
    db_path: Path,
    indikator: list[dict[str, Any]],
    nilai: list[dict[str, Any]],
    pic: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bangun ulang basis data staging dari nol; kembalikan ringkasan validasi."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SKEMA_STAGING)
        _sisip(conn, "indikator", indikator)
        _sisip(conn, "nilai_indikator", nilai)
        conn.executemany(
            "INSERT INTO metadata_indikator(id_indikator) VALUES (?)",
            [(item["id_indikator"],) for item in indikator],
        )
        _sisip(conn, "penugasan_pic", pic)
        hari_ini = date.today().isoformat()
        conn.executemany(
            "INSERT INTO snapshot_ketersediaan(id_indikator,tanggal_snapshot,status) VALUES (?,?,?)",
            [(item["id_indikator"], hari_ini, item["status_ketersediaan"] or STATUS_BAWAAN) for item in indikator],
        )
        conn.commit()

        galat_fk = conn.execute("PRAGMA foreign_key_check").fetchall()
        jumlah = {tabel: conn.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0] for tabel in TABEL_DIHITUNG}
        tanpa_realisasi = [
            baris[0]
            for baris in conn.execute(
                "SELECT i.id_indikator FROM indikator i "
                "LEFT JOIN nilai_indikator n ON n.id_indikator=i.id_indikator "
                "AND n.jenis='realisasi' AND n.nilai IS NOT NULL "
                "GROUP BY i.id_indikator HAVING COUNT(n.id_indikator)=0 ORDER BY i.id_indikator"
            )
        ]
    finally:
        conn.close()

    return {"jumlah": jumlah, "galat_fk": galat_fk, "tanpa_realisasi": tanpa_realisasi}


def tulis_csv(path: Path, baris: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not baris:
        return
    # utf-8-sig agar Excel di Windows membuka berkas tanpa mengacak karakter.
    with path.open("w", newline="", encoding="utf-8-sig") as berkas:
        penulis = csv.DictWriter(berkas, fieldnames=list(baris[0]))
        penulis.writeheader()
        penulis.writerows(baris)


def tulis_cadangan(
    direktori: Path,
    indikator: list[dict[str, Any]],
    nilai: list[dict[str, Any]],
    pic: list[dict[str, Any]],
) -> str:
    """Cadangan CSV selalu dibuat; Parquet hanya bila pustakanya tersedia."""
    tulis_csv(direktori / "indikator.csv", indikator)
    tulis_csv(direktori / "nilai_indikator.csv", nilai)
    tulis_csv(direktori / "penugasan_pic.csv", pic)
    tulis_csv(
        direktori / "metadata_indikator.csv",
        [{"id_indikator": item["id_indikator"]} for item in indikator],
    )
    try:
        import pandas as pd
    except ImportError:
        return "tidak dibuat (pyarrow tidak tersedia)"

    try:
        for nama, baris in (
            ("indikator", indikator),
            ("nilai_indikator", nilai),
            ("penugasan_pic", pic),
        ):
            pd.DataFrame(baris).to_parquet(direktori / f"{nama}.parquet", index=False)
    except (ImportError, ValueError):
        return "tidak dibuat (pyarrow tidak tersedia)"
    return "dibuat"
