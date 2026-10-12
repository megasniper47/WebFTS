"""
vvdn_wake_category_minsep_matrix.scn

Kich ban thu nghiem CO HE THONG: 4 cap tau bay ha canh lien tiep tren RWY35L
VVDN, moi cap dai dien cho DUNG 1 trong 4 to hop hang nhieu dong xuat hien
thuc te trong dan tau bay VVDN (chi co HEAVY/MEDIUM, khong co SUPER/LIGHT --
xac nhan tu 13 loai tau bay that da dung trong kich ban
"VVDN_KB5_1HOUR_MIXED.scn"):
  Cap 1: HEAVY  -> HEAVY
  Cap 2: HEAVY  -> MEDIUM
  Cap 3: MEDIUM -> HEAVY
  Cap 4: MEDIUM -> MEDIUM

Trong moi cap, tau DAN DAU va tau BAM SAU duoc chon la loai tau THAT co toc
do cham banh CUC BIEN (worst-case) trong hang cua no -- lay tu chinh du lieu
that da dung trong VVDN_KB5_1HOUR_MIXED.scn (_KB5GEN_ARR_APPROACH_ARRxxx.scn,
dong ADDWPT cuoi = toc do cham banh):
  HEAVY : A333 cham banh 130kt (CHAM NHAT trong hang HEAVY) -> dung lam
          DAN DAU worst-case (cham banh cham -> thoi gian chiem dung duong
          CHC lau hon).
          B78X cham banh 160kt (NHANH NHAT trong hang HEAVY) -> dung lam
          BAM SAU worst-case (toc do cao -> bay duoc xa hon trong cung 1
          khoang thoi gian, doi hoi phan cach lon hon).
  MEDIUM: E190 cham banh 120kt (CHAM NHAT) -> DAN DAU worst-case.
          B38M cham banh 160kt (NHANH NHAT) -> BAM SAU worst-case.
Day la lua chon CO CHU DICH de moi cap cho ra gia tri yeu cau CAO NHAT co
the trong hang do (an toan, khong danh gia thap), khong phai chon ngau
nhien.

Ca 4 cap deu bay CUNG 1 STAR RNAV RWY35L/R that "HUE 2K" (AIP AD2-VVDN-11-8,
AMDT 01/23) roi tiep tuc RNP Z RWY35L that (AD2-VVDN-13-52) -- giong het
kich ban vvdn_2acft_hue2k_b787_a321_35l_landing.scn da dung truoc do, chi
thay doi loai tau bay va lap lai 4 lan voi khoang cach thoi gian lon (30
phut/cap) de khong cap nao anh huong cap khac.

Phan cach ban dau tai t=0 giua 2 tau trong tung cap = 3NM bang hinh hoc
(phan cach radar toi thieu chuan tai khu vuc tiep can VVDN) -- CHUA cong
nhieu dong, giong quy uoc da dung o kich ban 2-tau truoc. Kich ban nay
DUNG DE DO tham so THAT (toc do cham banh thuc te theo mo hinh hieu suat
BlueSky, thoi gian chiem dung duong CHC thuc te) roi ap dung cong thuc
phan cach toi thieu (nhieu dong + occupancy/clearance) da xay dung o
phien lam viec truoc, KHONG de kiem tra rieng 3NM co du hay khong.
"""
import math
from pathlib import Path

OUT_DIR = Path(".")


def dms(d, m, s):
    return d + m / 60.0 + s / 3600.0


def dest_point(lat, lon, bearing_deg, dist_nm):
    R = 3440.065
    d = dist_nm / R
    brng = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    lat2 = math.asin(math.sin(lat1) * math.cos(d) + math.cos(lat1) * math.sin(d) * math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d) * math.cos(lat1), math.cos(d) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)


def m_to_ft(m):
    return round(m * 3.28084)


def kmh_to_kt(kmh):
    return round(kmh * 0.539957)


