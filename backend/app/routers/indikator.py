"""Endpoint daftar indikator, detail, metadata, dan koreksi arah baik."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlalchemy.orm import Session

from ..deps import get_session, wajib_peran
from ..models import KODE_PROVINSI, ArahBaik, JenisNilai, Peran
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..repositories import tata_kelola as repo_tata_kelola
from ..repositories.pengguna import ProfilPengguna
from ..services import capaian as svc_capaian

router = APIRouter(prefix="/api/v1", tags=["indikator"])

# Kolom yang boleh keluar lewat daftar publik. Nama PIC perorangan dan status
# ketersediaan sengaja tidak termasuk.
FIELD_PUBLIK = repo_indikator.FIELD_PUBLIK

# Kompatibilitas kontrak: kolom basis data dibakukan menjadi `opd_pengampu`,
# tetapi frontend lama masih membaca `opd_penanggung_jawab`. Pemetaan ini
# dilepas bersama penyelarasan frontend di Fase 6.
NAMA_LAMA = {"opd_pengampu": "opd_penanggung_jawab"}


def ringkas(indikator: Any) -> dict[str, Any]:
    return {NAMA_LAMA.get(f, f): getattr(indikator, f) for f in FIELD_PUBLIK}


@router.get("/indikator")
def daftar_indikator(
    q: str | None = None,
    kategori: list[str] | None = Query(None),
    kelompok: list[str] | None = Query(None),
    tim: list[str] | None = Query(None),
    metadata: list[str] | None = Query(None),
    sort: str = "id_indikator",
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    daftar, total = repo_indikator.cari(
        session,
        q=q,
        kategori=kategori,
        kelompok=kelompok,
        tim=tim,
        status_metadata=metadata,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    return {
        "data": [ringkas(item) for item in daftar],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def muatan_capaian(session: Session, indikator: Any, wilayah_kode: str = KODE_PROVINSI) -> dict[str, Any]:
    """Ringkasan capaian satu indikator untuk satu wilayah."""
    seri = repo_nilai.seri(session, indikator.id_indikator, wilayah_kode)
    realisasi = [baris for baris in seri if baris.jenis == JenisNilai.REALISASI and baris.nilai is not None]
    terakhir = max(realisasi, key=lambda baris: baris.tahun) if realisasi else None
    target_setahun = next(
        (
            baris
            for baris in seri
            if terakhir
            and baris.jenis == JenisNilai.TARGET
            and baris.tahun == terakhir.tahun
            and baris.nilai is not None
        ),
        None,
    )
    hasil = svc_capaian.capaian(
        terakhir.nilai if terakhir else None,
        target_setahun.nilai if target_setahun else None,
        indikator.arah_baik,
        bool(indikator.arah_baik_terverifikasi),
    )
    return {
        "id_indikator": indikator.id_indikator,
        "nama_indikator": indikator.nama_indikator,
        "kategori": indikator.kategori,
        "kelompok": indikator.kelompok,
        "arah_pembangunan": indikator.arah_pembangunan,
        "tim_pjk": indikator.tim_pjk,
        "satuan": indikator.satuan,
        "arah_baik": indikator.arah_baik,
        "arah_baik_terverifikasi": indikator.arah_baik_terverifikasi,
        "nilai_terakhir": terakhir.nilai if terakhir else None,
        "tahun_terakhir_realisasi": terakhir.tahun if terakhir else None,
        "target_tahun_sama": target_setahun.nilai if target_setahun else None,
        "persentase_capaian": hasil.persentase,
        "status_capaian": hasil.status,
        "tren": [{"tahun": baris.tahun, "nilai": baris.nilai} for baris in realisasi],
    }


@router.get("/indikator/{id_indikator}/detail")
def detail_indikator(id_indikator: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    indikator = repo_indikator.ambil(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan")

    muatan = muatan_capaian(session, indikator)
    muatan["nilai"] = [
        {
            "tahun": baris.tahun,
            "jenis": baris.jenis,
            "nilai": baris.nilai,
            # Nama lama dipertahankan sampai frontend diselaraskan (Fase 6).
            "sumber_sheet": baris.sumber,
        }
        for baris in repo_nilai.seri(session, id_indikator, KODE_PROVINSI)
    ]
    metadata = repo_indikator.ambil_metadata(session, id_indikator)
    muatan["metadata"] = (
        None
        if metadata is None
        else {
            "definisi": metadata.definisi,
            "rumus_mentah": metadata.rumus_mentah,
            "interpretasi": metadata.interpretasi,
            "sumber_data": metadata.sumber_data,
            "frekuensi": metadata.frekuensi,
            "halaman_sumber": metadata.halaman_sumber,
            "sumber_metadata": metadata.sumber_metadata,
            "perlu_verifikasi_manual": metadata.perlu_verifikasi_manual,
        }
    )
    return muatan


@router.get("/beranda-indikator/{id_indikator}/metadata")
def metadata_indikator(id_indikator: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    indikator = repo_indikator.ambil_terverifikasi(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan")

    metadata = repo_indikator.ambil_metadata(session, id_indikator)
    isi_metadata = (
        None
        if metadata is None
        else {
            "definisi": metadata.definisi,
            "rumus_mentah": metadata.rumus_mentah,
            "rumus_latex": metadata.rumus_latex,
            "interpretasi": metadata.interpretasi,
            "sumber_data": metadata.sumber_data,
            "frekuensi": metadata.frekuensi,
            "status_metadata": metadata.status_metadata,
            "sumber_metadata": metadata.sumber_metadata,
        }
    )
    # "Tersedia" berarti ada isi yang bermakna, bukan sekadar barisnya ada.
    tersedia = bool(
        isi_metadata
        and any(
            isi_metadata.get(kunci)
            for kunci in ("definisi", "rumus_mentah", "interpretasi", "sumber_data", "frekuensi")
        )
    )
    return {
        "id_indikator": indikator.id_indikator,
        "kategori": indikator.kategori,
        "kode_indikator": indikator.kode_indikator,
        "nama_indikator": indikator.nama_indikator,
        "kelompok": indikator.kelompok,
        "arah_pembangunan": indikator.arah_pembangunan,
        "satuan": indikator.satuan,
        "opd_pengampu": indikator.opd_pengampu,
        "status_ketersediaan": indikator.status_ketersediaan,
        "periode_data": indikator.periode_data,
        "metadata": isi_metadata,
        "metadata_tersedia": tersedia,
        "nilai": [
            {
                "tahun": baris.tahun,
                "jenis": baris.jenis,
                "nilai": baris.nilai,
                "nilai_teks": baris.nilai_teks,
                "satuan_catatan": baris.satuan_catatan,
            }
            for baris in repo_nilai.seri_lengkap(session, id_indikator, KODE_PROVINSI)
        ],
    }


@router.put("/arah-baik/{id_indikator}")
def koreksi_arah_baik(
    id_indikator: str,
    arah_baik: str = Form(...),
    pengguna: ProfilPengguna = Depends(wajib_peran(Peran.ADMIN)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    if arah_baik not in tuple(ArahBaik):
        raise HTTPException(422, "Arah harus NAIK atau TURUN")
    indikator = repo_indikator.ambil(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan")

    lama = repo_indikator.ubah_arah_baik(indikator, arah_baik)
    repo_tata_kelola.catat_perubahan(
        session,
        pengguna_id=pengguna.id,
        id_indikator=id_indikator,
        field="arah_baik",
        nilai_lama=lama,
        nilai_baru=arah_baik,
        sumber_perubahan="koreksi_admin",
    )
    session.commit()
    return {"status": "ok", "id_indikator": id_indikator, "arah_baik": arah_baik}
