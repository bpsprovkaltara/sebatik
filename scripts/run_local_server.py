"""Fallback launcher when the original project virtualenv is unavailable."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PACKAGES = PROJECT_ROOT / ".runtime-packages"
sys.path.insert(0, str(PROJECT_ROOT))
if LOCAL_PACKAGES.exists():
    sys.path.insert(0, str(LOCAL_PACKAGES))

import uvicorn  # noqa: E402  (diimpor setelah sys.path disiapkan)

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000)
