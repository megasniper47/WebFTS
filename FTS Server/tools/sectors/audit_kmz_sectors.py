"""One-off audit dump of every placemark under 'VUNG TROI SAN BAY (TMA, CTR)'
in the 2026.09.19 RNAV2 KMZ, so the real extractor can be written against
verified names/paths instead of guessing which nested placemark is which.
Not part of the permanent pipeline -- prints to stdout only.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET

K = "{http://www.opengis.net/kml/2.2}"
TARGET = "VÙNG TRỜI SÂN BAY (TMA, CTR)"

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
        if k and k not in out:
            out[k] = v
    return out


def geometry_summary(elem) -> str:
    parts = []
    for child in elem.iter():
        local = child.tag.split("}")[-1]
        if local == "Polygon":
            outer = child.find(f"{K}outerBoundaryIs/{K}LinearRing/{K}coordinates")
            n = len((outer.text or "").split()) if outer is not None else 0
            parts.append(f"Polygon({n}pts)")
        elif local == "LineString":
            coords = child.find(f"{K}coordinates")
            n = len((coords.text or "").split()) if coords is not None else 0
            parts.append(f"LineString({n}pts)")
        elif local == "Point":
            parts.append("Point")
    return ",".join(parts) if parts else "NONE"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kml", required=True)
    args = ap.parse_args()

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
                if any(TARGET in p for p in path):
                    pm_name = (elem.findtext(f"{K}name") or "").strip()
                    desc = elem.findtext(f"{K}description") or ""
                    fields = parse_desc(desc)
                    geom = geometry_summary(elem)
                    interesting = {
                        k: fields[k]
                        for k in (
                            "Name_Txt", "Class_Code", "DistVertUpper_Val", "DistVertUpper_UOM",
                            "DistVertLower_Val", "DistVertLower_UOM", "Radius_Val", "Radius_UOM",
                        )
                        if k in fields
                    }
                    print(f"PATH: {' / '.join(path)}")
                    print(f"  NAME: {pm_name!r}  GEOM: {geom}  FIELDS: {interesting}")
                elem.clear()
                continue
            if tag in (K + "Folder", K + "Document"):
                if stack:
                    stack.pop()
                elem.clear()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
