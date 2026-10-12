"""Same IAP rebuild as rebuild_iap_vvpq.py, applied to VVCM/VVDL/VVLT --
see that script's module docstring for the shared root cause (approach
procedures were named by their converging LEAF, i.e. the runway threshold
or an internal KML waypoint code, instead of the real AIP chart name).

Per-airport scope, each limited by what was actually transcribed from the
source PDFs this project has (never fabricated beyond):

  VVCM: PBN only -- "RNP Z RWY09", "RNP Z RWY27" (clean initial_entries +
    final_and_missed leg tables). "ILS Y RWY27" is SKIPPED: the source only
    captured its initial-approach branches plus an abstract
    final_approach_waypoints flag dict (which fix the ILS references, not
    an ordered leg table), so there's no real leg-by-leg sequence to redraw
    its final segment from without guessing. CV (VOR Z RWY09/27, ILS Z
    RWY27) is prose-only, same as every other airport's CV SID/STAR --
    not rebuilt, old entries removed (same decision as VVPQ's CV SID/STAR).

  VVDL: PBN only -- "RNP Z RWY09", "RNP Y RWY09", "RNP Z RWY27",
    "RNP Y RWY27", "ILS W RWY09", "ILS X RWY09" (the source notes ILS
    W/ILS X publish identical real waypoints/coordinates -- both real chart
    names, so the same geometry is emitted under each, not picking one
    arbitrarily). CV (VOR Z RWY09/27, ILS Z RWY09) is prose-only, removed.

  VVLT: CV only -- no PBN IAP data was ever OCR'd for VVLT (the 28
    remaining approach-chart pages were explicitly left un-transcribed
    earlier this session). The 7 CV entries (VOR Z RWY05R/23L/23R, ILS Y
    RWY05L/05R/23L/23R) DO have 2 real points each (IAF = LTH VOR/DME, FAF
    = a real transcribed lat/lon) -- rebuilt as a 2-point IAF->FAF line
    only. The MAPT/runway-threshold coordinate was never published with an
    absolute lat/lon in the source (only DME distance from LTH), so the
    line intentionally stops at the FAF rather than guessing a threshold
    position.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GEOJSON_DIR = ROOT / "WebATM/static/data/vatm_kmz/procedures_by_airport"
INDEX_PATH = ROOT / "WebATM/static/data/vatm_kmz/procedures_index.json"
BACKUP_DIR = ROOT / "WebATM/static/data/vatm_kmz/_backup_procedures_kml_rebuild"
TODAY = "2026-10-02_iap_official_name_rebuild_cm_dl_lt"
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


def truncate_at_mapt(legs: list[dict]) -> list[str]:
    """Ordered real fix names, stopping right after the first MAPT entry
    (never following the missed-approach-to-hold legs after it)."""
    names = []
    for leg in legs:
        n = wp_name(leg.get("waypoint"))
        if n:
            names.append(n)
        if str(leg.get("waypoint", "")).endswith("(MAPT)"):
            break
    return names


class Rebuilder:
    def __init__(self, icao: str, coords: dict[str, tuple[float, float]]):
        self.icao = icao
        self.coords = coords
        self.features: list[dict] = []
        self.fragment: dict[str, list[str]] = {}
        self.seq: dict[str, int] = defaultdict(int)
        self.missing: list[str] = []

    def emit_leg(self, proc_name: str, a: str, b: str):
        if a not in self.coords or b not in self.coords:
            missing_name = a if a not in self.coords else b
            self.missing.append(f"{self.icao}/{proc_name}: missing coords for {missing_name!r}")
            return
        lat1, lon1 = self.coords[a]
        lat2, lon2 = self.coords[b]
        self.seq[proc_name] += 1
        fid = f"{self.icao}_IAP_{slugify(proc_name)}_{self.seq[proc_name]:03d}"
        self.features.append({
            "type": "Feature",
            "properties": {
                "id": fid, "name": proc_name,
                "folder_path": f"{self.icao}/IAP/{proc_name}",
                "airport_icao": self.icao, "procedure_type": "IAP", "procedure_name": proc_name,
            },
            "geometry": {"type": "LineString", "coordinates": [[lon1, lat1, 0.0], [lon2, lat2, 0.0]]},
        })
        self.fragment.setdefault(proc_name, []).append(fid)

    def emit_chain(self, proc_name: str, names: list[str]):
        for a, b in zip(names, names[1:]):
            self.emit_leg(proc_name, a, b)

    def rebuild_pbn_entry(self, proc_name: str, entry: dict):
        branches_key = next((k for k in ("initial_entries", "initial_approach_entries") if k in entry), None)
        if branches_key:
            for branch in entry[branches_key]:
                self.emit_chain(proc_name, truncate_at_mapt(branch))
            final_legs = entry.get("final_and_missed")
            if final_legs:
                self.emit_chain(proc_name, truncate_at_mapt(final_legs))
        elif "initial" in entry:
            # Single flat chain (RNP Y style) already includes the final
            # approach + MAPT inline -- just cut at MAPT.
            self.emit_chain(proc_name, truncate_at_mapt(entry["initial"]))

    def merge_into_files(self, rebuilt_names: set[str], remove_name_prefixes: tuple[str, ...] = ()):
        geojson_path = GEOJSON_DIR / f"vatm_procedures_{self.icao}.geojson"
        with open(geojson_path, encoding="utf-8") as f:
            gj = json.load(f)
        shutil.copy(geojson_path, BACKUP_DIR / f"vatm_procedures_{self.icao}.geojson.bak_{TODAY}")

        def drop(props: dict) -> bool:
            if props.get("procedure_type") != "IAP":
                return False
            name = str(props.get("procedure_name", ""))
            return name in rebuilt_names or any(name.startswith(p) for p in remove_name_prefixes)

        gj["features"] = [f for f in gj["features"] if not drop(f["properties"])] + self.features
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(gj, f, ensure_ascii=False)

        with open(INDEX_PATH, encoding="utf-8") as f:
            index = json.load(f)
        shutil.copy(INDEX_PATH, BACKUP_DIR / f"procedures_index.json.bak_{TODAY}")
        iap = index[self.icao]["IAP"]
        for name in list(iap.keys()):
            if name in rebuilt_names or any(name.startswith(p) for p in remove_name_prefixes):
                del iap[name]
        iap.update(self.fragment)
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=1)

        print(f"{self.icao} IAP rebuilt: {sorted(self.fragment.keys())}")
        print(f"{self.icao} IAP remaining (untouched): {sorted(index[self.icao]['IAP'].keys())}")


def rebuild_cm():
    with open(OUTPUT_DIR / "vvcm_tabular_from_pdf.json", encoding="utf-8") as f:
        data = json.load(f)
    coords = {name: (dms_to_dec(v["lat"]), dms_to_dec(v["lon"])) for name, v in data["waypoints"].items() if v.get("lat") and v.get("lon")}
    rb = Rebuilder("VVCM", coords)
    for name in ("RNP Z RWY09", "RNP Z RWY27"):
        rb.rebuild_pbn_entry(name, data["PBN"]["IAP"][name])
    # "ILS Y RWY27" deliberately skipped -- see module docstring.
    rb.merge_into_files(
        rebuilt_names={"RNP Z RWY09", "RNP Z RWY27"},
        remove_name_prefixes=("CM001", "CM002", "CM003"),
    )
    return rb.missing


def rebuild_dl():
    with open(OUTPUT_DIR / "vvdl_tabular_from_pdf.json", encoding="utf-8") as f:
        data = json.load(f)
    coords = {name: (dms_to_dec(v["lat"]), dms_to_dec(v["lon"])) for name, v in data["waypoints"].items() if v.get("lat") and v.get("lon")}
    rb = Rebuilder("VVDL", coords)
    for name in ("RNP Z RWY09", "RNP Y RWY09", "RNP Z RWY27", "RNP Y RWY27"):
        rb.rebuild_pbn_entry(name, data["PBN"]["IAP"][name])
    ils_combo = data["PBN"]["IAP"]["ILS W RWY09 / ILS X RWY09"]
    rb.rebuild_pbn_entry("ILS W RWY09", ils_combo)
    rb.rebuild_pbn_entry("ILS X RWY09", ils_combo)
    rb.merge_into_files(
        rebuilt_names={"RNP Z RWY09", "RNP Y RWY09", "RNP Z RWY27", "RNP Y RWY27", "ILS W RWY09", "ILS X RWY09"},
        remove_name_prefixes=("DL001", "DL002", "DL003", "DL004", "RNP Z Y 27"),
    )
    return rb.missing


def rebuild_lt():
    with open(OUTPUT_DIR / "vvlt_tabular_from_pdf_cv.json", encoding="utf-8") as f:
        data = json.load(f)
    coords = {name: (dms_to_dec(v["lat"]), dms_to_dec(v["lon"])) for name, v in data["waypoints"].items() if v.get("lat") and v.get("lon")}
    # LTH VOR/DME is every entry's own IAF -- already in the waypoints dict
    # under "LTH_VORDME"; the real "iaf" string value itself ("LTH VOR/DME")
    # is not a coords-dict key, so map it explicitly.
    coords["LTH VOR/DME"] = coords["LTH_VORDME"]

    rb = Rebuilder("VVLT", coords)
    for proc_name, entry in data["IAP"].items():
        iaf = entry.get("iaf")
        faf = entry.get("faf_coords")
        if not iaf or not faf:
            rb.missing.append(f"VVLT/{proc_name}: missing iaf or faf_coords")
            continue
        faf_name = f"{proc_name} FAF"
        rb.coords[faf_name] = (dms_to_dec(faf["lat"]), dms_to_dec(faf["lon"]))
        rb.emit_chain(proc_name, [iaf, faf_name])
    rb.merge_into_files(
        rebuilt_names=set(data["IAP"].keys()),
        remove_name_prefixes=("DALAP", "LT008", "LT009", "RW23L", "THR (", "VAGTU", "VICAL"),
    )
    return rb.missing


def main():
    missing = []
    missing += rebuild_cm()
    missing += rebuild_dl()
    missing += rebuild_lt()
    if missing:
        print(f"\n{len(missing)} missing-coordinate warning(s) (skipped, not guessed):")
        for m in missing:
            print(" ", m)


if __name__ == "__main__":
    main()
