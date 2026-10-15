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
import shutil
from datetime import datetime
from pathlib import Path

OUT_FILE = Path("VVPQ-VVDN-5acft-3min-CADAS.scn")
BACKUP_DIR = Path("Backup")

SCENARIO_START_SEC = 30.0  # 00:00:30 -- tau dau xuat hien gan nhu ngay khi mo
DEPARTURE_GAP_SEC = 180.0  # 3 phut
N_AIRCRAFT = 5
ACTYPE = "A320"
V2_KT = 150

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

# Toc do THAT (A320), DOTEN tro di -- tu _gen_vvdn_minsep_pairs_from_doten.py
DN_SPEED_FROM_DOTEN = {
    "DOTEN": 250, "TRACO": 230, "CADAS": 205, "MONRY": 190, "TAMLA": 175,
    "KALET": 165, "NB2": 150, "DN351": 150, "RW35L": 130,
}


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


def climb_speed_kt(alt_ft):
    if alt_ft < 3000:
        return round(V2_KT + 20)
    if alt_ft < 10000:
        return 250
    return 280


def bada_descent_speed_kt(alt_ft):
    """Cung cong thuc voi capacity_scenario_engine._bada_descent_speed_kt,
    dung cho cac diem that nhung khong co toc do cong bo (NOVAN/NOCKA/
    DN368/VIDAN)."""
    if alt_ft >= 14000:
        return 250
    if alt_ft >= 6000:
        return 230
    return 210


def backup_if_exists():
    if OUT_FILE.exists():
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest_dir = BACKUP_DIR / f"VVPQ-VVDN {ts}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / OUT_FILE.name
        shutil.copy(OUT_FILE, dest)
        print(f"Da backup file cu vao {dest}")


def build_flight_lines(callsign, t0_sec):
    t0 = fmt_time(t0_sec)
    lat0, lon0 = RW10R
    lines = [f"# --- {callsign} ({ACTYPE}) - SID RG 3D (VVPQ RWY10R) -> enroute that -> STAR LATOM 2K (VVDN RWY35L) ---"]
    lines.append(f"{t0}>CRE {callsign},{ACTYPE},{lat0:.6f},{lon0:.6f},{DEP_INITIAL_COURSE},0,{V2_KT}")
    lines.append(f"{t0}>{callsign} ALT 50")

    for name, lat, lon, alt in SID_RG_3D:
        if alt is not None:
            spd = climb_speed_kt(alt)
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{alt:.0f},{spd}  # {name} (SID RG 3D, that)")
        else:
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f}  # {name} (SID RG 3D, that, khong rang buoc do cao)")

    for name, lat, lon in ENROUTE_BRIDGE:
        lines.append(
            f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{CRUISE_ALT_FT:.0f},{CRUISE_SPD_KT}"
            f"  # {name} (enroute that, do cao hanh trinh don gian hoa -- xem docstring)"
        )

    for name, lat, lon, alt in STAR_LATOM_2K:
        if alt is None:
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f}  # {name} (STAR LATOM 2K, that, khong rang buoc do cao)")
            continue
        if name in DN_SPEED_FROM_DOTEN:
            spd = DN_SPEED_FROM_DOTEN[name]
            src = "that"
        else:
            spd = bada_descent_speed_kt(alt)
            src = "BADA descent schedule, khong co toc do cong bo"
        label = "nguong 35L (cham cang chinh)" if name == "RW35L" else name
        lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{alt:.0f},{spd}  # {label} (STAR LATOM 2K, {src})")

    lines.append(f"{t0}>{callsign} LNAV ON")
    lines.append(f"{t0}>{callsign} VNAV ON")

    # Thoi gian bay THAT tu CRE den nguong (de tinh moc DEL an toan).
    all_pts = (
        [("RW10R", *RW10R)]
        + [(n, lat, lon) for n, lat, lon, _ in SID_RG_3D]
        + [(n, lat, lon) for n, lat, lon in ENROUTE_BRIDGE]
        + [(n, lat, lon) for n, lat, lon, _ in STAR_LATOM_2K]
    )
    speeds = (
        [climb_speed_kt(0)]
        + [climb_speed_kt(alt) if alt is not None else climb_speed_kt(7000) for _, _, _, alt in SID_RG_3D]
        + [CRUISE_SPD_KT] * len(ENROUTE_BRIDGE)
        + [
            (DN_SPEED_FROM_DOTEN.get(n) if n in DN_SPEED_FROM_DOTEN else (bada_descent_speed_kt(alt) if alt is not None else 230))
            for n, _, _, alt in STAR_LATOM_2K
        ]
    )
    total_t = 0.0
    cadas_t = None
    for i in range(len(all_pts) - 1):
        _, lat1, lon1 = all_pts[i]
        name2, lat2, lon2 = all_pts[i + 1]
        d = haversine_nm(lat1, lon1, lat2, lon2)
        avg = (speeds[i] + speeds[i + 1]) / 2.0
        total_t += d / avg * 3600.0
        if name2 == "CADAS":
            cadas_t = t0_sec + total_t

    del_time = t0_sec + total_t + 120.0
    lines.append(f"{fmt_time(del_time)}>DEL {callsign}")
    lines.append("")
    return lines, cadas_t


def main():
    backup_if_exists()

    lines = []
    lines.append("# VVPQ -> VVDN: 5 tau bay A320 cat canh SID RG 3D (VVPQ RWY10R that),")
    lines.append("# bay qua enroute bridge that (TUNPO-RG-TSH-PATMA-SADAS-DADEN), ha canh")
    lines.append("# VVDN STAR LATOM 2K (RWY35L that), cach nhau DUNG 3 phut tai CADAS.")
    # DTMULT phai o moc 00:00:00, KHONG phai moc cat canh dau tien: neu dat o
    # 00:00:30 thi moi lenh tang toc nguoi dung go truoc do deu bi dong nay ghi
    # de nguoc lai ve 1x (da gap khi chay thu live).
    lines.append("00:00:00.000>DTMULT 1")
    lines.append("")

    cadas_times = []
    for i in range(N_AIRCRAFT):
        callsign = f"VVPQ{i + 1:02d}"
        t0 = SCENARIO_START_SEC + i * DEPARTURE_GAP_SEC
        flight_lines, cadas_t = build_flight_lines(callsign, t0)
        lines.append(f"# {callsign}: cat canh luc {fmt_time(t0)}, qua CADAS (du kien) luc {fmt_time(cadas_t)}")
        lines += flight_lines
        cadas_times.append(cadas_t)

    OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Da ghi {OUT_FILE}")
    for i in range(1, len(cadas_times)):
        gap = cadas_times[i] - cadas_times[i - 1]
        print(f"Khoang cach CADAS (du kien) giua tau {i} va {i + 1}: {gap:.1f}s ({gap / 60:.2f} phut)")


if __name__ == "__main__":
    main()
