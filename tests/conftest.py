r"""Konfigurasi bersama pytest.

`tmp_path` bawaan menulis ke `%TEMP%\pytest-of-<user>` yang pada sebagian mesin
Windows tidak dapat dibuat (akses ditolak). Mengarahkan akar direktori sementara
ke `tmp/` di dalam repo membuat tes ETL dapat berjalan di mana pun.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = REPO_ROOT / "tmp" / "pytest"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(TEMP_ROOT))
