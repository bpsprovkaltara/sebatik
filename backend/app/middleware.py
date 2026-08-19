"""Middleware header keamanan HTTP."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Header yang berlaku untuk seluruh respons.
HEADER_KEAMANAN: dict[str, str] = {
    # Cegah peramban menebak tipe konten; bukti dukung diunggah pengguna.
    "X-Content-Type-Options": "nosniff",
    # Aplikasi tidak dirancang untuk ditanam di iframe pihak lain.
    "X-Frame-Options": "DENY",
    # Jangan bocorkan path internal ke situs luar saat pengguna mengeklik tautan.
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
}

# HSTS hanya bermakna pada koneksi HTTPS; memasangnya di HTTP diabaikan peramban
# dan berisiko mengunci pengembangan lokal.
HSTS = "max-age=31536000; includeSubDomains"


class HeaderKeamanan(BaseHTTPMiddleware):
    def __init__(self, app, *, aktifkan_hsts: bool = False) -> None:
        super().__init__(app)
        self.aktifkan_hsts = aktifkan_hsts

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        for nama, nilai in HEADER_KEAMANAN.items():
            response.headers.setdefault(nama, nilai)
        if self.aktifkan_hsts and request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", HSTS)
        return response
