"""One-off removal of CV (conventional VOR/DME) SID/STAR entries from
VVDL/VVPQ's display data. These were kept as-is during the official-name
rebuild (rebuild_sid_star_official_names.py) because the source PDFs
describe them in prose (radial/DME instructions), not an ARINC-424 leg
table -- but the underlying KML geometry for them turns out to be
fundamentally unreliable to redraw as a connected line: their "VA"/"VI"
root-marker legs (course-only, no fix) are real duplicated trunk segments
from multiple distinct real transitions bundled in one Document, with no
real waypoint sequence tying them together -- confirmed live (VVPQ's
"ADBOP (SID 10 CV)" draws 19 disconnected/overlapping segments, several
literally labeled "VA-#1".."VI-#4", not real fix names).

Removed entirely (not renamed, not kept) rather than displayed broken --
PBN already has a real, correctly-named, correctly-connected feature for
the same airports/runways (e.g. VVPQ's "ADBOP 3D"/"ADBOP 3E"), so no
coverage is lost, only the broken conventional duplicate.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GEOJSON_DIR = ROOT / "WebATM/static/data/vatm_kmz/procedures_by_airport"
INDEX_PATH = ROOT / "WebATM/static/data/vatm_kmz/procedures_index.json"
BACKUP_DIR = ROOT / "WebATM/static/data/vatm_kmz/_backup_procedures_kml_rebuild"
TODAY = "2026-10-02_remove_broken_cv_sid_star"

AIRPORTS = ["VVDL", "VVPQ"]


def is_cv_sid_star(props: dict) -> bool:
    return props.get("procedure_type") in ("SID", "STAR") and "CV" in (props.get("procedure_name") or "")


def main():
    with open(INDEX_PATH, encoding="utf-8") as f:
        index = json.load(f)
    shutil.copy(INDEX_PATH, BACKUP_DIR / f"procedures_index.json.bak_{TODAY}")

    for icao in AIRPORTS:
        geojson_path = GEOJSON_DIR / f"vatm_procedures_{icao}.geojson"
        with open(geojson_path, encoding="utf-8") as f:
            gj = json.load(f)
        before = len(gj["features"])
        gj["features"] = [feat for feat in gj["features"] if not is_cv_sid_star(feat["properties"])]
        removed = before - len(gj["features"])

        shutil.copy(geojson_path, BACKUP_DIR / f"vatm_procedures_{icao}.geojson.bak_{TODAY}")
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(gj, f, ensure_ascii=False)

        for ptype in ("SID", "STAR"):
            removed_names = [k for k in index[icao].get(ptype, {}) if "CV" in k]
            for name in removed_names:
                del index[icao][ptype][name]
            print(f"{icao} {ptype}: removed {removed_names}")
        print(f"{icao}: removed {removed} geojson feature(s)")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
