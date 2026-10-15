"""
VVPQ-VVDN-5acft-3min-CADAS.scn

5 tau bay A320 (VVPQ01..VVPQ05) cat canh VVPQ RWY 10R (SID that RG 3D --
RWY 10L chi dung cho ha canh, khong co SID 10L, xem bao cao Buoc 0), bay
qua VVDN ha canh RWY 35L theo STAR that "LATOM 2K", cach nhau DUNG 3 phut
(180s) tai waypoint CADAS -- diem hoi tu that cua nhieu STAR VVDN.

TOAN BO waypoint la du lieu THAT, khong bia -- nguon cu the tung doan:

1. SID RG 3D (VVPQ, RWY 10R that): PQ600 -> PQ620 (7000ft) -> SAMIX -> VILIT -> RG
   Nguon: vvpq_procedures.py (da transcribe tu PDF AIP VVPQ).

2. Doan "bridge" enroute TSH - PATMA - SADAS - DADEN (noi tu diem cuoi SID
   la RG sang diem dau STAR la LATOM; nguoi dung chi dinh, da xac minh
   tung diem):
   - TSH: "TAN SON NHAT DVOR/DME (TSH)", airways_enr31_legacy.json
   - PATMA/SADAS/DADEN: AIP ENR 3.1/3.3 (W12/Q7/G474)
   Khong co do cao cong bo rieng cho doan enroute nay trong du an (day la
   waypoint DIEM BAO CAO, khong phai procedure leg co rang buoc do cao).
   PROFILE DO CAO (LUA CHON KHAI THAC theo yeu cau nguoi dung, KHONG phai
   so lieu AIP): sau khi het SID RG 3D, leo len muc bay duong dai FL310 va
   giu suot TSH/PATMA/SADAS/DADEN; sau DADEN ha dan de dat DUNG FL250 tai
   LATOM, roi tu LATOM moi vao STAR LATOM 2K.

3. STAR "LATOM 2K" (VVDN, RWY 35L that): LATOM(IF) -> NOVAN -> NOCKA ->
   DN368 -> VIDAN -> DOTEN -> TRACO -> CADAS -> MONRY -> TAMLA -> KALET ->
   NB2 -> DN351 -> RW35L.
   Nguon: AD 2-VVDN-11-10, AIP Viet Nam, AMDT 01/23 (trang 76,
   "vietnam_ats_routes_pack/PTB QLBMT/scan_detail.json") cho doan
   LATOM->TAMLA; doan TAMLA->RW35L da co san, that, trong vvdn_procedures.py
   (tai su dung nguyen, cung chuoi da dung cho STAR DOTEN).
   Do cao: NOVAN=+FL110, NOCKA=+FL100, DN368=khong rang buoc (bang cong bo
   de trong, khong phai thieu du lieu), VIDAN=+2150m (~7054ft, lay gia tri
   AT-OR-ABOVE ro rang, bo qua so thu 2 "-420" do nghi OCR loi -- da xac
   nhan voi nguoi dung). Doi chieu: DOTEN=+1850m=6070ft khop CHINH XAC voi
   gia tri that da dung truoc do trong du an -- xac nhan nguon dang tin cay.

4. Toc do: SID dung schedule leo cao chuan (V2+20 duoi 3000ft, 250kt duoi
   FL100, 280kt tren) -- cung quy uoc voi capacity_scenario_engine.
   NOVAN/NOCKA/DN368/VIDAN khong co toc do cong bo (bang AIP de trong o
   cot Speed limit) -- dung BADA-style descent schedule (>=FL140:250kt,
   >=6000ft:230kt) cung cong thuc voi capacity_scenario_engine._bada_
   descent_speed_kt. DOTEN tro di dung dung toc do THAT da transcribe tu
   _KB5GEN_ARR_APPROACH_ARRxxx.scn (A320: 250/230/205/190/175/165/150/
   150/130 kt tai DOTEN/TRACO/CADAS/MONRY/TAMLA/KALET/NB2/DN351/THR).

Vi CA 5 tau cung loai (A320) + cung SID (RG 3D) + cung toan bo route -- khong
co khac biet toc do/profile giua cac tau -- nen cach deu nhau N phut luc cat
canh se cho CHINH XAC cach deu N phut tai MOI diem doc theo route, bao gom
CADAS (khong can tinh nguoc thoi gian phuc tap nhu truong hop nhieu loai
tau bay/nhieu SID khac nhau).

Lich cat canh TUYET DOI (khong dung dieu kien ghep ATDIST+DELAY):
  VVPQ01: 00:00:30   VVPQ02: 00:03:30   VVPQ03: 00:06:30
  VVPQ04: 00:09:30   VVPQ05: 00:12:30

LUU Y khi xem truc tiep: chang VVPQ->VVDN dai ~600NM nen DU cat canh som,
tau van mat ~2 tieng MO PHONG moi toi CADAS. De xem het kich ban trong vai
phut thuc te, dat DTMULT 64 (hoac cao hon) ngay sau khi mo.
"""
from __future__ import annotations