# ---------------------------------------------------------------------------
# Real waypoints (WGS-84), AIP AD2-VVDN-11-8/9/11 (STAR HUE 2K) and
# AD2-VVDN-13-52 (RNP Z RWY35L final segment), AMDT 01/23 -- same as the
# earlier 2-aircraft VVDN scenario this session.
# ---------------------------------------------------------------------------
WPT = {
    "HUE":   (dms(16, 24, 8), dms(107, 42, 6)),
    "HINTA": (dms(16, 10, 3), dms(108, 2, 55)),
    "DN369": (dms(16, 1, 12), dms(108, 4, 54)),
    "TAWAN": (dms(15, 51, 17), dms(108, 6, 19)),
    "DOTEN": (dms(15, 46, 2), dms(108, 7, 6)),
    "TRACO": (dms(15, 36, 6), dms(108, 8, 32)),
    "CADAS": (dms(15, 37, 5), dms(108, 15, 45)),
    "MONRY": (dms(15, 42, 2), dms(108, 15, 0)),
    "TAMLA": (dms(15, 47, 18), dms(108, 14, 15)),
    "KALET": (dms(15, 52, 24.8), dms(108, 13, 23.1)),
    "DN351": (dms(15, 57, 26.0), dms(108, 12, 39.4)),
    "RW35L": (dms(16, 1, 48.48), dms(108, 12, 1.34)),
}

ROLLOUT = dest_point(WPT["RW35L"][0], WPT["RW35L"][1], 352.0, 0.81)

# Full real STAR RNAV RWY35L/R "HUE 2K" chain (AIP AD2-VVDN-11-8/9/11) into
# RNP Z RWY35L (AD2-VVDN-13-52) -- same chain already validated this session
# against the real KB5 recording (produced correct touchdown speeds/behavior).
# An earlier attempt to shorten this to KALET-only caused BlueSky's VNAV to
# smooth the descent/deceleration profile into touching ground ~1NM short of
# the real threshold at a fixed ~100kt regardless of aircraft type -- a real
# defect from truncating the approach, not a sampling-resolution problem.
STAR_LEGS_AFTER_HUE = [
    ("HINTA", m_to_ft(2750), None),
    ("DN369", m_to_ft(2450), kmh_to_kt(420)),
    ("TAWAN", None, None),
    ("DOTEN", m_to_ft(1850), None),
    ("TRACO", None, None),
    ("CADAS", None, None),
    ("MONRY", m_to_ft(1500), kmh_to_kt(390)),
    ("TAMLA", m_to_ft(1350), None),
    ("KALET", m_to_ft(790), None),
    ("DN351", m_to_ft(450), None),
]

# Worst-case representative real aircraft per wake category, with their real
# touchdown speed from VVDN_KB5_1HOUR_MIXED.scn's own approach files.
CATEGORY_REPRESENTATIVES = {
    "HEAVY_LEADER":  ("A333", 130),   # slowest HEAVY touchdown -> longest runway occupancy
    "HEAVY_TRAILER": ("B78X", 160),   # fastest HEAVY touchdown -> largest V_trail
    "MEDIUM_LEADER":  ("E190", 120),  # slowest MEDIUM touchdown
    "MEDIUM_TRAILER": ("B38M", 160), # fastest MEDIUM touchdown
}

PAIRS = [
    ("HH", "HEAVY_LEADER", "HEAVY_TRAILER"),
    ("HM", "HEAVY_LEADER", "MEDIUM_TRAILER"),
    ("MH", "MEDIUM_LEADER", "HEAVY_TRAILER"),
    ("MM", "MEDIUM_LEADER", "MEDIUM_TRAILER"),
]

PAIR_CRE_OFFSET_SEC = 1500.0  # 25 min between pairs -- HUE-entry transit measured
                              # ~1200-1300s (20-22 min) in the earlier validated
                              # single-pair run, so this margin avoids inter-pair
                              # interference.

