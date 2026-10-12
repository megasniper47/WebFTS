"""
vvpq_pq404_chokepoint_4min.scn

Kich ban stress-test diem nghen PQ404 tai VVPQ (RNP Z RWY10L), theo yeu cau:
- Tau bay den giai cach 4 phut khi bay qua PQ404, ve theo 4 STAR RNP that
  cua duong CHC 10L/R (NUMDI 3F, OSOTA 3F, TUNPO 3F, ADBOP 3F), roi nhap
  chung vao GUKNU/LASOV -> PQ404 (IF) -> PQ402 (FAF) -> PQ400 (MAPT) ->
  cham banh RWY10L.
- Tau bay cat canh giai cach ~4 phut tren duong CHC 10R (theo cap voi lan
  cham banh), SID PBN ngau nhien trong 4 SID that (NUMDI 3D, OSOTA 3D,
  RG 3D, ADBOP 3D).
- Khi tau bay den cham banh duoc 30 giay, tau bay cat canh (ghep cap voi
  lan cham banh do) duoc phep chay da.
- Tau bay ha canh cham banh duoc 80 giay thi "bien mat" (DEL) o cuoi CHC10L.

Nguon du lieu that: Quyet dinh 1287/QD-CHK ngay 12/6/2026 cua Cuc HKVN
("Phu dinh 2" - PBN: SID/STAR RNP + RNP Z RWY10L/10R), file:
"vietnam_ats_routes_pack/Du lieu PTB + code/PTB QLBMN/PTB PQ/
2026.06.12 1287-QD-CHK Phu Quoc - Full VOR, PBN CHC hien huu + CHC moi.pdf"

Toa do tat ca waypoint duoc chuyen doi truc tiep tu bang WGS-84 (DMS) trong
tai lieu tren -- khong bia so lieu. Toc do bay tren tung chang la gia tri
uoc luong TRUNG BINH dua tren gioi han toc do (speed limit) that ghi trong
bang "Tabular Description" cua tai lieu (khong phai mo phong dong luc hoc
BADA day du) -- dung de tinh thoi diem CRE sao cho thoi diem qua PQ404
giai cach dung 4 phut; sai so thuc te khi chay BlueSky co the lech vai chuc
giay tuy toc do khai bao/gio bay thuc te cua tung loai tau bay.

Do dai duong CHC 10L khong co trong tai lieu nguon (chi co toa do nguong
CHC) -- diem "cuoi duong CHC" dung de tau bay "bien mat" duoc uoc luong
~1.6 NM tinh tu nguong theo huong CHC (096 T), tuong duong ~3000m, MOT GIA
TRI GIA DINH hop ly cho duong CHC phuc vu A320/A321, KHONG phai so lieu
chinh thuc.
"""
import math
import random
import os
import shutil
import datetime
from pathlib import Path

if hasattr(os, "add_dll_directory"):
    pass

random.seed(20260813)

OUT_DIR = Path(".")
BACKUP_ROOT = Path("Backup")
OUT_FILE = OUT_DIR / "vvpq_pq404_chokepoint_4min.scn"


def dms(d, m, s, hemi):
    val = d + m / 60.0 + s / 3600.0
    if hemi in ("S", "W"):
        val = -val
    return val


