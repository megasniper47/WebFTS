"""Phase 2: resolve each transition (already split by parse_procedures_kml.py's
graph-leaf-name method) into an ORDERED waypoint sequence with real
lat/lon/altitude, for use by a scenario-generation procedure module (not just
display geometry).

For each procedure boundary (same "has a direct Waypoints child" rule as
parse_procedures_kml.py), this script:
  1. Collects legs the same way (name, coords) to rebuild the transition graph
     via `build_transition_graph` (imported, not re-implemented).
  2. ALSO collects every Point placemark inside that boundary's own
     "Waypoints" folder: name (after stripping "WP "/"Navaid " prefix) ->
     (lon, lat, z_meters).
  3. For each transition (ordered edge path from the graph), walks the nodes
     in order and resolves each via that SAME boundary's waypoint dict --
     altitude is procedure-specific (confirmed by hand: the same fix can
     carry a different Z in a different procedure), so a node is never
     resolved against another boundary's Waypoints folder.

Z is in meters (confirmed by hand against a known threshold elevation in an
earlier session) -- converted to feet via x3.28084, rounded to the nearest
foot, never rounded to a "clean" number.

A node with no match in its own boundary's Waypoints folder is left with
alt_ft=None and reported in diagnostics -- never guessed.

Usage:
    python extract_transition_waypoints.py \
        --kml ".../PHƯƠNG THỨC BAY (SID, STAR, IAP).kml" \
        --airport-folder "VVDL (Hiệu lực TỪ 00h01 (HN) 01/10/26)" \
        --icao VVDL \
        --out-json /tmp/vvdl_transitions_from_kml.json
"""
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET

from parse_procedures_kml import (
    NS,
    build_transition_graph,
    classify_type,
    is_excluded_folder,
    local,
    scan_boundaries,
    ROOT,
)

_M_TO_FT = 3.28084
_WP_NAME_RE = re.compile(r"^(?:WP|Navaid)\s+(\S+)", re.I)