# --- Cat/ha canh xen ke (35R departure interleaved with 35L arrivals) -------
# Test THAT ngưỡng "ARR ≥ 6NM tren truc chot" (QĐ 2850/QĐ-CHK, muc 4.1, dieu
# kien thu 3 -- co giam sat ATS) bang cach kich hoat DEP dung tai thoi diem
# tau BAM SAU (tau con dang tiep can, la "ARR" duoc tham chieu trong dieu
# kien) cach nguong dung 6.0NM. Diem do/huong DEP giu nguyen thuc te (16.
# 052628,108.201989, hdg 80.9, da doi chuan -- ap dung nguong 30s theo muc
# 3.9). SID PAPRA va toan bo trinh tu TAXIOFF->30s->DELRTE+climb lay lai
# NGUYEN VAN tu _KB5GEN_DEP_ROLL_DEP001.scn (file da generic hoa qua %0,
# PCALL truc tiep duoc, khong can tao file moi).
DEP_TYPE = "B739"
DEP_SPAWN = (16.052628, 108.201989)
DEP_HEADING = 80.9
DEP_RELEASE_DIST_NM = 6.0  # nguong thu 3, muc 4.1


def fmt_time(total_sec):
    if total_sec < 0:
        total_sec = 0
    h = int(total_sec // 3600)
    m = int((total_sec % 3600) // 60)
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def build_leader_lines(callsign, ac_type, touchdown_spd_kt, t0_sec):
    lat0, lon0 = WPT["HUE"]
    heading = 125
    t0 = fmt_time(t0_sec)

    lines = [f"# --- {callsign} ({ac_type}) - dan dau, vao STAR tai IF HUE ---"]
    lines.append(f"{t0}>CRE {callsign},{ac_type},{lat0:.6f},{lon0:.6f},{heading},FL120,280")

    for name, alt_ft, spd_kt in STAR_LEGS_AFTER_HUE:
        lat, lon = WPT[name]
        parts = [f"{lat:.6f}", f"{lon:.6f}"]
        if alt_ft is not None:
            parts.append(str(alt_ft))
            if spd_kt is not None:
                parts.append(str(spd_kt))
        lines.append(f"{t0}>{callsign} ADDWPT {','.join(parts)}  # {name}")

    lat, lon = WPT["RW35L"]
    lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},0,{touchdown_spd_kt}  # RW35L threshold (touchdown, real spd)")
    lines.append(f"{t0}>{callsign} ADDWPT {ROLLOUT[0]:.6f},{ROLLOUT[1]:.6f},0,20  # rollout (assumed)")
    lines.append(f"{t0}>{callsign} LNAV ON")
    lines.append(f"{t0}>{callsign} VNAV ON")
    lines.append("")
    return lines


def build_trailer_lines(callsign, ac_type, touchdown_spd_kt, t0_sec):
    lat_hue, lon_hue = WPT["HUE"]
    trail_entry = dest_point(lat_hue, lon_hue, 305.0, 3.0)  # 3NM behind HUE (geometric)
    heading = 125
    t0 = fmt_time(t0_sec)

    lines = [f"# --- {callsign} ({ac_type}) - bam sau, cach dung 3NM tai t=0 (hinh hoc) ---"]
    lines.append(f"{t0}>CRE {callsign},{ac_type},{trail_entry[0]:.6f},{trail_entry[1]:.6f},{heading},FL120,280")

    lat, lon = WPT["HUE"]
    lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f}  # HUE (IF)")

    for name, alt_ft, spd_kt in STAR_LEGS_AFTER_HUE:
        lat, lon = WPT[name]
        parts = [f"{lat:.6f}", f"{lon:.6f}"]
        if alt_ft is not None:
            parts.append(str(alt_ft))
            if spd_kt is not None:
                parts.append(str(spd_kt))
        lines.append(f"{t0}>{callsign} ADDWPT {','.join(parts)}  # {name}")

    lat, lon = WPT["RW35L"]
    lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},0,{touchdown_spd_kt}  # RW35L threshold (touchdown, real spd)")
    lines.append(f"{t0}>{callsign} ADDWPT {ROLLOUT[0]:.6f},{ROLLOUT[1]:.6f},0,20  # rollout (assumed)")
    lines.append(f"{t0}>{callsign} LNAV ON")
    lines.append(f"{t0}>{callsign} VNAV ON")
    lines.append("")
    return lines


