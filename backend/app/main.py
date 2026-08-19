"""Factory aplikasi FastAPI SEBATIK.

Tidak ada efek samping saat impor selain membuat objek aplikasi: skema dikelola
Alembic dan data awal diisi migrasi/skrip terpisah, bukan saat modul dimuat.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .middleware import HeaderKeamanan
from .routers import SEMUA_ROUTER

log = logging.getLogger("sebatik")

JUDUL = "API SEBATIK"
DESKRIPSI = "API Dasbor Pemantauan Capaian Data Indikator ISV-IUP BPS Provinsi Kalimantan Utara"

BUILD_FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def create_app() -> FastAPI:
    settings.validasi_produksi()

    app = FastAPI(
        title=JUDUL,
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        description=DESKRIPSI,
    )
    app.add_middleware(HeaderKeamanan, aktifkan_hsts=settings.is_production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in SEMUA_ROUTER:
        app.include_router(router)

    @app.exception_handler(Exception)
    async def galat_tak_terduga(request: Request, exc: Exception) -> JSONResponse:
        """Catat stack trace ke log, kembalikan 500 tanpa membocorkan detail."""
        log.exception("Galat tak tertangani pada %s %s", request.method, request.url.path)
        return JSONResponse({"detail": "Terjadi kesalahan pada server"}, status_code=500)

    # Build frontend dilayani proses yang sama saat produksi. Dipasang terakhir
    # agar tidak menaungi rute /api.
    if BUILD_FRONTEND.exists():
        app.mount("/", StaticFiles(directory=BUILD_FRONTEND, html=True), name="frontend")

    return app


app = create_app()
