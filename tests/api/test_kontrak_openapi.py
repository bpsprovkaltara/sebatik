"""Setiap endpoint JSON harus punya skema respons di OpenAPI.

backend.md §4: "Setiap endpoint memakai skema respons eksplisit (atau minimal
`response_model`) agar kontrak JSON terdokumentasi di OpenAPI." Tanpa tes ini,
endpoint baru mudah lolos tanpa skema dan kontraknya kembali tersirat.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

# Endpoint yang memang tidak mengirim JSON: unduhan berkas dan berkas bukti.
TANPA_SKEMA_JSON = {
    ("/api/v1/ekspor.csv", "get"),
    ("/api/v1/ekspor.xlsx", "get"),
    ("/api/v1/indikator/{id_indikator}/unduh.csv", "get"),
    ("/api/v1/download/paket.zip", "get"),
    ("/api/v1/admin/usulan/{usulan_id}/bukti/{bukti_id}", "get"),
}


def _operasi(client: TestClient) -> list[tuple[str, str, dict]]:
    dokumen = client.get("/api/openapi.json").json()
    return [
        (jalur, metode, operasi)
        for jalur, isi in dokumen["paths"].items()
        for metode, operasi in isi.items()
        if metode in {"get", "post", "put", "patch", "delete"}
    ]


def test_openapi_memuat_semua_endpoint(client: TestClient):
    """Menjaga tes ini tidak lulus hampa bila dokumen OpenAPI kosong."""
    assert len(_operasi(client)) > 30


def test_setiap_endpoint_json_punya_skema_respons(client: TestClient):
    tanpa_skema = []
    for jalur, metode, operasi in _operasi(client):
        if (jalur, metode) in TANPA_SKEMA_JSON:
            continue
        isi = operasi.get("responses", {}).get("200", {}).get("content", {})
        skema = isi.get("application/json", {}).get("schema", {})
        # `{}` berarti "objek apa saja" — itu sama dengan tidak berkontrak.
        if not skema or skema == {"title": "Response"} or "$ref" not in str(skema):
            tanpa_skema.append(f"{metode.upper()} {jalur}")
    assert not tanpa_skema, "endpoint tanpa response_model: " + ", ".join(sorted(tanpa_skema))


@pytest.mark.parametrize(
    "jalur",
    [
        "/api/v1/beranda",
        "/api/v1/indikator",
        "/api/v1/capaian",
        "/api/v1/insight",
        "/api/v1/validitas",
        "/api/v1/auth/login",
    ],
)
def test_skema_utama_terdaftar_di_komponen(client: TestClient, jalur: str):
    """Skema respons harus berupa komponen bernama, bukan objek anonim."""
    dokumen = client.get("/api/openapi.json").json()
    metode = "post" if jalur.endswith("login") else "get"
    skema = dokumen["paths"][jalur][metode]["responses"]["200"]["content"]["application/json"]["schema"]
    assert skema["$ref"].startswith("#/components/schemas/")
