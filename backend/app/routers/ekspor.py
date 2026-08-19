"""Endpoint ekspor: CSV, XLSX, unduhan per indikator, dan paket ZIP."""

from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from ..deps import get_session
from ..repositories import indikator as repo_indikator
from ..services import ekspor as svc

router = APIRouter(prefix="/api/v1", tags=["ekspor"])

TIPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _lampiran(nama_berkas: str) -> dict[str, str]:
    return {"Content-Disposition": f"attachment; filename={nama_berkas}"}


@router.get("/ekspor.csv")
def ekspor_csv(session: Session = Depends(get_session)) -> Response:
    return Response(
        svc.csv_semua_indikator(session),
        media_type="text/csv; charset=utf-8",
        headers=_lampiran("indikator-sebatik.csv"),
    )


@router.get("/ekspor.xlsx")
def ekspor_xlsx(session: Session = Depends(get_session)) -> StreamingResponse:
    isi = svc.xlsx_semua_indikator(session)
    return StreamingResponse(BytesIO(isi), media_type=TIPE_XLSX, headers=_lampiran("indikator-sebatik.xlsx"))


@router.get("/indikator/{id_indikator}/unduh.csv")
def unduh_indikator(id_indikator: str, session: Session = Depends(get_session)) -> Response:
    indikator = repo_indikator.ambil(session, id_indikator)
    if indikator is None:
        raise HTTPException(404, "Indikator tidak ditemukan")
    isi = svc.csv_satu_indikator(session, indikator)
    return Response(isi, media_type="text/csv", headers=_lampiran(f"{id_indikator}.csv"))


@router.get("/download/paket.zip")
def unduh_paket(session: Session = Depends(get_session)) -> StreamingResponse:
    isi = svc.paket_lengkap(session)
    return StreamingResponse(BytesIO(isi), media_type="application/zip", headers=_lampiran("paket-data-sebatik.zip"))