# ---------------------------------------------------------------------------
# Real waypoint coordinates (WGS-84), from Quyet dinh 1287/QD-CHK 12/6/2026
# Phu dinh 2 - Phu luc 1A (SID RNP RWY10L/R), 3A (STAR RNP RWY10L/R),
# 5A (RNP Z RWY10L), 6A (RNP Z RWY10R).
# ---------------------------------------------------------------------------
WPT = {
    "NUMDI":  (dms(10, 26, 43.0, "N"), dms(103, 46, 35.0, "E")),
    "OSOTA":  (dms(10, 33, 7.0, "N"), dms(104, 15, 49.0, "E")),
    "TUNPO":  (dms(10, 3, 44.0, "N"), dms(104, 35, 22.0, "E")),
    "ADBOP":  (dms(8, 30, 0.0, "N"), dms(104, 5, 0.0, "E")),
    "TIHAN":  (dms(10, 6, 24.0, "N"), dms(104, 21, 9.0, "E")),
    "PQ500":  (dms(10, 16, 31.9, "N"), dms(104, 2, 19.0, "E")),
    "GUKNU":  (dms(10, 17, 50.3, "N"), dms(103, 49, 8.7, "E")),
    "VIBIL":  (dms(9, 20, 6.9, "N"), dms(104, 3, 40.0, "E")),
    "MEBMI":  (dms(9, 36, 52.1, "N"), dms(103, 53, 12.0, "E")),
    "BUVSU":  (dms(9, 48, 45.7, "N"), dms(103, 50, 54.5, "E")),
    "LASOV":  (dms(10, 5, 7.5, "N"), dms(103, 47, 52.0, "E")),
    "PQ404":  (dms(10, 11, 28.9, "N"), dms(103, 48, 30.3, "E")),
    "PQ402":  (dms(10, 11, 4.4, "N"), dms(103, 52, 39.6, "E")),
    "PQ400":  (dms(10, 10, 41.6, "N"), dms(103, 56, 29.0, "E")),
    "RW10L":  (dms(10, 10, 27.93, "N"), dms(103, 58, 47.24, "E")),
    "RW10R":  (dms(10, 10, 16.28, "N"), dms(103, 58, 46.07, "E")),
    "PQ410":  (dms(10, 9, 32.4, "N"), dms(104, 8, 6.6, "E")),
    "PQ411":  (dms(10, 15, 53.8, "N"), dms(104, 8, 45.4, "E")),
    "MEKAV":  (dms(10, 18, 10.8, "N"), dms(104, 0, 23.4, "E")),
    "PQ600":  (dms(10, 9, 10.2, "N"), dms(104, 9, 51.8, "E")),
    "PQ601":  (dms(10, 18, 13.3, "N"), dms(104, 12, 6.7, "E")),
    "PQ602":  (dms(10, 22, 8.4, "N"), dms(104, 0, 21.1, "E")),
    "PQ603":  (dms(10, 23, 31.2, "N"), dms(103, 56, 12.3, "E")),
    "PQ620":  (dms(9, 54, 58.0, "N"), dms(104, 16, 45.0, "E")),
    "SAMIX":  (dms(9, 52, 12.0, "N"), dms(104, 31, 27.0, "E")),
    "VILIT":  (dms(9, 47, 46.0, "N"), dms(104, 54, 53.0, "E")),
    "RG":     (dms(9, 57, 34.0, "N"), dms(105, 7, 59.0, "E")),
    "PIKUD":  (dms(9, 48, 43.7, "N"), dms(104, 16, 45.2, "E")),
    "DOVTA":  (dms(9, 36, 50.2, "N"), dms(104, 16, 44.9, "E")),
}

RWY_HEADING_TRUE = 095.7  # RWY 10L/10R true heading (approach course 096(095.7T))
END_OF_RWY10L_NM = 1.6    # gia dinh do dai CHC ~3000m (khong co trong tai lieu goc)


