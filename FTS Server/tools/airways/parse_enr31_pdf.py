"""Phase 2 -- Extract structured airway data for the legacy AIP routes from
`VV-ENR-3.1-en.pdf` (AIP Viet Nam, ENR 3.1 "Lower ATS Routes", AMDT 01/23,
15 JUL 2023).

Scope
-----
ENR 3.1 covers only the classic (non-RNAV) lower ATS routes. Cross-checking
every route name against the 74 legacy codes already served in
`vatm_ats_routes.geojson` shows 20 are simply not in this document at all --
mostly the Q-series (Q1-Q15 etc.), which belong to a different AIP chapter
(area nav / RNAV routes) that was not supplied. This script does not invent
data for those 20; they stay geometry-only until that chapter is provided.

Extraction approach
--------------------
Each route occupies a repeating 8-column table (columns 1-7 per the AIP's own
numbering, plus an always-empty column between 4 and 5):
  col0: route designator + every waypoint's name and coordinate for the whole
        route (conceptually one merged cell spanning all of the route's rows)
  col1: magnetic track (both directions) + leg distance
  col2: upper/lower vertical limits, minimum safe altitude, airspace class
  col3: lateral limit width (km)
  col4/col5: cruising level parity (Odd/Even) -- always blank in this
        document; ENR 3.1 does not publish a parity split for these routes
  col6: navigation accuracy requirement (RNP) -- 'NIL' or blank throughout
  col7: remarks / controlling unit / frequency / footnotes

col1-7 extract cleanly via pdfplumber's lines-based table strategy, one row
per leg, and were spot-checked against every route in the document (all agree
on leg count once footnote-only trailing rows -- rows where only col7 has
text, e.g. "(2) For continuation, see AIP Laos" -- are excluded from the leg
count; they carry no track/limits data of their own).

col0 is a different story: for a handful of long, page-spanning routes (only
W1 in this document) the merged waypoint-chain cell fails to associate with
ANY table row at all -- pdfplumber's row-grouping loses the text outright, not
just misplaces it. Relying on the table's col0 would silently drop those
waypoints. Instead, waypoints are read from a raw *positional crop*: for each
page, the column-0 x-range is read off that page's own table geometry (it
shifts by ~40pt between odd/even pages because the running header
left-aligns differently), the page is cropped to that vertical strip, and the
crop's plain text is parsed for "name line(s), then a coordinate line"
repeats. This bypasses row-detection entirely and was verified byte-for-byte
against the table-derived leg count for every route in the document (waypoint
count - 1 == leg count, everywhere).

Nothing is inferred across pages or invented if the two counts disagree --
mismatches are reported as warnings, not silently accepted.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    sys.exit("pdfplumber is required: pip install pdfplumber")


SCHEMA_VERSION = "1.0"

ROUTE_CODE_RE = re.compile(r"^[A-Z]{1,3}\d{1,4}$")
COORD_RE = re.compile(r"^(\d{2})(\d{2})(\d{2}(?:\.\d+)?)N\s+(\d{3})(\d{2})(\d{2}(?:\.\d+)?)E")
FOOTNOTE_SUFFIX_RE = re.compile(r"\s*\((\d+)\)\s*$")

# Lines that repeat verbatim (or near-verbatim once clipped by the column-0
# crop) on every page -- the running header/footer and the column-0 sub-header
# cells themselves. None of these are ever a real waypoint name.
BOILERPLATE_RE = re.compile(
    r"Viet Nam|E?NR\s*3\.1|Civil Aviation|A?MDT\s*0\d/\d\d|"
    r"Route designator|Name of Significant|^Coordinates$|RCP/RSP specification|"
    r"^\d+\s+[A-Z]{3}\s+\d{4}$|^\d$",
    re.IGNORECASE,
)


class Warnings:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, route: str, detail: str) -> None:
        self.items.append(f"[{route}] {detail}")

    def __len__(self) -> int:
        return len(self.items)


def dms_to_decimal(deg: str, minute: str, sec: str) -> float:
    return round(int(deg) + int(minute) / 60 + float(sec) / 3600, 6)


def extract_column0_lines(pdf: "pdfplumber.PDF") -> list[str]:
    """Return every non-boilerplate line from column 0, in document order,
    by cropping each page to that page's own column-0 x-range rather than
    trusting the table's row-to-cell association (see module docstring)."""
    lines: list[str] = []
    for page in pdf.pages:
        tables = page.find_tables(
            table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"}
        )
        candidates = [t for t in tables if len(t.rows) >= 4 and len(t.rows[0].cells) == 8]
        if not candidates:
            continue
        main = max(candidates, key=lambda t: len(t.rows))
        col0_cell = main.rows[0].cells[0]
        if col0_cell is None:
            continue
        x0, _, x1, _ = col0_cell
        crop = page.within_bbox((x0, 0, x1, page.height))
        text = crop.extract_text() or ""
        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line or BOILERPLATE_RE.search(line):
                continue
            lines.append(line)
    return lines


