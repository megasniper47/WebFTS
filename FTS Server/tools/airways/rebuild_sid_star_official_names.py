"""One-off rebuild of the SID/STAR (PBN only -- see note below) display
features for VVCM/VVDL/VVPQ/VVLT, replacing the KML-graph-split geometry
(which groups multiple distinct real transitions under one ambiguous name,
or in VVCM's case follows the KML's drawn line past the real official
endpoint to an unrelated further fix "TRN") with geometry built directly
from the already-transcribed PDF tabular-description data, using each
transition's REAL AIP designator (e.g. "ATSUK 1D", "BMT 2J", "NUMDI 3D",
"DOVIN 5H") as procedure_name.

Scope, deliberately NOT fabricated beyond:
  - Only PBN (RNP) transitions are rebuilt here. CV (conventional VOR/DME)
    SID/STAR are prose-only in the source PDFs (radial/DME instructions,
    no ARINC-424 tabular leg list) -- there is no reliable waypoint sequence
    to rebuild a LineString from without inventing intermediate points, so
    CV SID/STAR entries are left exactly as currently in the geojson/index
    (still KML-graph-derived, still carrying their pre-existing naming
    quirks) -- not touched, not removed.
  - IAP, HOLDING: untouched.
  - A SID's real initial leg is often "CA"/"heading to altitude" with no
    named fix (pure course off the runway) -- the real runway threshold
    coordinate (published in the same PDF) is used as that leg's start
    point, not invented.

Sources (already transcribed, no new OCR in this script):
  CM, DL: FTS Server/tools/airways/output/vv{cm,dl}_tabular_from_pdf.json
    -- PBN.SID / PBN.STAR dicts are flat {official_name: {runway, legs:[...]}},
    keys ARE already the real AIP designator.
  PQ, LT: WebATM/server/vv{pq,lt}_procedures.py -- SID_TRANSITIONS/
    STAR_TRANSITIONS (already-assembled real waypoint chains, built and
    live-tested earlier this session for scenario generation); mapped here
    to their real AIP designator via the OFFICIAL_NAME dicts below (the
    internal keys like "NUMDI_28" were never meant to BE the display name).
    The STAR dicts are used directly (not through star_route()), since
    star_route() appends the shared IAP final segment for flight-simulation
    purposes -- the real STAR chart itself ends at the hand-off/IAF fix,
    and merging the IAP tail into the STAR's own display would misrepresent
    it as part of the STAR procedure.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

INDEX_PATH = Path(__file__).resolve().parents[3] / "WebATM/static/data/vatm_kmz/procedures_index.json"
GEOJSON_DIR = Path(__file__).resolve().parents[3] / "WebATM/static/data/vatm_kmz/procedures_by_airport"
BACKUP_DIR = Path(__file__).resolve().parents[3] / "WebATM/static/data/vatm_kmz/_backup_procedures_kml_rebuild"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
TODAY = "2026-10-02_official_name_rebuild"


def dms_to_dec(s: str) -> float:
    m = re.match(r"(\d+)[°](\d+)'([\d.]+)\"([NSEW])", s.strip())
    d, mi, se, hemi = m.groups()
    val = float(d) + float(mi) / 60 + float(se) / 3600
    return -val if hemi in ("S", "W") else val


def slugify(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", name.strip())
    return re.sub(r"-+", "-", s).strip("-").upper()


def leg_names(legs: list[dict], runway_threshold_name: str | None) -> list[str]:
    """Ordered list of real fix names for one flat {legs:[...]} entry (CM/DL
    style). The first leg is sometimes a pure course/heading with no named
    fix ("CA"/"VA") -- substituted with the real runway threshold name
    (passed in, resolved by the caller against that airport's own
    waypoints dict) rather than dropped or invented."""
    names: list[str] = []
    for i, leg in enumerate(legs):
        wp = leg.get("waypoint")
        if wp:
            names.append(wp)
        elif i == 0 and runway_threshold_name:
            names.append(runway_threshold_name)
    return names


def build_cm_dl(icao: str, json_path: Path, runway_wp_name: dict[str, str]) -> tuple[dict[str, dict[str, list[str]]], dict[str, tuple[float, float]]]:
    """Returns ({ptype: {official_name: [fix_name,...]}}, {fix_name: (lat,lon)})
    for CM/DL's flat-entry PBN.SID/PBN.STAR structure."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    coords = {name: (dms_to_dec(v["lat"]), dms_to_dec(v["lon"])) for name, v in data["waypoints"].items() if v.get("lat") and v.get("lon")}

    result: dict[str, dict[str, list[str]]] = {"SID": {}, "STAR": {}}
    for ptype in ("SID", "STAR"):
        for name, entry in data.get("PBN", {}).get(ptype, {}).items():
            if not isinstance(entry, dict) or "legs" not in entry:
                continue  # skip non-procedure keys like "holding_rwy09"
            rwy = entry.get("runway", "")
            thr_name = runway_wp_name.get(rwy)
            names = leg_names(entry["legs"], thr_name)
            if len(names) >= 2:
                result[ptype][name] = names
    return result, coords


