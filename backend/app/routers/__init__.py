"""Lapisan HTTP.

Router hanya menerima parameter, memanggil dependency, memanggil service atau
repository, lalu mengembalikan respons. Tidak berisi SQL, perhitungan, maupun
aturan bisnis (arsitektur-target.md §2).
"""

from fastapi import APIRouter

from . import (
    admin,
    analitik,
    auth,
    beranda,
    capaian,
    ekspor,
    explorer,
    health,
    indikator,
    insight,
    unggahan,
    usulan,
    validitas,
    wilayah,
)

# Urutan pendaftaran menentukan pencocokan rute: modul dengan path statis
# didaftarkan sebelum yang memakai parameter jalur.
SEMUA_ROUTER: tuple[APIRouter, ...] = (
    health.router,
    wilayah.router,
    beranda.router,
    explorer.router,
    capaian.router,
    insight.router,
    validitas.router,
    analitik.router,
    ekspor.router,
    indikator.router,
    auth.router,
    admin.router,
    usulan.router,
    unggahan.router,
)

__all__ = ["SEMUA_ROUTER"]