import math
import random
import shutil
import sys
from datetime import datetime
from pathlib import Path

OUT_FILE = Path("VVPQ-VVDN-5acft-3min-CADAS.scn")
BACKUP_DIR = Path("Backup")

SCENARIO_START_SEC = 30.0  # 00:00:30 -- tau dau xuat hien gan nhu ngay khi mo
CADAS_GAP_SEC = 180.0  # 3 phut -- gian cach YEU CAU tai CADAS

# ---------------------------------------------------------------------------
# 5 LOAI TAU BAY -- deu la loai Viet Nam dang khai thac that va deu nam trong
# danh sach 12 loai da duoc du an xac nhan tu VVDN_KB5_1HOUR_MIXED.scn (xem
# _gen_vvdn_minsep_pairs_from_doten.py), nen moi loai vua co bang toc do BADA
# that, vua co toc do tiep can that da transcribe san.
#
# BADA 3.16, doc nguyen tu hang "CD ... AV" trong file .APF that
# (FTS Server/bluesky/data/performance/bada/<TYPE>__.APF), layout 9 gia tri
# theo BADA User Manual: CAScl1/CAScl2/Mcl | CAScr1/CAScr2/Mcr | Mdes/CASdes2/
# CASdes1. Khong bia, khong lam tron -- so nao trong file la so do.
# ---------------------------------------------------------------------------
BADA = {
    # type:  (CAScl1, CAScl2, Mcl,  CAScr2, Mcr,  Mdes, CASdes2, CASdes1)
    "A320": (310, 310, 0.78, 310, 0.78, 0.79, 300, 300),
    "A321": (310, 310, 0.78, 300, 0.78, 0.78, 300, 300),
    "A20N": (310, 310, 0.78, 310, 0.78, 0.79, 300, 300),
    "A21N": (300, 300, 0.79, 300, 0.79, 0.79, 300, 300),
    "B739": (300, 300, 0.79, 300, 0.79, 0.79, 300, 300),
}

# V2 (toc do an toan khi cat canh) theo tung loai -- UOC LUONG hop ly theo
# hang/kich co, KHONG phai so lieu BADA (file .APF khong cong bo V2; no nam
# trong .OPF duoi dang Vstall va con phu thuoc khoi luong/cau hinh canh thuc
# te cua tung chuyen bay).
V2_BY_TYPE = {"A320": 150, "A321": 155, "A20N": 148, "A21N": 150, "B739": 152}

# Thu tu 5 tau: moi tau 1 loai khac nhau.
FLEET = ["A320", "A321", "A20N", "A21N", "B739"]

# Gioi han toc do ATC duoi FL100 (quy dinh khai thac, khong phai so BADA).
ATC_SPEED_LIMIT_BELOW_FL100 = 250

