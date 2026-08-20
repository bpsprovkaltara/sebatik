"""Aturan perhitungan capaian dan progres menuju target.

Semua fungsi di sini murni: menerima angka, mengembalikan angka. Tidak menyentuh
basis data dan tidak tahu apa-apa tentang HTTP.
"""

from __future__ import annotations

from typing import NamedTuple

from ..models import ArahBaik

STATUS_BELUM_ADA_DATA = "BELUM_ADA_DATA"
STATUS_TERCAPAI = "TERCAPAI"
STATUS_MENDEKATI = "MENDEKATI"
STATUS_PERLU_PERHATIAN = "PERLU_PERHATIAN"

# Ambang yang memisahkan ketiga status capaian, dalam persen.
AMBANG_TERCAPAI = 100
AMBANG_MENDEKATI = 90


class HasilCapaian(NamedTuple):
    persentase: float | None
    status: str


def capaian(
    realisasi: float | None,
    target: float | None,
    arah_baik: str | None,
    terverifikasi: bool,
) -> HasilCapaian:
    """Persentase capaian terhadap target, sesuai arah baik indikator.

    Arah yang belum diverifikasi admin sengaja tidak dihitung: menghitungnya
    berarti menebak apakah naik itu baik atau buruk, dan tebakan yang salah
    membalik makna angka di dasbor.
    """
    if realisasi is None or target is None or not arah_baik or not terverifikasi:
        return HasilCapaian(None, STATUS_BELUM_ADA_DATA)

    if arah_baik == ArahBaik.NAIK:
        persen = (realisasi / target * 100) if target else None
    else:
        # Arah TURUN: makin kecil realisasi makin baik, jadi rasionya dibalik.
        persen = (target / realisasi * 100) if realisasi else None

    if persen is None:
        return HasilCapaian(None, STATUS_BELUM_ADA_DATA)
    return HasilCapaian(round(persen, 2), status_capaian(persen))


def status_capaian(persen: float) -> str:
    if persen >= AMBANG_TERCAPAI:
        return STATUS_TERCAPAI
    if persen >= AMBANG_MENDEKATI:
        return STATUS_MENDEKATI
    return STATUS_PERLU_PERHATIAN


def progres_menuju(
    nilai_sekarang: float | None,
    nilai_baseline: float | None,
    target: float | None,
) -> float | None:
    """Bagian jalan yang sudah ditempuh dari baseline menuju satu target.

    Dijepit ke 0–100 supaya cincin tracker tidak pernah tergambar melebihi
    lingkaran penuh atau berbalik arah ketika realisasi melewati target atau
    bergerak menjauh dari baseline.
    """
    if nilai_sekarang is None or nilai_baseline is None or target is None:
        return None
    pembagi = target - nilai_baseline
    if pembagi == 0:
        # Baseline sudah sama dengan target: hanya "sudah" atau tidak terdefinisi.
        return 100 if nilai_sekarang == target else None
    return max(0, min(100, round((nilai_sekarang - nilai_baseline) / pembagi * 100, 1)))


def arah_target(nilai_baseline: float | None, target: float | None) -> str | None:
    """Arah yang tersirat dari posisi target terhadap baseline."""
    if nilai_baseline is None or target is None:
        return None
    return ArahBaik.NAIK if target >= nilai_baseline else ArahBaik.TURUN


def membaik(nilai_sekarang: float | None, nilai_sebelumnya: float | None, arah: str | None) -> bool | None:
    if nilai_sekarang is None or nilai_sebelumnya is None or not arah:
        return None
    if arah == ArahBaik.NAIK:
        return nilai_sekarang >= nilai_sebelumnya
    return nilai_sekarang <= nilai_sebelumnya


def kebutuhan_per_tahun(gap: float | None, tahun_sekarang: int | None, tahun_target: int) -> float | None:
    """Laju perbaikan per tahun yang dibutuhkan untuk menutup gap."""
    if gap is None or tahun_sekarang is None or tahun_sekarang >= tahun_target:
        return None
    return round(gap / (tahun_target - tahun_sekarang), 4)


