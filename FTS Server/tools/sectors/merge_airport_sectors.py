"""Phase 3 of the Airport CTR/TMA rebuild: merge Phase 1 geometry +
Phase 2 attributes into the schema the Sectors module actually serves.

Inputs:
  --phase1  vatm_airport_sectors_2026.geojson   (real geometry, 20 areas)
  --phase2  vatm_airport_sectors_docx_table.json (docx attributes, 21 areas)
  --acc-fir vatm_acc_fir_2026.geojson           (for Da Nang CTL geometry --
                                                  not in Phase 1 at all, it
                                                  was extracted earlier from
                                                  the ACC en-route folder)
  --existing vietnam_tma_app_control_areas.geojson (only read for the 5
                                                  already-verified AIP ENR 2.1
                                                  radio frequencies -- TSN,
                                                  Noi Bai, Da Nang APP/CTL,
                                                  Cam Ranh -- carried forward
                                                  since neither the docx nor
                                                  the KMZ has frequency data)

Output: --out, a new GeoJSON with one feature per docx area (21 total) using
an extended property schema (adds airspace_class, radius_km, center,
horizontal_note, vertical_note, geometry_caveat). The 5 TSN Point Merge
arrival sectors and are left for the caller to re-append unchanged -- this
script only produces the 21 CTR/TMA/CTL areas.
"""
from __future__ import annotations

import argparse
import json

# docx row name, service tag, and the navaid-code fallback derived from the
# horizontal desc's "tam X" phrase (last token only, e.g. "DVOR/DME NOB" -> "NOB")
NAME_TO_SERVICE = {
    "nb_tma": "TMA", "nb_ctr": "CTR",
    "dh_ctr": "CTR", "pb_ctr": "CTR",
    "dn_tma": "TMA", "dn_ctl": "CTL", "dn_ctr": "CTR",
    "cl_ctr": "CTR", "pk_ctr": "CTR", "pc_ctr": "CTR", "th_ctr": "CTR",
    "cr_tma": "TMA", "cr_ctr": "CTR",
    "bmt_ctr": "CTR", "lk_ctr": "CTR",
    "tsnlt_tma": "TMA", "tsn_ctr": "CTR", "lt_ctr": "CTR",
    "ct_ctr": "CTR",
    "pq_ctr": "CTR", "pq_tma": "TMA",
}

# frequency/unit already verified against AIP ENR 2.1 in the previous dataset
# -- carried forward as-is, not re-derived from anything in this phase.
KNOWN_FREQ = {
    "tsnlt_tma": {"unit": "Tan Son Nhat APP",
                  "frequency": "125.500 MHz primary / 126.350 MHz secondary"},
    "nb_tma": {"unit": "Noi Bai APP",
               "frequency": "125.100 MHz primary / 121.000 MHz secondary"},
    "dn_tma": {"unit": "Da Nang APP",
               "frequency": "120.450 MHz primary / 125.450 MHz secondary"},
    "dn_ctl": {"unit": "Da Nang APP/CTL",
               "frequency": "125.300 MHz primary / 125.450 MHz secondary"},
    "cr_tma": {"unit": "Cam Ranh APP",
               "frequency": "127.900 MHz primary / 124.350 MHz secondary"},
}


def center_code(center_desc: str | None) -> str | None:
    if not center_desc:
        return None
    if center_desc.strip().upper() == "ARP":
        return "ARP"
    return center_desc.strip().split()[-1]


def format_vertical(lower: dict, upper: dict) -> str:
    def fmt(tok: dict) -> str:
        if tok["kind"] == "SFC":
            return "SFC"
        if tok["kind"] == "FL":
            return f"FL{tok['value_ft'] // 100}"
        if tok["kind"] == "ALT":
            return f"{tok['value_m']} m ({tok['value_ft']} ft)"
        if tok["kind"] == "ALT_RANGE":
            return f"{tok['value_m_min']}-{tok['value_m_max']} m ({tok['value_ft_min']}-{tok['value_ft_max']} ft)"
        return tok.get("raw", "?")
    return f"{fmt(lower)} - {fmt(upper)}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase1", required=True)
    ap.add_argument("--phase2", required=True)
    ap.add_argument("--acc-fir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    phase1 = json.load(open(args.phase1, encoding="utf-8"))
    phase2 = json.load(open(args.phase2, encoding="utf-8"))
    acc_fir = json.load(open(args.acc_fir, encoding="utf-8"))

    geom_by_key = {f["properties"]["output_key"]: f["geometry"] for f in phase1["features"]}
    caveat_by_key = {f["properties"]["output_key"]: f["properties"]["reconciliation_note"]
                     for f in phase1["features"]}

    # Da Nang CTL geometry lives in the ACC extraction, not Phase 1 -- it is
    # the one feature named exactly "CTL DA NANG" with a large lon/lat extent
    # (the other candidate under the same acc_folder is a small, unrelated
    # 37-point sliver near Dong Hoi and is deliberately excluded).
    dn_ctl_geom = None
    for f in acc_fir["features"]:
        if f["properties"].get("acc_folder") == "CTL DANANG" and f["properties"].get("name") == "CTL DA NANG":
            dn_ctl_geom = f["geometry"]
            break

    features = []
    missing_geom = []
    for area in phase2["areas"]:
        key = area["key"]
        if key == "dn_ctl":
            geom = dn_ctl_geom
        else:
            geom = geom_by_key.get(key)
        if geom is None:
            missing_geom.append(key)
            continue

        known = KNOWN_FREQ.get(key, {})
        horiz = area["horizontal"]
        props = {
            "name": area["name"],
            "unit": known.get("unit"),
            "frequency": known.get("frequency"),
            "service": NAME_TO_SERVICE[key],
            "airspace_class": area["airspace_class"],
            "vertical": format_vertical(area["vertical_lower"], area["vertical_upper"]),
            "source": "AIP ENR 2.1 (bang thong ke CTR/TMA doc theo duong HK RNAV2) "
                      "+ KMZ 2026.09.19 DUONG HK RNAV2 (hinh hoc)",
            "center": center_code(horiz["center_desc"]),
            "radius_km": horiz["radius_km"],
            "horizontal_note": horiz["raw"],
            "vertical_note": area["note"],
            "geometry_caveat": caveat_by_key.get(key) if key != "dn_ctl" else None,
        }
        features.append({"type": "Feature", "properties": props, "geometry": geom})

    payload = {"type": "FeatureCollection", "features": features}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    print(f"Merged {len(features)}/21 areas -> {args.out}")
    if missing_geom:
        print("MISSING GEOMETRY:", missing_geom)
    return 0 if not missing_geom else 1


if __name__ == "__main__":
    raise SystemExit(main())
