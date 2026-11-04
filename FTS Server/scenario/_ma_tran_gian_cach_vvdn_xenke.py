"""Ma tran gian cach toi thieu theo loai cap (muc 5 prompt) cho VVDN-XENKE-60MIN.

Hai phan:
  1. YEU CAU (tinh tu vvdn_xenke_rules.json): moi loai cap den-den, di-den,
     den-di, di-di -> NM va giay tai nguong 35L (giay quy doi bang toc do 5 NM
     cua chinh loai tau trong file .scn).
  2. THUC DO (tu VVDN-XENKE-60MIN.track.json do _verify_vvdn_xenke.py ghi): cu ly
     tau sau toi tau truoc tai luc tau truoc qua DOTEN, 10 NM, 5 NM, 2 NM va nguong.

Chay sau _verify_vvdn_xenke.py:  python _ma_tran_gian_cach_vvdn_xenke.py
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
import math
from pathlib import Path

HERE = Path(__file__).parent
RULES = json.loads((HERE / "vvdn_xenke_rules.json").read_text(encoding="utf-8"))
PLAN = json.loads((HERE / "VVDN-XENKE-60MIN.plan.json").read_text(encoding="utf-8"))
SCN = (HERE / "VVDN-XENKE-60MIN.scn").read_text(encoding="utf-8").splitlines()
TRACK = json.loads((HERE / "VVDN-XENKE-60MIN.track.json").read_text(encoding="utf-8"))
ARRS, DEPS = PLAN["arrivals"], PLAN["departures"]
HEAVY = set(RULES["co_cau_tau_bay"]["heavy"])
THR35L = tuple(RULES["so_do_san_bay"]["nguong_35L"])
DOTEN = (15.767222, 108.118333)      # _gen_kb5_1hour.py (STAR RNAV RWY35L/R that)


def wake(t):
    return "H" if t in HEAVY else "M"


def nm(a, b):
    R = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    x = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(x)) / 1852.0


def v5nm(acid):
    for line in SCN:
        if ">" in line and line.split(">", 1)[1].startswith(f"{acid} ADDWPT 15.947115,108.212410"):
            return float(line.rsplit(" ", 1)[1])
    return None


def yeu_cau():
    cfg = RULES["phan_cach_ha_canh_lien_tiep_35L"]
    M, Mt = cfg["ma_tran"], RULES["phan_cach_cat_canh_vs_tau_den_35L"]["ma_tran"]
    W = {"H": "HEAVY", "M": "MEDIUM"}
    v = {}
    for a in ARRS:
        s = v5nm(a["id"])
        if s:
            v.setdefault(wake(a["type"]), []).append(s)
    vtb = {k: sum(x) / len(x) for k, x in v.items()}
    out = []
    for lead in "HM":
        for trail in "HM":
            nd = max(M.get(f"{W[trail]}_sau_{W[lead]}", 0), cfg["radar_toi_thieu"])
            req = max(nd, cfg.get("gian_cach_toi_thieu_NM", 0))
            out.append({"loai": "Đến-Đến", "cap": f"{lead}-{trail}", "nhieu_dong_NM": nd,
                        "yeu_cau_NM": req, "giay_tai_nguong": round(req / vtb[trail] * 3600)})
    for dep in "HM":
        for arr in "HM":
            req = Mt[W[dep]][W[arr]]
            out.append({"loai": "Đi-Đến", "cap": f"{dep}-{arr}", "yeu_cau_NM": req,
                        "giay_tai_nguong": round(req / vtb[arr] * 3600)})
    out.append({"loai": "Đến-Đi", "cap": "moi cap", "yeu_cau_NM": None,
                "giay_tai_nguong": RULES["cham_cang_den_chay_da"]["mac_dinh_giay"],
                "ghi_chu": "chay da sau cham cang (huan lenh sau cham cang, muc 4.2.1.a)"})
    Md = RULES["phan_cach_cat_canh_lien_tiep_35R"]["ma_tran"]
    for lead in "HM":
        for trail in "HM":
            out.append({"loai": "Đi-Đi", "cap": f"{lead}-{trail}", "yeu_cau_NM": None,
                        "giay_tai_nguong": Md[f"{W[trail]}_sau_{W[lead]}"]})
    return out, vtb


def thuc_do():
    """Cu ly tau sau -> tau truoc khi tau truoc qua DOTEN / 10 / 5 / 2 NM / nguong."""
    moc = {"DOTEN": None, "10NM": 10.0, "5NM": 5.0, "2NM": 2.0, "nguong": 0.0}
    kq = {}
    for a, b in zip(ARRS, ARRS[1:]):
        ta, tb = TRACK.get(a["id"]), TRACK.get(b["id"])
        if not ta or not tb:
            continue
        cap = f"{wake(a['type'])}-{wake(b['type'])}"
        for ten, d in moc.items():
            if ten == "DOTEN":
                p = min(ta, key=lambda q: nm((q[1], q[2]), DOTEN))
                if nm((p[1], p[2]), DOTEN) > 0.5:
                    continue
            else:
                p = next((q for q in ta if q[3] < 5000 and nm((q[1], q[2]), THR35L) <= d + 0.02), None)
                if p is None:
                    continue
            r = min(tb, key=lambda q: abs(q[0] - p[0]))
            if abs(r[0] - p[0]) > 3:
                continue
            kq.setdefault(cap, {}).setdefault(ten, []).append(nm((p[1], p[2]), (r[1], r[2])))
    return {cap: {ten: {"nho_nhat": round(min(x), 2), "trung_binh": round(sum(x) / len(x), 2),
                        "so_cap": len(x)} for ten, x in m.items()} for cap, m in kq.items()}


def main():
    yc, vtb = yeu_cau()
    td = thuc_do()
    print("Toc do 5 NM trung binh (kt):", {k: round(v, 1) for k, v in vtb.items()})
    for r in yc:
        print(r)
    for cap, m in sorted(td.items()):
        print(cap, m)
    (HERE / "VVDN-XENKE-60MIN.ma_tran.json").write_text(json.dumps(
        {"toc_do_5NM_tb_kt": vtb, "yeu_cau": yc, "thuc_do_den_den_NM": td},
        indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
