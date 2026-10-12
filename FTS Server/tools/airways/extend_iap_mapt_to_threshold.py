"""Extends a handful of already-rebuilt IAP final segments that stop at a
published MAPT which sits short of the real runway threshold, instead of
continuing to it -- user-reported visual gap on VVPQ's RNP Z RWY10L.

Root cause confirmed from the source PDF tabular data: for most approaches
the transcribed MAPT fix *is* the runway threshold itself (e.g. VVCM's
"RWY09 (MAPT)", VVPQ's "RW28L (MAPT)") -- no gap. But a few publish a MAPT
offset from the threshold (VVPQ's PQ400/PQ401 ~0.9NM short; VVDL's DL922
~1NM short), and VVDL's two ILS entries don't carry a leg-level final
segment at all (ILS guidance isn't a waypoint-to-waypoint leg -- only the
FAP is published, e.g. DL900). In every one of these cases the real,
already-transcribed runway-threshold coordinate (RWY09/RWY27/RW10L/RW10R)
was sitting unused in the same waypoints dict.

Fix, confirmed with the user: append one more real segment, MAPT (or FAP)
-> threshold, using only already-transcribed threshold coordinates -- never
inventing a position. This is a pure visual completion to the runway, not
a new IFR procedure leg.

Bonus: VVCM's "ILS Y RWY27" was skipped entirely in the earlier IAP rebuild
(rebuild_iap_cm_dl_lt.py) for lacking a leg-level final segment -- its
source only has initial_approach_entries + abstract final_approach_waypoints
flags. Re-reading the data shows it shares the EXACT SAME convergence fix
(CM722) as "RNP Z RWY27", which does have a full final segment
(CM722->CM721->RWY27). Since both procedures share one physical final
track to the same runway (confirmed, not assumed, by the identical IF
waypoint/course/distance), it's now rebuilt by combining its own two real
initial-approach branches with RNP Z RWY27's already-verified final
segment -- not a guess.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GEOJSON_DIR = ROOT / "WebATM/static/data/vatm_kmz/procedures_by_airport"
INDEX_PATH = ROOT / "WebATM/static/data/vatm_kmz/procedures_index.json"
BACKUP_DIR = ROOT / "WebATM/static/data/vatm_kmz/_backup_procedures_kml_rebuild"
TODAY = "2026-10-02_extend_iap_mapt_to_threshold"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def dms_to_dec(s: str) -> float:
    m = re.match(r"(\d+)[°](\d+)'([\d.]+)\"([NSEW])", s.strip())
    d, mi, se, hemi = m.groups()
    val = float(d) + float(mi) / 60 + float(se) / 3600
    return -val if hemi in ("S", "W") else val


def slugify(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", name.strip())
    return re.sub(r"-+", "-", s).strip("-").upper()


def wp_name(raw: str | None) -> str | None:
    if not raw:
        return None
    return re.sub(r"\s*\(MAPT\)\s*$", "", raw).strip()


def load_coords(json_path: Path) -> dict[str, tuple[float, float]]:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return {name: (dms_to_dec(v["lat"]), dms_to_dec(v["lon"]))
            for name, v in data["waypoints"].items() if v.get("lat") and v.get("lon")}, data


class AirportPatcher:
    def __init__(self, icao: str, coords: dict[str, tuple[float, float]]):
        self.icao = icao
        self.coords = coords
        self.new_features: list[dict] = []
        self.fragment_adds: dict[str, list[str]] = {}

    def _next_seq(self, gj_features: list[dict], proc_name: str) -> int:
        existing = [f for f in gj_features
                    if f["properties"].get("procedure_type") == "IAP"
                    and f["properties"].get("procedure_name") == proc_name]
        return len(existing) + 1

    def append_leg(self, gj_features: list[dict], proc_name: str, a: str, b: str):
        if a not in self.coords or b not in self.coords:
            missing = a if a not in self.coords else b
            print(f"  SKIP {self.icao}/{proc_name}: missing coords for {missing!r}")
            return
        lat1, lon1 = self.coords[a]
        lat2, lon2 = self.coords[b]
        seq = self._next_seq(gj_features, proc_name) + len(self.fragment_adds.get(proc_name, []))
        fid = f"{self.icao}_IAP_{slugify(proc_name)}_{seq:03d}"
        feat = {
            "type": "Feature",
            "properties": {
                "id": fid, "name": f"{a}-{b}",
                "folder_path": f"{self.icao}/IAP/{proc_name}",
                "airport_icao": self.icao, "procedure_type": "IAP", "procedure_name": proc_name,
            },
            "geometry": {"type": "LineString", "coordinates": [[lon1, lat1, 0.0], [lon2, lat2, 0.0]]},
        }
        self.new_features.append(feat)
        self.fragment_adds.setdefault(proc_name, []).append(fid)

    def append_chain(self, gj_features: list[dict], proc_name: str, names: list[str]):
        for a, b in zip(names, names[1:]):
            self.append_leg(gj_features, proc_name, a, b)

    def apply(self):
        geojson_path = GEOJSON_DIR / f"vatm_procedures_{self.icao}.geojson"
        with open(geojson_path, encoding="utf-8") as f:
            gj = json.load(f)
        shutil.copy(geojson_path, BACKUP_DIR / f"vatm_procedures_{self.icao}.geojson.bak_{TODAY}")

        self.extend(gj["features"])

        gj["features"] += self.new_features
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(gj, f, ensure_ascii=False)

        with open(INDEX_PATH, encoding="utf-8") as f:
            index = json.load(f)
        shutil.copy(INDEX_PATH, BACKUP_DIR / f"procedures_index.json.bak_{TODAY}")
        iap = index[self.icao]["IAP"]
        for name, ids in self.fragment_adds.items():
            iap.setdefault(name, [])
            iap[name] += ids
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=1)

        print(f"{self.icao}: added {sum(len(v) for v in self.fragment_adds.values())} feature(s) "
              f"to {sorted(self.fragment_adds.keys())}")

    def extend(self, gj_features: list[dict]):
        raise NotImplementedError


class PatchVVPQ(AirportPatcher):
    def extend(self, gj_features):
        self.append_chain(gj_features, "RNP Z RWY10L", ["PQ400", "RW10L"])
        self.append_chain(gj_features, "RNP Z RWY10R", ["PQ401", "RW10R"])


class PatchVVDL(AirportPatcher):
    def extend(self, gj_features):
        self.append_chain(gj_features, "RNP Z RWY09", ["DL922", "RWY09"])
        self.append_chain(gj_features, "RNP Y RWY09", ["DL922", "RWY09"])
        self.append_chain(gj_features, "ILS W RWY09", ["DL900", "RWY09"])
        self.append_chain(gj_features, "ILS X RWY09", ["DL900", "RWY09"])


class PatchVVCM(AirportPatcher):
    def __init__(self, icao, coords, ils_y_rwy27_entry, rnp_z_rwy27_final_names):
        super().__init__(icao, coords)
        self.entry = ils_y_rwy27_entry
        self.final_names = rnp_z_rwy27_final_names

    def extend(self, gj_features):
        proc_name = "ILS Y RWY27"
        for branch in self.entry["initial_approach_entries"]:
            names = [wp_name(leg.get("waypoint")) for leg in branch if wp_name(leg.get("waypoint"))]
            self.append_chain(gj_features, proc_name, names)
        self.append_chain(gj_features, proc_name, self.final_names)


def truncate_at_mapt(legs: list[dict]) -> list[str]:
    names = []
    for leg in legs:
        n = wp_name(leg.get("waypoint"))
        if n:
            names.append(n)
        if str(leg.get("waypoint", "")).endswith("(MAPT)"):
            break
    return names


def main():
    coords_pq, _ = load_coords(OUTPUT_DIR / "vvpq_tabular_from_pdf_pbn.json")
    PatchVVPQ("VVPQ", coords_pq).apply()

    coords_dl, _ = load_coords(OUTPUT_DIR / "vvdl_tabular_from_pdf.json")
    PatchVVDL("VVDL", coords_dl).apply()

    coords_cm, data_cm = load_coords(OUTPUT_DIR / "vvcm_tabular_from_pdf.json")
    ils_y_rwy27 = data_cm["PBN"]["IAP"]["ILS Y RWY27"]
    rnp_z_rwy27_final = truncate_at_mapt(data_cm["PBN"]["IAP"]["RNP Z RWY27"]["final_and_missed"])
    PatchVVCM("VVCM", coords_cm, ils_y_rwy27, rnp_z_rwy27_final).apply()


if __name__ == "__main__":
    main()
