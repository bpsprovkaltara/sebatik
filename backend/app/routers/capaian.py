"""Endpoint capaian: daftar ringkas dan penelusuran progres per indikator."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_session
from ..models import KODE_PROVINSI, JenisNilai
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..repositories import wilayah as repo_wilayah
from ..services import capaian as svc
from ..services import nilai as svc_nilai
from ..services.analitik import TAHUN_TARGET_AKHIR, TAHUN_TARGET_ANTARA
from .indikator import muatan_capaian

router = APIRouter(prefix="/api/v1", tags=["capaian"])

STATUS_HANYA_TERVERIFIKASI = "HANYA_TERVERIFIKASI"


@router.get("/capaian")
def daftar_capaian(
    kategori: str | None = None,
    kelompok: str | None = None,
    arah_pembangunan: str | None = None,
    tim: str | None = None,
    status_capaian: str | None = None,
    wilayah_kode: str | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    if wilayah_kode and not repo_wilayah.ada_dan_aktif(session, wilayah_kode):
        raise HTTPException(422, "Wilayah tidak valid")

    lingkup = wilayah_kode or KODE_PROVINSI
    data = [muatan_capaian(session, indikator, lingkup) for indikator in repo_indikator.daftar_ekspor(session)]
    for kunci, nilai in (
        ("kategori", kategori),
        ("kelompok", kelompok),
        ("arah_pembangunan", arah_pembangunan),
        ("tim_pjk", tim),
        ("status_capaian", status_capaian),
    ):
        if nilai:
            data = [baris for baris in data if baris.get(kunci) == nilai]
    return {"data": data, "total": len(data), "arah_bersifat_sementara": True}


@router.get("/capaian-explorer")
def pilihan_capaian(session: Session = Depends(get_session)) -> dict[str, Any]:
    indikator = [
        {
            "id_indikator": item.id_indikator,
            "kategori": item.kategori,
            "kelompok": item.kelompok,
            "arah_pembangunan": item.arah_pembangunan,
            "kode_indikator": item.kode_indikator,
            "nama_indikator": item.nama_indikator,
            "satuan": item.satuan,
        }
        for item in repo_indikator.daftar_terverifikasi(session)
    ]
    return {
        "indikator": indikator,
        "kelompok": sorted({x["kelompok"] for x in indikator if x["kelompok"]}),
        "wilayah": [{"kode": w.kode, "nama": w.nama, "tingkat": w.tingkat} for w in repo_wilayah.daftar_aktif(session)],
        "status_data": STATUS_HANYA_TERVERIFIKASI,
    }


@router.get("/capaian-explorer/{id_indikator}")
def detail_capaian(
    id_indikator: str,
    tahun: int | None = None,
    wilayah_kode: str = KODE_PROVINSI,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    indikator = repo_indikator.ambil_terverifikasi(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan atau belum diverifikasi")
    wilayah = repo_wilayah.ambil_aktif(session, wilayah_kode)
    if wilayah is None:
        raise HTTPException(422, "Wilayah tidak valid")

    semua = repo_nilai.seri(session, id_indikator, wilayah_kode)
    target = {baris.tahun: baris for baris in semua if baris.jenis == JenisNilai.TARGET}
    realisasi = [
        baris
        for baris in semua
        if baris.jenis == JenisNilai.REALISASI and svc_nilai.angka_terakhir(baris.nilai, baris.nilai_teks) is not None
    ]
    tahun_tersedia = [baris.tahun for baris in realisasi]
    dipilih = tahun if tahun in tahun_tersedia else (max(tahun_tersedia) if tahun_tersedia else tahun)

    def angka_target(tahun_target: int) -> float | None:
        baris = target.get(tahun_target)
        return svc_nilai.angka_terakhir(baris.nilai, baris.nilai_teks) if baris else None

    target_2045 = angka_target(TAHUN_TARGET_AKHIR)
    # Target antara RPJMD dipakai sebagai tolok progres pada tracker karena 2029
    # adalah horizon yang masih bisa ditindaklanjuti perencana hari ini; 2045
    # tetap dikirim sebagai tujuan akhir.
    target_2029 = angka_target(TAHUN_TARGET_ANTARA)

    seri: list[dict[str, Any]] = []
    sebelumnya: float | None = None
    for baris in realisasi:
        angka = svc_nilai.angka_terakhir(baris.nilai, baris.nilai_teks)
        seri.append(
            {
                "tahun": baris.tahun,
                "nilai": angka,
                "nilai_asli": baris.nilai,
                "nilai_teks": baris.nilai_teks,
                "growth": svc_nilai.pertumbuhan(angka, sebelumnya),
                "target": angka_target(baris.tahun),
            }
        )
        sebelumnya = angka

    sekarang = next((x for x in seri if x["tahun"] == dipilih), None)
    baseline = seri[0] if seri else None
    tahun_sebelumnya = next((x for x in reversed(seri) if dipilih and x["tahun"] < dipilih), None)

    arah = svc.arah_target(baseline["nilai"] if baseline else None, target_2045)
    nilai_sekarang = sekarang["nilai"] if sekarang else None
    nilai_baseline = baseline["nilai"] if baseline else None
    progres_2045 = svc.progres_menuju(nilai_sekarang, nilai_baseline, target_2045)
    progres_2029 = svc.progres_menuju(nilai_sekarang, nilai_baseline, target_2029)
    gap_2045 = svc_nilai.selisih(target_2045, nilai_sekarang, digit=4)
    gap_2029 = svc_nilai.selisih(target_2029, nilai_sekarang, digit=4)

    proyeksi = [
        {
            "tahun": x["tahun"],
            "realisasi": x["nilai"],
            "jalur_target": nilai_sekarang if x["tahun"] == dipilih else None,
        }
        for x in seri
    ]
    if target_2045 is not None and not any(x["tahun"] == TAHUN_TARGET_AKHIR for x in proyeksi):
        proyeksi.append({"tahun": TAHUN_TARGET_AKHIR, "realisasi": None, "jalur_target": target_2045})

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
        "wilayah": {"kode": wilayah.kode, "nama": wilayah.nama, "tingkat": wilayah.tingkat},
        "tahun": dipilih,
        "tahun_tersedia": tahun_tersedia,
        "series": seri,
        "projection": proyeksi,
        "nilai_tahun": nilai_sekarang,
        "nilai_teks": sekarang["nilai_teks"] if sekarang else None,
        "target_2045": target_2045,
        "target_2045_teks": target[TAHUN_TARGET_AKHIR].nilai_teks if TAHUN_TARGET_AKHIR in target else None,
        "target_2029": target_2029,
        "target_2029_teks": target[TAHUN_TARGET_ANTARA].nilai_teks if TAHUN_TARGET_ANTARA in target else None,
        "arah_target": arah,
        "progres_2045": progres_2045,
        "progres_2029": progres_2029,
        "gap_2045": gap_2045,
        "gap_2029": gap_2029,
        "kebutuhan_per_tahun": svc.kebutuhan_per_tahun(gap_2045, dipilih, TAHUN_TARGET_AKHIR),
        "insight": svc.kalimat_insight(
            nama_wilayah=wilayah.nama,
            tahun=dipilih,
            ada_nilai=sekarang is not None,
            tahun_baseline=baseline["tahun"] if baseline else None,
            progres_2029=progres_2029,
            progres_2045=progres_2045,
            target_2029=target_2029,
            target_2045=target_2045,
            sedang_membaik=svc.membaik(
                nilai_sekarang,
                tahun_sebelumnya["nilai"] if tahun_sebelumnya else None,
                arah,
            ),
        ),
        "status_data": STATUS_HANYA_TERVERIFIKASI,
        "catatan_wilayah": None
        if wilayah_kode == KODE_PROVINSI
        else "Belum ada basis data kabupaten/kota. Visualisasi akan terisi setelah data wilayah diverifikasi.",
    }
