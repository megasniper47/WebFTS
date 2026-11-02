"""Hieu chuan thoi diem tao tau den cho VVDN-XENKE-60MIN.scn.

Van de: thoi diem CRE duoc tinh NGUOC tu moc cham banh bang ham uoc luong
estimate_transit_s. Uoc luong do sai vai chuc giay (da do: trung binh 52s,
lon nhat 85s), lam chuoi lenh MOVE lan vao ben khoi dong khi tau CHUA toi
diem cho -- lenh MOVE dau tien keo tau di 11.669 m trong 1 giay.

Cach lam: sinh kich ban -> chay mo phong that -> do moc cham banh thuc te cua
tung chuyen -> cong do lech vao bang hieu chuan -> sinh lai. Lap den khi sai
lech lon nhat duoi NGUONG_S giay.

Chay:  python _calib_vvdn_xenke.py
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
import math
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
CALIB_FILE = HERE / "VVDN-XENKE-60MIN.calib.json"
PLAN_FILE = HERE / "VVDN-XENKE-60MIN.plan.json"
THR35L = (16.030133, 108.200372)
NGUONG_S = 5.0
SO_VONG = 6


def hav_m(la1, lo1, la2, lo2):
    R = 6371000.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def sinh_kich_ban():
    r = subprocess.run([sys.executable, str(HERE / "_gen_vvdn_xenke_60min.py")],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit(f"Sinh kich ban that bai:\n{r.stdout}\n{r.stderr}")


def do_moc_cham_banh(t_end):
    """Chay mo phong headless, tra ve {acid: thoi diem cham banh that}."""
    os.chdir(HERE.parent)
    sys.path.insert(0, str(HERE.parent))
    import importlib
    import bluesky as bs
    if getattr(bs, "traf", None) is None:
        bs.init(mode="sim", detached=True)
    else:                      # chay lai trong cung tien trinh -> nap lai sach
        bs.stack.stack("RESET")
        for _ in range(5):
            bs.sim.step()
    bs.stack.stack("IC VVDN-XENKE-60MIN")
    bs.sim.op()
    td, next_log = {}, 0.0
    while bs.sim.simt < t_end:
        bs.sim.step()
        if bs.sim.simt < next_log:
            continue
        next_log += 1.0
        for i, acid in enumerate(bs.traf.id):
            if not acid.startswith("ARR") or acid in td:
                continue
            if (bs.traf.alt[i] / 0.3048 < 50
                    and hav_m(float(bs.traf.lat[i]), float(bs.traf.lon[i]), *THR35L) < 3000):
                td[acid] = float(bs.sim.simt)
    return td


def main():
    calib = json.loads(CALIB_FILE.read_text(encoding="utf-8")) if CALIB_FILE.exists() else {}
    for vong in range(1, SO_VONG + 1):
        CALIB_FILE.write_text(json.dumps(calib, indent=1), encoding="utf-8")
        sinh_kich_ban()
        plan = json.loads(PLAN_FILE.read_text(encoding="utf-8"))
        arrs = plan["arrivals"]
        t_end = max(a["td"] for a in arrs) + 180.0
        td = do_moc_cham_banh(t_end)

        lech = {a["id"]: td[a["id"]] - a["td"] for a in arrs if a["id"] in td}
        thieu = [a["id"] for a in arrs if a["id"] not in td]
        if not lech:
            raise SystemExit("Khong do duoc moc cham banh nao")
        mx = max(lech.items(), key=lambda kv: abs(kv[1]))
        tb = sum(abs(v) for v in lech.values()) / len(lech)
        print(f"Vong {vong}: {len(lech)}/{len(arrs)} chuyen do duoc, "
              f"sai lech TB {tb:5.1f}s, lon nhat {mx[1]:+6.1f}s ({mx[0]})"
              + (f", THIEU: {thieu}" if thieu else ""))
        if abs(mx[1]) <= NGUONG_S and not thieu:
            print(f"Da hoi tu (sai lech lon nhat <= {NGUONG_S}s). "
                  f"Bang hieu chuan: {CALIB_FILE.name}")
            return
        for acid, dv in lech.items():
            calib[acid] = calib.get(acid, 0.0) + dv
    CALIB_FILE.write_text(json.dumps(calib, indent=1), encoding="utf-8")
    sinh_kich_ban()
    print(f"Het {SO_VONG} vong, chua dat nguong {NGUONG_S}s -- xem so lieu tung vong o tren.")


if __name__ == "__main__":
    main()
