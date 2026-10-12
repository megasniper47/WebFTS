"""
vvdn_minsep_pairs_from_doten.scn

Kich ban 2 tau bay ha canh lien tiep VVDN RWY35L, dung dung khoang cach toi
thieu tinh trong VVDN_KhoangCachToiThieu_TiepCanLienTiep.docx (bai toan
nguoc tu VVDN_KB5_1HOUR_MIXED.scn). Ban nay BO SUNG:

1. NHIEU LOAI TAU BAY THAT, TY LE HEAVY ~30%: 12 loai tau bay that da dung
   trong VVDN_KB5_1HOUR_MIXED.scn (E190 KHONG dung nua vi Viet Nam khong
   con khai thac loai nay) -- toc do IAS tai tung moc (DOTEN, TRACO, CADAS,
   MONRY, TAMLA, KALET, diem trung gian, DN351, nguong) lay NGUYEN VAN tu
   chinh cac file _KB5GEN_ARR_APPROACH_ARRxxx.scn cua loai tau bay tuong
   ung -- khong bia. Ty le tau bay hang HEAVY trong toan bo kich ban chi
   ~30% (phan con lai la MEDIUM) de phan anh dung co cau doi bay thuc te,
   khong phai 50/50.

2. THOAT LY NGAU NHIEN G4/G6 + LAN VAO BEN DO THAT: sau khi cham banh, moi
   tau bay NGAU NHIEN (seed co dinh de tai lap duoc) chon thoat ly qua G4
   hoac G6 (dung profile giam toc that _KB5GEN_ARR_EXIT_G4/G6.scn), roi
   lan vao ben do THAT:
     G4 -> lan vao GATE 28 theo toa do re thuc te
     G6 -> lan vao SAN DO SO 11
   Chuoi MOVE thu cong (khong phai LNAV/VNAV) cho 2 duong lan nay duoc doc
   1 LAN tu 2 file du lieu nguon co san trong du an (_ARR_RESUME_G4_GATE28.scn,
   _ARR_RESUME_G6_GATE11.scn, xem load_move_sequence()) roi NHOI TRUC TIEP
   (voi moc thoi gian tuyet doi tinh san tu occupancy_time_sec) vao thang
   trong file .scn dau ra -- KHONG con dung PCALL/ATDIST toi cac file rieng
   nua, de kich ban tao ra CHI CON DUY NHAT 1 file .scn, khong con nhieu
   file _KB5GEN_*/_ARR_RESUME_* lam nguoi dung roi khi mo trinh chay
   kich ban.

3. TRUONG HOP THIEU PHAN CACH NHIEU DONG -- TAU BAY SAU VAO VONG CHO: 3
   tinh huong rieng (GA1/GA2/GA3), moi tinh huong 1 cap voi khoang cach ban
   dau CO CHU DICH chi dung 3NM (baseline toi thieu VVDN, KHONG du phan
   cach nhieu dong thuc te cho cap duoc chon). Khac ban truoc: tau bay
   DI TRUOC van ha canh binh thuong (khong bi anh huong); tau bay DI SAU
   (tau dang tiep can gan, phat hien thieu phan cach) moi la tau phai bay
   lai va tien nhap vong cho.

   CA 3 tinh huong deu bay lai vao CUNG 1 vong cho That: Holding KONGA --
   dung theo AIP AD2-VVDN-13-30/32/52 (AMDT 01/23), phuong thuc bay lai
   (missed approach) cua CA ILS U, ILS V, va RNP Z RWY35L deu HOI TU ve
   CUNG 1 duong bay lai: CF DN353 -> TF DN333 -> TF DN555 -> TF KONGA ->
   HM KONGA (giu cho). Khong co "vong cho rieng cho ILS V" -- ban truoc co
   gan LOLUC/TAMLA cho GA2/GA3 la SAI, vi 2 fix do chi la diem tiep can
   (STAR/approach fix) chu khong phai diem giu cho cong bo trong phuong
   thuc bay lai. Toa do vong cho KONGA lay nguyen tu vatm_procedures_
   VVDN.geojson (khong phai hinh hoc xap xi). Sau 1 vong cho, tau bay sau
   bay lai tu DOTEN va ha canh binh thuong.
"""
import math
import random
from pathlib import Path

OUT_FILE = Path("vvdn_minsep_pairs_from_doten.scn")
random.seed(20260818)

# ---------------------------------------------------------------------------
# Real coordinates (WGS-84), from _KB5GEN_ARR_APPROACH_ARRxxx.scn (common
# post-DOTEN tail, shared by all real aircraft types in VVDN_KB5_1HOUR_MIXED)
# and AIP AD2-VVDN-13-52 (RNP Z RWY35L) / AD2-VVDN-13-30/32 (ILS U/V, missed
# approach chain).
# ---------------------------------------------------------------------------
CP = {
    "DOTEN": (15.767222, 108.118333),
    "TRACO": (15.601667, 108.142222),
    "CADAS": (15.618056, 108.262500),
    "MONRY": (15.700556, 108.250000),
    "TAMLA": (15.788333, 108.237500),
    "KALET": (15.865171, 108.224271),
    "NB2":   (15.947115, 108.212410),
    "DN351": (15.957222, 108.210944),
    "THR":   (16.030133, 108.200372),
}
ORDER = ["TRACO", "CADAS", "MONRY", "TAMLA", "KALET", "NB2", "DN351", "THR"]

ALT_FT = {
    "TRACO": 5548, "CADAS": 5181, "MONRY": 4921, "TAMLA": 4429,
    "KALET": 2592, "NB2": 1611, "DN351": 1476, "THR": 0,
}

