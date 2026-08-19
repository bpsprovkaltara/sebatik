"""Ekstraksi kartu metadata Buku 1 dan pemetaan ke indikator SEBATIK."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from rapidfuzz import fuzz, process

from .common import clean_text

LABELS = ["Definisi", "Rumus Perhitungan", "Interpretasi", "Sumber Data", "Frekuensi"]


@dataclass
class Card:
    name: str
    definition: str | None
    raw_formula: str | None
    interpretation: str | None
    source: str | None
    frequency: str | None
    page: int


def normalize_labels(text: str) -> str:
    text = re.sub(r"Nama\s+([^\n]+)\nIndikator\b", r"Nama Indikator \1", text, flags=re.I)
    text = re.sub(r"Nama\s*\n\s*Indikator\b", "Nama Indikator", text, flags=re.I)
    text = re.sub(r"Rumus\s+([^\n]*)\n(?:Perhitungan|Penghitungan)\b", r"Rumus Perhitungan \1", text, flags=re.I)
    text = re.sub(r"Rumus\s*\n\s*(?:Perhitungan|Penghitungan)\b", "Rumus Perhitungan", text, flags=re.I)
    text = re.sub(r"Rumus\s+Penghitungan\b", "Rumus Perhitungan", text, flags=re.I)
    text = re.sub(r"Sumber\s+([^\n]+)\nData\b", r"Sumber Data \1", text, flags=re.I)
    text = re.sub(r"Sumber\s*\n\s*Data\b", "Sumber Data", text, flags=re.I)
    return text


def clean_field(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\[\[PAGE:\d+\]\]", " ", value)
    return clean_text(value)


def label_positions(chunk: str) -> dict[str, tuple[int, int]]:
    """Posisi awal/akhir setiap label kartu di dalam satu potongan teks."""
    positions = {}
    for label in LABELS:
        found = re.search(rf"\b{re.escape(label)}\b", chunk, flags=re.I)
        if found:
            positions[label] = (found.start(), found.end())
    return positions


def field_value(chunk: str, positions: dict[str, tuple[int, int]], label: str) -> str | None:
    """Isi satu label: dari akhir posisi labelnya sampai label berikutnya."""
    if label not in positions:
        return None
    begin = positions[label][1]
    following = [awal for awal, _ in positions.values() if awal > begin]
    return clean_field(chunk[begin : min(following) if following else len(chunk)])


def parse_cards(page_texts: list[tuple[int, str]]) -> list[Card]:
    joined = "\n".join(f"[[PAGE:{page}]]\n{text}" for page, text in page_texts)
    joined = normalize_labels(joined)
    starts = list(re.finditer(r"\bNama Indikator\s+", joined, flags=re.I))
    cards = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(joined)
        chunk = joined[match.end() : end]
        definition_at = re.search(r"\bDefinisi\b", chunk, flags=re.I)
        if not definition_at:
            continue
        name = clean_field(chunk[: definition_at.start()])
        if not name or len(name) > 300:
            continue
        page_markers = re.findall(r"\[\[PAGE:(\d+)\]\]", joined[: match.start()])
        page = int(page_markers[-1]) if page_markers else page_texts[0][0]
        positions = label_positions(chunk)
        cards.append(
            Card(
                name,
                field_value(chunk, positions, "Definisi"),
                field_value(chunk, positions, "Rumus Perhitungan"),
                field_value(chunk, positions, "Interpretasi"),
                field_value(chunk, positions, "Sumber Data"),
                field_value(chunk, positions, "Frekuensi"),
                page,
            )
        )
    return cards


def normalized_name(value: str) -> str:
    value = value.casefold().replace("produk domestik bruto", "pdrb").replace("produk domestik regional bruto", "pdrb")
    value = re.sub(r"\([^)]*\)", " ", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def score_names(left: str, right: str, **_: object) -> float:
    a, b = normalized_name(left), normalized_name(right)
    return max(fuzz.WRatio(a, b), fuzz.token_set_ratio(a, b))


def run(pdf_path: Path, db_path: Path, mapping_path: Path, report_path: Path, alignment_path: Path):
    with pdfplumber.open(pdf_path) as pdf:
        texts = [(i + 1, page.extract_text() or "") for i, page in enumerate(pdf.pages)]
    start = next(
        i
        for i, (_, text) in enumerate(texts)
        if re.search(r"2\.3\.\s*Metadata", text, re.I) and "5 INDIKATOR SASARAN VISI DALAM RPJPD PROVINSI" in text
    )
    alignment_path.parent.mkdir(parents=True, exist_ok=True)
    alignment_path.write_text(
        "\n\n".join(f"===== HALAMAN PDF {p} =====\n{t}" for p, t in texts[:start]), encoding="utf-8"
    )
    raw_path = db_path.parent / "metadata_buku1_berhalaman.txt"
    raw_path.write_text("\n\n".join(f"===== HALAMAN PDF {p} =====\n{t}" for p, t in texts[start:]), encoding="utf-8")
    cards = parse_cards(texts[start:])
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    indicators = conn.execute(
        "SELECT * FROM indikator ORDER BY CASE kategori WHEN 'ISV' THEN 0 ELSE 1 END, nomor"
    ).fetchall()
    conn.execute(
        "UPDATE metadata_indikator SET definisi=NULL, rumus=NULL, rumus_mentah=NULL, interpretasi=NULL, sumber_data=NULL, frekuensi=NULL, halaman_sumber=NULL, perlu_verifikasi_manual=0, sumber_metadata=NULL, nama_di_buku1=NULL"
    )
    card_names = [c.name for c in cards]
    mapping_rows = []
    # Pemetaan satu-ke-satu secara greedy berdasarkan skor tertinggi.
    pairs = sorted(
        (
            (score_names(ind["nama_indikator"], name), i, j)
            for i, ind in enumerate(indicators)
            for j, name in enumerate(card_names)
        ),
        reverse=True,
    )
    assigned_ind, assigned_card, assignments = set(), set(), {}
    for score, i, j in pairs:
        if score < 85:
            break
        if i not in assigned_ind and j not in assigned_card:
            assignments[i] = (j, score)
            assigned_ind.add(i)
            assigned_card.add(j)
    for i, ind in enumerate(indicators):
        best = process.extractOne(ind["nama_indikator"], card_names, scorer=score_names) if card_names else None
        best_name, best_score, _ = best if best else (None, 0, None)
        assigned = assignments.get(i)
        card_index, score = assigned if assigned else (None, best_score)
        name = card_names[card_index] if card_index is not None else best_name
        status = "COCOK" if assigned else "PERLU_REVIEW"
        mapping_rows.append(
            {
                "id_indikator": ind["id_indikator"],
                "nama_di_excel": ind["nama_indikator"],
                "nama_di_buku1": name or "",
                "skor": round(score, 2),
                "status_cocok": status,
            }
        )
        if status == "COCOK" and card_index is not None:
            card = cards[card_index]
            conn.execute(
                """UPDATE metadata_indikator SET definisi=?, rumus_mentah=?, interpretasi=?, sumber_data=?, frekuensi=?, halaman_sumber=?, perlu_verifikasi_manual=1, sumber_metadata='Buku 1 RPJPN-RPJPD 2025-2045', nama_di_buku1=? WHERE id_indikator=?""",
                (
                    card.definition,
                    card.raw_formula,
                    card.interpretation,
                    card.source,
                    card.frequency,
                    str(card.page),
                    card.name,
                    ind["id_indikator"],
                ),
            )
        elif ind["catatan_teknis"] or ind["link_metadata"]:
            fallback = ind["catatan_teknis"] or f"Metadata rujukan: {ind['link_metadata']}"
            source = " | ".join(x for x in (ind["link_metadata"], ind["link_publikasi"]) if x)
            conn.execute(
                """UPDATE metadata_indikator SET definisi=?, sumber_data=?, frekuensi=?, perlu_verifikasi_manual=1, sumber_metadata='BPS Kaltara' WHERE id_indikator=?""",
                (fallback, source or None, ind["periode_data"], ind["id_indikator"]),
            )
    conn.commit()
    complete = conn.execute(
        "SELECT COUNT(*) FROM metadata_indikator WHERE definisi IS NOT NULL AND rumus_mentah IS NOT NULL AND interpretasi IS NOT NULL AND sumber_data IS NOT NULL AND frekuensi IS NOT NULL"
    ).fetchone()[0]
    partial = conn.execute(
        "SELECT COUNT(*) FROM metadata_indikator WHERE (definisi IS NOT NULL OR rumus_mentah IS NOT NULL OR interpretasi IS NOT NULL OR sumber_data IS NOT NULL OR frekuensi IS NOT NULL) AND NOT (definisi IS NOT NULL AND rumus_mentah IS NOT NULL AND interpretasi IS NOT NULL AND sumber_data IS NOT NULL AND frekuensi IS NOT NULL)"
    ).fetchone()[0]
    empty = 86 - complete - partial
    official = conn.execute(
        "SELECT COUNT(*) FROM metadata_indikator WHERE sumber_metadata='Buku 1 RPJPN-RPJPD 2025-2045'"
    ).fetchone()[0]
    local = conn.execute("SELECT COUNT(*) FROM metadata_indikator WHERE sumber_metadata='BPS Kaltara'").fetchone()[0]
    conn.close()
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    with mapping_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id_indikator", "nama_di_excel", "nama_di_buku1", "skor", "status_cocok"]
        )
        writer.writeheader()
        writer.writerows(mapping_rows)
    report = [
        "# Laporan Cakupan Metadata Buku 1",
        "",
        f"- Awal sub-bab 2.3 terdeteksi pada halaman PDF **{texts[start][0]}**.",
        f"- Kartu metadata berhasil diparse: **{len(cards)}**.",
        f"- Cocok otomatis (skor >= 85): **{official}** indikator.",
        f"- Fallback BPS Kaltara: **{local}** indikator.",
        f"- Metadata lengkap: **{complete}/86**.",
        f"- Metadata sebagian: **{partial}/86**.",
        f"- Metadata kosong: **{empty}/86**.",
        "",
        "Semua rumus hasil ekstraksi disimpan sebagai `rumus_mentah` dan ditandai `perlu_verifikasi_manual = TRUE`. Skor di bawah 85 tidak dipaksakan menjadi pasangan.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(
        f"Metadata: kartu={len(cards)}, resmi={official}, lokal={local}, lengkap={complete}, sebagian={partial}, kosong={empty}"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("pdf", type=Path)
    p.add_argument("--db", type=Path, default=Path("data/processed/sebatik.db"))
    p.add_argument("--mapping", type=Path, default=Path("docs/03-pemetaan-metadata.csv"))
    p.add_argument("--report", type=Path, default=Path("docs/03-metadata-report.md"))
    p.add_argument("--alignment", type=Path, default=Path("data/processed/penyelarasan_sebelum_2.3.txt"))
    a = p.parse_args()
    run(a.pdf, a.db, a.mapping, a.report, a.alignment)