# ---------------------------------------------------------------------------
# VVPQ SID RG 3D (RWY 10R that) -- vvpq_procedures.py's SID_TRANSITIONS["RG"].
# Toan bo chuoi di deu ve huong dong-dong nam roi vong len RG (154/101/101/53
# do), khong gap khuc.
#
# DA SUA: ban truoc dung SID OSOTA roi noi them TUNPO phia sau -> tau bay len
# BAC toi OSOTA (014 do) roi phai quay nguoc xuong DONG NAM toi TUNPO (147 do),
# gap khuc 133 do vo ly. Nguyen nhan: hieu sai y "doi diem OSOTA thanh TUNPO -
# RG - ..." thanh "giu SID OSOTA roi noi them", thay vi "thay han SID OSOTA
# bang SID RG 3D".
# ---------------------------------------------------------------------------
RW10R = (10.171189, 103.979464)
DEP_INITIAL_COURSE = 96  # that, cong bo 096(096.2)
SID_RG_3D = [
    ("PQ600", 10.152833, 104.164389, None),
    ("PQ620", 9.916111, 104.279167, 7000.0),
    ("SAMIX", 9.870000, 104.524167, None),
    ("VILIT", 9.796111, 104.914722, None),
    ("RG", 9.959444, 105.133056, None),
]

# ---------------------------------------------------------------------------
# Enroute bridge that (nguoi dung chi dinh, da xac minh tung diem) -- khong
# co do cao cong bo, dung 1 muc hanh trinh co dinh (ghi ro la lua chon khai
# thac, khong phai AIP).
#
# TUNPO DA BO: no khong nam trong SID RG 3D cong bo (phuong thuc that chi co
# PQ600-PQ620-SAMIX-VILIT-RG), va trong danh sach nguoi dung dua ra no dung
# TRUOC RG -- tuc thuoc phan "thay cho OSOTA", nay da duoc thay bang chinh
# SID RG 3D. Chen TUNPO vao giua cac diem cua 1 SID cong bo la sai phuong thuc.
# RG cung da la diem cuoi SID nen khong lap lai o day.
# ---------------------------------------------------------------------------
# Muc bay duong dai FL310, giu suot doan enroute; sau DADEN tau ha dan de dat
# DUNG FL250 tai LATOM (diem dau STAR LATOM 2K) -- yeu cau nguoi dung. Day la
# LUA CHON KHAI THAC, khong phai so lieu AIP (cac diem nay la diem bao cao
# enroute, khong co rang buoc do cao cong bo).
#
# Da kiem tra kha thi truoc khi dat:
#   PQ620(7000ft) -> TSH : 154 NM, leo 24000ft = 156 ft/NM   (thoai mai)
#   DADEN -> LATOM       :  53 NM, giam 6000ft = 114 ft/NM   (thoai mai)
#   LATOM -> NOVAN(+FL110): 24.5 NM, giam 14000ft = 2384 ft/min @250kt
#                           (trong kha nang A320; va "+FL110" la AT-OR-ABOVE
#                            nen khong vi pham neu tau con cao hon)
CRUISE_ALT_FT = 31000.0  # FL310
STAR_ENTRY_ALT_FT = 25000.0  # FL250 tai LATOM
CRUISE_SPD_KT = 290
ENROUTE_BRIDGE = [
    ("TSH", 10.818333, 106.650556),
    ("PATMA", 12.336389, 107.810000),
    ("SADAS", 13.320000, 107.829444),
    ("DADEN", 13.999444, 107.843611),
]

# ---------------------------------------------------------------------------
# VVDN STAR LATOM 2K (RWY 35L that) -- AD 2-VVDN-11-10, AMDT 01/23 (trang 76)
# + doan TAMLA->RW35L da co san that trong vvdn_procedures.py.
# ---------------------------------------------------------------------------
STAR_LATOM_2K = [
    ("LATOM", 14.879444, 107.843611, STAR_ENTRY_ALT_FT),  # FL250 -- yeu cau nguoi dung
    ("NOVAN", 15.262500, 107.987500, 11000.0),   # +FL110
    ("NOCKA", 15.419444, 108.046667, 10000.0),   # +FL100
    ("DN368", 15.585278, 108.022500, None),       # khong rang buoc (that)
    ("VIDAN", 15.750833, 107.998611, 7054.0),     # +2150m, AT-OR-ABOVE
    ("DOTEN", 15.767222, 108.118333, 6070.0),     # +1850m -- khop that
    ("TRACO", 15.601667, 108.142222, 5548.0),
    ("CADAS", 15.618056, 108.262500, 5181.0),     # <-- DIEM KIEM TRA SPACING
    ("MONRY", 15.700556, 108.250000, 4921.0),
    ("TAMLA", 15.788333, 108.237500, 4429.0),
    ("KALET", 15.865171, 108.224271, 2592.0),
    ("NB2",   15.947115, 108.212410, 1611.0),
    ("DN351", 15.957222, 108.210944, 1476.0),
    ("RW35L", 16.030133, 108.200372, 0.0),
]

