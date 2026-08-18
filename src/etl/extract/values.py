"""Pembacaan nilai indikator dari sheet-sheet sumber, seluruhnya dari konfigurasi.

Urutan sumber di konfigurasi adalah urutan prioritas: sumber berikutnya hanya
mengisi kombinasi (indikator, tahun, jenis) yang masih kosong.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..config import Blok, KonfigurasiWorkbook, SumberNilai
from ..transform import (
    bersihkan_teks,
    id_indikator,
    kategori_dari_nomor,
    nomor_dalam_kategori,
    parse_angka,
)

JENIS_DIKENAL = ("realisasi", "target")
JENIS_DARI_KOLOM = "dari_kolom"


@dataclass
class StatistikParsing:
    berhasil: int = 0
    gagal: int = 0
    kosong: int = 0


def _identitas_kategori_nomor(ws, baris: int, sumber: SumberNilai, terakhir: dict[str, Any]) -> str | None:
    """Identitas dari kolom kategori + nomor, dengan penerusan merged cell."""
    kategori = ws.cell(baris, sumber.kolom_kategori).value
    nomor = ws.cell(baris, sumber.kolom_nomor).value
    if sumber.teruskan_identitas:
        kategori = kategori or terakhir.get("kategori")
        nomor = nomor or terakhir.get("nomor")
        terakhir["kategori"], terakhir["nomor"] = kategori, nomor

    kategori_bersih = (bersihkan_teks(kategori) or "").upper()
    if not kategori_bersih:
        return None
    return id_indikator(
        kategori_bersih,
        nomor_dalam_kategori(nomor, kategori_bersih, terakhir["isv_maks"]),
    )


def _identitas_nomor_saja(ws, baris: int, sumber: SumberNilai, isv_maks: int) -> str | None:
    """Identitas dari nomor menyambung; nama dipakai sebagai penanda baris terisi."""
    nomor = parse_angka(ws.cell(baris, sumber.kolom_nomor).value)
    nama = bersihkan_teks(ws.cell(baris, sumber.kolom_nama).value) if sumber.kolom_nama else None
    if nomor is None or not nama:
        return None
    kategori = kategori_dari_nomor(nomor, isv_maks)
    if kategori is None:
        return None
    return id_indikator(kategori, nomor_dalam_kategori(nomor, kategori, isv_maks))


def _catat(
    gudang: dict[tuple[str, int, str], dict[str, Any]],
    statistik: StatistikParsing,
    iid: str,
    tahun: int,
    jenis: str,
    mentah: Any,
    sheet: str,
) -> None:
    if mentah is None or (isinstance(mentah, str) and not mentah.strip()):
        statistik.kosong += 1
        return
    nilai = parse_angka(mentah)
    if nilai is None:
        statistik.gagal += 1
        return
    statistik.berhasil += 1
    # setdefault: sumber berprioritas lebih rendah tidak menimpa yang lebih tinggi.
    gudang.setdefault(
        (iid, int(tahun), jenis),
        {
            "id_indikator": iid,
            "tahun": int(tahun),
            "jenis": jenis,
            "nilai": nilai,
            "sumber_sheet": sheet,
        },
    )


def _jenis_blok(blok: Blok, jenis_baris: str | None) -> str | None:
    """Jenis efektif satu blok pada satu baris, atau None bila blok dilewati."""
    if blok.jenis != JENIS_DARI_KOLOM:
        return blok.jenis
    if jenis_baris is None or jenis_baris not in JENIS_DIKENAL:
        return None
    if blok.hanya_jenis and jenis_baris != blok.hanya_jenis:
        return None
    return jenis_baris


def baca_nilai(wb, konfigurasi: KonfigurasiWorkbook) -> tuple[list[dict[str, Any]], StatistikParsing]:
    gudang: dict[tuple[str, int, str], dict[str, Any]] = {}
    statistik = StatistikParsing()

    for sumber in konfigurasi.nilai:
        if sumber.sheet not in wb.sheetnames:
            continue
        ws = wb[sumber.sheet]
        terakhir: dict[str, Any] = {"isv_maks": konfigurasi.isv_nomor_maksimum}

        for baris in sumber.baris.rentang(ws.max_row):
            if sumber.identitas == "kategori_nomor":
                iid = _identitas_kategori_nomor(ws, baris, sumber, terakhir)
            else:
                iid = _identitas_nomor_saja(ws, baris, sumber, konfigurasi.isv_nomor_maksimum)
            if not iid:
                continue

            jenis_baris = (
                (bersihkan_teks(ws.cell(baris, sumber.kolom_jenis).value) or "").casefold()
                if sumber.kolom_jenis
                else None
            )
            for blok in sumber.blok:
                jenis = _jenis_blok(blok, jenis_baris)
                if jenis is None:
                    continue
                for kolom, tahun in blok.pasangan_kolom_tahun():
                    if kolom > ws.max_column:
                        continue
                    _catat(gudang, statistik, iid, tahun, jenis, ws.cell(baris, kolom).value, ws.title)

    return list(gudang.values()), statistik
