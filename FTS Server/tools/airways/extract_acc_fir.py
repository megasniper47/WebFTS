"""Extract the ACC (en-route) airspace polygons from the 2026.09.19 RNAV2 KMZ.

The previous FIR file shipped with the app (`vatm_fir_only.geojson`) was a
hand-drawn approximation: Ha Noi FIR was a 6-point coastal strip that excluded
the whole northern landmass, and Ho Chi Minh FIR had a western edge running
straight from 10°22'N/103°44'E to 17°00'N/106°24'E, slicing through Cambodia
and Vietnam. This tool replaces it with the real controlled-airspace polygons
published in the KMZ, under:

    2026.09.19 ĐƯỜNG HK RNAV2 / VÙNG TRỜI ĐƯỜNG DÀI (ACC)
        ├── ACC HANOI          -> Ha Noi FIR (VVHN)
        ├── ACC HO CHI MINH     -> Ho Chi Minh FIR (VVHM)
        └── CTL DANANG          -> Da Nang control area

Notes
-----
* The KML declares `xsi:schemaLocation` without ever binding the `xsi` prefix,
  so it is not well-formed; the root element is patched while streaming.
* The document is ~138 MB, so it is parsed incrementally and every finished
  element is cleared to keep memory flat.
* Only Polygon geometry is taken. Each sector keeps its own polygon -- no union
  is computed, because merging them would invent a boundary that is not in the
  source. Consumers that want a single FIR silhouette should draw the sectors
  as one filled layer.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

K = '{http://www.opengis.net/kml/2.2}'

# The KMZ groups en-route airspace by controlling unit, not by FIR. Ha Noi and
# Ho Chi Minh ACC map one-to-one onto the two Vietnamese FIRs, but Da Nang is a
# control area whose FIR membership is not stated anywhere in the source, so it
# is deliberately left unattributed rather than guessed.
FIR_BY_FOLDER = {
    'ACC HANOI': ('VVHN', 'HA NOI FIR (VVHN)', 'Ha Noi ACC'),
    'ACC HO CHI MINH': ('VVHM', 'HO CHI MINH FIR (VVHM)', 'Ho Chi Minh ACC'),
    'CTL DANANG': ('', 'DA NANG CTL', 'Da Nang ACC/CTL'),
}

ACC_ROOT = 'VÙNG TRỜI ĐƯỜNG DÀI'


class PatchedKml:
    """File-like wrapper that binds the missing `xsi` prefix on the root tag."""

    NEEDLE = b'<kml '
    INJECT = b'<kml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '

    def __init__(self, path: str):
        self._f = open(path, 'rb')
        self._patched = False

    def read(self, size: int = -1) -> bytes:
        chunk = self._f.read(size)
        if not self._patched and chunk:
            idx = chunk.find(self.NEEDLE)
            if idx != -1:
                chunk = chunk[:idx] + self.INJECT + chunk[idx + len(self.NEEDLE):]
                self._patched = True
        return chunk

    def close(self) -> None:
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def parse_ring(text: str) -> list[list[float]]:
    ring = []
    for token in (text or '').split():
        parts = token.split(',')
        if len(parts) >= 2:
            ring.append([round(float(parts[0]), 6), round(float(parts[1]), 6)])
    return ring


def polygon_coords(poly: ET.Element) -> list[list[list[float]]] | None:
    outer = poly.find(f'{K}outerBoundaryIs/{K}LinearRing/{K}coordinates')
    if outer is None or not outer.text:
        return None
    rings = [parse_ring(outer.text)]
    for inner in poly.findall(f'{K}innerBoundaryIs/{K}LinearRing/{K}coordinates'):
        r = parse_ring(inner.text or '')
        if len(r) >= 4:
            rings.append(r)
    if len(rings[0]) < 4:
        return None
    return rings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kml', required=True, help='path to the extracted doc.kml')
    ap.add_argument('--out', required=True, help='GeoJSON file to write')
    args = ap.parse_args()

    if not os.path.exists(args.kml):
        sys.exit(f'doc.kml not found: {args.kml}')

    features: list[dict] = []
    stack: list[str | None] = []
    counts: dict[str, int] = {}

    with PatchedKml(args.kml) as fh:
        for event, elem in ET.iterparse(fh, events=('start', 'end')):
            tag = elem.tag
            if event == 'start':
                if tag in (K + 'Folder', K + 'Document'):
                    stack.append(None)
                continue

            if tag == K + 'name':
                if stack and stack[-1] is None:
                    stack[-1] = (elem.text or '').strip()
                continue

            if tag == K + 'Placemark':
                path = [s for s in stack if s]
                # Only keep placemarks that live under the ACC root folder.
                if not any(ACC_ROOT in p for p in path):
                    elem.clear()
                    continue
                folder = next((p for p in path if p in FIR_BY_FOLDER), None)
                if folder is None:
                    elem.clear()
                    continue

                pm_name = elem.findtext(f'{K}name') or ''
                fir_code, fir_name, unit = FIR_BY_FOLDER[folder]

                for poly in elem.iter(K + 'Polygon'):
                    rings = polygon_coords(poly)
                    if not rings:
                        continue
                    counts[folder] = counts.get(folder, 0) + 1
                    features.append({
                        'type': 'Feature',
                        'properties': {
                            'name': pm_name.strip() or folder,
                            'category': 'ACC_FIR_SECTOR',
                            'fir': fir_code,
                            'fir_name': fir_name,
                            'unit': unit,
                            'acc_folder': folder,
                            'folder_path': ' / '.join(path),
                            'source': '2026.09.19 ĐƯỜNG HK RNAV2.kmz / VÙNG TRỜI ĐƯỜNG DÀI (ACC)',
                            'status': 'Decision-support / Non-operational',
                        },
                        'geometry': {'type': 'Polygon', 'coordinates': rings},
                    })
                elem.clear()
                continue

            if tag in (K + 'Folder', K + 'Document'):
                if stack:
                    stack.pop()
                elem.clear()

    payload = {'type': 'FeatureCollection', 'features': features}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))

    print(f'Wrote {len(features)} ACC polygons -> {args.out}')
    for folder, n in sorted(counts.items()):
        code, name, _ = FIR_BY_FOLDER[folder]
        print(f'  {folder:18s} -> {code}  {n} polygon(s)')

    # Report the extent of each group so the result can be sanity-checked.
    for code in sorted({f['properties']['fir'] or f['properties']['acc_folder']
                        for f in features}):
        pts = [c for f in features
               if (f['properties']['fir'] or f['properties']['acc_folder']) == code
               for ring in f['geometry']['coordinates'] for c in ring]
        lons = [p[0] for p in pts]
        lats = [p[1] for p in pts]
        print(f'  {code} extent: lon {min(lons):.2f}..{max(lons):.2f}, '
              f'lat {min(lats):.2f}..{max(lats):.2f}  ({len(pts)} vertices)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
