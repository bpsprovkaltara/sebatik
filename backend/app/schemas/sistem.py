"""Skema endpoint sistem."""

from __future__ import annotations

from pydantic import BaseModel


class KesehatanResponse(BaseModel):
    status: str
