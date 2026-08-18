"""Endpoint analitik: selisih tahunan, peringkat, gap target, multi-seri, korelasi."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..deps import get_session
from ..models import KODE_PROVINSI, JenisNilai
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..services import analitik as svc

router = APIRouter(prefix="/api/v1", tags=["analitik"])

MAKSIMUM_INDIKATOR_MULTI = 4
BATAS_PERINGKAT = 10


def _seri_realisasi(session: Session, id_indikator: str) -> list[tuple[int, float]]:
    """Pasangan (tahun, nilai) realisasi tahunan yang benar-benar berangka."""
    return [
        (baris.tahun, float(baris.nilai))
        for baris in repo_nilai.seri(session, id_indikator, KODE_PROVINSI, JenisNilai.REALISASI)
        if baris.nilai is not None
    ]


@router.get("/analitik/selisih/{id_indikator}")
def selisih_tahunan(id_indikator: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    indikator = repo_indikator.ambil(session, id_indikator)
    arah = indikator.arah_baik if indikator else None
    return {
        "id_indikator": id_indikator,
        "arah_baik": arah,
        "data": svc.selisih_tahunan(_seri_realisasi(session, id_indikator), arah),
    }


@router.get("/analitik/peringkat")
def peringkat(session: Session = Depends(get_session)) -> dict[str, Any]:
    hasil: list[dict[str, Any]] = []
    for indikator in repo_indikator.daftar_arah_terverifikasi(session):
        seri = _seri_realisasi(session, indikator.id_indikator)
        if len(seri) < 2:
            continue
        (tahun_awal, nilai_awal), (tahun_akhir, nilai_akhir) = seri[-2], seri[-1]
        perubahan = nilai_akhir - nilai_awal
        hasil.append(
            {
                "id_indikator": indikator.id_indikator,
                "nama_indikator": indikator.nama_indikator,
                "arah_baik": indikator.arah_baik,
                "tahun_awal": tahun_awal,
                "tahun_akhir": tahun_akhir,
                "perubahan": perubahan,
                "skor_perbaikan": svc.skor_perbaikan(perubahan, indikator.arah_baik),
            }
        )
    hasil.sort(key=lambda x: float(x["skor_perbaikan"]), reverse=True)
    return {
        "perbaikan_terbesar": hasil[:BATAS_PERINGKAT],
        "pemburukan_terbesar": list(reversed(hasil[-BATAS_PERINGKAT:])),
    }


@router.get("/analitik/gap/{id_indikator}")
def gap(id_indikator: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    indikator = repo_indikator.ambil(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan")

    realisasi = _seri_realisasi(session, id_indikator)
    if not realisasi:
        return {"status": "BELUM_ADA_DATA", "disclaimer": svc.DISCLAIMER_PROYEKSI}

    target = {
        baris.tahun: baris.nilai
        for baris in repo_nilai.seri(session, id_indikator, KODE_PROVINSI, JenisNilai.TARGET)
        if baris.tahun in (svc.TAHUN_TARGET_ANTARA, svc.TAHUN_TARGET_AKHIR) and baris.nilai is not None
    }
    tahun_terakhir, nilai_terakhir = realisasi[-1]
    target_2029 = target.get(svc.TAHUN_TARGET_ANTARA)
    target_2045 = target.get(svc.TAHUN_TARGET_AKHIR)

    historis = svc.laju_historis(realisasi)
    dibutuhkan = svc.laju_dibutuhkan(nilai_terakhir, tahun_terakhir, target_2045, svc.TAHUN_TARGET_AKHIR)
    return {
        "id_indikator": id_indikator,
        "realisasi_terakhir": {"tahun": tahun_terakhir, "nilai": nilai_terakhir},
        "target_2029": target_2029,
        "target_2045": target_2045,
        "gap_2029": None if target_2029 is None else target_2029 - nilai_terakhir,
        "gap_2045": None if target_2045 is None else target_2045 - nilai_terakhir,
        "laju_historis": historis,
        "required_run_rate": dibutuhkan,
        "status_jalur": svc.status_jalur(
            historis, dibutuhkan, indikator.arah_baik, bool(indikator.arah_baik_terverifikasi)
        ),
        "disclaimer": svc.DISCLAIMER_PROYEKSI,
    }


@router.get("/analitik/multi")
def multi(ids: list[str] = Query(...), session: Session = Depends(get_session)) -> dict[str, Any]:
    if len(ids) > MAKSIMUM_INDIKATOR_MULTI:
        raise HTTPException(422, "Maksimal empat indikator")

    data = []
    for id_indikator in ids:
        indikator = repo_indikator.ambil(session, id_indikator)
        if indikator is None:
            raise HTTPException(404, f"Indikator tidak ditemukan: {id_indikator}")
        data.append(
            {
                "id_indikator": id_indikator,
                "nama": indikator.nama_indikator,
                "seri": [
                    {"tahun": baris.tahun, "jenis": baris.jenis, "nilai": baris.nilai}
                    for baris in repo_nilai.seri(session, id_indikator, KODE_PROVINSI)
                    if baris.nilai is not None
                ],
            }
        )
    return {"data": data}


@router.get("/analitik/korelasi")
def korelasi(x: str, y: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    hasil = svc.korelasi(
        dict(_seri_realisasi(session, x)),
        dict(_seri_realisasi(session, y)),
    )
    return {
        "n": hasil.n,
        "pearson": hasil.pearson,
        "data": hasil.titik,
        "peringatan": hasil.peringatan,
    }