# Real per-type IAS (kt) at each checkpoint, from the actual scenario files
# (_KB5GEN_ARR_APPROACH_ARRxxx.scn for the aircraft type shown).
SPEED = {
    "A321": {"DOTEN": 250, "TRACO": 230, "CADAS": 205, "MONRY": 190, "TAMLA": 175, "KALET": 165, "NB2": 155, "DN351": 155, "THR": 135},  # ARR001
    "B78X": {"DOTEN": 250, "TRACO": 230, "CADAS": 230, "MONRY": 215, "TAMLA": 195, "KALET": 180, "NB2": 160, "DN351": 160, "THR": 160},  # ARR002
    "B744": {"DOTEN": 250, "TRACO": 230, "CADAS": 225, "MONRY": 210, "TAMLA": 190, "KALET": 175, "NB2": 160, "DN351": 160, "THR": 155},  # ARR003
    "B739": {"DOTEN": 250, "TRACO": 230, "CADAS": 215, "MONRY": 200, "TAMLA": 185, "KALET": 170, "NB2": 155, "DN351": 155, "THR": 145},  # ARR004
    "A333": {"DOTEN": 250, "TRACO": 230, "CADAS": 205, "MONRY": 190, "TAMLA": 175, "KALET": 165, "NB2": 150, "DN351": 150, "THR": 130},  # ARR005
    "A20N": {"DOTEN": 250, "TRACO": 230, "CADAS": 205, "MONRY": 190, "TAMLA": 175, "KALET": 165, "NB2": 150, "DN351": 150, "THR": 130},  # ARR006
    "B772": {"DOTEN": 250, "TRACO": 230, "CADAS": 210, "MONRY": 195, "TAMLA": 180, "KALET": 165, "NB2": 155, "DN351": 155, "THR": 135},  # ARR007
    # E190 bo khoi danh sach: Viet Nam khong con khai thac loai nay.
    "A21N": {"DOTEN": 250, "TRACO": 230, "CADAS": 215, "MONRY": 200, "TAMLA": 185, "KALET": 170, "NB2": 155, "DN351": 155, "THR": 140},  # ARR010
    "A332": {"DOTEN": 250, "TRACO": 230, "CADAS": 210, "MONRY": 195, "TAMLA": 180, "KALET": 165, "NB2": 155, "DN351": 155, "THR": 135},  # ARR012
    "A359": {"DOTEN": 250, "TRACO": 230, "CADAS": 215, "MONRY": 200, "TAMLA": 185, "KALET": 170, "NB2": 155, "DN351": 155, "THR": 145},  # ARR015
    "A320": {"DOTEN": 250, "TRACO": 230, "CADAS": 205, "MONRY": 190, "TAMLA": 175, "KALET": 165, "NB2": 150, "DN351": 150, "THR": 130},  # ARR018
    "B38M": {"DOTEN": 250, "TRACO": 230, "CADAS": 225, "MONRY": 210, "TAMLA": 190, "KALET": 175, "NB2": 160, "DN351": 160, "THR": 160},  # ARR019
}
WAKE_CAT = {
    "A321": "MEDIUM", "B78X": "HEAVY", "B744": "HEAVY", "B739": "MEDIUM",
    "A333": "HEAVY", "A20N": "MEDIUM", "B772": "HEAVY",
    "A21N": "MEDIUM", "A332": "HEAVY", "A359": "HEAVY", "A320": "MEDIUM",
    "B38M": "MEDIUM",
}

# Real touchdown-to-vacate exit chains (G4/G6), verbatim from
# _KB5GEN_ARR_EXIT_G4.scn / _KB5GEN_ARR_EXIT_G6.scn, adapted so the
# aircraft NEVER decelerates to a literal stop before handing off to the
# real gate-taxi MOVE data (STOP_HOLD_THEN_GATE) -- earlier "chain" had a
# genuine SPD 0 waypoint mid-taxi (a hard stop commanded via ADDWPT) then
# re-accelerated past it to a short extra tail point; because t_stop /
# LNAV OFF fired right around that same spot, the aircraft visibly came
# to a full stop exactly at the runway exit before continuing -- exactly
# what the "no stop, roll straight to gate" scenario should NOT do. Fix:
# "chain" now ends at the SAME point as "occ_chain" (no extra tail
# waypoint) and the final speed is a low but NON-ZERO taxi speed matching
# the real MOVE data's own starting speed (STOP_HOLD_THEN_GATE), so the
# LNAV-flown rollout and the MOVE-puppeted gate taxi join at a continuous
# roll instead of a dead stop.
EXIT_CHAINS = {
    "G4": {
        "chain": [
            (16.034580, 108.199721, 122), (16.039028, 108.199071, 102), (16.043475, 108.198420, 75),
            (16.046143, 108.198030, 54), (16.047922, 108.197769, 32), (16.048687, 108.197658, 10),
            (16.048950, 108.198100, 8), (16.048727, 108.197660, 10),
        ],
        "occ_chain": [
            (16.034580, 108.199721, 122), (16.039028, 108.199071, 102), (16.043475, 108.198420, 75),
            (16.046143, 108.198030, 54), (16.047922, 108.197769, 32), (16.048687, 108.197658, 10),
            (16.048950, 108.198100, 8), (16.048727, 108.197660, 10),
        ],
        "dest_label": "gate 28",
    },
    "G6": {
        "chain": [
            (16.034580, 108.199721, 128), (16.039028, 108.199071, 115), (16.043475, 108.198420, 100),
            (16.047922, 108.197769, 83), (16.052370, 108.197119, 61), (16.055927, 108.196598, 34),
            (16.057199, 108.196412, 10), (16.057250, 108.196800, 8), (16.057200, 108.197400, 12),
        ],
        "occ_chain": [
            (16.034580, 108.199721, 128), (16.039028, 108.199071, 115), (16.043475, 108.198420, 100),
            (16.047922, 108.197769, 83), (16.052370, 108.197119, 61), (16.055927, 108.196598, 34),
            (16.057199, 108.196412, 10), (16.057250, 108.196800, 8), (16.057200, 108.197400, 12),
        ],
        "dest_label": "san do so 11",
    },
}