# Toc do IAS THAT tai tung moc tu DOTEN tro di, RIENG cho tung loai tau bay --
# chep nguyen tu _gen_vvdn_minsep_pairs_from_doten.py's SPEED dict (chinh no
# da chep tu cac file _KB5GEN_ARR_APPROACH_ARRxxx.scn that cua tung loai).
# Doan nay dung toc do THAT thay vi BADA vi do la profile tiep can thuc te da
# duoc do/kiem chung trong du an, sat hon mot bang BADA chung chung.
DN_SPEED_FROM_DOTEN = {
    "A320": {"DOTEN": 250, "TRACO": 230, "CADAS": 205, "MONRY": 190, "TAMLA": 175, "KALET": 165, "NB2": 150, "DN351": 150, "RW35L": 130},
    "A321": {"DOTEN": 250, "TRACO": 230, "CADAS": 205, "MONRY": 190, "TAMLA": 175, "KALET": 165, "NB2": 155, "DN351": 155, "RW35L": 135},
    "A20N": {"DOTEN": 250, "TRACO": 230, "CADAS": 205, "MONRY": 190, "TAMLA": 175, "KALET": 165, "NB2": 150, "DN351": 150, "RW35L": 130},
    "A21N": {"DOTEN": 250, "TRACO": 230, "CADAS": 215, "MONRY": 200, "TAMLA": 185, "KALET": 170, "NB2": 155, "DN351": 155, "RW35L": 140},
    "B739": {"DOTEN": 250, "TRACO": 230, "CADAS": 215, "MONRY": 200, "TAMLA": 185, "KALET": 170, "NB2": 155, "DN351": 155, "RW35L": 145},
}


# ---------------------------------------------------------------------------
# Lich toc do BADA theo giai doan + muc bay
# ---------------------------------------------------------------------------
def _isa(alt_ft):
    h = alt_ft * 0.3048
    if h < 11000.0:
        T = 288.15 - 0.0065 * h
        p = 101325.0 * (T / 288.15) ** 5.25588
    else:
        T = 216.65
        p = 22632.0 * math.exp(-9.80665 * (h - 11000.0) / (287.05 * 216.65))
    return T, p


def mach_to_cas_kt(mach, alt_ft):
    """Doi so Mach cong bo cua BADA sang CAS (IAS) de ghi vao ADDWPT -- cong
    thuc khi quyen tieu chuan ISA + dong ap nen duoc (compressible), cung ho
    cong thuc bluesky/tools/aero.py dung."""
    _T, p = _isa(alt_ft)
    qc = p * ((1.0 + 0.2 * mach * mach) ** 3.5 - 1.0)
    cas_ms = 340.294 * math.sqrt(5.0 * ((qc / 101325.0 + 1.0) ** (1.0 / 3.5) - 1.0))
    return cas_ms / 0.514444


