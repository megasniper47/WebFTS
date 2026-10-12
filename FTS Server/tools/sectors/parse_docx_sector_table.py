"""Phase 2 of the Airport CTR/TMA rebuild.

Parses the 21-row summary table in
'CTR TMA cac san bay doc theo duong HK RNAV2.docx' (table index 0, header
row skipped) into structured vertical/horizontal limits, then cross-checks
each row against the KMZ metadata already captured per area in Phase 1's
output (vatm_airport_sectors_2026.geojson, `kmz_fields`). Cross-check results
are reported, not silently resolved -- Phase 3 decides which value wins.

Usage:
    python parse_docx_sector_table.py --docx "<path to .docx>" \
        --phase1 WebATM/static/data/vatm_kmz/vatm_airport_sectors_2026.geojson \
        --out WebATM/static/data/vatm_kmz/vatm_airport_sectors_docx_table.json
"""
from __future__ import annotations

import argparse
import json
import re

import docx

# Row order in the docx == row order here; each docx row name maps 1:1 to a
# Phase 1 output_key (verified by hand against the 20 extracted areas + the
# one area -- Da Nang CTL -- that was already extracted separately from the
# ACC folder in an earlier phase and is not in the Phase 1 file at all).
KEY_BY_NAME = {
    "Nội Bài - TMA": "nb_tma",
    "Nội Bài - CTR": "nb_ctr",
    "Đồng Hới - CTR": "dh_ctr",
    "Phú Bài - CTR": "pb_ctr",
    "Đà Nẵng - TMA": "dn_tma",  # docx name has a "\n(2000-9000ft)" suffix, stripped before lookup
    "Đà Nẵng - CTL": "dn_ctl",  # NOT in Phase 1 file -- already covered by vatm_acc_fir_2026.geojson
    "Đà Nẵng - CTR": "dn_ctr",
    "Chu Lai - CTR": "cl_ctr",
    "Pleiku - CTR": "pk_ctr",
    "Phù Cát - CTR": "pc_ctr",
    "Tuy Hoà - CTR": "th_ctr",
    "Cam Ranh - TMA (APP)": "cr_tma",
    "Cam Ranh - CTR": "cr_ctr",
    "Buôn Ma Thuột - CTR": "bmt_ctr",
    "Liên Khương - CTR": "lk_ctr",
    "TSN - Long Thành - TMA": "tsnlt_tma",
    "Tân Sơn Nhất - CTR": "tsn_ctr",
    "Long Thành - CTR": "lt_ctr",
    "Cần Thơ - CTR": "ct_ctr",
    "Phú Quốc - CTR": "pq_ctr",
    "Phú Quốc - TMA": "pq_tma",
}

FT_PER_M = 3.28084

FL_RE = re.compile(r"^FL\s*(\d+)$", re.I)
M_FT_RE = re.compile(r"^(\d+)\s*m\s*\((\d+)\s*ft\)$", re.I)
FT_M_RE = re.compile(r"^(\d+)\s*ft\s*\((\d+)\s*m\)$", re.I)
M_ONLY_RE = re.compile(r"^(\d+)\s*m$", re.I)
FT_ONLY_RE = re.compile(r"^(\d+)\s*ft$", re.I)
RANGE_M_FT_RE = re.compile(r"^(\d+)-(\d+)\s*m\s*\((\d+)-(\d+)\s*ft\)$", re.I)
RADIUS_RE = re.compile(r"R\s*(\d+(?:\.\d+)?)\s*km", re.I)
CENTER_RE = re.compile(r"tâm\s+([A-Za-z0-9/. ]+?)(?:,|$)", re.I)


def parse_limit_token(raw: str) -> dict:
    raw = raw.strip()
    if raw.upper() in ("SFC", "SFC/NƯỚC", "SFC/NUOC"):
        return {"kind": "SFC", "value_ft": 0, "value_m": 0, "raw": raw}
    m = FL_RE.match(raw)
    if m:
        fl = int(m.group(1))
        return {"kind": "FL", "value_ft": fl * 100, "value_m": round(fl * 100 / FT_PER_M), "raw": raw}
    m = M_FT_RE.match(raw)
    if m:
        return {"kind": "ALT", "value_m": int(m.group(1)), "value_ft": int(m.group(2)), "raw": raw}
    m = FT_M_RE.match(raw)
    if m:
        return {"kind": "ALT", "value_ft": int(m.group(1)), "value_m": int(m.group(2)), "raw": raw}
    m = M_ONLY_RE.match(raw)
    if m:
        val = int(m.group(1))
        return {"kind": "ALT", "value_m": val, "value_ft": round(val * FT_PER_M), "raw": raw}
    m = FT_ONLY_RE.match(raw)
    if m:
        val = int(m.group(1))
        return {"kind": "ALT", "value_ft": val, "value_m": round(val / FT_PER_M), "raw": raw}
    m = RANGE_M_FT_RE.match(raw)
    if m:
        return {
            "kind": "ALT_RANGE",
            "value_m_min": int(m.group(1)), "value_m_max": int(m.group(2)),
            "value_ft_min": int(m.group(3)), "value_ft_max": int(m.group(4)),
            "raw": raw,
        }
    return {"kind": "UNPARSED", "raw": raw}