def kalimat_insight(
    *,
    nama_indikator: str = "Indikator",
    nama_wilayah: str,
    tahun: int | None,
    ada_nilai: bool,
    tahun_baseline: int | None,
    progres_2029: float | None,
    progres_2045: float | None,
    target_2029: float | None,
    target_2045: float | None,
    sedang_membaik: bool | None,
    nilai_sekarang: float | None = None,
    nilai_baseline: float | None = None,
    satuan: str | None = None,
    interpretasi: str | None = None,
    riwayat: list[tuple[int, float]] | None = None,
) -> str:
    """Narasi capaian berbasis nilai, baseline, target 2029, dan metadata."""
    if not ada_nilai:
        return f"Data realisasi terverifikasi untuk {nama_wilayah} pada tahun yang dipilih belum tersedia."
    if target_2029 is None and target_2045 is None:
        return "Target 2029 dan 2045 belum tersedia sehingga progres belum dapat dihitung."
    tren = (
        "membaik"
        if sedang_membaik is True
        else "menjauh dari arah target"
        if sedang_membaik is False
        else "belum dapat dibandingkan"
    )

    if (
        progres_2029 is not None
        and nilai_sekarang is not None
        and nilai_baseline is not None
        and target_2029 is not None
    ):
        unit = f" {satuan}" if satuan else ""
        perubahan = nilai_sekarang - nilai_baseline
        relatif = abs(perubahan) / abs(nilai_baseline) if nilai_baseline else abs(perubahan)
        gerak = "bergerak tipis dari" if relatif <= 0.01 else "naik dari" if perubahan > 0 else "turun dari"

        catatan = ""
        riwayat = riwayat or []
        delta = [(akhir[0], akhir[1] - awal[1]) for awal, akhir in zip(riwayat, riwayat[1:], strict=False)]
        if delta and all(nilai > 0 for _, nilai in delta):
            catatan = " dengan kenaikan yang konsisten tiap tahun"
        elif delta and all(nilai < 0 for _, nilai in delta):
            catatan = " dengan penurunan yang konsisten tiap tahun"
        elif delta:
            arah_total = 1 if perubahan >= 0 else -1
            tertahan = [tahun_delta for tahun_delta, nilai in delta[:-1] if nilai * arah_total <= 0]
            if tertahan:
                catatan = f" meski sempat tertahan pada {tertahan[-1]}"

        tercapai = (target_2029 >= nilai_baseline and nilai_sekarang >= target_2029) or (
            target_2029 < nilai_baseline and nilai_sekarang <= target_2029
        )
        rentang = abs(target_2029 - nilai_baseline)
        jarak = abs(target_2029 - nilai_sekarang)
        status = (
            "sudah terlampaui"
            if tercapai
            else "tinggal sedikit"
            if rentang and jarak / rentang <= 0.25
            else "masih cukup lebar"
        )

        sisa_tahun = max(0, 2029 - (tahun or 2029))
        tahun_lalu = max(1, len(riwayat))
        laju_lalu = abs(perubahan) / max(1, (tahun or tahun_baseline or 0) - (tahun_baseline or 0))
        laju_perlu = jarak / sisa_tahun if sisa_tahun else 0
        laju = (
            "dan laju sekarang sudah memadai untuk menutupnya"
            if tercapai or laju_lalu >= laju_perlu
            else f"sehingga {sisa_tahun} tahun tersisa menuntut laju lebih cepat daripada {tahun_lalu} tahun terakhir"
        )

        narasi = (
            f"{nama_indikator} {nama_wilayah} pada {tahun} tercatat {_format_angka(nilai_sekarang)}{unit}, "
            f"{gerak} {_format_angka(nilai_baseline)}{unit} pada {tahun_baseline}{catatan}. "
            f"Jaraknya ke target 2029 sebesar {_format_angka(jarak)}{unit} {status}, {laju}."
        )
        if interpretasi:
            ringkas = interpretasi.split(". ")[0].strip().rstrip(".")
            # Baris baru, bukan spasi. Interpretasi adalah keterangan tentang
            # ARTI indikatornya, bukan lanjutan cerita angka di kalimat
            # sebelumnya; disambung dalam satu paragraf keduanya terbaca
            # sebagai satu alur padahal berpindah pokok bahasan.
            narasi += f"\nInterpretasi indikator: {ringkas[:320]}."

        return narasi
    if progres_2045 is not None:
        return (
            f"Target 2029 belum tersedia. Terhadap target akhir 2045, capaian {tahun} "
            f"berada pada {progres_2045}% perjalanan dari baseline {tahun_baseline} "
            f"dan trennya {tren}."
        )
    return f"Capaian {tahun} tersedia, tetapi progres belum dapat dihitung lengkap."


