"""Kiem chung DOC LAP kich ban VVDN-XENKE-60MIN.scn.

Script nay KHONG dung lai ham lap lich cua generator. No tu doc:
  - vvdn_xenke_rules.json  (quy tac phan cach, tham so lan)
  - VVDN-XENKE-60MIN.plan.json  (lich da sinh: loai tau, SID/STAR, cac moc)
roi TU TINH lai tung dieu kien va ket luan DAT / KHONG DAT kem dieu khoan nguon.

Phan B chay mo phong HEADLESS that (khong qua Flask) de do:
  - cu ly that giua hai tau ha canh lien tiep tai thoi diem cham banh,
  - cu ly that giua tau cat canh va tau dang tiep can khi bat dau chay da,
  - canh bao xung dot tren khong theo nguong trong file cau hinh,
  - lech tim duong lan cua pha lan (so voi taxiway_centerlines.geojson),
  - tau bay bi "troi" (toc do mat dat vo ly trong pha lan),
  - cat qua 35R (thoi gian, xung dot voi tau cat canh, giai phong 35L truoc
    2 NM), han che duong lan E theo ma chu, thoi gian thoat ly 35L -- theo
    du thao MANOP Da Nang; hinh hoc doc truc tiep tu cac file .geojson.

Cach dung:
    python _verify_vvdn_xenke.py            # ca phan A va B
    python _verify_vvdn_xenke.py --static   # chi phan A (khong chay sim)
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
import math
import os
from pathlib import Path

HERE = Path(__file__).parent
RULES = json.loads((HERE / "vvdn_xenke_rules.json").read_text(encoding="utf-8"))
PLAN = json.loads((HERE / "VVDN-XENKE-60MIN.plan.json").read_text(encoding="utf-8"))
SCN = HERE / "VVDN-XENKE-60MIN.scn"
LAYOUT = (HERE / "../data/aerodrome_layout/datasets/vietnam_kml_layout/"
          "normalized/airports/VVDN").resolve()

ARRS = PLAN["arrivals"]
DEPS = PLAN["departures"]
HEAVY = set(RULES["co_cau_tau_bay"]["heavy"])
THR35L = (16.030133, 108.200372)

results = []        # (muc, ket_luan, chi_tiet, dieu_khoan)


def check(muc, ok, chi_tiet, dieu_khoan):
    results.append((muc, "DAT" if ok else "KHONG DAT", chi_tiet, dieu_khoan))
    return ok


def wake(t):
    return "HEAVY" if t in HEAVY else "MEDIUM"


def fmt(t):
    return f"{int(t//3600):02d}:{int((t%3600)//60):02d}:{t%60:04.1f}"


def hav_m(la1, lo1, la2, lo2):
    R = 6371000.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def approach_spd_5nm(actype):
    """Toc do IAS tai moc 5NM -- doc tu chinh file .scn da sinh (gia tri BADA
    cua tung loai), khong lay lai tu generator."""
    want = f"ADDWPT 15.947115,108.212410"
    for line in SCN.read_text(encoding="utf-8").splitlines():
        if want in line:
            acid = line.split(">")[1].split()[0]
            a = next((x for x in ARRS if x["id"] == acid), None)
            if a and a["type"] == actype:
                return float(line.rsplit(" ", 1)[1])
    rng = RULES["toc_do_tau_den_IAS"]["tai_5NM_truc_chot"]
    return sum(rng) / 2.0


# ===========================================================================
# PHAN A -- KIEM TRA TINH TREN LICH
# ===========================================================================
def A1_co_cau_doi_tau():
    tl = RULES["co_cau_tau_bay"]
    for ten, ds in (("DEN", ARRS), ("DI", DEPS)):
        n = len(ds)
        nh = sum(1 for d in ds if wake(d["type"]) == "HEAVY")
        want_h = round(n * tl["ty_le_heavy"])
        check(f"A1. Co cau doi tau ({ten})", nh == want_h,
              f"{n - nh} MEDIUM + {nh} HEAVY tren {n} chuyen "
              f"({(n-nh)/n*100:.0f}%/{nh/n*100:.0f}%), han ngach yeu cau {n-want_h}M+{want_h}H",
              "vvdn_xenke_rules.json > co_cau_tau_bay (muc 2 prompt)")
        thu_tu = [wake(d["type"])[0] for d in sorted(ds, key=lambda x: x.get("td", x.get("roll")))]
        cap = {}
        for k in range(len(thu_tu) - 1):
            key = f"{thu_tu[k]}-{thu_tu[k + 1]}"
            cap[key] = cap.get(key, 0) + 1
        thieu = [c for c in ("H-H", "H-M", "M-H", "M-M") if c not in cap]
        check(f"A1b. Du cac cap ke tiep H-H/H-M/M-H/M-M ({ten})", not thieu,
              ", ".join(f"{k}: {v}" for k, v in sorted(cap.items()))
              + (f"; THIEU {thieu}" if thieu else ""),
              "Muc 2 prompt: bao dam xuat hien du cac to hop cap ke tiep")


NGUON_HA_CANH = ("vvdn_xenke_rules.json > phan_cach_ha_canh_lien_tiep_35L: nhieu dong/giam sat ATS "
                 "theo MANOP (= ICAO Doc 4444 8.7.3.4); KHONG ap dung gian cach 8 NM cua MANOP "
                 "(nguoi dung chi dinh 2026-11-04)")
NGUON_CAT_VS_DEN = ("vvdn_xenke_rules.json > phan_cach_cat_canh_vs_tau_den_35L: du thao Phuong thuc 2 CHC "
                    "song song Da Nang 24.7.2026 muc 4.2.1 = MANOP Phu luc muc 4.2.1 (bang co giam sat ATS)")


def can_ha_canh_nm(lead_type, trail_type):
    cfg = RULES["phan_cach_ha_canh_lien_tiep_35L"]
    M = cfg["ma_tran"]
    key = f"{wake(trail_type)}_sau_{wake(lead_type)}"
    return max(M.get(key, M["MEDIUM_sau_MEDIUM"]), cfg["radar_toi_thieu"],
               cfg.get("gian_cach_toi_thieu_NM", 0.0))


def A2_phan_cach_ha_canh():
    xau = []
    for i in range(1, len(ARRS)):
        lead, tr = ARRS[i - 1], ARRS[i]
        need = can_ha_canh_nm(lead["type"], tr["type"])
        dt = tr["td"] - lead["td"]
        got = dt / 3600.0 * approach_spd_5nm(tr["type"])
        if got < need - 0.05:
            xau.append(f"{lead['id']}({wake(lead['type'])[0]})->{tr['id']}"
                       f"({wake(tr['type'])[0]}): {got:.2f}NM < {need}NM")
    check("A2. Phan cach hai tau ha canh lien tiep 35L", not xau,
          f"{len(ARRS)-1} cap, {len(xau)} cap khong dat"
          + ("; " + "; ".join(xau[:4]) if xau else ""),
          NGUON_HA_CANH)


def A3_phan_cach_cat_canh():
    cfg = RULES["phan_cach_cat_canh_lien_tiep_35R"]
    M, S = cfg["ma_tran"], cfg["phan_cach_theo_SID"]
    brg = sid_bearings()
    xau = []
    for i in range(1, len(DEPS)):
        lead, tr = DEPS[i - 1], DEPS[i]
        key = f"{wake(tr['type'])}_sau_{wake(lead['type'])}"
        d = abs(brg[lead["sid"]] - brg[tr["sid"]]) % 360
        d = min(d, 360 - d)
        same = lead["sid"] == tr["sid"] or d < 45.0
        need = max(M.get(key, M["MEDIUM_sau_MEDIUM"]),
                   S["cung_duong_bay_giay"] if same else S["phan_ky_giay"])
        got = tr["roll"] - lead["roll"]
        if got < need - 0.5:
            xau.append(f"{lead['id']}->{tr['id']}: {got:.0f}s < {need}s "
                       f"({'cung duong bay' if same else 'phan ky'})")
    check("A3. Phan cach hai tau cat canh lien tiep 35R", not xau,
          f"{len(DEPS)-1} cap, {len(xau)} cap khong dat"
          + ("; " + "; ".join(xau[:4]) if xau else ""),
          "vvdn_xenke_rules.json > phan_cach_cat_canh_lien_tiep_35R [CAN XAC NHAN]")


def sid_bearings():
    """Huong doan dau cua tung SID -- doc tu chinh file .scn da sinh."""
    out, seen = {}, {}
    for line in SCN.read_text(encoding="utf-8").splitlines():
        if " ADDWPT " not in line or ">" not in line:
            continue
        acid = line.split(">")[1].split()[0]
        d = next((x for x in DEPS if x["id"] == acid), None)
        if not d:
            continue
        la, lo = map(float, line.split("ADDWPT ")[1].split()[0].split(","))
        seen.setdefault(d["sid"], []).append((la, lo))
    for sid, pts in seen.items():
        (la1, lo1), (la2, lo2) = pts[1], pts[2]
        la1, lo1, la2, lo2 = map(math.radians, (la1, lo1, la2, lo2))
        dl = lo2 - lo1
        x = math.sin(dl) * math.cos(la2)
        y = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dl)
        out[sid] = (math.degrees(math.atan2(x, y)) + 360) % 360
    return out


def A4_cat_canh_vs_tau_den():
    M = RULES["phan_cach_cat_canh_vs_tau_den_35L"]["ma_tran"]
    xau = []
    for d in DEPS:
        nxt = [a for a in ARRS if a["td"] > d["roll"]]
        if not nxt:
            continue
        a = min(nxt, key=lambda x: x["td"])
        need = M[wake(d["type"])][wake(a["type"])]
        got = (a["td"] - d["roll"]) / 3600.0 * approach_spd_5nm(a["type"])
        if got < need - 0.05:
            xau.append(f"{d['id']}({wake(d['type'])[0]}) chay da khi {a['id']}"
                       f"({wake(a['type'])[0]}) con {got:.2f}NM < {need}NM")
    check("A4. Cat canh 35R khi co tau dang tiep can 35L", not xau,
          f"{len(DEPS)} chuyen di, {len(xau)} chuyen khong dat"
          + ("; " + "; ".join(xau[:4]) if xau else ""),
          NGUON_CAT_VS_DEN)


def A5_cham_cang_den_chay_da():
    s = RULES["cham_cang_den_chay_da"]
    xau = []
    for d in DEPS:
        tr = [a for a in ARRS if a["td"] <= d["roll"]]
        if not tr:
            xau.append(f"{d['id']} chay da {fmt(d['roll'])} khi chua co tau nao cham cang")
            continue
        gap = d["roll"] - max(a["td"] for a in tr)
        if gap < s["mac_dinh_giay"] - 0.5:
            xau.append(f"{d['id']}: chi {gap:.0f}s sau khi tau den cham cang")
    check("A5. Chi cap huan lenh chay da sau khi tau den da cham cang", not xau,
          f"{len(DEPS)} chuyen di, {len(xau)} chuyen khong dat"
          + ("; " + "; ".join(xau[:3]) if xau else ""),
          f"vvdn_xenke_rules.json > cham_cang_den_chay_da = {s['mac_dinh_giay']}s (muc 3c)")


def A6_diem_cho():
    lim = RULES["gioi_han_diem_cho"]["so_tau_toi_da"]
    busy, peak_t = {}, None
    for d in DEPS:
        # tu luc VAO HANG CHO (vi tri thu hai neu phai xep hang) den luc chay da
        for t in range(int(d.get("t_xep_hang", d["start_taxi"] + d["taxi_s"])), int(d["roll"]) + 1):
            busy[t] = busy.get(t, 0) + 1
    peak = max(busy.values()) if busy else 0
    if busy:
        peak_t = max(busy, key=busy.get)
    check("A6. So tau bay cho tai diem cho truoc 35R", peak <= lim,
          f"lon nhat {peak} tau (luc {fmt(peak_t) if peak_t else '-'}), gioi han {lim}",
          "vvdn_xenke_rules.json > gioi_han_diem_cho (muc 6 prompt -- yeu cau cung)")


def A7_len_duong_chc():
    xau = []
    for j, d in enumerate(DEPS):
        if j == 0:
            continue
        if d["lineup"] < DEPS[j - 1]["roll"] - 0.5:
            xau.append(f"{d['id']} len CHC {fmt(d['lineup'])} truoc khi "
                       f"{DEPS[j-1]['id']} chay da {fmt(DEPS[j-1]['roll'])}")
        if d["lineup"] > d["roll"] + 0.5:
            xau.append(f"{d['id']} len CHC sau khi chay da (vo ly)")
    check("A7. Chi len duong CHC sau khi tau truoc bat dau chay da", not xau,
          f"{len(DEPS)-1} cap, {len(xau)} truong hop khong dat"
          + ("; " + "; ".join(xau[:3]) if xau else ""),
          "vvdn_xenke_rules.json > thoi_gian_phan_ung_mat_dat (muc 3e prompt)")


def A8_xen_ke():
    seq = sorted([(a["td"], "DEN") for a in ARRS] + [(d["roll"], "DI") for d in DEPS])
    runs, cur = [], 1
    for i in range(1, len(seq)):
        if seq[i][1] == seq[i - 1][1]:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    check("A8. Tinh XEN KE giua cat canh va ha canh", max(runs) <= 2,
          f"chuoi cung loai dai nhat {max(runs)} lan chuyen "
          f"(thu tu: {''.join('D' if s[1]=='DEN' else 'I' for s in seq)})",
          "Muc 1 prompt: 'cat canh xen ke voi ha canh'")


def A9_thong_luong():
    T = RULES["thiet_ke_lich"]["thoi_luong_phut"] * 60
    t0 = min(a["td"] for a in ARRS)          # cua so do bat dau tu lan cham banh dau tien
    na = sum(1 for a in ARRS if t0 <= a["td"] < t0 + T)
    nd = sum(1 for d in DEPS if t0 <= d["roll"] < t0 + T)
    gaps = [ARRS[i]["td"] - ARRS[i - 1]["td"] for i in range(1, len(ARRS))]
    results.append((f"A9. Thong luong cua so {T // 60:.0f} phut ({fmt(t0)} - {fmt(t0 + T)}, "
                    f"sau pha khoi dong)", "SO LIEU",
                    f"{na} den + {nd} di = {na + nd} chuyen dong/gio; nhip den "
                    f"TB {sum(gaps) / len(gaps):.0f}s, nho nhat {min(gaps):.0f}s",
                    "vvdn_xenke_rules.json > thiet_ke_lich"))


def A11_tao_tai_IAF():
    """Muc 5 prompt: moi chuyen den duoc tao (CRE) TAI IAF cua STAR duoc gan --
    doc truc tiep chu thich cua tung lenh CRE trong file .scn."""
    xau, n = [], 0
    for line in SCN.read_text(encoding="utf-8").splitlines():
        if line.startswith("# ARR") and " -- " in line:
            n += 1
            if "CRE tai IAF" not in line:
                xau.append(line.split()[1])
    check("A11. Moi chuyen den duoc tao tai IAF cua STAR", n == len(ARRS) and not xau,
          f"{n - len(xau)}/{len(ARRS)} chuyen tao tai IAF"
          + (f"; tao giua STAR: {xau}" if xau else ""),
          "Muc 5 prompt (tinh nguoc CRE tu IAF; thieu thoi gian thi them pha khoi dong)")


def A10_lan_khong_am():
    xau = [d["id"] for d in DEPS if d["start_taxi"] < 0]
    check("A10. Moi chuyen di deu bat dau lan trong pham vi kich ban", not xau,
          f"som nhat {fmt(min(d['start_taxi'] for d in DEPS))}"
          + (f", {len(xau)} chuyen co lich am: {xau[:3]}" if xau else ""),
          "Kiem tra tinh hop le cua file .scn")


# ===========================================================================
# PHAN B -- CHAY MO PHONG HEADLESS VA DO SO LIEU THAT
# ===========================================================================
def run_headless(t_end, dt_log=1.0):
    os.chdir(HERE.parent)
    sys.path.insert(0, str(HERE.parent))
    import bluesky as bs
    bs.init(mode="sim", detached=True)
    bs.stack.stack("IC VVDN-XENKE-60MIN")
    bs.sim.op()

    track = {}          # acid -> [(t, lat, lon, alt_ft, gs_kt)]
    echo_err = []
    next_log = 0.0
    while bs.sim.simt < t_end:
        bs.sim.step()
        if bs.sim.simt >= next_log:
            for i, acid in enumerate(bs.traf.id):
                track.setdefault(acid, []).append(
                    (bs.sim.simt, float(bs.traf.lat[i]), float(bs.traf.lon[i]),
                     float(bs.traf.alt[i]) / 0.3048, float(bs.traf.gs[i]) / 0.514444))
            next_log += dt_log
    return track, echo_err


def B1_cham_banh(track):
    """Thoi diem va vi tri cham banh THAT do duoc trong mo phong."""
    td = {}
    for acid, pts in track.items():
        if not acid.startswith("ARR"):
            continue
        for (t, la, lo, alt, gs) in pts:
            if alt < 50 and hav_m(la, lo, *THR35L) < 3000:
                td[acid] = t
                break
    thieu = [a["id"] for a in ARRS if a["id"] not in td]
    check("B1. Moi chuyen den deu cham banh duoc trong mo phong", not thieu,
          f"{len(td)}/{len(ARRS)} chuyen cham banh"
          + (f", thieu: {thieu[:5]}" if thieu else ""),
          "Do truc tiep tu mo phong headless")
    lech = [(a["id"], td[a["id"]] - a["td"]) for a in ARRS if a["id"] in td]
    if lech:
        mx = max(lech, key=lambda x: abs(x[1]))
        results.append(("B2. Sai lech cham banh thuc te so voi lich", "SO LIEU",
                        f"trung binh {sum(abs(x[1]) for x in lech)/len(lech):.1f}s, "
                        f"lon nhat {abs(mx[1]):.1f}s ({mx[0]})",
                        "Do truc tiep tu mo phong headless"))
    return td


def B3_phan_cach_that(track, td):
    """Cu ly THAT giua tau sau va tau truoc tai dung thoi diem tau truoc cham banh."""
    xau, do_duoc = [], []
    for i in range(1, len(ARRS)):
        lead, tr = ARRS[i - 1], ARRS[i]
        if lead["id"] not in td or tr["id"] not in track:
            continue
        t0 = td[lead["id"]]
        p = min(track[tr["id"]], key=lambda x: abs(x[0] - t0))
        if abs(p[0] - t0) > 3:
            continue
        got = hav_m(p[1], p[2], *THR35L) / 1852.0
        need = can_ha_canh_nm(lead["type"], tr["type"])
        do_duoc.append((lead["id"], tr["id"], got, need))
        if got < need - 0.1:
            xau.append(f"{lead['id']}->{tr['id']}: {got:.2f}NM < {need}NM")
    check("B3. Cu ly THAT giua hai tau ha canh lien tiep (do trong mo phong)", not xau,
          f"{len(do_duoc)} cap do duoc, nho nhat "
          f"{min((x[2] for x in do_duoc), default=0):.2f}NM, {len(xau)} cap khong dat"
          + ("; " + "; ".join(xau[:4]) if xau else ""),
          NGUON_HA_CANH)
    return do_duoc


def B4_xung_dot(track):
    c = RULES["canh_bao_xung_dot"]
    times = {}
    for acid, pts in track.items():
        for p in pts:
            times.setdefault(round(p[0]), []).append((acid, p))
    canh_bao = []
    for t, lst in times.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, pa = lst[i]
                b, pb = lst[j]
                if pa[3] < 10 or pb[3] < 10:
                    # Chi xet XUNG DOT TREN KHONG: tau da cham banh (alt ~ 0)
                    # dang lan tren san thi khong the xung dot voi tau dang
                    # cat canh. Dieu kien "tau ha canh thap hon 3000ft" trong
                    # file cau hinh duoc hieu la tau DANG TIEP CAN, chua cham
                    # banh -- xem ghi chu dien giai trong vvdn_xenke_rules.json.
                    continue
                d = hav_m(pa[1], pa[2], pb[1], pb[2]) / 1852.0
                if d >= c["cu_ly_ngang_toi_thieu_NM"]:
                    continue
                dep = pa if a.startswith("DEP") else (pb if b.startswith("DEP") else None)
                arr = pb if a.startswith("DEP") else (pa if b.startswith("DEP") else None)
                if dep is None or arr is None:
                    continue
                if dep[3] > c["tau_cat_canh_cao_hon_ft"] and arr[3] < c["tau_ha_canh_thap_hon_ft"]:
                    canh_bao.append((t, a, b, d, dep[3], arr[3]))
    gop = {}
    for t, a, b, d, h1, h2 in canh_bao:
        k = tuple(sorted((a, b)))
        if k not in gop or d < gop[k][2]:
            gop[k] = (t, k, d, h1, h2)
    check("B4. Canh bao xung dot tren khong (tau di vs tau den)", not gop,
          f"{len(gop)} cap canh bao"
          + ("; " + "; ".join(f"{k[0]}/{k[1]} {v[2]:.2f}NM luc {fmt(v[0])}"
                              for k, v in list(gop.items())[:4]) if gop else ""),
          f"vvdn_xenke_rules.json > canh_bao_xung_dot "
          f"(di >{c['tau_cat_canh_cao_hon_ft']}ft, den <{c['tau_ha_canh_thap_hon_ft']}ft, "
          f"<{c['cu_ly_ngang_toi_thieu_NM']}NM)")
    return gop


def taxiway_segments():
    tc = json.loads((LAYOUT / "taxiway_centerlines.geojson").read_text(encoding="utf-8"))
    segs = []
    for f in tc["features"]:
        g = f["geometry"]
        lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for s in lines:
            for i in range(len(s) - 1):
                segs.append(((s[i][1], s[i][0]), (s[i + 1][1], s[i + 1][0])))
    return segs


def pt_seg_m(p, a, b):
    la = math.radians((a[0] + b[0]) / 2)
    ax, ay = (a[1] - p[1]) * math.cos(la) * 111320, (a[0] - p[0]) * 110540
    bx, by = (b[1] - p[1]) * math.cos(la) * 111320, (b[0] - p[0]) * 110540
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L2))
    return math.hypot(ax + t * dx, ay + t * dy)


def cua_so_lan():
    """Khoang thoi gian tung tau thuc su LAN TREN DUONG LAN.

    Tau den: tu khi thoat ly xong duong CHC den khi vao ben.
    Tau di : tu khi roi ben den khi LEN DUONG CHC (khong tinh thoi gian dung
             cho tren 35R -- luc do tau nam tren duong CHC chu khong phai
             duong lan, do khoang cach toi tim duong lan la vo nghia).
    """
    win = {}
    for a in ARRS:
        win[a["id"]] = (a.get("t_vacated", 0) + 5, a.get("t_onblock", 1e9))
    for d in DEPS:
        win[d["id"]] = (d["start_taxi"], d["lineup"])
    return win


def B5_lech_tim_duong_lan(track):
    """Chi xet pha LAN that: duoi 10 ft va duoi 25 kt (loai bo doan chay da
    tren duong CHC -- doan do tu nhien cach xa moi duong lan)."""
    segs = taxiway_segments()
    win = cua_so_lan()
    thong_ke = []
    for acid, pts in track.items():
        t0, t1 = win.get(acid, (0, 1e9))
        ds = [min(pt_seg_m((p[1], p[2]), *s) for s in segs)
              for p in pts if t0 <= p[0] <= t1 and p[3] < 10 and p[4] < 25]
        if len(ds) >= 10:
            thong_ke.append((acid, sum(ds) / len(ds), max(ds)))
    if not thong_ke:
        return check("B5. Bam tim duong lan", False, "khong do duoc diem nao", "-")
    tb = sum(x[1] for x in thong_ke) / len(thong_ke)
    xau = [x for x in thong_ke if x[1] > 15.0]
    check("B5. Pha lan bam tim duong lan that", not xau,
          f"{len(thong_ke)} tau, lech trung binh {tb:.1f} m, "
          f"lon nhat trung binh {max(x[1] for x in thong_ke):.1f} m"
          + (f"; {len(xau)} tau lech >15 m: {[x[0] for x in xau[:4]]}" if xau else ""),
          "taxiway_centerlines.geojson (so do san bay VVDN that)")


def B6_toc_do_lan(track):
    """Phat hien tau bi 'troi' trong pha LAN (loi da ghi nhan cua BlueSky:
    khoang trong giua hai lenh MOVE lam tau bay tu do).

    Do toc do bang DICH CHUYEN THAT giua hai mau ghi lien tiep, KHONG dung
    traf.gs: tai dung buoc co lenh MOVE, BlueSky quy doi quang duong MOVE dich
    tau ra toc do tuc thoi cua MOT buoc dt (0.05s) nen cho ra tri so vo nghia
    (da do duoc 1021 kt trong khi dich chuyen that chi 6.2 m/s). Chi xet trong
    cua so pha lan that: tau den tu luc thoat ly xong duong CHC den khi vao
    ben; tau di tu luc roi ben den truoc khi bat dau chay da.
    """
    win = cua_so_lan()
    xau = []
    for acid, pts in track.items():
        t0, t1 = win.get(acid, (0, 1e9))
        tr = [p for p in pts if t0 <= p[0] <= t1 and p[3] < 10]
        for i in range(1, len(tr)):
            dt = tr[i][0] - tr[i - 1][0]
            if dt <= 0:
                continue
            v = hav_m(tr[i - 1][1], tr[i - 1][2], tr[i][1], tr[i][2]) / dt / 0.514444
            if v > 60:
                xau.append((acid, tr[i][0], v))
                break
    lim = RULES["tham_so_lan"]["toc_do_lan_doan_thang_kt"]
    nhanh = []
    for acid, pts in track.items():
        t0, t1 = win.get(acid, (0, 1e9))
        tr = [p for p in pts if t0 <= p[0] <= t1 and p[3] < 10]
        for i in range(1, len(tr)):
            dt = tr[i][0] - tr[i - 1][0]
            if dt > 0:
                v = hav_m(tr[i - 1][1], tr[i - 1][2], tr[i][1], tr[i][2]) / dt / 0.514444
                nhanh.append(v)
    check("B6. Khong co tau bay bi 'troi' trong pha lan", not xau,
          f"{len(track)} tau, toc do lan lon nhat do duoc "
          f"{max(nhanh) if nhanh else 0:.1f} kt (gioi han thiet ke {lim} kt), "
          f"{len(xau)} tau vuot 60 kt"
          + ("; " + "; ".join(f"{a} {v:.0f}kt luc {fmt(t)}" for a, t, v in xau[:4]) if xau else ""),
          f"vvdn_xenke_rules.json > tham_so_lan (muc 6 prompt)")


AC_LEN = {"A320":37.57,"A321":44.51,"A20N":37.57,"A21N":44.51,"B738":39.47,"B38M":39.47,
          "B739":42.11,"E190":36.24,"A332":58.82,"A333":63.67,"A359":66.80,"B744":70.66,
          "B763":54.94,"B772":63.73,"B773":73.86,"B77W":73.86,"B788":56.72,"B789":62.81,
          "B748":76.30,"B78X":68.28}
TY = {**{a["id"]: a["type"] for a in ARRS}, **{d["id"]: d["type"] for d in DEPS}}


def B8_xung_dot_mat_dat(track):
    """Cu ly giua hai tau bay DANG LAN tren duong lan -- do trong mo phong.

    Nguong lay DUNG cong thuc cua plugin bluesky/plugins/surfacetaxi.py:
    nua chieu dai hai tau + taxi_tail_buffer (20 m), tuc "con lai sau duoi
    tau truoc", khong phai khoang cach tam-toi-tam.
    """
    buf = RULES["tham_so_lan"].get("dem_sau_duoi_tau_truoc_m", 20.0)
    win = cua_so_lan()
    byt = {}
    for acid, pts in track.items():
        t0, t1 = win.get(acid, (0, 1e9))
        for p in pts:
            if t0 <= p[0] <= t1 and p[3] < 10:
                byt.setdefault(round(p[0]), []).append((acid, p))
    xau, gan_nhat = {}, None
    for t, lst in byt.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, pa = lst[i]
                b, pb = lst[j]
                d = hav_m(pa[1], pa[2], pb[1], pb[2])
                req = (AC_LEN.get(TY.get(a, ""), 40) + AC_LEN.get(TY.get(b, ""), 40)) / 2 + buf
                if gan_nhat is None or d - req < gan_nhat[0] - gan_nhat[1]:
                    gan_nhat = (d, req, t, a, b)
                if d < req:
                    k = tuple(sorted((a, b)))
                    if k not in xau or d < xau[k][0]:
                        xau[k] = (d, req, t)
    ct = (f"{len(byt)} giay co tau dang lan, {len(xau)} cap vi pham")
    if gan_nhat:
        ct += (f"; cap sat nhau nhat {gan_nhat[3]}<->{gan_nhat[4]} "
               f"{gan_nhat[0]:.0f} m (yeu cau {gan_nhat[1]:.0f} m) luc {fmt(gan_nhat[2])}")
    if xau:
        ct += "; " + "; ".join(f"{k[0]}<->{k[1]} {v[0]:.0f}m<{v[1]:.0f}m luc {fmt(v[2])}"
                               for k, v in list(xau.items())[:4])
    check("B8. Cu ly giua hai tau bay dang lan (tranh nhau khi lan)", not xau, ct,
          "bluesky/plugins/surfacetaxi.py (taxi_tail_buffer = 20 m) "
          "+ vvdn_xenke_rules.json > tham_so_lan (muc 6 prompt)")


def B9_lineup_dung_tim_35R(track):
    """Tau bay len duong CHC 35R phai nam tren TIM 35R that."""
    rc = json.loads((LAYOUT / "runway_centerlines.geojson").read_text(encoding="utf-8"))
    cl = None
    for f in rc["features"]:
        if f["properties"].get("name") == "17L/35R":
            c = f["geometry"]["coordinates"]
            pts = c if f["geometry"]["type"] == "LineString" else c[0]
            cl = [(p[1], p[0]) for p in pts]
    if cl is None:
        return check("B9. Tau bay len duong CHC dung tim 35R", False,
                     "khong tim thay tim 17L/35R trong runway_centerlines.geojson", "-")
    # Do tu DUNG thoi diem bat dau chay da den khi roi dat. KHONG do tu
    # thoi diem "len duong CHC": trong khoang do tau bay con dang lan TU
    # diem cho vao, ma diem cho (PREHOLD, cuoi tuyen lan ra) nam cach tim
    # duong CHC 112 m -- dung nhu no phai the, vi diem cho bat buoc nam
    # NGOAI duong CHC.
    lech, tai_roll = [], []
    for d in DEPS:
        pts = track.get(d["id"])
        if not pts:
            continue
        p0 = min(pts, key=lambda q: abs(q[0] - d["roll"]))
        tai_roll.append((d["id"], min(pt_seg_m((p0[1], p0[2]), cl[k], cl[k + 1])
                                      for k in range(len(cl) - 1))))
        # Chi lay doan tau bay CON LAN BANH tren duong CHC (alt ~ 0). Sau khi
        # roi dat tau bay vao SID va rat nhanh ra khoi pham vi duong CHC -- do
        # khoang cach toi tim luc do la vo nghia (da do 2208 m, chinh la cu ly
        # toi dau bac duong CHC khi tau da bay qua no).
        seg = [q for q in pts if d["roll"] <= q[0] and q[3] < 10]
        if seg:
            lech.append((d["id"], max(min(pt_seg_m((q[1], q[2]), cl[k], cl[k + 1])
                                          for k in range(len(cl) - 1)) for q in seg)))
    if not tai_roll:
        return check("B9. Tau bay len duong CHC dung tim 35R", False,
                     "khong do duoc chuyen di nao", "-")
    xau = [x for x in tai_roll if x[1] > 10.0] + [x for x in lech if x[1] > 10.0]
    check("B9. Tau bay len duong CHC va chay da dung tim 35R", not xau,
          f"{len(tai_roll)} chuyen di: lech tim tai thoi diem bat dau chay da "
          f"lon nhat {max(x[1] for x in tai_roll):.1f} m; suot pha chay da "
          f"lon nhat {max((x[1] for x in lech), default=0):.1f} m"
          + (f"; {len(xau)} truong hop lech >10 m: {[x[0] for x in xau[:4]]}" if xau else ""),
          "runway_centerlines.geojson (tim duong CHC 17L/35R that cua VVDN)")


def B7_ve_den_ben(track):
    bens = {"ben 28": (16.051747, 108.202278), "ben 8": (16.059413, 108.201205)}
    xa = []
    for a in ARRS:
        pts = track.get(a["id"])
        if not pts:
            xa.append((a["id"], "khong ton tai trong mo phong"))
            continue
        la, lo = pts[-1][1], pts[-1][2]
        d = min(hav_m(la, lo, *v) for v in bens.values())
        if d > 50:
            xa.append((a["id"], f"dung cach ben gan nhat {d:.0f} m"))
    check("B7. Moi chuyen den deu lan ve toi ben do", not xa,
          f"{len(ARRS)-len(xa)}/{len(ARRS)} chuyen ve dung ben"
          + ("; " + "; ".join(f"{i}: {m}" for i, m in xa[:4]) if xa else ""),
          "gates.geojson (toa do ben 28 / ben 8 that)")


# ===========================================================================
# PHAN B (tiep) -- CAT QUA 35R, DUONG LAN E, GIAI PHONG 35L (MANOP)
# Hinh hoc doc TRUC TIEP tu runway_centerlines.geojson / taxiway_centerlines
# .geojson, khong lay tu generator.
# ===========================================================================
CODE = {k: v[0] for k, v in RULES["han_che_duong_lan_E"]["ma_chu_theo_loai"].items()}


def _he_35R():
    rc = json.loads((LAYOUT / "runway_centerlines.geojson").read_text(encoding="utf-8"))
    f = next(f for f in rc["features"] if f["properties"].get("name") == "17L/35R")
    c = f["geometry"]["coordinates"]
    c = c if f["geometry"]["type"] == "LineString" else c[0]
    pts = sorted((p[1], p[0]) for p in c)          # theo vi do: dau 35R (phia nam) truoc
    o = pts[0]

    def xy(la, lo):
        return ((lo - o[1]) * math.cos(math.radians(o[0])) * 111320.0, (la - o[0]) * 110574.0)
    ex, ey = xy(*pts[-1])
    n = math.hypot(ex, ey)
    ux, uy = ex / n, ey / n

    def st(la, lo):
        x, y = xy(la, lo)
        return x * ux + y * uy, x * uy - y * ux     # (doc tim, lech ngang; + = phia dong)
    return st, n, xy


ST35R, LEN35R, XY = _he_35R()


def vach_dung_cho():
    """(vach 35R phia tay, vach 35R phia dong, vach 35L phia dong) theo lech ngang
    so voi tim 35R (m), do tu cac doan 'hold' trong taxiway_centerlines.geojson
    tai khu vuc hai duong lan thoat ly G4/G6 (doc tim 2100-3300 m)."""
    tc = json.loads((LAYOUT / "taxiway_centerlines.geojson").read_text(encoding="utf-8"))
    tay, dong, l35 = [], [], []
    for f in tc["features"]:
        if "hold" not in str(f["properties"].get("name", "")).lower():
            continue
        g = f["geometry"]
        for ln in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]):
            for c in ln:
                s, x = ST35R(c[1], c[0])
                if not 2100 < s < 3300:
                    continue
                if -110 < x < 0:
                    tay.append(x)
                elif 0 < x < 110:
                    dong.append(x)
                elif -140 < x < -110:
                    l35.append(x)
    return min(tay), max(dong), max(l35)


def _phan_ung_s(actype):
    pu = RULES["thoi_gian_phan_ung_mat_dat"]
    return (pu["doi_chuan_den_chay_da_code_C_giay"] if CODE[actype] == "C"
            else pu["doi_chuan_den_chay_da_code_D_tro_len_giay"])


def _ho_so_dep(track):
    """{dep: [(t, doc tim 35R)]} tu luc chay da."""
    return {d["id"]: [(q[0], ST35R(q[1], q[2])[0]) for q in track.get(d["id"], [])
                      if q[0] >= d["roll"] - 1] for d in DEPS}


def _t_qua(ho_so, s_m, mac_dinh):
    return next((t for t, s in ho_so if s >= s_m), mac_dinh)


def B10_cat_canh_vs_den_that(track, td):
    """Do trong mo phong: (1) huan lenh cat canh (= chay da - thoi gian phan
    ung 10/15 s) SAU khi tau den truoc da cham cang; (2) tau den ke tiep con
    cach nguong 35L khong nho hon bang du thao/MANOP muc 4.2.1 tai luc CHAY DA
    (muon hon luc huan lenh -> tau den da gan hon -> do nhu vay la chat hon)."""
    M = RULES["phan_cach_cat_canh_vs_tau_den_35L"]["ma_tran"]
    xau, do = [], []
    for d in DEPS:
        t_clr = d["roll"] - _phan_ung_s(d["type"])
        truoc = [td[a["id"]] for a in ARRS if a["id"] in td and td[a["id"]] <= d["roll"]]
        if truoc and t_clr < max(truoc) - 0.5:
            xau.append(f"{d['id']}: huan lenh ~{fmt(t_clr)} truoc khi tau den cham cang {fmt(max(truoc))}")
        sau = [a for a in ARRS if a["id"] in td and td[a["id"]] > d["roll"]]
        if not sau:
            continue
        a = min(sau, key=lambda x: td[x["id"]])
        p = min(track[a["id"]], key=lambda q: abs(q[0] - d["roll"]))
        got = hav_m(p[1], p[2], *THR35L) / 1852.0
        need = M[wake(d["type"])][wake(a["type"])]
        do.append(got - need)
        if got < need - 0.05:
            xau.append(f"{d['id']}({wake(d['type'])[0]}) chay da khi {a['id']}({wake(a['type'])[0]}) "
                       f"con {got:.2f}NM < {need}NM")
    check("B10. Cat canh 35R vs tau den 35L (do trong mo phong)", not xau,
          f"{len(DEPS)} chuyen di; du cu ly nho nhat so voi bang {min(do, default=0):+.2f} NM; "
          f"{len(xau)} truong hop khong dat" + ("; " + "; ".join(xau[:4]) if xau else ""),
          NGUON_CAT_VS_DEN + "; huan lenh cat canh sau cham cang (muc 4.2.1.a)")


def B11_cat_qua_35R(track, td):
    """MANOP Phu luc 2 CHC song song: cat qua 35R <= 45 s (tu luc mui tau qua
    vach dung cho phia tay den luc duoi tau qua vach phia dong); khong cat qua
    trong khoang [huan lenh cat canh, tau cat canh qua diem cat + 100 m]; tau
    nam giua hai CHC -> 35L chua giai phong, nen tau ha canh truoc phai cat
    qua HET 35R truoc khi tau sau toi 2 NM (cap huan lenh ha canh)."""
    cfg = RULES["dieu_kien_cat_qua_35R"]
    clr_nm = RULES["phan_cach_ha_canh_lien_tiep_35L"]["giai_phong_truoc_huan_lenh_ha_canh"][
        "cu_ly_cap_huan_lenh_ha_canh_NM"]
    hl_w, hl_e, _ = vach_dung_cho()
    hs = _ho_so_dep(track)
    xau_tg, xau_dep, xau_hl, tg, dung = [], [], [], [], []
    cat = {}
    for a in ARRS:
        if a["id"] not in td:
            continue
        L = AC_LEN[a["type"]]
        pts = [(q[0],) + ST35R(q[1], q[2]) + (q[1], q[2]) for q in track[a["id"]] if q[0] > td[a["id"]]]
        t_in = next((p[0] for p in pts if p[2] >= hl_w - L / 2), None)
        t_out = next((p[0] for p in pts if p[2] >= hl_e + L / 2), None)
        if t_in is None or t_out is None:
            xau_tg.append(f"{a['id']}: khong thay cat qua 35R")
            continue
        s_c = min(pts, key=lambda p: abs(p[2]))[1]
        cat[a["id"]] = (t_in, t_out)
        tg.append(t_out - t_in)
        if t_out - t_in > cfg["thoi_gian_cat_qua_toi_da_s"] + 0.5:
            xau_tg.append(f"{a['id']}: {t_out - t_in:.0f}s")
        # thoi gian dung yen giua hai CHC truoc vach 35R
        n = 0
        for p, q in zip(pts, pts[1:]):
            if p[0] < t_in and -190 < p[2] < hl_w - L / 2 + 1 and hav_m(p[3], p[4], q[3], q[4]) < 0.5:
                n += q[0] - p[0]
        dung.append((a["id"], n))
        for d in DEPS:
            w0 = d["roll"] - _phan_ung_s(d["type"])
            w1 = _t_qua(hs[d["id"]], s_c + 100.0, d["roll"] + 90.0)
            if t_in < w1 and t_out > w0:
                xau_dep.append(f"{a['id']} cat qua {fmt(t_in)}-{fmt(t_out)} khi {d['id']} "
                               f"(huan lenh {fmt(w0)}, qua diem cat {fmt(w1)})")
    for i in range(len(ARRS) - 1):
        a, b = ARRS[i], ARRS[i + 1]
        if a["id"] not in cat or b["id"] not in track:
            continue
        t_out = cat[a["id"]][1]
        if b["id"] in td and td[b["id"]] <= t_out:
            xau_hl.append(f"{b['id']} cham banh {fmt(td[b['id']])} khi {a['id']} chua cat qua het 35R")
            continue
        p = min(track[b["id"]], key=lambda q: abs(q[0] - t_out))
        got = hav_m(p[1], p[2], *THR35L) / 1852.0
        if got < clr_nm:
            xau_hl.append(f"{a['id']} cat qua xong {fmt(t_out)} khi {b['id']} con {got:.2f}NM < {clr_nm}NM")
    dmax = max(dung, key=lambda x: x[1]) if dung else ("-", 0)
    check("B11a. Cat qua 35R xong trong gioi han thoi gian", not xau_tg,
          f"{len(tg)} lan cat qua, lau nhat {max(tg, default=0):.0f}s (vach dung cho do duoc: "
          f"{hl_w:.0f} m / +{hl_e:.0f} m)" + ("; " + "; ".join(xau_tg[:4]) if xau_tg else ""),
          "MANOP Phu luc 2 CHC song song: cat qua duong CHC trong vong 45 giay")
    check("B11b. Khong cat qua 35R khi tau cat canh chua qua diem cat", not xau_dep,
          f"{len(cat)} lan cat qua x {len(DEPS)} chuyen di, {len(xau_dep)} xung dot; dung cho giua hai "
          f"CHC lau nhat {dmax[1]:.0f}s ({dmax[0]})" + ("; " + "; ".join(xau_dep[:3]) if xau_dep else ""),
          "vvdn_xenke_rules.json > dieu_kien_cat_qua_35R (MANOP Phu luc 2 CHC song song)")
    check("B11c. Tau truoc cat qua het 35R truoc khi tau sau toi 2 NM", not xau_hl,
          f"{max(len(ARRS) - 1, 0)} cap, {len(xau_hl)} cap khong dat"
          + ("; " + "; ".join(xau_hl[:3]) if xau_hl else ""),
          "MANOP: huan lenh ha canh truoc 2 NM, chi khi tau ha canh truoc da roi duong CHC; "
          "tau dung cho giua hai CHC -> khong su dung 35L")


def B12_duong_lan_E(track):
    """MANOP: khi tau code D/E (kich ban ap ca F) cat canh 35R -- tu chay da den
    khi roi duong CHC -- chi tau code C tro xuong o tren duong lan E; khi tau code
    C cat canh, tau code E tro xuong duoc o tren E."""
    cfg = RULES["han_che_duong_lan_E"]
    allowed, tol, excl = cfg["khi_cat_canh_code"], cfg["dung_sai_quanh_tim_m"], cfg["loai_tru_quanh_PREHOLD_m"]
    tc = json.loads((LAYOUT / "taxiway_centerlines.geojson").read_text(encoding="utf-8"))
    segs = []
    for f in tc["features"]:
        if f["properties"].get("name") != "E":
            continue
        g = f["geometry"]
        for ln in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]):
            P = [XY(c[1], c[0]) for c in ln]
            segs += list(zip(P, P[1:]))

    def dseg(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        l2 = dx * dx + dy * dy
        f = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
        return math.hypot(p[0] - a[0] - f * dx, p[1] - a[1] - f * dy)
    ph = RULES["so_do_san_bay"]["diem_cho_cat_canh_35R"]["PREHOLD"]
    php = XY(ph[0], ph[1])
    types = {a["id"]: a["type"] for a in ARRS} | {d["id"]: d["type"] for d in DEPS}
    tren_E = {}
    for acid, pts in track.items():
        s = set()
        for (t, la, lo, alt, gs) in pts:
            if alt > 10:
                continue
            p = XY(la, lo)
            if math.dist(p, php) < excl:
                continue
            if min(dseg(p, *sg) for sg in segs) < tol:
                s.add(int(t))
        tren_E[acid] = s
    hs = _ho_so_dep(track)
    xau, n_kt = [], 0
    for d in DEPS:
        w0 = d["roll"]
        w1 = _t_qua(hs[d["id"]], LEN35R, d["roll"] + 90.0)
        ok_codes = allowed[CODE[d["type"]]]
        for other, secs in tren_E.items():
            if other == d["id"] or CODE[types[other]] in ok_codes:
                continue
            n_kt += 1
            hit = sorted(t for t in secs if w0 <= t <= w1)
            if hit:
                xau.append(f"{d['id']}({CODE[d['type']]}) cat canh {fmt(w0)}-{fmt(w1)} khi "
                           f"{other}({CODE[types[other]]}) tren E {fmt(hit[0])}-{fmt(hit[-1])}")
    check("B12. Duong lan E khi tau code D/E/F cat canh 35R", not xau,
          f"{len(DEPS)} lan cat canh, {len(xau)} vi pham"
          + ("; " + "; ".join(xau[:3]) if xau else ""),
          "MANOP Phu luc 2 CHC song song muc 3 'Phuong an khai thac duong lan E' "
          "[vung duong lan E: CAN XAC NHAN cach hieu]")


def B13_thoat_ly_35L(track, td):
    """MANOP: thoat ly 35L trong 100 s tu luc qua nguong toi khi qua vach dung
    cho cua duong lan thoat ly. Tau dung cho GIUA hai CHC truoc 35R (MANOP coi
    la vi tri dung cho, khi do khong su dung 35L) cung tinh la da thoat ly."""
    lim = RULES["thoi_gian_phan_ung_mat_dat"]["thoat_ly_duong_CHC_toi_da_giay"]
    hl_w, _, hl_35l = vach_dung_cho()
    s_thr = ST35R(*THR35L)[0]
    ds, xau = [], []
    for a in ARRS:
        if a["id"] not in td:
            continue
        L = AC_LEN[a["type"]]
        pts = [(q[0],) + ST35R(q[1], q[2]) for q in track[a["id"]] if q[0] >= td[a["id"]] - 90]
        t_thr = next((t for t, s, x in pts if s >= s_thr and x < -150), None)
        if t_thr is None:
            xau.append(f"{a['id']}: khong thay qua nguong")
            continue
        muc = min(hl_35l + L / 2, hl_w - L / 2 - 5.0)
        t_ok = next((t for t, s, x in pts if t > t_thr and x >= muc), None)
        if t_ok is None:
            xau.append(f"{a['id']}: khong thay thoat ly")
            continue
        ds.append((a["id"], t_ok - t_thr))
        if t_ok - t_thr > lim + 0.5:
            xau.append(f"{a['id']}: {t_ok - t_thr:.0f}s")
    mx = max(ds, key=lambda x: x[1]) if ds else ("-", 0)
    check("B13. Thoat ly 35L trong gioi han thoi gian", not xau,
          f"{len(ds)} chuyen den, lau nhat {mx[1]:.0f}s ({mx[0]}), gioi han {lim}s"
          + ("; " + "; ".join(xau[:4]) if xau else ""),
          "MANOP Phu luc 2 CHC song song (thoat ly trong vong 100 giay)")


def B14_diem_cho_that(track):
    """Do trong mo phong: so tau DI dang o khu diem cho truoc 35R (trong vong
    dung sai loai tru quanh PREHOLD, hoac da len duong CHC cho chay da) tai
    tung giay, tu luc vao khu do den luc bat dau chay da. Muc 6 prompt: <= 3."""
    lim = RULES["gioi_han_diem_cho"]["so_tau_toi_da"]
    vung = RULES["han_che_duong_lan_E"]["loai_tru_quanh_PREHOLD_m"] + 10.0
    ph = RULES["so_do_san_bay"]["diem_cho_cat_canh_35R"]["PREHOLD"]
    dem = {}
    for d in DEPS:
        for (t, la, lo, alt, gs) in track.get(d["id"], []):
            if t >= d["roll"] or alt > 10:
                continue
            s, x = ST35R(la, lo)
            tren_chc = abs(x) < 30 and s < 400
            if tren_chc or hav_m(la, lo, ph[0], ph[1]) < vung:
                dem.setdefault(int(t), set()).add(d["id"])
    peak_t = max(dem, key=lambda k: len(dem[k])) if dem else None
    peak = len(dem[peak_t]) if dem else 0
    phut = {}
    for t, s in dem.items():
        phut[t // 300] = max(phut.get(t // 300, 0), len(s))
    check("B14. So tau tai diem cho truoc 35R (do trong mo phong)", peak <= lim,
          f"lon nhat {peak} tau (luc {fmt(peak_t) if peak_t is not None else '-'}), gioi han {lim}; "
          "lon nhat theo khoang 5 phut: "
          + " ".join(f"{fmt(k * 300)[:5]}={v}" for k, v in sorted(phut.items())),
          "Muc 6 prompt -- yeu cau cung")


def bao_cao():
    w = max(len(r[0]) for r in results)
    n_fail = sum(1 for r in results if r[1] == "KHONG DAT")
    print("\n" + "=" * 100)
    print("KET QUA KIEM CHUNG KICH BAN VVDN-XENKE-60MIN")
    print("=" * 100)
    for muc, kl, ct, dk in results:
        print(f"\n[{kl:^9}] {muc}")
        print(f"            {ct}")
        print(f"            Nguon: {dk}")
    print("\n" + "=" * 100)
    print(f"TONG: {len(results)} muc kiem tra, {n_fail} muc KHONG DAT")
    print("=" * 100)
    return n_fail


def main():
    static_only = "--static" in sys.argv
    A1_co_cau_doi_tau()
    A2_phan_cach_ha_canh()
    A3_phan_cach_cat_canh()
    A4_cat_canh_vs_tau_den()
    A5_cham_cang_den_chay_da()
    A6_diem_cho()
    A7_len_duong_chc()
    A8_xen_ke()
    A10_lan_khong_am()
    A11_tao_tai_IAF()
    A9_thong_luong()

    if not static_only:
        t_end = max([a.get("t_onblock", a["td"]) for a in ARRS]
                    + [d["roll"] for d in DEPS]) + 60.0
        print(f"Dang chay mo phong headless den {fmt(t_end)} ...")
        track, _ = run_headless(t_end)
        print(f"Da ghi quy dao {len(track)} tau bay.")
        json.dump({k: v for k, v in track.items()},
                  open(HERE / "VVDN-XENKE-60MIN.track.json", "w"), separators=(",", ":"))
        td = B1_cham_banh(track)
        B3_phan_cach_that(track, td)
        B4_xung_dot(track)
        B5_lech_tim_duong_lan(track)
        B6_toc_do_lan(track)
        B7_ve_den_ben(track)
        B8_xung_dot_mat_dat(track)
        B9_lineup_dung_tim_35R(track)
        B10_cat_canh_vs_den_that(track, td)
        B11_cat_qua_35R(track, td)
        B12_duong_lan_E(track)
        B13_thoat_ly_35L(track, td)
        B14_diem_cho_that(track)

    n = bao_cao()
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
