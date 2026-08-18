"""Basis deklaratif ORM.

Dipisah dari `database.py` supaya `models/` dapat diimpor tanpa menyeret
pembuatan engine — penting agar Alembic dan tes unit tidak menyentuh basis data
saat mengimpor model.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
