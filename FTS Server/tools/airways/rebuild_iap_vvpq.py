"""One-off rebuild of VVPQ's IAP (instrument approach) display features,
replacing the KML-graph-split geometry -- which named every approach by its
converging LEAF (the runway threshold itself, e.g. "THR (LNAV 10L)"), the
same root-vs-leaf naming direction bug already fixed for STAR -- with
geometry built from the already-transcribed PDF tabular data, using the
real AIP designator (e.g. "RNP Z RWY10L", "ILS Y RWY28R") as procedure_name.

Source: FTS Server/tools/airways/output/vvpq_tabular_from_pdf_pbn.json's
"IAP" dict. Each approach publishes several real initial-approach entries
(different real IAFs, e.g. GUKNU/LASOV/MEKAV) that converge onto ONE shared
final segment to the runway -- same real-world shape as VVDN's existing
IAP entries (one chart name covers the whole approach, IAF branches
included). Missed-approach legs (after the MAPT) are real but represent a
different-flown-path contingency procedure, not part of the inbound track
shown elsewhere in this project (VVNB/VVDN/VVGB's own IAP entries stop at
the runway too) -- intentionally excluded here, not merged into the same
feature set as the approach itself.

Scope: VVPQ only (the airport flagged this round). CM/DL/LT's IAP geojson
is a separate, not-yet-investigated case -- left untouched.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JSON_PATH = Path(__file__).resolve().parent / "output/vvpq_tabular_from_pdf_pbn.json"
GEOJSON_PATH = ROOT / "WebATM/static/data/vatm_kmz/procedures_by_airport/vatm_procedures_VVPQ.geojson"
INDEX_PATH = ROOT / "WebATM/static/data/vatm_kmz/procedures_index.json"
BACKUP_DIR = ROOT / "WebATM/static/data/vatm_kmz/_backup_procedures_kml_rebuild"
TODAY = "2026-10-02_iap_official_name_rebuild_vvpq"


def dms_to_dec(s: str) -> float:
    m = re.match(r"(\d+)[°](\d+)'([\d.]+)\"([NSEW])", s.strip())
    d, mi, se, hemi = m.groups()
    val = float(d) + float(mi) / 60 + float(se) / 3600
    return -val if hemi in ("S", "W") else val


def slugify(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", name.strip())
    return re.sub(r"-+", "-", s).strip("-").upper()


def wp_name(raw: str | None) -> str | None:
    """Strip a trailing " (MAPT)" annotation off a waypoint name, e.g.
    "PQ400 (MAPT)" -> "PQ400" -- both refer to the same real, already-
    coordinated fix; the annotation is metadata (missed-approach-point),
    not a different name."""
    if not raw:
        return None
    return re.sub(r"\s*\(MAPT\)\s*$", "", raw).strip()


def branch_names(legs: list[dict]) -> list[str]:
    names = []
    for leg in legs:
        n = wp_name(leg.get("waypoint"))
        if n:
            names.append(n)
    return names


def final_segment_names(entry: dict, runway_from_name: str) -> list[str]:
    """Real final-approach-track waypoint names, stopping at the MAPT (not
    following the missed-approach legs after it)."""
    if "final_and_missed" in entry:
        names = []
        for leg in entry["final_and_missed"]:
            n = wp_name(leg.get("waypoint"))
            if n:
                names.append(n)
            if leg.get("waypoint", "").endswith("(MAPT)"):
                break
        return names
    # ILS Y RWY28R style: no explicit final-segment leg list captured, but
    # the real IF/FAF fix names ARE known (if_fix/faf_fap) plus the runway
    # threshold itself -- same 3 real points the other approaches' final
    # segments have (IF -> FAF -> MAPT/threshold), not invented.
    if "if_fix" in entry and "faf_fap" in entry:
        return [entry["if_fix"]["waypoint"], entry["faf_fap"]["waypoint"], runway_from_name]
    return []


def main():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    coords = {name: (dms_to_dec(v["lat"]), dms_to_dec(v["lon"])) for name, v in data["waypoints"].items() if v.get("lat") and v.get("lon")}

    missing: list[str] = []
    features = []
    fragment: dict[str, list[str]] = {}
    seq = defaultdict(int)

    def emit_leg(proc_name: str, a: str, b: str):
        if a not in coords:
            missing.append(f"{proc_name}: missing coords for {a!r}")
            return
        if b not in coords:
            missing.append(f"{proc_name}: missing coords for {b!r}")
            return
        lat1, lon1 = coords[a]
        lat2, lon2 = coords[b]
        seq[proc_name] += 1
        fid = f"VVPQ_IAP_{slugify(proc_name)}_{seq[proc_name]:03d}"
        features.append({
            "type": "Feature",
            "properties": {
                "id": fid, "name": proc_name,
                "folder_path": f"VVPQ/IAP/{proc_name}",
                "airport_icao": "VVPQ", "procedure_type": "IAP", "procedure_name": proc_name,
            },
            "geometry": {"type": "LineString", "coordinates": [[lon1, lat1, 0.0], [lon2, lat2, 0.0]]},
        })
        fragment.setdefault(proc_name, []).append(fid)

    for proc_name, entry in data["IAP"].items():
        runway_token = re.search(r"RWY?(\d{2}[LRC]?)", proc_name)
        runway_from_name = f"RW{runway_token.group(1)}" if runway_token else ""

        entries_key = "initial_entries" if "initial_entries" in entry else "initial_approach_entries"
        for branch in entry.get(entries_key, []):
            names = branch_names(branch)
            for a, b in zip(names, names[1:]):
                emit_leg(proc_name, a, b)

        final_names = final_segment_names(entry, runway_from_name)
        for a, b in zip(final_names, final_names[1:]):
            emit_leg(proc_name, a, b)

    # Merge into the existing geojson/index: replace only IAP entries that
    # are being rebuilt (the 5 real PBN approach charts); keep everything
    # else (SID/STAR already rebuilt earlier, HOLDING, and any other IAP
    # entry not covered by this PDF transcription, e.g. VOR/LNAV CV-side
    # charts) exactly as-is.
    rebuilt_names = set(data["IAP"].keys())

    with open(GEOJSON_PATH, encoding="utf-8") as f:
        gj = json.load(f)
    shutil.copy(GEOJSON_PATH, BACKUP_DIR / f"vatm_procedures_VVPQ.geojson.bak_{TODAY}")
    kept = [feat for feat in gj["features"]
            if not (feat["properties"].get("procedure_type") == "IAP" and feat["properties"].get("procedure_name") in rebuilt_names)]
    # Also drop the old leaf-named "THR (LNAV ...)" entries -- same real
    # approach charts, now replaced by their correct AIP names above.
    kept = [feat for feat in kept
            if not (feat["properties"].get("procedure_type") == "IAP" and str(feat["properties"].get("procedure_name", "")).startswith("THR (LNAV"))]
    gj["features"] = kept + features
    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False)

    with open(INDEX_PATH, encoding="utf-8") as f:
        index = json.load(f)
    shutil.copy(INDEX_PATH, BACKUP_DIR / f"procedures_index.json.bak_{TODAY}")
    iap = index["VVPQ"]["IAP"]
    for name in list(iap.keys()):
        if name in rebuilt_names or str(name).startswith("THR (LNAV"):
            del iap[name]
    iap.update(fragment)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)

    print("VVPQ IAP rebuilt:", sorted(fragment.keys()))
    print("Remaining VVPQ IAP (not touched):", sorted(k for k in index["VVPQ"]["IAP"] if k not in fragment))
    if missing:
        print(f"\n{len(missing)} missing-coordinate warning(s) (skipped, not guessed):")
        for m in missing:
            print(" ", m)


if __name__ == "__main__":
    main()