# Real missed-approach chain (identical on ILS U/V and RNP Z RWY35L, AIP
# AD2-VVDN-13-30/32/52, AMDT 01/23): CF DN353 (353M/352.2T) -> TF DN333
# (039M, 9.10km) -> TF DN555 (092M, 21.53km) -> TF KONGA (167M, 34.21km,
# len +1200m) -> HM KONGA (giu cho, vong trai, +1200m).
MISSED_APPROACH = [
    ("DN353", (16.146389, 108.183889), None),
    ("DN333", (16.211111, 108.236389), None),
    ("DN555", (16.209167, 108.437778), None),
    ("KONGA", (15.908611, 108.512500), 3937),  # +1200m
]

# REAL published KONGA holding-pattern geometry, extracted verbatim from
# vatm_procedures_VVDN.geojson (WebATM/static/data/vatm_kmz/procedures_by_airport),
# feature name "Holding KONGA". Closed LineString (67 points, entry fix ->
# outbound curve -> far turn -> inbound curve -> back to the same entry
# fix) -- not an approximation like the earlier rectangular racetrack.
# KONGA is the ONLY published missed-approach hold for VVDN RWY35L: per AIP
# AD2-VVDN-13-30/32/52, ILS U, ILS V, and RNP Z RWY35L all converge onto
# the same missed-approach track (CF DN353 -> TF DN333 -> TF DN555 -> TF
# KONGA -> HM KONGA). An earlier version of this generator wrongly gave
# ILS V go-arounds their own LOLUC/TAMLA holds -- those are approach/STAR
# fixes, not published holding points, and have been removed.
HOLDING_PATTERNS = {
    "KONGA": {
        "entry": (15.908611, 108.512500),
        "coords": [
            (15.908611, 108.512500), (15.917088, 108.583947), (15.917321, 108.587246),
            (15.917239, 108.590553), (15.916845, 108.593835), (15.916140, 108.597062),
            (15.915133, 108.600202), (15.913833, 108.603224), (15.912253, 108.606101),
            (15.910407, 108.608803), (15.908314, 108.611306), (15.905994, 108.613584),
            (15.903469, 108.615616), (15.900763, 108.617383), (15.897902, 108.618867),
            (15.894915, 108.620054), (15.891829, 108.620932), (15.888675, 108.621494),
            (15.885482, 108.621734), (15.882283, 108.621650), (15.879106, 108.621241),
            (15.875984, 108.620513), (15.872946, 108.619472), (15.870021, 108.618129),
            (15.867238, 108.616496), (15.864623, 108.614589), (15.862201, 108.612427),
            (15.859996, 108.610029), (15.858030, 108.607420), (15.856320, 108.604625),
            (15.854884, 108.601670), (15.853735, 108.598583), (15.852884, 108.595396),
            (15.852340, 108.592137), (15.843865, 108.520713), (15.843632, 108.517415),
            (15.843712, 108.514109), (15.844106, 108.510828), (15.844809, 108.507602),
            (15.845814, 108.504463), (15.847113, 108.501440), (15.848692, 108.498564),
            (15.850536, 108.495862), (15.852628, 108.493359), (15.854947, 108.491080),
            (15.857471, 108.489046), (15.860176, 108.487279), (15.863036, 108.485793),
            (15.866022, 108.484604), (15.869108, 108.483723), (15.872261, 108.483159),
            (15.875454, 108.482917), (15.878653, 108.483000), (15.881830, 108.483406),
            (15.884953, 108.484132), (15.887992, 108.485171), (15.890917, 108.486512),
            (15.893701, 108.488144), (15.896318, 108.490049), (15.898740, 108.492211),
            (15.900946, 108.494607), (15.902914, 108.497216), (15.904625, 108.500011),
            (15.906063, 108.502966), (15.907214, 108.506053), (15.908066, 108.509241),
            (15.908611, 108.512500),
        ],
    },
}
HOLD_SPEED_KT = 220
HOLD_ALT_FT = 3937  # +1200m, real KONGA missed-approach climb altitude

DOTEN_SPEED_KT = 250.0  # real, identical for every representative type

# Baseline time between one pair's LEADER and the next pair's LEADER. Kept
# short (5 min) so the scenario is quick to watch/step through. This is only
# a *tentative* schedule though: main() bumps a pair's start later than this
# baseline whenever the previous pair's TRAILER would otherwise be closer to
# the next pair's LEADER than the real wake/ROT-based minimum gap allows
# (both aircraft fly the identical DOTEN corridor, so an unchecked 5-min
# stagger could put unrelated aircraft dangerously close together).
MIN_PAIR_OFFSET_SEC = 300.0

# Safety-net DEL time (seconds after an aircraft's own CRE), independent of
# the next pair's schedule. Each aircraft is designed to self-delete via its
# gate-taxi-in file once it actually reaches its gate/apron; this is only a
# backstop in case that self-delete doesn't fire, so it can be generous.
AIRCRAFT_LIFECYCLE_SEC = 1400.0
# The go-around aircraft is now the TRAILER: full approach to MAPT, short
# climb-out, 1 real hold lap, then a full SECOND approach + exit + gate
# taxi -- roughly 2x a normal aircraft's lifecycle plus the hold lap, so
# give it a generous safety-net window.
GOAROUND_TRAILER_LIFECYCLE_SEC = 2800.0


