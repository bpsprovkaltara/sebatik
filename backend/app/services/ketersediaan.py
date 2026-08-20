"""Perhitungan kelengkapan slot data pada empat lapis klasifikasi."""

from __future__ import annotations

from typing import NamedTuple

from sqlalchemy.orm import Session

from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai

# Rentang tahun realisasi yang dihitung sebagai "slot" ketersediaan.
TAHUN_AWAL = 2021
TAHUN_AKHIR = 2025
JUMLAH_SLOT_PER_INDIKATOR = TAHUN_AKHIR - TAHUN_AWAL + 1

# (kolom klasifikasi, label tampil, jumlah kelompok menurut dokumen RPJPD).
DIMENSI: tuple[tuple[str, str, int], ...] = (
    ("sasaran_visi", "Sasaran Visi", 5),
    ("misi_agenda", "Misi/Agenda Pembangunan", 8),
    ("arah_ie", "Arah Pembangunan", 17),
    ("indikator_induk", "Indikator Utama Pembangunan", 45),
)

NAMA_SASARAN_VISI = (
    "Peningkatan Pendapatan per Kapita",
    "Pengentasan Kemiskinan dan Ketimpangan",
    "Kepemimpinan dan Pengaruh di Dunia Internasional Meningkat",
    "Peningkatan Daya Saing Sumber Daya Manusia",
    "Penurunan Emisi GRK menuju Net Zero Emission",
)
NAMA_MISI = (
    "Transformasi Sosial", "Transformasi Ekonomi", "Transformasi Tata Kelola",
    "Supremasi Hukum, Stabilitas, dan Kepemimpinan Indonesia", "Ketahanan Sosial Budaya dan Ekologi",
    "Pembangunan Kewilayahan yang Merata dan Berkeadilan",
    "Sarana dan Prasarana yang Berkualitas dan Ramah Lingkungan", "Kesinambungan Pembangunan",
)
NAMA_ARAH = (
    "Kesehatan untuk Semua", "Pendidikan Berkualitas yang Merata", "Perlindungan Sosial yang Adaptif",
    "Iptek, Inovasi, dan Produktivitas Ekonomi", "Penerapan Ekonomi Hijau", "Transformasi Digital",
    "Integrasi Ekonomi Domestik dan Global", "Perkotaan sebagai Pusat Pertumbuhan Ekonomi",
    "Regulasi dan Tata Kelola yang Berintegritas dan Adaptif",
    "Hukum Berkeadilan, Keamanan Nasional Tangguh, dan Demokrasi Substansial", "Stabilitas Ekonomi Makro",
    "Ketangguhan Diplomasi dan Pertahanan Berdaya Gentar Kawasan", "Beragama Maslahat dan Berkebudayaan Maju",
    "Keluarga Berkualitas, Kesetaraan Gender, dan Masyarakat Inklusif", "Lingkungan Hidup Berkualitas",
    "Berketahanan Energi, Air, dan Kemandirian Pangan", "Resiliensi terhadap Bencana dan Perubahan Iklim",
)
NAMA_IUP = (
    "Usia Harapan Hidup", "Kesehatan Ibu dan Anak", "Penanganan Tuberkulosis",
    "Cakupan Kepesertaan Jaminan Kesehatan Nasional", "Hasil Pembelajaran", "Rata-rata Lama Sekolah",
    "Harapan Lama Sekolah", "Proporsi Penduduk Berkualifikasi Pendidikan Tinggi",
    "Pekerja Lulusan Pendidikan Menengah dan Tinggi di Bidang Keahlian Menengah Tinggi", "Tingkat Kemiskinan",
    "Cakupan Kepesertaan Jaminan Sosial Ketenagakerjaan", "Penyandang Disabilitas Bekerja di Sektor Formal",
    "Produktivitas Industri dan Pertanian", "Pembentukan Modal Tetap Bruto", "Tingkat Pengangguran Terbuka",
    "Tingkat Partisipasi Angkatan Kerja Perempuan", "Kontribusi Pariwisata terhadap PDRB",
    "Kontribusi Ekonomi Kreatif terhadap PDRB", "Produktivitas Perkotaan", "Biaya Logistik",
    "Pembentukan Modal Tetap Bruto terhadap PDRB", "Ekspor Barang dan Jasa", "Kota dan Desa Maju, Inklusif, dan Berkelanjutan",
    "Indeks Reformasi Hukum", "Indeks Sistem Pemerintahan Berbasis Elektronik", "Indeks Pelayanan Publik",
    "Indeks Integritas Nasional", "Indeks Pembangunan Hukum", "Rasa Aman di Lingkungan Tempat Tinggal",
    "Indeks Demokrasi Indonesia", "Rasio Pajak Daerah terhadap PDRB", "Tingkat Inflasi",
    "Pendalaman dan Intermediasi Sektor Keuangan", "Inklusi Keuangan", "Ketangguhan Diplomasi",
    "Ketangguhan Pertahanan", "Indeks Pembangunan Kebudayaan", "Indeks Kerukunan Umat Beragama",
    "Indeks Pembangunan Kualitas Keluarga", "Indeks Ketimpangan Gender", "Indeks Pengelolaan Keanekaragaman Hayati",
    "Kualitas Lingkungan Hidup", "Ketahanan Energi, Air, dan Pangan", "Indeks Risiko Bencana",
    "Persentase Penurunan Emisi GRK",
)
NAMA_KELOMPOK_BUKU = {
    "sasaran_visi": NAMA_SASARAN_VISI, "misi_agenda": NAMA_MISI,
    "arah_ie": NAMA_ARAH, "indikator_induk": NAMA_IUP,
}