def dest_point(lat, lon, brg_deg, dist_nm):
    R_nm = 3440.065
    brg = math.radians(brg_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    d_r = dist_nm / R_nm
    lat2 = math.asin(math.sin(lat1) * math.cos(d_r) + math.cos(lat1) * math.sin(d_r) * math.cos(brg))
    lon2 = lon1 + math.atan2(
        math.sin(brg) * math.sin(d_r) * math.cos(lat1),
        math.cos(d_r) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


END_OF_RWY10L = dest_point(WPT["RW10L"][0], WPT["RW10L"][1], RWY_HEADING_TRUE, END_OF_RWY10L_NM)

# ---------------------------------------------------------------------------
# 4 STAR RNP that (NUMDI 3F, OSOTA 3F, TUNPO 3F, ADBOP 3F) -- moi transition
# la 1 chuoi (wpt, alt_ft_or_None, spd_kt_or_None) tu diem vao STAR toi
# GUKNU hoac LASOV (diem nhap chung vao RNP Z RWY10L/10R qua PQ404/PQ405).
# Cu ly (NM) va gioi han toc do lay dung theo bang Tabular Description that.
# ---------------------------------------------------------------------------
STAR_TRANSITIONS = {
    # "entry_heading" = magnetic course (deg M) of the first real leg out of
    # the entry fix, from the tabular "Flyover Course deg M(deg T)" column --
    # used as the CRE heading (matches the convention already used in the
    # real vvpq_busiest_hour_01aug2026_0920-1020.scn, e.g. OSOTA entry -> 219).
    "NUMDI 3F": {
        "entry": ("NUMDI", 8000, 230),
        "entry_heading": 164,
        "legs": [("GUKNU", 5000, 200)],
        "dist_nm": 9.19,
        "avg_speed_kt": 215,  # trung binh 230->200 theo gioi han that
        "merge": "GUKNU",
    },
    "OSOTA 3F": {
        "entry": ("OSOTA", 11000, None),  # FL110
        "entry_heading": 219,
        "legs": [("PQ500", 9000, 230), ("GUKNU", 5000, 200)],
        "dist_nm": 21.20 + 13.05,
        "avg_speed_kt": 225,
        "merge": "GUKNU",
    },
    "TUNPO 3F": {
        "entry": ("TUNPO", None, None),
        "entry_heading": 281,
        "legs": [("TIHAN", None, None), ("PQ500", 9000, 230), ("GUKNU", 5000, 200)],
        "dist_nm": 14.27 + 21.13 + 13.05,
        "avg_speed_kt": 235,
        "merge": "GUKNU",
    },
    "ADBOP 3F": {
        "entry": ("ADBOP", None, None),
        "entry_heading": 358,
        "legs": [("VIBIL", 13500, None), ("MEBMI", None, None), ("BUVSU", None, 230), ("LASOV", 5000, 200)],
        "dist_nm": 49.90 + 19.62 + 12.05 + 16.56,
        "avg_speed_kt": 250,
        "merge": "LASOV",
    },
}

# ---------------------------------------------------------------------------
# Doan chung RNP Z RWY10L sau khi nhap tai GUKNU/LASOV: -> PQ404 (IF) ->
# PQ402 (FAF) -> PQ400 (MAPT, VPA -3.0deg/TCH50) -> RW10L (cham banh).
# Toc do gia dinh giam dan hop ly (khong co trong bang vi day la doan tiep
# can cuoi, BlueSky se tu giam toc theo VNAV).
# ---------------------------------------------------------------------------
FINAL_SEGMENT = [
    ("PQ404", 2500, 180),
    ("PQ402", 2000, 160),
    ("PQ400", 790, 145),
    ("RW10L", 0, 140),   # cham banh
]
FINAL_SEGMENT_DIST_NM = 6.36 + 4.11 + 3.80  # entry(GUKNU/LASOV)->PQ404 + PQ404->PQ402 + PQ402->PQ400(MAPT)
FINAL_SEGMENT_AVG_SPEED_KT = 165  # trung binh giam toc tren toan doan cuoi
TOUCHDOWN_TO_DEL_SEC = 80.0  # tau bay den "bien mat" 80 giay sau khi cham cang


def transit_minutes(transition_key):
    t = STAR_TRANSITIONS[transition_key]
    star_min = t["dist_nm"] / t["avg_speed_kt"] * 60.0
    final_min = FINAL_SEGMENT_DIST_NM / FINAL_SEGMENT_AVG_SPEED_KT * 60.0
    return star_min + final_min


# ---------------------------------------------------------------------------
# 4 SID PBN that tu RWY10R (NUMDI 3D, OSOTA 3D, RG 3D, ADBOP 3D), tat ca
# xuat phat tu PQ600 (IF chung sau initial climb 096T len 500ft).
# ---------------------------------------------------------------------------
SID_ROUTES = {
    # Ca 4 SID that deu chung doan "INITIAL CLIMB RWY 10L/10R -> DF PQ600"
    # roi moi phan ky tai PQ600 (IF) theo dung bang "FROM PQ600" trong tai
    # lieu -- truoc day script bo qua PQ600 va cat thang toi diem phan ky
    # dau tien cua tung SID, sai voi hinh dang phuong thuc that.
    "NUMDI 3D": [("PQ600", None, None), ("PQ601", 5000, 250), ("PQ602", 8000, 250), ("PQ603", 9000, 250), ("NUMDI", None, 280)],
    "OSOTA 3D": [("PQ600", None, None), ("OSOTA", 6000, 280)],
    "RG 3D":    [("PQ600", None, None), ("PQ620", 7000, 250), ("SAMIX", None, 280), ("VILIT", None, 280), ("RG", None, 280)],
    "ADBOP 3D": [("PQ600", None, None), ("PQ620", 7000, 250), ("PIKUD", None, 250), ("DOVTA", None, 250), ("VIBIL", 13500, 250), ("ADBOP", None, 280)],
}

MEDIUM_TYPES_REAL_BADA = ["A320", "A321", "A20N", "A21N"]  # xac nhan co file OPF that trong du an

AIRLINE_PREFIXES = ["VN", "VJ", "9G", "QH", "BL"]  # cac hang that dang khai thac VVPQ (theo kich ban da xac thuc truoc)


def fmt_time(total_sec):
    if total_sec < 0:
        total_sec = 0
    h = int(total_sec // 3600)
    m = int((total_sec % 3600) // 60)
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def backup_existing():
    if not OUT_FILE.exists():
        return
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest = BACKUP_ROOT / f"VVPQ {ts}"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT_FILE, dest / OUT_FILE.name)
    print(f"Da backup {OUT_FILE} -> {dest}")


def build_arrival_lines(callsign, ac_type, transition_key, pq404_cross_time_sec):
    t = STAR_TRANSITIONS[transition_key]
    transit_sec = transit_minutes(transition_key) * 60.0
    cre_time = pq404_cross_time_sec - transit_sec
    if cre_time < 0:
        raise ValueError(f"CRE time am cho {callsign} ({transition_key}); tang OFFSET_MIN.")

    entry_name, entry_alt, entry_spd = t["entry"]
    entry_lat, entry_lon = WPT[entry_name]
    heading_to_first = t["entry_heading"]

    lines = []
    lines.append(f"# --- {callsign} ARR VVPQ RWY10L (STAR {transition_key}) ({ac_type}) ---")
    alt_str = f"FL{entry_alt // 100}" if entry_alt and entry_alt >= 10000 else (str(entry_alt) if entry_alt else "FL110")
    spd_str = str(entry_spd) if entry_spd else "230"
    t0 = fmt_time(cre_time)
    lines.append(f"{t0}>CRE {callsign},{ac_type},{entry_lat:.6f},{entry_lon:.6f},{heading_to_first:.0f},{alt_str},{spd_str}")

    for wpt_name, alt_ft, spd_kt in t["legs"]:
        lat, lon = WPT[wpt_name]
        parts = [f"{lat:.6f}", f"{lon:.6f}"]
        if alt_ft is not None:
            parts.append(str(alt_ft))
            if spd_kt is not None:
                parts.append(str(spd_kt))
        lines.append(f"{t0}>{callsign} ADDWPT {','.join(parts)}")

    for wpt_name, alt_ft, spd_kt in FINAL_SEGMENT:
        lat, lon = WPT[wpt_name]
        lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{alt_ft},{spd_kt}")

    # Rollout past touchdown to the (assumed) far end of RWY10L -- the point
    # where the aircraft is scheduled to "disappear" per the user's request.
    lat_end, lon_end = END_OF_RWY10L
    lines.append(f"{t0}>{callsign} ADDWPT {lat_end:.6f},{lon_end:.6f},0,30")

    lines.append(f"{t0}>{callsign} SPD {spd_str}")
    lines.append(f"{t0}>{callsign} LNAV ON")
    lines.append(f"{t0}>{callsign} VNAV ON")

    touchdown_time = pq404_cross_time_sec + (FINAL_SEGMENT_DIST_NM / FINAL_SEGMENT_AVG_SPEED_KT * 60.0)
    del_time = touchdown_time + TOUCHDOWN_TO_DEL_SEC
    lines.append(f"{fmt_time(del_time)}>DEL {callsign}")
    lines.append("")
    return lines, touchdown_time


def build_departure_lines(callsign, ac_type, sid_key, roll_time_sec):
    lat0, lon0 = WPT["RW10R"]
    t0 = fmt_time(roll_time_sec)
    lines = []
    lines.append(f"# --- {callsign} DEP VVPQ RWY10R (SID {sid_key}) ({ac_type}) ---")
    lines.append(f"{t0}>CRE {callsign},{ac_type},{lat0:.6f},{lon0:.6f},96,0,0")
    t1 = fmt_time(roll_time_sec + 10.0)
    lines.append(f"{t1}>{callsign} HDG 96")
    lines.append(f"{t1}>{callsign} SPD 160")

    t2 = fmt_time(roll_time_sec + 35.0)
    legs = SID_ROUTES[sid_key]
    first_alt, first_spd = None, None
    for wpt_name, alt_ft, spd_kt in legs:
        lat, lon = WPT[wpt_name]
        if alt_ft is not None:
            lines.append(f"{t2}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{alt_ft},{spd_kt}")
        else:
            lines.append(f"{t2}>{callsign} ADDWPT {lat:.6f},{lon:.6f}")

    lines.append(f"{t2}>{callsign} LNAV ON")
    lines.append(f"{t2}>{callsign} VNAV ON")
    lines.append(f"{t2}>{callsign} ALT 7000")
    lines.append(f"{t2}>{callsign} SPD 250")

    del_time = roll_time_sec + 3600.0  # xoa sau 1h bay (quy uoc chung du an)
    lines.append(f"{fmt_time(del_time)}>DEL {callsign}")
    lines.append("")
    return lines


def main():
    backup_existing()

    N_PER_TRANSITION = 5
    PQ404_SEP_SEC = 240.0
    TOUCHDOWN_TO_ROLL_SEC = 30.0

    transitions_cycle = list(STAR_TRANSITIONS.keys())
    n_arr = N_PER_TRANSITION * len(transitions_cycle)

    # OFFSET_MIN chi can du lon de chuyen tiep NHANH NHAT (NUMDI) co the
    # duoc gan vao slot dau tien (i=0) ma van CRE >= 0 -- neu dat OFFSET_MIN
    # du cho ca chuyen tiep CHAM NHAT (ADBOP, ~28.7 phut) thi khong co tau
    # bay nao xuat hien tren man hinh trong 25+ phut dau, gay hieu ung
    # "khong thay tau bay dau" du kich ban van dung logic giai cach.
    OFFSET_MIN = math.ceil(transit_minutes("NUMDI 3F")) + 0.5

    transit_sec_by_key = {k: transit_minutes(k) * 60.0 for k in transitions_cycle}
    min_slot = {
        k: max(0, math.ceil((transit_sec_by_key[k] - OFFSET_MIN * 60.0) / PQ404_SEP_SEC))
        for k in transitions_cycle
    }
    remaining = {k: N_PER_TRANSITION for k in transitions_cycle}
    arr_order = [None] * n_arr
    # Gan tu slot CUOI ve slot DAU: o moi slot, uu tien chuyen tiep bi rang
    # buoc chat nhat (min_slot lon nhat) truoc, de danh cac slot som cho
    # chuyen tiep nhanh hon -- dam bao kha thi (CRE >= 0) cho ca 4 STAR ma
    # van xen ke thay vi don khoi theo tung STAR.
    for idx in range(n_arr - 1, -1, -1):
        candidates = [k for k in transitions_cycle if remaining[k] > 0 and min_slot[k] <= idx]
        if not candidates:
            raise RuntimeError(f"Khong the gan chuyen tiep kha thi cho slot {idx}; tang OFFSET_MIN.")
        candidates.sort(key=lambda k: (-min_slot[k], -remaining[k]))
        chosen = candidates[0]
        arr_order[idx] = chosen
        remaining[chosen] -= 1

    sid_cycle = list(SID_ROUTES.keys())

    all_lines = ["00:00:00.00>ASAS OFF", ""]
    arr_counter = 0
    dep_counter = 0
    touchdown_times = []

    for i, transition_key in enumerate(arr_order):
        arr_counter += 1
        callsign = f"{random.choice(AIRLINE_PREFIXES)}{1000 + arr_counter}"
        ac_type = random.choice(MEDIUM_TYPES_REAL_BADA)
        pq404_cross_time_sec = OFFSET_MIN * 60.0 + i * PQ404_SEP_SEC
        lines, touchdown_time = build_arrival_lines(callsign, ac_type, transition_key, pq404_cross_time_sec)
        all_lines.extend(lines)
        touchdown_times.append(touchdown_time)

    for i, touchdown_time in enumerate(touchdown_times):
        dep_counter += 1
        callsign = f"{random.choice(AIRLINE_PREFIXES)}{2000 + dep_counter}"
        ac_type = random.choice(MEDIUM_TYPES_REAL_BADA)
        sid_key = random.choice(sid_cycle)
        roll_time_sec = touchdown_time + TOUCHDOWN_TO_ROLL_SEC
        lines = build_departure_lines(callsign, ac_type, sid_key, roll_time_sec)
        all_lines.extend(lines)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")

    total_min = (touchdown_times[-1] + TOUCHDOWN_TO_DEL_SEC) / 60.0
    print(f"Da sinh {OUT_FILE} -- {n_arr} tau bay den (PQ404 giai cach {PQ404_SEP_SEC:.0f}s), "
          f"{n_arr} tau bay di (giai cach ~{PQ404_SEP_SEC:.0f}s theo cap voi lan cham banh), "
          f"tong thoi luong ~{total_min:.1f} phut.")


if __name__ == "__main__":
    main()