def dest_point(lat, lon, bearing_deg, dist_nm):
    R = 3440.065
    d = dist_nm / R
    brng = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    lat2 = math.asin(math.sin(lat1) * math.cos(d) + math.cos(lat1) * math.sin(d) * math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d) * math.cos(lat1), math.cos(d) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)


def fmt_time(total_sec):
    if total_sec < 0:
        total_sec = 0
    h = int(total_sec // 3600)
    m = int((total_sec % 3600) // 60)
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def parse_time(ts):
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def load_move_sequence(filename):
    """Doc 1 file MOVE/DEL nguon (vi du _ARR_RESUME_G4_GATE28.scn) va tra
    ve list (offset_sec, command_suffix_voi_%0) -- dung LAM DU LIEU de
    generator NHOI TRUC TIEP vao file .scn dau ra (thay vi de kich ban
    dau ra tu PCALL 1 file rieng). Muc dich: kich ban tao ra chi con
    DUY NHAT 1 file .scn, khong con nhieu file _KB5GEN_*/_ARR_RESUME_*
    lam nguoi dung roi vao khi mo trinh chay kich ban.

    Da THU dung ATDIST + 1 dong 'DELAY <giay> <lenh>; ...' noi het toan bo
    chuoi nay (tu dieu chinh chinh xac theo khoang cach THAT, khong can
    uoc luong thoi gian) nhung PHAT HIEN BlueSky khong kich hoat dung khi
    1 dong ATDIST co qua nhieu doan noi bang ';' (~40 doan tro len la hong,
    ~25 tro xuong thi on voi 1 tau, nhung khi CO NHIEU TAU cung luc dang
    cho dieu kien kich hoat (moi tau tu luc CRE den luc cham banh, ~10+
    phut) thi du moi tau chi ~20 doan cung hong luon -- co ve la GIOI HAN
    TONG so doan tren TOAN BO cac dieu kien dang cho, khong phai rieng
    tung dong) -- gay may bay bien mat rat som, truoc ca khi cham banh.
    Vi kich ban nay co toi 22 tau bay dang cho dieu kien cung luc, ky
    thuat ATDIST+DELAY gop khong an toan. Quay lai dung MOC THOI GIAN
    TUYET DOI tinh truoc (touchdown + occupancy_time_sec, da sua cho
    khop chinh xac diem dung That -- xem chu thich o EXIT_CHAINS)."""
    lines = (Path(__file__).parent / filename).read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or ">" not in line:
            continue
        ts, rest = line.split(">", 1)
        out.append((parse_time(ts), rest))
    return out


# Chuoi MOVE lan vao gate That (doc tu 2 file du lieu nguon, nhoi thang
# vao kich ban dau ra -- khong PCALL nua). Diem bat dau cua moi chuoi da
# duoc xac nhan khop voi diem cuoi cua occ_chain (EXIT_CHAINS) o tren.
STOP_HOLD_THEN_GATE = {
    "G4": {"sequence": load_move_sequence("_ARR_RESUME_G4_GATE28.scn")},
    "G6": {"sequence": load_move_sequence("_ARR_RESUME_G6_GATE11.scn")},
}


def inline_stop_then_gate_lines(callsign, exit_choice, t_stop_sec, dest_label):
    """Kich ban kiem tra ha canh: khong can dung han lai tai diem thoat ly
    nua, chuyen thang tu VNAV/LNAV (dang giam toc theo profile that) sang
    lan vao ben do/gate That -- LNAV/VNAV OFF roi noi NGAY vao chuoi MOVE
    lan vao gate (khong con buoc "dung + doi 3s" nhu truoc). Tat ca la MOC
    THOI GIAN TUYET DOI tinh san (touchdown + occupancy_time_sec), nhoi
    thang vao file .scn dau ra -- khong con PCALL toi file rieng nua."""
    stop = STOP_HOLD_THEN_GATE[exit_choice]
    lines = [
        f"{fmt_time(t_stop_sec)}>{callsign} LNAV OFF",
        f"{fmt_time(t_stop_sec)}>{callsign} VNAV OFF"
        f"  # thoat ly {exit_choice}, lan thang vao {dest_label} (thuc te)",
    ]
    for offset_sec, rest in stop["sequence"]:
        rest = rest.replace("%0", callsign)
        lines.append(f"{fmt_time(t_stop_sec + offset_sec)}>{rest}")
    return lines


def haversine_nm(lat1, lon1, lat2, lon2):
    R = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def occupancy_time_sec(exit_name, touchdown_spd_kt):
    profile = EXIT_CHAINS[exit_name]["occ_chain"]
    pts = [CP["THR"] + (touchdown_spd_kt,)] + profile
    total_t = 0.0
    for i in range(len(pts) - 1):
        lat1, lon1, s1 = pts[i]
        lat2, lon2, s2 = pts[i + 1]
        d = haversine_nm(lat1, lon1, lat2, lon2)
        avg = max((s1 + s2) / 2.0, 0.5)
        total_t += d / avg * 3600
    return total_t


def transit_time_doten_to_thr_sec(ac_type):
    """Thoi gian bay THAT tu DOTEN den nguong, dung toc do IAS thuc te cua
    tung loai tau bay -- dung de tinh MOC THOI GIAN cham cang chinh, roi
    tu do tinh tiep moc dung tai diem thoat ly (touchdown + occupancy_time)."""
    spd_by_type = SPEED[ac_type]
    pts = ["DOTEN"] + ORDER
    t = 0.0
    for i in range(len(pts) - 1):
        cp1, cp2 = pts[i], pts[i + 1]
        d = haversine_nm(*CP[cp1], *CP[cp2])
        avg_spd = (spd_by_type[cp1] + spd_by_type[cp2]) / 2.0
        t += d / avg_spd * 3600.0
    return t


WAKE_MATRIX = {("HEAVY", "HEAVY"): 5.0, ("HEAVY", "MEDIUM"): 6.0, ("MEDIUM", "HEAVY"): 4.0, ("MEDIUM", "MEDIUM"): 4.0}
T_COMM = 10.0


def gap_at_doten_nm(lead_type, trail_type):
    """Same backward-propagation method as the earlier analytical report:
    compute required gap at touchdown (wake + 3NM baseline + 2NM/ROT/comm),
    then propagate back to DOTEN using each type's own real speed profile
    (DOTEN/TRACO speeds are identical across all types, so the gap carried
    from DOTEN is unchanged over that leg)."""
    wake_req = WAKE_MATRIX[(WAKE_CAT[lead_type], WAKE_CAT[trail_type])]
    lead_td_spd = SPEED[lead_type]["THR"]
    t_occ = occupancy_time_sec("G6", lead_td_spd)  # conservative (longer) profile for sizing
    spd_dn351 = SPEED[trail_type]["DN351"]
    spd_thr = SPEED[trail_type]["THR"]
    v_trail_2nm = spd_thr + (2.0 / 4.420) * (spd_dn351 - spd_thr)
    occ_clr = 2.0 + (v_trail_2nm / 3600.0) * (t_occ + T_COMM)
    req_td = max(wake_req, 3.0, occ_clr)

    # Build time-distance tables (elapsed sec from DOTEN vs dist-to-go NM)
    def dist_to_thr(cp):
        idx = ORDER.index(cp) if cp in ORDER else -1
        pts = ["DOTEN"] + ORDER
        total = 0.0
        start = pts.index(cp)
        for i in range(start, len(pts) - 1):
            total += haversine_nm(*CP[pts[i]], *CP[pts[i + 1]])
        return total

    def build_table(actype):
        spd = SPEED[actype]
        t = 0.0
        pts = ["DOTEN"] + ORDER
        table = [(0.0, dist_to_thr("DOTEN"))]
        for i in range(len(pts) - 1):
            cp1, cp2 = pts[i], pts[i + 1]
            d = haversine_nm(*CP[cp1], *CP[cp2])
            avg_spd = (spd[cp1] + spd[cp2]) / 2.0
            t += d / avg_spd * 3600.0
            table.append((t, dist_to_thr(cp2)))
        return table

    lead_table = build_table(lead_type)
    trail_table = build_table(trail_type)

    def time_at_dist(table, target_dist):
        for i in range(len(table) - 1):
            t0, d0 = table[i]
            t1, d1 = table[i + 1]
            if d1 <= target_dist <= d0:
                frac = (d0 - target_dist) / (d0 - d1) if d0 != d1 else 0
                return t0 + frac * (t1 - t0)
        return table[-1][0]

    def dist_at_time(table, t, spd_first):
        if t <= table[0][0]:
            return table[0][1] + (table[0][0] - t) * spd_first / 3600.0
        for i in range(len(table) - 1):
            t0, d0 = table[i]
            t1, d1 = table[i + 1]
            if t0 <= t <= t1:
                frac = (t - t0) / (t1 - t0) if t1 != t0 else 0
                return d0 + frac * (d1 - d0)
        return table[-1][1]

    t_lead_touchdown = lead_table[-1][0]
    t_trail_at_gap = time_at_dist(trail_table, req_td)
    t_lead_doten = lead_table[0][0]
    delta = t_lead_touchdown - t_lead_doten
    t_trail_then = t_trail_at_gap - delta
    trail_dist_then = dist_at_time(trail_table, t_trail_then, 250.0)
    return trail_dist_then - dist_to_thr("DOTEN"), req_td


# ---------------------------------------------------------------------------
# Pairs: 4 worst-case (category-extreme) + 4 "typical" MEDIUM-heavy-diluting
# pairs, chosen so the whole scenario's HEAVY ratio stays ~30% (real traffic
# mix, not an artificial 50/50) + 3 go-around situations (insufficient wake
# separation).
# ---------------------------------------------------------------------------
NORMAL_PAIRS = [
    ("HH1", "A333", "B78X"),   # worst-case HEAVY->HEAVY
    ("HM1", "A333", "B38M"),   # worst-case HEAVY->MEDIUM
    ("MH1", "A21N", "B78X"),   # worst-case MEDIUM->HEAVY
    ("MM1", "A21N", "B38M"),   # worst-case MEDIUM->MEDIUM
    ("MM2", "A321", "B739"),   # typical MEDIUM->MEDIUM (dilutes HEAVY ratio)
    ("MM3", "A20N", "A320"),   # typical MEDIUM->MEDIUM
    ("MM4", "B38M", "A321"),   # typical MEDIUM->MEDIUM
    ("MM5", "A320", "A20N"),   # typical MEDIUM->MEDIUM
]

# 3 tinh huong thieu phan cach nhieu dong RIENG BIET. Khac ban truoc: tau
# DI TRUOC (lead_type) van ha canh BINH THUONG; tau DI SAU (trail_type) --
# tau dang tiep can gan hon, phat hien thieu phan cach -- moi la tau phai
# bay lai va tien nhap vong cho THAT cua IAP tuong ung (hold_name tra trong
# HOLDING_PATTERNS). forced_gap_nm la khoang cach CO CHU DICH tai DOTEN,
# luon nho hon yeu cau nhieu dong thuc te cua cap do (xem WAKE_MATRIX).
GOAROUND_PAIRS = [
    ("GA1", "KONGA", "A332", "B739", 3.0),  # HEAVY->MEDIUM
    ("GA2", "KONGA", "A20N", "A320", 3.0),  # MEDIUM->MEDIUM
    ("GA3", "KONGA", "A21N", "B78X", 3.0),  # MEDIUM->HEAVY
]


def build_landing_lines(callsign, ac_type, touchdown_spd_kt, t0_sec, exit_choice):
    lat0, lon0 = CP["DOTEN"]
    heading = 173
    t0 = fmt_time(t0_sec)
    spd = SPEED[ac_type]

    lines = [f"# --- {callsign} ({ac_type}) - CRE thang tai DOTEN, thoat ly {exit_choice} -> {EXIT_CHAINS[exit_choice]['dest_label']} ---"]
    lines.append(f"{t0}>CRE {callsign},{ac_type},{lat0:.6f},{lon0:.6f},{heading},6070,{int(DOTEN_SPEED_KT)}")

    for cp in ORDER:
        lat, lon = CP[cp]
        alt = ALT_FT[cp]
        s = spd[cp]
        if cp == "THR":
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},0,{s}  # nguong 35L (cham cang chinh, toc do that)")
        else:
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{alt},{s}  # {cp}")

    exit_info = EXIT_CHAINS[exit_choice]
    for lat, lon, s in exit_info["chain"]:
        lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},0,{s}  # thoat ly {exit_choice} (thuc te)")
    lines.append(f"{t0}>{callsign} LNAV ON")
    lines.append(f"{t0}>{callsign} VNAV ON")

    # Moc thoi gian dung tai diem thoat ly = cham cang chinh + thoi gian
    # xa da/lan thoat that (occupancy_time_sec, da sua khop dung diem dung
    # That) -- nhoi THANG chuoi MOVE lan vao gate That vao day (khong con
    # PCALL toi 1 file rieng nua), de kich ban dau ra chi con 1 file duy nhat.
    t_touchdown = t0_sec + transit_time_doten_to_thr_sec(ac_type)
    t_stop = t_touchdown + occupancy_time_sec(exit_choice, touchdown_spd_kt)
    lines += inline_stop_then_gate_lines(callsign, exit_choice, t_stop, exit_info["dest_label"])
    lines.append("")
    return lines


