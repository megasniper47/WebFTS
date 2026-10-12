"""One-off re-run of parse_procedures_kml.py for CM/DL/LT/PQ after the
cross-boundary-leaf-name collision fix, merging the new SID/STAR/IAP
features back in with each airport's existing HOLDING data (untouched),
backing up the previous geojson/index first.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from parse_procedures_kml import extract, scan_boundaries

KML = "../../../vietnam_ats_routes_pack/Dữ liệu PTB SID STAR IAP Mới 19.9.2026/PHƯƠNG THỨC BAY (SID, STAR, IAP).kml"
KML_ALT = "../../../vietnam_ats_routes_pack/Dữ liệu PTB + code/PTB SID STAR IAP Mới 19.9.2026/PHƯƠNG THỨC BAY (SID, STAR, IAP).kml"
GEOJSON_DIR = Path("../../../WebATM/static/data/vatm_kmz/procedures_by_airport")
INDEX_PATH = Path("../../../WebATM/static/data/vatm_kmz/procedures_index.json")
BACKUP_DIR = Path("../../../WebATM/static/data/vatm_kmz/_backup_procedures_kml_rebuild")
TODAY = "2026-10-02_star_root_naming_fix"

AIRPORTS = [
    ("VVCM", "VVCM"),
    ("VVDL", "VVDL (Hiệu lực TỪ 00h01 (HN) 01/10/26)"),
    ("VVLT", "VVLT"),
    ("VVPQ", "VVPQ (Hiệu lực TỪ 07h00 (HN) 01/10/26)"),
]


def main():
    import os
    kml_path = KML if os.path.exists(KML) else KML_ALT
    assert os.path.exists(kml_path), f"KML not found at either {KML} or {KML_ALT}"

    with open(INDEX_PATH, encoding="utf-8") as f:
        index = json.load(f)

    for icao, airport_folder in AIRPORTS:
        geojson_path = GEOJSON_DIR / f"vatm_procedures_{icao}.geojson"
        with open(geojson_path, encoding="utf-8") as f:
            old_geojson = json.load(f)
        holding_features = [feat for feat in old_geojson["features"] if feat["properties"].get("procedure_type") == "HOLDING"]

        shutil.copy(geojson_path, BACKUP_DIR / f"vatm_procedures_{icao}.geojson.bak_{TODAY}")

        boundary_flags = scan_boundaries(kml_path, airport_folder)
        new_geojson, fragment, diagnostics = extract(kml_path, airport_folder, icao, boundary_flags)

        merged_features = new_geojson["features"] + holding_features
        merged_geojson = {"type": "FeatureCollection", "features": merged_features}
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(merged_geojson, f, ensure_ascii=False)

        holding_entry = index.get(icao, {}).get("HOLDING", {})
        index[icao] = {"HOLDING": holding_entry, **fragment}

        print(f"\n=== {icao} ===")
        for ptype in ("SID", "STAR", "IAP"):
            names = fragment.get(ptype, {})
            print(f"  {ptype}: {len(names)} procedure(s)")
        if diagnostics:
            for d in diagnostics:
                print(f"  {d}")

    shutil.copy(INDEX_PATH, BACKUP_DIR / f"procedures_index.json.bak_{TODAY}")
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)

    print("\nDone. Backups written with suffix", TODAY)


if __name__ == "__main__":
    main()