def bada_speed_kt(actype, alt_ft, phase, v2=None):
    """Toc do CAS theo dung lich BADA 3.x cua RIENG loai tau bay do, theo
    giai doan bay va muc bay:

      - Duoi 3000ft (chi khi leo): V2 + 20, giai doan tang toc sau cat canh.
      - Duoi FL100: CAS cua giai doan nhung bi gioi han boi quy dinh ATC
        250kt (gioi han khai thac, KHONG phai so BADA).
      - Tren FL100: lay MIN giua CAS cong bo va CAS tuong duong cua so Mach
        cong bo -- chinh la cach BADA chuyen tu che do giu CAS sang giu Mach
        tai "crossover altitude" (duoi crossover CAS nho hon, tren crossover
        Mach nho hon), khong can tinh rieng crossover.
    """
    cascl1, cascl2, mcl, cascr2, mcr, mdes, casdes2, casdes1 = BADA[actype]
    if phase == "climb":
        if alt_ft < 3000 and v2 is not None:
            return round(v2 + 20)
        cas_lo, cas_hi, mach = cascl1, cascl2, mcl
    elif phase == "cruise":
        cas_lo, cas_hi, mach = cascr2, cascr2, mcr
    else:  # descent
        cas_lo, cas_hi, mach = casdes1, casdes2, mdes

    if alt_ft < 10000:
        return min(cas_lo, ATC_SPEED_LIMIT_BELOW_FL100)
    return round(min(cas_hi, mach_to_cas_kt(mach, alt_ft)))


def haversine_nm(lat1, lon1, lat2, lon2):
    R = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def fmt_time(total_sec):
    if total_sec < 0:
        total_sec = 0
    h = int(total_sec // 3600)
    m = int((total_sec % 3600) // 60)
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def build_flight_lines(callsign, actype, t0_sec, exit_choice):
    t0 = fmt_time(t0_sec)
    lat0, lon0 = RW10R
    v2 = V2_BY_TYPE[actype]
    lines = [f"# --- {callsign} ({actype}) - SID RG 3D (VVPQ RWY10R) -> FL310 -> LATOM FL250 -> STAR LATOM 2K (VVDN RWY35L) ---"]
    lines.append(f"{t0}>CRE {callsign},{actype},{lat0:.6f},{lon0:.6f},{DEP_INITIAL_COURSE},0,{v2}")
    lines.append(f"{t0}>{callsign} ALT 50")

    for name, lat, lon, alt, spd, note in route_points(actype):
        if alt is None:
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f}  # {name} ({note})")
        else:
            label = "nguong 35L (cham cang chinh)" if name == "RW35L" else name
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{alt:.0f},{spd}  # {label} ({note})")

    exit_info = EXIT_CHAINS[exit_choice]
    for lat, lon, spd in exit_info["chain"]:
        lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},0,{spd}  # thoat ly {exit_choice} (that)")

    lines.append(f"{t0}>{callsign} LNAV ON")
    lines.append(f"{t0}>{callsign} VNAV ON")

    # Chuyen tu LNAV/VNAV sang chuoi MOVE lan vao ben do that. Moc thoi gian
    # = cham nguong (DO THAT bang headless) + thoi gian xa da/lan thoat ly.
    td_spd = DN_SPEED_FROM_DOTEN[actype]["RW35L"]
    t_stop = t0_sec + TOUCHDOWN_CALIB[actype] + occupancy_time_sec(exit_choice, td_spd)
    lines.append(f"{fmt_time(t_stop)}>{callsign} LNAV OFF")
    lines.append(f"{fmt_time(t_stop)}>{callsign} VNAV OFF  # thoat ly {exit_choice}, lan vao {exit_info['dest_label']}")
    for offset, cmd in load_move_sequence(exit_info["move_file"]):
        lines.append(f"{fmt_time(t_stop + offset)}>{cmd.replace('%0', callsign)}")
    lines.append("")
    return lines