def build_from_procedures_module(module_name: str, official_name_of: dict[str, dict[str, str]]) -> tuple[dict[str, dict[str, list[str]]], dict[str, tuple[float, float]]]:
    """Returns the same shape as build_cm_dl, but sourced from an already-
    assembled vv{pq,lt}_procedures.py module's SID_TRANSITIONS/
    STAR_TRANSITIONS dicts (list of (name, alt[, spd]) tuples) -- these
    already resolved every real waypoint chain correctly (including the
    CA-initial-leg/runway-threshold substitution) when they were built
    earlier this session for scenario generation."""
    import importlib
    mod = importlib.import_module(module_name)
    coords = dict(mod._WP_COORDS)

    result: dict[str, dict[str, list[str]]] = {"SID": {}, "STAR": {}}
    for ptype, transitions_attr in (("SID", "SID_TRANSITIONS"), ("STAR", "STAR_TRANSITIONS")):
        transitions = getattr(mod, transitions_attr)
        name_map = official_name_of[ptype]
        for key, legs in transitions.items():
            official = name_map.get(key)
            if not official:
                continue  # no known real AIP designator for this internal key -- skip, do not guess
            names = [leg[0] for leg in legs]
            result[ptype][official] = names
    return result, coords


# Real AIP designators for VVPQ's internal SID_TRANSITIONS/STAR_TRANSITIONS
# keys (vvpq_procedures.py) -- transcribed from "2026.08.06 Dự thảo PD2 QĐ
# PTB PBN tại sân bay PQ.pdf" earlier this session.
PQ_OFFICIAL_NAMES = {
    "SID": {
        "NUMDI": "NUMDI 3D", "OSOTA": "OSOTA 3D", "RG": "RG 3D", "ADBOP": "ADBOP 3D",
        "NUMDI_28": "NUMDI 3E", "OSOTA_28": "OSOTA 3E", "RG_28A": "RG 3E", "RG_28B": "RG 3F", "ADBOP_28": "ADBOP 3E",
    },
    "STAR": {
        "NUMDI": "NUMDI 3F", "OSOTA": "OSOTA 3F", "TUNPO": "TUNPO 3F", "ADBOP": "ADBOP 3F",
        "NUMDI_28": "NUMDI 3G", "OSOTA_28": "OSOTA 3G", "TUNPO_28": "TUNPO 3G", "ADBOP_28": "ADBOP 3G",
    },
}

# Real AIP designators for VVLT's internal SID_TRANSITIONS/STAR_TRANSITIONS
# keys (vvlt_procedures.py) -- transcribed from "SID VVLT Coding 1/2/3.pdf",
# the STAR "...Coding.pdf" set, and "PD2 Sơ đồ PBN.pdf" pages 1-15.
LT_OFFICIAL_NAMES = {
    "SID": {
        "PATMA_23": "PATMA 5C", "DOVIN_23": "DOVIN 5F", "BIXEX_23": "BIXEX 5D", "PTH_23": "PTH 5E",
        "PATMA2_23": "PATMA 5D", "ANBOV_23": "ANBOV 5C", "TRN_23": "TRN 5D", "POTIX_23": "POTIX 5A",
        "ATGAS_23": "ATGAS 5A", "SAPEN_23": "SAPEN 5C",
        "PATMA_05": "PATMA 5H", "DOVIN_05": "DOVIN 5R", "BIXEX_05": "BIXEX 5L", "PTH_05N": "PTH 5N",
        "PTH_05P": "PTH 5P", "ELSAS_05": "ELSAS 5H", "NIXIV_05": "NIXIV 5K", "ANHOA_05": "ANHOA 5D",
        "ENPAS_05": "ENPAS 5D", "POTIX_05": "POTIX 5C", "ATGAS_05": "ATGAS 5C", "SAPEN_05": "SAPEN 5H",
    },
    "STAR": {
        "DOVIN_23": "DOVIN 5H", "VETOM_23": "VETOM 5B", "PTH_23": "PTH 5G", "DAGAG_23": "DAGAG 5A",
        "NIXIV_23": "NIXIV 5D", "TRN_23": "TRN 5E", "ANBOV_23": "ANBOV 5D", "SAPEN_23": "SAPEN 5D",
        "DOVIN_05": "DOVIN 5S", "VETOM_05": "VETOM 5D", "PTH_05": "PTH 5Q", "ELSAS_05": "ELSAS 5J",
        "NIXIV_05": "NIXIV 5L", "TRN_05": "TRN 5L", "ANBOV_05": "ANBOV 5F", "SAPEN_05": "SAPEN 5J",
    },
}


