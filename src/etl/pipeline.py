"""Orkestrator ETL workbook ISV-IUP: extract -> transform -> load.

Modul ini hanya merangkai tahapan dan menyusun laporan. Seluruh pemetaan sheet,
kolom, dan tahun berada di `src/etl/config/workbook.yaml`; tidak ada rentang
angka bermakna bisnis di berkas ini.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import openpyxl

from .config import KonfigurasiWorkbook, bawaan
from .extract import baca_master, baca_nilai, lengkapi_pemilik
from .extract.values import StatistikParsing
from .load import tulis_basis_data, tulis_cadangan

NAMA_DIREKTORI_CADANGAN = "cadangan"


class JumlahIndikatorTidakSesuai(RuntimeError):
    """Workbook menghasilkan jumlah indikator di luar ekspektasi konfigurasi."""


def _susun_laporan(
    jumlah: dict[str, int],
    statistik: StatistikParsing,
    jumlah_nilai: int,
    status_parquet: str,
    galat_fk: list[Any],
    tanpa_realisasi: list[str],
    konfigurasi: KonfigurasiWorkbook,
) -> str:
    urutan_sumber = " -> ".join(f"`{sumber.sheet}`" for sumber in konfigurasi.nilai)
    baris = [
        "# Laporan ETL SEBATIK",
        "",
        f"Konfigurasi workbook versi **{konfigurasi.versi}**.",
        "",
        "## Ringkasan tabel",
        "",
        "| Tabel | Jumlah baris |",
        "|---|---:|",
    ]
    baris += [f"| {nama} | {angka} |" for nama, angka in jumlah.items()]
    baris += [
        "",
        "## Validasi parsing nilai",
        "",
        f"- Berhasil di-parse: **{statistik.berhasil}** sel sumber.",
        f"- Gagal di-parse: **{statistik.gagal}** sel sumber nonkosong.",
        f"- Kosong dan dipertahankan sebagai NULL/tidak dibuat: **{statistik.kosong}** sel sumber.",
        f"- Fakta unik setelah prioritas sumber: **{jumlah_nilai}** baris.",
        f"- Cadangan Parquet: **{status_parquet}**; CSV selalu dibuat.",
        f"- Pelanggaran foreign key: **{len(galat_fk)}**.",
        "",
        f"## Indikator tanpa satu pun nilai realisasi ({len(tanpa_realisasi)})",
        "",
    ]
    baris += [f"- {iid}" for iid in tanpa_realisasi] or ["Tidak ada."]
    baris += [
        "",
        "## Aturan provenans",
        "",
        f"Urutan prioritas: {urutan_sumber}. "
        "Sumber lama hanya mengisi kombinasi indikator-tahun-jenis yang masih kosong.",
    ]
    return "\n".join(baris) + "\n"


def run(
    workbook_path: Path,
    db_path: Path,
    report_path: Path,
    konfigurasi: KonfigurasiWorkbook | None = None,
) -> dict[str, Any]:
    """Jalankan pipeline penuh dan kembalikan ringkasan hasilnya."""
    konfigurasi = konfigurasi or bawaan()
    wb = openpyxl.load_workbook(workbook_path, data_only=True)
    try:
        indikator, pic = baca_master(wb, konfigurasi)
        lengkapi_pemilik(wb, konfigurasi, indikator)
        nilai, statistik = baca_nilai(wb, konfigurasi)
    finally:
        wb.close()

    diharapkan = konfigurasi.jumlah_indikator_diharapkan
    if len(indikator) != diharapkan:
        raise JumlahIndikatorTidakSesuai(
            f"Dimensi indikator diharapkan {diharapkan} menurut konfigurasi, ditemukan {len(indikator)}"
        )

    hasil = tulis_basis_data(db_path, indikator, nilai, pic)
    status_parquet = tulis_cadangan(db_path.parent / NAMA_DIREKTORI_CADANGAN, indikator, nilai, pic)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _susun_laporan(
            hasil["jumlah"],
            statistik,
            len(nilai),
            status_parquet,
            hasil["galat_fk"],
            hasil["tanpa_realisasi"],
            konfigurasi,
        ),
        encoding="utf-8",
    )
    print(f"ETL selesai: {hasil['jumlah']}; parse berhasil={statistik.berhasil}, gagal={statistik.gagal}")
    return {"indikator": indikator, "nilai": nilai, "pic": pic, "statistik": statistik, **hasil}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--db", type=Path, default=Path("data/processed/sebatik.db"))
    parser.add_argument("--report", type=Path, default=Path("docs/02-etl-report.md"))
    parser.add_argument("--config", type=Path, default=None, help="berkas workbook.yaml alternatif")
    argumen = parser.parse_args()

    konfigurasi = bawaan()
    if argumen.config:
        from .config import muat

        konfigurasi = muat(argumen.config)
    run(argumen.workbook, argumen.db, argumen.report, konfigurasi)


if __name__ == "__main__":
    main()