def split_vertical(cell: str) -> tuple[dict, dict, str | None]:
    """Return (lower, upper, note). `note` carries any trailing clause after
    a comma that isn't part of the limit itself (e.g. 'tru khu vuc thuoc CTR')."""
    note = None
    body = cell
    if "," in cell:
        # only split on a comma that starts a trailing prose clause, not one
        # embedded inside a numeric range -- none of our rows have a comma
        # inside the numeric part, so a plain split is safe here.
        parts = cell.split(",", 1)
        body, note = parts[0].strip(), parts[1].strip()
    # the separator is always " - " between the lower and upper token
    halves = body.split(" - ")
    if len(halves) != 2:
        return {"kind": "UNPARSED", "raw": body}, {"kind": "UNPARSED", "raw": body}, note
    lower, upper = (parse_limit_token(h) for h in halves)
    return lower, upper, note


def parse_horizontal(cell: str) -> dict:
    radius_m = RADIUS_RE.search(cell)
    center_m = CENTER_RE.search(cell)
    return {
        "raw": cell,
        "radius_km": float(radius_m.group(1)) if radius_m else None,
        "center_desc": center_m.group(1).strip() if center_m else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--docx", required=True)
    ap.add_argument("--phase1", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    d = docx.Document(args.docx)
    table = d.tables[0]
    rows = [[c.text.strip() for c in r.cells] for r in table.rows[1:]]

    phase1 = json.load(open(args.phase1, encoding="utf-8"))
    kmz_by_key = {f["properties"]["output_key"]: f["properties"] for f in phase1["features"]}

    areas = []
    unmatched_names = []
    for _, name_raw, horiz, vert, cls in rows:
        name = re.sub(r"\s*\n.*", "", name_raw).strip()  # strip "\n(2000-9000ft)" style suffixes
        key = KEY_BY_NAME.get(name)
        if key is None:
            unmatched_names.append(name_raw)
            continue
        lower, upper, note = split_vertical(vert)
        horiz_parsed = parse_horizontal(horiz)
        entry = {
            "key": key,
            "name": name,
            "airspace_class": cls or None,
            "horizontal": horiz_parsed,
            "vertical_lower": lower,
            "vertical_upper": upper,
            "note": note,
        }

        kmz = kmz_by_key.get(key)
        cross_check = []
        if kmz is not None:
            fields = kmz.get("kmz_fields", {})
            kmz_class = fields.get("Class_Code")
            if kmz_class and cls and kmz_class != cls:
                cross_check.append(f"KMZ Class_Code={kmz_class!r} vs docx Loại={cls!r}")
            kmz_upper_val = fields.get("DistVertUpper_Val")
            kmz_upper_uom = fields.get("DistVertUpper_UOM", "")
            if kmz_upper_val and kmz_upper_val != "<Null>":
                if "Flight Level" in kmz_upper_uom:
                    kmz_upper_ft = int(kmz_upper_val) * 100
                elif "Meters" in kmz_upper_uom:
                    kmz_upper_ft = round(int(kmz_upper_val) * FT_PER_M)
                else:
                    kmz_upper_ft = None
                docx_upper_ft = upper.get("value_ft")
                if kmz_upper_ft is not None and docx_upper_ft is not None and abs(kmz_upper_ft - docx_upper_ft) > 50:
                    cross_check.append(
                        f"KMZ upper={kmz_upper_val} {kmz_upper_uom} (~{kmz_upper_ft}ft) "
                        f"vs docx upper {upper['raw']!r} (~{docx_upper_ft}ft)"
                    )
            kmz_radius = fields.get("Radius_Val")
            if kmz_radius and kmz_radius != "<Null>" and horiz_parsed["radius_km"] is not None:
                try:
                    if abs(float(kmz_radius) - horiz_parsed["radius_km"]) > 0.5:
                        cross_check.append(
                            f"KMZ radius={kmz_radius} {fields.get('Radius_UOM')} vs docx radius="
                            f"{horiz_parsed['radius_km']}km"
                        )
                except ValueError:
                    pass
            entry["kmz_reconciliation_note"] = kmz.get("reconciliation_note")
        else:
            cross_check.append("No Phase 1 KMZ geometry entry for this key (expected only for dn_ctl)")
        entry["cross_check"] = cross_check
        areas.append(entry)

    payload = {
        "schemaVersion": 1,
        "source": {
            "document": "CTR TMA các sân bay dọc theo đường HK RNAV2.docx",
            "table": "Bảng tổng hợp",
        },
        "areaCount": len(areas),
        "areas": areas,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    print(f"Parsed {len(areas)}/21 rows -> {args.out}")
    if unmatched_names:
        print("UNMATCHED:", unmatched_names)
    flagged = [a for a in areas if a["cross_check"]]
    print(f"{len(flagged)} area(s) with cross-check notes:")
    for a in flagged:
        print(f"  {a['key']:12s} {a['name']}")
        for c in a["cross_check"]:
            print(f"      - {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