def build_trailer_goaround_then_land(callsign, ac_type, touchdown_spd_kt, t0_sec, hold_name, exit_choice):
    """Tau bay DI SAU: dang tiep can gan thi phat hien thieu phan cach nhieu
    dong voi tau di truoc -- KHONG ha canh, bay lai va tien nhap 1 vong cho
    THAT (toa do lay tu vatm_procedures_VVDN.geojson, khong phai xap xi) tai
    fix cua IAP tuong ung, roi bay lai tu DOTEN va ha canh binh thuong.

    MOT route LIEN TUC DUY NHAT (khong DELRTE, khong tach pha theo thoi
    gian) -- da kiem chung 2 van de rieng biet truoc khi chot thiet ke nay:

    1. Neu de VNAV ON xuyen suot ca doan len (60->1500->{hold_alt}) roi lai
       xuong (6070->...->0), BlueSky tinh truoc 1 duong ha do lien tuc cho
       CA route va "cat duong" xuong thang toi diem thap nhat (nguong lan
       2), bo qua hoan toan doan bay len + vong cho. Khac phuc: VNAV OFF +
       lenh ALT/SPD tuong minh trong suot doan len + vong cho (LNAV van dan
       duong ngang qua ADDWPT binh thuong); bat VNAV ON tro lai chi khi vao
       lai doan ha do that (DOTEN -> nguong), luc do la 1 chuoi giam do cao
       don dieu binh thuong.

    2. QUAN TRONG HON: BlueSky TU DONG XOA may bay ngay khi no bay den
       WAYPOINT CUOI CUNG cua route hien tai (coi la da "toi noi", xem
       bluesky/traffic/autopilot.py dong ~309-314). Neu vong cho + doan ha
       canh lan 2 duoc nap vao SAU, bang 1 lenh rieng phat o MOT MOC THOI
       GIAN tinh truoc (vi du qua DELRTE), thi ngay khi may bay bay het
       vong cho (diem cuoi cung dang co trong route luc do), no se BI XOA
       ngay lap tuc -- TRUOC CA KHI lenh nap route moi kip chay -- du lenh
       do da duoc lap lich dung. Da xac nhan qua nhieu lan chay thu that.
       Khac phuc DUY NHAT dang tin cay: nap TOAN BO cac waypoint (tiep can
       + doan len + vong cho + tiep can lai + thoat ly) trong CUNG 1 loat
       lenh ADDWPT phat cung luc (t0), de tai BAT KY thoi diem nao may bay
       cung luon con waypoint phia sau trong route, khong bao gio cham toi
       "waypoint cuoi cung" cho den khi thuc su cham banh that."""
    lat0, lon0 = CP["DOTEN"]
    heading = 173
    spd = SPEED[ac_type]
    hold = HOLDING_PATTERNS[hold_name]

    t0 = fmt_time(t0_sec)
    lines = [
        f"# --- {callsign} ({ac_type}) - TAU DI SAU: thieu phan cach nhieu dong, "
        f"bay lai vao Holding {hold_name} roi tiep can lai ---"
    ]
    lines.append(f"{t0}>CRE {callsign},{ac_type},{lat0:.6f},{lon0:.6f},{heading},6070,{int(DOTEN_SPEED_KT)}")

    # Tiep can den gan MAPT (KHONG ha xuong 0), VNAV ON binh thuong.
    for cp in ORDER:
        lat, lon = CP[cp]
        alt = ALT_FT[cp]
        s = spd[cp]
        if cp == "THR":
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},60,{s}  # gan MAPT, thieu phan cach -> bay lai")
        else:
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{alt},{s}  # {cp}")

    # Doan bay len + 1 vong Holding {hold_name} THAT (67 diem, khep kin).
    # VNAV OFF + ALT/SPD tuong minh (xem giai thich (1) o docstring).
    # Bay dung CA 3 doan cua phuong thuc bay lai that (AIP AD2-VVDN-13-30/
    # 32/52): DN353 -> DN333 -> DN555 -> KONGA (hold["coords"][0] la chinh
    # fix KONGA), khong cat thang tu DN353 vao vong cho nhu ban truoc.
    lines.append(f"{t0}>{callsign} VNAV OFF")
    lines.append(f"{t0}>{callsign} ALT {HOLD_ALT_FT}")
    lines.append(f"{t0}>{callsign} SPD {HOLD_SPEED_KT}")
    for ga_name, (ga_lat, ga_lon), _ in MISSED_APPROACH[:-1]:
        lines.append(f"{t0}>{callsign} ADDWPT {ga_lat:.6f},{ga_lon:.6f}  # {ga_name} (bay lai, that)")
    for i, (lat, lon) in enumerate(hold["coords"]):
        lines.append(
            f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f}"
            f"  # Holding {hold_name} diem {i + 1}/{len(hold['coords'])} (that, theo IAP)"
        )

    # Thoat vong cho, bay ve lai DOTEN va tiep can lai lan 2 (VNAV ON tro
    # lai -- tu day chi la 1 chuoi giam do cao don dieu, giong het 1 lan ha
    # canh binh thuong). Noi TIEP TUC vao CUNG route (khong DELRTE) -- xem
    # giai thich (2) o docstring.
    lines.append(f"{t0}>{callsign} VNAV ON")
    lines.append(f"{t0}>{callsign} ADDWPT {lat0:.6f},{lon0:.6f},6070,{int(DOTEN_SPEED_KT)}  # DOTEN, tiep can lai lan 2")
    for cp in ORDER:
        lat, lon = CP[cp]
        alt = ALT_FT[cp]
        s = spd[cp]
        if cp == "THR":
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},0,{s}  # nguong 35L (lan 2, cham cang chinh, toc do that)")
        else:
            lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{alt},{s}  # {cp} (lan 2)")

    exit_info = EXIT_CHAINS[exit_choice]
    for lat, lon, s in exit_info["chain"]:
        lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},0,{s}  # thoat ly {exit_choice} (thuc te)")
    lines.append(f"{t0}>{callsign} LNAV ON")

    # Moc thoi gian cham cang chinh LAN 2 = tiep can lan 1 den gan MAPT +
    # doan bay len (THR->DN353->DN333->DN555->diem vao vong cho, day du ca
    # 3 doan cua phuong thuc bay lai that) + 1 vong Holding that + tiep can
    # lan 2 tu DOTEN den nguong -- roi cong them occupancy_time_sec de ra
    # moc dung tai diem thoat ly, nhoi thang chuoi MOVE lan vao gate That
    # vao day (khong con PCALL toi file rieng nua).
    ga_chain_pts = [CP["THR"]] + [pt for _, pt, _ in MISSED_APPROACH[:-1]] + [hold["entry"]]
    ga_chain_nm = sum(
        haversine_nm(*ga_chain_pts[i], *ga_chain_pts[i + 1])
        for i in range(len(ga_chain_pts) - 1)
    )
    hold_loop_nm = sum(
        haversine_nm(*hold["coords"][i], *hold["coords"][i + 1])
        for i in range(len(hold["coords"]) - 1)
    )
    t_touchdown_2nd = (
        t0_sec
        + transit_time_doten_to_thr_sec(ac_type)
        + (ga_chain_nm + hold_loop_nm) / HOLD_SPEED_KT * 3600.0
        + transit_time_doten_to_thr_sec(ac_type)
    )
    t_stop = t_touchdown_2nd + occupancy_time_sec(exit_choice, touchdown_spd_kt)
    lines += inline_stop_then_gate_lines(callsign, exit_choice, t_stop, exit_info["dest_label"])
    lines.append("")
    return lines