def route_points(actype):
    """Chuoi (ten, lat, lon, alt_ft, spd_kt, ghi_chu) day du cua 1 chuyen bay,
    toc do da ap dung dung lich BADA cua RIENG loai tau bay do."""
    v2 = V2_BY_TYPE[actype]
    pts = []

    for name, lat, lon, alt in SID_RG_3D:
        if alt is None:
            pts.append((name, lat, lon, None, None, "SID RG 3D, that, khong rang buoc do cao"))
        else:
            spd = bada_speed_kt(actype, alt, "climb", v2)
            pts.append((name, lat, lon, alt, spd, f"SID RG 3D, that; toc do BADA climb {actype}"))

    for name, lat, lon in ENROUTE_BRIDGE:
        spd = bada_speed_kt(actype, CRUISE_ALT_FT, "cruise")
        pts.append((name, lat, lon, CRUISE_ALT_FT, spd, f"enroute FL310; toc do BADA cruise {actype}"))

    for name, lat, lon, alt in STAR_LATOM_2K:
        if alt is None:
            pts.append((name, lat, lon, None, None, "STAR LATOM 2K, that, khong rang buoc do cao"))
            continue
        real = DN_SPEED_FROM_DOTEN[actype].get(name)
        if real is not None:
            pts.append((name, lat, lon, alt, real, f"STAR LATOM 2K; toc do tiep can THAT cua {actype}"))
        else:
            spd = bada_speed_kt(actype, alt, "descent")
            pts.append((name, lat, lon, alt, spd, f"STAR LATOM 2K; toc do BADA descent {actype}"))
    return pts


def estimate_times(actype):
    """Uoc luong thoi gian bay tu luc CRE den (CADAS, nguong) bang toc do
    trung binh tung chang. Chi dung de SAP XEP gio cat canh ban dau -- con so
    chinh xac lay tu lan do THAT bang BlueSky headless (CADAS_CALIB)."""
    pts = [("RW10R", RW10R[0], RW10R[1], 0.0, bada_speed_kt(actype, 0, "climb", V2_BY_TYPE[actype]), "")] + route_points(actype)
    last_spd = pts[0][4]
    t = 0.0
    t_cadas = None
    for i in range(len(pts) - 1):
        _, la1, lo1, _a1, s1, _ = pts[i]
        n2, la2, lo2, _a2, s2, _ = pts[i + 1]
        s1 = s1 if s1 is not None else last_spd
        s2 = s2 if s2 is not None else s1
        last_spd = s2
        d = haversine_nm(la1, lo1, la2, lo2)
        t += d / max((s1 + s2) / 2.0, 1.0) * 3600.0
        if n2 == "CADAS":
            t_cadas = t
    return t_cadas, t


# Thoi gian bay THAT tu luc CRE den khi qua CADAS / den khi cham nguong, DO
# BANG BlueSky headless (khong phai uoc luong) cho tung loai tau bay voi dung
# profile trong file nay. Dung de:
#   1. Giai nguoc gio cat canh sao cho gian cach TAI CADAS dung 180s -- vi 5
#      loai co toc do khac nhau nen cat canh cach deu 180s se KHONG cho gian
#      cach 180s tai CADAS.
#   2. Dat dung moc thoi gian bat dau chuoi MOVE lan vao ben do.
# Cap nhat bang quy trinh hieu chinh (chay headless do lai roi dien vao day).
CADAS_CALIB = {   # so giay tu CRE den khi qua CADAS
    "A320": 4996.0,   # do duoc khi cach CADAS 0.90 NM
    "A321": 4978.0,   # 0.90 NM
    "A20N": 4972.0,   # 0.90 NM
    "A21N": 4926.0,   # 0.89 NM
    "B739": 4936.0,   # 0.89 NM
}
TOUCHDOWN_CALIB = {   # so giay tu CRE den khi cham nguong 35L
    "A320": 5484.0,   # do duoc khi cach nguong 0.01 NM
    "A321": 5462.0,   # 0.00 NM
    "A20N": 5460.0,   # 0.01 NM
    "A21N": 5392.0,   # 0.04 NM
    "B739": 5402.0,   # 0.04 NM
}

