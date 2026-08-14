"""Migrasi fitur Tahap 5-7 dan koreksi arah indikator."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
import sqlite3

from pwdlib import PasswordHash

from .arah_baik import ensure_columns


FEATURE_SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshot_ketersediaan (
 id_indikator TEXT NOT NULL REFERENCES indikator(id_indikator),
 tanggal_snapshot TEXT NOT NULL, status TEXT NOT NULL,
 PRIMARY KEY(id_indikator,tanggal_snapshot)
);
CREATE TABLE IF NOT EXISTS pengguna (
 id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
 nama TEXT NOT NULL, password_hash TEXT NOT NULL,
 peran TEXT NOT NULL CHECK(peran IN ('ADMIN','PIC_TIM','PENGUNJUNG')),
 tim_pjk TEXT, aktif INTEGER NOT NULL DEFAULT 1, harus_ganti_password INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS usulan_nilai (
 id INTEGER PRIMARY KEY AUTOINCREMENT, id_indikator TEXT NOT NULL REFERENCES indikator(id_indikator),
 tahun INTEGER NOT NULL, jenis TEXT NOT NULL CHECK(jenis IN ('realisasi','target')),
 nilai REAL NOT NULL, sumber TEXT NOT NULL, catatan TEXT,
 status TEXT NOT NULL DEFAULT 'MENUNGGU_VERIFIKASI' CHECK(status IN ('MENUNGGU_VERIFIKASI','DISETUJUI','DITOLAK')),
 pengusul_id INTEGER NOT NULL REFERENCES pengguna(id), verifikator_id INTEGER REFERENCES pengguna(id),
 dibuat_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, diverifikasi_pada TEXT
);
CREATE TABLE IF NOT EXISTS log_perubahan (
 id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 pengguna_id INTEGER REFERENCES pengguna(id), id_indikator TEXT REFERENCES indikator(id_indikator),
 field TEXT NOT NULL, nilai_lama TEXT, nilai_baru TEXT, sumber_perubahan TEXT NOT NULL,
 referensi_id TEXT, catatan TEXT
);
CREATE TABLE IF NOT EXISTS unggahan_excel (
 id INTEGER PRIMARY KEY AUTOINCREMENT, nama_file_asli TEXT NOT NULL, path_arsip TEXT NOT NULL,
 checksum_sha256 TEXT NOT NULL, status TEXT NOT NULL,
 ringkasan_diff TEXT, pengguna_id INTEGER REFERENCES pengguna(id),
 dibuat_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, disetujui_pada TEXT
);
"""

GOVERNANCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS wilayah (
 kode TEXT PRIMARY KEY, nama TEXT NOT NULL, tingkat TEXT NOT NULL,
 parent_kode TEXT REFERENCES wilayah(kode), aktif INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS bukti_dukung (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 usulan_id INTEGER NOT NULL REFERENCES usulan_nilai(id) ON DELETE CASCADE,
 nama_file TEXT NOT NULL, path_file TEXT NOT NULL, mime_type TEXT,
 ukuran INTEGER NOT NULL, checksum_sha256 TEXT NOT NULL,
 diunggah_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS nilai_indikator_wilayah (
 id_indikator TEXT NOT NULL REFERENCES indikator(id_indikator),
 wilayah_kode TEXT NOT NULL REFERENCES wilayah(kode), tahun INTEGER NOT NULL,
 jenis TEXT NOT NULL CHECK(jenis IN ('realisasi','target')), nilai REAL,
 sumber TEXT NOT NULL, usulan_id INTEGER NOT NULL REFERENCES usulan_nilai(id),
 diverifikasi_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(id_indikator,wilayah_kode,tahun,jenis)
);
CREATE TABLE IF NOT EXISTS log_aktivitas (
 id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 pengguna_id INTEGER REFERENCES pengguna(id), aksi TEXT NOT NULL,
 objek_tipe TEXT, objek_id TEXT, detail TEXT
);
CREATE INDEX IF NOT EXISTS ix_usulan_status ON usulan_nilai(status);
CREATE INDEX IF NOT EXISTS ix_usulan_wilayah ON usulan_nilai(wilayah_kode);
"""

WILAYAH_KALTARA = (
    ("65", "Kalimantan Utara", "PROVINSI", None),
    ("6501", "Bulungan", "KABUPATEN", "65"),
    ("6502", "Malinau", "KABUPATEN", "65"),
    ("6503", "Nunukan", "KABUPATEN", "65"),
    ("6504", "Tana Tidung", "KABUPATEN", "65"),
    ("6571", "Tarakan", "KOTA", "65"),
)


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _upgrade_users(conn: sqlite3.Connection) -> None:
    """Rebuild once because the old SQLite CHECK only permits PIC_TIM."""
    sql = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='pengguna'").fetchone()
    if sql and "OPERATOR" not in sql[0]:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("PRAGMA legacy_alter_table=ON")
        conn.executescript("""
        ALTER TABLE pengguna RENAME TO pengguna_lama;
        CREATE TABLE pengguna (
         id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
         nama TEXT NOT NULL, password_hash TEXT NOT NULL,
         peran TEXT NOT NULL CHECK(peran IN ('ADMIN','OPERATOR','VERIFIKATOR','PENGUNJUNG')),
         tim_pjk TEXT, wilayah_kode TEXT REFERENCES wilayah(kode),
         aktif INTEGER NOT NULL DEFAULT 1, harus_ganti_password INTEGER NOT NULL DEFAULT 1,
         dibuat_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO pengguna(id,username,nama,password_hash,peran,tim_pjk,aktif,harus_ganti_password)
        SELECT id,username,nama,password_hash,
          CASE WHEN peran='PIC_TIM' THEN 'OPERATOR' ELSE peran END,
          tim_pjk,aktif,harus_ganti_password FROM pengguna_lama;
        DROP TABLE pengguna_lama;
        """)
        conn.execute("PRAGMA foreign_keys=ON")
    elif sql:
        cols = _columns(conn, "pengguna")
        if "wilayah_kode" not in cols: conn.execute("ALTER TABLE pengguna ADD COLUMN wilayah_kode TEXT REFERENCES wilayah(kode)")
        if "dibuat_pada" not in cols: conn.execute("ALTER TABLE pengguna ADD COLUMN dibuat_pada TEXT")


def migrate_governance(db_path: Path) -> None:
    """Idempotent role, regional workflow, evidence, and seed migration."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("CREATE TABLE IF NOT EXISTS wilayah (kode TEXT PRIMARY KEY,nama TEXT NOT NULL,tingkat TEXT NOT NULL,parent_kode TEXT,aktif INTEGER NOT NULL DEFAULT 1);")
    _upgrade_users(conn)
    for column, definition in (
        ("wilayah_kode", "TEXT REFERENCES wilayah(kode)"),
        ("dikirim_pada", "TEXT"),
        ("alasan_verifikasi", "TEXT"),
        ("periode", "INTEGER"),
    ):
        if column not in _columns(conn, "usulan_nilai"):
            conn.execute(f"ALTER TABLE usulan_nilai ADD COLUMN {column} {definition}")
    conn.executescript(GOVERNANCE_SCHEMA)
    conn.executemany("INSERT OR IGNORE INTO wilayah(kode,nama,tingkat,parent_kode) VALUES (?,?,?,?)", WILAYAH_KALTARA)

    # Two initial operator slots per province/regency/city; all must change password.
    initial_password = PasswordHash.recommended().hash("Sebatik-Operator-Ganti-2026!")
    for code, name, _level, _parent in WILAYAH_KALTARA:
        for number in (1, 2):
            username = f"operator.{code}.{number}"
            conn.execute(
                "INSERT OR IGNORE INTO pengguna(username,nama,password_hash,peran,wilayah_kode,harus_ganti_password) VALUES (?,?,?,?,?,1)",
                (username, f"Operator {name} {number}", initial_password, "OPERATOR", code),
            )
    conn.commit(); conn.close()


def migrate(db_path: Path, direction_csv: Path | None = None) -> None:
    conn = sqlite3.connect(db_path)
    ensure_columns(conn)
    conn.executescript(FEATURE_SCHEMA)
    if direction_csv and direction_csv.exists():
        with direction_csv.open(encoding="utf-8-sig") as stream:
            for row in csv.DictReader(stream):
                direction = row.get("arah_baik_verifikasi") or row.get("arah_baik_heuristik")
                if direction in {"NAIK", "TURUN"}:
                    conn.execute("UPDATE indikator SET arah_baik=?, arah_baik_terverifikasi=1 WHERE id_indikator=?", (direction, row["id_indikator"]))
    today = date.today().isoformat()
    conn.execute("INSERT OR IGNORE INTO snapshot_ketersediaan(id_indikator,tanggal_snapshot,status) SELECT id_indikator,?,status_ketersediaan FROM indikator", (today,))
    if not conn.execute("SELECT 1 FROM pengguna WHERE username='admin'").fetchone():
        password_hash = PasswordHash.recommended().hash("Sebatik-Ganti-Segera-2026!")
        conn.execute("INSERT INTO pengguna(username,nama,password_hash,peran,harus_ganti_password) VALUES ('admin','Administrator Awal',?,'ADMIN',1)", (password_hash,))
    conn.commit(); conn.close()
    migrate_governance(db_path)


if __name__ == "__main__":
    migrate(Path("data/processed/sebatik.db"), Path("docs/05-arah-baik.csv"))
