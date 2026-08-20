"""Penyusunan muatan penjelajah indikator: pengelompokan dan lini masa.

Pengelompokan dan penyusunan lini masa adalah perhitungan, jadi tempatnya di
sini dan bukan di router (backend.md §1.2).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..models import KODE_PROVINSI, Indikator, JenisNilai
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..repositories import wilayah as repo_wilayah
from . import nilai as svc_nilai
from .beranda import STATUS_HANYA_TERVERIFIKASI

TANPA_KELOMPOK = "Tanpa Kelompok"
CATATAN_WILAYAH = (
    "Data kabupaten/kota belum tersedia. Nilai akan tampil setelah operator "
    "wilayah mengirim dan verifikator menyetujui."
)


def _ringkas(item: Indikator) -> dict[str, Any]:
    return {
        "id_indikator": item.id_indikator,
        "kategori": item.kategori,
        "kelompok": item.kelompok,
        "arah_pembangunan": item.arah_pembangunan,
        "kode_indikator": item.kode_indikator,
        "nama_indikator": item.nama_indikator,
        "satuan": item.satuan,
    }


def kelompokkan(daftar: list[Indikator]) -> dict[str, Any]:
    """Indikator terverifikasi dikelompokkan per kelompok/pilar."""
    data = [
        _ringkas(item)
        # Urutan lama: kelompok, lalu ISV sebelum IUP, lalu id.
        for item in sorted(daftar, key=lambda x: (x.kelompok or TANPA_KELOMPOK, x.kategori != "IUP", x.id_indikator))
    ]
    kelompok = []
    for nama in dict.fromkeys(x["kelompok"] or TANPA_KELOMPOK for x in data):
        anggota = [x for x in data if (x["kelompok"] or TANPA_KELOMPOK) == nama]
        kelompok.append({"kelompok": nama, "jumlah": len(anggota), "indikator": anggota})
    return {
        "data": kelompok,
        "total_indikator": len(data),
        "status_data": STATUS_HANYA_TERVERIFIKASI,
    }


def daftar(session: Session) -> dict[str, Any]:
    return kelompokkan(repo_indikator.daftar_terverifikasi(session))


def pilihan_capaian(session: Session) -> dict[str, Any]:
    """Daftar pilihan untuk halaman capaian: indikator, kelompok, wilayah."""
    indikator = [_ringkas(item) for item in repo_indikator.daftar_terverifikasi(session)]
    return {
        "indikator": indikator,
        "kelompok": sorted({x["kelompok"] for x in indikator if x["kelompok"]}),
        "wilayah": [{"kode": w.kode, "nama": w.nama, "tingkat": w.tingkat} for w in repo_wilayah.daftar_aktif(session)],
        "status_data": STATUS_HANYA_TERVERIFIKASI,
    }


def detail(session: Session, indikator: Indikator, *, tahun: int | None) -> dict[str, Any]:
    """Lini masa provinsi dan sebaran wilayah untuk satu indikator."""
    id_indikator = indikator.id_indikator
    semua = repo_nilai.seri(session, id_indikator, KODE_PROVINSI)
    realisasi = {b.tahun: b for b in semua if b.jenis == JenisNilai.REALISASI}
    target = {b.tahun: b for b in semua if b.jenis == JenisNilai.TARGET}
    tahun_tersedia = sorted(realisasi)
    dipilih = tahun if tahun in tahun_tersedia else (max(tahun_tersedia) if tahun_tersedia else None)

    lini_masa: list[dict[str, Any]] = []
    sebelumnya: float | None = None
    for satu_tahun in sorted(set(realisasi) | set(target)):
        baris_realisasi = realisasi.get(satu_tahun)
        baris_target = target.get(satu_tahun)
        angka = svc_nilai.angka_terakhir(
            baris_realisasi.nilai if baris_realisasi else None,
            baris_realisasi.nilai_teks if baris_realisasi else None,
        )
        lini_masa.append(
            {
                "tahun": satu_tahun,
                "realisasi": baris_realisasi.nilai if baris_realisasi else None,
                "realisasi_teks": baris_realisasi.nilai_teks if baris_realisasi else None,
                "label_periode": svc_nilai.label_periode_tampil(
                    indikator.nama_indikator, baris_realisasi.label_periode, satu_tahun
                ) if baris_realisasi else None,
                "target": baris_target.nilai if baris_target else None,
                "target_teks": baris_target.nilai_teks if baris_target else None,
                "growth": svc_nilai.pertumbuhan(angka, sebelumnya),
            }
        )
        if angka is not None:
            sebelumnya = angka

    wilayah = []
    for daerah in repo_wilayah.daftar_anak_provinsi(session):
        nilai = repo_nilai.ambil(session, id_indikator, daerah.kode, dipilih, JenisNilai.REALISASI) if dipilih else None
        target_wilayah = (
            repo_nilai.ambil(session, id_indikator, daerah.kode, dipilih, JenisNilai.TARGET) if dipilih else None
        )
        wilayah.append(
            {
                "kode": daerah.kode,
                "nama": daerah.nama,
                "tingkat": daerah.tingkat,
                "tahun": dipilih,
                "nilai": nilai.nilai if nilai else None,
                "nilai_teks": nilai.nilai_teks if nilai else None,
                "target": target_wilayah.nilai if target_wilayah else None,
                "target_teks": target_wilayah.nilai_teks if target_wilayah else None,
                "status": "TERSEDIA" if nilai else "BELUM_ADA_DATA",
            }
        )

    return {
        "id_indikator": indikator.id_indikator,
        "kategori": indikator.kategori,
        "kelompok": indikator.kelompok,
        "arah_pembangunan": indikator.arah_pembangunan,
        "kode_indikator": indikator.kode_indikator,
        "nama_indikator": indikator.nama_indikator,
        "satuan": indikator.satuan,
        "sumber_data": indikator.sumber_data,
        "frekuensi": indikator.frekuensi,
        "opd_pengampu": indikator.opd_pengampu,
        "tahun": dipilih,
        "tahun_tersedia": tahun_tersedia,
        "series": lini_masa,
        "wilayah": wilayah,
        "status_data": STATUS_HANYA_TERVERIFIKASI,
        "catatan_wilayah": CATATAN_WILAYAH,
    }