def extract_transitions(kml_path: str, airport_folder: str, icao: str, boundary_flags: list[bool]):
    stack = []
    in_target = False
    in_placemark = False
    current_pm = None
    proc_stack = []
    legs_stack = []
    waypoints_stack = []  # parallel to proc_stack: dict[fixname] -> (lon, lat, alt_ft)
    flag_i = 0

    result = {}  # ptype -> transition_name -> [ {name,lat,lon,alt_ft}, ... ]
    sources = {}  # ptype -> transition_name -> doc_name that provided the kept sequence
    diagnostics = []

    def flush_boundary(doc_name: str, legs: list[dict], waypoints: dict):
        if not legs:
            return
        ptype = classify_type(doc_name)
        edges, transitions, unknown, collisions, trunk_legs = build_transition_graph(legs)
        if not transitions:
            return  # display-only fallback already reported by parse_procedures_kml.py; nothing orderable here
        for leaf_name, path in transitions.items():
            if not path:
                continue
            nodes = [path[0][0]] + [b for (_a, b) in path]
            nodes = [n for n in nodes if n != ROOT]
            seq = []
            for n in nodes:
                hit = waypoints.get(n)
                if hit is None:
                    diagnostics.append(f"[no-waypoint-coord] {doc_name!r} transition {leaf_name!r}: node {n!r} not found in this Document's Waypoints folder")
                    seq.append({"name": n, "lat": None, "lon": None, "alt_ft": None})
                else:
                    lon, lat, alt_ft = hit
                    seq.append({"name": n, "lat": lat, "lon": lon, "alt_ft": alt_ft})
            existing = result.get(ptype, {}).get(leaf_name)
            if existing is not None:
                # Same leaf (transition) name produced by more than one Document
                # (e.g. the same published fix reached via both a CV and a PBN
                # variant of the same runway) -- never silently overwrite; keep
                # the LONGEST sequence found so far (most likely the complete
                # route rather than a partial/shared-trunk fragment) and flag
                # every case for manual review, since the two may genuinely be
                # different routes that happen to share a leaf fix name.
                prev_doc = sources[ptype][leaf_name]
                diagnostics.append(
                    f"[multi-document-leaf] transition {leaf_name!r} ({ptype}) produced by both {prev_doc!r} "
                    f"({len(existing)} wp) and {doc_name!r} ({len(seq)} wp) -- kept the longer one, review manually"
                )
                if len(seq) <= len(existing):
                    continue
            result.setdefault(ptype, {})[leaf_name] = seq
            sources.setdefault(ptype, {})[leaf_name] = doc_name

    context = ET.iterparse(kml_path, events=("start", "end"))
    for event, elem in context:
        tag = local(elem.tag)
        if event == "start":
            if tag in ("Document", "Folder"):
                stack.append({"tag": tag, "name": None, "is_boundary": False, "consume_flag": in_target})
            elif tag == "Placemark":
                in_placemark = True
                if in_target:
                    folder_names = [s["name"] for s in stack if s["name"]]
                    excluded = any(is_excluded_folder(n) for n in folder_names)
                    current_pm = {
                        "name": None, "geom": None, "coords": None,
                        "excluded": excluded, "folder_path": folder_names,
                    }
                else:
                    current_pm = None
        else:
            if tag == "name":
                if in_placemark:
                    if current_pm is not None and current_pm["name"] is None:
                        current_pm["name"] = (elem.text or "").strip()
                elif stack and stack[-1]["name"] is None:
                    nm = (elem.text or "").strip()
                    stack[-1]["name"] = nm
                    if not in_target and len(stack) == 3 and stack[-1]["tag"] == "Folder" and nm == airport_folder:
                        in_target = True
                    if stack[-1]["consume_flag"]:
                        is_boundary = boundary_flags[flag_i] if flag_i < len(boundary_flags) else False
                        flag_i += 1
                        stack[-1]["is_boundary"] = is_boundary
                        if is_boundary:
                            pname = nm[: -len(".kmz")].strip() if nm.lower().endswith(".kmz") else nm
                            proc_stack.append(pname)
                            legs_stack.append([])
                            waypoints_stack.append({})
            elif tag == "Placemark":
                in_placemark = False
                if current_pm is not None and legs_stack:
                    folder_path = current_pm["folder_path"]
                    in_waypoints = bool(folder_path) and folder_path[-1].strip().lower() == "waypoints"
                    if in_waypoints and current_pm["geom"] == "Point" and current_pm["coords"]:
                        raw = current_pm["name"] or ""
                        m = _WP_NAME_RE.match(raw.strip())
                        if m:
                            fixname = m.group(1)
                            lon, lat, z = current_pm["coords"][0]
                            alt_ft = round(z * _M_TO_FT) if z else None
                            waypoints_stack[-1].setdefault(fixname, (lon, lat, alt_ft))
                    elif not current_pm["excluded"] and current_pm["geom"] == "LineString":
                        leg_name = folder_path[-1] if folder_path else "(no-folder)"
                        legs_stack[-1].append({
                            "name": leg_name,
                            "raw_name": current_pm["name"] or "",
                            "coords": current_pm["coords"],
                        })
                current_pm = None
            elif tag in ("LineString", "Point", "Polygon", "LinearRing"):
                if current_pm is not None and current_pm["geom"] is None:
                    coord_el = elem.find(f"{NS}coordinates")
                    if coord_el is not None and coord_el.text:
                        pts = []
                        for tok in coord_el.text.split():
                            parts = tok.split(",")
                            if len(parts) >= 2:
                                lon, lat = float(parts[0]), float(parts[1])
                                z = float(parts[2]) if len(parts) >= 3 else 0.0
                                pts.append([lon, lat, z])
                        if pts:
                            current_pm["geom"] = tag
                            current_pm["coords"] = pts
            elif tag in ("Document", "Folder"):
                info = stack.pop()
                if info["is_boundary"]:
                    doc_name = proc_stack.pop()
                    legs = legs_stack.pop()
                    waypoints = waypoints_stack.pop()
                    flush_boundary(doc_name, legs, waypoints)
                if in_target and info["name"] == airport_folder and len(stack) == 2:
                    in_target = False
                elem.clear()

    return result, diagnostics


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kml", required=True)
    ap.add_argument("--airport-folder", required=True)
    ap.add_argument("--icao", required=True)
    ap.add_argument("--out-json", required=True)
    args = ap.parse_args()

    boundary_flags = scan_boundaries(args.kml, args.airport_folder)
    result, diagnostics = extract_transitions(args.kml, args.airport_folder, args.icao, boundary_flags)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print(f"icao={args.icao}")
    for ptype, transitions in result.items():
        print(f"  {ptype}: {len(transitions)} transition(s)")
        for name, seq in transitions.items():
            missing = sum(1 for wp in seq if wp["alt_ft"] is None and wp["lat"] is None)
            print(f"    - {name!r}: {len(seq)} waypoint(s), {missing} khong tra duoc toa do")
    if diagnostics:
        print(f"\n  {len(diagnostics)} diagnostic(s):")
        for d in diagnostics[:50]:
            print(f"    {d}")


if __name__ == "__main__":
    main()
