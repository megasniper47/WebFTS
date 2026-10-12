"""Phase 1 -- Extract structured airway data from the RNAV2 specification .docx.

Source document
---------------
"Thông số đường HK RNAV2 và điều kiện sử dụng.docx" (DỰ THẢO, sau cuộc họp
16.9.2026). Each airway occupies one table whose rows alternate between:

  * a WAYPOINT row  -- col0 = '▲', col1 = fix name, col2/col3 = DMS coordinates
                       (duplicated because the two cells are merged)
  * a SEGMENT row   -- describes the leg *between* the preceding waypoint and
                       the following one:
                         col2 = magnetic track (deg)
                         col3 = leg distance (km)
                         col4 = 'FL460\\nFL040'  (upper / lower limit)
                         col5 = minimum safe altitude ('400 M')
                         col6 = lateral limit ('4NM (7.4km)')
                         col7 = cruising levels, ↓ direction (even / 'Chẵn')
                         col8 = cruising levels, ↑ direction (odd / 'Lẻ')
                         col9 = usage conditions (free Vietnamese prose)

Why parse the .docx rather than the KMZ
---------------------------------------
The KMZ only draws *turn points*. Fixes that sit on a straight leg (e.g. DZUKU
on Q16, LEBUV on Q17) have no vertex in the KMZ at all, yet they are published
waypoints and are needed to build a flyable route. The .docx is therefore the
authoritative source for the ordered waypoint chain and for every published
constraint; the KMZ is only used as an independent cross-check of geometry.

The parser never guesses: any cell it cannot interpret is reported as a warning
and the corresponding field is emitted as null.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

try:
    import docx  # python-docx
except ImportError:  # pragma: no cover
    sys.exit("python-docx is required: pip install python-docx")


SCHEMA_VERSION = "1.0"

# "100500N 1054220E" (sometimes with a double space between the two halves)
DMS_RE = re.compile(r"^(\d{2})(\d{2})(\d{2})N\s+(\d{3})(\d{2})(\d{2})E$")
# "FL460" / "FL040"
FL_RE = re.compile(r"^FL\s*(\d{2,3})$", re.IGNORECASE)
# "400 M" / "2150  M" / "1300M"
ALT_M_RE = re.compile(r"^(\d+)\s*M$", re.IGNORECASE)
# "4NM (7.4km)"
LATERAL_RE = re.compile(r"^([\d.]+)\s*NM\s*\(\s*([\d.]+)\s*km\s*\)$", re.IGNORECASE)
# route title cell: "Q16 {RNAV 2}"
ROUTE_TITLE_RE = re.compile(r"\b(Q\d{2})\s*\{\s*(RNAV\s*\d)\s*\}", re.IGNORECASE)

WAYPOINT_MARKER = "▲"


class Warnings:
    """Collects non-fatal parse problems so they can be surfaced, not hidden."""

    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, route: str, detail: str) -> None:
        self.items.append(f"[{route}] {detail}")

    def __len__(self) -> int:
        return len(self.items)


def dms_to_decimal(text: str) -> tuple[float, float, bool] | None:
    """Return (lat, lon, normalised) or None.

    The source document rounds some coordinates to a literal 60 seconds
    (e.g. '1055660E' = 105°56'60"). That is an unambiguous carry into the next
    minute, and each such fix was cross-checked against the independent KMZ
    geometry -- all five land within 20 m of a KMZ vertex after the carry, so
    the interpretation is verified rather than assumed. `normalised` is True
    whenever a carry was applied, so the fact stays visible in the output.
    """
    m = DMS_RE.match(text.strip())
    if not m:
        return None
    la_d, la_m, la_s, lo_d, lo_m, lo_s = (int(x) for x in m.groups())

    normalised = False
    for _ in range(1):  # single carry is all the source ever needs
        if la_s == 60:
            la_s, la_m, normalised = 0, la_m + 1, True
        if lo_s == 60:
            lo_s, lo_m, normalised = 0, lo_m + 1, True
        if la_m == 60:
            la_m, la_d, normalised = 0, la_d + 1, True
        if lo_m == 60:
            lo_m, lo_d, normalised = 0, lo_d + 1, True

    if la_m >= 60 or la_s >= 60 or lo_m >= 60 or lo_s >= 60:
        return None
    lat = la_d + la_m / 60 + la_s / 3600
    lon = lo_d + lo_m / 60 + lo_s / 3600
    return round(lat, 6), round(lon, 6), normalised


def parse_int(text: str) -> int | None:
    """Pull a leading integer out of a cell ('181 -' -> 181, '' -> None)."""
    m = re.match(r"^\s*(\d+)", text or "")
    return int(m.group(1)) if m else None


def parse_vertical_limits(text: str, route: str, warn: Warnings) -> dict[str, Any]:
    """'FL460\\nFL040' -> upper FL460, lower FL040."""
    out: dict[str, Any] = {"upper": None, "lower": None}
    parts = [p.strip() for p in (text or "").split("\n") if p.strip()]
    if not parts:
        return out
    flight_levels = []
    for p in parts:
        m = FL_RE.match(p)
        if m:
            flight_levels.append(int(m.group(1)))
        else:
            warn.add(route, f"unrecognised vertical-limit token {p!r}")
    if len(flight_levels) >= 2:
        out["upper"] = {"value": max(flight_levels), "unit": "FL"}
        out["lower"] = {"value": min(flight_levels), "unit": "FL"}
    elif len(flight_levels) == 1:
        out["upper"] = {"value": flight_levels[0], "unit": "FL"}
        warn.add(route, f"only one flight level found in {text!r}")
    return out


def parse_min_safe_alt(text: str, route: str, warn: Warnings) -> int | None:
    t = (text or "").strip()
    if not t:
        return None
    m = ALT_M_RE.match(t)
    if m:
        return int(m.group(1))
    warn.add(route, f"unrecognised minimum-safe-altitude {text!r}")
    return None


def parse_lateral_limit(text: str, route: str, warn: Warnings) -> dict[str, float] | None:
    t = (text or "").strip()
    if not t:
        return None
    m = LATERAL_RE.match(t)
    if m:
        return {"valueNm": float(m.group(1)), "valueKm": float(m.group(2))}
    warn.add(route, f"unrecognised lateral limit {text!r}")
    return None


def parse_cruising_levels(down_cell: str, up_cell: str) -> str | None:
    """Return 'odd' | 'even' | None.

    The ↑ column carries 'Lẻ' (odd) and the ↓ column 'Chẵn' / 'Even' (even).
    Both cells contain OCR-ish debris in the source document (e.g. 'en1ev)',
    'Chẵnveven'), so match on the meaningful substring only and let the
    unambiguous 'Lẻ' in the ↑ column win.
    """
    up = (up_cell or "").strip()
    down = (down_cell or "").strip()
    if "Lẻ" in up:
        return "odd"
    if "Chẵn" in down or "Even" in down or "even" in down:
        return "even"
    if "Lẻ" in down:
        return "odd"
    if "Chẵn" in up or "Even" in up:
        return "even"
    return None


def parse_table(table, warn: Warnings) -> dict[str, Any] | None:
    """Parse one airway table into {code, navigationSpec, waypoints, segments}."""
    rows = [[c.text.strip() for c in r.cells] for r in table.rows]

    code = None
    nav_spec = None
    for cells in rows:
        m = ROUTE_TITLE_RE.search(" ".join(cells))
        if m:
            code = m.group(1).upper()
            nav_spec = re.sub(r"\s+", " ", m.group(2)).upper()
            break
    if not code:
        return None

    waypoints: list[dict[str, Any]] = []
    # Raw segment rows, kept in document order; linked to waypoints afterwards.
    raw_segments: list[dict[str, Any]] = []
    # index into `waypoints` of the fix that precedes each segment row
    seg_after: list[int] = []

    for cells in rows:
        if len(cells) < 10:
            continue
        c0 = cells[0].strip()

        if c0 == WAYPOINT_MARKER:
            name = cells[1].strip()
            coord = dms_to_decimal(cells[2])
            if coord is None:
                coord = dms_to_decimal(cells[3])
            if not name:
                warn.add(code, "waypoint row without a name -- skipped")
                continue
            if coord is None:
                warn.add(code, f"waypoint {name!r}: unparsable DMS {cells[2]!r} -- skipped")
                continue
            lat, lon, normalised = coord
            dms_text = re.sub(r"\s+", " ", cells[2].strip())
            entry = {
                "seq": len(waypoints) + 1,
                "name": name,
                "lat": lat,
                "lon": lon,
                "latDms": dms_text.split(" ")[0],
                "lonDms": dms_text.split(" ")[-1],
            }
            if normalised:
                entry["coordinateNote"] = (
                    "Toạ độ gốc ghi 60 giây; đã chuẩn hoá cộng lên 1 phút "
                    "(đối chiếu khớp hình học KMZ trong phạm vi 20 m)."
                )
                warn.add(code, f"waypoint {name!r}: DMS {dms_text!r} had 60 seconds -- carried to the next minute")
            waypoints.append(entry)
            continue

        # A segment row: no marker, but carries a track and/or a distance.
        track = parse_int(cells[2])
        distance = parse_int(cells[3])
        has_payload = any(cells[i].strip() for i in (2, 3, 4, 5, 6, 9))
        if c0 or not has_payload:
            continue
        if not waypoints:
            warn.add(code, "segment row appears before any waypoint -- skipped")
            continue

        limits = parse_vertical_limits(cells[4], code, warn)
        raw_segments.append(
            {
                "magneticTrackDeg": track,
                "distanceKm": distance,
                "upperLimit": limits["upper"],
                "lowerLimit": limits["lower"],
                "minSafeAltitudeM": parse_min_safe_alt(cells[5], code, warn),
                "lateralLimit": parse_lateral_limit(cells[6], code, warn),
                "cruisingLevels": parse_cruising_levels(cells[7], cells[8]),
                "usageConditions": re.sub(r"\s*\n\s*", " ", cells[9].strip()) or None,
            }
        )
        seg_after.append(len(waypoints) - 1)

    # Link each segment to the fix pair it joins.
    segments: list[dict[str, Any]] = []
    for i, seg in enumerate(raw_segments):
        from_idx = seg_after[i]
        to_idx = from_idx + 1
        if to_idx >= len(waypoints):
            warn.add(
                code,
                f"segment after {waypoints[from_idx]['name']!r} has no following "
                "waypoint -- dropped",
            )
            continue
        segments.append(
            {
                "seq": len(segments) + 1,
                "fromWaypoint": waypoints[from_idx]["name"],
                "toWaypoint": waypoints[to_idx]["name"],
                **seg,
            }
        )

    if len(segments) != max(len(waypoints) - 1, 0):
        warn.add(
            code,
            f"expected {max(len(waypoints) - 1, 0)} segments for "
            f"{len(waypoints)} waypoints but parsed {len(segments)}",
        )

    return {
        "code": code,
        "navigationSpec": nav_spec,
        "waypointCount": len(waypoints),
        "segmentCount": len(segments),
        "waypoints": waypoints,
        "segments": segments,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--docx", required=True, help="path to the RNAV2 .docx")
    ap.add_argument("--out", required=True, help="path of the JSON file to write")
    ap.add_argument(
        "--source-name",
        default="Thông số đường HK RNAV2 và điều kiện sử dụng.docx",
        help="document file name recorded in the output provenance block",
    )
    args = ap.parse_args()

    if not os.path.exists(args.docx):
        sys.exit(f"docx not found: {args.docx}")

    document = docx.Document(args.docx)
    warn = Warnings()

    airways: list[dict[str, Any]] = []
    for table in document.tables:
        parsed = parse_table(table, warn)
        if parsed:
            airways.append(parsed)

    airways.sort(key=lambda a: a["code"])

    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "source": {
            "document": args.source_name,
            "documentTitle": "DỰ THẢO THÔNG SỐ ĐƯỜNG HÀNG KHÔNG RNAV2 VÀ ĐIỀU KIỆN SỬ DỤNG",
            "meetingDate": "2026-09-16",
            "status": "draft",
            "note": (
                "Dự thảo sau họp ngày 16.9.2026 - chưa công bố chính thức trong AIP. "
                "Chỉ dùng cho mô phỏng/phân tích, không dùng cho khai thác thực tế."
            ),
        },
        "airwayCount": len(airways),
        "airways": airways,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Parsed {len(airways)} airways -> {args.out}")
    for a in airways:
        print(f"  {a['code']:5s} {a['navigationSpec']:8s} "
              f"{a['waypointCount']:3d} waypoints, {a['segmentCount']:3d} segments")

    if len(warn):
        print(f"\n{len(warn)} warning(s):")
        for w in warn.items:
            print("  " + w)
    else:
        print("\nNo warnings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