def build_dep_lines(dep_cs, trigger_cs, t0_sec):
    lat0, lon0 = DEP_SPAWN
    t0 = fmt_time(t0_sec)
    lines = [f"# --- {dep_cs} ({DEP_TYPE}) - dau tai san do G26, lan ra RWYHOLD 35R that ---"]
    lines.append(f"{t0}>CRE {dep_cs},{DEP_TYPE},{lat0:.6f},{lon0:.6f},{DEP_HEADING},0,15")
    # Dong bo TAXION+PCALL tuyen lan that (giong DEP001 trong KB5) -- KHONG
    # de rieng, tranh dung lap loi "di thang huong do" da gap truoc day khi
    # TAXION dat toc do nhung chua co tuyen/route.
    lines.append(f"{t0}>TAXION {dep_cs} 15 42.1")
    lines.append(f"{t0}>PCALL _KB5GEN_TAXI_G26_RWYHOLD {dep_cs}  # tuyen lan that (G26 -> RWYHOLD 35R)")
    lines.append(
        f"{t0}>{trigger_cs} ATDIST {WPT['RW35L'][0]:.6f},{WPT['RW35L'][1]:.6f},{DEP_RELEASE_DIST_NM} "
        f"PCALL _KB5GEN_DEP_ROLL_DEP001 {dep_cs}  "
        f"# huan lenh cat canh khi {trigger_cs} cach nguong dung {DEP_RELEASE_DIST_NM}NM (muc 4.1 dieu kien 3)"
    )
    lines.append("")
    return lines


def main():
    lines = []
    lines.append("# VVDN - Ma tran phan cach toi thieu theo hang nhieu dong (HEAVY/MEDIUM)")
    lines.append("# 4 cap dai dien worst-case, cung STAR RNAV \"HUE 2K\" -> RNP Z RWY35L that.")
    lines.append("# Moi cap co them 1 DEP xen ke tren 35R, huan lenh cat canh khi tau bam")
    lines.append("# sau cach nguong dung 6.0NM (QD 2850/QD-CHK muc 4.1 dieu kien 3).")
    lines.append("# Moi cap cach nhau 30 phut CRE de khong giao thoa.")
    lines.append("00:00:00.000>DTMULT 1")
    lines.append("00:00:00.000>PLUGINS LOAD SURFACETAXI")
    lines.append("")

    max_del_time = 0.0
    for i, (label, leader_key, trailer_key) in enumerate(PAIRS):
        t0 = i * PAIR_CRE_OFFSET_SEC
        leader_type, leader_spd = CATEGORY_REPRESENTATIVES[leader_key]
        trailer_type, trailer_spd = CATEGORY_REPRESENTATIVES[trailer_key]
        leader_cs = f"L{label}"
        trailer_cs = f"T{label}"

        dep_cs = f"D{label}"

        lines.append(f"# ===== Cap {label}: {leader_type}({leader_key.split('_')[0]}) -> {trailer_type}({trailer_key.split('_')[0]}) + DEP xen ke 35R =====")
        lines += build_leader_lines(leader_cs, leader_type, leader_spd, t0)
        lines += build_trailer_lines(trailer_cs, trailer_type, trailer_spd, t0)
        lines += build_dep_lines(dep_cs, trailer_cs, t0)

        del_time = t0 + PAIR_CRE_OFFSET_SEC - 60.0
        lines.append(f"{fmt_time(del_time)}>DEL {leader_cs}")
        lines.append(f"{fmt_time(del_time)}>DEL {trailer_cs}")
        lines.append(f"{fmt_time(del_time)}>DEL {dep_cs}")
        lines.append("")
        max_del_time = del_time

    out_path = OUT_DIR / "vvdn_wake_category_minsep_matrix.scn"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Da ghi {out_path}")
    print(f"Tong thoi luong kich ban: ~{fmt_time(max_del_time + 60)}")


if __name__ == "__main__":
    main()
