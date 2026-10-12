#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_gen_2a2d_1hour.py -- Sinh kịch bản 1 giờ VVDN bằng cách "nhân" logic 1 cặp
ARR/DEP đã kiểm chứng kỹ trong VVDN_2A2D_35R_HOLDSHORT thành N cặp liên
tiếp, mỗi cặp cách nhau đúng 5 phút, NHƯNG giờ tàu bay về (ARR002+) bay theo
ĐÚNG 1 trong 8 STAR RNAV RWY35LR thật của VVDN (BUNTA dùng bản "2M" mới, 7
STAR còn lại giữ "2K"), và tàu bay đi (DEP) bay theo SID RNAV RWY35LR ngẫu
nhiên -- toạ độ/khống chế cao độ-tốc độ lấy NGUYÊN VĂN từ _gen_kb5_1hour.py
(đã đọc trực tiếp từ AIP AD 2-VVDN, không bịa số liệu).

- ARR001 (chuyến đầu): CRE thẳng tại CADAS, T=0 tuyệt đối (không qua STAR --
  giữ đúng quy ước đã kiểm chứng của VVDN_2A2D_35R_HOLDSHORT).
- ARR002+: mỗi chuyến được gán ngẫu nhiên 1 trong 8 STAR, tỉ lệ theo hướng
  địa lý: Bắc (HUE, CAHEO) 35%, Nam (KUMUN, SADIN, VILOT) 35%, Đông (BUNTA)
  15%, Tây (LATOM, PAPRA) 15% -- chia đều trong từng nhóm. Mực bay tại điểm
  đầu STAR: Đông+Bắc = FL240, Tây+Nam = FL250 (khớp đúng dữ liệu STAR_IAF
  thật đã dùng trong _gen_kb5_1hour.py, không cần chỉnh).
- Thời điểm CRE (spawn) của mỗi ARR002+ được tính NGƯỢC từ mục tiêu giãn
  cách 5 phút tại CADAS (target_cadas_t = (i-1)*300s), dùng ĐÚNG toạ độ/tốc
  độ thật của STAR đó để ước lượng thời gian bay (estimate_transit_s) --
  KHÔNG ép cứng thời gian bay thật (BlueSky tự bay theo BADA). Nếu bay từ
  đúng IAF vẫn kịp mục tiêu thì CRE tại IAF; nếu không kịp (STAR quá dài so
  với slot giãn cách 5 phút -- hiếm khi xảy ra nhưng vẫn xử lý), CRE tại 1
  điểm nội suy GẦN CADAS HƠN trên chính STAR đó (bỏ đoạn IAF xa), y hệt cơ
  chế truncated_star_spawn() đã kiểm chứng trong _gen_kb5_1hour.py.
- Mỗi DEP được gán 1 SID RNAV RWY35LR ngẫu nhiên trong 8 SID thật (SID_CHAINS)
  -- sinh riêng 1 file DEP_ROLL_<dep_id>.scn cho từng chuyến (SID khác thì
  climb-out khác).
- Thoát ly ARR (E4 30% / E6 70%), Trigger A/B, plugin TAXIWAYREROUTE, HDG
  352° tại điểm chờ... giữ NGUYÊN như đã kiểm chứng.
