"""Penyusunan muatan insight: kartu makro terbaru dan perbandingan antarwilayah.

Aturan pemilihan angka di sini sengaja sama dengan `services/beranda.py`:
bila ada rilis semester yang sudah disetujui, angka itulah yang dipakai. Dua
halaman yang menampilkan indikator sama tidak boleh memperlihatkan angka beda.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from ..models import KODE_PROVINSI, JenisNilai, Wilayah
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..repositories import wilayah as repo_wilayah
from . import nilai as svc_nilai
from .beranda import STATUS_HANYA_TERVERIFIKASI, urutkan_makro

CATATAN_WILAYAH = (
    "Data kabupaten/kota belum tersedia. Peta dan bar chart akan terisi setelah data operator wilayah diverifikasi."
)


def _kartu(session: Session, indikator: Any, wilayah_kode: str, tahun_sistem: int) -> tuple[dict[str, Any], int | None]:
    iid = indikator.id_indikator
    terakhir = repo_nilai.terakhir_terisi(session, iid, wilayah_kode, tahun_sistem)
    tahun_terakhir = terakhir.tahun if terakhir else None
    sebelumnya = (
        repo_nilai.sebelum_tahun(session, iid, wilayah_kode, tahun_terakhir) if tahun_terakhir is not None else None
    )
    periode = (
        repo_nilai.nilai_periode_terbaru(session, iid, wilayah_kode, tahun_terakhir)
        if tahun_terakhir is not None
        else None
    )
    angka_sekarang = (
        periode.nilai
        if periode
        else (svc_nilai.angka_terakhir(terakhir.nilai, terakhir.nilai_teks) if terakhir else None)
    )
    angka_sebelumnya = svc_nilai.angka_terakhir(sebelumnya.nilai, sebelumnya.nilai_teks) if sebelumnya else None
    # Label dirangkai lengkap dengan tahunnya: "Semester 2" saja tidak
    # memberi tahu semester tahun berapa.
    label = (
        f"{periode.label_periode} {tahun_terakhir}"
        if periode and periode.label_periode
        else (str(tahun_terakhir) if tahun_terakhir is not None else None)
    )
    kartu = {
        "id_indikator": iid,
        "kode_indikator": indikator.kode_indikator,
        "nama_indikator": indikator.nama_indikator,
        "kelompok": indikator.kelompok,
        "satuan": indikator.satuan,
        "sumber_data": indikator.sumber_data,
        "opd_pengampu": indikator.opd_pengampu,
        "tahun": tahun_terakhir,
        "label_periode": label,
        "nilai": periode.nilai if periode else (terakhir.nilai if terakhir else None),
        "nilai_teks": None if periode else (terakhir.nilai_teks if terakhir else None),
        "perubahan": svc_nilai.selisih(angka_sekarang, angka_sebelumnya),
        "status": "TERSEDIA" if terakhir else "BELUM_ADA_DATA",
    }
    return kartu, tahun_terakhir


def _seri(session: Session, id_indikator: str, wilayah_kode: str) -> list[dict[str, Any]]:
    hasil: list[dict[str, Any]] = []
    sebelumnya: float | None = None
    for baris in repo_nilai.seri(session, id_indikator, wilayah_kode, JenisNilai.REALISASI):
        angka = svc_nilai.angka_terakhir(baris.nilai, baris.nilai_teks)
        if angka is None:
            continue
        hasil.append(
            {
                "tahun": baris.tahun,
                "nilai": angka,
                "nilai_teks": baris.nilai_teks,
                "growth": svc_nilai.pertumbuhan(angka, sebelumnya),
            }
        )
        sebelumnya = angka
    return hasil


def susun(session: Session, wilayah: Wilayah, *, indikator_id: str | None) -> dict[str, Any]:
    """Muatan lengkap `/insight` untuk satu wilayah."""
    wilayah_kode = wilayah.kode
    tahun_sistem = date.today().year

    kartu: list[dict[str, Any]] = []
    # Tahun terakhir per indikator disimpan terpisah supaya pemakaian
    # berikutnya tidak perlu membacanya kembali dari dict campur tipe.
    tahun_kartu: dict[str, int | None] = {}
    # Tanpa batas jumlah: pemilih kartu berupa rel mendatar, jadi seluruh
    # indikator makro muat tanpa memotong daftar.
    for indikator in urutkan_makro(repo_indikator.daftar_makro(session)):
        satu, tahun_terakhir = _kartu(session, indikator, wilayah_kode, tahun_sistem)
        tahun_kartu[indikator.id_indikator] = tahun_terakhir
        kartu.append(satu)

    id_kartu = [str(x["id_indikator"]) for x in kartu]
    dipilih = indikator_id if indikator_id in id_kartu else (id_kartu[0] if id_kartu else None)
    aktif = next((x for x in kartu if x["id_indikator"] == dipilih), None)

    seri = _seri(session, dipilih, wilayah_kode) if dipilih else []

    tahun_aktif = tahun_kartu.get(dipilih) if dipilih else None
    perbandingan = []
    for daerah in repo_wilayah.daftar_anak_provinsi(session):
        nilai = (
            repo_nilai.ambil(session, dipilih, daerah.kode, tahun_aktif, JenisNilai.REALISASI)
            if dipilih and tahun_aktif
            else None
        )
        perbandingan.append(
            {
                "kode": daerah.kode,
                "nama": daerah.nama,
                "tingkat": daerah.tingkat,
                "nilai": nilai.nilai if nilai else None,
                "nilai_teks": nilai.nilai_teks if nilai else None,
                "status": "TERSEDIA" if nilai else "BELUM_ADA_DATA",
            }
        )

    return {
        "tahun_sistem": tahun_sistem,
        "wilayah": {"kode": wilayah.kode, "nama": wilayah.nama, "tingkat": wilayah.tingkat},
        "wilayah_opsi": [
            {"kode": w.kode, "nama": w.nama, "tingkat": w.tingkat} for w in repo_wilayah.daftar_aktif(session)
        ],
        "indikator_makro": kartu,
        "indikator_aktif": aktif,
        "series": seri,
        "perbandingan_wilayah": perbandingan,
        "status_data": STATUS_HANYA_TERVERIFIKASI,
        "catatan_wilayah": None if any(x["status"] == "TERSEDIA" for x in perbandingan) else CATATAN_WILAYAH,
    }


__all__ = ["CATATAN_WILAYAH", "KODE_PROVINSI", "susun"]