class Kelompok(NamedTuple):
    kode: str
    label: str
    jumlah_kelompok: int
    jumlah_indikator: int
    slot_terisi: int
    slot_total: int
    persentase: float


def _persentase(terisi: int, total: int) -> float:
    return round(terisi / total * 100, 1) if total else 0


def ketersediaan_tahunan(
    session: Session, tahun_tersedia: list[int], wilayah_kode: str
) -> list[dict[str, object]]:
    """Ketersediaan realisasi per tahun untuk seluruh indikator, ISV, dan IUP."""
    indikator = repo_indikator.daftar_terverifikasi(session)
    menurut_kategori = {
        kategori: [item.id_indikator for item in indikator if item.kategori == kategori]
        for kategori in ("ISV", "IUP")
    }
    semua = [item.id_indikator for item in indikator]
    hasil = []
    for tahun in tahun_tersedia:
        terisi = repo_nilai.hitung_terisi_tahun(session, semua, wilayah_kode, tahun)
        rincian = {}
        for kategori, daftar_id in menurut_kategori.items():
            jumlah = repo_nilai.hitung_terisi_tahun(session, daftar_id, wilayah_kode, tahun)
            rincian[kategori.lower()] = {
                "terisi": jumlah,
                "total": len(daftar_id),
                "persentase": _persentase(jumlah, len(daftar_id)),
            }
        hasil.append(
            {
                "tahun": tahun,
                "terisi": terisi,
                "total": len(semua),
                "persentase": _persentase(terisi, len(semua)),
                **rincian,
            }
        )
    return hasil


def ketersediaan_kelompok(session: Session) -> list[dict[str, object]]:
    """Daftar kelompok unik pada setiap dimensi kerangka pembangunan."""
    hasil = []
    for kolom, label, jumlah_kelompok in DIMENSI:
        daftar = repo_indikator.daftar_berklasifikasi(session, kolom)
        id_indikator = [item.id_indikator for item in daftar]
        terisi = repo_nilai.hitung_slot_terisi(session, id_indikator, TAHUN_AWAL, TAHUN_AKHIR)
        total = len(id_indikator) * JUMLAH_SLOT_PER_INDIKATOR
        hasil.append(
            Kelompok(
                kode=kolom,
                label=label,
                jumlah_kelompok=jumlah_kelompok,
                jumlah_indikator=len(id_indikator),
                slot_terisi=terisi,
                slot_total=total,
                persentase=_persentase(terisi, total),
            )._asdict()
            | {"kelompok": _kelompok_dimensi(daftar, kolom)}
        )
    return hasil


def _kelompok_dimensi(daftar: list, kolom: str) -> list[dict[str, object]]:
    """Nama klasifikasi unik beserta banyak indikator yang menjadi anggotanya."""
    hasil = []
    for urutan, nama_asli in enumerate(dict.fromkeys(getattr(item, kolom) for item in daftar), start=1):
        anggota = [item for item in daftar if getattr(item, kolom) == nama_asli]
        nama_buku = NAMA_KELOMPOK_BUKU[kolom][urutan - 1]
        hasil.append(
            {
                "nama": nama_buku,
                "jumlah_indikator": len(anggota),
                "id_indikator": [item.id_indikator for item in anggota],
            }
        )
    return hasil