def _format_angka(nilai: float) -> str:
    """Angka Indonesia tanpa nol desimal yang tidak bermakna."""
    mentah = f"{nilai:,.4f}".rstrip("0").rstrip(".")
    return mentah.replace(",", "#").replace(".", ",").replace("#", ".")


# ---------------------------------------------------------------------------
# Penyusunan muatan capaian.
#
# Bagian di atas murni angka. Bagian ini merangkainya menjadi muatan endpoint
# dengan membaca repository — tetap di luar router karena isinya perhitungan,
# bukan HTTP (backend.md §1.2).
# ---------------------------------------------------------------------------

from typing import Any  # noqa: E402

from sqlalchemy.orm import Session  # noqa: E402

from ..models import KODE_PROVINSI, Indikator, JenisNilai, Wilayah  # noqa: E402
from ..repositories import indikator as repo_indikator  # noqa: E402
from ..repositories import nilai as repo_nilai  # noqa: E402
from . import nilai as svc_nilai  # noqa: E402
from .analitik import TAHUN_TARGET_AKHIR, TAHUN_TARGET_ANTARA  # noqa: E402
from .beranda import STATUS_HANYA_TERVERIFIKASI  # noqa: E402

CATATAN_WILAYAH = "Belum ada basis data kabupaten/kota. Visualisasi akan terisi setelah data wilayah diverifikasi."


def muatan(session: Session, indikator: Indikator, wilayah_kode: str = KODE_PROVINSI) -> dict[str, Any]:
    """Ringkasan capaian satu indikator untuk satu wilayah."""
    seri = repo_nilai.seri(session, indikator.id_indikator, wilayah_kode)
    realisasi = [baris for baris in seri if baris.jenis == JenisNilai.REALISASI and baris.nilai is not None]
    terakhir = max(realisasi, key=lambda baris: baris.tahun) if realisasi else None
    target_setahun = next(
        (
            baris
            for baris in seri
            if terakhir
            and baris.jenis == JenisNilai.TARGET
            and baris.tahun == terakhir.tahun
            and baris.nilai is not None
        ),
        None,
    )
    hasil = capaian(
        terakhir.nilai if terakhir else None,
        target_setahun.nilai if target_setahun else None,
        indikator.arah_baik,
        bool(indikator.arah_baik_terverifikasi),
    )
    return {
        "id_indikator": indikator.id_indikator,
        "nama_indikator": indikator.nama_indikator,
        "kategori": indikator.kategori,
        "kelompok": indikator.kelompok,
        "arah_pembangunan": indikator.arah_pembangunan,
        "tim_pjk": indikator.tim_pjk,
        "satuan": indikator.satuan,
        "arah_baik": indikator.arah_baik,
        "arah_baik_terverifikasi": indikator.arah_baik_terverifikasi,
        "nilai_terakhir": terakhir.nilai if terakhir else None,
        "tahun_terakhir_realisasi": terakhir.tahun if terakhir else None,
        "target_tahun_sama": target_setahun.nilai if target_setahun else None,
        "persentase_capaian": hasil.persentase,
        "status_capaian": hasil.status,
        "tren": [{"tahun": baris.tahun, "nilai": baris.nilai} for baris in realisasi],
    }