# ---------------------------------------------------------------------------
# THOAT LY SAU KHI HA CANH -- chep nguyen tu _gen_vvdn_minsep_pairs_from_
# doten.py's EXIT_CHAINS (chinh no chep tu _KB5GEN_ARR_EXIT_G4/G6.scn that).
# Moi tau NGAU NHIEN (seed co dinh de tai lap duoc) thoat ly qua G4 hoac G6:
#   G4 -> lan vao BEN 26      (du lieu MOVE: _ARR_RESUME_G4_GATE26.scn)
#   G6 -> lan vao BEN 11      (du lieu MOVE: _ARR_RESUME_G6_GATE11.scn)
# Toc do giam dan den muc lan (10kt) chu KHONG ve 0: de chuoi LNAV rollout noi
# lien mach sang chuoi MOVE lan vao ben, khong bi dung khuc giua duong bang
# (loi nay da tung gap va duoc ghi lai trong _gen_vvdn_minsep_pairs_from_doten).
# ---------------------------------------------------------------------------
EXIT_CHAINS = {
    "G4": {
        "chain": [
            (16.034580, 108.199721, 122), (16.039028, 108.199071, 102), (16.043475, 108.198420, 75),
            (16.046143, 108.198030, 54), (16.047922, 108.197769, 32), (16.048687, 108.197658, 10),
            (16.048950, 108.198100, 8), (16.048727, 108.197660, 10),
        ],
        "move_file": "_ARR_RESUME_G4_GATE26.scn",
        "dest_label": "ben 26",
    },
    "G6": {
        "chain": [
            (16.034580, 108.199721, 128), (16.039028, 108.199071, 115), (16.043475, 108.198420, 100),
            (16.047922, 108.197769, 83), (16.052370, 108.197119, 61), (16.055927, 108.196598, 34),
            (16.057199, 108.196412, 10), (16.057250, 108.196800, 8), (16.057200, 108.197400, 12),
        ],
        "move_file": "_ARR_RESUME_G6_GATE11.scn",
        "dest_label": "ben 11",
    },
}
RANDOM_SEED = 20261014


def load_move_sequence(filename):
    """Doc file MOVE/DEL nguon, tra ve [(offset_giay, lenh_co_%0)] de NHOI
    THANG vao file dau ra -- khong dung PCALL toi file rieng, de kich ban chi
    con DUY NHAT 1 file .scn."""
    out = []
    for line in (Path(__file__).parent / filename).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ">" not in line:
            continue
        ts, rest = line.split(">", 1)
        h, m, s = ts.split(":")
        out.append((int(h) * 3600 + int(m) * 60 + float(s), rest))
    return out


def occupancy_time_sec(exit_name, touchdown_spd_kt):
    """Thoi gian tu luc cham nguong den khi toi diem cuoi chuoi thoat ly."""
    pts = [(STAR_LATOM_2K[-1][1], STAR_LATOM_2K[-1][2], touchdown_spd_kt)] + EXIT_CHAINS[exit_name]["chain"]
    t = 0.0
    for i in range(len(pts) - 1):
        la1, lo1, s1 = pts[i]
        la2, lo2, s2 = pts[i + 1]
        t += haversine_nm(la1, lo1, la2, lo2) / max((s1 + s2) / 2.0, 0.5) * 3600.0
    return t


def backup_if_exists():
    if OUT_FILE.exists():
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest_dir = BACKUP_DIR / f"VVPQ-VVDN {ts}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / OUT_FILE.name
        shutil.copy(OUT_FILE, dest)
        print(f"Da backup file cu vao {dest}")


def assign_exits():
    """Ngau nhien G4/G6 cho tung tau, seed co dinh de moi lan sinh lai ra ket
    qua y het (tai lap duoc)."""
    rng = random.Random(RANDOM_SEED)
    return [rng.choice(["G4", "G6"]) for _ in FLEET]


def solve_t0():
    """Giai nguoc gio cat canh: 5 loai tau bay co toc do khac nhau nen thoi
    gian bay toi CADAS khac nhau; muon gian cach TAI CADAS dung 180s thi gio
    cat canh KHONG the cach deu 180s.

        t0[i] = (moc CADAS mong muon cua tau i) - (thoi gian bay toi CADAS cua
                 loai tau i)

    Moc CADAS dau tien chon du lon de khong tau nao co t0 am."""
    if CADAS_CALIB:
        to_cadas = [CADAS_CALIB[ac] for ac in FLEET]
        src = "DO THAT bang BlueSky headless"
    else:
        to_cadas = [estimate_times(ac)[0] for ac in FLEET]
        src = "UOC LUONG (chua hieu chinh -- chay che do --calib de do that)"
    first = max(to_cadas) + SCENARIO_START_SEC
    t0s = [first + i * CADAS_GAP_SEC - to_cadas[i] for i in range(len(FLEET))]
    return t0s, [first + i * CADAS_GAP_SEC for i in range(len(FLEET))], src