- Hạng tàu bay: mỗi tàu bay (ARR và DEP, tính độc lập trên toàn bộ 2*N_PAIRS
  chuyến) được chia CHÍNH XÁC theo tỷ lệ 70% MEDIUM / 30% HEAVY (stratified
  shuffle, giống cơ chế E4/E6). LOẠI tàu bay cụ thể trong mỗi hạng (ví dụ
  A321/A320/B738 cho MEDIUM, A333/B777/B787 cho HEAVY) được random THẬT
  trong danh sách các ICAO type đã có sẵn file hiệu suất BADA thật (đối
  chiếu trực tiếp với bluesky/data/performance/bada/*.OPF), để BlueSky mô
  phỏng đúng tính năng bay (leo/giảm/tốc độ) riêng của từng loại tàu bay
  thay vì dùng 1 loại cố định cho cả kịch bản.

Chạy: python _gen_2a2d_1hour.py
"""
import datetime
import io
import math
import random
import shutil
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ================================================================
# Tham số
# ================================================================
SEED = 20260812
N_PAIRS = 12             # 60 phút / 5 phút = 12 cặp
SPACING_S = 300           # 5 phút -- ARR tại CADAS VÀ DEP bắt đầu lăn
E4_PROBABILITY = 0.30    # 30% E4, 70% E6
HEAVY_PROBABILITY = 0.30  # 30% HEAVY, 70% MEDIUM -- áp cho từng tàu bay (ARR và DEP độc lập)

# Danh sách loại tàu bay CHỈ gồm các ICAO type ĐÃ CÓ file hiệu suất BADA thật
# trong FTS Server/bluesky/data/performance/bada/ (đối chiếu trực tiếp từng
# type với *.OPF có sẵn -- không suy diễn) VÀ đúng hạng nhiễu động tương ứng
# trong aircraft_wake_categories.json, để BlueSky mô phỏng đúng tính năng bay
# thật (leo/giảm/tốc độ theo BADA) cho từng loại, không dùng 1 loại cố định.
MEDIUM_TYPE_POOL = ["A319", "A320", "A321", "A20N", "A21N", "B737", "B738", "B739", "B38M", "B39M", "E195", "E170", "F100"]
# E190 (Embraer E-Jet) loai bo khoi pool theo yeu cau cua nguoi dung: khong
# con duoc cac hang hang khong Viet Nam khai thac nua -- khong dung cho cac
# kich ban sinh moi tu nay ve sau. E195/E170 van giu vi khong duoc yeu cau bo.
HEAVY_TYPE_POOL = ["A332", "A333", "A339", "A342", "A343", "A345", "A346", "A359", "A35K", "B744", "B748", "B762", "B763", "B764", "B772", "B773", "B77L", "B77W", "B788", "B789", "B78X"]

HERE = Path(__file__).parent
SRC_DIR = HERE / "VVDN_2A2D_35R_HOLDSHORT"
OUT_DIR = HERE / "VVDN_2A2D_1HOUR_35R"
BACKUP_ROOT = HERE / "Backup"

SHARED_TEMPLATES_VERBATIM = [
    "ARR_EXIT_E4.scn",
    "ARR_EXIT_E6.scn",
    "DEP_TAXI_TO_HOLD.scn",
    "DEP_TAXI_TO_HOLD_ALT_D.scn",
    "DEP_ENTER_LINEUP.scn",
    "STOP_AND_DEL.scn",
    "VNAV_ON.scn",
]

E4_TURN = (16.049011, 108.199650)
E6_POINT = (16.057523, 108.199282)
GATE26 = (16.052628, 108.201989, 80.9)

# ================================================================
# Toạ độ thật (nguyên văn từ _gen_kb5_1hour.py, không bịa số liệu)
# ================================================================
CADAS = (15.618056, 108.262500)
_TRACO = (15.601667, 108.142222, 7695, 230)

STAR_IAF = {
    # tên: (lat, lon, alt_ft khi CRE, spd_kt khi CRE)
    "HUE": (16.402222, 107.701667, 24000, 280),
    "CAHEO": (16.536389, 107.965278, 24000, 280),
    "BUNTA": (16.833333, 109.395000, 24000, 280),
    "KUMUN": (14.971389, 108.807500, 25000, 280),
    "SADIN": (15.080000, 108.177222, 25000, 280),
    "VILOT": (15.038611, 108.111667, 25000, 280),
    "LATOM": (14.879444, 107.843611, 25000, 280),
    "PAPRA": (15.766667, 107.183333, 25000, 280),
}

_CHAIN_HINTA_ONWARD = [
    (16.167500, 108.048611, 15000, 280),  # HINTA
    (16.020000, 108.081667, 12000, 250),  # DN369
    (15.854722, 108.105278, 8000, 250),   # TAWAN
    (15.767222, 108.118333, 6070, 250),   # DOTEN
]
_CHAIN_NOCKA_ONWARD = [
    (15.419444, 108.046667, 16000, 280),  # NOCKA
    (15.585278, 108.022500, 12000, 280),  # DN368
    (15.750833, 107.998611, 8500, 250),   # VIDAN
    (15.767222, 108.118333, 6070, 250),   # DOTEN
]

STAR_CHAINS = {
    "HUE": _CHAIN_HINTA_ONWARD,
    "CAHEO": _CHAIN_HINTA_ONWARD,
    "BUNTA": [  # BUNTA 2M (AIP amendment mới, thay "2K")
        (16.354167, 108.664722, 24000, 280),   # KANGU
        (16.258056, 108.507222, 22000, 280),   # LINDA
        (15.908611, 108.512500, 15000, 250),   # KONGA
        (15.820556, 108.512778, 12000, 240),   # ROMIN
        (15.799722, 108.358056, 9500, 230),    # ZATON
        (15.633889, 108.381667, 8000, 225),    # ESSEN
    ],
    "KUMUN": _CHAIN_NOCKA_ONWARD,
    "SADIN": [(15.262778, 108.106944, 20000, 280)] + _CHAIN_NOCKA_ONWARD,  # HENTA
    "VILOT": [(15.254444, 108.074722, 20000, 280)] + _CHAIN_NOCKA_ONWARD,  # KHUHO
    "LATOM": [(15.262500, 107.987500, 20000, 280)] + _CHAIN_NOCKA_ONWARD,  # NOVAN
    "PAPRA": [
        (15.748611, 107.733056, 14000, 280),  # MANGA
        (15.750833, 107.998611, 8500, 250),   # VIDAN
        (15.767222, 108.118333, 6070, 250),   # DOTEN
    ],
}


def _full_pre_cadas_chain(star):
    if star == "BUNTA":
        return STAR_CHAINS[star]  # BUNTA 2M: đã tự kết thúc ở ESSEN, ngay trước CADAS
    return STAR_CHAINS[star] + [_TRACO]

# Nhóm hướng địa lý + tỉ lệ theo yêu cầu: Bắc 35%, Nam 35%, Đông 15%, Tây 15%
# (chia đều trong từng nhóm; Đông chỉ có 1 STAR nên nhận trọn 15%).
STAR_DIRECTION_WEIGHT = {
    "HUE": 35 / 2, "CAHEO": 35 / 2,                              # Bắc
    "KUMUN": 35 / 3, "SADIN": 35 / 3, "VILOT": 35 / 3,           # Nam
    "BUNTA": 15,                                                  # Đông
    "LATOM": 15 / 2, "PAPRA": 15 / 2,                            # Tây
}

# Đuôi cố định sau CADAS (dùng chung mọi ARR, tàu bay A321) -- nguyên văn
# ARR_APPROACH.scn gốc của VVDN_2A2D_35R_HOLDSHORT.
CADAS_REAL = (15.618056, 108.262500, 6071, 230)
POST_CADAS_TAIL = [
    (15.700556, 108.250000, 4921, 210),   # MONRY
    (15.788333, 108.237500, 4429, 180),   # TAMLA
    (15.872651, 108.225236, 2880, 166),   # FIRAI
    (15.956505, 108.213078, 1335, 152),   # FF35R
    (16.029047, 108.202547, 0, 140),      # DN010 (ngưỡng 35R)
]
DN010 = (16.029047, 108.202547)

# ================================================================
# 8 SID RNAV RWY35LR thật (nguyên văn từ _gen_kb5_1hour.py)
# ================================================================
_SID_INITIAL = (16.076637, 108.195656, 1500, 180)
_SID_DN456 = (16.334167, 108.192500, 8038, 250)
_SID_DN450 = (16.174444, 108.194722, 4000, 200)

_SID_NORTH_TRUNK = [
    _SID_DN456,
    (16.586667, 108.135278, 11000, 260),   # LAIKA
    (16.694722, 107.888611, 14000, 280),   # PHULU
]
_SID_SOUTH_TRUNK = [
    _SID_DN450,
    (16.177222, 108.387778, 6000, 250),    # DN451
    (16.093333, 108.388889, 7054, 240),    # DN452
    (15.909444, 108.391389, 10000, 260),   # DN453
]

SID_CHAINS = {
    "PHULU": [_SID_INITIAL] + _SID_NORTH_TRUNK,
    "KONCO": [_SID_INITIAL] + _SID_NORTH_TRUNK + [
        (16.895833, 107.426944, 18000, 300),   # TRABE
        (17.000000, 107.186944, 21000, 310),   # KONCO
    ],
    "VIDEN": [_SID_INITIAL] + _SID_NORTH_TRUNK + [
        (16.895833, 107.426944, 18000, 300),   # TRABE
        (17.020556, 107.365556, 21000, 310),   # VIDEN
    ],
    "BUNTA": [_SID_INITIAL, _SID_DN456,
        (16.451111, 108.578611, 11000, 260),   # HOKIN
        (16.559722, 108.973056, 16000, 290),   # BINKU
        (16.833333, 109.395000, 20000, 310),   # BUNTA
    ],
    "KUMUN": [_SID_INITIAL] + _SID_SOUTH_TRUNK + [
        (15.543333, 108.395833, 14000, 280),   # KEMSY
        (14.971389, 108.807500, 18000, 300),   # KUMUN
    ],
    "SADIN": [_SID_INITIAL] + _SID_SOUTH_TRUNK + [
        (15.543333, 108.395833, 14000, 280),   # KEMSY
        (15.080000, 108.177222, 17000, 290),   # SADIN
    ],
    "XAQUA": [_SID_INITIAL] + _SID_SOUTH_TRUNK + [
        (15.543333, 108.395833, 14000, 280),   # KEMSY
        (15.080000, 108.177222, 17000, 290),   # SADIN
        (14.919444, 108.101667, 19000, 300),   # XAQUA
    ],
    "PAPRA": [_SID_INITIAL] + _SID_SOUTH_TRUNK + [
        (15.906944, 108.061944, 18000, 290),   # DN454
        (15.905833, 107.931111, 20000, 300),   # DN455
        (15.903333, 107.658889, 21000, 300),   # TANNA
        (15.766667, 107.183333, 22000, 310),   # PAPRA
    ],
}
SID_NAMES = list(SID_CHAINS.keys())


# ================================================================
# Helpers hình học / ước lượng thời gian bay (nguyên văn từ _gen_kb5_1hour.py)
# ================================================================
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def tas_correction(alt_ft):
    return 1.0 + 0.00002 * max(alt_ft, 0.0)


def leg_times_s(points_with_spd_kt, start_latlon):
    KT = 0.514444
    total_t = 0.0
    prev = start_latlon
    prev_spd = None
    for lat, lon, spd in points_with_spd_kt:
        d = haversine_m(prev[0], prev[1], lat, lon)
        v0 = prev_spd if prev_spd else spd
        avg_v = max(((v0 + spd) / 2) * KT, 1.0)
        total_t += d / avg_v
        prev = (lat, lon)
        prev_spd = spd
    return total_t


def estimate_transit_s(chain_with_alt, start_latlon):
    legs = [(lat, lon, spd * tas_correction(alt)) for (lat, lon, alt, spd) in chain_with_alt]
    return leg_times_s(legs, start_latlon)


_CADAS_PLACEHOLDER = (CADAS[0], CADAS[1], CADAS_REAL[2], CADAS_REAL[3])
_STAR_TRANSIT = {
    name: estimate_transit_s(_full_pre_cadas_chain(name) + [_CADAS_PLACEHOLDER], (STAR_IAF[name][0], STAR_IAF[name][1]))
    for name in STAR_IAF
}


def _star_nodes(star):
    iaf_lat, iaf_lon, iaf_alt, iaf_spd = STAR_IAF[star]
    return [(iaf_lat, iaf_lon, iaf_alt, iaf_spd)] + _full_pre_cadas_chain(star) + [_CADAS_PLACEHOLDER]


def _remaining_transit_per_node(nodes):
    n = len(nodes)
    remaining = [0.0] * n
    for j in range(n - 2, -1, -1):
        lat0, lon0, _alt0, _spd0 = nodes[j]
        lat1, lon1, alt1, spd1 = nodes[j + 1]
        d = haversine_m(lat0, lon0, lat1, lon1)
        v = spd1 * tas_correction(alt1) * 0.514444
        remaining[j] = d / v + remaining[j + 1]
    return remaining


def truncated_star_spawn(star, target_cadas_t):
    nodes = _star_nodes(star)
    remaining = _remaining_transit_per_node(nodes)
    n = len(nodes)
    for j in range(n - 1):
        if remaining[j] >= target_cadas_t >= remaining[j + 1]:
            lat0, lon0, alt0, _spd0 = nodes[j]
            lat1, lon1, alt1, spd1 = nodes[j + 1]
            leg_t = remaining[j] - remaining[j + 1]
            frac = 0.0 if leg_t <= 0 else (remaining[j] - target_cadas_t) / leg_t
            frac = min(max(frac, 0.0), 1.0)
            lat = lat0 + (lat1 - lat0) * frac
            lon = lon0 + (lon1 - lon0) * frac
            alt = round(alt0 + (alt1 - alt0) * frac)
            hdg = round(bearing_deg(lat, lon, lat1, lon1), 1)
            return lat, lon, alt, spd1, hdg, nodes[j + 1:-1]
    lat, lon, alt, spd = nodes[-2]
    return lat, lon, alt, spd, round(bearing_deg(lat, lon, nodes[-1][0], nodes[-1][1]), 1), []


def clamp_monotonic_descent(legs):
    """Ép cao độ không tăng dọc chuỗi -- tránh lỗi khi ghép nhiều đoạn STAR
    khác nguồn có thể có 1 điểm cao hơn điểm ngay trước nó (ví dụ DOTEN 6070ft
    -> TRACO 7695ft) -- y hệt safeguard trong _gen_kb5_1hour.py."""
    out = []
    prev_alt = 999999
    for (lat, lon, alt, spd) in legs:
        alt = min(alt, prev_alt)
        out.append((lat, lon, alt, spd))
        prev_alt = alt
    return out


def fmt_time(seconds):
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


def backup_existing():
    if not OUT_DIR.exists():
        return
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest = BACKUP_ROOT / f"VVDN {ts}"
    dest.mkdir(parents=True, exist_ok=True)
    for item in OUT_DIR.iterdir():
        if item.is_file():
            shutil.copy2(item, dest / item.name)
    print(f"Da backup {OUT_DIR} -> {dest}")


def make_arr_approach_file(arr_id, star, cre_override):
    """Sinh file ARR_APPROACH_<arr_id>.scn -- ghép [chuỗi STAR thật trước
    CADAS (hoặc phần còn lại nếu bị cắt bớt do truncated spawn)] + CADAS thật
    + đuôi cố định sau CADAS (MONRY->TAMLA->FIRAI->FF35R->DN010)."""
    if star is None:
        # ARR001: CRE thẳng tại CADAS, không có STAR phía trước.
        legs = [CADAS_REAL] + POST_CADAS_TAIL
        note = "CRE thẳng tại CADAS (T=0, không qua STAR)"
    elif cre_override is not None:
        legs = cre_override["remaining_nodes"] + [CADAS_REAL] + POST_CADAS_TAIL
        note = f"STAR {star} -- CRE tại điểm cắt gần CADAS hơn (bỏ đoạn IAF xa)"
    else:
        legs = _full_pre_cadas_chain(star) + [CADAS_REAL] + POST_CADAS_TAIL
        note = f"STAR {star} (IAF -> CADAS -> ngưỡng 35R)"

    legs = clamp_monotonic_descent(legs)
    lines_txt = "\n".join(
        f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} {alt} {spd}" for (lat, lon, alt, spd) in legs
    )
    content = f"""# ARR_APPROACH_{arr_id}.scn -- {note}
# Toạ độ/khống chế lấy nguyên văn AIP STAR RNAV RWY35LR (không bịa số liệu).
# Gọi ngay sau CRE: PCALL ARR_APPROACH_{arr_id} <acid>
{lines_txt}
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
"""
    (OUT_DIR / f"ARR_APPROACH_{arr_id}.scn").write_text(content, encoding="utf-8")


def make_dep_roll_file(dep_id, sid):
    legs = SID_CHAINS[sid]
    lines_txt = "\n".join(
        f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} {alt} {spd}" for (lat, lon, alt, spd) in legs
    )
    content = f"""# DEP_ROLL_{dep_id}.scn -- chạy đà cất cánh, bay SID {sid} (RNAV RWY35LR thật)
# Gọi: PCALL DEP_ROLL_{dep_id} <acid>
00:00:00.00>TAXIOFF %0
00:00:00.00>%0 DELRTE
{lines_txt}
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV OFF
00:00:00.00>%0 SPD 250
00:00:00.00>%0 VS 2000
00:00:00.00>%0 ALT 10000
00:00:00.00>%0 ATALT 1500 PCALL VNAV_ON %0
"""
    (OUT_DIR / f"DEP_ROLL_{dep_id}.scn").write_text(content, encoding="utf-8")


def main():
    backup_existing()
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)  # da backup xong, xoa sach de khong ton file cu/mo-hinh-cu con sot lai
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for name in SHARED_TEMPLATES_VERBATIM:
        shutil.copy2(SRC_DIR / name, OUT_DIR / name)

    # ARR_VACATED_ROLL.scn -- bản riêng cho kịch bản này, nhận thêm %1 = tên
    # file DEP_ROLL_<dep_id> riêng của từng chuyến (vì SID khác nhau theo
    # từng DEP, không dùng chung 1 file DEP_ROLL.scn như bản 2 cặp gốc nữa).
    (OUT_DIR / "ARR_VACATED_ROLL.scn").write_text("""# ARR_VACATED_ROLL.scn -- 30 giây SAU KHI ARR thoát ly hoàn toàn khỏi 35R,
# PCALL đúng file DEP_ROLL riêng (SID riêng) của DEP tương ứng.
# Gọi: ATDIST ... PCALL ARR_VACATED_ROLL <acid_DEP> <ten_file_DEP_ROLL>
00:00:30.00>PCALL %1 %0
""", encoding="utf-8")

    rng = random.Random(SEED)

    n_e4_target = round(N_PAIRS * E4_PROBABILITY)
    n_e6_target = N_PAIRS - n_e4_target
    exit_choices = ["E4"] * n_e4_target + ["E6"] * n_e6_target
    rng.shuffle(exit_choices)

    # Tỷ lệ HẠNG tàu bay 70% MEDIUM / 30% HEAVY chia CHÍNH XÁC theo số lượng
    # (stratified) trên toàn bộ 2*N_PAIRS tàu bay (ARR + DEP), không dùng
    # random.choice thô cho TỶ LỆ để tránh lệch khi N nhỏ. Trong mỗi hạng,
    # LOẠI tàu bay cụ thể (A321/A320/B738/...) MỚI random thật trong pool
    # BADA thật của hạng đó -- không gán cứng 1 loại duy nhất cho cả hạng.
    n_aircraft = N_PAIRS * 2
    n_heavy_target = round(n_aircraft * HEAVY_PROBABILITY)
    n_medium_target = n_aircraft - n_heavy_target
    category_choices = ["HEAVY"] * n_heavy_target + ["MEDIUM"] * n_medium_target
    rng.shuffle(category_choices)
    ac_type_choices = [
        rng.choice(HEAVY_TYPE_POOL) if cat == "HEAVY" else rng.choice(MEDIUM_TYPE_POOL)
        for cat in category_choices
    ]
    ac_type_iter = iter(ac_type_choices)

    star_names = list(STAR_DIRECTION_WEIGHT.keys())
    star_weights = list(STAR_DIRECTION_WEIGHT.values())
    sid_choices = [rng.choice(SID_NAMES) for _ in range(N_PAIRS)]

    lines = [f"""# ================================================================
# VVDN_2A2D_1HOUR_35R.scn -- Kịch bản 1 giờ, {N_PAIRS} cặp ARR/DEP trên 35R.
# ARR001 CRE thẳng tại CADAS (T=0). ARR002+ bay theo 1 trong 8 STAR RNAV
# RWY35LR thật (BUNTA dùng bản "2M"), chọn ngẫu nhiên theo hướng địa lý:
# Bắc (HUE,CAHEO) 35%, Nam (KUMUN,SADIN,VILOT) 35%, Đông (BUNTA) 15%, Tây
# (LATOM,PAPRA) 15%. Mực bay tại điểm đầu STAR: Đông+Bắc=FL240, Tây+Nam=FL250.
# Thời điểm CRE tính ngược để MỖI ARR tới CADAS cách chuyến trước đúng
# {SPACING_S}s ({SPACING_S // 60} phút) -- dùng estimate_transit_s() theo
# đúng toạ độ/tốc độ thật của STAR được gán (không ép cứng thời gian bay
# thật trong engine).
#
# DEP mỗi chuyến bay theo 1 SID RNAV RWY35LR thật ngẫu nhiên trong 8 SID
# (SID_CHAINS). DEP bắt đầu lăn cách nhau đúng {SPACING_S}s ({SPACING_S // 60} phút),
# độc lập với lịch CRE của ARR.
#
# Toàn bộ logic Trigger A/B, plugin TAXIWAYREROUTE (đường lăn E/D), HDG 352°
# tại điểm chờ... giữ NGUYÊN như đã kiểm chứng trong VVDN_2A2D_35R_HOLDSHORT.
# Seed cố định {SEED} để tái tạo được.
# ================================================================
00:00:00.00>PLUGINS LOAD SURFACETAXI
00:00:00.00>PLUGINS LOAD DEPARRALERT
00:00:00.00>PLUGINS LOAD TAXIWAYREROUTE
00:00:00.00>ASAS OFF
00:00:00.00>TRAILS ON
00:00:00.00>PAN 16.0400,108.2000
"""]

    summary = []

    for i in range(1, N_PAIRS + 1):
        arr_id = f"ARR{i:03d}"
        dep_id = f"DEP{i:03d}"
        exitway = exit_choices[i - 1]
        exit_file = f"ARR_EXIT_{exitway}"
        vacate_pt = E4_TURN if exitway == "E4" else E6_POINT
        sid = sid_choices[i - 1]
        dep_type = next(ac_type_iter)
        arr_type = next(ac_type_iter)
        dep_t = (i - 1) * SPACING_S
        dep_ts = fmt_time(dep_t)

        target_cadas_t = (i - 1) * SPACING_S

        if i == 1:
            star = None
            cre_override = None
            arr_t = 0.0
            arr_lat, arr_lon, arr_hdg, arr_alt, arr_spd = CADAS[0], CADAS[1], 353, 6071, 230
        else:
            star = rng.choices(star_names, weights=star_weights, k=1)[0]
            full_transit = _STAR_TRANSIT[star]
            if full_transit <= target_cadas_t:
                cre_override = None
                arr_t = target_cadas_t - full_transit
                iaf_lat, iaf_lon, iaf_alt, iaf_spd = STAR_IAF[star]
                first_lat, first_lon = _full_pre_cadas_chain(star)[0][0], _full_pre_cadas_chain(star)[0][1]
                arr_lat, arr_lon, arr_alt, arr_spd = iaf_lat, iaf_lon, iaf_alt, iaf_spd
                arr_hdg = round(bearing_deg(iaf_lat, iaf_lon, first_lat, first_lon), 1)
            else:
                lat, lon, alt, spd, hdg, remaining_nodes = truncated_star_spawn(star, target_cadas_t)
                cre_override = {"remaining_nodes": remaining_nodes}
                arr_t = 0.0
                arr_lat, arr_lon, arr_alt, arr_spd, arr_hdg = lat, lon, alt, spd, hdg

        make_arr_approach_file(arr_id, star, cre_override)
        make_dep_roll_file(dep_id, sid)

        arr_ts = fmt_time(arr_t)
        summary.append(f"  {arr_id} [{arr_type}]: STAR={star or '(CADAS truc tiep)'} CRE_t={arr_t:.1f}s target_CADAS_t={target_cadas_t:.0f}s "
                        f"{'[CAT NGAN]' if cre_override else ''} | {dep_id} [{dep_type}]: SID={sid} exit={exitway}")

        lines.append(f"""
# ================================================================
# CẶP {i} -- {arr_id} [{arr_type}] (STAR {star or 'CADAS trực tiếp'}) / {dep_id} [{dep_type}] (SID {sid}, thoát ly {exitway})
# ================================================================
{dep_ts}>CRE {dep_id},{dep_type},{GATE26[0]:.6f},{GATE26[1]:.6f},{GATE26[2]},0,0
{dep_ts}>TAXION {dep_id} 15 44.5
{dep_ts}>TAXIROUTE {dep_id}

{arr_ts}>CRE {arr_id},{arr_type},{arr_lat:.6f},{arr_lon:.6f},{arr_hdg},{arr_alt},{arr_spd}
{arr_ts}>PCALL ARR_APPROACH_{arr_id} {arr_id}
{arr_ts}>PCALL {exit_file} {arr_id}

# Trigger A{i}: {arr_id} vượt đầu thềm 35R -> +10s {dep_id} vào đường CHC (lineup)
{arr_ts}>{arr_id} ATDIST {DN010[0]:.6f},{DN010[1]:.6f},0.02 PCALL DEP_ENTER_LINEUP {dep_id}

# Trigger B{i}: {arr_id} thoát ly hoàn toàn tại {exitway} -> +30s {dep_id} chạy đà (SID {sid})
{arr_ts}>{arr_id} ATDIST {vacate_pt[0]:.6f},{vacate_pt[1]:.6f},0.02 PCALL ARR_VACATED_ROLL {dep_id} DEP_ROLL_{dep_id}
""")

    out_path = OUT_DIR / "VVDN_2A2D_1HOUR_35R.scn"
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Da sinh {out_path}\n")
    print("Chi tiet lich trinh:")
    for s in summary:
        print(s)
    n_e4 = exit_choices.count("E4")
    print(f"\nPhan bo thoat ly: E4={n_e4} ({n_e4 / N_PAIRS * 100:.0f}%), E6={N_PAIRS - n_e4} ({(N_PAIRS - n_e4) / N_PAIRS * 100:.0f}%)")
    n_heavy = category_choices.count("HEAVY")
    heavy_types_used = sorted(set(t for t, c in zip(ac_type_choices, category_choices) if c == "HEAVY"))
    medium_types_used = sorted(set(t for t, c in zip(ac_type_choices, category_choices) if c == "MEDIUM"))
    print(f"Phan bo hang tau bay: HEAVY={n_heavy} ({n_heavy / n_aircraft * 100:.0f}%) [{', '.join(heavy_types_used)}], "
          f"MEDIUM={n_aircraft - n_heavy} ({(n_aircraft - n_heavy) / n_aircraft * 100:.0f}%) [{', '.join(medium_types_used)}]")


if __name__ == "__main__":
    main()