# Filter daftar capaian: nama parameter endpoint -> kolom pada muatan.
FILTER_DAFTAR = (
    ("kategori", "kategori"),
    ("kelompok", "kelompok"),
    ("arah_pembangunan", "arah_pembangunan"),
    ("tim", "tim_pjk"),
    ("status_capaian", "status_capaian"),
)


def daftar(session: Session, *, wilayah_kode: str = KODE_PROVINSI, **filter_aktif: str | None) -> dict[str, Any]:
    """Daftar capaian seluruh indikator, disaring menurut kolom muatannya."""
    data = [muatan(session, indikator, wilayah_kode) for indikator in repo_indikator.daftar_ekspor(session)]
    for parameter, kolom in FILTER_DAFTAR:
        nilai = filter_aktif.get(parameter)
        if nilai:
            data = [baris for baris in data if baris.get(kolom) == nilai]
    return {"data": data, "total": len(data), "arah_bersifat_sementara": True}


def detail(session: Session, indikator: Indikator, wilayah: Wilayah, *, tahun: int | None) -> dict[str, Any]:
    """Penelusuran progres satu indikator terhadap target 2029 dan 2045."""
    id_indikator = indikator.id_indikator
    semua = repo_nilai.seri(session, id_indikator, wilayah.kode)
    target = {baris.tahun: baris for baris in semua if baris.jenis == JenisNilai.TARGET}
    realisasi = [
        baris
        for baris in semua
        if baris.jenis == JenisNilai.REALISASI and svc_nilai.angka_terakhir(baris.nilai, baris.nilai_teks) is not None
    ]
    tahun_tersedia = [baris.tahun for baris in realisasi]
    dipilih = tahun if tahun in tahun_tersedia else (max(tahun_tersedia) if tahun_tersedia else tahun)

    def angka_target(tahun_target: int) -> float | None:
        baris = target.get(tahun_target)
        return svc_nilai.angka_terakhir(baris.nilai, baris.nilai_teks) if baris else None

    target_2045 = angka_target(TAHUN_TARGET_AKHIR)
    # Target antara RPJMD dipakai sebagai tolok progres pada tracker karena 2029
    # adalah horizon yang masih bisa ditindaklanjuti perencana hari ini; 2045
    # tetap dikirim sebagai tujuan akhir.
    target_2029 = angka_target(TAHUN_TARGET_ANTARA)

    seri: list[dict[str, Any]] = []
    sebelumnya: float | None = None
    for baris in realisasi:
        angka = svc_nilai.angka_terakhir(baris.nilai, baris.nilai_teks)
        seri.append(
            {
                "tahun": baris.tahun,
                "nilai": angka,
                "nilai_asli": baris.nilai,
                "nilai_teks": baris.nilai_teks,
                "growth": svc_nilai.pertumbuhan(angka, sebelumnya),
                "target": angka_target(baris.tahun),
                "label_periode": svc_nilai.label_periode_tampil(
                    indikator.nama_indikator, baris.label_periode, baris.tahun
                ),
            }
        )
        sebelumnya = angka

    sekarang = next((x for x in seri if x["tahun"] == dipilih), None)
    baseline = seri[0] if seri else None
    tahun_sebelumnya = next((x for x in reversed(seri) if dipilih and x["tahun"] < dipilih), None)

    tahun_target_analisis = TAHUN_TARGET_ANTARA if target_2029 is not None else TAHUN_TARGET_AKHIR
    target_analisis = target_2029 if target_2029 is not None else target_2045
    arah = arah_target(baseline["nilai"] if baseline else None, target_analisis)
    nilai_sekarang = sekarang["nilai"] if sekarang else None
    nilai_baseline = baseline["nilai"] if baseline else None
    progres_2045 = progres_menuju(nilai_sekarang, nilai_baseline, target_2045)
    progres_2029 = progres_menuju(nilai_sekarang, nilai_baseline, target_2029)
    gap_2045 = svc_nilai.selisih(target_2045, nilai_sekarang, digit=4)
    gap_2029 = svc_nilai.selisih(target_2029, nilai_sekarang, digit=4)

    proyeksi = [
        {
            "tahun": x["tahun"],
            "realisasi": x["nilai"],
            "jalur_target": nilai_sekarang if x["tahun"] == dipilih else None,
        }
        for x in seri
    ]
    if target_analisis is not None and not any(x["tahun"] == tahun_target_analisis for x in proyeksi):
        proyeksi.append({"tahun": tahun_target_analisis, "realisasi": None, "jalur_target": target_analisis})

    metadata = repo_indikator.ambil_metadata(session, indikator.id_indikator)

    return {
        "id_indikator": indikator.id_indikator,
        "kategori": indikator.kategori,
        "kelompok": indikator.kelompok,
        "arah_pembangunan": indikator.arah_pembangunan,
        "kode_indikator": indikator.kode_indikator,
        "nama_indikator": indikator.nama_indikator,
        "satuan": indikator.satuan,
        "sumber_data": indikator.sumber_data,
        "frekuensi": indikator.frekuensi,
        "opd_pengampu": indikator.opd_pengampu,
        "wilayah": {"kode": wilayah.kode, "nama": wilayah.nama, "tingkat": wilayah.tingkat},
        "tahun": dipilih,
        "tahun_tersedia": tahun_tersedia,
        "series": seri,
        "projection": proyeksi,
        "nilai_tahun": nilai_sekarang,
        "nilai_teks": sekarang["nilai_teks"] if sekarang else None,
        "label_periode": sekarang["label_periode"] if sekarang else None,
        "target_2045": target_2045,
        "target_2045_teks": target[TAHUN_TARGET_AKHIR].nilai_teks if TAHUN_TARGET_AKHIR in target else None,
        "target_2029": target_2029,
        "target_2029_teks": target[TAHUN_TARGET_ANTARA].nilai_teks if TAHUN_TARGET_ANTARA in target else None,
        "arah_target": arah,
        "tahun_target_analisis": tahun_target_analisis,
        "progres_2045": progres_2045,
        "progres_2029": progres_2029,
        "gap_2045": gap_2045,
        "gap_2029": gap_2029,
        "kebutuhan_per_tahun": kebutuhan_per_tahun(gap_2045, dipilih, TAHUN_TARGET_AKHIR),
        "insight": kalimat_insight(
            nama_indikator=indikator.nama_indikator,
            nama_wilayah=wilayah.nama,
            tahun=dipilih,
            ada_nilai=sekarang is not None,
            tahun_baseline=baseline["tahun"] if baseline else None,
            progres_2029=progres_2029,
            progres_2045=progres_2045,
            target_2029=target_2029,
            target_2045=target_2045,
            sedang_membaik=membaik(
                nilai_sekarang,
                tahun_sebelumnya["nilai"] if tahun_sebelumnya else None,
                arah,
            ),
            nilai_sekarang=nilai_sekarang,
            nilai_baseline=nilai_baseline,
            satuan=indikator.satuan,
            interpretasi=metadata.interpretasi if metadata else None,
            riwayat=[(x["tahun"], x["nilai"]) for x in seri if x["nilai"] is not None and x["tahun"] <= dipilih]
            if dipilih
            else [],
        ),
        "status_data": STATUS_HANYA_TERVERIFIKASI,
        "catatan_wilayah": None if wilayah.kode == KODE_PROVINSI else CATATAN_WILAYAH,
    }
