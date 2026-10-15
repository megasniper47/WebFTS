"""Dung lai _ARR_RESUME_G4_GATE26.scn bam DUNG tim duong lan that cua VVDN.

LY DO: ban cu (45 diem) lech tim duong lan trung binh 21.6 m, cho co 72.8 m
(16/45 diem lech >25 m) -- tau bay lan "cat qua san" chu khong theo duong lan.
Doi chieu: _ARR_RESUME_G4_GATE28.scn (90 diem) chi lech 0.3 m, tuc du lieu
duong lan that la dung, chi rieng file GATE26 la ban tho chua tinh chinh.

CACH DUNG (khong bia toa do):
  1. Lay nguyen phan dau tuyen GATE28 -- tu G4 chay doc duong lan song song
     len huong bac -- den dung diem no re vao Gate 28 (diem #68).
  2. Di THANG tiep tren chinh duong lan do (cung huong 352.6) den dau duong
     dan vao Gate 26.
  3. Re theo duong dan vao Gate 26, lay nguyen tu taxiway_centerlines.geojson
     (feature "Linear Feature 3": 16.052563,108.200542 -> 16.052468,108.200743
     -> 16.052625,108.201996), diem cuoi trung voi toa do Gate 26 that trong
     gates.geojson (16.052622,108.201973).

Toc do/giam toc va nhip ~9 m/diem giu giong tuyen GATE28 da duoc kiem chung.
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
SRC = HERE / "_ARR_RESUME_G4_GATE28.scn"
OUT = HERE / "_ARR_RESUME_G4_GATE26.scn"
BACKUP_DIR = HERE / "Backup"
LAYOUT = (HERE / "../data/aerodrome_layout/datasets/vietnam_kml_layout/"
          "normalized/airports/VVDN").resolve()

CUT_INDEX = 68           # diem cuoi cung con chay doc duong lan (truoc khi GATE28 re vao bai do)
DT_S = 2.0               # NHIP THOI GIAN giua 2 lenh MOVE (tuyen GATE28 goc ~2.4s)
TAXI_SPD_KT = 6.1        # toc do lan, bang doan tuong ung cua tuyen GATE28
SLOWDOWN_M = 45.0        # quang duong cuoi dung de giam toc ve 0
MIN_SPD_KT = 0.8         # toc do san khi sap dung, tranh nhip MOVE bi gian qua dai

# QUAN TRONG -- phat lenh MOVE theo NHIP THOI GIAN DEU, khong phai theo khoang
# cach deu. Ban dau script nay phat moi 9 m; khi tau giam toc ve 0 thi 9 m do
# mat toi ~29 s, tao KHOANG TRONG giua 2 lenh MOVE va trong khoang trong do
# BlueSky cho tau "bay tu do" -- da do duoc tau vot di 350-1138 kt ra xa 5.5 km
# roi moi bi lenh MOVE cuoi keo nguoc ve ben. Phat deu 2 s/lenh thi tau luon
# duoc ghim vi tri, khong con khoang trong de troi.


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
        if "MOVE" not in line:
            continue
        ts, rest = line.split(">", 1)
        f = rest.split("MOVE %0,")[1].split(",")
        out.append((float(f[0]), float(f[1])))
    return out


def gate26_leadin():
    tc = json.loads((LAYOUT / "taxiway_centerlines.geojson").read_text(encoding="utf-8"))
    for feat in tc["features"]:
        g = feat["geometry"]
        lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for s in lines:
            if abs(s[0][1] - 16.052563) < 1e-5 and abs(s[0][0] - 108.200542) < 1e-5:
                return [(p[1], p[0]) for p in s]
    raise SystemExit("Khong tim thay duong dan vao Gate 26 trong taxiway_centerlines.geojson")


def densify(path_pts, step_m):
    """Chen them diem sao cho khoang cach <= step_m, giu nguyen hinh tuyen."""
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
    spine = read_move(SRC)[: CUT_INDEX + 1]
    lead = gate26_leadin()

    # Tuyen hinh hoc: spine (chay doc duong lan) -> duong dan -> Gate 26
    shape = densify(spine + lead, 3.0)
    cum = [0.0]
    for i in range(len(shape) - 1):
        cum.append(cum[-1] + m_between(*shape[i], *shape[i + 1]))
    total = cum[-1]

    def at_dist(s):
        """Vi tri tai quang duong s doc tuyen."""
        if s <= 0:
            return shape[0]
        if s >= total:
            return shape[-1]
        j = 0
        while j < len(cum) - 2 and cum[j + 1] < s:
            j += 1
        f = (s - cum[j]) / max(cum[j + 1] - cum[j], 1e-9)
        la = shape[j][0] + (shape[j + 1][0] - shape[j][0]) * f
        lo = shape[j][1] + (shape[j + 1][1] - shape[j][1]) * f
        return (la, lo)

    lines = [
        "# G4 -> BEN 26 (VVDN). Sinh boi _gen_arr_resume_g4_gate26.py.",
        "# Bam tim duong lan that (taxiway_centerlines.geojson); diem cuoi la",
        "# toa do Gate 26 that trong gates.geojson.",
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
        d = BACKUP_DIR / f"VVPQ-VVDN {ts}"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(OUT, d / OUT.name)
        print(f"Da backup ban cu vao Backup/{d.name}/{OUT.name}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Da ghi {OUT.name}: {sum(1 for L in lines if 'MOVE' in L)} lenh MOVE, dai {total:.0f} m, ket thuc {fmt(t)}")
    print(f"  diem dau  ({shape[0][0]:.6f},{shape[0][1]:.6f})")
    print(f"  diem cuoi ({shape[-1][0]:.6f},{shape[-1][1]:.6f})")


if __name__ == "__main__":
    main()
