"""Endpoint ekspor: CSV, XLSX, unduhan per indikator, dan paket ZIP."""

from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from ..deps import get_session
from ..models import KODE_PROVINSI
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..services import ekspor as svc

router = APIRouter(prefix="/api/v1", tags=["ekspor"])

TIPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _lampiran(nama_berkas: str) -> dict[str, str]:
    return {"Content-Disposition": f"attachment; filename={nama_berkas}"}


@router.get("/ekspor.csv")
def ekspor_csv(session: Session = Depends(get_session)) -> Response:
    isi = svc.csv_indikator(repo_indikator.daftar_ekspor(session))
    return Response(
        isi,
        media_type="text/csv; charset=utf-8",
        headers=_lampiran("indikator-sebatik.csv"),
    )


@router.get("/ekspor.xlsx")
def ekspor_xlsx(session: Session = Depends(get_session)) -> StreamingResponse:
    isi = svc.xlsx_indikator(repo_indikator.daftar_ekspor(session))
    return StreamingResponse(BytesIO(isi), media_type=TIPE_XLSX, headers=_lampiran("indikator-sebatik.xlsx"))


@router.get("/indikator/{id_indikator}/unduh.csv")
def unduh_indikator(id_indikator: str, session: Session = Depends(get_session)) -> Response:
    indikator = repo_indikator.ambil(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan")
    isi = svc.csv_nilai_indikator(
        id_indikator,
        indikator.nama_indikator,
        repo_nilai.seri(session, id_indikator, KODE_PROVINSI),
    )
    return Response(isi, media_type="text/csv", headers=_lampiran(f"{id_indikator}.csv"))


@router.get("/download/paket.zip")
def unduh_paket(session: Session = Depends(get_session)) -> StreamingResponse:
    daftar = repo_indikator.daftar_ekspor(session)
    katalog = []
    tabel_indikator = []
    for item in daftar:
        metadata = repo_indikator.ambil_metadata(session, item.id_indikator)
        katalog.append(
            {
                "id_indikator": item.id_indikator,
                "nama_indikator": item.nama_indikator,
                "definisi": metadata.definisi if metadata else None,
                "rumus_mentah": metadata.rumus_mentah if metadata else None,
                "interpretasi": metadata.interpretasi if metadata else None,
                "sumber_data": metadata.sumber_data if metadata else None,
                "frekuensi": metadata.frekuensi if metadata else None,
                "sumber_metadata": metadata.sumber_metadata if metadata else None,
            }
        )
        tabel_indikator.append(
            {
                "id_indikator": item.id_indikator,
                "kategori": item.kategori,
                "nomor": item.nomor,
                "kode_indikator": item.kode_indikator,
                "nama_indikator": item.nama_indikator,
                "kelompok": item.kelompok,
                "satuan": item.satuan,
                "opd_pengampu": item.opd_pengampu,
                "tim_pjk": item.tim_pjk,
                "status_metadata": item.status_metadata,
                "tahun_terakhir": item.tahun_terakhir,
                "is_proxy": item.is_proxy,
                "arah_baik": item.arah_baik,
            }
        )

    tabel_nilai = [
        {
            "id_indikator": baris.id_indikator,
            "wilayah_kode": baris.wilayah_kode,
            "tahun": baris.tahun,
            "jenis": baris.jenis,
            "periode": baris.periode,
            "nilai": baris.nilai,
            "nilai_teks": baris.nilai_teks,
            "sumber": baris.sumber,
        }
        for item in daftar
        for baris in repo_nilai.seri_lengkap(session, item.id_indikator, KODE_PROVINSI)
    ]
    tabel_metadata = [{k: v for k, v in baris.items() if k != "nama_indikator"} for baris in katalog]

    isi = svc.zip_paket(
        {
            "indikator": tabel_indikator,
            "nilai_indikator": tabel_nilai,
            "metadata_indikator": tabel_metadata,
        },
        katalog,
    )
    return StreamingResponse(BytesIO(isi), media_type="application/zip", headers=_lampiran("paket-data-sebatik.zip"))