def build_waypoint_chains(col0_lines: list[str], warn: Warnings) -> dict[str, list[dict[str, Any]]]:
    """Group column-0 lines into per-route ordered waypoint lists."""
    chains: dict[str, list[dict[str, Any]]] = {}
    current_code: str | None = None
    pending_name: list[str] = []

    def flush_name_only():
        if pending_name:
            warn.add(current_code or "?", f"waypoint name with no coordinate: {pending_name!r}")

    for line in col0_lines:
        if ROUTE_CODE_RE.match(line):
            flush_name_only()
            current_code = line
            chains.setdefault(current_code, [])
            pending_name = []
            continue

        m = COORD_RE.match(line)
        if m:
            if current_code is None:
                warn.add("?", f"coordinate line before any route code: {line!r}")
                continue
            name = " ".join(pending_name).strip()
            pending_name = []
            footnote = None
            fm = FOOTNOTE_SUFFIX_RE.search(name)
            if fm:
                footnote = fm.group(1)
                name = name[: fm.start()].strip()
            if not name:
                warn.add(current_code, f"coordinate {line!r} with no preceding name")
                name = "?"
            lat = dms_to_decimal(m.group(1), m.group(2), m.group(3))
            lon = dms_to_decimal(m.group(4), m.group(5), m.group(6))
            chains[current_code].append({
                "name": name, "lat": lat, "lon": lon,
                "latDms": f"{m.group(1)}{m.group(2)}{m.group(3)}N",
                "lonDms": f"{m.group(4)}{m.group(5)}{m.group(6)}E",
                "footnoteRef": footnote,
            })
        else:
            if current_code is not None:
                pending_name.append(line)
    flush_name_only()
    return chains


def parse_leg_track_cell(cell: str) -> tuple[int | None, int | None, int | None]:
    track = rev_track = dist = None
    for line in (cell or "").split("\n"):
        line = line.strip()
        m = re.match(r"^(\d{3})°\s*T\s*/\s*(\d{3})°\s*T$", line)
        if m:
            track, rev_track = int(m.group(1)), int(m.group(2))
            continue
        m = re.match(r"^(\d+)\s*KM$", line, re.IGNORECASE)
        if m:
            dist = int(m.group(1))
    return track, rev_track, dist


