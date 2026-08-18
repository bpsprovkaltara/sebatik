"""Menegakkan aturan pemisahan lapisan sebagai tes, bukan sekadar konvensi.

Kriteria selesai backend.md §8: router tidak berisi SQL atau perhitungan, tidak
ada `text("...")` di `routers/` maupun `services/`, dan arah ketergantungan
selalu routers -> services -> repositories -> models.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

AKAR = Path(__file__).resolve().parents[2] / "backend" / "app"
ROUTERS = sorted((AKAR / "routers").glob("*.py"))
SERVICES = sorted((AKAR / "services").glob("*.py"))
REPOSITORIES = sorted((AKAR / "repositories").glob("*.py"))
MODELS = sorted((AKAR / "models").glob("*.py"))


def _impor(path: Path) -> set[str]:
    pohon = ast.parse(path.read_text(encoding="utf-8"))
    hasil: set[str] = set()
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.ImportFrom) and simpul.module:
            hasil.add(simpul.module)
        elif isinstance(simpul, ast.Import):
            hasil.update(alias.name for alias in simpul.names)
    return hasil


def _panggilan(path: Path) -> set[str]:
    pohon = ast.parse(path.read_text(encoding="utf-8"))
    hasil: set[str] = set()
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.Call):
            fungsi = simpul.func
            if isinstance(fungsi, ast.Name):
                hasil.add(fungsi.id)
            elif isinstance(fungsi, ast.Attribute):
                hasil.add(fungsi.attr)
    return hasil


def test_ada_router_dan_service_untuk_diperiksa():
    """Menjaga tes ini tidak lulus hampa bila struktur direktori berubah."""
    assert len(ROUTERS) > 5
    assert len(SERVICES) > 5
    assert len(REPOSITORIES) > 3


@pytest.mark.parametrize("berkas", ROUTERS + SERVICES, ids=lambda p: p.name)
def test_tidak_ada_sql_mentah_di_router_dan_service(berkas: Path):
    """`text("SELECT ...")` hanya boleh hidup di repositories/ dan migrasi."""
    assert "text(" not in berkas.read_text(encoding="utf-8"), (
        f"{berkas.name} memakai SQL mentah; pindahkan query ke repositories/"
    )


@pytest.mark.parametrize("berkas", ROUTERS, ids=lambda p: p.name)
def test_router_tidak_menyusun_query_sendiri(berkas: Path):
    """Router tidak boleh memanggil select()/insert() — itu tugas repository."""
    terlarang = {"select", "insert", "update", "delete", "execute"} & _panggilan(berkas)
    assert not terlarang, f"{berkas.name} menyusun query sendiri: {sorted(terlarang)}"


@pytest.mark.parametrize("berkas", SERVICES + REPOSITORIES + MODELS, ids=lambda p: p.name)
def test_lapisan_dalam_tidak_mengimpor_router(berkas: Path):
    """Arah ketergantungan tidak boleh berbalik."""
    melanggar = {m for m in _impor(berkas) if "routers" in m}
    assert not melanggar, f"{berkas.name} mengimpor routers: {sorted(melanggar)}"


@pytest.mark.parametrize("berkas", REPOSITORIES + MODELS, ids=lambda p: p.name)
def test_repository_dan_model_tidak_mengimpor_service(berkas: Path):
    melanggar = {m for m in _impor(berkas) if "services" in m}
    assert not melanggar, f"{berkas.name} mengimpor services: {sorted(melanggar)}"


@pytest.mark.parametrize("berkas", MODELS, ids=lambda p: p.name)
def test_model_tidak_mengimpor_repository(berkas: Path):
    melanggar = {m for m in _impor(berkas) if "repositories" in m}
    assert not melanggar, f"{berkas.name} mengimpor repositories: {sorted(melanggar)}"


@pytest.mark.parametrize("berkas", SERVICES, ids=lambda p: p.name)
def test_service_tidak_mengimpor_fastapi(berkas: Path):
    """Service harus dapat diuji tanpa HTTP."""
    melanggar = {m for m in _impor(berkas) if m.split(".")[0] in {"fastapi", "starlette"}}
    assert not melanggar, f"{berkas.name} mengimpor {sorted(melanggar)}"


def test_modul_lama_sudah_dihapus():
    """features_api.py, models_legacy.py, dan master_seed.py tidak boleh kembali."""
    for nama in ("features_api.py", "models_legacy.py", "master_seed.py"):
        assert not (AKAR / nama).exists(), f"{nama} seharusnya sudah dihapus"


def test_database_tidak_punya_efek_samping_impor():
    """Migrasi dan seed tidak boleh berjalan saat modul dimuat (backend.md §7)."""
    isi = (AKAR / "database.py").read_text(encoding="utf-8")
    for terlarang in ("migrate_governance", "seed_verified_master"):
        assert terlarang not in isi, f"database.py masih memanggil {terlarang} saat impor"