def main():
    calib_mode = "--calib" in sys.argv
    backup_if_exists()

    exits = assign_exits()
    t0s, cadas_targets, src = solve_t0()

    lines = [
        "# VVPQ -> VVDN: 5 tau bay (5 LOAI KHAC NHAU) cat canh SID RG 3D (VVPQ",
        "# RWY10R that), leo FL310, ha dan dat FL250 tai LATOM, ha canh VVDN",
        "# STAR LATOM 2K (RWY35L that), cach nhau DUNG 3 phut tai CADAS.",
        "# Toc do moi giai doan theo lich BADA 3.16 that cua TUNG loai tau bay.",
        "# Sau khi ha canh: ngau nhien thoat ly G4 -> ben 26 hoac G6 -> ben 11.",
        f"# Gio cat canh giai nguoc tu moc CADAS ({src}).",
        "00:00:00.000>DTMULT 1",
        "",
    ]

    for i, actype in enumerate(FLEET):
        cs = f"VVPQ{i + 1:02d}"
        if calib_mode:
            # Che do hieu chinh: cat canh cach deu, KHONG vacate -- chi de do
            # thoi gian bay thuan tuy cua tung loai.
            t0 = SCENARIO_START_SEC + i * CADAS_GAP_SEC
            lines.append(f"# {cs} ({actype}): cat canh {fmt_time(t0)} [CHE DO HIEU CHINH]")
            lines += build_flight_lines_nocalib(cs, actype, t0)
        else:
            t0 = t0s[i]
            lines.append(
                f"# {cs} ({actype}): cat canh {fmt_time(t0)}, qua CADAS {fmt_time(cadas_targets[i])}, "
                f"thoat ly {exits[i]} -> {EXIT_CHAINS[exits[i]]['dest_label']}"
            )
            lines += build_flight_lines(cs, actype, t0, exits[i])

    OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Da ghi {OUT_FILE}" + ("  [CHE DO HIEU CHINH]" if calib_mode else ""))
    print(f"Nguon thoi gian: {src}")
    for i, ac in enumerate(FLEET):
        print(f"  VVPQ{i+1:02d} {ac}: cat canh {fmt_time(t0s[i] if not calib_mode else SCENARIO_START_SEC + i*CADAS_GAP_SEC)}"
              + (f", CADAS {fmt_time(cadas_targets[i])}, thoat ly {exits[i]} -> {EXIT_CHAINS[exits[i]]['dest_label']}" if not calib_mode else ""))
    if not calib_mode:
        for i in range(1, len(cadas_targets)):
            gap = cadas_targets[i] - cadas_targets[i - 1]
            print(f"  gian cach CADAS {i}->{i+1}: {gap:.1f}s")


def build_flight_lines_nocalib(callsign, actype, t0_sec):
    """Ban rut gon chi dung cho che do hieu chinh: khong co doan thoat ly/
    vacate (nhung doan do can TOUCHDOWN_CALIB -- thu chua co o vong do dau)."""
    t0 = fmt_time(t0_sec)
    lat0, lon0 = RW10R
    v2 = V2_BY_TYPE[actype]
    lines = [f"# --- {callsign} ({actype}) [hieu chinh] ---"]
    lines.append(f"{t0}>CRE {callsign},{actype},{lat0:.6f},{lon0:.6f},{DEP_INITIAL_COURSE},0,{v2}")
    lines.append(f"{t0}>{callsign} ALT 50")
    for name, lat, lon, alt, spd, note in route_points(actype):
        if alt is None:
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f}  # {name}")
        else:
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{alt:.0f},{spd}  # {name}")
    lines.append(f"{t0}>{callsign} LNAV ON")
    lines.append(f"{t0}>{callsign} VNAV ON")
    lines.append("")
    return lines


if __name__ == "__main__":
    main()