def parse_limits_cell(cell: str) -> tuple[int | None, int | None, int | None, str | None]:
    upper = lower = msa = cls = None
    for line in (cell or "").split("\n"):
        line = line.strip()
        m = re.match(r"^FL\s*(\d+)$", line, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if upper is None:
                upper = val
            else:
                lower = val
            continue
        m = re.match(r"^(\d+)\s*M$", line, re.IGNORECASE)
        if m:
            msa = int(m.group(1))
            continue
        m = re.match(r"^Class:\s*([A-Za-z])$", line, re.IGNORECASE)
        if m:
            cls = m.group(1).upper()
    return upper, lower, msa, cls


def build_leg_lists(pdf: "pdfplumber.PDF", warn: Warnings) -> dict[str, list[dict[str, Any]]]:
    """Extract per-route leg parameter rows from the table's columns 1-7.
    This part of the table is reliable (unlike column 0) -- see module
    docstring -- so it is read directly via `extract_tables()`."""
    legs_by_route: dict[str, list[dict[str, Any]]] = {}
    current_code: str | None = None

    for page in pdf.pages:
        tables = page.extract_tables(
            table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"}
        )
        for tbl in tables:
            if len(tbl) < 4 or len(tbl[0]) != 8:
                continue
            for row in tbl[3:]:
                c0 = (row[0] or "").strip()
                if c0:
                    first_line = c0.split("\n")[0].strip()
                    if ROUTE_CODE_RE.match(first_line):
                        current_code = first_line
                        legs_by_route.setdefault(current_code, [])
                        continue
                    # continuation-orphan waypoint block glued to a real leg
                    # row (see G474/W1 in the module docstring) -- the row's
                    # own leg columns (if populated) are still real data.
                if current_code is None:
                    continue
                track_cell, limits_cell, width_cell, _odd, _even, rnp_cell, remarks_cell = row[1:]
                has_leg_data = (track_cell or "").strip() or (limits_cell or "").strip()
                if not has_leg_data:
                    continue  # footnote/blank trailing row, not a leg
                track, rev_track, dist = parse_leg_track_cell(track_cell)
                upper, lower, msa, cls = parse_limits_cell(limits_cell)
                width = int(width_cell.strip()) if (width_cell or "").strip().isdigit() else None
                legs_by_route[current_code].append({
                    "magneticTrackDeg": track,
                    "reverseMagneticTrackDeg": rev_track,
                    "distanceKm": dist,
                    "upperFL": upper,
                    "lowerFL": lower,
                    "minSafeAltitudeM": msa,
                    "airspaceClass": cls,
                    "widthKm": width,
                    "navAccuracy": (rnp_cell or "").strip() or None,
                    "remarks": (remarks_cell or "").strip().replace("\n", " ") or None,
                })
    return legs_by_route


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", required=True, help="path to VV-ENR-3.1-en.pdf")
    ap.add_argument("--out", required=True, help="path of the JSON file to write")
    ap.add_argument(
        "--known-codes",
        help="optional path to a JSON file with a flat list of expected route "
             "codes (e.g. dumped from vatm_ats_routes.geojson), to report which "
             "ones this PDF doesn't cover",
    )
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit(f"PDF not found: {args.pdf}")

    warn = Warnings()
    with pdfplumber.open(args.pdf) as pdf:
        col0_lines = extract_column0_lines(pdf)
        waypoints_by_route = build_waypoint_chains(col0_lines, warn)
        legs_by_route = build_leg_lists(pdf, warn)

    routes = []
    all_codes = sorted(set(waypoints_by_route) | set(legs_by_route))
    for code in all_codes:
        wps = waypoints_by_route.get(code, [])
        legs_raw = legs_by_route.get(code, [])
        if legs_raw and len(legs_raw) != max(len(wps) - 1, 0):
            warn.add(code, f"{len(wps)} waypoints but {len(legs_raw)} legs "
                            f"(expected {max(len(wps) - 1, 0)})")
        segments = []
        for i, leg in enumerate(legs_raw):
            frm = wps[i]["name"] if i < len(wps) else "?"
            to = wps[i + 1]["name"] if i + 1 < len(wps) else "?"
            segments.append({"seq": i + 1, "fromWaypoint": frm, "toWaypoint": to, **leg})
        for i, wp in enumerate(wps):
            wp["seq"] = i + 1
        routes.append({
            "code": code,
            "waypointCount": len(wps),
            "segmentCount": len(segments),
            "waypoints": wps,
            "segments": segments,
        })

    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "source": {
            "document": os.path.basename(args.pdf),
            "documentTitle": "AIP Viet Nam ENR 3.1 - Lower ATS Routes",
            "amendment": "AMDT 01/23",
            "effectiveDate": "2023-07-15",
            "status": "official",
            "note": (
                "AIP chính thức (ENR 3.1 - đường bay ATS tầng thấp). Chỉ bao gồm "
                "các đường bay quy ước (conventional), KHÔNG bao gồm các đường bay "
                "khu vực dẫn đường (RNAV, ví dụ Q-series) -- những đường đó thuộc "
                "chương AIP khác chưa được cung cấp."
            ),
        },
        "routeCount": len(routes),
        "routes": routes,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Parsed {len(routes)} routes -> {args.out}")
    mismatches = [r for r in routes if r["segments"] and r["segmentCount"] != r["waypointCount"] - 1]
    print(f"Routes with waypoint/segment count mismatch: {len(mismatches)}")
    for r in mismatches:
        print(f"  {r['code']}: {r['waypointCount']} wps, {r['segmentCount']} segs")

    if args.known_codes:
        with open(args.known_codes, encoding="utf-8") as f:
            known = set(json.load(f))
        parsed_codes = {r["code"] for r in routes}
        missing = sorted(known - parsed_codes)
        print(f"\nExpected {len(known)} known route codes.")
        print(f"Not found in this PDF ({len(missing)}): {missing}")

    if len(warn):
        print(f"\n{len(warn)} warning(s):")
        for w in warn.items:
            print("  " + w)
    else:
        print("\nNo warnings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
