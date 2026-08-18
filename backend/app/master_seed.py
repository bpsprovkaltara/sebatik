from __future__ import annotations

import json
import sqlite3
from contextlib import suppress
from pathlib import Path

from src.etl.units import indicator_unit

SOURCE_JSON = Path(__file__).resolve().parents[2] / "data" / "raw" / "basis_data_indikator_isv_iup_kaltara.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS beranda_indikator (
 id_indikator TEXT PRIMARY KEY, kategori TEXT NOT NULL, kelompok TEXT,
 arah_pembangunan TEXT, kode_indikator TEXT, nama_indikator TEXT NOT NULL,
 is_proxy INTEGER NOT NULL DEFAULT 0, nama_proxy TEXT, satuan TEXT,
 sumber_data TEXT, frekuensi TEXT, opd_pengampu TEXT, status_ketersediaan TEXT, periode_data TEXT,
 sasaran_visi TEXT, misi_agenda TEXT, arah_ie TEXT, indikator_induk TEXT, kelompok_makro TEXT,
 sumber_master TEXT NOT NULL, status_verifikasi TEXT NOT NULL DEFAULT 'DISETUJUI',
 diverifikasi_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS beranda_nilai (
 id_indikator TEXT NOT NULL REFERENCES beranda_indikator(id_indikator),
 tahun INTEGER NOT NULL, jenis TEXT NOT NULL CHECK(jenis IN ('realisasi','target')),
 nilai REAL, nilai_teks TEXT, satuan_catatan TEXT,
 sumber_master TEXT NOT NULL, status_verifikasi TEXT NOT NULL DEFAULT 'DISETUJUI',
 diverifikasi_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(id_indikator,tahun,jenis)
);
CREATE TABLE IF NOT EXISTS beranda_nilai_periode (
 id_indikator TEXT NOT NULL REFERENCES beranda_indikator(id_indikator),
 tahun INTEGER NOT NULL, jenis TEXT NOT NULL CHECK(jenis IN ('realisasi','target')),
 periode INTEGER NOT NULL, nilai REAL NOT NULL, label_periode TEXT,
 sumber_master TEXT NOT NULL, status_verifikasi TEXT NOT NULL DEFAULT 'DISETUJUI',
 diverifikasi_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(id_indikator,tahun,jenis,periode)
);
CREATE INDEX IF NOT EXISTS ix_beranda_nilai_tahun ON beranda_nilai(tahun,jenis,status_verifikasi);
CREATE TABLE IF NOT EXISTS beranda_nilai_wilayah (
 id_indikator TEXT NOT NULL REFERENCES beranda_indikator(id_indikator),
 wilayah_kode TEXT NOT NULL REFERENCES wilayah(kode), tahun INTEGER NOT NULL,
 jenis TEXT NOT NULL CHECK(jenis IN ('realisasi','target')), nilai REAL,
 nilai_teks TEXT, sumber TEXT NOT NULL, usulan_id INTEGER REFERENCES usulan_nilai(id),
 status_verifikasi TEXT NOT NULL DEFAULT 'DISETUJUI',
 diverifikasi_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(id_indikator,wilayah_kode,tahun,jenis)
);
CREATE TABLE IF NOT EXISTS beranda_nilai_wilayah_periode (
 id_indikator TEXT NOT NULL REFERENCES beranda_indikator(id_indikator),
 wilayah_kode TEXT NOT NULL REFERENCES wilayah(kode), tahun INTEGER NOT NULL,
 jenis TEXT NOT NULL CHECK(jenis IN ('realisasi','target')), periode INTEGER NOT NULL,
 nilai REAL NOT NULL, label_periode TEXT, sumber TEXT NOT NULL,
 usulan_id INTEGER REFERENCES usulan_nilai(id), status_verifikasi TEXT NOT NULL DEFAULT 'DISETUJUI',
 diverifikasi_pada TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(id_indikator,wilayah_kode,tahun,jenis,periode)
);
CREATE TABLE IF NOT EXISTS beranda_metadata (
 id_indikator TEXT PRIMARY KEY REFERENCES beranda_indikator(id_indikator) ON DELETE CASCADE,
 definisi TEXT, rumus_mentah TEXT, rumus_latex TEXT, interpretasi TEXT,
 sumber_data TEXT, frekuensi TEXT, status_metadata TEXT,
 sumber_metadata TEXT NOT NULL DEFAULT 'RPJPD Provinsi'
);
"""


def _records(rows: list[list]) -> list[dict]:
    """Map workbook rows by header so column additions/reordering stay safe."""
    if not rows:
        return []
    headers = [str(value or "").strip() for value in rows[0]]
    return [dict(zip(headers, row, strict=False)) for row in rows[1:] if row and row[0]]


def _key(value) -> str:
    return " ".join(str(value or "").split()).casefold()


def seed_verified_master(db_path: Path) -> None:
    if not SOURCE_JSON.exists():
        return
    payload = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    source = payload.get("source", SOURCE_JSON.name)
    indicators = _records(payload["sheets"]["Basis Data Indikator"])
    values = _records(payload["sheets"]["Data Target-Realisasi"])
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    # Sinkronkan juga tabel ETL lama karena beberapa endpoint analitik masih
    # membacanya. Migrasi aman untuk instalasi baru yang belum punya tabel itu.
    legacy_tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "indikator" in legacy_tables:
        for legacy_id in (row[0] for row in conn.execute("SELECT id_indikator FROM indikator")):
            conn.execute("UPDATE indikator SET satuan=? WHERE id_indikator=?", (indicator_unit(legacy_id), legacy_id))
    columns = {row[1] for row in conn.execute("PRAGMA table_info(beranda_indikator)")}
    if "sumber_data" not in columns: conn.execute("ALTER TABLE beranda_indikator ADD COLUMN sumber_data TEXT")
    if "frekuensi" not in columns: conn.execute("ALTER TABLE beranda_indikator ADD COLUMN frekuensi TEXT")
    for name in ("sasaran_visi","misi_agenda","arah_ie","indikator_induk","kelompok_makro"):
        if name not in columns: conn.execute(f"ALTER TABLE beranda_indikator ADD COLUMN {name} TEXT")

    indicator_ids = {str(row["ID Indikator"]).strip() for row in indicators}
    # The classified workbook retains legacy IDs in Data Target-Realisasi.
    # Resolve values from their semantic identity so inserted/reordered master
    # rows cannot attach a series to the wrong indicator.
    indicator_by_identity = {
        (_key(row.get("Kategori")), _key(row.get("Kode Indikator")),
         _key(row.get("Nama Indikator (RPJPD Provinsi / dipakai Kaltara)"))):
        str(row["ID Indikator"]).strip()
        for row in indicators
    }
    placeholders = ",".join("?" for _ in indicator_ids)
    if indicator_ids:
        stale = [row[0] for row in conn.execute(
            f"SELECT id_indikator FROM beranda_indikator WHERE id_indikator NOT IN ({placeholders})",
            tuple(sorted(indicator_ids)),
        )]
        for indicator_id in stale:
            conn.execute("DELETE FROM beranda_nilai_wilayah WHERE id_indikator=?", (indicator_id,))
            conn.execute("DELETE FROM beranda_nilai WHERE id_indikator=?", (indicator_id,))
            conn.execute("DELETE FROM beranda_metadata WHERE id_indikator=?", (indicator_id,))
            conn.execute("DELETE FROM beranda_indikator WHERE id_indikator=?", (indicator_id,))

    for row in indicators:
        indicator_id = str(row["ID Indikator"]).strip()
        proxy = str(row.get("Indikator Proxy?") or "").strip().casefold() == "ya"
        conn.execute(
            """INSERT INTO beranda_indikator
            (id_indikator,kategori,kelompok,arah_pembangunan,kode_indikator,nama_indikator,
             is_proxy,nama_proxy,satuan,sumber_data,frekuensi,opd_pengampu,status_ketersediaan,periode_data,
             sasaran_visi,misi_agenda,arah_ie,indikator_induk,kelompok_makro,sumber_master)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id_indikator) DO UPDATE SET
             kategori=excluded.kategori,kelompok=excluded.kelompok,
             arah_pembangunan=excluded.arah_pembangunan,kode_indikator=excluded.kode_indikator,
             nama_indikator=excluded.nama_indikator,is_proxy=excluded.is_proxy,
             nama_proxy=excluded.nama_proxy,satuan=excluded.satuan,sumber_data=excluded.sumber_data,
             frekuensi=excluded.frekuensi,opd_pengampu=excluded.opd_pengampu,
             status_ketersediaan=excluded.status_ketersediaan,periode_data=excluded.periode_data,
             sasaran_visi=COALESCE(excluded.sasaran_visi,beranda_indikator.sasaran_visi),
             misi_agenda=COALESCE(excluded.misi_agenda,beranda_indikator.misi_agenda),
             arah_ie=COALESCE(excluded.arah_ie,beranda_indikator.arah_ie),
             indikator_induk=COALESCE(excluded.indikator_induk,beranda_indikator.indikator_induk),
             kelompok_makro=COALESCE(excluded.kelompok_makro,beranda_indikator.kelompok_makro),
             sumber_master=excluded.sumber_master,status_verifikasi='DISETUJUI'""",
            (indicator_id, row.get("Kategori"), row.get("Kelompok / Pilar"), row.get("Arah Pembangunan"),
             str(row.get("Kode Indikator") or ""), row.get("Nama Indikator (RPJPD Provinsi / dipakai Kaltara)"),
             int(proxy), None, indicator_unit(indicator_id), row.get("Sumber Data (RPJPD Provinsi)"), row.get("Frekuensi (RPJPD Provinsi)"),
             row.get("Perangkat Daerah Pengampu (Kaltara)"), row.get("Ketersediaan Data"),
             row.get("Periode Data"), row.get("Sasaran Visi (1-5)"),
             row.get("Misi/Agenda Pembangunan (1-8)"), row.get("Arah Pembangunan (IE1-IE17)"),
             row.get("No. Indikator Utama Induk (1-45)"), row.get("Kelompok Makro"), source),
        )

        conn.execute(
            """INSERT INTO beranda_metadata
            (id_indikator,definisi,rumus_mentah,interpretasi,sumber_data,frekuensi,status_metadata,sumber_metadata)
            VALUES (?,?,?,?,?,?,?,'RPJPD Provinsi')
            ON CONFLICT(id_indikator) DO UPDATE SET
             definisi=excluded.definisi,rumus_mentah=excluded.rumus_mentah,
             interpretasi=excluded.interpretasi,sumber_data=excluded.sumber_data,
             frekuensi=excluded.frekuensi,status_metadata=excluded.status_metadata,
             sumber_metadata=excluded.sumber_metadata""",
            (indicator_id, row.get("Definisi (RPJPD Provinsi)"), row.get("Rumus Perhitungan (RPJPD Provinsi)"),
             row.get("Interpretasi (RPJPD Provinsi)"), row.get("Sumber Data (RPJPD Provinsi)"),
             row.get("Frekuensi (RPJPD Provinsi)"), row.get("Status Metadata")),
        )

    conn.execute("DELETE FROM beranda_nilai WHERE sumber_master<>? OR id_indikator IN (SELECT id_indikator FROM beranda_indikator)", (source,))
    conn.execute("DELETE FROM beranda_nilai_periode")
    for row in values:
        if not row.get("ID Indikator") or not row.get("Jenis Nilai") or not row.get("Tahun"):
            continue
        identity = (_key(row.get("Kategori")), _key(row.get("Kode Indikator")), _key(row.get("Nama Indikator (Kaltara)")))
        resolved_id = indicator_by_identity.get(identity)
        if not resolved_id:
            candidates = [
                value for key,value in indicator_by_identity.items()
                if key[:2] == identity[:2]
            ]
            resolved_id = candidates[0] if len(candidates) == 1 else None
        if not resolved_id:
            # The indicator master is authoritative; orphan value rows are ignored.
            continue
        kind = str(row["Jenis Nilai"]).strip().lower()
        if kind not in {"realisasi", "target"}:
            continue
        numeric_value = row.get("Nilai (Angka)")
        numeric = numeric_value if isinstance(numeric_value, (int, float)) else None
        original_text = row.get("Nilai (Teks Asli)")
        text_value = str(original_text) if original_text not in (None, "") else None
        period_values=[]
        if kind == "realisasi" and text_value and ";" in text_value:
            for period,part in enumerate(text_value.split(";"),1):
                # Bagian non-numerik (mis. "n/a") dilewati, bukan menggagalkan seluruh baris.
                with suppress(ValueError): period_values.append((period,float(part.strip().replace(",","."))))
            if period_values: numeric=period_values[-1][1]
        conn.execute(
            """INSERT INTO beranda_nilai
            (id_indikator,tahun,jenis,nilai,nilai_teks,satuan_catatan,sumber_master)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(id_indikator,tahun,jenis) DO UPDATE SET
             nilai=excluded.nilai,nilai_teks=excluded.nilai_teks,
             satuan_catatan=excluded.satuan_catatan,sumber_master=excluded.sumber_master,
             status_verifikasi='DISETUJUI'""",
            (resolved_id, int(row["Tahun"]), kind, numeric, text_value,
             row.get("Satuan/Catatan"), source),
        )
        for period,period_value in period_values:
            conn.execute(
                """INSERT INTO beranda_nilai_periode
                (id_indikator,tahun,jenis,periode,nilai,label_periode,sumber_master)
                VALUES (?,?,?,?,?,?,?)""",
                (resolved_id,int(row["Tahun"]),kind,period,period_value,f"Semester {period}",source),
            )
    conn.commit()
    conn.close()
