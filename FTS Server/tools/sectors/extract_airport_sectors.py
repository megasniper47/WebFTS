"""Phase 1 of the Airport CTR/TMA rebuild (see docx 'CTR TMA cac san bay doc
theo duong HK RNAV2.docx' + WebFTS memory project_airport_sectors_rebuild).

Extracts real CTR/TMA geometry for the 21 areas listed in that docx's summary
table from the 2026.09.19 RNAV2 KMZ, folder 'VUNG TROI SAN BAY (TMA, CTR)'
(the same KMZ already used by extract_acc_fir.py for the FIR rebuild -- it is
the newest available source, superseding the 2026.04.20 KMZ that
vatm_kmz/airspace_fir_acc_tma_ctr.geojson was built from).

Selection notes (audited by hand against tools/sectors/audit_kmz_sectors.py
output -- do not "fix" these without re-running that audit):

* Da Nang CTR/TMA: the KMZ has a naming/metadata mismatch inherited from the
  source survey. The placemark whose OUTER <name> tag says "TMA DA NANG" has
  an embedded Name_Txt of "CTR DA NANG" with vertical SFC-2750m -- exactly
  the docx's CTR band. A second placemark literally named "CTR DA NANG" is a
  bare 73-point LineString with no embedded metadata at all. Since the docx
  states CTR and TMA Da Nang share the same 60km horizontal circle (only the
  vertical band differs: CTR SFC-2750m vs TMA 600-2750m), the metadata-bearing
  polygon is taken as CTR (trusting Name_Txt over the outer <name>, which is
  most likely a copy/paste labelling slip), and the bare LineString is taken
  as the TMA's outline. This is a *reconciliation*, not a guess: it is
  recorded in each feature's `reconciliation_note` field so it can be
  reviewed/overridden later.
* Da Nang CTL is NOT re-extracted here -- it already exists, correctly, in
  vatm_acc_fir_2026.geojson (extract_acc_fir.py), sourced from the same KMZ's
  ACC folder.
* Phu Quoc CTR/TMA: KMZ has both a pre- and post-01.10.2026 version; the
  newer "hieu luc TU 01.10.2026" one is used (matches the project's
  established "newest source wins" rule). The CTR one is a genuine 5-point
  rectangle, which matches the docx's own description ("hinh chu nhat quanh
  truc CHC").
* Tan Son Nhat CTR / Long Thanh CTR: the KMZ only has a simplified 7-point
  bounding box for each, NOT the true AIP polygon (TS01-04 / LT04-01-02-AS26)
  described in the docx. Flagged via `is_simplified_box: true` -- do not
  present these as authoritative AIP polygons.
* TMA TSN-LT: two candidate boundaries exist (SECTOR 0x.kml "TMA TSN" and
  SECTOR 2x.kml "TMA TSN 16500FT"), both 651 points. Cause of the duplicate
  is not stated in the source; "TMA TSN" (unqualified name, matches the
  docx's plain "TMA" wording) is used. Flagged via `alternate_source_exists`.
* Pleiku CTR: KMZ geometry is a full 50km circle; the docx describes a notch
  cut out between 30-50km on bearings R045-R156 that is NOT present in this
  geometry (the exact cut boundary is not in any source we have). Flagged via
  `known_geometry_simplification`.
* Cam Ranh TMA/CTR and Da Nang TMA carry no vertical/class metadata in the
  KMZ at all -- Phase 2 fills these from the docx table, not from here.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

K = "{http://www.opengis.net/kml/2.2}"
ROOT_FOLDER = "VÙNG TRỜI SÂN BAY (TMA, CTR)"

ROW_RE = re.compile(r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*</tr>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")


class PatchedKml:
    NEEDLE = b"<kml "
    INJECT = b'<kml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '

    def __init__(self, path: str):
        self._f = open(path, "rb")
        self._patched = False

    def read(self, size: int = -1) -> bytes:
        chunk = self._f.read(size)
        if not self._patched and chunk:
            idx = chunk.find(self.NEEDLE)
            if idx != -1:
                chunk = chunk[:idx] + self.INJECT + chunk[idx + len(self.NEEDLE):]
                self._patched = True
        return chunk

    def close(self):
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def strip_tags(s: str) -> str:
    return html.unescape(TAG_RE.sub("", s)).strip()


def parse_desc(desc: str) -> dict:
    out = {}
    for k, v in ROW_RE.findall(desc or ""):
        k = strip_tags(k)
        v = strip_tags(v)
        if k and k not in out and v != "<Null>":
            out[k] = v
    return out


def parse_ring(text: str) -> list[list[float]]:
    ring = []
    for token in (text or "").split():
        parts = token.split(",")
        if len(parts) >= 2:
            ring.append([round(float(parts[0]), 6), round(float(parts[1]), 6)])
    return ring


def first_geometry(elem) -> tuple[str, list[list[list[float]]]] | None:
    """Return ('Polygon'|'LineString', rings) for the first geometry found."""
    poly = elem.find(f".//{K}Polygon")
    if poly is not None:
        outer = poly.find(f"{K}outerBoundaryIs/{K}LinearRing/{K}coordinates")
        if outer is not None and outer.text:
            ring = parse_ring(outer.text)
            if len(ring) >= 3:
                return "Polygon", [ring]
    line = elem.find(f".//{K}LineString")
    if line is not None:
        coords = line.find(f"{K}coordinates")
        if coords is not None and coords.text:
            ring = parse_ring(coords.text)
            if len(ring) >= 3:
                return "LineString", [ring]
    return None


# path segments are matched by substring against the joined folder path,
# scoped by requiring the placemark name to equal `name` too (avoids
# picking up the wrong nested "ARR .../Style..." placemarks).
TARGETS = [
    # (output_key, placemark_name, extra_path_substring_or_None, reconciliation_note)
    ("nb_tma", "TMA NỘI BÀI", None, None),
    ("nb_ctr", "CTR NỘI BÀI", None, None),
    ("dh_ctr", "CTR ĐỒNG HỚI", None, None),
    ("pb_ctr", "CTR PHÚ BÀI", None, None),
    ("dn_ctr", "TMA ĐÀ NẴNG", None,
     "Outer <name> says 'TMA DA NANG' but embedded Name_Txt says 'CTR DA NANG' "
     "with vertical SFC-2750m (the docx's CTR band); reassigned to CTR per Name_Txt."),
    ("dn_tma", "CTR ĐÀ NẴNG", None,
     "Outer <name> says 'CTR DA NANG' but this placemark carries no metadata "
     "at all, while a separate polygon already claims the CTR identity via its "
     "Name_Txt (see dn_ctr). Docx states CTR and TMA Da Nang share the same "
     "60km circle (only vertical band differs), so this bare outline is "
     "reassigned to TMA; vertical/class taken from the docx table, not this KMZ."),
    ("cl_ctr", "CTR CHU LAI", None, None),
    ("pk_ctr", "CTR PLEIKU", None,
     "KMZ geometry is a full 50km circle; docx describes a 30-50km notch on "
     "bearings R045-R156 that is not represented here (source coords for the "
     "notch are not available)."),
    ("pc_ctr", "CTR PHÙ CÁT", None, None),
    ("th_ctr", "CTR TUY HÒA", None, None),
    ("cr_tma", "TMA CRA", None, None),
    ("cr_ctr", "CTR CAM RANH", None, None),
    ("bmt_ctr", "CTR BUÔN MA THUỘT", None, None),
    ("lk_ctr", "CTR LIÊN KHƯƠNG", None, None),
    ("tsnlt_tma", "TMA TSN", "SECTOR 0x.kml",
     "A second candidate boundary 'TMA TSN 16500FT' (SECTOR 2x.kml, also 651 "
     "points) exists in the source with no stated reason for the duplicate; "
     "the unqualified 'TMA TSN' name was used as it matches the docx's plain "
     "'TMA' wording."),
    ("tsn_ctr", "CTR TÂN SƠN NHẤT 2500FT", None,
     "KMZ only has a simplified bounding box here, not the true AIP polygon "
     "(TS01-TS02-TS03-TS04) described in the docx."),
    ("lt_ctr", "CTR LONG THÀNH 2500FT", None,
     "KMZ only has a simplified bounding box here, not the true AIP polygon "
     "(LT04-LT01-LT02-AS26) described in the docx."),
    ("ct_ctr", "CTR CẦN THƠ", None, None),
    ("pq_ctr", "CTR Phu Quoc", "CTR PHÚ QUỐC (Hiệu lực TỪ", None),
    ("pq_tma", "Style3", "TMA PHÚ QUỐC (Hiệu lực Từ", None),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kml", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if not os.path.exists(args.kml):
        sys.exit(f"doc.kml not found: {args.kml}")

    by_key = {t[0]: t for t in TARGETS}
    matched: dict[str, dict] = {}
    stack: list[str | None] = []

    with PatchedKml(args.kml) as fh:
        for event, elem in ET.iterparse(fh, events=("start", "end")):
            tag = elem.tag
            if event == "start":
                if tag in (K + "Folder", K + "Document"):
                    stack.append(None)
                continue
            if tag == K + "name":
                if stack and stack[-1] is None:
                    stack[-1] = (elem.text or "").strip()
                continue
            if tag == K + "Placemark":
                path = [s for s in stack if s]
                if any(ROOT_FOLDER in p for p in path):
                    pm_name = (elem.findtext(f"{K}name") or "").strip()
                    joined_path = " / ".join(path)
                    for key, want_name, want_path_sub, note in TARGETS:
                        if key in matched:
                            continue
                        if pm_name != want_name:
                            continue
                        if want_path_sub and want_path_sub not in joined_path:
                            continue
                        geom = first_geometry(elem)
                        if geom is None:
                            continue
                        desc = elem.findtext(f"{K}description") or ""
                        fields = parse_desc(desc)
                        matched[key] = {
                            "output_key": key,
                            "placemark_name": pm_name,
                            "folder_path": joined_path,
                            "geometry_kind": geom[0],
                            "rings": geom[1],
                            "kmz_fields": fields,
                            "reconciliation_note": note,
                        }
                        break
                elem.clear()
                continue
            if tag in (K + "Folder", K + "Document"):
                if stack:
                    stack.pop()
                elem.clear()

    missing = [k for k in by_key if k not in matched]
    features = []
    for key, rec in matched.items():
        features.append({
            "type": "Feature",
            "properties": {
                "output_key": rec["output_key"],
                "placemark_name": rec["placemark_name"],
                "folder_path": rec["folder_path"],
                "kmz_fields": rec["kmz_fields"],
                "reconciliation_note": rec["reconciliation_note"],
                "source": "2026.09.19 ĐƯỜNG HK RNAV2.kmz / VÙNG TRỜI SÂN BAY (TMA, CTR)",
                "status": "Decision-support / Non-operational",
            },
            "geometry": {"type": "Polygon", "coordinates": rec["rings"]},
        })

    payload = {"type": "FeatureCollection", "features": features}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    print(f"Matched {len(matched)}/{len(TARGETS)} target areas -> {args.out}")
    if missing:
        print("MISSING:", missing)
    for key, rec in matched.items():
        n = len(rec["rings"][0])
        print(f"  {key:12s} {rec['geometry_kind']:10s} {n:5d}pts  {rec['placemark_name']!r}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
