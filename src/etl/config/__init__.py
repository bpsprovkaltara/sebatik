"""Pemuat konfigurasi workbook ETL.

Konfigurasi dibaca sekali menjadi struktur data bertipe, lalu diteruskan ke
tahap extract/transform/load. Kode tidak lagi menyimpan nomor baris, nomor
kolom, atau rentang tahun yang bermakna bisnis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

BERKAS_BAWAAN = Path(__file__).resolve().parent / "workbook.yaml"

# Penanda "baca sampai data habis" pada `Baris.akhir`.
SAMPAI_HABIS = None


class KonfigurasiTidakValid(Exception):
    """Konfigurasi workbook tidak dapat dipakai."""


@dataclass(frozen=True)
class Baris:
    awal: int
    akhir: int | None = SAMPAI_HABIS

    def rentang(self, baris_maksimum: int) -> range:
        """Rentang baris yang akan dibaca, dibatasi ukuran sheet sebenarnya."""
        akhir = baris_maksimum if self.akhir is None else min(self.akhir, baris_maksimum)
        return range(self.awal, akhir + 1)


@dataclass(frozen=True)
class Blok:
    """Sekelompok kolom yang memetakan satu jenis nilai ke deretan tahun."""

    jenis: str
    tahun_awal: int | None = None
    kolom_awal: int | None = None
    kolom_akhir: int | None = None
    kolom: int | None = None
    tahun: int | None = None
    hanya_jenis: str | None = None

    def pasangan_kolom_tahun(self) -> list[tuple[int, int]]:
        if self.kolom is not None and self.tahun is not None:
            return [(self.kolom, self.tahun)]
        if self.kolom_awal is None or self.kolom_akhir is None or self.tahun_awal is None:
            raise KonfigurasiTidakValid(f"Blok {self.jenis} tidak lengkap")
        jumlah = self.kolom_akhir - self.kolom_awal + 1
        return [(self.kolom_awal + i, self.tahun_awal + i) for i in range(jumlah)]


@dataclass(frozen=True)
class SumberNilai:
    sheet: str
    identitas: str
    baris: Baris
    blok: tuple[Blok, ...]
    kolom_kategori: int | None = None
    kolom_nomor: int | None = None
    kolom_nama: int | None = None
    kolom_jenis: int | None = None
    teruskan_identitas: bool = False


@dataclass(frozen=True)
class SumberMaster:
    sheet: str
    baris_header: int
    baris: Baris
    kolom: dict[str, str]
    kolom_alternatif: dict[str, list[str]]
    pic: dict[str, str]
    bawaan: dict[str, str]
    tahun_terakhir_rentang: tuple[int, int]

    def label(self, field_internal: str) -> list[str]:
        """Semua label header yang dapat mewakili satu field."""
        utama = self.kolom.get(field_internal)
        alternatif = self.kolom_alternatif.get(field_internal, [])
        return ([utama] if utama else []) + list(alternatif)


@dataclass(frozen=True)
class SumberPemilik:
    sheet: str
    identitas: str
    baris: Baris
    kolom_nomor: int
    kolom_nama: int
    kolom_opd: int


@dataclass(frozen=True)
class KonfigurasiWorkbook:
    versi: int
    isv_nomor_maksimum: int
    kategori: tuple[str, ...]
    jumlah_indikator_diharapkan: int
    master: SumberMaster
    pemilik: SumberPemilik
    nilai: tuple[SumberNilai, ...]
    sheet_audit: tuple[str, ...]
    tahun_valid: tuple[int, int]
    sheet_wajib: tuple[str, ...] = field(default=())


def _baris(data: dict[str, Any]) -> Baris:
    return Baris(awal=int(data["awal"]), akhir=data.get("akhir"))


def _blok(data: dict[str, Any]) -> Blok:
    return Blok(
        jenis=str(data["jenis"]),
        tahun_awal=data.get("tahun_awal"),
        kolom_awal=data.get("kolom_awal"),
        kolom_akhir=data.get("kolom_akhir"),
        kolom=data.get("kolom"),
        tahun=data.get("tahun"),
        hanya_jenis=data.get("hanya_jenis"),
    )


def muat(path: Path | None = None) -> KonfigurasiWorkbook:
    """Baca dan validasi konfigurasi workbook."""
    berkas = path or BERKAS_BAWAAN
    try:
        mentah = yaml.safe_load(berkas.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise KonfigurasiTidakValid(f"Konfigurasi tidak ditemukan: {berkas}") from exc
    if not isinstance(mentah, dict):
        raise KonfigurasiTidakValid(f"Konfigurasi harus berupa pemetaan: {berkas}")

    master_mentah = mentah["master"]
    master = SumberMaster(
        sheet=master_mentah["sheet"],
        baris_header=int(master_mentah.get("baris_header", 1)),
        baris=_baris(master_mentah["baris"]),
        kolom=dict(master_mentah["kolom"]),
        kolom_alternatif={k: list(v) for k, v in (master_mentah.get("kolom_alternatif") or {}).items()},
        pic=dict(master_mentah.get("pic") or {}),
        bawaan=dict(master_mentah.get("bawaan") or {}),
        tahun_terakhir_rentang=tuple(master_mentah.get("tahun_terakhir_rentang", (1900, 2100))),
    )

    pemilik_mentah = mentah["pemilik"]
    pemilik = SumberPemilik(
        sheet=pemilik_mentah["sheet"],
        identitas=pemilik_mentah["identitas"],
        baris=_baris(pemilik_mentah["baris"]),
        kolom_nomor=int(pemilik_mentah["kolom_nomor"]),
        kolom_nama=int(pemilik_mentah["kolom_nama"]),
        kolom_opd=int(pemilik_mentah["kolom_opd"]),
    )

    sumber_nilai = tuple(
        SumberNilai(
            sheet=item["sheet"],
            identitas=item["identitas"],
            baris=_baris(item["baris"]),
            blok=tuple(_blok(b) for b in item["blok"]),
            kolom_kategori=item.get("kolom_kategori"),
            kolom_nomor=item.get("kolom_nomor"),
            kolom_nama=item.get("kolom_nama"),
            kolom_jenis=item.get("kolom_jenis"),
            teruskan_identitas=bool(item.get("teruskan_identitas", False)),
        )
        for item in mentah["nilai"]
    )

    konfigurasi = KonfigurasiWorkbook(
        versi=int(mentah.get("versi", 1)),
        isv_nomor_maksimum=int(mentah["kategori"]["isv_nomor_maksimum"]),
        kategori=tuple(mentah["kategori"]["daftar"]),
        jumlah_indikator_diharapkan=int(mentah["ekspektasi"]["jumlah_indikator"]),
        master=master,
        pemilik=pemilik,
        nilai=sumber_nilai,
        sheet_audit=tuple(mentah["audit"]["sheet"]),
        tahun_valid=tuple(mentah["audit"]["tahun_valid"]),
        sheet_wajib=tuple(dict.fromkeys([master.sheet, pemilik.sheet, *(s.sheet for s in sumber_nilai)])),
    )
    _validasi(konfigurasi)
    return konfigurasi


def _validasi(konfigurasi: KonfigurasiWorkbook) -> None:
    if not konfigurasi.nilai:
        raise KonfigurasiTidakValid("Minimal satu sumber nilai harus dikonfigurasi")
    for sumber in konfigurasi.nilai:
        if sumber.identitas not in {"kategori_nomor", "nomor_saja"}:
            raise KonfigurasiTidakValid(f"{sumber.sheet}: identitas '{sumber.identitas}' tidak dikenal")
        if sumber.identitas == "kategori_nomor" and sumber.kolom_kategori is None:
            raise KonfigurasiTidakValid(f"{sumber.sheet}: kolom_kategori wajib diisi")
        if sumber.kolom_nomor is None:
            raise KonfigurasiTidakValid(f"{sumber.sheet}: kolom_nomor wajib diisi")
        for blok in sumber.blok:
            if blok.jenis == "dari_kolom" and sumber.kolom_jenis is None:
                raise KonfigurasiTidakValid(f"{sumber.sheet}: blok 'dari_kolom' butuh kolom_jenis")
            # Memanggilnya sekaligus memvalidasi kelengkapan blok.
            blok.pasangan_kolom_tahun()


@lru_cache
def bawaan() -> KonfigurasiWorkbook:
    """Konfigurasi bawaan yang dipakai pipeline dan audit."""
    return muat()