def build_trailer_at_gap(callsign, ac_type, touchdown_spd_kt, t0_sec, gap_doten_nm, exit_choice):
    trail_delay_sec = gap_doten_nm / DOTEN_SPEED_KT * 3600.0
    return build_landing_lines(callsign, ac_type, touchdown_spd_kt, t0_sec + trail_delay_sec, exit_choice), trail_delay_sec


def build_trailer_goaround_at_gap(callsign, ac_type, touchdown_spd_kt, t0_sec, gap_doten_nm, hold_name, exit_choice):
    trail_delay_sec = gap_doten_nm / DOTEN_SPEED_KT * 3600.0
    return (
        build_trailer_goaround_then_land(callsign, ac_type, touchdown_spd_kt, t0_sec + trail_delay_sec, hold_name, exit_choice),
        trail_delay_sec,
    )


def main():
    lines = []
    lines.append("# VVDN - Cap tau bay hang canh lien tiep RWY35L, khoang cach toi thieu")
    lines.append("# tinh trong VVDN_KhoangCachToiThieu_TiepCanLienTiep.docx. Nhieu loai tau")
    lines.append("# bay THAT (ty le HEAVY ~30%), thoat ly NGAU NHIEN G4->gate 28 / G6->san")
    lines.append("# do so 11, + 3 tinh huong tau DI SAU phai bay lai vao vong cho THAT")
    lines.append("# Holding KONGA (phuong thuc bay lai that RWY35L) do thieu phan cach nhieu dong.")
    lines.append("00:00:00.000>DTMULT 1")
    lines.append("00:00:00.000>PLUGINS LOAD SURFACETAXI")
    lines.append("")

    max_del_time = 0.0
    all_pairs = list(NORMAL_PAIRS)

    t0 = 0.0
    prev_trail_type = None
    prev_trail_spawn = None

    for i, (label, lead_type, trail_type) in enumerate(all_pairs):
        if prev_trail_type is not None:
            cross_gap_nm, _ = gap_at_doten_nm(prev_trail_type, lead_type)
            cross_delay_sec = cross_gap_nm / DOTEN_SPEED_KT * 3600.0
            t0 = max(t0, prev_trail_spawn + cross_delay_sec)

        lead_cs = f"L{label}"
        trail_cs = f"T{label}"

        gap_doten_nm, req_td = gap_at_doten_nm(lead_type, trail_type)
        lead_exit = random.choice(["G4", "G6"])
        trail_exit = random.choice(["G4", "G6"])

        lines.append(
            f"# ===== Cap {label}: {lead_type} -> {trail_type} | Khoang cach yeu cau tai DOTEN = "
            f"{gap_doten_nm:.2f} NM (yeu cau khi cham cang chinh = {req_td:.2f} NM) ====="
        )
        lines += build_landing_lines(lead_cs, lead_type, SPEED[lead_type]["THR"], t0, lead_exit)
        trailer_lines, trail_delay_sec = build_trailer_at_gap(trail_cs, trail_type, SPEED[trail_type]["THR"], t0, gap_doten_nm, trail_exit)
        lines += trailer_lines
        lines.append("")

        # KHONG phat lenh DEL an toan o day: moi tau bay da tu xoa (DEL %0)
        # ngay trong file lan vao ben do/san do that cua no (da xac nhan qua
        # nhieu lan chay thu song). Neu them 1 lenh "DEL <acid>" sau khi
        # acid do da tu xoa roi, BlueSky KHONG bao loi an toan ma co the
        # xoa nham 1 tau bay khac dang bay (da kiem chung: DEL voi acid
        # khong ton tai roi vao nhanh xu ly "txt" thay vi "acid" va cuoi
        # cung goi bs.traf.delete voi du lieu sai, xoa nham tau cuoi cung
        # trong mang traffic) -- rui ro hon la khong co gi ca.
        trail_del_time = t0 + trail_delay_sec + AIRCRAFT_LIFECYCLE_SEC
        max_del_time = max(max_del_time, trail_del_time)

        prev_trail_type = trail_type
        prev_trail_spawn = t0 + trail_delay_sec
        t0 = t0 + MIN_PAIR_OFFSET_SEC  # tentative next start; may get bumped up above

    # --- 3 tinh huong thieu phan cach nhieu dong: tau DI SAU vao vong cho ---
    for ga_label, hold_name, ga_lead_type, ga_trail_type, ga_forced_gap_nm in GOAROUND_PAIRS:
        cross_gap_nm, _ = gap_at_doten_nm(prev_trail_type, ga_lead_type)
        cross_delay_sec = cross_gap_nm / DOTEN_SPEED_KT * 3600.0
        t0 = max(t0, prev_trail_spawn + cross_delay_sec)
        lead_cs = f"L{ga_label}"
        trail_cs = f"T{ga_label}"
        wake_req = WAKE_MATRIX[(WAKE_CAT[ga_lead_type], WAKE_CAT[ga_trail_type])]

        lines.append(
            f"# ===== Cap {ga_label} (TAU SAU BAY LAI): {ga_lead_type} -> {ga_trail_type} | "
            f"Khoang cach CO CHU DICH tai DOTEN = {ga_forced_gap_nm:.1f} NM "
            f"(< yeu cau nhieu dong {wake_req:.1f} NM -> {trail_cs} phai bay lai vao Holding {hold_name}) ====="
        )
        lead_exit = random.choice(["G4", "G6"])
        trail_exit = random.choice(["G4", "G6"])
        lines += build_landing_lines(lead_cs, ga_lead_type, SPEED[ga_lead_type]["THR"], t0, lead_exit)
        trailer_lines, trail_delay_sec = build_trailer_goaround_at_gap(
            trail_cs, ga_trail_type, SPEED[ga_trail_type]["THR"], t0, ga_forced_gap_nm, hold_name, trail_exit
        )
        lines += trailer_lines
        lines.append("")

        # Khong phat lenh DEL an toan o day, cung ly do nhu cac cap binh
        # thuong (xem chu thich phia tren): moi tau da tu xoa qua file gate
        # that cua no.
        lead_del_time = t0 + AIRCRAFT_LIFECYCLE_SEC
        trail_del_time = t0 + trail_delay_sec + GOAROUND_TRAILER_LIFECYCLE_SEC
        max_del_time = max(max_del_time, lead_del_time, trail_del_time)

        prev_trail_type = ga_trail_type
        # The go-around trailer only actually re-touches the DOTEN corridor
        # (heading toward the runway again) after its hold+second-approach;
        # for cross-pair scheduling purposes treat its EFFECTIVE "spawn at
        # DOTEN" as its own spawn time (its first pass is a real, if
        # aborted, approach through the same corridor at the same time).
        prev_trail_spawn = t0 + trail_delay_sec
        t0 = t0 + MIN_PAIR_OFFSET_SEC

    OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Da ghi {OUT_FILE}")
    print(f"Tong thoi luong kich ban: ~{fmt_time(max_del_time + 60)}")
    print(f"So cap binh thuong: {len(all_pairs)}, + {len(GOAROUND_PAIRS)} tinh huong bay lai (tau sau)")


if __name__ == "__main__":
    main()
