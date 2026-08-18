from __future__ import annotations

import csv
from io import BytesIO, StringIO
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openpyxl import Workbook
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .features_api import router as features_router
from .models import Indikator

app = FastAPI(title="API SEBATIK", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json", description="API Dasbor Pemantauan Capaian Data Indikator ISV-IUP BPS Provinsi Kalimantan Utara")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(features_router)

PUBLIC_FIELDS = ["id_indikator", "nama_indikator", "kategori", "kelompok", "satuan", "tim_pjk", "opd_penanggung_jawab", "status_metadata", "tahun_terakhir", "is_proxy"]


def serialize(row: Indikator):
    return {field: getattr(row, field) for field in PUBLIC_FIELDS}


def filters(stmt, q=None, kategori=None, kelompok=None, tim=None, metadata=None):
    if q: stmt = stmt.where(Indikator.nama_indikator.ilike(f"%{q}%"))
    if kategori: stmt = stmt.where(Indikator.kategori.in_(kategori))
    if kelompok: stmt = stmt.where(Indikator.kelompok.in_(kelompok))
    if tim: stmt = stmt.where(Indikator.tim_pjk.in_(tim))
    if metadata: stmt = stmt.where(Indikator.status_metadata.in_(metadata))
    return stmt


@app.get("/api/v1/health")
def health(): return {"status": "ok"}


@app.get("/api/v1/indikator")
def indicators(q: str | None=None, kategori: list[str] | None=Query(None), kelompok: list[str] | None=Query(None), tim: list[str] | None=Query(None), metadata: list[str] | None=Query(None), sort: str="id_indikator", order: Literal["asc","desc"]="asc", page: int=Query(1,ge=1), page_size: int=Query(25,ge=1,le=200), db: Session=Depends(get_db)):
    base = filters(select(Indikator), q, kategori, kelompok, tim, metadata)
    count_stmt = filters(select(func.count()).select_from(Indikator), q, kategori, kelompok, tim, metadata)
    allowed = {x: getattr(Indikator,x) for x in PUBLIC_FIELDS if x != "is_proxy"}
    col = allowed.get(sort, Indikator.id_indikator)
    rows = db.scalars(base.order_by(desc(col) if order=="desc" else asc(col)).offset((page-1)*page_size).limit(page_size)).all()
    return {"data": [serialize(r) for r in rows], "total": db.scalar(count_stmt) or 0, "page": page, "page_size": page_size}


def export_rows(db):
    return db.scalars(select(Indikator).order_by(Indikator.kategori.desc(), Indikator.nomor)).all()


EXPORT_HEADERS = {"id_indikator":"ID Indikator","nama_indikator":"Nama Indikator","kategori":"Kategori","kelompok":"Kelompok Indikator","satuan":"Satuan","tim_pjk":"Tim PJK","opd_penanggung_jawab":"OPD Pengampu","status_metadata":"Status Metadata","tahun_terakhir":"Tahun Terakhir Data","is_proxy":"Menggunakan Proxy"}


@app.get("/api/v1/ekspor.csv")
def export_csv(db: Session=Depends(get_db)):
    output=StringIO(); writer=csv.DictWriter(output,fieldnames=list(EXPORT_HEADERS.values())); writer.writeheader()
    for row in export_rows(db): writer.writerow({label:("Ya" if field=="is_proxy" and getattr(row,field) else "Tidak" if field=="is_proxy" else getattr(row,field)) for field,label in EXPORT_HEADERS.items()})
    return Response("\ufeff"+output.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition":"attachment; filename=indikator-sebatik.csv"})


@app.get("/api/v1/ekspor.xlsx")
def export_xlsx(db: Session=Depends(get_db)):
    wb=Workbook(); ws=wb.active; ws.title="Indikator"; ws.append(list(EXPORT_HEADERS.values()))
    for row in export_rows(db): ws.append(["Ya" if field=="is_proxy" and getattr(row,field) else "Tidak" if field=="is_proxy" else getattr(row,field) for field in EXPORT_HEADERS])
    ws.freeze_panes="A2"; ws.auto_filter.ref=ws.dimensions
    for cell in ws[1]: cell.font=cell.font.copy(bold=True)
    stream=BytesIO(); wb.save(stream); stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition":"attachment; filename=indikator-sebatik.xlsx"})


# Build frontend dapat dilayani oleh proses FastAPI yang sama saat produksi.

frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
