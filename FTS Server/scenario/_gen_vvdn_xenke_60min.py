"""
VVDN-XENKE-60MIN.scn -- Kich ban cat canh/ha canh XEN KE tai VVDN, 60 phut.

Sinh theo prompt "kich ban cat canh xen ke (Linh).docx": khai thac huong 35,
hai duong CHC song song PHU THUOC (35L ha canh ILS, 35R cat canh). MOT pha
duy nhat suot 60 phut, xep sat phan cach toi thieu cua du thao Phuong thuc
2 CHC song song Da Nang (24.7.2026), du thao MANOP APP/TWR Da Nang va ICAO
Doc 4444 -- so chuyen thu duoc chinh la NANG LUC DIEU HANH BAY toi da.

NGUON DU LIEU (khong bia -- moi toa do/toc do deu tu du lieu that):
  - STAR/SID RNAV RWY35L/R, toc do tiep can theo tung loai tau bay, tuyen lan
    ra tu ben 26/27, diem cho PREHOLD/RWYHOLD: trich bang AST tu
    _gen_kb5_1hour.py (generator cua kich ban 40 chuyen da kiem chung).
  - Tuyen lan vao ben 28 / ben 8: _ARR_RESUME_G4_GATE28.scn /
    _ARR_RESUME_G6_GATE8.scn, deu bam tim duong lan that cua VVDN.
  - Quy tac phan cach + tham so lan: vvdn_xenke_rules.json (ghi ro dieu khoan
    nguon; 2 muc danh dau CAN XAC NHAN theo xac nhan cua nguoi dung).

CAC DON GIAN HOA CO CHU DICH (ghi ro, khong giau):
  - Khong mo phong bay lai / huy cat canh (gia dinh co dinh cua prompt).
  - Tau bay DI bien mat sau 5 phut ke tu cat canh (prompt muc 5).
  - Tau bay DEN bien mat khi toi ben (lenh DEL cuoi chuoi lan vao ben).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import ast
import json
import math
import random
import shutil
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
OUT_FILE = HERE / "VVDN-XENKE-60MIN.scn"
BACKUP_DIR = HERE / "Backup"
RULES_FILE = HERE / "vvdn_xenke_rules.json"
SRC_GEN = HERE / "_gen_kb5_1hour.py"
CALIB_FILE = HERE / "VVDN-XENKE-60MIN.calib.json"

# Hieu chuan thoi diem tao tau den. Uoc luong thoi gian bay nguoc tu moc cham
# banh (estimate_transit_s) chi dung trong khoang vai chuc giay -- da do duoc
# sai lech trung binh 52s, lon nhat 85s. Sai lech do lam chuoi lenh MOVE lan
# vao ben khoi dong KHI TAU CHUA TOI diem cho, va lenh MOVE dau tien keo tau
# di hang nghin met (da do: 11.669 m trong 1 giay). _calib_vvdn_xenke.py chay
# mo phong that, do moc cham banh thuc te roi ghi do lech vao file nay; o day
# chi doc len va bu truoc vao thoi diem CRE.
CALIB = json.loads(CALIB_FILE.read_text(encoding="utf-8")) if CALIB_FILE.exists() else {}

SEED = 20261102
DURATION_S = 3600.0
FIRST_ARR_TD = 530.0   # Moc cham banh cua chuyen den dau tien (se tu doi len
                       # neu chuyen di dau tien khong kip lan ra truoc T=0).
                       # KHONG duoc dat thap hon ~506s: chuyen den dau tien som
                       # nhat cung phai sinh tai CADAS (25NM) o T=0, va bay tu
                       # CADAS vao nguong 35L mat 455-506s tuy loai tau. Dat
                       # 300s thi hieu chuan khong bao gio hoi tu duoc (da do:
                       # ARR001 ket o +66.5s qua ca 6 vong).


# ---------------------------------------------------------------------------
# Trich du lieu tu generator cua kich ban 40 chuyen (AST -- chi lay dinh nghia,
# KHONG chay phan sinh file cua no)
# ---------------------------------------------------------------------------
def load_source_data():
    tree = ast.parse(SRC_GEN.read_text(encoding="utf-8"))
    keep = [n for n in tree.body
            if isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign,
                              ast.FunctionDef, ast.ClassDef))
            or (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
    ns: dict = {"__name__": "_kb5_data", "__file__": str(SRC_GEN)}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(SRC_GEN), "exec"), ns)
    return ns


D = load_source_data()
RULES = json.loads(RULES_FILE.read_text(encoding="utf-8"))

STAR_IAF = D["STAR_IAF"]
STAR_CHAINS = D["STAR_CHAINS"]
SID_CHAINS = D["SID_CHAINS"]
SID_NAMES = D["SID_NAMES"]
MEDIUM_TYPES = D["MEDIUM_TYPES"]
HEAVY_TYPES = D["HEAVY_TYPES"]
APPROACH_SPEEDS = D["APPROACH_SPEEDS"]
TAXI_COMMON_G26 = D["TAXI_COMMON_G26"]
TAXI_COMMON_G27 = D["TAXI_COMMON_G27"]
GATE26, GATE27 = D["GATE26"], D["GATE27"]
RWYHOLD, PREHOLD = D["RWYHOLD"], D["PREHOLD"]
haversine_m = D["haversine_m"]
estimate_transit_s = D["estimate_transit_s"]
aircraft_length_m = D["aircraft_length_m"]
approach_speeds = D["approach_speeds"]   # (toc do@25NM, @10NM, @5NM, cham banh)
interp_speed = D["interp_speed"]
bearing_deg = D["bearing_deg"]
tas_correction = D["tas_correction"]
post_cadas_legs = D["post_cadas_legs"]
truncated_star_spawn = D["truncated_star_spawn"]
_full_pre_cadas_chain = D["_full_pre_cadas_chain"]
_CADAS_PLACEHOLDER = D["_CADAS_PLACEHOLDER"]
_STAR_TRANSIT = D["_STAR_TRANSIT"]
GATE26 = D["GATE26"]
GATE27 = D["GATE27"]
RWYHOLD = D["RWYHOLD"]
PREHOLD = D["PREHOLD"]

MOVE_DT = 2.0        # nhip phat lenh MOVE khi lan (giay)
HOLD_DT = 10.0       # nhip ghim tau dung yen tai diem cho (giay)
DEP_KEEP_S = 420.0   # giu tau di trong mo phong sau khi chay da (giay)
HOLD_MARGIN_S = 4.0  # dem an toan truoc khi chuoi MOVE lan vao ben tiep quan.
                     # Lon hon sai lech cham banh sau hieu chuan (<= 3.9 s) nhung
                     # khong lon hon: tau dung o cuoi chuoi thoat ly van con trong
                     # 35L, ma MANOP chi cho 100 s tu nguong den luc thoat ly (10 s
                     # lam 3 chuyen thoat ly G6 mat 102-104 s).

# Tranh nhau khi lan -- lay DUNG tham so cua plugin bluesky/plugins/surfacetaxi.py
# (settings.taxi_tail_buffer = 20.0 m). Plugin do khong tu can thiep duoc vao
# kich ban nay vi no CO Y khong dung toi selspd cua tau bay dang bi dieu khien
# bang MOVE (swlnav = False -- xem surfacetaxi.py dong 201-212), ma ca tau den
# lan vao ben lan tau di lan ra deu dung MOVE. Vi vay ap dung CUNG quy tac do
# ngay trong khau lap lich, noi ta biet truoc vi tri moi tau tai moi thoi diem.
TAXI_TAIL_BUFFER_M = 20.0
# Cu ly chay da (take-off run) tren 35R, tinh tu nguong. Gia tri dai dien
# theo nhom nhieu dong xoay o dieu kien kich ban (CHC kho, khong gio, muc
# nuoc bien): MEDIUM ~2000 m, HEAVY ~2600 m. Duong CHC 35R dai 3517 m nen
# ca hai deu roi dat TRONG pham vi duong CHC.
TOR_MEDIUM_M = 2000.0
TOR_HEAVY_M = 2600.0
LIFTOFF_ALT_FT = 35.0   # screen height tieu chuan ICAO
NHUONG_BUOC_S = 15.0   # buoc lui/day moi vong khi giai xung dot lan
# Tim duong CHC 17L/35R LAY TU DU LIEU SAN BAY THAT (runway_centerlines.geojson):
# nguong 35R (dau nam) -> nguong 17L (dau bac), dai 3517 m, huong 352.1 do.
THR35R = (16.029038, 108.202528)
END17L = (16.060366, 108.198004)

def _diem_tren_tim_35R(m_tu_nguong):
    """Toa do tren TIM duong CHC 35R, cach nguong 35R m_tu_nguong met."""
    f = m_tu_nguong / haversine_m(*THR35R, *END17L)
    return (THR35R[0] + (END17L[0] - THR35R[0]) * f,
            THR35R[1] + (END17L[1] - THR35R[1]) * f)

# Vi tri bat dau chay da. Gia tri cu (16.030000,108.202000) lay tu
# _KB5GEN_DEP_ENTER_RWY.scn cua kich ban 40 chuyen LECH TIM 35R toi 41.2 m
# (do bang runway_centerlines.geojson) -- tau bay "chay da ben canh duong
# CHC". Nay tinh truc tiep tu tim that. Chon 150 m tu nguong: du de tau quay
# mui on dinh sau khi vao tu RWYHOLD (RWYHOLD nam ngay nguong, cach 18 m doc
# tim, lech 0.5 m), van con 3367 m duong CHC -- thua cho moi loai tau bay.
LINEUP_35R = _diem_tren_tim_35R(150.0)

THR35L = (16.030133, 108.200372)


def _xy(la, lo):
    """Toa do phang (m) quanh nguong 35R."""
    return ((lo - THR35R[1]) * math.cos(math.radians(THR35R[0])) * 111320.0,
            (la - THR35R[0]) * 110574.0)


_ex, _ey = _xy(*END17L)
_UX, _UY = _ex / math.hypot(_ex, _ey), _ey / math.hypot(_ex, _ey)


def truc_35R(la, lo):
    """(doc tim tu nguong 35R, lech ngang so voi tim 35R; + = phia dong), met."""
    x, y = _xy(la, lo)
    return x * _UX + y * _UY, x * _UY - y * _UX


def _d_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    f = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - a[0] - f * dx, p[1] - a[1] - f * dy)


LAYOUT_DIR = (HERE / "../data/aerodrome_layout/datasets/vietnam_kml_layout/"
              "normalized/airports/VVDN").resolve()


def _doan_duong_lan(name):
    tc = json.loads((LAYOUT_DIR / "taxiway_centerlines.geojson").read_text(encoding="utf-8"))
    segs = []
    for f in tc["features"]:
        if f["properties"].get("name") != name:
            continue
        g = f["geometry"]
        for ln in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]):
            P = [_xy(c[1], c[0]) for c in ln]
            segs += list(zip(P, P[1:]))
    return segs


TWY_E_SEGS = _doan_duong_lan("E")


G4 = (16.048864, 108.198650)
G6 = (16.057240, 108.197425)

# Tuyen lan vao ben (G4 -> ben 28, G6 -> ben 8) theo yeu cau prompt
ARR_TAXI_FILES = {"G4": "_ARR_RESUME_G4_GATE28.scn", "G6": "_ARR_RESUME_G6_GATE8.scn"}
ARR_GATE_NAME = {"G4": "ben 28", "G6": "ben 8"}

# Chuoi thoat ly tu nguong 35L ra diem cho G4/G6 (trich tu kich ban 40 chuyen,
# da bo diem thua gay lui nguoc -- xem _gen_vvpq_vvdn_5acft_3min_cadas.py)
EXIT_CHAINS = {
    "G4": [(16.034580, 108.199721, 122), (16.039028, 108.199071, 102), (16.043475, 108.198420, 75),
           (16.046143, 108.198030, 54), (16.047922, 108.197769, 32), (16.048687, 108.197658, 10),
           (16.048727, 108.197660, 10)],
    "G6": [(16.034580, 108.199721, 128), (16.039028, 108.199071, 115), (16.043475, 108.198420, 100),
           (16.047922, 108.197769, 83), (16.052370, 108.197119, 61), (16.055927, 108.196598, 34),
           (16.057199, 108.196412, 10), (16.057250, 108.196800, 8)],
}
# Diem cuoi cu cua chuoi G6 (16.057200,108.197400) cach tim 35R chi 112 m: tau
# dai hon 42 m dung o do da LAN MUI qua vach dung cho 35R (91 m). Vi vay chuoi
# LNAV G6 nay dung o diem truoc khi re ve phia 35R (cach tim 35R 175 m), diem
# cuoi cu tro thanh diem dau cua tuyen MOVE -- de tau DUNG CHO DUNG truoc vach
# 35R roi moi cat qua (MANOP Phu luc 2 CHC song song).
EXIT_TAIL = {"G4": [], "G6": [(16.057250, 108.196800), (16.057200, 108.197400)]}

# ---------------------------------------------------------------------------
# Quy tac phan cach (tu file cau hinh)
# ---------------------------------------------------------------------------
R_ARR = RULES["phan_cach_ha_canh_lien_tiep_35L"]["ma_tran"]
R_DEP = RULES["phan_cach_cat_canh_lien_tiep_35R"]["ma_tran"]
R_DEP_SID = RULES["phan_cach_cat_canh_lien_tiep_35R"]["phan_ky_theo_SID"] \
    if "phan_ky_theo_SID" in RULES["phan_cach_cat_canh_lien_tiep_35R"] \
    else RULES["phan_cach_cat_canh_lien_tiep_35R"]["phan_cach_theo_SID"]
R_DEP_VS_ARR = RULES["phan_cach_cat_canh_vs_tau_den_35L"]["ma_tran"]
TOUCHDOWN_TO_ROLL_S = RULES["cham_cang_den_chay_da"]["mac_dinh_giay"]
CROSS_MIN_NM = RULES["dieu_kien_cat_qua_35R"]["cu_ly_toi_thieu_tau_tiep_can_35R_NM"]
MAX_AT_HOLD = RULES["gioi_han_diem_cho"]["so_tau_toi_da"]
TAXI_SPD_STRAIGHT = RULES["tham_so_lan"]["toc_do_lan_doan_thang_kt"]
TAXI_SPD_TURN = RULES["tham_so_lan"]["toc_do_lan_khi_re_kt"]

# Ha canh lien tiep: gian cach toi thieu (0 = khong ap dung; 8 NM MANOP da bo theo nguoi dung) + giai phong 35L
# truoc khi tau sau toi 2 NM (cap huan lenh ha canh).
_R_ARR_CFG = RULES["phan_cach_ha_canh_lien_tiep_35L"]
ARR_MIN_SPACING_NM = _R_ARR_CFG.get("gian_cach_toi_thieu_NM", 0.0)
LAND_CLR_NM = _R_ARR_CFG["giai_phong_truoc_huan_lenh_ha_canh"]["cu_ly_cap_huan_lenh_ha_canh_NM"]

# Cat qua 35R (MANOP Phu luc 2 CHC song song)
_R_CROSS = RULES["dieu_kien_cat_qua_35R"]
HOLDLINE_W_M = _R_CROSS["vach_dung_cho_35R_m"]["phia_tay"]
HOLDLINE_E_M = _R_CROSS["vach_dung_cho_35R_m"]["phia_dong"]
CROSS_MAX_S = _R_CROSS["thoi_gian_cat_qua_toi_da_s"]
HOLD_BUFFER_M = 2.0     # mui tau dung cach vach dung cho 2 m

# Han che duong lan E (MANOP): ma chu san bay theo loai tau + nhom duoc phep
_R_TWY_E = RULES["han_che_duong_lan_E"]
CODE = {k: v[0] for k, v in _R_TWY_E["ma_chu_theo_loai"].items()}
ALLOWED_ON_E = _R_TWY_E["khi_cat_canh_code"]
TWY_E_TOL_M = _R_TWY_E["dung_sai_quanh_tim_m"]
PREHOLD_EXCL_M = _R_TWY_E["loai_tru_quanh_PREHOLD_m"]

# Ho so chay da DO DUOC trong mo phong (BADA, 2026-11-04): cu ly doc tim 35R
# tinh tu nguong 35R (m) theo thoi gian ke tu luc bat dau chay da (s). Ca 15
# chuyen di cua ban truoc deu trung nhau +-1 s; day la chuyen CHAM NHAT
# (DEP008 B773). Dung de biet luc tau cat canh qua diem cat cua tau den va luc
# roi khoi duong CHC (3498 m).
DEP_PROFILE = [(0, 150), (6, 182), (11, 265), (16, 397), (21, 578), (26, 810), (31, 1091),
               (36, 1422), (41, 1803), (46, 2233), (51, 2693), (56, 3154), (61, 3616)]
RWY35R_LEN_M = 3498.0
DEP_PASS_MARGIN_S = 3.0
CLEARANCE_LEAD_S = 15.0  # huan lenh cat canh truoc chay da toi da 15 s (code D tro len)


def t_dep_qua(s_m):
    """So giay ke tu luc chay da den khi tau cat canh qua moc s_m doc tim 35R."""
    for (t0, s0), (t1, s1) in zip(DEP_PROFILE, DEP_PROFILE[1:]):
        if s_m <= s1:
            return t0 + (t1 - t0) * max(s_m - s0, 0.0) / (s1 - s0) + DEP_PASS_MARGIN_S
    t0, s0 = DEP_PROFILE[-2]
    t1, s1 = DEP_PROFILE[-1]
    return t1 + (s_m - s1) * (t1 - t0) / (s1 - s0) + DEP_PASS_MARGIN_S


T_DEP_ROI_CHC_S = t_dep_qua(RWY35R_LEN_M)


def wake(ac_type):
    return "HEAVY" if ac_type in HEAVY_TYPES else "MEDIUM"


def duoc_tren_E(code_cat_canh, code_tren_E):
    """MANOP: khi tau code X dang cat canh 35R, tau code Y co duoc o tren duong lan E khong."""
    return code_tren_E in ALLOWED_ON_E[code_cat_canh]


def arr_sep_nm(lead_type, trail_type):
    """Ha canh lien tiep 35L (NM): max(nhieu dong theo cap, giam sat ATS toi
    thieu, gian cach toi thieu ha canh lien tiep cua MANOP)."""
    key = f"{wake(trail_type)}_sau_{wake(lead_type)}"
    return max(R_ARR.get(key, R_ARR["MEDIUM_sau_MEDIUM"]), _R_ARR_CFG["radar_toi_thieu"],
               ARR_MIN_SPACING_NM)


def dep_sep_s(lead_type, trail_type, lead_sid, trail_sid):
    """Phan cach cat canh lien tiep 35R (giay): lay LON NHAT giua phan cach
    nhieu dong xoay va phan cach theo duong bay SID."""
    key = f"{wake(trail_type)}_sau_{wake(lead_type)}"
    wake_s = R_DEP.get(key, R_DEP["MEDIUM_sau_MEDIUM"])
    same_track = sid_same_track(lead_sid, trail_sid)
    track_s = R_DEP_SID["cung_duong_bay_giay"] if same_track else R_DEP_SID["phan_ky_giay"]
    return max(wake_s, track_s)


def sid_first_leg_bearing(sid):
    ch = SID_CHAINS[sid]
    if len(ch) < 3:
        return 352.0
    (la1, lo1) = ch[1][0], ch[1][1]
    (la2, lo2) = ch[2][0], ch[2][1]
    la1, lo1, la2, lo2 = map(math.radians, (la1, lo1, la2, lo2))
    dl = lo2 - lo1
    x = math.sin(dl) * math.cos(la2)
    y = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


_SID_BRG = {s: sid_first_leg_bearing(s) for s in SID_CHAINS}


def sid_same_track(a, b):
    """Hai SID coi la CUNG duong bay khi goc tach < 45 do (nguong trong file
    cau hinh, da danh dau CAN XAC NHAN)."""
    if a == b:
        return True
    d = abs(_SID_BRG[a] - _SID_BRG[b]) % 360
    d = min(d, 360 - d)
    return d < 45.0


def dep_vs_arr_nm(dep_type, arr_type):
    """Cu ly toi thieu tau dang tiep can 35L khi cap huan lenh cat canh."""
    return R_DEP_VS_ARR[wake(dep_type)][wake(arr_type)]


# ---------------------------------------------------------------------------
# Tien ich
# ---------------------------------------------------------------------------
def fmt(t):
    if t < 0:
        t = 0
    return f"{int(t//3600):02d}:{int((t%3600)//60):02d}:{t%60:06.3f}"


def nm(a, b, c, d):
    return haversine_m(a, b, c, d) / 1852.0


def taxi_time_s(path_pts):
    """Thoi gian lan theo chieu dai that va toc do lan trong file cau hinh;
    doan re (doi huong > 30 do) dung toc do re."""
    t = 0.0
    for i in range(len(path_pts) - 1):
        la1, lo1 = path_pts[i][0], path_pts[i][1]
        la2, lo2 = path_pts[i + 1][0], path_pts[i + 1][1]
        d = haversine_m(la1, lo1, la2, lo2)
        spd = TAXI_SPD_STRAIGHT
        if i > 0:
            pa = path_pts[i - 1]
            b1 = math.atan2(lo1 - pa[1], la1 - pa[0])
            b2 = math.atan2(lo2 - lo1, la2 - la1)
            if abs(math.degrees(b2 - b1)) > 30:
                spd = TAXI_SPD_TURN
        t += d / (spd * 0.514444)
    return t


def load_move_seq(filename):
    out = []
    for line in (HERE / filename).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ">" not in line:
            continue
        ts, rest = line.split(">", 1)
        h, m, s = ts.split(":")
        out.append((int(h) * 3600 + int(m) * 60 + float(s), rest))
    return out


def occupancy_s(exit_name, td_spd):
    pts = [(THR35L[0], THR35L[1], td_spd)] + EXIT_CHAINS[exit_name]
    t = 0.0
    for i in range(len(pts) - 1):
        d = haversine_m(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]) / 1852.0
        t += d / max((pts[i][2] + pts[i + 1][2]) / 2.0, 0.5) * 3600.0
    return t


# ---------------------------------------------------------------------------
# LAP LICH
# ---------------------------------------------------------------------------
def build_fleet(n_arr, n_dep, rng):
    """Han ngach CHINH XAC 70/30 roi xao tron bang seed (khong boc ngau nhien
    doc lap tung chuyen -- yeu cau muc 2 prompt)."""
    def pool(n):
        n_h = round(n * RULES["co_cau_tau_bay"]["ty_le_heavy"])
        n_m = n - n_h
        p = ([rng.choice(MEDIUM_TYPES) for _ in range(n_m)] +
             [rng.choice(HEAVY_TYPES) for _ in range(n_h)])
        rng.shuffle(p)
        # Muc 2 prompt: bao dam xuat hien du cac cap ke tiep H-H, H-M, M-H, M-M.
        # Xao lai (van bang cung rng -> tai lap) den khi du; gioi han 5000 lan.
        for _ in range(5000):
            cap = {(wake(p[k]), wake(p[k + 1])) for k in range(len(p) - 1)}
            if n_h < 2 or n_m < 2 or len(cap) == 4:
                break
            rng.shuffle(p)
        return p, n_m, n_h
    arr, am, ah = pool(n_arr)
    dep, dm, dh = pool(n_dep)
    return arr, dep, (am, ah, dm, dh)


def schedule(rng, first_td=FIRST_ARR_TD, n_arr=40, n_dep=40, tre_them=None):
    """Lap lich XEN KE: lan luot 1 chuyen den -> 1 chuyen di -> 1 chuyen den...

    Khong co nhip muc tieu: moi moc dat SOM NHAT ma van thoa DONG THOI moi phan
    cach toi thieu, cho den het 60 phut. Nhip thu duoc CHINH LA nang luc dieu
    hanh bay toi da cua cau hinh khai thac nay.

    Rang buoc cho chuyen den (moc cham banh):
      - ha canh lien tiep: max(nhieu dong MANOP/ICAO, 3 NM) (8 NM MANOP da bo);
      - tau truoc da cat qua HET 35R (35L moi duoc coi la giai phong) truoc
        khi tau nay toi 2 NM -- cap huan lenh ha canh;
      - cach chuyen di vua cat canh theo bang du thao/MANOP muc 4.2.1.
    Rang buoc cho chuyen di (moc chay da):
      - chay da sau cham cang TOUCHDOWN_TO_ROLL_S (huan lenh luon sau cham cang);
      - phan cach cat canh lien tiep;
      - MANOP duong lan E: tau code D/E/F cat canh thi khong co tau code D tro
        len o tren duong lan E (tau den da cat qua 35R dang lan ve ben).
    "Gia tang gian cach thich hop khi co tau cat canh xen giua" (MANOP) tu
    nhien thoa: moc den ke tiep lay max cua moi rang buoc tren.
    """
    arr_types, dep_types, quota = build_fleet(n_arr, n_dep, rng)
    arr_stars = [rng.choice(list(STAR_IAF)) for _ in range(n_arr)]
    dep_sids = [rng.choice(SID_NAMES) for _ in range(n_dep)]
    arr_exits = [rng.choice(["G4", "G6"]) for _ in range(n_arr)]
    dep_gates = [rng.choice(["G26", "G27"]) for _ in range(n_dep)]

    arrs, deps = [], []
    i = j = 0
    while i < n_arr and j < n_dep:
        # ---- chuyen den thu i ----
        if not arrs:
            t_arr = first_td
        else:
            lead = arrs[-1]
            if "t_ce" not in lead:
                lap_lich_lan_vao(lead, deps)
            t_arr = max(
                lead["td"] + arr_sep_nm(lead["type"], arr_types[i])        # nhieu dong / giam sat ATS
                / approach_speeds(arr_types[i])[2] * 3600.0,
                lead["t_ce"] + LAND_CLR_NM                                 # 35L giai phong truoc 2 NM
                / approach_speeds(arr_types[i])[3] * 3600.0,
            )
        if deps:                       # du cu ly voi chuyen di vua cat canh
            need = dep_vs_arr_nm(deps[-1]["type"], arr_types[i])
            t_arr = max(t_arr, deps[-1]["roll"]
                        + need / approach_speeds(arr_types[i])[2] * 3600.0)
        if t_arr >= first_td + DURATION_S:
            break
        arrs.append({"i": i + 1, "id": f"ARR{i+1:03d}", "type": arr_types[i],
                     "star": arr_stars[i], "exit": arr_exits[i], "td": t_arr})
        i += 1

        # ---- chuyen di thu j, chen ngay sau chuyen den vua roi ----
        t_roll = t_arr + TOUCHDOWN_TO_ROLL_S
        if deps:
            t_roll = max(t_roll, deps[-1]["roll"]
                         + dep_sep_s(deps[-1]["type"], dep_types[j],
                                     deps[-1]["sid"], dep_sids[j]))
        # Lui them khi khau lap lich lan ra khong tim duoc gio roi ben hop le
        # cho chuyen nay (xem main): dieu hanh that cung lui gio cat canh.
        t_roll += (tre_them or {}).get(j, 0.0)
        # Chuyen di KE TIEP la code F: MANOP chi cho code <= E tren duong lan E
        # khi co tau cat canh 35R, nen tau code F chi lan tren E khi KHONG co tau
        # nao dang cat canh. Nó toi diem cho dung luc chuyen di nay chay da, nen
        # chuyen nay phai cach chuyen di truoc it nhat (thoi gian roi CHC + thoi
        # gian tau code F lan tren E) -- tuc bo trong mot khe cat canh.
        if deps and j + 1 < n_dep and CODE[dep_types[j + 1]] == "F":
            t_roll = max(t_roll, deps[-1]["roll"] + T_DEP_ROI_CHC_S
                         + thoi_gian_tren_E_lan_ra(dep_gates[j + 1]) + 5.0)
        # MANOP duong lan E: lui chay da den khi tau den (da cat qua 35R) co ma
        # chu khong duoc phep roi khoi duong lan E. Chuyen den vua ha canh
        # (arrs[-1]) duoc tinh lai lich lan vao THEO gio chay da dang xet: binh
        # thuong no cat qua 35R sau chuyen di nay, nhung khi gio chay da bi lui
        # (tre_them) no co the da cat qua truoc va dang o tren E luc chay da.
        ma = CODE[dep_types[j]]
        for _ in range(50):
            doi = False
            lap_lich_lan_vao(arrs[-1], deps + [{"roll": t_roll}])
            for a in arrs:
                if duoc_tren_E(ma, CODE[a["type"]]):
                    continue
                for e0, e1 in a.get("E", []):
                    if e0 < t_roll + T_DEP_ROI_CHC_S and e1 > t_roll:
                        t_roll, doi = e1 + 1.0, True
            if not doi:
                break
        if t_roll >= first_td + DURATION_S:
            break
        deps.append({"i": j + 1, "id": f"DEP{j+1:03d}", "type": dep_types[j],
                     "sid": dep_sids[j], "gate": dep_gates[j], "roll": t_roll})
        j += 1
        lap_lich_lan_vao(arrs[-1], deps)

    for a in arrs:
        lap_lich_lan_vao(a, deps)       # moc cuoi cung theo lich cat canh day du
    return arrs, deps, quota


_CACHE_HINH: dict = {}


def vi_tri_theo_thoi_gian(pts, t0, t1):
    """Tra ve ham t -> (lat, lon): di deu doc tuyen pts tu t0 den t1.

    Dung CHUNG mot phep noi suy voi taxi_moves() de vi tri dung de kiem tra
    xung dot KHOP CHINH XAC voi vi tri se duoc phat ra bang lenh MOVE."""
    key = (pts[0], pts[-1], len(pts))
    if key not in _CACHE_HINH:
        sh = densify(pts, 3.0)
        cm = [0.0]
        for k in range(len(sh) - 1):
            cm.append(cm[-1] + haversine_m(*sh[k], *sh[k + 1]))
        _CACHE_HINH[key] = (sh, cm)
    shape, cum = _CACHE_HINH[key]
    total, dur = cum[-1], max(t1 - t0, 1.0)

    def at(t):
        if t <= t0:
            return shape[0]
        if t >= t1:
            return shape[-1]
        s = total * (t - t0) / dur
        k = 0
        while k < len(cum) - 2 and cum[k + 1] < s:
            k += 1
        f = (s - cum[k]) / max(cum[k + 1] - cum[k], 1e-9)
        return (shape[k][0] + (shape[k + 1][0] - shape[k][0]) * f,
                shape[k][1] + (shape[k + 1][1] - shape[k][1]) * f)
    return at


_CACHE_TUYEN: dict = {}


def _tuyen_lan_vao_ben(exit_name):
    """Hinh tuyen + thoi luong lan vao ben, doc tu file _ARR_RESUME_*.
    Co cache: khau giai xung dot goi ham nay hang nghin lan."""
    if exit_name in _CACHE_TUYEN:
        return _CACHE_TUYEN[exit_name]
    seq = load_move_seq(ARR_TAXI_FILES[exit_name])
    pts = list(EXIT_TAIL[exit_name])
    for (_dt, cmd) in seq:
        if cmd.startswith("MOVE"):
            f = cmd.split("MOVE %0,")[1].split(",")
            pts.append((float(f[0]), float(f[1])))
    _CACHE_TUYEN[exit_name] = (pts, seq[-1][0] - seq[0][0])
    return _CACHE_TUYEN[exit_name]


def _do_dai(pts):
    return sum(haversine_m(*pts[k], *pts[k + 1]) for k in range(len(pts) - 1))


def tren_duong_lan_E(la, lo):
    """Diem (la, lo) nam tren duong lan E theo dinh nghia trong file cau hinh
    (khong tinh vi tri dung cho cat canh quanh PREHOLD)."""
    p = _xy(la, lo)
    if math.dist(p, _xy(PREHOLD[0], PREHOLD[1])) < PREHOLD_EXCL_M:
        return False
    return min(_d_seg(p, a, b) for a, b in TWY_E_SEGS) < TWY_E_TOL_M


_CACHE_E: dict = {}


def khoang_tren_E(pts):
    """([(s0, s1)], tong) -- cac khoang cu ly doc tuyen (m) nam tren duong lan E."""
    key = (pts[0], pts[-1], len(pts))
    if key not in _CACHE_E:
        sh = densify(pts, 3.0)
        s, out, cur = 0.0, [], None
        for k, p in enumerate(sh):
            if k:
                s += haversine_m(*sh[k - 1], *p)
            on = tren_duong_lan_E(*p)
            if on and cur is None:
                cur = [s, s]
            elif on:
                cur[1] = s
            elif cur is not None:
                out.append(tuple(cur))
                cur = None
        if cur is not None:
            out.append(tuple(cur))
        _CACHE_E[key] = (out, s)
    return _CACHE_E[key]


def _khoang_E_theo_gio(pts, t0, t1):
    e, tot = khoang_tren_E(pts)
    if tot <= 0:
        return []
    return [(t0 + (t1 - t0) * s0 / tot, t0 + (t1 - t0) * s1 / tot) for s0, s1 in e]


_CACHE_CHIA: dict = {}


def chia_tuyen_vao_ben(exit_name, actype):
    """Tach tuyen lan vao ben theo vach dung cho 35R (MANOP Phu luc 2 CHC):
      d1: tu cuoi chuoi thoat ly toi VI TRI DUNG CHO truoc 35R -- mui tau cach
          vach dung cho phia tay HOLD_BUFFER_M (tau nam GIUA hai CHC);
      d2: CAT QUA 35R, toi khi duoi tau qua vach dung cho phia dong;
      d3: phan con lai ve ben (giu toc do trung binh cua file tuyen goc).
    d1, d2 di o toc do lan doan thang (15 kt): cat qua 35R mat
    (184 m + chieu dai tau)/7.7 m/s <= 34 s, duoi gioi han 45 s cua MANOP."""
    key = (exit_name, actype)
    if key not in _CACHE_CHIA:
        pts, dur = _tuyen_lan_vao_ben(exit_name)
        L = aircraft_length_m(actype)
        sh = densify(pts, 3.0)
        xt = [truc_35R(*p)[1] for p in sh]
        x_hp = -(HOLDLINE_W_M + L / 2.0 + HOLD_BUFFER_M)
        x_out = HOLDLINE_E_M + L / 2.0 + HOLD_BUFFER_M
        if xt[0] > x_hp:
            raise SystemExit(f"Tuyen {exit_name}: diem dau ({xt[0]:.0f} m) da qua vi tri dung cho "
                             f"truoc 35R cua {actype} ({x_hp:.0f} m)")
        k_hp = 0
        while k_hp + 1 < len(sh) and xt[k_hp + 1] <= x_hp:
            k_hp += 1
        k_x = next(k for k in range(len(sh)) if xt[k] >= x_out)
        d1, d2, d3 = sh[:k_hp + 1], sh[k_hp:k_x + 1], sh[k_x:]
        v = TAXI_SPD_STRAIGHT * 0.514444
        k0 = min(range(len(sh)), key=lambda k: abs(xt[k]))
        _CACHE_CHIA[key] = {
            "d1": d1, "d2": d2, "d3": d3,
            "t1": _do_dai(d1) / v, "t2": _do_dai(d2) / v,
            "t3": dur * _do_dai(d3) / _do_dai(sh),
            "s_cat": truc_35R(*sh[k0])[0],          # diem cat tim 35R (doc tim, m)
        }
    return _CACHE_CHIA[key]


def lap_lich_lan_vao(a, deps):
    """Dat cac moc lan vao ben cua chuyen den a theo lich cat canh `deps`:
      t_vacated: het chuoi thoat ly LNAV (+ dem), bat dau lan bang MOVE;
      t_hp     : toi vi tri dung cho truoc 35R (giua hai CHC);
      t_cs/t_ce: bat dau / xong cat qua 35R;   t_onblock: toi ben;
      E        : cac khoang thoi gian tau o tren duong lan E.
    Khong cat qua 35R trong khoang [huan lenh cat canh, tau cat canh qua diem
    cat + 100 m] cua bat ky chuyen di nao -- tau dung cho giua hai CHC cho den
    khi duoc phep (MANOP: trong luc do khong su dung 35L)."""
    c = chia_tuyen_vao_ben(a["exit"], a["type"])
    a["t_vacated"] = a["td"] + occupancy_s(a["exit"], approach_speeds(a["type"])[3]) + HOLD_MARGIN_S
    t_hp = a["t_vacated"] + c["t1"]
    t_cs = t_hp
    t_qua = t_dep_qua(c["s_cat"] + 100.0)
    for _ in range(50):
        doi = False
        for d in deps:
            w0, w1 = d["roll"] - CLEARANCE_LEAD_S, d["roll"] + t_qua
            if t_cs < w1 and t_cs + c["t2"] > w0:
                t_cs, doi = w1, True
        if not doi:
            break
    a["t_hp"], a["t_cs"], a["t_ce"] = t_hp, t_cs, t_cs + c["t2"]
    a["t_onblock"] = a["t_ce"] + c["t3"]
    a["E"] = (_khoang_E_theo_gio(c["d2"], a["t_cs"], a["t_ce"])
              + _khoang_E_theo_gio(c["d3"], a["t_ce"], a["t_onblock"]))
    return a


def ham_vi_tri_nhieu_doan(doan):
    """Ghep cac doan (pts, t0, t1) di deu thanh mot ham t -> (lat, lon); giua
    hai doan tau dung yen tai diem cuoi doan truoc."""
    fs = [(t0, t1, pts, vi_tri_theo_thoi_gian(pts, t0, t1)) for pts, t0, t1 in doan if len(pts) > 1]

    def at(t):
        cur = fs[0][2][0]
        for t0, t1, pts, f in fs:
            if t < t0:
                return cur
            if t <= t1:
                return f(t)
            cur = pts[-1]
        return cur
    return at


def doan_lan_vao(a):
    c = chia_tuyen_vao_ben(a["exit"], a["type"])
    return [(c["d1"], a["t_vacated"], a["t_hp"]), (c["d2"], a["t_cs"], a["t_ce"]),
            (c["d3"], a["t_ce"], a["t_onblock"])]


def quy_dao_lan(arrs, deps):
    """{acid: (t_bat_dau, t_ket_thuc, ham_vi_tri, chieu_dai_m)} cho pha LAN
    TREN DUONG LAN cua moi chuyen (khong tinh doan chay da/thoat ly tren
    duong CHC)."""
    out = {}
    for a in arrs:
        if "t_vacated" not in a:
            continue
        out[a["id"]] = (a["t_vacated"], a["t_onblock"], ham_vi_tri_nhieu_doan(doan_lan_vao(a)),
                        aircraft_length_m(a["type"]))
    for d in deps:
        if "_doan" in d:
            out[d["id"]] = (d["start_taxi"], d["lineup"], ham_vi_tri_nhieu_doan(d["_doan"]),
                            aircraft_length_m(d["type"]))
            continue
        gate = GATE26 if d["gate"] == "G26" else GATE27
        path = TAXI_COMMON_G26 if d["gate"] == "G26" else TAXI_COMMON_G27
        pts = [(gate[0], gate[1])] + [(p[0], p[1]) for p in path]
        t0, t1 = d["start_taxi"], d["start_taxi"] + d["taxi_s"]
        out[d["id"]] = (t0, t1, vi_tri_theo_thoi_gian(pts, t0, t1),
                        aircraft_length_m(d["type"]))
    return out


def cap_vi_pham_mat_dat(qd, buoc_s=1.0):
    """Moi cap tau bay lan qua gan nhau. Khoang cach yeu cau lay DUNG cong
    thuc cua plugin surfacetaxi.py: nua chieu dai hai tau + TAXI_TAIL_BUFFER
    ('con lai sau duoi tau truoc'), khong phai khoang cach tam-toi-tam."""
    ds = sorted(qd.items(), key=lambda kv: kv[1][0])
    xau = []
    for p in range(len(ds)):
        ida, (a0, a1, fa, la) = ds[p]
        for q in range(p + 1, len(ds)):
            idb, (b0, b1, fb, lb) = ds[q]
            if b0 >= a1:
                break                      # da sap xep theo t0 -> khong con giao
            req = (la + lb) / 2.0 + TAXI_TAIL_BUFFER_M
            t, hep = max(a0, b0), None
            while t <= min(a1, b1):
                pa, pb = fa(t), fb(t)
                dd = haversine_m(*pa, *pb)
                if dd < req and (hep is None or dd < hep[1]):
                    hep = (t, dd)
                t += buoc_s
            if hep:
                xau.append({"t": hep[0], "d": hep[1], "req": req, "a": ida, "b": idb})
    return xau


def _va_cham(qd_a, qd_b, buoc_s=1.0):
    """Khoang cach nho nhat giua hai quy dao lan (None neu khong vi pham)."""
    a0, a1, fa, la = qd_a
    b0, b1, fb, lb = qd_b
    t0, t1 = max(a0, b0), min(a1, b1)
    if t0 > t1:
        return None
    req = (la + lb) / 2.0 + TAXI_TAIL_BUFFER_M
    t, nho_nhat = t0, None
    while t <= t1:
        dd = haversine_m(*fa(t), *fb(t))
        if dd < req and (nho_nhat is None or dd < nho_nhat):
            nho_nhat = dd
        t += buoc_s
    return nho_nhat


def _qd_dep(d, start_taxi):
    gate = GATE26 if d["gate"] == "G26" else GATE27
    path = TAXI_COMMON_G26 if d["gate"] == "G26" else TAXI_COMMON_G27
    pts = [(gate[0], gate[1])] + [(p[0], p[1]) for p in path]
    t1 = start_taxi + d["taxi_s"]
    return (start_taxi, t1, vi_tri_theo_thoi_gian(pts, start_taxi, t1),
            aircraft_length_m(d["type"]))


# Thoi gian toi thieu tu diem cho (PREHOLD) len vi tri chay da tren tim 35R:
# ~130 m o toc do lan khi re + 10 s on dinh truoc khi chay da.
LINEUP_S = (haversine_m(PREHOLD[0], PREHOLD[1], RWYHOLD[0], RWYHOLD[1])
            + haversine_m(RWYHOLD[0], RWYHOLD[1], *LINEUP_35R)) / (TAXI_SPD_TURN * 0.514444) + 10.0


def _tuyen_lan_ra(d):
    gate = GATE26 if d["gate"] == "G26" else GATE27
    path = TAXI_COMMON_G26 if d["gate"] == "G26" else TAXI_COMMON_G27
    return [(gate[0], gate[1])] + [(p[0], p[1]) for p in path]


def thoi_gian_tren_E_lan_ra(gate_name):
    """So giay tu luc tau lan ra (tu ben gate_name) vao duong lan E den luc roi E."""
    path = TAXI_COMMON_G26 if gate_name == "G26" else TAXI_COMMON_G27
    e = _khoang_E_theo_gio(_tuyen_lan_ra({"gate": gate_name}), 0.0, taxi_time_s(path))
    return (e[-1][1] - e[0][0]) if e else 0.0


def vi_pham_E_khi_lan_ra(d, start_taxi, deps, doan=None):
    """id chuyen di dang cat canh ma d (lan ra tu start_taxi) lai o tren duong
    lan E trai MANOP; None neu khong vi pham. `doan` = cac doan lan thuc te
    (co xep hang); mac dinh lan thang mot mach toi PREHOLD."""
    if doan is None:
        my = _khoang_E_theo_gio(_tuyen_lan_ra(d), start_taxi, start_taxi + d["taxi_s"])
    else:
        my = [e for pts, a, b in doan if len(pts) > 1 for e in _khoang_E_theo_gio(pts, a, b)]
    for h in deps:
        if h is d or duoc_tren_E(CODE[h["type"]], CODE[d["type"]]):
            continue
        if any(e0 < h["roll"] + T_DEP_ROI_CHC_S and e1 > h["roll"] for e0, e1 in my):
            return h["id"]
    return None


def _t_vao_diem_cho(o):
    return o.get("t_xep_hang", o["start_taxi"] + o["taxi_s"])


def qua_tai_diem_cho(d, t_xep, deps):
    """True neu d vao khu diem cho luc t_xep lam so tau o diem cho (tinh tu
    luc vao hang cho den luc bat dau chay da, gom ca tau da len duong CHC)
    vuot MAX_AT_HOLD."""
    a0, a1 = int(t_xep), int(d["roll"])
    khac = [(int(_t_vao_diem_cho(o)), int(o["roll"])) for o in deps if o is not d]
    for p in [a0] + [s for s, _ in khac if a0 <= s <= a1]:
        if 1 + sum(1 for s, e in khac if s <= p <= e) > MAX_AT_HOLD:
            return True
    return False


CHO_CACH_S = 20.0   # tau sau toi PREHOLD it nhat 20 s sau khi tau truoc roi PREHOLD
HANG2_DEM_M = 2.0   # dem them sau khoang cach toi thieu xep hang
_CACHE_HINH_RA: dict = {}


def _hinh_lan_ra(d):
    if d["gate"] not in _CACHE_HINH_RA:
        sh = densify(_tuyen_lan_ra(d), 3.0)
        cum = [0.0]
        for k in range(len(sh) - 1):
            cum.append(cum[-1] + haversine_m(*sh[k], *sh[k + 1]))
        _CACHE_HINH_RA[d["gate"]] = (sh, cum)
    return _CACHE_HINH_RA[d["gate"]]


def ke_hoach_lan_ra(d, start, truoc):
    """Ke hoach lan ra cua d (bat dau lan luc `start`), co XEP HANG tai diem cho E.

    `truoc` = chuyen di chay da ngay truoc d (da xep xong) hoac None. Neu d toi
    PREHOLD khi tau truoc con dang dung o do, d dung o VI TRI THU HAI phia sau,
    cach tam tau truoc = nua chieu dai hai tau + 20 m (+2 m dem) -- dung muc 6
    prompt; 10 s sau khi tau truoc len duong CHC thi d lan len PREHOLD o toc do
    lan khi re. Diem cho chi co hai vi tri (PREHOLD + vi tri thu hai) cong voi
    tau da len duong CHC = toi da 3 tau. Tra ve None neu d toi khi ca hai vi tri
    con kin (tau truoc chua len toi PREHOLD).

    Tra ve dict: t_xep_hang (vao khu diem cho), t_prehold, lineup, hang2,
    doan = [(pts, t0, t1)] cac doan di chuyen (giua cac doan tau dung yen)."""
    sh, cum = _hinh_lan_ra(d)
    v = cum[-1] / d["taxi_s"]
    a_full = start + d["taxi_s"]
    if truoc is None or a_full >= truoc["lineup"] + CHO_CACH_S:
        return {"t_xep_hang": a_full, "t_prehold": a_full, "hang2": False,
                "lineup": max(d["lineup_min"], a_full), "doan": [(sh, start, a_full)]}
    off = ((aircraft_length_m(truoc["type"]) + aircraft_length_m(d["type"])) / 2.0
           + TAXI_TAIL_BUFFER_M + HANG2_DEM_M)
    k = len(sh) - 1
    while k > 0 and haversine_m(*sh[k], *sh[-1]) < off:
        k -= 1
    t_s1 = start + cum[k] / v
    if t_s1 < truoc.get("t_prehold", truoc["start_taxi"] + truoc["taxi_s"]):
        return None                        # vi tri thu hai con chua trong
    t_len = max(truoc["lineup"] + CHO_CACH_S / 2.0, t_s1)
    pts2 = sh[k:]
    t_pre = t_len + _do_dai(pts2) / (TAXI_SPD_TURN * 0.514444)
    return {"t_xep_hang": t_s1, "t_prehold": t_pre, "hang2": True,
            "lineup": max(d["lineup_min"], t_pre),
            "doan": [(sh[:k + 1], start, t_s1), (pts2, t_len, t_pre)]}


def nhuong_duong_khi_lan(arrs, deps):
    """Giai xung dot DOI DAU khi lan giua tau vao ben va tau ra duong CHC.

    Quy tac uu tien lay DUNG tu plugin surfacetaxi.py cua du an: tau bay con
    QUANG DUONG TOI DICH NGAN HON thi duoc di truoc. Luc hai tau gap nhau,
    tau DEN sap vao ben (gan dich) con tau DI vua roi ben (xa dich), nen tau
    DI phai nhuong. Nhuong duoc gan nhu "mien phi" vi tau DI con phai cho o
    diem cho truoc 35R (trung binh 175 s): doi gio roi ben chi lam thay doi
    thoi gian cho, KHONG lam tre thoi diem cat canh.

    Cach giai: xep lan luot tung chuyen di theo thu tu gio roi ben, moi chuyen
    chon do LECH NHO NHAT so voi gio goc sao cho khong va cham voi bat ky tau
    nao DA XEP (moi chuyen den + moi chuyen di truoc no). Khong do tung buoc
    co dinh nhu ban dau -- cach do dao dong vo tan (day som 15s roi lui 15s
    lap lai) vi buoc co dinh khong bao gio dat dung mep cua so an toan.
    """
    qd_arr = {a["id"]: v for a, v in
              ((a, quy_dao_lan([a], [])[a["id"]]) for a in arrs if "t_vacated" in a)}
    da_xep = dict(qd_arr)
    nhat_ky = []

    # Xep theo THU TU CAT CANH: ke hoach xep hang cua mot chuyen phu thuoc
    # chuyen cat canh ngay truoc no, nen chuyen do phai xep xong truoc.
    truoc = None
    for d in sorted(deps, key=lambda x: x["roll"]):
        goc = d["start_taxi"]
        chon = None
        for delta in sorted(range(-600, 601, 5), key=lambda x: (abs(x), x < 0)):
            t = goc + delta
            if t < -1e-6:
                continue
            kh = ke_hoach_lan_ra(d, t, truoc)
            # toi PREHOLD van con du thoi gian lan len duong CHC truoc luc chay da
            if kh is None or kh["t_prehold"] > d["roll"] - LINEUP_S + 1e-6:
                continue
            if (vi_pham_E_khi_lan_ra(d, t, deps, kh["doan"])
                    or qua_tai_diem_cho(d, kh["t_xep_hang"], deps)):
                continue
            qd = (t, kh["lineup"], ham_vi_tri_nhieu_doan(kh["doan"]), aircraft_length_m(d["type"]))
            if any(_va_cham(qd, v) is not None for v in da_xep.values()):
                continue
            chon = (t, kh)
            break
        if chon is None:
            nhat_ky.append(f"{d['id']}: KHONG tim duoc gio roi ben nao tranh duoc "
                           f"va cham / duong lan E / diem cho")
            d["khong_xep_duoc"] = True
            chon = (goc, ke_hoach_lan_ra(d, goc, None))
        t, kh = chon
        if abs(t - goc) > 1e-6 and not d.get("khong_xep_duoc"):
            ly_do = ("duong lan E" if vi_pham_E_khi_lan_ra(d, goc, deps) else "nhuong duong khi lan")
            nhat_ky.append(f"{d['id']} {'lui' if t > goc else 'day som'} "
                           f"{abs(t-goc):.0f}s ({ly_do})")
        d["start_taxi"] = t
        d["lineup"] = kh["lineup"]
        d["t_xep_hang"], d["t_prehold"], d["hang2"] = kh["t_xep_hang"], kh["t_prehold"], kh["hang2"]
        d["_doan"] = kh["doan"]
        da_xep[d["id"]] = (t, d["lineup"], ham_vi_tri_nhieu_doan(kh["doan"]),
                           aircraft_length_m(d["type"]))
        truoc = d
    return deps, nhat_ky


def schedule_taxi_out(deps):
    """Lap lich lan ra: tinh nguoc tu thoi diem len duong CHC, roi lui thoi
    diem bat dau lan neu so tau tai diem cho vuot MAX_AT_HOLD."""
    for j, d in enumerate(deps):
        path = TAXI_COMMON_G26 if d["gate"] == "G26" else TAXI_COMMON_G27
        d["taxi_s"] = taxi_time_s(path)
        # Tau sau duoc LEN duong CHC khi tau truoc BAT DAU CHAY DA (muc 3e)
        d["lineup"] = deps[j - 1]["roll"] if j > 0 else d["roll"] - 60.0
        d["lineup"] = min(d["lineup"], d["roll"] - LINEUP_S)
        d["lineup_min"] = d["lineup"]          # som nhat duoc len duong CHC (tau truoc chay da)
        d["start_taxi"] = d["lineup"] - d["taxi_s"]

    # Dem so tau tai diem cho theo tung giay; neu >MAX thi lui tau den sau
    for _ in range(200):
        busy = {}
        over = None
        for d in sorted(deps, key=lambda x: x["start_taxi"]):
            t0 = int(d["start_taxi"] + d["taxi_s"])     # toi diem cho
            t1 = int(d["roll"])                         # roi diem cho (bat dau chay da)
            for t in range(max(t0, 0), max(t1, 0) + 1):
                busy[t] = busy.get(t, 0) + 1
                if busy[t] > MAX_AT_HOLD and over is None:
                    over = (t, d)
        if over is None:
            break
        t_bad, d_bad = over
        d_bad["start_taxi"] += 30.0                     # giu them tai ben 30s
    return deps


# ---------------------------------------------------------------------------
# SINH LENH .scn
# ---------------------------------------------------------------------------
def cadas_to_thr_s(actype):
    """Thoi gian bay tu CADAS toi nguong 35L theo toc do BADA cua tung loai."""
    legs = post_cadas_legs(actype)
    t = 0.0
    for i in range(len(legs) - 1):
        d = haversine_m(legs[i][0], legs[i][1], legs[i + 1][0], legs[i + 1][1])
        v = ((legs[i][3] + legs[i + 1][3]) / 2.0
             * tas_correction((legs[i][2] + legs[i + 1][2]) / 2.0) * 0.514444)
        t += d / v
    return t


def densify(pts, step_m):
    """Chen diem sao cho khoang cach <= step_m, giu nguyen hinh tuyen."""
    out = [pts[0]]
    for i in range(len(pts) - 1):
        la1, lo1 = pts[i][0], pts[i][1]
        la2, lo2 = pts[i + 1][0], pts[i + 1][1]
        d = haversine_m(la1, lo1, la2, lo2)
        n = max(1, int(math.ceil(d / step_m)))
        for k in range(1, n + 1):
            f = k / n
            out.append((la1 + (la2 - la1) * f, lo1 + (lo2 - lo1) * f))
    return out


def taxi_moves(acid, pts, t0, t1, alt_ft=0):
    """Chuoi MOVE deu MOVE_DT giay doc tuyen pts, di het trong [t0, t1].

    Dung MOVE (khong dung ADDWPT/LNAV) cho toan bo pha lan vi:
      - kiem soat CHINH XAC thoi diem toi/roi diem cho -> so lieu kiem chung
        ve so tau tai diem cho moi co y nghia;
      - tranh bay VNAV/selspd=-999 lam tau dung yen vinh vien (da ghi nhan
        trong _KB5GEN_CROSS_G4.scn cua kich ban 40 chuyen);
      - nhip THOI GIAN deu (khong phai khoang cach deu) de khong bao gio co
        khoang trong giua 2 lenh MOVE -- da do duoc tau "bay tu do" 350-1138
        kt khi phat MOVE theo khoang cach deu luc giam toc.
    """
    shape = densify(pts, 3.0)
    cum = [0.0]
    for i in range(len(shape) - 1):
        cum.append(cum[-1] + haversine_m(*shape[i], *shape[i + 1]))
    total = cum[-1]
    dur = max(t1 - t0, 1.0)

    def at(s):
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

    out, t = [], t0
    while t < t1:
        s = total * (t - t0) / dur
        la, lo = at(s)
        nla, nlo = at(min(s + 6.0, total))
        spd = total / dur / 0.514444
        out.append((t, f"MOVE {acid},{la:.6f},{lo:.6f},{alt_ft},"
                       f"{bearing_deg(la, lo, nla, nlo):.1f},{spd:.1f}"))
        t += MOVE_DT
    la, lo = shape[-1]
    prev = at(max(total - 6.0, 0.0))
    out.append((t1, f"MOVE {acid},{la:.6f},{lo:.6f},{alt_ft},"
                    f"{bearing_deg(*prev, la, lo):.1f},0.0"))
    return out


def hold_moves(acid, pt, hdg, t0, t1):
    """Ghim tau dung yen tai diem cho tu t0 den t1."""
    out, t = [], t0 + HOLD_DT
    while t < t1:
        out.append((t, f"MOVE {acid},{pt[0]:.6f},{pt[1]:.6f},0,{hdg:.1f},0.0"))
        t += HOLD_DT
    return out


def build_arr_lines(a):
    """Lenh cho 1 chuyen den: CRE tren STAR -> ILS 35L -> thoat ly -> lan ve ben."""
    L = []
    actype, star = a["type"], a["star"]
    # Bu sai lech do bang mo phong that. Bu vao MOC QUA CADAS chu khong phai
    # thoi diem CRE: chuyen den dau tien phai sinh ngay tai T=0 nen neu bu vao
    # t_cre thi gia tri am bi kep ve 0 va hieu chuan khong co tac dung (da do:
    # ARR001 ket o +66.5s qua ca 6 vong). Bu vao t_cadas thi tau duoc sinh o
    # diem GAN CADAS hon tuong ung, van co tac dung ca khi t_cre = 0.
    t_cadas = a["td"] - cadas_to_thr_s(actype) - CALIB.get(a["id"], 0.0)
    full = _STAR_TRANSIT[star]

    if t_cadas >= full:
        iaf = STAR_IAF[star]
        nxt = (_full_pre_cadas_chain(star) + [_CADAS_PLACEHOLDER])[0]
        t_cre = t_cadas - full
        lat, lon, alt, spd = iaf
        hdg = bearing_deg(lat, lon, nxt[0], nxt[1])
        pre = _full_pre_cadas_chain(star)
        spawn_note = f"CRE tai IAF {star}"
    else:
        lat, lon, alt, spd, hdg, rest = truncated_star_spawn(star, t_cadas)
        t_cre = 0.0
        pre = [n for n in rest]
        spawn_note = (f"CRE tren STAR {star} tai diem con lai {t_cadas/60:.1f} phut "
                      f"bay toi CADAS (bo doan IAF xa de kip nhip)")

    legs = list(pre) + post_cadas_legs(actype)
    out, prev_alt = [], 99999          # ep ha do cao don dieu
    for (la, lo, al, sp) in legs:
        al = min(al, prev_alt)
        out.append((la, lo, al, sp))
        prev_alt = al
    legs = out

    L.append((t_cre, f"CRE {a['id']},{actype},{lat:.6f},{lon:.6f},{hdg:.1f},{alt},{spd}"))
    L.append((t_cre, f"# {a['id']} {actype} ({wake(actype)}) -- {spawn_note}; "
                     f"cham banh 35L luc {fmt(a['td'])}, thoat ly {a['exit']} ve {ARR_GATE_NAME[a['exit']]}"))
    for (la, lo, al, sp) in legs:
        L.append((t_cre, f"{a['id']} ADDWPT {la:.6f},{lo:.6f} {al} {sp}"))
    for (la, lo, sp) in EXIT_CHAINS[a["exit"]]:
        L.append((t_cre, f"{a['id']} ADDWPT {la:.6f},{lo:.6f} 0 {sp}"))
    L.append((t_cre, f"{a['id']} LNAV ON"))
    L.append((t_cre, f"{a['id']} VNAV ON"))

    # Toi diem cho sau khi thoat ly -> chuyen sang dieu khien bang MOVE
    t_hold = a["t_vacated"]
    L.append((t_hold, f"{a['id']} LNAV OFF"))
    L.append((t_hold, f"{a['id']} VNAV OFF"))

    # Lan vao ben. Lay HINH TUYEN tu file _ARR_RESUME_* (bam tim duong lan
    # that) nhung PHAT LAI theo nhip thoi gian deu MOVE_DT, khong chep nguyen
    # nhip cu: file goc cua kich ban 40 chuyen co cho gian toi 3.5s va lenh ap
    # chot van dat 5 kt -- da do duoc tau bay tu do 674 m trong khoang trong do
    # (hien thanh 1019 kt). Lenh cuoi dat 0 kt roi ghim them vai lan tai ben
    # (da kiem chung: sau lenh MOVE 0 kt tau dung yen tuyet doi).
    # Ba doan: (1) toi vi tri dung cho truoc 35R giua hai CHC, dung cho neu
    # tau cat canh chua qua diem cat; (2) cat qua 35R o 15 kt (<= 45 s, MANOP);
    # (3) ve ben theo toc do trung binh cua tuyen goc.
    c = chia_tuyen_vao_ben(a["exit"], a["type"])
    if len(c["d1"]) > 1:
        L += taxi_moves(a["id"], c["d1"], t_hold, a["t_hp"])
    hp = c["d2"][0]
    L += hold_moves(a["id"], hp, bearing_deg(*hp, *c["d2"][min(3, len(c["d2"]) - 1)]),
                    a["t_hp"], a["t_cs"])
    L += taxi_moves(a["id"], c["d2"], a["t_cs"], a["t_ce"])
    pts = c["d3"]
    t_on = a["t_onblock"]
    L += taxi_moves(a["id"], pts, a["t_ce"], t_on)
    L += hold_moves(a["id"], pts[-1], bearing_deg(*pts[-2], *pts[-1]), t_on, t_on + 30.0)
    L.append((t_on + 32.0, f"DEL {a['id']}"))
    return L


def build_dep_lines(d):
    """Lenh cho 1 chuyen di: CRE tai ben -> lan ra -> diem cho -> len CHC ->
    chay da 35R -> SID."""
    L = []
    gate = GATE26 if d["gate"] == "G26" else GATE27
    path = TAXI_COMMON_G26 if d["gate"] == "G26" else TAXI_COMMON_G27
    t0 = d["start_taxi"]

    L.append((t0, f"CRE {d['id']},{d['type']},{gate[0]:.6f},{gate[1]:.6f},{gate[2]},0,0"))
    L.append((t0, f"# {d['id']} {d['type']} ({wake(d['type'])}) -- xuat phat {d['gate']}, "
                  f"SID {d['sid']}; vao hang cho {fmt(d['t_xep_hang'])}"
                  f"{' (vi tri thu hai)' if d['hang2'] else ''}, toi diem cho {fmt(d['t_prehold'])}, "
                  f"len CHC {fmt(d['lineup'])}, chay da {fmt(d['roll'])}"))
    L.append((t0, f"TAXIOFF {d['id']}"))

    # 1) Lan tu ben ra diem cho truoc nguong 35R; neu tau truoc con dung tai
    #    PREHOLD thi dung o vi tri thu hai phia sau roi tien len khi tau truoc
    #    len duong CHC (xep hang, muc 6 prompt).
    # 2) Cho tai diem cho den khi duoc phep len duong CHC
    doan = d["_doan"]
    for k, (pts, a, b) in enumerate(doan):
        L += taxi_moves(d["id"], pts, a, b)
        cuoi = k == len(doan) - 1
        L += hold_moves(d["id"], pts[-1], PREHOLD[2] if cuoi else bearing_deg(*pts[-2], *pts[-1]),
                        b, d["lineup"] if cuoi else doan[k + 1][1])
    # 3) Len duong CHC 35R roi GHIM tai cho den khi duoc phep chay da.
    #    Khong duoc trai quang duong ngan nay (~130 m) ra suot thoi gian cho:
    #    lam vay toc do MOVE tut xuong 1.7 kt va BlueSky khong giu noi tau o
    #    toc do do -- da do duoc tau dao dong qua lai 294 m moi giay (577 kt).
    #    Lan dung toc do lan khi re roi dung han, giong dieu hanh that.
    lineup_pts = [(path[-1][0], path[-1][1]), (RWYHOLD[0], RWYHOLD[1]), LINEUP_35R]
    dai = sum(haversine_m(*lineup_pts[k], *lineup_pts[k + 1]) for k in range(len(lineup_pts) - 1))
    t_xong = min(d["roll"], d["lineup"] + dai / (TAXI_SPD_TURN * 0.514444))
    L += taxi_moves(d["id"], lineup_pts, d["lineup"], t_xong)
    L += hold_moves(d["id"], LINEUP_35R, RWYHOLD[2], t_xong, d["roll"])
    # 4) Chay da theo SID that.
    #    Chen them MOT diem ROI DAT nam TRONG pham vi duong CHC truoc chuoi
    #    SID: moi chuoi SID cua VVDN deu bat dau tai (16.076637,108.195656)
    #    alt 1500 ft -- cach nguong 35R 5343 m, tuc NGOAI duong CHC (dai
    #    3517 m) 1826 m. Neu khong chen, VNAV trai doan leo deu toi diem do
    #    va giu tau o cao do 0 ft suot ca doan -- da do duoc tau bay "truot
    #    tren mat dat" o 180 kt ra ngoai dau bac duong CHC 1428 m roi moi
    #    bat dau leo. Diem chen dat tai cu ly chay da thuc te theo nhom
    #    nhieu dong xoay, cao do 35 ft (screen height tieu chuan ICAO).
    L.append((d["roll"], f"{d['id']} DELRTE"))
    lift = _diem_tren_tim_35R(TOR_HEAVY_M if wake(d["type"]) == "HEAVY" else TOR_MEDIUM_M)
    L.append((d["roll"], f"{d['id']} ADDWPT {lift[0]:.6f},{lift[1]:.6f} "
                         f"{LIFTOFF_ALT_FT:.0f} {SID_CHAINS[d['sid']][0][3]}"))
    for (la, lo, al, sp) in SID_CHAINS[d["sid"]]:
        L.append((d["roll"], f"{d['id']} ADDWPT {la:.6f},{lo:.6f} {al} {sp}"))
    L.append((d["roll"], f"{d['id']} LNAV ON"))
    L.append((d["roll"], f"{d['id']} VNAV ON"))
    L.append((d["roll"], f"{d['id']} SPD {SID_CHAINS[d['sid']][0][3]}"))
    L.append((d["roll"] + DEP_KEEP_S, f"DEL {d['id']}"))
    return L


def header(arrs, deps, quota):
    dva = {f"{d[0]} {a[0]}": v for d, row in R_DEP_VS_ARR.items() for a, v in row.items()
           if d in ("HEAVY", "MEDIUM") and a in ("HEAVY", "MEDIUM")}
    dva_txt = (f"{next(iter(dva.values())):g} NM moi cap loai tau" if len(set(dva.values())) == 1
               else ", ".join(f"{k}={v:g}" for k, v in dva.items()))
    return "\n".join([
        "# =========================================================================",
        "# VVDN -- KICH BAN CAT CANH XEN KE, 60 PHUT, HUONG 35",
        "# 35L ha canh (ILS) / 35R cat canh -- hai duong CHC song song PHU THUOC",
        "# =========================================================================",
        f"# Sinh boi: _gen_vvdn_xenke_60min.py   SEED = {SEED} (tai lap duoc 100%)",
        f"# Quy tac phan cach + tham so lan: vvdn_xenke_rules.json",
        f"# Du lieu SID/STAR/so do san bay: _gen_kb5_1hour.py (kich ban 40 chuyen",
        f"#   tai VVDN da kiem chung) -- trich tu AIP RNAV RWY35L/R that.",
        "#",
        f"# Quy mo: {len(arrs)} chuyen den + {len(deps)} chuyen di = {len(arrs)+len(deps)} lan chuyen",
        f"# Co cau: DEN {quota[0]} MEDIUM + {quota[1]} HEAVY | DI {quota[2]} MEDIUM + {quota[3]} HEAVY",
        f"#   (han ngach CHINH XAC 70/30 roi xao tron bang seed, khong boc ngau nhien tung chuyen)",
        "#",
        "# THIET KE: MOT pha duy nhat suot 60 phut, KHONG co nhip muc tieu. Moi moc",
        "#   dat som nhat ma van thoa moi phan cach toi thieu -> so chuyen thu duoc",
        f"#   ({len(arrs)} den + {len(deps)} di) CHINH LA nang luc toi da cua cau hinh.",
        "#",
        "# PHAN CACH AP DUNG -- du thao Phuong thuc 2 CHC song song Da Nang (24.7.2026),",
        "#   du thao MANOP APP/TWR Da Nang va ICAO Doc 4444 (chi tiet + dieu khoan:",
        "#   vvdn_xenke_rules.json). 35L/35R cach nhau 214 m (< 760 m) -> nhieu dong",
        "#   ap dung nhu mot duong CHC.",
        f"#   Cat canh 35R vs tau den ke tiep tren 35L (du thao/MANOP muc 4.2.1, co giam",
        f"#     sat ATS; hang = tau cat canh, cot = tau ha canh): {dva_txt}",
        f"#   Huan lenh cat canh chi sau khi tau den da cham cang; chay da {TOUCHDOWN_TO_ROLL_S}s sau cham cang",
        f"#   Ha canh lien tiep 35L (NM, MANOP = ICAO 8.7.3.4): H sau H={R_ARR['HEAVY_sau_HEAVY']:g}, "
        f"M sau H={R_ARR['MEDIUM_sau_HEAVY']:g}, M sau M={R_ARR['MEDIUM_sau_MEDIUM']:g}, "
        f"H sau M={R_ARR['HEAVY_sau_MEDIUM']:g}; toi thieu {_R_ARR_CFG['radar_toi_thieu']:g} NM",
        (f"#     va gian cach toi thieu {ARR_MIN_SPACING_NM:g} NM" if ARR_MIN_SPACING_NM else
         "#     KHONG ap dung gian cach 8 NM cua MANOP (nguoi dung chi dinh 2026-11-04)"),
        f"#   Tau ha canh truoc phai cat qua het 35R truoc khi tau sau toi {LAND_CLR_NM:g} NM",
        f"#   Cat canh lien tiep 35R (giay): M sau H={R_DEP['MEDIUM_sau_HEAVY']} (MANOP), "
        f"H sau H={R_DEP['HEAVY_sau_HEAVY']}, M sau M={R_DEP['MEDIUM_sau_MEDIUM']}, "
        f"H sau M={R_DEP['HEAVY_sau_MEDIUM']}; cung duong bay "
        f"{R_DEP_SID['cung_duong_bay_giay']}s / phan ky {R_DEP_SID['phan_ky_giay']}s (prompt)",
        f"#   Cat qua 35R: dung cho giua hai CHC truoc vach 35R; chi cat khi tau cat canh",
        f"#     da qua diem cat; cat xong trong {CROSS_MAX_S}s (MANOP)",
        "#   Duong lan E: tau code D/E/F cat canh 35R -> chi tau code C tren duong lan E (MANOP)",
        f"#   Gioi han diem cho truoc 35R: toi da {MAX_AT_HOLD} tau",
        "#",
        "# GIA DINH / DON GIAN HOA CO CHU DICH:",
        "#   1. Khong gio, khong nhieu dong -- GS = TAS. Thoi tiet tot, CHC kho.",
        "#   2. Pha LAN (ca ra va vao) dieu khien bang MOVE theo nhip thoi gian deu",
        f"#      {MOVE_DT:.0f}s, KHONG dung LNAV/VNAV. Ly do: kiem soat chinh xac thoi",
        "#      diem toi/roi diem cho de so lieu kiem chung co y nghia, va tranh hai",
        "#      loi da ghi nhan cua BlueSky (selspd=-999 lam tau dung yen vinh vien;",
        "#      khoang trong giua 2 lenh MOVE lam tau 'bay tu do' toi 1138 kt).",
        "#   3. Tau DEN duoc tao tren STAR o cu ly du de kip nhip; chuyen nao can",
        "#      cham banh som thi tao tai diem cat tren STAR (bo doan IAF xa) thay vi",
        "#      tao truoc T=0.",
        f"#   4. Tau DI bi xoa {DEP_KEEP_S:.0f}s sau khi bat dau chay da (da ra khoi khu",
        "#      vuc TMA gan, khong con anh huong den phan cach tai san bay).",
        "#   5. Tau DEN ve ben 28 (thoat ly G4) hoac ben 8 (thoat ly G6); tau DI xuat",
        "#      phat tu ben 26/27 -- deu bam tim duong lan that (lech TB 0.3-3.8 m).",
        "#   6. Tau DEN thoat ly 35L ra G4/G6 (giua hai CHC) roi CAT QUA 35R ve ben:",
        "#      dung cho truoc vach 35R neu tau cat canh chua qua diem cat.",
        "# =========================================================================",
        "",
        "00:00:00.000>DTMULT 1",
        f"00:00:00.000>ASAS OFF",
        "",
    ])


def main():
    # So chuyen KHONG dat truoc: lich chay den het 60 phut roi dung lai, nen
    # so chuyen thuc te la KET QUA cua phan cach chu khong phai dau vao. Nhung
    # han ngach 70/30 lai can biet truoc so chuyen -> lap den khi on dinh.
    # Dong thoi chuyen di dau tien phai du thoi gian lan ra TRUOC T=0, neu
    # khong thi lich cua no bi am -> doi moc cham banh cua chuyen den dau tien.
    # Neu mot chuyen di KHONG co gio roi ben nao hop le (va cham khi lan /
    # duong lan E / diem cho day), lui gio CAT CANH cua no 15 s roi lap lai ca
    # lich -- tat ca chuyen sau tu dich theo. Dung la cach dieu hanh that.
    tre_them: dict = {}
    IAF_DEM_S = 10.0

    def can_som_nhat(arrs, deps):
        """Bao nhieu giay co the KEO SOM toan bo lich ma moi chuyen den van tao
        duoc tai IAF (dem IAF_DEM_S) va moi chuyen di van bat dau lan sau T=0."""
        du_iaf = min(a["td"] - (_STAR_TRANSIT[a["star"]] + cadas_to_thr_s(a["type"])
                                + max(CALIB.get(a["id"], 0.0), 0.0) + IAF_DEM_S) for a in arrs)
        return min(du_iaf, min(d["start_taxi"] for d in deps) - 5.0)

    def lap_lich(first_td, n_arr, n_dep):
        for _vong in range(120):
            ft, na, nd = first_td, n_arr, n_dep
            for _ in range(40):
                arrs, deps, quota = schedule(random.Random(SEED), ft, na, nd, tre_them)
                # PHA KHOI DONG (muc 5 prompt): moi chuyen den phai duoc tao TAI
                # IAF cua STAR. Lui moc cham banh dau tien den khi chuyen nao
                # cung du thoi gian bay tu IAF (tinh ca bu hieu chuan neu duong).
                thieu = max(_STAR_TRANSIT[a["star"]] + cadas_to_thr_s(a["type"])
                            + max(CALIB.get(a["id"], 0.0), 0.0) + IAF_DEM_S - a["td"] for a in arrs)
                if thieu > 0:
                    ft += thieu
                    continue
                deps = schedule_taxi_out(deps)
                deps, nk = nhuong_duong_khi_lan(arrs, deps)
                earliest = min(d["start_taxi"] for d in deps)
                if earliest < 0:
                    ft += -earliest + 10.0
                    continue
                if (len(arrs), len(deps)) == (na, nd):
                    break
                na, nd = len(arrs), len(deps)
            else:
                raise SystemExit("Khong hoi tu duoc so chuyen / lich lan ra")
            loi = [d for d in deps if d.get("khong_xep_duoc")]
            if not loi:
                return arrs, deps, quota, ft, nk, earliest
            k = loi[0]["i"] - 1
            tre_them[k] = tre_them.get(k, 0.0) + 15.0
        raise SystemExit(f"Khong xep duoc lich lan ra sau 120 vong (lui them: {tre_them})")

    arrs, deps, quota, first_td, nhat_ky_nhuong, earliest = lap_lich(FIRST_ARR_TD, 40, 40)
    # Moc cham banh dau tien chi tang dan trong luc tim so chuyen, nen thuong
    # bi day qua tay (ban truoc: 7 phut 38 giay dau kich ban KHONG co tau nao --
    # nguoi dung tuong kich ban khong chay). Keo som toan bo lich toi muc toi
    # thieu: moi moc dich cung mot luong nen lich tuong doi giua cac chuyen
    # khong doi.
    for _ in range(5):
        som = can_som_nhat(arrs, deps)
        if som <= 1.0:
            break
        arrs, deps, quota, first_td, nhat_ky_nhuong, earliest = lap_lich(
            first_td - som, len(arrs), len(deps))
    if tre_them:
        print("Lui gio cat canh de co gio lan ra hop le: "
              + ", ".join(f"DEP{k+1:03d} +{v:.0f}s" for k, v in sorted(tre_them.items())))
    print(f"Chuyen den dau tien cham banh luc {fmt(first_td)} "
          f"(de chuyen di dau tien kip lan ra tu ben, som nhat {fmt(earliest)})")
    if nhat_ky_nhuong:
        print(f"Nhuong duong khi lan: {len(nhat_ky_nhuong)} lan dieu chinh")
        for d in nhat_ky_nhuong[:6]:
            print(f"   {d}")
        con = cap_vi_pham_mat_dat(quy_dao_lan(arrs, deps))
        print(f"   -> con lai {len(con)} cap vi pham"
              + (f": {con[0]['a']}<->{con[0]['b']} {con[0]['d']:.0f}m" if con else ""))
    else:
        print("Nhuong duong khi lan: khong co xung dot nao can giai")

    L = []
    for a in arrs:
        L += build_arr_lines(a)
    for d in deps:
        L += build_dep_lines(d)

    L.sort(key=lambda x: (x[0], 0 if x[1].startswith("CRE") else 1))
    body = "\n".join(f"{fmt(t)}>{c}" if not c.startswith("#") else c for (t, c) in L)

    if OUT_FILE.exists():
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        bd = BACKUP_DIR / f"VVDN-xenke {ts}"
        bd.mkdir(parents=True, exist_ok=True)
        shutil.copy(OUT_FILE, bd / OUT_FILE.name)
        print(f"Da backup ban cu vao Backup/{bd.name}/{OUT_FILE.name}")

    OUT_FILE.write_text(header(arrs, deps, quota) + body + "\n", encoding="utf-8")

    meta = {
        "seed": SEED,
        "arrivals": [{k: v for k, v in a.items()} for a in arrs],
        "departures": [{k: v for k, v in d.items() if not k.startswith("_")} for d in deps],
    }
    (HERE / "VVDN-XENKE-60MIN.plan.json").write_text(
        json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")

    n_cmd = sum(1 for _, c in L if not c.startswith("#"))
    print(f"Da ghi {OUT_FILE.name}: {len(arrs)} ARR + {len(deps)} DEP, {n_cmd} lenh")
    print(f"Da ghi VVDN-XENKE-60MIN.plan.json (lich chi tiet cho script kiem chung)")
    print(f"  Nang luc toi da trong 60 phut: {len(arrs)} den + {len(deps)} di "
          f"= {len(arrs) + len(deps)} chuyen dong")


if __name__ == "__main__":
    main()
