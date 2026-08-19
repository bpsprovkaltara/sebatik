"""Pembacaan dimensi indikator dari sheet master.

Berbasis header: nama kolom dipetakan sekali ke indeksnya, lalu pembacaan
memakai nama field internal. Tidak ada indeks kolom ajaib di kode ini.
"""

from __future__ import annotations

from typing import Any

from ..config import KonfigurasiWorkbook, SumberMaster
from ..transform import bersihkan_teks, ekstrak_proxy, enum_rpjmd, id_indikator, parse_angka
from ..units import indicator_unit


class SheetTidakDitemukan(Exception):
    """Workbook tidak memuat sheet yang dibutuhkan konfigurasi."""


def indeks_header(ws, baris_header: int) -> dict[str, int]:
    """Pemetaan label header -> nomor kolom. Kolom tanpa label dilewati."""
    hasil: dict[str, int] = {}
    for kolom in range(1, ws.max_column + 1):
        label = bersihkan_teks(ws.cell(baris_header, kolom).value)
        if label:
            hasil[label] = kolom
    return hasil


def _pembaca(ws, header: dict[str, int], master: SumberMaster):
    def baca(baris: int, field_internal: str) -> Any:
        for label in master.label(field_internal):
            kolom = header.get(label)
            if kolom:
                return ws.cell(baris, kolom).value
        return None

    return baca


def _sheet(wb, nama: str):
    if nama not in wb.sheetnames:
        raise SheetTidakDitemukan(f"Sheet '{nama}' tidak ada di workbook")
    return wb[nama]


def baca_master(wb, konfigurasi: KonfigurasiWorkbook) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Baris indikator dan penugasan PIC dari sheet master."""
    master = konfigurasi.master
    ws = _sheet(wb, master.sheet)
    header = indeks_header(ws, master.baris_header)
    baca = _pembaca(ws, header, master)

    indikator: list[dict[str, Any]] = []
    pic: list[dict[str, Any]] = []
    urutan = dict.fromkeys(konfigurasi.kategori, 0)

    for baris in master.baris.rentang(ws.max_row):
        kategori = (bersihkan_teks(baca(baris, "kategori")) or "").upper()
        if kategori not in urutan:
            continue
        urutan[kategori] += 1
        iid = id_indikator(kategori, urutan[kategori])
        if not iid:
            continue

        nama_asli = bersihkan_teks(baca(baris, "nama_asli"))
        nama_perbaikan = bersihkan_teks(baca(baris, "nama_perbaikan"))
        proxy, nama_proxy = ekstrak_proxy(baca(baris, "indikator_proxy"), baca(baris, "catatan_teknis"))
        indikator.append(
            {
                "id_indikator": iid,
                "kategori": kategori,
                "nomor": urutan[kategori],
                "nama_indikator": nama_perbaikan or nama_asli,
                "nama_asli": nama_asli,
                "kelompok": bersihkan_teks(baca(baris, "kelompok")),
                "arah_pembangunan": bersihkan_teks(baca(baris, "arah_pembangunan")),
                "satuan": indicator_unit(iid),
                "penghasil": bersihkan_teks(baca(baris, "penghasil")),
                "kl_pengampu": bersihkan_teks(baca(baris, "kl_pengampu")),
                "opd_penanggung_jawab": None,
                "tim_pjk": bersihkan_teks(baca(baris, "tim_pjk")),
                "status_ketersediaan": bersihkan_teks(baca(baris, "status_ketersediaan")),
                "status_metadata": bersihkan_teks(baca(baris, "status_metadata"))
                or master.bawaan.get("status_metadata"),
                "periode_data": bersihkan_teks(baca(baris, "periode_data")),
                "tahun_terakhir": _tahun_wajar(baca(baris, "tahun_terakhir"), master),
                "is_proxy": proxy,
                "nama_proxy": nama_proxy,
                "status_rpjmd": enum_rpjmd(baca(baris, "status_rpjmd")),
                "kode_sdgs": bersihkan_teks(baca(baris, "kode_sdgs")),
                "link_metadata": bersihkan_teks(baca(baris, "link_metadata")),
                "link_publikasi": bersihkan_teks(baca(baris, "link_publikasi")),
                "link_data": bersihkan_teks(baca(baris, "link_data")),
                "catatan_teknis": bersihkan_teks(baca(baris, "catatan_teknis")),
            }
        )
        for jenis, label in master.pic.items():
            kolom = header.get(label)
            orang = bersihkan_teks(ws.cell(baris, kolom).value) if kolom else None
            if orang:
                pic.append({"id_indikator": iid, "jenis_pic": jenis, "nama_pic": orang})

    return indikator, pic


def _tahun_wajar(nilai: Any, master: SumberMaster) -> int | None:
    """Tahun di luar rentang wajar diperlakukan sebagai tidak terisi."""
    tahun = parse_angka(nilai)
    if tahun is None:
        return None
    awal, akhir = master.tahun_terakhir_rentang
    return int(tahun) if awal <= tahun <= akhir else None


def lengkapi_pemilik(wb, konfigurasi: KonfigurasiWorkbook, indikator: list[dict[str, Any]]) -> None:
    """Isi `opd_penanggung_jawab` dari sheet kepemilikan.

    Tim PJK sengaja tidak diambil dari sini; master tetap sumbernya supaya
    domain nilainya tidak berubah.
    """
    pemilik = konfigurasi.pemilik
    ws = _sheet(wb, pemilik.sheet)
    peta: dict[str, str | None] = {}
    for baris in pemilik.baris.rentang(ws.max_row):
        iid = _id_dari_nomor(
            ws.cell(baris, pemilik.kolom_nomor).value,
            ws.cell(baris, pemilik.kolom_nama).value,
            konfigurasi.isv_nomor_maksimum,
        )
        if iid:
            peta[iid] = bersihkan_teks(ws.cell(baris, pemilik.kolom_opd).value)

    for item in indikator:
        item["opd_penanggung_jawab"] = peta.get(item["id_indikator"])


def _id_dari_nomor(nomor: Any, nama: Any, isv_nomor_maksimum: int) -> str | None:
    """Identitas pada sheet lama: nomor menyambung + nama sebagai penanda baris isi."""
    from ..transform import kategori_dari_nomor, nomor_dalam_kategori

    angka = parse_angka(nomor)
    if angka is None or not bersihkan_teks(nama):
        return None
    kategori = kategori_dari_nomor(angka, isv_nomor_maksimum)
    if kategori is None:
        return None
    return id_indikator(kategori, nomor_dalam_kategori(angka, kategori, isv_nomor_maksimum))
