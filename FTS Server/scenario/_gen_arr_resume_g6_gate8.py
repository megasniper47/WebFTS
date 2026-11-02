"""Dung tuyen lan G6 -> BEN 8 (VVDN), bam tim duong lan that.

Ban dau du an chi co tuyen G6 -> ben 11. Kich ban "cat canh xen ke" yeu cau
tau ha canh ve ben 28 HOAC ben 8, nen can dung them tuyen nay.

CACH DUNG (khong bia toa do, moi diem deu tu du lieu san bay that):
  1. Lay nguyen phan dau tuyen G6 -> ben 11 da duoc kiem chung (tu G6 chay
     ve dong) den dung diem no cat qua tim duong lan E (diem #20).
  2. Chay doc duong lan E len huong bac, lay nguyen tim E tu
     taxiway_centerlines.geojson (feature 'E': 16.057596,108.199801 ->
     16.060423,108.199397), den dau duong dan vao ben 8.
  3. Re theo duong dan vao ben 8 ('Linear Feature 3': 16.059331,108.199551
     -> 16.059205,108.199817 -> 16.059370,108.200871).
  4. Doan cuoi vao dung vi tri do ben 8 trong gates.geojson
     (16.059413,108.201205).

Phat lenh MOVE theo NHIP THOI GIAN DEU 2s -- neu phat theo khoang cach deu
thi luc giam toc ve 0, khoang trong giua 2 lenh gian ra hang chuc giay va
BlueSky cho tau "bay tu do" trong khoang do (da do duoc tau vot di 350-1138
kt khi dung cach cu).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
import math
import shutil
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "_ARR_RESUME_G6_GATE11.scn"
OUT = HERE / "_ARR_RESUME_G6_GATE8.scn"
BACKUP_DIR = HERE / "Backup"
LAYOUT = (HERE / "../data/aerodrome_layout/datasets/vietnam_kml_layout/"
          "normalized/airports/VVDN").resolve()

CUT_INDEX = 20        # diem tuyen G6->ben11 cat qua tim duong lan E
DT_S = 2.0            # nhip thoi gian giua 2 lenh MOVE
TAXI_SPD_KT = 6.1
SLOWDOWN_M = 45.0
MIN_SPD_KT = 0.8

LEADIN_FIRST = (16.059331, 108.199551)   # dau duong dan vao ben 8


def m_between(la1, lo1, la2, lo2):
    R = 6371000.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def bearing(la1, lo1, la2, lo2):
    la1, lo1, la2, lo2 = map(math.radians, (la1, lo1, la2, lo2))
    dl = lo2 - lo1
    x = math.sin(dl) * math.cos(la2)
    y = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def read_move(path):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if ">MOVE" not in line:
            continue
        f = line.split("MOVE %0,")[1].split(",")
        out.append((float(f[0]), float(f[1])))
    return out


def layout_lines():
    tc = json.loads((LAYOUT / "taxiway_centerlines.geojson").read_text(encoding="utf-8"))
    out = []
    for feat in tc["features"]:
        g = feat["geometry"]
        lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for s in lines:
            out.append((feat["properties"].get("name"), [(p[1], p[0]) for p in s]))
    return out


def gate8_coord():
    g = json.loads((LAYOUT / "gates.geojson").read_text(encoding="utf-8"))
    for f in g["features"]:
        if str(f["properties"].get("name", "")) == "Gate8":
            c = f["geometry"]["coordinates"]
            return (c[1], c[0])
    raise SystemExit("Khong tim thay Gate8 trong gates.geojson")


def taxiway_E():
    """Tim duong lan E, noi cac doan lai theo thu tu tu nam len bac."""
    segs = [pts for name, pts in layout_lines() if name == "E" and len(pts) == 2]
    if not segs:
        raise SystemExit("Khong tim thay duong lan E")
    segs.sort(key=lambda s: min(p[0] for p in s))
    chain = [segs[0][0], segs[0][1]]
    for s in segs[1:]:
        a, b = (s if m_between(*chain[-1], *s[0]) < m_between(*chain[-1], *s[1]) else (s[1], s[0]))
        if m_between(*chain[-1], *a) > 1.0:
            chain.append(a)
        chain.append(b)
    return chain


def gate8_leadin():
    for name, pts in layout_lines():
        if m_between(*pts[0], *LEADIN_FIRST) < 1.0:
            return pts
    raise SystemExit("Khong tim thay duong dan vao ben 8")


def densify(path_pts, step_m):
    out = [path_pts[0]]
    for i in range(len(path_pts) - 1):
        la1, lo1 = path_pts[i]
        la2, lo2 = path_pts[i + 1]
        d = m_between(la1, lo1, la2, lo2)
        n = max(1, int(math.ceil(d / step_m)))
        for k in range(1, n + 1):
            t = k / n
            out.append((la1 + (la2 - la1) * t, lo1 + (lo2 - lo1) * t))
    return out


def fmt(t):
    return f"{int(t//3600):02d}:{int((t%3600)//60):02d}:{t%60:05.2f}"


def main():
    spine = read_move(SRC)[: CUT_INDEX + 1]          # G6 -> ra toi duong lan E
    E = taxiway_E()
    lead = gate8_leadin()
    gate8 = gate8_coord()

    # Doan doc duong lan E: tu diem cat (spine[-1]) len den dau duong dan
    lat_lo, lat_hi = spine[-1][0], lead[0][0]
    along_E = [p for p in E if lat_lo < p[0] < lat_hi]
    along_E.sort(key=lambda p: p[0])

    route_shape = spine + along_E + lead + [gate8]
    shape = densify(route_shape, 3.0)

    cum = [0.0]
    for i in range(len(shape) - 1):
        cum.append(cum[-1] + m_between(*shape[i], *shape[i + 1]))
    total = cum[-1]

    def at_dist(s):
        if s <= 0:
            return shape[0]
        if s >= total:
            return shape[-1]
        j = 0
        while j < len(cum) - 2 and cum[j + 1] < s:
            j += 1
        f = (s - cum[j]) / max(cum[j + 1] - cum[j], 1e-9)
        return (shape[j][0] + (shape[j + 1][0] - shape[j][0]) * f,
                shape[j][1] + (shape[j + 1][1] - shape[j][1]) * f)

    lines = [
        "# G6 -> BEN 8 (VVDN). Sinh boi _gen_arr_resume_g6_gate8.py.",
        "# Bam tim duong lan that: phan dau tuyen G6->ben11 -> duong lan E ->",
        "# duong dan vao ben 8 -> vi tri do ben 8 (gates.geojson).",
        f"# Phat MOVE deu {DT_S:.0f}s/lenh de tau luon duoc ghim vi tri.",
    ]
    t, s = 2.0, 0.0
    while s < total:
        remain = total - s
        spd = TAXI_SPD_KT if remain > SLOWDOWN_M else max(TAXI_SPD_KT * remain / SLOWDOWN_M, MIN_SPD_KT)
        la, lo = at_dist(s)
        nla, nlo = at_dist(min(s + 5.0, total))
        lines.append(f"{fmt(t)}>MOVE %0,{la:.6f},{lo:.6f},0,{bearing(la, lo, nla, nlo):.1f},{spd:.1f}")
        s += spd * 0.514444 * DT_S
        t += DT_S
    la, lo = shape[-1]
    prev = at_dist(max(total - 5.0, 0.0))
    lines.append(f"{fmt(t)}>MOVE %0,{la:.6f},{lo:.6f},0,{bearing(*prev, la, lo):.1f},0.0")
    lines.append(f"{fmt(t + 10)}>DEL %0")

    if OUT.exists():
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        d = BACKUP_DIR / f"VVDN-xenke {ts}"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(OUT, d / OUT.name)
        print(f"Da backup ban cu vao Backup/{d.name}/{OUT.name}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Da ghi {OUT.name}: {sum(1 for L in lines if '>MOVE' in L)} lenh MOVE, dai {total:.0f} m, ket thuc {fmt(t)}")
    print(f"  diem dau  ({shape[0][0]:.6f},{shape[0][1]:.6f})")
    print(f"  diem cuoi ({shape[-1][0]:.6f},{shape[-1][1]:.6f})  [ben 8]")
    print(f"  qua duong lan E: {len(along_E)} diem tim E")


if __name__ == "__main__":
    main()
