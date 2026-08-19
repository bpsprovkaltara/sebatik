"""Pindahkan data SQLite lama ke skema konsolidasi (PostgreSQL atau SQLite).

Sekali jalan. Membaca `data/processed/sebatik.db` (skema lama, dua keluarga
tabel paralel) dan menulis ke basis data tujuan yang skemanya sudah dibuat
Alembic.

KEPUTUSAN MODEL DATA
--------------------
docs/refactoring/model-data.md §4 mengasumsikan `indikator` (ETL) dan
`beranda_indikator` (master) dapat digabung menjadi satu dimensi 86 baris.
Data sebenarnya membantah asumsi itu: kedua tabel memakai skema ID yang
berbeda (`ISV-01` vs `ISV-001`), irisan ID-nya nol, dan hanya 23 dari 86 nama
yang cocok — `ISV-01` adalah "GNI per kapita" sedangkan `ISV-001` adalah
"PDRB per Kapita". Keduanya dua versi daftar indikator yang berbeda.

Keputusan yang diambil: **daftar master yang dipakai, jalur ETL dibuang.**
Dimensi baru berisi 86 indikator dari `beranda_indikator`. Konsekuensinya
dicatat eksplisit di bawah dan dilaporkan skrip ini saat dijalankan.

Pemetaan tabel:

    beranda_indikator                                 -> indikator (86)
    beranda_metadata                                  -> metadata_indikator (86)
    beranda_nilai + beranda_nilai_periode             -> nilai_indikator (wilayah '65')
    beranda_nilai_wilayah + ..._periode               -> nilai_indikator (kab/kota)
    wilayah, pengguna, usulan_nilai, bukti_dukung,
    log_perubahan, log_aktivitas, unggahan_excel      -> tetap
    indikator, nilai_indikator, metadata_indikator    -> DIBUANG (jalur ETL)
    penugasan_pic, snapshot_ketersediaan              -> dipetakan lewat nama; sisanya dibuang

Atribut yang hanya ada di jalur ETL (`arah_baik`, `tim_pjk`, `nama_asli`,
`status_rpjmd`, `kode_sdgs`, `link_*`, `catatan_teknis`) tetap dibawa untuk
indikator yang namanya cocok, karena itu hasil verifikasi manual admin dan
membuangnya akan melumpuhkan perhitungan capaian tanpa alasan. Indikator yang
tidak cocok dilaporkan agar `arah_baik`-nya dapat diisi ulang lewat endpoint
`PUT /api/v1/arah-baik/{id}` yang sudah ada.

Pemakaian::

    python scripts/migrasi_ke_skema_target.py --periksa
    python scripts/migrasi_ke_skema_target.py --jalankan
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import create_engine, func, select, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from backend.app.config import DEFAULT_DB_PATH, settings  # noqa: E402
from backend.app.models import (  # noqa: E402
    BuktiDukung,
    Indikator,
    JenisNilai,
    LogAktivitas,
    LogPerubahan,
    MetadataIndikator,
    NilaiIndikator,
    Pengguna,
    PenugasanPic,
    SnapshotKetersediaan,
    StatusVerifikasi,
    UnggahanExcel,
    UsulanNilai,
    Wilayah,
)
from backend.app.models.wilayah import KODE_PROVINSI  # noqa: E402


class Laporan:
    """Kumpulan hitungan baris dan catatan untuk verifikasi pasca-migrasi."""

    def __init__(self) -> None:
        self.baris: dict[str, int] = {}
        self.peringatan: list[str] = []
        self.catatan: list[str] = []

    def catat(self, nama: str, jumlah: int = 1) -> None:
        self.baris[nama] = self.baris.get(nama, 0) + jumlah

    def ingatkan(self, pesan: str) -> None:
        self.peringatan.append(pesan)

    def beritahu(self, pesan: str) -> None:
        self.catatan.append(pesan)

    def cetak(self) -> None:
        lebar = max((len(k) for k in self.baris), default=10)
        print("\nRingkasan baris yang ditulis:")
        for nama, jumlah in sorted(self.baris.items()):
            print(f"  {nama.ljust(lebar)}  {jumlah:>7}")
        for pesan in self.catatan:
            print(f"\n{pesan}")
        if self.peringatan:
            print(f"\nPeringatan ({len(self.peringatan)}):")
            for pesan in self.peringatan[:30]:
                print(f"  - {pesan}")
            if len(self.peringatan) > 30:
                print(f"  ... dan {len(self.peringatan) - 30} lainnya")


# --- utilitas --------------------------------------------------------------


def _koneksi_sumber(path: Path) -> sqlite3.Connection:
    koneksi = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    koneksi.row_factory = sqlite3.Row
    return koneksi


def _tabel_ada(koneksi: sqlite3.Connection, nama: str) -> bool:
    return koneksi.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nama,)).fetchone() is not None


def _baca(koneksi: sqlite3.Connection, tabel: str) -> Iterator[dict[str, Any]]:
    if not _tabel_ada(koneksi, tabel):
        return
    for baris in koneksi.execute(f"SELECT * FROM {tabel}"):
        yield dict(baris)


def _waktu(nilai: Any) -> datetime | None:
    """SQLite menyimpan waktu sebagai teks; PostgreSQL butuh datetime sadar zona."""
    if nilai in (None, ""):
        return None
    if isinstance(nilai, datetime):
        return nilai if nilai.tzinfo else nilai.replace(tzinfo=UTC)
    teks = str(nilai).strip().replace("Z", "+00:00")
    for pola in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(teks, pola).replace(tzinfo=UTC)
        except ValueError:
            continue
    try:
        terurai = datetime.fromisoformat(teks)
    except ValueError:
        return None
    return terurai if terurai.tzinfo else terurai.replace(tzinfo=UTC)


def _bool(nilai: Any, *, bawaan: bool = False) -> bool:
    return bawaan if nilai is None else bool(nilai)


def _nama_baku(nilai: Any) -> str:
    """Normalisasi nama indikator untuk pencocokan lintas versi daftar."""
    teks = str(nilai or "").casefold()
    teks = teks.replace("produk domestik regional bruto", "pdrb")
    teks = re.sub(r"\([^)]*\)", " ", teks)
    return re.sub(r"[^a-z0-9]+", " ", teks).strip()


def _nomor_dari_id(id_indikator: str) -> int | None:
    """`ISV-001` -> 1. Master tidak punya kolom nomor, tetapi urutan ekspor butuh."""
    cocok = re.search(r"(\d+)$", id_indikator)
    return int(cocok.group(1)) if cocok else None


# --- tahap migrasi ---------------------------------------------------------


def petakan_etl_ke_master(sumber: sqlite3.Connection, laporan: Laporan) -> dict[str, str]:
    """Pemetaan id ETL -> id master berdasarkan nama indikator yang identik.

    Hanya kecocokan satu-ke-satu yang diterima; nama ganda di salah satu sisi
    dilewati agar tidak ada atribut yang menempel pada indikator yang salah.
    """
    etl: dict[str, list[str]] = {}
    for baris in _baca(sumber, "indikator"):
        etl.setdefault(_nama_baku(baris["nama_indikator"]), []).append(baris["id_indikator"])
    master: dict[str, list[str]] = {}
    for baris in _baca(sumber, "beranda_indikator"):
        master.setdefault(_nama_baku(baris["nama_indikator"]), []).append(baris["id_indikator"])

    pemetaan = {
        etl[nama][0]: master[nama][0]
        for nama in set(etl) & set(master)
        if len(etl[nama]) == 1 and len(master[nama]) == 1
    }
    laporan.beritahu(
        f"Pencocokan nama ETL -> master: {len(pemetaan)} dari {len(etl)} indikator ETL.\n"
        f"Atribut hasil verifikasi manual (arah_baik, tim_pjk, dll.) hanya terbawa untuk "
        f"{len(pemetaan)} indikator itu."
    )
    return pemetaan


def pindahkan_wilayah(sumber: sqlite3.Connection, sesi: Session, laporan: Laporan) -> None:
    """Wilayah sudah diisi migrasi Alembic; di sini hanya menyelaraskan status aktif."""
    for baris in _baca(sumber, "wilayah"):
        wilayah = sesi.get(Wilayah, baris["kode"])
        if wilayah is None:
            sesi.add(
                Wilayah(
                    kode=baris["kode"],
                    nama=baris["nama"],
                    tingkat=baris["tingkat"],
                    parent_kode=baris.get("parent_kode"),
                    aktif=_bool(baris.get("aktif"), bawaan=True),
                )
            )
            laporan.catat("wilayah (baru)")
        else:
            wilayah.aktif = _bool(baris.get("aktif"), bawaan=True)
    sesi.flush()


def pindahkan_indikator(
    sumber: sqlite3.Connection, sesi: Session, pemetaan: dict[str, str], laporan: Laporan
) -> set[str]:
    """Dimensi indikator berasal dari daftar master; ETL hanya memperkaya."""
    warisan = {
        pemetaan[baris["id_indikator"]]: baris
        for baris in _baca(sumber, "indikator")
        if baris["id_indikator"] in pemetaan
    }
    status_metadata = {
        baris["id_indikator"]: baris.get("status_metadata") for baris in _baca(sumber, "beranda_metadata")
    }
    # Tahun terakhir tidak ada di master; diturunkan dari data yang benar-benar ada.
    tahun_terakhir: dict[str, int] = {}
    for baris in _baca(sumber, "beranda_nilai"):
        if baris["jenis"] != JenisNilai.REALISASI:
            continue
        if baris.get("nilai") is None and baris.get("nilai_teks") is None:
            continue
        id_indikator = baris["id_indikator"]
        tahun = int(baris["tahun"])
        if tahun > tahun_terakhir.get(id_indikator, 0):
            tahun_terakhir[id_indikator] = tahun

    dikenal: set[str] = set()
    tanpa_arah = []
    for baris in _baca(sumber, "beranda_indikator"):
        id_indikator = baris["id_indikator"]
        lama = warisan.get(id_indikator, {})
        if not lama.get("arah_baik"):
            tanpa_arah.append(id_indikator)
        sesi.add(
            Indikator(
                id_indikator=id_indikator,
                kategori=baris["kategori"],
                nomor=lama.get("nomor") or _nomor_dari_id(id_indikator),
                kode_indikator=baris.get("kode_indikator"),
                nama_indikator=baris["nama_indikator"],
                nama_asli=lama.get("nama_asli"),
                kelompok=baris.get("kelompok"),
                arah_pembangunan=baris.get("arah_pembangunan"),
                sasaran_visi=baris.get("sasaran_visi"),
                misi_agenda=baris.get("misi_agenda"),
                arah_ie=baris.get("arah_ie"),
                indikator_induk=baris.get("indikator_induk"),
                kelompok_makro=baris.get("kelompok_makro"),
                satuan=baris.get("satuan"),
                penghasil=lama.get("penghasil"),
                kl_pengampu=lama.get("kl_pengampu"),
                opd_pengampu=baris.get("opd_pengampu"),
                tim_pjk=lama.get("tim_pjk"),
                sumber_data=baris.get("sumber_data"),
                frekuensi=baris.get("frekuensi"),
                status_ketersediaan=baris.get("status_ketersediaan"),
                status_metadata=status_metadata.get(id_indikator),
                periode_data=baris.get("periode_data"),
                tahun_terakhir=tahun_terakhir.get(id_indikator),
                is_proxy=_bool(baris.get("is_proxy")),
                nama_proxy=baris.get("nama_proxy"),
                status_rpjmd=lama.get("status_rpjmd"),
                arah_baik=lama.get("arah_baik"),
                arah_baik_terverifikasi=_bool(lama.get("arah_baik_terverifikasi")),
                kode_sdgs=lama.get("kode_sdgs"),
                link_metadata=lama.get("link_metadata"),
                link_publikasi=lama.get("link_publikasi"),
                link_data=lama.get("link_data"),
                catatan_teknis=lama.get("catatan_teknis"),
                sumber_master=baris.get("sumber_master"),
                status_verifikasi=baris.get("status_verifikasi") or StatusVerifikasi.DISETUJUI,
                diverifikasi_pada=_waktu(baris.get("diverifikasi_pada")),
            )
        )
        dikenal.add(id_indikator)
        laporan.catat("indikator")

    if tanpa_arah:
        laporan.beritahu(
            f"{len(tanpa_arah)} indikator belum punya `arah_baik` karena tidak ada padanannya di\n"
            f"daftar ETL lama. Perhitungan capaian untuk indikator ini akan berstatus\n"
            f"BELUM_ADA_DATA sampai admin mengisinya lewat PUT /api/v1/arah-baik/{{id}}.\n"
            f"Contoh: {', '.join(sorted(tanpa_arah)[:8])}"
        )
    sesi.flush()
    return dikenal


def pindahkan_metadata(
    sumber: sqlite3.Connection,
    sesi: Session,
    dikenal: set[str],
    pemetaan: dict[str, str],
    laporan: Laporan,
) -> None:
    warisan = {
        pemetaan[baris["id_indikator"]]: baris
        for baris in _baca(sumber, "metadata_indikator")
        if baris["id_indikator"] in pemetaan
    }
    for baris in _baca(sumber, "beranda_metadata"):
        id_indikator = baris["id_indikator"]
        if id_indikator not in dikenal:
            laporan.ingatkan(f"metadata {id_indikator}: indikator induk tidak ada, dilewati")
            continue
        lama = warisan.get(id_indikator, {})
        sesi.add(
            MetadataIndikator(
                id_indikator=id_indikator,
                definisi=baris.get("definisi") or lama.get("definisi"),
                interpretasi=baris.get("interpretasi") or lama.get("interpretasi"),
                sumber_data=baris.get("sumber_data") or lama.get("sumber_data"),
                frekuensi=baris.get("frekuensi") or lama.get("frekuensi"),
                rumus=lama.get("rumus"),
                rumus_mentah=baris.get("rumus_mentah") or lama.get("rumus_mentah"),
                rumus_latex=baris.get("rumus_latex"),
                halaman_sumber=lama.get("halaman_sumber"),
                perlu_verifikasi_manual=_bool(lama.get("perlu_verifikasi_manual")),
                sumber_metadata=baris.get("sumber_metadata") or lama.get("sumber_metadata"),
                nama_di_buku1=lama.get("nama_di_buku1"),
                status_metadata=baris.get("status_metadata"),
            )
        )
        laporan.catat("metadata_indikator")
    sesi.flush()


def pindahkan_pengguna(sumber: sqlite3.Connection, sesi: Session, laporan: Laporan) -> set[int]:
    """Hash Argon2 disalin apa adanya — tidak bergantung basis data."""
    id_pengguna = set()
    for baris in _baca(sumber, "pengguna"):
        sesi.add(
            Pengguna(
                id=baris["id"],
                username=baris["username"],
                nama=baris["nama"],
                password_hash=baris["password_hash"],
                peran=baris["peran"],
                tim_pjk=baris.get("tim_pjk"),
                wilayah_kode=baris.get("wilayah_kode"),
                aktif=_bool(baris.get("aktif"), bawaan=True),
                harus_ganti_password=_bool(baris.get("harus_ganti_password"), bawaan=True),
                dibuat_pada=_waktu(baris.get("dibuat_pada")) or datetime.now(UTC),
            )
        )
        id_pengguna.add(baris["id"])
        laporan.catat("pengguna")
    sesi.flush()
    return id_pengguna


def pindahkan_usulan(
    sumber: sqlite3.Connection,
    sesi: Session,
    dikenal: set[str],
    pemetaan: dict[str, str],
    laporan: Laporan,
) -> set[int]:
    id_usulan = set()
    for baris in _baca(sumber, "usulan_nilai"):
        id_indikator = pemetaan.get(baris["id_indikator"], baris["id_indikator"])
        if id_indikator not in dikenal:
            laporan.ingatkan(
                f"usulan {baris['id']}: indikator {baris['id_indikator']} tidak ada di daftar master, dilewati"
            )
            continue
        sesi.add(
            UsulanNilai(
                id=baris["id"],
                id_indikator=id_indikator,
                wilayah_kode=baris.get("wilayah_kode"),
                tahun=baris["tahun"],
                jenis=baris["jenis"],
                periode=baris.get("periode"),
                nilai=baris["nilai"],
                sumber=baris["sumber"],
                catatan=baris.get("catatan"),
                status=baris["status"],
                pengusul_id=baris["pengusul_id"],
                verifikator_id=baris.get("verifikator_id"),
                alasan_verifikasi=baris.get("alasan_verifikasi"),
                dibuat_pada=_waktu(baris.get("dibuat_pada")) or datetime.now(UTC),
                dikirim_pada=_waktu(baris.get("dikirim_pada")),
                diverifikasi_pada=_waktu(baris.get("diverifikasi_pada")),
            )
        )
        id_usulan.add(baris["id"])
        laporan.catat("usulan_nilai")
    sesi.flush()
    return id_usulan


def pindahkan_bukti(sumber: sqlite3.Connection, sesi: Session, id_usulan: set[int], laporan: Laporan) -> None:
    for baris in _baca(sumber, "bukti_dukung"):
        if baris["usulan_id"] not in id_usulan:
            laporan.ingatkan(f"bukti {baris['id']}: usulan {baris['usulan_id']} tidak ada, dilewati")
            continue
        sesi.add(
            BuktiDukung(
                id=baris["id"],
                usulan_id=baris["usulan_id"],
                nama_file=baris["nama_file"],
                # Path absolut Windows dari pemasangan lama tidak dapat dibaca
                # container Linux. File fisik disalin ke volume pada cutover.
                path_file=str(
                    Path(settings.evidence_dir)
                    / str(baris["usulan_id"])
                    / PureWindowsPath(str(baris["path_file"])).name
                ),
                mime_type=baris.get("mime_type"),
                ukuran=baris["ukuran"],
                checksum_sha256=baris["checksum_sha256"],
                diunggah_pada=_waktu(baris.get("diunggah_pada")) or datetime.now(UTC),
            )
        )
        laporan.catat("bukti_dukung")
    sesi.flush()


def pindahkan_nilai(
    sumber: sqlite3.Connection,
    sesi: Session,
    dikenal: set[str],
    id_usulan: set[int],
    laporan: Laporan,
) -> None:
    """Empat tabel nilai master menyatu menjadi satu tabel fakta."""
    terkumpul: dict[tuple[str, str, int, str, int | None], dict[str, Any]] = {}

    def tambah(baris: dict[str, Any], wilayah_kode: str, asal: str, *, periode: int | None) -> None:
        id_indikator = baris["id_indikator"]
        if id_indikator not in dikenal:
            laporan.ingatkan(f"nilai {asal}: indikator {id_indikator} tidak ada, dilewati")
            return
        if str(baris["jenis"]) not in tuple(JenisNilai):
            laporan.ingatkan(f"nilai {asal}: jenis '{baris['jenis']}' tidak dikenal, dilewati")
            return
        kunci = (id_indikator, wilayah_kode, int(baris["tahun"]), str(baris["jenis"]), periode)
        usulan_id = baris.get("usulan_id")
        if kunci in terkumpul:
            # Fakta yang sama tertulis di dua tabel oleh `verify_submission` lama
            # (penulisan N-arah). Gabungkan, jangan buang: baris master membawa
            # nilai_teks/satuan_catatan, baris wilayah membawa jejak usulan.
            gabungan = terkumpul[kunci]
            nilai_lama, nilai_baru = gabungan["nilai"], baris.get("nilai")
            if nilai_lama is not None and nilai_baru is not None and nilai_lama != nilai_baru:
                laporan.ingatkan(
                    f"nilai {kunci}: dua sumber berbeda angka ({nilai_lama} vs {nilai_baru}); "
                    f"memakai {nilai_lama} dari sumber yang lebih dulu"
                )
            for kolom, isi in (
                ("nilai", nilai_baru),
                ("nilai_teks", baris.get("nilai_teks")),
                ("label_periode", baris.get("label_periode")),
                ("satuan_catatan", baris.get("satuan_catatan")),
            ):
                if gabungan[kolom] is None:
                    gabungan[kolom] = isi
            if usulan_id in id_usulan:
                # Jejak usulan lebih berharga daripada nama berkas workbook.
                gabungan["usulan_id"] = usulan_id
                gabungan["sumber"] = baris.get("sumber") or gabungan["sumber"]
            laporan.catat("nilai digabung dari dua tabel")
            return
        terkumpul[kunci] = {
            "id_indikator": id_indikator,
            "wilayah_kode": wilayah_kode,
            "tahun": int(baris["tahun"]),
            "jenis": str(baris["jenis"]),
            "periode": periode,
            "nilai": baris.get("nilai"),
            "nilai_teks": baris.get("nilai_teks"),
            "label_periode": baris.get("label_periode"),
            "satuan_catatan": baris.get("satuan_catatan"),
            # `sumber_master` dan `sumber` menyatu menjadi satu kolom `sumber`.
            "sumber": baris.get("sumber") or baris.get("sumber_master"),
            "usulan_id": usulan_id if usulan_id in id_usulan else None,
            "status_verifikasi": baris.get("status_verifikasi") or StatusVerifikasi.DISETUJUI,
            "diverifikasi_pada": _waktu(baris.get("diverifikasi_pada")),
        }

    for baris in _baca(sumber, "beranda_nilai_periode"):
        tambah(baris, KODE_PROVINSI, "beranda_nilai_periode", periode=baris.get("periode"))
    for baris in _baca(sumber, "beranda_nilai"):
        tambah(baris, KODE_PROVINSI, "beranda_nilai", periode=None)
    for baris in _baca(sumber, "beranda_nilai_wilayah_periode"):
        tambah(
            baris,
            str(baris["wilayah_kode"]),
            "beranda_nilai_wilayah_periode",
            periode=baris.get("periode"),
        )
    for baris in _baca(sumber, "beranda_nilai_wilayah"):
        tambah(baris, str(baris["wilayah_kode"]), "beranda_nilai_wilayah", periode=None)

    sesi.bulk_insert_mappings(NilaiIndikator, list(terkumpul.values()))
    laporan.catat("nilai_indikator", len(terkumpul))
    sesi.flush()


def pindahkan_audit(
    sumber: sqlite3.Connection,
    sesi: Session,
    dikenal: set[str],
    id_pengguna: set[int],
    pemetaan: dict[str, str],
    laporan: Laporan,
) -> None:
    def pengguna_valid(nilai: Any) -> int | None:
        return nilai if nilai in id_pengguna else None

    def indikator_valid(nilai: Any) -> str | None:
        dipetakan = pemetaan.get(str(nilai), nilai)
        return dipetakan if dipetakan in dikenal else None

    for baris in _baca(sumber, "log_perubahan"):
        sesi.add(
            LogPerubahan(
                id=baris["id"],
                waktu=_waktu(baris.get("waktu")) or datetime.now(UTC),
                pengguna_id=pengguna_valid(baris.get("pengguna_id")),
                id_indikator=indikator_valid(baris.get("id_indikator")),
                field=baris["field"],
                nilai_lama=baris.get("nilai_lama"),
                nilai_baru=baris.get("nilai_baru"),
                sumber_perubahan=baris["sumber_perubahan"],
                referensi_id=baris.get("referensi_id"),
                catatan=baris.get("catatan"),
            )
        )
        laporan.catat("log_perubahan")

    for baris in _baca(sumber, "log_aktivitas"):
        sesi.add(
            LogAktivitas(
                id=baris["id"],
                waktu=_waktu(baris.get("waktu")) or datetime.now(UTC),
                pengguna_id=pengguna_valid(baris.get("pengguna_id")),
                aksi=baris["aksi"],
                objek_tipe=baris.get("objek_tipe"),
                objek_id=baris.get("objek_id"),
                detail=baris.get("detail"),
            )
        )
        laporan.catat("log_aktivitas")

    for baris in _baca(sumber, "unggahan_excel"):
        sesi.add(
            UnggahanExcel(
                id=baris["id"],
                nama_file_asli=baris["nama_file_asli"],
                path_arsip=str(Path(settings.archive_dir) / PureWindowsPath(str(baris["path_arsip"])).name),
                checksum_sha256=baris["checksum_sha256"],
                status=baris["status"],
                ringkasan_diff=baris.get("ringkasan_diff"),
                pengguna_id=pengguna_valid(baris.get("pengguna_id")),
                dibuat_pada=_waktu(baris.get("dibuat_pada")) or datetime.now(UTC),
                disetujui_pada=_waktu(baris.get("disetujui_pada")),
            )
        )
        laporan.catat("unggahan_excel")

    # Dua tabel berikut memakai id ETL; hanya yang punya padanan master terbawa.
    dilewati_snapshot = 0
    terpakai: set[tuple[str, str]] = set()
    for baris in _baca(sumber, "snapshot_ketersediaan"):
        id_indikator = indikator_valid(baris["id_indikator"])
        kunci = (str(id_indikator), str(baris["tanggal_snapshot"]))
        if id_indikator is None or kunci in terpakai:
            dilewati_snapshot += 1
            continue
        terpakai.add(kunci)
        sesi.add(
            SnapshotKetersediaan(
                id_indikator=id_indikator,
                tanggal_snapshot=str(baris["tanggal_snapshot"]),
                status=baris["status"],
            )
        )
        laporan.catat("snapshot_ketersediaan")

    dilewati_pic = 0
    for baris in _baca(sumber, "penugasan_pic"):
        id_indikator = indikator_valid(baris["id_indikator"])
        if id_indikator is None:
            dilewati_pic += 1
            continue
        sesi.add(
            PenugasanPic(
                id=baris["id"],
                id_indikator=id_indikator,
                jenis_pic=baris["jenis_pic"],
                nama_pic=baris["nama_pic"],
            )
        )
        laporan.catat("penugasan_pic")

    if dilewati_snapshot or dilewati_pic:
        laporan.beritahu(
            f"Tabel berbasis id ETL: {dilewati_snapshot} baris snapshot_ketersediaan dan "
            f"{dilewati_pic} baris penugasan_pic\ndibuang karena indikatornya tidak ada di "
            f"daftar master. Keduanya tidak dipakai endpoint publik."
        )
    sesi.flush()


def selaraskan_urutan(sesi: Session) -> None:
    """Setel ulang sequence PostgreSQL setelah menyisipkan id eksplisit.

    Tanpa ini, INSERT berikutnya memakai id 1 dan langsung bentrok.
    """
    if sesi.bind is None or sesi.bind.dialect.name != "postgresql":
        return
    for tabel in (
        "pengguna",
        "usulan_nilai",
        "bukti_dukung",
        "log_perubahan",
        "log_aktivitas",
        "unggahan_excel",
        "penugasan_pic",
        "nilai_indikator",
    ):
        sesi.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{tabel}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {tabel}), 1), true)"
            )
        )


# --- verifikasi ------------------------------------------------------------


def verifikasi(sumber: sqlite3.Connection, sesi: Session) -> list[str]:
    """Bandingkan sumber dan tujuan; kembalikan daftar selisih yang ditemukan."""
    masalah: list[str] = []

    def hitung_sumber(sql: str) -> int:
        try:
            return int(sumber.execute(sql).fetchone()[0])
        except sqlite3.OperationalError:
            return 0

    def hitung_tujuan(model: Any) -> int:
        return int(sesi.scalar(select(func.count()).select_from(model)) or 0)

    for tabel, model in (
        ("beranda_indikator", Indikator),
        ("beranda_metadata", MetadataIndikator),
        ("pengguna", Pengguna),
        ("log_aktivitas", LogAktivitas),
        ("log_perubahan", LogPerubahan),
        ("unggahan_excel", UnggahanExcel),
    ):
        asal, tujuan = hitung_sumber(f"SELECT COUNT(*) FROM {tabel}"), hitung_tujuan(model)
        if asal != tujuan:
            masalah.append(f"{tabel}: {tujuan} baris di tujuan, {asal} di sumber")

    # Yang diharapkan adalah jumlah kunci alami yang *berbeda*, bukan jumlah
    # baris mentah: satu fakta bisa tertulis di dua tabel oleh kode lama.
    kunci_sumber: set[tuple[Any, ...]] = set()
    for tabel, wilayah_tetap, berperiode in (
        ("beranda_nilai", KODE_PROVINSI, False),
        ("beranda_nilai_periode", KODE_PROVINSI, True),
        ("beranda_nilai_wilayah", None, False),
        ("beranda_nilai_wilayah_periode", None, True),
    ):
        if not _tabel_ada(sumber, tabel):
            continue
        for baris in sumber.execute(f"SELECT * FROM {tabel}"):
            data = dict(baris)
            kunci_sumber.add(
                (
                    data["id_indikator"],
                    wilayah_tetap or str(data["wilayah_kode"]),
                    int(data["tahun"]),
                    str(data["jenis"]),
                    data.get("periode") if berperiode else None,
                )
            )
    if hitung_tujuan(NilaiIndikator) != len(kunci_sumber):
        masalah.append(
            f"nilai_indikator: {hitung_tujuan(NilaiIndikator)} baris, "
            f"{len(kunci_sumber)} kunci alami berbeda diharapkan dari empat tabel master"
        )

    # Setiap baris nilai master harus punya padanan persis di tujuan.
    for tabel, wilayah_tetap, berperiode in (
        ("beranda_nilai", KODE_PROVINSI, False),
        ("beranda_nilai_periode", KODE_PROVINSI, True),
        ("beranda_nilai_wilayah", None, False),
        ("beranda_nilai_wilayah_periode", None, True),
    ):
        if not _tabel_ada(sumber, tabel):
            continue
        for baris in sumber.execute(f"SELECT * FROM {tabel}"):
            data = dict(baris)
            kode = wilayah_tetap or str(data["wilayah_kode"])
            periode = data.get("periode") if berperiode else None
            ada = sesi.scalar(
                select(func.count())
                .select_from(NilaiIndikator)
                .where(
                    NilaiIndikator.id_indikator == data["id_indikator"],
                    NilaiIndikator.wilayah_kode == kode,
                    NilaiIndikator.tahun == data["tahun"],
                    NilaiIndikator.jenis == data["jenis"],
                    NilaiIndikator.periode.is_(None) if periode is None else NilaiIndikator.periode == periode,
                )
            )
            if not ada:
                masalah.append(
                    f"{tabel}: {data['id_indikator']} {kode} {data['tahun']} "
                    f"{data['jenis']} periode={periode} hilang di tujuan"
                )
    return masalah


# --- orkestrasi ------------------------------------------------------------


MODEL_URUT_HAPUS = (
    NilaiIndikator,
    BuktiDukung,
    UsulanNilai,
    LogPerubahan,
    LogAktivitas,
    UnggahanExcel,
    SnapshotKetersediaan,
    PenugasanPic,
    MetadataIndikator,
    Pengguna,
    Indikator,
)


def jalankan(sumber_path: Path, url_tujuan: str, *, kosongkan: bool) -> int:
    if not sumber_path.exists():
        print(f"Basis data sumber tidak ditemukan: {sumber_path}", file=sys.stderr)
        return 1

    sumber = _koneksi_sumber(sumber_path)
    mesin = create_engine(url_tujuan)
    pabrik = sessionmaker(bind=mesin, autoflush=False)
    laporan = Laporan()

    with pabrik() as sesi:
        terisi = sesi.scalar(select(func.count()).select_from(Indikator)) or 0
        if terisi and not kosongkan:
            print(
                f"Tujuan sudah berisi {terisi} indikator. Jalankan ulang dengan --kosongkan bila memang ingin menimpa.",
                file=sys.stderr,
            )
            return 1
        if kosongkan:
            for model in MODEL_URUT_HAPUS:
                sesi.query(model).delete()
            sesi.flush()

        # Satu transaksi: bila ada tahap yang gagal, tidak ada yang separuh jadi.
        pemetaan = petakan_etl_ke_master(sumber, laporan)
        pindahkan_wilayah(sumber, sesi, laporan)
        dikenal = pindahkan_indikator(sumber, sesi, pemetaan, laporan)
        pindahkan_metadata(sumber, sesi, dikenal, pemetaan, laporan)
        id_pengguna = pindahkan_pengguna(sumber, sesi, laporan)
        id_usulan = pindahkan_usulan(sumber, sesi, dikenal, pemetaan, laporan)
        pindahkan_bukti(sumber, sesi, id_usulan, laporan)
        pindahkan_nilai(sumber, sesi, dikenal, id_usulan, laporan)
        pindahkan_audit(sumber, sesi, dikenal, id_pengguna, pemetaan, laporan)
        selaraskan_urutan(sesi)

        masalah = verifikasi(sumber, sesi)
        if masalah:
            sesi.rollback()
            laporan.cetak()
            print(f"\nVerifikasi GAGAL ({len(masalah)} masalah); tidak ada yang ditulis:")
            for pesan in masalah[:40]:
                print(f"  - {pesan}")
            return 1

        sesi.commit()

    laporan.cetak()
    print("\nVerifikasi lolos. Migrasi selesai.")
    sumber.close()
    mesin.dispose()
    return 0


TABEL_DIPERIKSA = (
    "beranda_indikator",
    "beranda_metadata",
    "beranda_nilai",
    "beranda_nilai_periode",
    "beranda_nilai_wilayah",
    "beranda_nilai_wilayah_periode",
    "wilayah",
    "pengguna",
    "usulan_nilai",
    "bukti_dukung",
    "log_perubahan",
    "log_aktivitas",
    "unggahan_excel",
    "indikator",
    "nilai_indikator",
    "metadata_indikator",
    "snapshot_ketersediaan",
    "penugasan_pic",
)


def periksa(sumber_path: Path, tujuan: str) -> int:
    sumber = _koneksi_sumber(sumber_path)
    print(f"Sumber : {sumber_path}")
    print(f"Tujuan : {tujuan}")
    print("\nJumlah baris di sumber (tabel ETL ditandai *dibuang*):")
    dibuang = {"indikator", "nilai_indikator", "metadata_indikator"}
    for tabel in TABEL_DIPERIKSA:
        if _tabel_ada(sumber, tabel):
            jumlah = sumber.execute(f"SELECT COUNT(*) FROM {tabel}").fetchone()[0]
            tanda = "  *dibuang*" if tabel in dibuang else ""
            print(f"  {tabel.ljust(34)} {jumlah:>7}{tanda}")
    pemetaan = petakan_etl_ke_master(sumber, Laporan())
    print(f"\nIndikator ETL yang punya padanan nama di master: {len(pemetaan)}")
    sumber.close()
    print("\nTambahkan --jalankan untuk benar-benar memindahkan.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sumber", type=Path, default=DEFAULT_DB_PATH, help="berkas SQLite lama")
    parser.add_argument("--tujuan", default=None, help="URL tujuan (bawaan: SEBATIK_DATABASE_URL)")
    parser.add_argument("--jalankan", action="store_true", help="tulis ke basis data tujuan")
    parser.add_argument("--periksa", action="store_true", help="tampilkan rencana tanpa menulis")
    parser.add_argument("--kosongkan", action="store_true", help="hapus isi tujuan lebih dulu")
    argumen = parser.parse_args()

    tujuan = argumen.tujuan or settings.database_url
    if Path(str(argumen.sumber)).resolve() == Path(str(tujuan).replace("sqlite:///", "")).resolve():
        print("Sumber dan tujuan menunjuk berkas yang sama; batal.", file=sys.stderr)
        return 1

    if argumen.periksa or not argumen.jalankan:
        return periksa(argumen.sumber, tujuan)
    return jalankan(argumen.sumber, tujuan, kosongkan=argumen.kosongkan)


if __name__ == "__main__":
    raise SystemExit(main())
