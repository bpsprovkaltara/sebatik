"""Endpoint insight: kartu makro terbaru dan perbandingan antarwilayah."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_session
from ..models import KODE_PROVINSI, JenisNilai
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..repositories import wilayah as repo_wilayah
from ..services import nilai as svc_nilai
from .beranda import urutkan_makro

router = APIRouter(prefix="/api/v1", tags=["insight"])

STATUS_HANYA_TERVERIFIKASI = "HANYA_TERVERIFIKASI"
CATATAN_WILAYAH = (
    "Data kabupaten/kota belum tersedia. Peta dan bar chart akan terisi setelah data operator wilayah diverifikasi."
)


@router.get("/insight")
def insight(
    indikator_id: str | None = None,
    wilayah_kode: str = KODE_PROVINSI,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    wilayah = repo_wilayah.ambil_aktif(session, wilayah_kode)
    if wilayah is None:
        raise HTTPException(422, "Wilayah tidak valid")

    tahun_sistem = date.today().year
    kartu: list[dict[str, Any]] = []
    # Tahun terakhir per indikator disimpan terpisah supaya pemakaian
    # berikutnya tidak perlu membacanya kembali dari dict campur tipe.
    tahun_kartu: dict[str, int | None] = {}
    # Tanpa batas jumlah: pemilih kartu berupa rel mendatar, jadi seluruh
    # indikator makro muat tanpa memotong daftar.
    for indikator in urutkan_makro(repo_indikator.daftar_makro(session)):
        iid = indikator.id_indikator
        terakhir = repo_nilai.terakhir_terisi(session, iid, wilayah_kode, tahun_sistem)
        tahun_terakhir = terakhir.tahun if terakhir else None
        tahun_kartu[iid] = tahun_terakhir
        sebelumnya = (
            repo_nilai.sebelum_tahun(session, iid, wilayah_kode, tahun_terakhir) if tahun_terakhir is not None else None
        )
        # Beranda sudah memakai aturan periode-terbaru; kartu Insight harus sama
        # agar keduanya tidak memperlihatkan angka berbeda untuk indikator sama.
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
        kartu.append(
            {
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
        )

    id_kartu = [str(x["id_indikator"]) for x in kartu]
    dipilih = indikator_id if indikator_id in id_kartu else (id_kartu[0] if id_kartu else None)
    aktif = next((x for x in kartu if x["id_indikator"] == dipilih), None)

    seri: list[dict[str, Any]] = []
    sebelumnya_angka: float | None = None
    if dipilih:
        for baris in repo_nilai.seri(session, dipilih, wilayah_kode, JenisNilai.REALISASI):
            angka = svc_nilai.angka_terakhir(baris.nilai, baris.nilai_teks)
            if angka is None:
                continue
            seri.append(
                {
                    "tahun": baris.tahun,
                    "nilai": angka,
                    "nilai_teks": baris.nilai_teks,
                    "growth": svc_nilai.pertumbuhan(angka, sebelumnya_angka),
                }
            )
            sebelumnya_angka = angka

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
