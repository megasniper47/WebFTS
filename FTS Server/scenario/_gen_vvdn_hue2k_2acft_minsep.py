"""
vvdn_2acft_hue2k_b787_a321_35l_landing.scn
vvdn_2acft_hue2k_b787_a321_35l_goaround.scn

Kich ban 2 tau bay ha canh lien tiep VVDN, cung STAR RNAV RWY35L/R "HUE 2K"
(AIP AD2-VVDN-11-8, AMDT 01/23), dung de xac dinh cu ly toi thieu thuc te
giua 2 tau bay tai 3 moc:
  1. Tau 1 (dan dau) cham banh (touchdown RWY35L).
  2. Tau 1 tien nhap "canh 5" cua phuong thuc bay (STAR HUE 2K danh so
     cac canh: 1=IF HUE, 2=HINTA, 3=DN369, 4=TAWAN, 5=DOTEN) -> canh 5 = DOTEN.
  3. Truong hop tau 1 bay lai (missed approach) thay vi ha canh.

Thu tu: Tau 1 = B787 (dan dau), Tau 2 = A321 (bam sau). Dieu kien khi tuong
thong thuong (VMC). Phan cach ban dau giua 2 tau khi thiet lap tren STAR =
3NM (phan cach radar toi thieu chuan tai khu vuc tiep can VVDN), CO Y THUC
KHONG cong them phan cach nhieu dong (wake turbulence) -- day la yeu cau
ro rang cua nguoi dung de co lap bai toan: xem voi dung 3NM phan cach radar
thuan tuy, cu ly thuc te con lai la bao nhieu tai 3 moc tren.

NGUON DU LIEU THAT (khong bia):
- STAR RNAV RWY35L/R "HUE 2K" (waypoint/alt/toc do), AIP AD2-VVDN-11-8/9/11,
  AMDT 01/23: HUE(IF) -> HINTA(+2750m) -> DN369(-2450m, <=420km/h)
  -> TAWAN -> DOTEN(+1850m) -> TRACO -> CADAS -> MONRY(+1500m,<=390km/h)
  -> TAMLA(+1350m).
- Tiep tuc tiep can ILS/RNP Z RWY35L (AIP AD2-VVDN-13-52, RNP Z RWY35L,
  AMDT 01/23): TAMLA(IAF) -> KALET(IF,+790m) -> DN351(+450m)
  -> nguong RWY35L (MAPT, VPA -3.00 do, TCH 15.25m).
- Phuong thuc bay lai (missed approach), giong het tren ca ILS U/V va
  RNP Z RWY35L (AIP AD2-VVDN-13-30/32/52, AMDT 01/23): CF DN353 (353M/352.2T)
  -> TF DN333 (039M, 9.10km) -> TF DN555 (092M, 21.53km)
  -> TF KONGA (167M, 34.21km, len +1200m) -> HM KONGA (giu cho, vong trai,
  +1200m).
- Toa do WGS-84 chuyen doi truc tiep tu DMS trong 2 tai lieu tren.

GIA DINH (khong phai so lieu AIP, ghi ro):
- Do cao ATC-assigned tai IF HUE (khong co gia tri cong bo tai diem nay,
  vi day la diem vao STAR, do cao do ATC cap chu khong phai chart-published):
  dung FL120 (3658m) lam do cao vao STAR hop ly, VNAV se tu dieu chinh giam
  dan theo cac rang buoc that phia sau.
- Toc do tai cac chang khong co gioi han cong bo: uoc luong toc do IAS dien
  hinh theo tung loai tau bay (B787 nhanh hon A321 mot chut o pha tiep can
  xa), KHONG anh huong den cac rang buoc do cao/khoang cach/huong that.
- Diem "cuoi duong lan sau khi cham banh" (rollout ~1500m qua nguong, cung
  huong 352 T): uoc luong hop ly de tau bay "bien mat" sau khi ha canh,
  khong phai so lieu chinh thuc chieu dai duong CHC.
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
# Real waypoint coordinates (WGS-84), AIP AD2-VVDN-11-8/9/11 (STAR) and
# AD2-VVDN-13-52 (RNP Z RWY35L final segment + missed approach), AMDT 01/23.
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
    "DN353": (dms(16, 8, 47.0), dms(108, 11, 2.0)),
    "DN333": (dms(16, 12, 40.0), dms(108, 14, 11.0)),
    "DN555": (dms(16, 12, 33.0), dms(108, 26, 16.0)),
    "KONGA": (dms(15, 54, 31.0), dms(108, 30, 45.0)),
}

# Rollout point ~1500m past RW35L threshold, continuing the same inbound
# track (352.0 T) -- assumed, not an official runway-length figure.
ROLLOUT = dest_point(WPT["RW35L"][0], WPT["RW35L"][1], 352.0, 0.81)

# Trailing aircraft spawn point: exactly 3 NM behind HUE along the
# reciprocal of the real HUE->HINTA track (125.0 T -> reciprocal 305.0 T).
# This gives an EXACT 3NM initial separation at t=0 by geometry, avoiding
# any need to predict BlueSky's own performance-model timing.
TRAIL_ENTRY = dest_point(WPT["HUE"][0], WPT["HUE"][1], 305.0, 3.0)

STAR_LEGS_AFTER_HUE = [
    # (name, alt_ft or None, spd_kt or None)  -- alt/spd from AIP where given
    ("HINTA", m_to_ft(2750), None),
    ("DN369", m_to_ft(2450), kmh_to_kt(420)),
    ("TAWAN", None, None),
    ("DOTEN", m_to_ft(1850), None),   # <-- "canh 5" cua STAR HUE 2K
    ("TRACO", None, None),
    ("CADAS", None, None),
    ("MONRY", m_to_ft(1500), kmh_to_kt(390)),
    ("TAMLA", m_to_ft(1350), None),
    ("KALET", m_to_ft(790), None),
    ("DN351", m_to_ft(450), None),
]

MISSED_APPROACH_LEGS = [
    ("DN353", None, None),
    ("DN333", None, None),
    ("DN555", None, None),
    ("KONGA", m_to_ft(1200), None),
]


def fmt_time(total_sec):
    if total_sec < 0:
        total_sec = 0
    h = int(total_sec // 3600)
    m = int((total_sec % 3600) // 60)
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def build_leader_lines(goaround):
    """ARR1 = B787, tau dan dau. CRE truc tiep tai HUE (leg 1 cua STAR)."""
    callsign = "ARR1"
    ac_type = "B788"
    lat0, lon0 = WPT["HUE"]
    heading = 125  # course That HUE->HINTA (AIP: 126 M / 125.0 T)
    t0 = "00:00:00.000"

    lines = [f"# --- {callsign} ({ac_type}, B787) - dan dau, vao STAR tai IF HUE ---"]
    lines.append(f"{t0}>CRE {callsign},{ac_type},{lat0:.6f},{lon0:.6f},{heading},FL120,280")

    for name, alt_ft, spd_kt in STAR_LEGS_AFTER_HUE:
        lat, lon = WPT[name]
        parts = [f"{lat:.6f}", f"{lon:.6f}"]
        if alt_ft is not None:
            parts.append(str(alt_ft))
            if spd_kt is not None:
                parts.append(str(spd_kt))
        lines.append(f"{t0}>{callsign} ADDWPT {','.join(parts)}  # {name}")

    if not goaround:
        lat, lon = WPT["RW35L"]
        lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},0  # RW35L threshold (touchdown)")
        lines.append(f"{t0}>{callsign} ADDWPT {ROLLOUT[0]:.6f},{ROLLOUT[1]:.6f},0,20  # rollout (assumed)")
    else:
        # Bay lai: khong ha xuong 0, ma tiep tuc chuoi missed-approach that
        # tu ngay tai/gan nguong (CF DN353 353M/352.2T, that giong ILS U/V
        # va RNP Z RWY35L).
        lat, lon = WPT["RW35L"]
        lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},{m_to_ft(60)}  # gan MAPT, quyet dinh bay lai")
        for name, alt_ft, spd_kt in MISSED_APPROACH_LEGS:
            lat, lon = WPT[name]
            parts = [f"{lat:.6f}", f"{lon:.6f}"]
            if alt_ft is not None:
                parts.append(str(alt_ft))
            lines.append(f"{t0}>{callsign} ADDWPT {','.join(parts)}  # {name} (missed approach)")

    lines.append(f"{t0}>{callsign} LNAV ON")
    lines.append(f"{t0}>{callsign} VNAV ON")
    lines.append("")
    return lines


def build_trailer_lines():
    """ARR2 = A321, tau bam sau, cach dung 3NM phia sau ARR1 tai t=0 (theo
    hinh hoc, khong phu thuoc du doan toc do)."""
    callsign = "ARR2"
    ac_type = "A321"
    lat0, lon0 = TRAIL_ENTRY
    heading = 125
    t0 = "00:00:00.000"

    lines = [f"# --- {callsign} ({ac_type}, A321) - bam sau ARR1 dung 3NM tai t=0 (hinh hoc) ---"]
    lines.append(f"{t0}>CRE {callsign},{ac_type},{lat0:.6f},{lon0:.6f},{heading},FL120,260")

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
    lines.append(f"{t0}>{callsign} ADDWPT {lat:.6f},{lon:.6f},0  # RW35L threshold (touchdown)")
    lines.append(f"{t0}>{callsign} ADDWPT {ROLLOUT[0]:.6f},{ROLLOUT[1]:.6f},0,20  # rollout (assumed)")

    lines.append(f"{t0}>{callsign} LNAV ON")
    lines.append(f"{t0}>{callsign} VNAV ON")
    lines.append("")
    return lines


def build_scn(goaround):
    lines = []
    lines.append("# VVDN - 2 tau bay ha canh lien tiep RWY35L, cung STAR RNAV \"HUE 2K\"")
    lines.append("# ARR1 = B787 (dan dau), ARR2 = A321 (bam sau)")
    lines.append("# Phan cach ban dau tai t=0: dung 3NM (hinh hoc), CHUA cong nhieu dong.")
    if goaround:
        lines.append("# BIEN THE: ARR1 BAY LAI (missed approach that) thay vi ha canh.")
    else:
        lines.append("# BIEN THE: ca 2 tau ha canh binh thuong.")
    lines.append("00:00:00.000>PAN VVDN")
    lines.append("00:00:00.000>DTMULT 1")
    lines.append("")
    lines += build_leader_lines(goaround)
    lines += build_trailer_lines()
    lines.append("01:00:00.000>DEL ARR1")
    lines.append("01:00:00.000>DEL ARR2")
    return "\n".join(lines) + "\n"


def main():
    landing_path = OUT_DIR / "vvdn_2acft_hue2k_b787_a321_35l_landing.scn"
    goaround_path = OUT_DIR / "vvdn_2acft_hue2k_b787_a321_35l_goaround.scn"

    landing_path.write_text(build_scn(goaround=False), encoding="utf-8")
    goaround_path.write_text(build_scn(goaround=True), encoding="utf-8")

    print(f"Da ghi {landing_path}")
    print(f"Da ghi {goaround_path}")
    print(f"TRAIL_ENTRY (ARR2 spawn, 3NM sau HUE) = {TRAIL_ENTRY}")
    print(f"ROLLOUT (sau nguong RW35L) = {ROLLOUT}")


if __name__ == "__main__":
    main()
