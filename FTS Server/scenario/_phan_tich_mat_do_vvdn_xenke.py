"""Phan tich MAT DO BAT DAU VI PHAM cho VVDN-XENKE-60MIN (muc 7 prompt).

Kich ban chinh chay MOT pha sat phan cach toi thieu (nang luc toi da). Script
nay tra loi cau hoi con lai: neu KSVKL nen lich day hon (giam moi khoang cach
giua cac moc tren duong CHC theo he so f < 1), thi o mat do nao bat dau vi pham,
quy tac nao vi pham truoc, va cap loai tau nao la nut co chai.

Doc LAP voi generator: chi doc vvdn_xenke_rules.json, VVDN-XENKE-60MIN.plan.json
va toc do tiep can 5 NM cua tung loai trong chinh file .scn.

Cach nen lich: moc cham banh / chay da t -> t0 + (t - t0) * f. Cac khoang thoi
gian MAT DAT (cham banh -> cat qua xong 35R, phan ung chay da 10/15 s) giu
nguyen vi chung khong phu thuoc mat do. Chi xet cac quy tac tren duong CHC va
tren khong (khong lap lai lich lan) -- ghi ro trong bao cao.

Chay:  python _phan_tich_mat_do_vvdn_xenke.py   -> in bang + ghi .mat_do.json
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
from pathlib import Path

HERE = Path(__file__).parent
RULES = json.loads((HERE / "vvdn_xenke_rules.json").read_text(encoding="utf-8"))
PLAN = json.loads((HERE / "VVDN-XENKE-60MIN.plan.json").read_text(encoding="utf-8"))
SCN = (HERE / "VVDN-XENKE-60MIN.scn").read_text(encoding="utf-8").splitlines()
ARRS, DEPS = PLAN["arrivals"], PLAN["departures"]
HEAVY = set(RULES["co_cau_tau_bay"]["heavy"])
CODE = {k: v[0] for k, v in RULES["han_che_duong_lan_E"]["ma_chu_theo_loai"].items()}
HE_SO = [1.00, 0.98, 0.96, 0.94, 0.92, 0.90, 0.85, 0.80]


def wake(t):
    return "HEAVY" if t in HEAVY else "MEDIUM"


def v5nm(acid):
    """Toc do (kt) tai moc 5 NM cua chuyen acid, doc tu lenh ADDWPT trong .scn."""
    for line in SCN:
        if ">" in line and line.split(">", 1)[1].startswith(f"{acid} ADDWPT 15.947115,108.212410"):
            return float(line.rsplit(" ", 1)[1])
    return sum(RULES["toc_do_tau_den_IAS"]["tai_5NM_truc_chot"]) / 2.0


def rang_buoc():
    """Danh sach rang buoc: (ten quy tac, loai cap, khoang nen duoc (s),
    khoang co dinh (s), yeu cau (s)). Vi pham khi nen*f - co_dinh < yeu_cau."""
    out = []
    cfg = RULES["phan_cach_ha_canh_lien_tiep_35L"]
    M = cfg["ma_tran"]
    clr = cfg["giai_phong_truoc_huan_lenh_ha_canh"]["cu_ly_cap_huan_lenh_ha_canh_NM"]
    for a, b in zip(ARRS, ARRS[1:]):
        cap = f"{wake(a['type'])[0]}-{wake(b['type'])[0]}"
        v = v5nm(b["id"])
        key = f"{wake(b['type'])}_sau_{wake(a['type'])}"
        nm_nd = max(M.get(key, M["MEDIUM_sau_MEDIUM"]), cfg["radar_toi_thieu"])
        out.append(("Nhieu dong ha canh (MANOP/ICAO)", cap, b["td"] - a["td"], 0.0, nm_nd / v * 3600))
        if cfg.get("gian_cach_toi_thieu_NM", 0.0) > 0:      # 8 NM MANOP: nguoi dung da bo
            out.append((f"Gian cach ha canh {cfg['gian_cach_toi_thieu_NM']:g} NM (MANOP)", cap,
                        b["td"] - a["td"], 0.0, cfg["gian_cach_toi_thieu_NM"] / v * 3600))
        out.append(("Giai phong 35L truoc 2 NM", cap, b["td"] - a["td"], a["t_ce"] - a["td"],
                    clr / v * 3600))
    Mt = RULES["phan_cach_cat_canh_vs_tau_den_35L"]["ma_tran"]
    pu = RULES["thoi_gian_phan_ung_mat_dat"]
    for d in DEPS:
        sau = [a for a in ARRS if a["td"] > d["roll"]]
        truoc = [a for a in ARRS if a["td"] <= d["roll"]]
        if sau:
            a = min(sau, key=lambda x: x["td"])
            cap = f"I{wake(d['type'])[0]}-Đ{wake(a['type'])[0]}"
            out.append(("Cat canh vs tau den (muc 4.2.1)", cap, a["td"] - d["roll"], 0.0,
                        Mt[wake(d["type"])][wake(a["type"])] / v5nm(a["id"]) * 3600))
        if truoc:
            a = max(truoc, key=lambda x: x["td"])
            pu_s = pu["doi_chuan_den_chay_da_code_C_giay"] if CODE[d["type"]] == "C" \
                else pu["doi_chuan_den_chay_da_code_D_tro_len_giay"]
            out.append(("Huan lenh cat canh sau cham cang (4.2.1.a)",
                        f"Đ{wake(a['type'])[0]}-I{wake(d['type'])[0]}", d["roll"] - a["td"], pu_s, 0.0))
    Md = RULES["phan_cach_cat_canh_lien_tiep_35R"]["ma_tran"]
    for a, b in zip(DEPS, DEPS[1:]):
        key = f"{wake(b['type'])}_sau_{wake(a['type'])}"
        if key == "MEDIUM_sau_HEAVY":          # chi o nay co nguon MANOP/ICAO
            out.append(("Nhieu dong cat canh 2 phut (MANOP)", "H-M", b["roll"] - a["roll"], 0.0,
                        Md[key]))
    return out


def main():
    rb = rang_buoc()
    t_all = sorted([a["td"] for a in ARRS] + [d["roll"] for d in DEPS])
    span, n = t_all[-1] - t_all[0], len(t_all)

    # He so nen toi han cua tung rang buoc: f* = (yeu cau + co dinh) / nen duoc
    nguong = {}
    for ten, cap, nen, co_dinh, yc in rb:
        f_star = (yc + co_dinh) / nen
        k = (ten, cap)
        if k not in nguong or f_star > nguong[k]:
            nguong[k] = f_star
    print("HE SO NEN TOI HAN theo quy tac va loai cap (vi pham khi f < f*):")
    for (ten, cap), f in sorted(nguong.items(), key=lambda kv: -kv[1]):
        print(f"  f* = {f:.3f}   {ten:45s} {cap}")

    bang = []
    for f in HE_SO:
        vp = {}
        for ten, cap, nen, co_dinh, yc in rb:
            if nen * f - co_dinh < yc - 1e-6:
                vp.setdefault(ten, {}).setdefault(cap, 0)
                vp[ten][cap] += 1
        rate = (n - 1) * 3600.0 / (span * f)
        bang.append({"he_so": f, "chuyen_dong_moi_gio": round(rate, 1),
                     "so_vi_pham": sum(sum(c.values()) for c in vp.values()), "chi_tiet": vp})
    print("\nNEN LICH THEO HE SO f:")
    for r in bang:
        print(f"  f={r['he_so']:.2f}  ~{r['chuyen_dong_moi_gio']:5.1f} chuyen dong/gio  "
              f"vi pham: {r['so_vi_pham']:3d}  {json.dumps(r['chi_tiet'], ensure_ascii=False)}")
    (HERE / "VVDN-XENKE-60MIN.mat_do.json").write_text(json.dumps({
        "phuong_phap": "nen moc cham banh/chay da quanh moc dau tien theo he so f; khoang mat dat giu nguyen",
        "he_so_toi_han": [{"quy_tac": t, "cap": c, "f_toi_han": round(f, 4)}
                          for (t, c), f in sorted(nguong.items(), key=lambda kv: -kv[1])],
        "bang": bang}, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
