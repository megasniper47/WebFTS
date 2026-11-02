"""
VVDN-XENKE-60MIN.scn -- Kich ban cat canh/ha canh XEN KE tai VVDN, 60 phut.

Sinh theo prompt "kich ban cat canh xen ke (Linh).docx": khai thac huong 35,
hai duong CHC song song PHU THUOC (35L ha canh ILS, 35R cat canh), 3 pha mat
do tang dan de xac dinh NANG LUC DIEU HANH BAY toi da ma moi phan cach van
dat, va mat do bat dau phat sinh vi pham.

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
HOLD_MARGIN_S = 10.0 # dem an toan truoc khi chuoi MOVE lan vao ben tiep quan
LINEUP_35R = (16.030000, 108.202000)   # vi tri bat dau chay da tren 35R
                                       # (_KB5GEN_DEP_ENTER_RWY.scn, kich ban 40 chuyen)

THR35L = (16.030133, 108.200372)
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
           (16.057199, 108.196412, 10), (16.057250, 108.196800, 8), (16.057200, 108.197400, 12)],
}

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

PHASES = [RULES["thiet_ke_pha"][k] for k in ("pha_1", "pha_2", "pha_3")]


def wake(ac_type):
    return "HEAVY" if ac_type in HEAVY_TYPES else "MEDIUM"


def arr_sep_nm(lead_type, trail_type):
    """Phan cach ha canh lien tiep 35L (NM) theo cap nhieu dong xoay."""
    key = f"{wake(trail_type)}_sau_{wake(lead_type)}"
    return max(R_ARR.get(key, R_ARR["MEDIUM_sau_MEDIUM"]), RULES["phan_cach_ha_canh_lien_tiep_35L"]["radar_toi_thieu"])


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
        return p, n_m, n_h
    arr, am, ah = pool(n_arr)
    dep, dm, dh = pool(n_dep)
    return arr, dep, (am, ah, dm, dh)


def phase_of(t):
    for i, ph in enumerate(PHASES):
        if ph["tu_phut"] * 60 <= t < ph["den_phut"] * 60:
            return i
    return len(PHASES) - 1


def schedule(rng, first_td=FIRST_ARR_TD, n_arr=40, n_dep=40):
    """Lap lich XEN KE: lan luot 1 chuyen den -> 1 chuyen di -> 1 chuyen den...

    Moi moc deu phai thoa DONG THOI moi phan cach toi thieu. Nhip muc tieu tung
    pha chi la CAN TREN (mong muon); khi phan cach doi hoi lon hon thi lich TU
    GIAN RA -- nhip thuc te thu duoc CHINH LA nang luc dieu hanh bay toi da cua
    cau hinh khai thac nay.

    LUU Y NGHIEP VU quan trong (da kiem chung bang script kiem chung doc lap):
    ma tran "cat canh 35R khi co tau dang tiep can 35L" (5-7 NM) CHAT HON phan
    cach hai tau ha canh lien tiep (3-5 NM). Hau qua: KHONG the giu dong thoi
    nhip den day VA chen duoc chuyen di giua hai chuyen den. Vi "cat canh xen
    ke" la yeu cau cung cua kich ban, thuat toan nay UU TIEN XEN KE va day
    chuyen den ke tiep ra xa de tao khe cat canh -- dung nhu cach dieu hanh
    that. Vi vay nhip den thuc te luon thap hon muc tieu pha o mat do cao, va
    do chinh la ket qua can tim cua kich ban.
    """
    arr_types, dep_types, quota = build_fleet(n_arr, n_dep, rng)
    arr_stars = [rng.choice(list(STAR_IAF)) for _ in range(n_arr)]
    dep_sids = [rng.choice(SID_NAMES) for _ in range(n_dep)]
    arr_exits = [rng.choice(["G4", "G6"]) for _ in range(n_arr)]
    dep_gates = [rng.choice(["G26", "G27"]) for _ in range(n_dep)]

    def target_gap(t):
        """Khoang cach MONG MUON giua hai chuyen den lien tiep theo pha."""
        return 3600.0 / PHASES[phase_of(t)]["muc_tieu_chuyen_dong_gio"] * 2.0

    arrs, deps = [], []
    i = j = 0
    while i < n_arr and j < n_dep:
        # ---- chuyen den thu i ----
        if not arrs:
            t_arr = first_td
        else:
            lead = arrs[-1]
            t_arr = max(
                lead["td"] + target_gap(lead["td"]),                       # nhip mong muon
                lead["td"] + arr_sep_nm(lead["type"], arr_types[i])        # phan cach nhieu dong
                / approach_speeds(arr_types[i])[2] * 3600.0,
                lead["td"] + occupancy_s(lead["exit"],                     # giai phong duong CHC
                                         approach_speeds(lead["type"])[3]),
            )
        if deps:                       # du cu ly voi chuyen di vua cat canh
            need = dep_vs_arr_nm(deps[-1]["type"], arr_types[i])
            t_arr = max(t_arr, deps[-1]["roll"]
                        + need / approach_speeds(arr_types[i])[2] * 3600.0)
        if t_arr >= DURATION_S:
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
        if t_roll >= DURATION_S:
            break
        deps.append({"i": j + 1, "id": f"DEP{j+1:03d}", "type": dep_types[j],
                     "sid": dep_sids[j], "gate": dep_gates[j], "roll": t_roll})
        j += 1

    return arrs, deps, quota


def schedule_taxi_out(deps):
    """Lap lich lan ra: tinh nguoc tu thoi diem len duong CHC, roi lui thoi
    diem bat dau lan neu so tau tai diem cho vuot MAX_AT_HOLD."""
    for j, d in enumerate(deps):
        path = TAXI_COMMON_G26 if d["gate"] == "G26" else TAXI_COMMON_G27
        d["taxi_s"] = taxi_time_s(path)
        # Tau sau duoc LEN duong CHC khi tau truoc BAT DAU CHAY DA (muc 3e)
        d["lineup"] = deps[j - 1]["roll"] if j > 0 else d["roll"] - 60.0
        d["lineup"] = min(d["lineup"], d["roll"])
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
    t_hold = a["td"] + occupancy_s(a["exit"], approach_speeds(actype)[3]) + HOLD_MARGIN_S
    a["t_vacated"] = t_hold
    L.append((t_hold, f"{a['id']} LNAV OFF"))
    L.append((t_hold, f"{a['id']} VNAV OFF"))

    # Lan vao ben. Lay HINH TUYEN tu file _ARR_RESUME_* (bam tim duong lan
    # that) nhung PHAT LAI theo nhip thoi gian deu MOVE_DT, khong chep nguyen
    # nhip cu: file goc cua kich ban 40 chuyen co cho gian toi 3.5s va lenh ap
    # chot van dat 5 kt -- da do duoc tau bay tu do 674 m trong khoang trong do
    # (hien thanh 1019 kt). Lenh cuoi dat 0 kt roi ghim them vai lan tai ben
    # (da kiem chung: sau lenh MOVE 0 kt tau dung yen tuyet doi).
    seq = load_move_seq(ARR_TAXI_FILES[a["exit"]])
    pts = []
    for (_dt, cmd) in seq:
        if not cmd.startswith("MOVE"):
            continue
        f = cmd.split("MOVE %0,")[1].split(",")
        pts.append((float(f[0]), float(f[1])))
    dur = seq[-1][0] - seq[0][0]
    t_on = t_hold + dur
    L += taxi_moves(a["id"], pts, t_hold, t_on)
    L += hold_moves(a["id"], pts[-1], bearing_deg(*pts[-2], *pts[-1]), t_on, t_on + 30.0)
    a["t_onblock"] = t_on
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
                  f"SID {d['sid']}; toi diem cho {fmt(t0 + d['taxi_s'])}, "
                  f"len CHC {fmt(d['lineup'])}, chay da {fmt(d['roll'])}"))
    L.append((t0, f"TAXIOFF {d['id']}"))

    # 1) Day lui + lan tu ben ra diem cho truoc nguong 35R
    t_hold = t0 + d["taxi_s"]
    L += taxi_moves(d["id"], [(gate[0], gate[1])] + [(p[0], p[1]) for p in path], t0, t_hold)
    # 2) Cho tai diem cho den khi duoc phep len duong CHC
    L += hold_moves(d["id"], (path[-1][0], path[-1][1]), PREHOLD[2], t_hold, d["lineup"])
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
    # 4) Chay da theo SID that
    L.append((d["roll"], f"{d['id']} DELRTE"))
    for (la, lo, al, sp) in SID_CHAINS[d["sid"]]:
        L.append((d["roll"], f"{d['id']} ADDWPT {la:.6f},{lo:.6f} {al} {sp}"))
    L.append((d["roll"], f"{d['id']} LNAV ON"))
    L.append((d["roll"], f"{d['id']} VNAV ON"))
    L.append((d["roll"], f"{d['id']} SPD {SID_CHAINS[d['sid']][0][3]}"))
    L.append((d["roll"] + DEP_KEEP_S, f"DEL {d['id']}"))
    return L


def header(arrs, deps, quota):
    R = RULES
    rows = []
    for i, ph in enumerate(PHASES):
        t0, t1 = ph["tu_phut"] * 60, ph["den_phut"] * 60
        na = sum(1 for a in arrs if t0 <= a["td"] < t1)
        nd = sum(1 for d in deps if t0 <= d["roll"] < t1)
        rows.append(f"#   Pha {i+1} ({ph['tu_phut']:>2d}-{ph['den_phut']:>2d} phut): "
                    f"muc tieu {ph['muc_tieu_chuyen_dong_gio']} chuyen dong/h -> "
                    f"dat {na} den + {nd} di = {(na+nd)*3} chuyen dong/h")
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
        "# THIET KE 3 PHA MAT DO TANG DAN:",
        *rows,
        "#   Nhip muc tieu chi la MONG MUON. Phan cach toi thieu luon duoc uu tien:",
        "#   neu phan cach doi hoi lon hon nhip muc tieu thi lich bi gian ra va thong",
        "#   luong thuc te thap hon muc tieu -- do CHINH LA nang luc that cua cau hinh.",
        "#",
        "# PHAN CACH AP DUNG (chi tiet + dieu khoan nguon: vvdn_xenke_rules.json):",
        f"#   Ha canh lien tiep 35L (NM): H sau H={R_ARR['HEAVY_sau_HEAVY']}, "
        f"M sau H={R_ARR['MEDIUM_sau_HEAVY']}, M sau M={R_ARR['MEDIUM_sau_MEDIUM']}, "
        f"H sau M={R_ARR['HEAVY_sau_MEDIUM']}  [CAN XAC NHAN]",
        f"#   Cat canh lien tiep 35R (giay): M sau H={R_DEP['MEDIUM_sau_HEAVY']}, "
        f"H sau H={R_DEP['HEAVY_sau_HEAVY']}, M sau M={R_DEP['MEDIUM_sau_MEDIUM']}, "
        f"H sau M={R_DEP['HEAVY_sau_MEDIUM']}; cung duong bay "
        f"{R_DEP_SID['cung_duong_bay_giay']}s / phan ky {R_DEP_SID['phan_ky_giay']}s  [CAN XAC NHAN]",
        f"#   Cat canh 35R vs tau den 35L (NM): M sau H=7, M sau M=5, H sau H=6, H sau M=7",
        f"#   Cham cang -> cap huan lenh chay da: {TOUCHDOWN_TO_ROLL_S}s",
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
        "#   6. Chua mo phong cat qua duong CHC 35R: ca hai tuyen lan vao ben (28 va 8)",
        "#      deu nam cung phia tay voi duong lan thoat ly, khong phai cat qua 35R.",
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
    first_td = FIRST_ARR_TD
    n_arr = n_dep = 40
    for _ in range(12):
        arrs, deps, quota = schedule(random.Random(SEED), first_td, n_arr, n_dep)
        deps = schedule_taxi_out(deps)
        earliest = min(d["start_taxi"] for d in deps)
        if earliest < 0:
            first_td += -earliest + 10.0
            continue
        if (len(arrs), len(deps)) == (n_arr, n_dep):
            break
        n_arr, n_dep = len(arrs), len(deps)
    else:
        raise SystemExit("Khong hoi tu duoc so chuyen / lich lan ra")
    print(f"Chuyen den dau tien cham banh luc {fmt(first_td)} "
          f"(de chuyen di dau tien kip lan ra tu ben, som nhat {fmt(earliest)})")

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
        "departures": [{k: v for k, v in d.items()} for d in deps],
    }
    (HERE / "VVDN-XENKE-60MIN.plan.json").write_text(
        json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")

    n_cmd = sum(1 for _, c in L if not c.startswith("#"))
    print(f"Da ghi {OUT_FILE.name}: {len(arrs)} ARR + {len(deps)} DEP, {n_cmd} lenh")
    print(f"Da ghi VVDN-XENKE-60MIN.plan.json (lich chi tiet cho script kiem chung)")
    for i, ph in enumerate(PHASES):
        t0, t1 = ph["tu_phut"] * 60, ph["den_phut"] * 60
        na = sum(1 for a in arrs if t0 <= a["td"] < t1)
        nd = sum(1 for d in deps if t0 <= d["roll"] < t1)
        print(f"  Pha {i+1}: muc tieu {ph['muc_tieu_chuyen_dong_gio']}/h -> "
              f"dat {na}+{nd}={(na+nd)*3} chuyen dong/h")


if __name__ == "__main__":
    main()