def make_features(icao: str, by_type: dict[str, dict[str, list[str]]], coords: dict[str, tuple[float, float]]) -> tuple[list[dict], dict[str, dict[str, list[str]]], list[str]]:
    features = []
    fragment: dict[str, dict[str, list[str]]] = {"SID": {}, "STAR": {}}
    missing: list[str] = []
    seq = defaultdict(int)
    for ptype, names_dict in by_type.items():
        for proc_name, fix_names in names_dict.items():
            pts = []
            ok = True
            for fn in fix_names:
                if fn not in coords:
                    missing.append(f"{icao}/{ptype}/{proc_name}: missing coords for {fn!r}")
                    ok = False
                    break
                lat, lon = coords[fn]
                pts.append((lon, lat))
            if not ok or len(pts) < 2:
                continue
            key = (ptype, proc_name)
            for a, b in zip(pts, pts[1:]):
                seq[key] += 1
                fid = f"{icao}_{ptype}_{slugify(proc_name)}_{seq[key]:03d}"
                features.append({
                    "type": "Feature",
                    "properties": {
                        "id": fid, "name": proc_name,
                        "folder_path": f"{icao}/{ptype}/{proc_name}",
                        "airport_icao": icao, "procedure_type": ptype, "procedure_name": proc_name,
                    },
                    "geometry": {"type": "LineString", "coordinates": [[a[0], a[1], 0.0], [b[0], b[1], 0.0]]},
                })
                fragment[ptype].setdefault(proc_name, []).append(fid)
    return features, fragment, missing


def rebuild_airport(icao: str, by_type, coords, index: dict):
    """Mutates `index` in place for this icao; writes/backs up only this
    airport's own geojson file (index.json itself is backed up/written once
    in main() after every airport has been merged into `index`)."""
    features, fragment, missing = make_features(icao, by_type, coords)
    geojson_path = GEOJSON_DIR / f"vatm_procedures_{icao}.geojson"
    with open(geojson_path, encoding="utf-8") as f:
        old_geojson = json.load(f)
    keep = [feat for feat in old_geojson["features"] if feat["properties"].get("procedure_type") not in ("SID", "STAR")]
    # CV SID/STAR (not rebuilt here, see module docstring) are kept as-is --
    # they're still typed "SID"/"STAR" in the old data, so re-select them
    # back in by checking their procedure_name for the "CV" marker already
    # present in every CV-sourced entry's qualified name.
    cv_kept = [feat for feat in old_geojson["features"]
               if feat["properties"].get("procedure_type") in ("SID", "STAR")
               and "CV" in feat["properties"].get("procedure_name", "")]
    merged = keep + cv_kept + features
    shutil.copy(geojson_path, BACKUP_DIR / f"vatm_procedures_{icao}.geojson.bak_{TODAY}")
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": merged}, f, ensure_ascii=False)

    old_entry = index.get(icao, {})
    # Keep CV SID/STAR + untouched IAP/HOLDING sections; replace only the
    # PBN-rebuilt SID/STAR names.
    cv_sid = {k: v for k, v in old_entry.get("SID", {}).items() if "CV" in k}
    cv_star = {k: v for k, v in old_entry.get("STAR", {}).items() if "CV" in k}
    index[icao] = {
        "HOLDING": old_entry.get("HOLDING", {}),
        "SID": {**cv_sid, **fragment["SID"]},
        "STAR": {**cv_star, **fragment["STAR"]},
        "IAP": old_entry.get("IAP", {}),
    }
    return missing


def main():
    kml_missing_report = []

    with open(INDEX_PATH, encoding="utf-8") as f:
        index = json.load(f)
    shutil.copy(INDEX_PATH, BACKUP_DIR / f"procedures_index.json.bak_{TODAY}")

    # --- CM ---
    cm_by_type, cm_coords = build_cm_dl("VVCM", Path(__file__).parent / "output/vvcm_tabular_from_pdf.json", {"09": "RWY09", "27": "RWY27"})
    kml_missing_report += rebuild_airport("VVCM", cm_by_type, cm_coords, index)

    # --- DL ---
    dl_by_type, dl_coords = build_cm_dl("VVDL", Path(__file__).parent / "output/vvdl_tabular_from_pdf.json", {"09": "RWY09", "27": None})
    kml_missing_report += rebuild_airport("VVDL", dl_by_type, dl_coords, index)

    # --- PQ ---
    pq_by_type, pq_coords = build_from_procedures_module("WebATM.server.vvpq_procedures", PQ_OFFICIAL_NAMES)
    kml_missing_report += rebuild_airport("VVPQ", pq_by_type, pq_coords, index)

    # --- LT ---
    lt_by_type, lt_coords = build_from_procedures_module("WebATM.server.vvlt_procedures", LT_OFFICIAL_NAMES)
    kml_missing_report += rebuild_airport("VVLT", lt_by_type, lt_coords, index)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)

    for icao in ("VVCM", "VVDL", "VVPQ", "VVLT"):
        print(f"{icao}: SID={len(index[icao]['SID'])} STAR={len(index[icao]['STAR'])}")
        for ptype in ("SID", "STAR"):
            for name in sorted(index[icao][ptype]):
                print(f"   {ptype} {name!r}")

    if kml_missing_report:
        print(f"\n{len(kml_missing_report)} fix(es) with no coordinate (skipped, not guessed):")
        for m in kml_missing_report:
            print(" ", m)
    else:
        print("\nNo missing coordinates.")


if __name__ == "__main__":
    main()
