"""Perintah administratif SEBATIK.

Menggantikan seed otomatis yang dulu berjalan saat modul diimpor. Sekarang
pembuatan akun awal adalah tindakan eksplisit yang dijalankan operator saat
pemasangan::

    python -m backend.app.cli seed
    python -m backend.app.cli seed --tampilkan-sandi
"""

from __future__ import annotations

import argparse
import secrets
import string
import sys

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import KODE_PROVINSI, Peran, Wilayah
from .repositories import pengguna as repo_pengguna
from .repositories import wilayah as repo_wilayah
from .security import hash_password

# Panjang sandi acak yang dibuat saat seed. Jauh di atas kebijakan minimum
# karena sandi ini hanya dipakai sekali sebelum wajib diganti.
PANJANG_SANDI_SEED = 20
ABJAD_SANDI = string.ascii_letters + string.digits + "!@#$%^&*-_"

WILAYAH_KALTARA: tuple[tuple[str, str, str, str | None], ...] = (
    ("65", "Kalimantan Utara", "PROVINSI", None),
    ("6501", "Bulungan", "KABUPATEN", "65"),
    ("6502", "Malinau", "KABUPATEN", "65"),
    ("6503", "Nunukan", "KABUPATEN", "65"),
    ("6504", "Tana Tidung", "KABUPATEN", "65"),
    ("6571", "Tarakan", "KOTA", "65"),
)

# Dua slot operator per wilayah, sesuai pemasangan yang berjalan sekarang.
OPERATOR_PER_WILAYAH = 2


def sandi_acak(panjang: int = PANJANG_SANDI_SEED) -> str:
    """Sandi acak kriptografis; dicetak sekali lalu tidak dapat dilihat lagi."""
    return "".join(secrets.choice(ABJAD_SANDI) for _ in range(panjang))


def pastikan_wilayah(session: Session) -> int:
    """Isi wilayah yang belum ada. Idempoten."""
    dibuat = 0
    for kode, nama, tingkat, induk in WILAYAH_KALTARA:
        if session.get(Wilayah, kode) is None:
            session.add(Wilayah(kode=kode, nama=nama, tingkat=tingkat, parent_kode=induk, aktif=True))
            dibuat += 1
    session.flush()
    return dibuat


def seed_akun(session: Session) -> list[tuple[str, str]]:
    """Buat akun awal yang belum ada; kembalikan (username, sandi) yang baru.

    Akun yang sudah ada tidak disentuh sama sekali — menjalankan ulang perintah
    ini tidak boleh menyetel ulang sandi siapa pun.
    """
    baru: list[tuple[str, str]] = []

    def buat(username: str, nama: str, peran: str, wilayah_kode: str | None) -> None:
        if repo_pengguna.ambil_untuk_login(session, username) is not None:
            return
        sandi = sandi_acak()
        repo_pengguna.buat(
            session,
            username=username,
            nama=nama,
            password_hash=hash_password(sandi),
            peran=peran,
            wilayah_kode=wilayah_kode,
        )
        baru.append((username, sandi))

    buat("admin", "Administrator Awal", Peran.ADMIN, KODE_PROVINSI)
    for kode, nama, _tingkat, _induk in WILAYAH_KALTARA:
        for nomor in range(1, OPERATOR_PER_WILAYAH + 1):
            buat(f"operator.{kode}.{nomor}", f"Operator {nama} {nomor}", Peran.OPERATOR, kode)
    session.flush()
    return baru


def perintah_seed(tampilkan_sandi: bool) -> int:
    with SessionLocal() as session:
        wilayah_baru = pastikan_wilayah(session)
        akun_baru = seed_akun(session)
        session.commit()

        print(f"Wilayah ditambahkan: {wilayah_baru}")
        print(f"Akun ditambahkan   : {len(akun_baru)}")
        if not akun_baru:
            print("Tidak ada akun baru; sandi akun yang sudah ada tidak diubah.")
            return 0

        if not tampilkan_sandi:
            print(
                "\nSandi awal TIDAK ditampilkan. Jalankan ulang dengan --tampilkan-sandi\n"
                "pada terminal yang aman untuk melihatnya, atau reset lewat panel admin."
            )
            return 0

        print("\nSandi awal berikut hanya ditampilkan SEKALI. Catat dan bagikan")
        print("lewat kanal aman; semua akun wajib menggantinya saat login pertama.\n")
        lebar = max(len(nama) for nama, _ in akun_baru)
        for username, sandi in akun_baru:
            print(f"  {username.ljust(lebar)}  {sandi}")
        return 0


def perintah_periksa() -> int:
    """Ringkasan cepat kesiapan basis data."""
    with SessionLocal() as session:
        wilayah = repo_wilayah.daftar_aktif(session)
        akun = repo_pengguna.daftar_dengan_wilayah(session)
        wajib_ganti = [a for a, _ in akun if a.harus_ganti_password]
        print(f"Wilayah aktif      : {len(wilayah)}")
        print(f"Akun               : {len(akun)}")
        print(f"Wajib ganti sandi  : {len(wajib_ganti)}")
        if wajib_ganti:
            print("  " + ", ".join(a.username for a in wajib_ganti))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m backend.app.cli", description=__doc__)
    sub = parser.add_subparsers(dest="perintah", required=True)

    seed = sub.add_parser("seed", help="buat wilayah dan akun awal bila belum ada")
    seed.add_argument(
        "--tampilkan-sandi",
        action="store_true",
        help="cetak sandi awal ke layar (hanya di terminal yang aman)",
    )
    sub.add_parser("periksa", help="ringkasan kesiapan basis data")

    argumen = parser.parse_args(argv)
    if argumen.perintah == "seed":
        return perintah_seed(argumen.tampilkan_sandi)
    return perintah_periksa()


if __name__ == "__main__":
    sys.exit(main())
