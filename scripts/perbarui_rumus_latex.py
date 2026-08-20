"""Isi kolom rumus LaTeX metadata indikator dari berkas turunan Buku 1.

Kenapa perlu skrip tersendiri, terpisah dari `perbarui_metadata_master.py`:
workbook master mengambil metadata apa adanya dari hasil ekstraksi PDF, dan
untuk kolom rumus hasilnya tidak terpakai. Buku 1 menyusun rumusnya memakai
font matematis dengan peta karakter tidak baku, sehingga pecahan terurai jadi
baris terpisah dan sebagian huruf tertukar. Bentuk LaTeX-nya disusun ulang
sekali di `data/processed/rumus_latex_buku1.json`, lalu skrip ini memasangnya.

Teks mentah hasil ekstraksi TIDAK dihapus. Ia tetap tersimpan di
`rumus_mentah` sebagai jejak audit terhadap dokumen sumber; yang berubah hanya
kolom yang dipakai untuk menampilkan rumus.

Jalankan::

    python -m scripts.perbarui_rumus_latex
    python -m scripts.perbarui_rumus_latex --periksa     # tanpa menulis
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Skrip dijalankan langsung (`python scripts/...`), jadi akar repo belum ada di
# jalur impor — sama seperti skrip tetangganya di folder ini.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select  # noqa: E402

from backend.app.database import SessionLocal  # noqa: E402
from backend.app.models import MetadataIndikator  # noqa: E402

SUMBER_BAWAAN = Path("data/processed/rumus_latex_buku1.json")

# Penanda `asal` yang berarti rumusnya benar-benar tercetak sebagai rumus di
# Buku 1. Selain itu — bentuk yang disusun dari kalimat definisi karena rumus
# aslinya berupa gambar — ditandai supaya verifikator memeriksanya lebih dulu.
ASAL_TERSALIN = "buku1"


def muat(path: Path) -> dict[str, dict]:
    berkas = json.loads(path.read_text(encoding="utf-8"))
    return berkas["indikator"]


def jalankan(path: Path, *, tulis: bool = True) -> dict[str, int]:
    isi = muat(path)
    hitung = {"cocok": 0, "berumus": 0, "tanpa_rumus": 0, "perlu_verifikasi": 0, "tak_dikenal": 0}

    with SessionLocal() as session:
        baris = {
            m.id_indikator: m
            for m in session.scalars(
                select(MetadataIndikator).where(MetadataIndikator.id_indikator.in_(isi))
            )
        }
        hitung["tak_dikenal"] = len(set(isi) - set(baris))

        for id_indikator, data in isi.items():
            metadata = baris.get(id_indikator)
            if metadata is None:
                continue
            hitung["cocok"] += 1

            latex = data.get("latex")
            perlu_verifikasi = bool(latex) and data.get("asal") != ASAL_TERSALIN

            metadata.rumus_latex = latex
            # Kolom `rumus` menampung keterangan notasi — daftar "simbol =
            # arti" yang di buku tercetak persis di bawah rumusnya. Ia disimpan
            # sebagai baris-baris terpisah supaya lapisan tampilan tidak perlu
            # menebak pemisahnya.
            keterangan = list(data.get("keterangan") or [])
            if data.get("catatan"):
                keterangan.append(f"Catatan: {data['catatan']}")
            metadata.rumus = "\n".join(keterangan) or None
            # Halaman hanya diisi bila masih kosong: 21 baris sudah membawa
            # rujukan halamannya sendiri dari muatan awal, dan menimpanya
            # berarti membuang keterangan yang belum tentu salah.
            if not metadata.halaman_sumber and data.get("halaman"):
                metadata.halaman_sumber = data["halaman"]
            if perlu_verifikasi:
                metadata.perlu_verifikasi_manual = True

            hitung["berumus" if latex else "tanpa_rumus"] += 1
            hitung["perlu_verifikasi"] += int(perlu_verifikasi)

        if tulis:
            session.commit()
        else:
            session.rollback()

    return hitung


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sumber", type=Path, default=SUMBER_BAWAAN)
    parser.add_argument("--periksa", action="store_true", help="jalankan tanpa menyimpan perubahan")
    args = parser.parse_args()

    hasil = jalankan(args.sumber, tulis=not args.periksa)
    awalan = "[periksa] " if args.periksa else ""
    print(
        f"{awalan}{hasil['cocok']} indikator diproses — "
        f"{hasil['berumus']} berumus LaTeX, {hasil['tanpa_rumus']} tanpa rumus di Buku 1, "
        f"{hasil['perlu_verifikasi']} ditandai perlu verifikasi manual."
    )
    if hasil["tak_dikenal"]:
        print(f"Peringatan: {hasil['tak_dikenal']} entri tidak punya baris metadata di basis data.")
