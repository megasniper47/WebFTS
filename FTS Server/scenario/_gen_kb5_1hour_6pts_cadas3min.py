import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
"""
Generator cho kịch bản VVDN_KB5_1HOUR_6PTS_CADAS3MIN.scn — BIẾN THỂ của
_gen_kb5_1hour.py (KHÔNG sửa file gốc), theo yêu cầu:
  - Tàu bay ĐẾN chỉ xuất hiện (CRE) tại 6 điểm: HAMIN 30%, SADIN 20%,
    VILOT 10%, PAPRA 15%, BUNTA 20%, CQ 5% (thay 8 STAR gốc/tỉ lệ gốc).
  - Thời điểm CRE tại các điểm trên được tính ngược sao cho, bay theo đúng
    tính năng BADA/OpenAP của từng loại tàu bay, đạt giãn cách 3 phút
    (ARR_SPACING_S=180s -- KHÔNG đổi so với bản gốc, bản gốc vốn đã dùng đúng
    180s) tại điểm CADAS -- dùng lại NGUYÊN VẸN thuật toán tính ngược
    (estimate_transit_s/truncated_star_spawn) đã có sẵn và đã kiểm chứng.
  - Mực bay tại các điểm CRE nói trên là FL230 hoặc FL240 (chọn ngẫu nhiên
    mỗi chuyến) khi CRE ĐÚNG TẠI điểm thật (không áp cho các slot quá sớm bị
    "cắt bớt" CRE gần CADAS hơn -- xem cadas6_alt_override bên dưới, vì lúc
    đó tàu bay không thực sự "xuất hiện tại" điểm được đặt tên nữa, mà tại 1
    điểm nội suy gần CADAS hơn nhiều, không hợp lý nếu vẫn giữ FL230/240).

DỮ LIỆU MỚI (CQ 2K, HAMIN) lấy trực tiếp từ AIP, KHÔNG bịa:
  - CQ 2K ARRIVAL: đọc nguyên văn từ chính file PDF gốc dùng cho 8 STAR còn
    lại (AIP AD 2-VVDN-11-9, "1. TABULAR DESCRIPTION" + "3. WAYPOINT LIST"
    tại AD 2-VVDN-11-11) -- STAR_RNAV_RWY35LR_CQ_2K.pdf trong
    "vietnam_ats_routes_pack/Dữ liệu PTB + code/PTB QLBMT/
    VVDN_PBN_Procedure_Extract_Pack/STAR_RNAV_RWY35LR/". Chuỗi thật:
    CQ -> TAMKY -> ESSEN -> CADAS -> MONRY -> TAMLA (CQ 2K KHÔNG qua TRACO,
    nhập thẳng CADAS từ ESSEN -- giống BUNTA, khác 7 STAR còn lại). Toạ độ
    CADAS/MONRY/TAMLA/ESSEN đọc ra từ chính waypoint list này khớp CHÍNH XÁC
    (6 chữ số thập phân) với giá trị đã dùng sẵn trong _gen_kb5_1hour.py --
    xác nhận chéo CADAS=(15.618056,108.262500) là điểm thật, đúng.
  - HAMIN: điểm ATS enroute CÓ THẬT (AIP ENR 3.1, xem
    WebATM/static/data/vietnam_ats_waypoints.geojson + AIXM DesignatedPoint
    export), KHÔNG phải 1 trong 9 STAR/IAF của VVDN -- không có lộ trình
    STAR riêng. Theo đúng thứ tự thật trên đường bay công bố ("... XONUS
    HAMIN PHULU CAHEO DA NANG ...", vietnam_ats_routes.geojson), ghép
    HAMIN -> PHULU -> CAHEO (điểm CAHEO chính là IAF của CAHEO 2K) rồi bay
    tiếp đúng chuỗi CAHEO 2K đã có sẵn (_CHAIN_HINTA_ONWARD) -- không tạo
    lộ trình mới, chỉ nối 1 đoạn thật trước 1 STAR thật đã kiểm chứng.
    PHULU/CAHEO dùng lại ĐÚNG toạ độ đã có trong generator gốc (khớp 6 chữ
    số thập phân với AIP WAYPOINT LIST khi đối chiếu lại độc lập).

Phần còn lại (SID/DEP, taxi, pushback, thoát ly, plugin, v.v.) giữ NGUYÊN
100% như _gen_kb5_1hour.py -- yêu cầu của người dùng chỉ liên quan tàu bay
ĐẾN (arrival), không đụng khởi hành.

Chạy: py _gen_kb5_1hour_6pts_cadas3min.py
"""
import datetime
import math
import os
import random
import shutil

random.seed(20260807)  # cố định để tái tạo được cùng kịch bản khi cần

# Thư mục backup dùng chung cho MỌI generator kịch bản trong dự án (không chỉ
# file này) -- mỗi lần sinh kịch bản mới, backup TOÀN BỘ file .scn vừa sinh
# vào 1 thư mục con đặt tên "<ICAO> <giờ-ngày-tháng-năm>" lúc sinh (ví dụ
# "VVDN 2026-08-08_20-46-16"), để phân biệt được kịch bản của sân bay nào
# khi có nhiều generator/sân bay khác nhau, và không mất lịch sử các phiên
# bản kịch bản trước đó.
BACKUP_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Backup")
AIRPORT_ICAO = "VVDN"


def backup_generated_files(out_dir, filenames, icao=AIRPORT_ICAO):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest_dir = os.path.join(BACKUP_ROOT, f"{icao} {ts}")
    os.makedirs(dest_dir, exist_ok=True)
    for fname in filenames:
        src = os.path.join(out_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest_dir, fname))
    print(f"Đã backup {len(filenames)} file vào {dest_dir}")

# Thư mục MỚI, riêng biệt cho biến thể này -- KHÔNG dùng chung OUT_DIR với
# _gen_kb5_1hour.py gốc, vì cả 2 sinh ra file cùng tên (ARR001..ARR020, v.v.)
# và sẽ ghi đè lẫn nhau nếu dùng chung thư mục.
OUT_DIR = r"D:\Coding\Dự án FTS\WebFTS v4\FTS Server\scenario\VVDN_KB5_1HOUR_6PTS_CADAS3MIN"
os.makedirs(OUT_DIR, exist_ok=True)

N_PAIRS = 20  # giữ nguyên bản gốc -- 20 cặp ARR/DEP, ~1 giờ khai thác
ARR_SPACING_S = 180  # 3 phút giữa 2 chuyến hạ cánh liên tiếp tại CADAS (giữ nguyên bản gốc, đúng yêu cầu "giãn cách 3 phút")
DEP_SPACING_S = 180  # giữ nguyên bản gốc

MEDIUM_TYPES = ["A320", "A321", "A20N", "A21N", "B738", "B38M", "B739"]
HEAVY_TYPES = ["A332", "A333", "A359", "B744", "B763", "B772", "B773", "B77W", "B788", "B789", "B748", "B78X"]

# Chiều dài thân tàu bay thật [m] -- lấy nguyên từ bảng đã dùng cho render 3D
# ở frontend (frontend/src/data/aircraftDimensions.ts) để đồng bộ số liệu
# trong toàn dự án. B78X (787-10) không có trong bảng đó -- dùng chiều dài
# thật công bố của Boeing (68.28m) làm giá trị bổ sung.
AIRCRAFT_LENGTH_M = {
    "A320": 37.57, "A321": 44.51, "A20N": 37.57, "A21N": 44.51,
    "B738": 39.47, "B38M": 39.47, "B739": 42.11, "E190": 36.24,
    "A332": 58.82, "A333": 63.67, "A359": 66.80, "B744": 70.66,
    "B763": 54.94, "B772": 63.73, "B773": 73.86, "B77W": 73.86,
    "B788": 56.72, "B789": 62.81, "B748": 76.30, "B78X": 68.28,
}


def aircraft_length_m(actype):
    return AIRCRAFT_LENGTH_M.get(actype, 45.0 if actype in MEDIUM_TYPES else 65.0)

# ================================================================
# KHỐNG CHẾ TỐC ĐỘ TIẾP CẬN (IAS) THEO TỪNG LOẠI TÀU BAY -- lấy từ Vstall
# thật trong BADA (WebATM/server/bada_api.py, stallSpeedsKcas cấu hình AP/LD),
# rồi rải theo tỉ lệ tuyến tính (nội suy theo Vstall của CẢ 20 loại đang dùng
# trong kịch bản) vào đúng 3 dải tốc độ người dùng yêu cầu:
#   - 25NM cách ngưỡng 35L: 200-230kt (rải theo Vstall cấu hình AP)
#   - 10NM cách ngưỡng 35L (trên trục tiếp cận chót): 160-180kt (theo Vstall AP)
#   - 5NM cách ngưỡng 35L (trên trục tiếp cận chót): 150-160kt (theo Vstall LD)
# Tốc độ chạm bánh (trước khi vào chuỗi giảm tốc riêng của EXIT_G4/G6) lấy
# ~1.3×Vstall_LD (cùng công thức Vapp đã dùng trong bada_api._derive_approach_speeds),
# không bị ép vào dải 150-160 vì đó là mốc SAU điểm 5NM.
# Cách tính (đã chạy 1 lần, chốt số liệu tại đây để generator không phải phụ
# thuộc import package WebATM lúc sinh kịch bản):
#   scale(v,vmin,vmax,lo,hi) = round_to_5(lo + (hi-lo)*(v-vmin)/(vmax-vmin))
#   Vstall_AP: min=97 (E190), max=135 (B77W); Vstall_LD: min=94 (E190), max=124 (B748)
# Mỗi giá trị: (tốc độ@25NM, tốc độ@10NM, tốc độ@5NM, tốc độ chạm bánh)
# ================================================================
MEDIUM_APPROACH_SPEEDS = {
    "A320": (205, 165, 150, 130),
    "A321": (205, 165, 155, 135),
    "A20N": (205, 165, 150, 130),
    "A21N": (215, 170, 155, 140),
    "B738": (210, 165, 155, 140),
    "B38M": (225, 175, 160, 160),
    "B739": (215, 170, 155, 145),
    "E190": (200, 160, 150, 120),
}
HEAVY_APPROACH_SPEEDS = {
    "A332": (210, 165, 155, 135),
    "A333": (205, 165, 150, 130),
    "A359": (215, 170, 155, 145),
    "B744": (225, 175, 160, 155),
    "B763": (220, 175, 160, 155),
    "B772": (210, 165, 155, 135),
    "B773": (220, 175, 155, 145),
    "B77W": (230, 180, 160, 160),
    "B788": (215, 170, 155, 145),
    "B789": (215, 170, 155, 145),
    "B748": (225, 180, 160, 160),
    "B78X": (230, 180, 160, 160),
}
APPROACH_SPEEDS = {**MEDIUM_APPROACH_SPEEDS, **HEAVY_APPROACH_SPEEDS}


def approach_speeds(actype):
    """(tốc độ@25NM, tốc độ@10NM, tốc độ@5NM, tốc độ chạm bánh) theo BADA."""
    return APPROACH_SPEEDS[actype]


def interp_speed(spd_a, spd_b, frac):
    """Nội suy tuyến tính giữa 2 mốc tốc độ đã chốt theo BADA, làm tròn 5kt."""
    raw = spd_a + (spd_b - spd_a) * frac
    return int(round(raw / 5.0) * 5)


# Tỉ lệ 70/30 áp CHÍNH XÁC trên tổng số tàu bay (2*N_PAIRS), không phải xác
# suất độc lập từng chuyến (xác suất độc lập với mẫu nhỏ dễ lệch xa 70/30 --
# đã thử và ra 48/52 với N=20). Danh sách nhãn cố định rồi xáo trộn, đảm bảo
# đúng tỉ lệ bất kể seed.
_total_aircraft = 2 * N_PAIRS
_n_medium = round(_total_aircraft * 0.70)
_n_heavy = _total_aircraft - _n_medium
_type_pool = (
    [random.choice(MEDIUM_TYPES) for _ in range(_n_medium)]
    + [random.choice(HEAVY_TYPES) for _ in range(_n_heavy)]
)
random.shuffle(_type_pool)
_type_pool_iter = iter(_type_pool)


def pick_type():
    return next(_type_pool_iter)

# Tỉ lệ thoát ly: 30% G4, 70% G6 trên tổng số chuyến đến (N_PAIRS)
_n_g4 = round(N_PAIRS * 0.30)
_n_g6 = N_PAIRS - _n_g4
_exit_pool = ["G4"] * _n_g4 + ["G6"] * _n_g6
random.shuffle(_exit_pool)
_exit_pool_iter = iter(_exit_pool)

def pick_exit():
    return next(_exit_pool_iter)


def _quota_pool(weights_dict, total_n):
    """Phân bổ total_n phần tử theo ĐÚNG tỉ lệ weights_dict, dùng phương pháp
    "số dư lớn nhất" (largest remainder) để tổng luôn khớp total_n chính xác
    -- CÙNG vấn đề/cách xử lý đã dùng ở trên cho tỉ lệ loại tàu bay 70/30
    (random.choices độc lập với mẫu nhỏ [ở đây chỉ 19 chuyến] dễ lệch xa tỉ
    lệ yêu cầu -- đã thử: HAMIN 30% ra thành 9/19=47%, VILOT 10% ra thành
    0/19=0%). Trả về list đã xáo trộn, dùng qua iterator như pick_type/pick_exit."""
    names = list(weights_dict.keys())
    total_w = sum(weights_dict.values())
    raw = {n: weights_dict[n] / total_w * total_n for n in names}
    floors = {n: int(raw[n]) for n in names}
    remainder = total_n - sum(floors.values())
    order = sorted(names, key=lambda n: raw[n] - floors[n], reverse=True)
    for n in order[:remainder]:
        floors[n] += 1
    pool = []
    for n in names:
        pool += [n] * floors[n]
    random.shuffle(pool)
    return pool


# 6 điểm CRE theo đúng tỉ lệ người dùng yêu cầu (tổng = 100), áp cho
# ARR002-{N_PAIRS} (ARR001 luôn CRE thẳng tại CADAS, không thuộc 6 điểm này).
STAR_WEIGHTS_6PTS = {
    "HAMIN": 30, "SADIN": 20, "VILOT": 10,
    "PAPRA": 15, "BUNTA": 20, "CQ": 5,
}
_star_pool = _quota_pool(STAR_WEIGHTS_6PTS, N_PAIRS - 1)
_star_pool_iter = iter(_star_pool)

def pick_star():
    return next(_star_pool_iter)


def fmt_t(seconds: float) -> str:
    seconds = round(seconds, 2)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


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


def dest_point(lat, lon, bearing_deg_, dist_m):
    """Điểm đến khi đi từ (lat,lon) theo hướng bearing_deg_ một khoảng dist_m
    (bài toán thuận, dùng để tính điểm lùi khi đẩy lùi khỏi bến đỗ)."""
    R = 6371000.0
    br = math.radians(bearing_deg_)
    lat1, lon1 = math.radians(lat), math.radians(lon)
    dr = dist_m / R
    lat2 = math.asin(math.sin(lat1) * math.cos(dr) + math.cos(lat1) * math.sin(dr) * math.cos(br))
    lon2 = lon1 + math.atan2(math.sin(br) * math.sin(dr) * math.cos(lat1),
                              math.cos(dr) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)


def leg_times_s(points_with_spd_kt, start_latlon):
    """points_with_spd_kt: [(lat,lon,spd_kt), ...]. Trả về tổng thời gian (s),
    ước lượng bằng tốc độ trung bình 2 điểm liên tiếp (đủ chính xác cho mục
    đích tính NGƯỢC thời gian xuất phát -- không dùng để ép cứng giờ bay
    thật, vì thời gian bay thật trong engine phụ thuộc BADA/OpenAP)."""
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


def tas_correction(alt_ft):
    """Tốc độ ADDWPT là IAS/CAS (đúng thực tế khai thác), nhưng tốc độ MẶT
    ĐẤT thật (dùng để ƯỚC LƯỢNG thời gian bay) ở độ cao lớn nhanh hơn IAS khá
    nhiều (không khí loãng hơn) -- quy tắc gần đúng chuẩn ~+2%/1000ft. Chỉ
    dùng cho ước lượng lịch xuất phát, KHÔNG đổi tốc độ ADDWPT thật lệnh cho
    tàu bay (vẫn là IAS/CAS đúng khai thác thực tế)."""
    return 1.0 + 0.00002 * max(alt_ft, 0.0)


def estimate_transit_s(chain_with_alt, start_latlon):
    """Như leg_times_s nhưng tự quy đổi IAS->TAS gần đúng theo cao độ từng
    đoạn trước khi tính thời gian -- dùng riêng cho ước lượng NGƯỢC thời gian
    xuất phát tại IAF (đã kiểm chứng qua headless sim: nếu không quy đổi,
    tàu bay ở FL100-140 tới CADAS SỚM hơn ước lượng 150-250s vì bay theo TAS
    thật nhanh hơn IAS coi như tốc độ mặt đất)."""
    legs = [(lat, lon, spd * tas_correction(alt)) for (lat, lon, alt, spd) in chain_with_alt]
    return leg_times_s(legs, start_latlon)


# ================================================================
# 9 PHƯƠNG THỨC STAR RNAV RWY35L/R THẬT của VVDN (AIP AD 2-VVDN-11-7..11,
# AMDT 01/23, trang 1 cập nhật AIRAC 01/26) -- toạ độ + khống chế cao độ/tốc
# độ lấy NGUYÊN VĂN từ mục "3. WAYPOINT LIST" và bảng lộ trình từng STAR
# (đọc trực tiếp từ PDF gốc, đối chiếu khoảng cách charted vs great-circle
# khớp trong 0.5%). Quy đổi: m -> ft (x3.28084), km/h -> kt (x0.539957, làm
# tròn 5kt). "+" = tối thiểu (tại/trên), "-" = tối đa (tại/dưới) theo chart.
#
# 8 STAR còn dùng (BỎ "CQ 2K" theo yêu cầu -- CQ là STAR duy nhất không bay
# qua CADAS, nhập thẳng CADAS, nên loại khỏi danh sách ngẫu nhiên để MỌI
# chuyến ARR002-020 đều bay qua đúng "nút thắt" CADAS, không cần xử lý
# trường hợp riêng).
#
# Điểm IAF của mỗi STAR KHÔNG có ADDWPT riêng -- dùng làm vị trí CRE (spawn)
# trực tiếp. Các điểm còn thiếu khống chế tốc độ trên chart (đa số các đoạn
# xa CADAS) được gán tốc độ ước lượng hợp lý theo cao độ (280kt trên FL100,
# 250kt dưới FL100 -- khớp giới hạn chung "465km/h dưới FL100" ghi trên
# chart, 465*0.539957=251kt≈250kt).
# ================================================================
CADAS = (15.767222, 108.118333)

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
    # -- 2 điểm MỚI cho biến thể 6-điểm/CADAS-3-phút này (xem docstring đầu
    # file để biết nguồn AIP). alt_ft ở đây CHỈ còn vai trò placeholder cho
    # bước ước lượng thời gian bay (estimate_transit_s) -- mực bay CRE thật
    # (FL230/FL240) được GHI ĐÈ riêng ở BƯỚC 1 (xem cadas6_alt_override).
    "CQ": (15.412222, 108.704444, 23500, 280),      # CQ NDB, AIP AD 2-VVDN-11-11 WAYPOINT LIST (15°24'44"N 108°42'16"E)
    "HAMIN": (17.129722, 107.677778, 23500, 280),   # HAMIN, AIP ENR 3.1 (17°07'47"N 107°40'40"E) -- điểm enroute, không phải IAF STAR
}

# (lat, lon, alt_ft, spd_kt) -- nhánh HINTA->DN369->TAWAN->CADAS, dùng chung
# cho HUE/CAHEO/BUNTA (chart cho thấy cả 3 nhập lại tại HINTA).
# SỬA so với _gen_kb5_1hour.py gốc, đối chiếu lại chính chart AD 2-VVDN-11-8
# (bảng TABULAR DESCRIPTION, giống nhau ở cả HUE 2K/CAHEO 2K/BUNTA 2K):
#  - HINTA: bản gốc ghi 15000ft, chart "+2750" = +2750m = 9022ft (tối thiểu).
#  - DN369: bản gốc ghi 12000ft/250kt, chart "-2450 -420" = tối đa 2450m=
#    8038ft VÀ tối đa 420km/h=227kt (làm tròn 225kt theo đúng quy ước 5kt của
#    file) -- 12000ft/250kt đều VƯỢT khống chế tối đa thật.
# File này CHỈ dùng chuỗi qua HAMIN (HUE/CAHEO không nằm trong 6 điểm được
# chọn ở biến thể này), nên sửa tại đây an toàn, không ảnh hưởng chuyến nào
# khác đang hoạt động trong file.
_CHAIN_HINTA_ONWARD = [
    (16.167500, 108.048611, 9022, 280),  # HINTA (+2750m theo AIP, không phải 15000ft như bản gốc)
    (16.020000, 108.081667, 8038, 225),  # DN369 (-2450m/-420km/h theo AIP, không phải 12000ft/250kt như bản gốc)
    (15.854722, 108.105278, 8000, 250),   # TAWAN
    (15.767222, 108.118333, 6070, 250),   # DOTEN
]
# nhánh NOCKA->DN368->VIDAN->CADAS, dùng chung cho KUMUN/SADIN/VILOT/LATOM.
_CHAIN_NOCKA_ONWARD = [
    (15.419444, 108.046667, 16000, 280),  # NOCKA
    (15.585278, 108.022500, 12000, 280),  # DN368
    (15.750833, 107.998611, 8500, 250),   # VIDAN
    (15.767222, 108.118333, 6070, 250),   # DOTEN
]

STAR_CHAINS = {
    "HUE": _CHAIN_HINTA_ONWARD,
    "CAHEO": _CHAIN_HINTA_ONWARD,
    "BUNTA": [
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
    # CQ 2K THẬT (AIP AD 2-VVDN-11-9): CQ -> TAMKY -> ESSEN -> CADAS (không
    # qua TRACO). TAMKY altitude window thật trên chart là "1850m-2450m"
    # ("-2450/+1850") -- chọn CẬN TRÊN +2450m=8038ft (KHÁC quy ước "chọn cận
    # dưới" dùng cho DN452, vì DN452 ở NGỮ CẢNH SID đang LEO cao -- ở đây
    # TAMKY thuộc STAR đang HẠ ĐỘ CAO, nên chọn cận trên mới cho hồ sơ hạ độ
    # cao đơn điệu hợp lý CQ(FL230/240) -> TAMKY(8038) -> ESSEN(8000) ->
    # CADAS(6071); đã kiểm chứng bằng sim thật -- nếu chọn cận dưới (6070,
    # THẤP hơn ESSEN 8000) thì bộ kẹp "giảm độ cao đơn điệu" của
    # make_arr_approach_file_for_pair sẽ tự kẹp ESSEN xuống 6070, XOÁ MẤT giá
    # trị 8000ft thật của ESSEN một cách âm thầm). Không có khống chế tốc độ
    # trên chart tại TAMKY -> 250kt (dưới FL100, đúng quy ước chung của file).
    # ESSEN dùng lại NGUYÊN giá trị (8000ft/225kt) đã có sẵn trong
    # STAR_CHAINS["BUNTA"] ở trên -- cùng 1 điểm thật, đã được gán hợp lý từ trước.
    "CQ": [
        (15.615833, 108.544167, 8038, 250),   # TAMKY
        (15.633889, 108.381667, 8000, 225),   # ESSEN
    ],
    # HAMIN không phải STAR -- ghép đoạn ENR thật (HAMIN->PHULU->CAHEO, xem
    # vietnam_ats_routes.geojson) rồi nối vào đúng chuỗi CAHEO 2K đã có sẵn
    # (_CHAIN_HINTA_ONWARD bắt đầu từ HINTA, ngay sau CAHEO trên chart CAHEO
    # 2K). PHULU alt/spd (14000ft/280kt) dùng lại nguyên giá trị đã có trong
    # generator gốc cho đúng điểm này (ngữ cảnh SID, không khống chế trên
    # chart nên hợp lý dùng chung). CAHEO ở đây lấy đúng khống chế CHARTED
    # tại chính IF của CAHEO 2K ("+FL130"=13000ft), KHÁC với STAR_IAF["CAHEO"]
    # (24000ft) vì đó là độ cao CRE tự chọn khi CAHEO là điểm CRE trực tiếp,
    # còn ở đây CAHEO chỉ là 1 điểm bay QUA giữa đường.
    "HAMIN": [
        (16.694722, 107.888611, 14000, 280),  # PHULU
        (16.536389, 107.965278, 13000, 280),  # CAHEO (bay qua, không CRE tại đây)
    ] + _CHAIN_HINTA_ONWARD,
}

# CADAS: điểm hội tụ đo giãn cách MỚI (thay CADAS) -- toạ độ giữ NGUYÊN như
# trước (đã dùng làm điểm 25NM trong post_doten_legs cũ), vì CADAS là điểm
# chung cho CẢ 8 STAR (7 STAR "2K" cũ qua CADAS->TRACO->CADAS, riêng BUNTA
# "2M" mới qua LINDA->...->ESSEN->CADAS) -- theo yêu cầu đo giãn cách 3 phút
# tại CADAS thay vì CADAS.
CADAS = (15.618056, 108.262500)
_TRACO = (15.601667, 108.142222, 7695, 230)  # nối CADAS -> CADAS, dùng cho 7 STAR "2K" (không đổi so với bản cũ)
_CADAS_PLACEHOLDER = (CADAS[0], CADAS[1], 6071, 225)  # CHỈ dùng để ước lượng thời gian bay (BƯỚC 1) -- tốc độ/cao độ THẬT tại CADAS lấy theo BADA từng loại tàu bay, xem post_cadas_legs()


def _full_pre_cadas_chain(star):
    """Chuỗi toạ độ từ NGAY SAU IAF tới NGAY TRƯỚC CADAS (không gồm CADAS --
    CADAS luôn lấy từ post_cadas_legs() vì tốc độ/cao độ tại đó riêng theo
    BADA từng loại tàu bay VÀ theo phân tầng cadas_alt_ft từng chuyến)."""
    if star in ("BUNTA", "CQ"):
        # BUNTA 2M: tự kết thúc ở ESSEN, ngay trước CADAS.
        # CQ 2K (AIP AD 2-VVDN-11-9): ...->ESSEN->CADAS trực tiếp, KHÔNG qua
        # TRACO -- khác 7 STAR/điểm còn lại (đã kiểm chứng lại đúng bảng
        # TABULAR DESCRIPTION gốc, dòng "040 TF CADAS" nối thẳng từ ESSEN).
        return STAR_CHAINS[star]
    return STAR_CHAINS[star] + [_TRACO]  # còn lại: ...->DOTEN->TRACO->CADAS

# ================================================================
# 8 PHƯƠNG THỨC SID RNAV RWY35L/R THẬT của VVDN (AIP AD 2-VVDN-9-6..9-8,
# AMDT 01/23, cập nhật AIRAC 01/26) -- toạ độ + khống chế cao độ/tốc độ lấy
# NGUYÊN VĂN từ "2. WAYPOINT LIST" + "1. TABULAR DESCRIPTION" (đọc trực tiếp
# từ PDF gốc, đối chiếu khoảng cách charted vs great-circle khớp trong
# 0.22km). Chart chung cho CẢ RWY35L và 35R (không phân biệt), gồm 2 nhánh
# độc lập cùng xuất phát từ 1 điểm leo ban đầu trên tim đường CHC:
#   - Nhánh Bắc qua DN456: PHULU/KONCO/VIDEN (chung DN456->LAIKA->PHULU rồi
#     rẽ), BUNTA (chỉ chung DN456, rẽ riêng qua HOKIN/BINKU).
#   - Nhánh Nam qua DN450: KUMUN/SADIN/XAQUA/PAPRA (chung DN450->DN451->
#     DN452->DN453 rồi rẽ riêng).
# "+"=tối thiểu (tại/trên), "-"=tối đa (tại/dưới) theo chart, đổi m->ft
# (x3.28084). Các đoạn xa (không khống chế cao độ trên chart) được gán cao
# độ/tốc độ leo hợp lý tăng dần (không bịa quá xa thực tế BADA/OpenAP).
# ================================================================
_SID_INITIAL = (16.076637, 108.195656, 1500, 180)  # điểm leo đầu tiên trên tim đường CHC (giữ nguyên như bản cũ)
_SID_DN456 = (16.334167, 108.192500, 8038, 250)     # DN456 -2450m
_SID_DN450 = (16.174444, 108.194722, 4000, 200)     # DN450 (không khống chế cao độ trên chart)

_SID_NORTH_TRUNK = [
    _SID_DN456,
    (16.586667, 108.135278, 11000, 260),   # LAIKA -FL110
    (16.694722, 107.888611, 14000, 280),   # PHULU (không khống chế trên chart)
]
_SID_SOUTH_TRUNK = [
    _SID_DN450,
    (16.177222, 108.387778, 6000, 250),    # DN451 -465km/h(=251kt, dùng 250kt)
    (16.093333, 108.388889, 7054, 240),    # DN452 window -2450m/+2150m, chọn cận dưới +2150m
    (15.909444, 108.391389, 10000, 260),   # DN453 +FL100
]

SID_CHAINS = {
    "PHULU": [_SID_INITIAL] + _SID_NORTH_TRUNK,                                            # DN456->LAIKA->PHULU (kết thúc)
    "KONCO": [_SID_INITIAL] + _SID_NORTH_TRUNK + [
        (16.895833, 107.426944, 18000, 300),   # TRABE
        (17.000000, 107.186944, 21000, 310),   # KONCO
    ],
    "VIDEN": [_SID_INITIAL] + _SID_NORTH_TRUNK + [
        (16.895833, 107.426944, 18000, 300),   # TRABE
        (17.020556, 107.365556, 21000, 310),   # VIDEN
    ],
    "BUNTA": [_SID_INITIAL, _SID_DN456,
        (16.451111, 108.578611, 11000, 260),   # HOKIN -FL110
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
        (15.906944, 108.061944, 18000, 290),   # DN454 +FL180
        (15.905833, 107.931111, 20000, 300),   # DN455
        (15.903333, 107.658889, 21000, 300),   # TANNA
        (15.766667, 107.183333, 22000, 310),   # PAPRA
    ],
}
SID_NAMES = list(SID_CHAINS.keys())


def post_cadas_legs(actype):
    """[(lat,lon,alt_ft,spd_kt), ...] từ CADAS tới ngưỡng
    35L -- tốc độ riêng theo BADA từng loại tàu bay (xem approach_speeds())."""
    s25, s10, s5, std = approach_speeds(actype)
    s_20nm = interp_speed(s25, s10, (25.0 - 19.994) / (25.0 - 10.0))
    s_14_7nm = interp_speed(s25, s10, (25.0 - 14.675) / (25.0 - 10.0))
    s_4_4nm = interp_speed(s5, std, (5.0 - 4.42) / 5.0)
    return [
        (15.618056, 108.262500, 6071, s25),       # CADAS -- mốc 25NM
        (15.700556, 108.250000, 4921, s_20nm),    # MONRY
        (15.788333, 108.237500, 4429, s_14_7nm),  # TAMLA
        (15.865171, 108.224271, 2592, s10),       # mốc 10NM
        (15.947115, 108.212410, 1611, s5),        # mốc 5NM
        (15.957222, 108.210944, 1476, s_4_4nm),
        (16.030133, 108.200372, 0, std),          # ngưỡng 35L
    ]


files = {}  # filename -> content, written at the end


def add_file(name, content):
    files[name] = content


# ================================================================
# TEMPLATE FILES (dùng chung, tham số hoá qua PCALL %0/%1/...)
# ================================================================

add_file("_KB5GEN_STOP_HOLD.scn", """# _KB5GEN_STOP_HOLD.scn — dừng cứng tại 1 điểm bằng MOVE (dùng chung mọi điểm chờ)
# Gọi: PCALL _KB5GEN_STOP_HOLD <acid> <lat> <lon> <hdg>
# LƯU Ý: KHÔNG TAXIOFF ở đây, dù tàu bay đang dừng cứng (LNAV OFF) -- vẫn cần
# giữ trong tập theo dõi của SurfaceTaxiController để các tàu KHÁC đang lăn
# phía sau còn "thấy" và né nó (xem sửa lỗi tương ứng trong surfacetaxi.py:
# plugin đã được sửa để KHÔNG đụng vào selspd của tàu có LNAV OFF, nên không
# còn rủi ro nó tự trôi đi khi đang đứng chờ).
00:00:00.00>%0 LNAV OFF
00:00:00.00>%0 VNAV OFF
00:00:00.00>MOVE %0,%1,%2,0,%3,0.0
""")

add_file("_KB5GEN_STOP_AND_DEL.scn", """# _KB5GEN_STOP_AND_DEL.scn — dừng cứng tại bến đỗ rồi xoá sau 10s
# Gọi: PCALL _KB5GEN_STOP_AND_DEL <acid> <lat> <lon> <hdg>
00:00:00.00>%0 LNAV OFF
00:00:00.00>%0 VNAV OFF
00:00:00.00>MOVE %0,%1,%2,0,%3,0.0
00:00:00.00>PCALL _KB5v2_DEL_AFTER10 %0
""")

# _KB5GEN_ARR_APPROACH_<ARR_ID>.scn — MỘT FILE RIÊNG CHO TỪNG CHUYẾN (không
# còn theo loại tàu bay nữa, vì giờ mỗi chuyến còn phụ thuộc STAR ngẫu nhiên
# được gán) -- ghép [chuỗi STAR thật trước CADAS] + [chuỗi sau CADAS riêng
# theo BADA từng loại]. Sinh trong vòng lặp cặp ARR/DEP ở BƯỚC 1 (cần biết
# "star" đã gán cho từng cặp trước). Xem post_doten_legs()/STAR_CHAINS ở trên.

def make_arr_approach_file_for_pair(p):
    actype = p["arr_type"]
    star = p.get("star")
    post_legs = post_cadas_legs(actype)
    if star is None:
        legs = post_legs[1:]  # ARR001: CRE qua CADAS 2NM, bỏ điểm CADAS để không quay đầu lại
        star_note = f"CRE qua CADAS 2NM (T=0, không qua STAR)"
    elif p.get("cre_override"):
        pre_legs = p["cre_override"]["remaining_nodes"]
        legs = pre_legs + post_legs
        star_note = f"STAR {star} -- CRE tại điểm cắt gần CADAS hơn (bỏ đoạn IAF xa) -> CADAS -> ngưỡng 35L"
    else:
        pre_legs = _full_pre_cadas_chain(star)
        legs = pre_legs + post_legs
        star_note = f"STAR {star} (IAF -> CADAS -> ngưỡng 35L)"
    
    # Bắt buộc giảm độ cao dần (monotonic descent) để tránh lỗi tăng độ cao vô lý
    # Ví dụ: DOTEN(6070) -> TRACO(7695) -> CADAS(6071) sẽ thành 6070 -> 6070 -> 6071(clamped to 6070)
    new_legs = []
    prev_alt = 99999
    for (lat, lon, alt, spd) in legs:
        alt = min(alt, prev_alt)
        new_legs.append((lat, lon, alt, spd))
        prev_alt = alt
    legs = new_legs

    lines_txt = "\n".join(
        f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} {alt} {spd}" for (lat, lon, alt, spd) in legs
    )
    add_file(f"_KB5GEN_ARR_APPROACH_{p['arr_id']}.scn", f"""# _KB5GEN_ARR_APPROACH_{p['arr_id']}.scn — {p['arr_id']} ({actype}) — {star_note}
# Toạ độ/khống chế lấy nguyên văn AIP STAR RNAV, điều chỉnh giãn cách tại CADAS.
# Gọi ngay sau CRE: PCALL _KB5GEN_ARR_APPROACH_{p['arr_id']} <acid>
{lines_txt}
""")


add_file("_KB5GEN_ARR_EXIT_G4.scn", """# _KB5GEN_ARR_EXIT_G4.scn — giảm tốc sau chạm đất, thoát ly khu vực G4, dừng chờ
# Gọi: PCALL _KB5GEN_ARR_EXIT_G4 <acid>  (SAU _KB5GEN_ARR_APPROACH cùng acid)
00:00:00.00>%0 ADDWPT 16.034580,108.199721 0 122
00:00:00.00>%0 ADDWPT 16.039028,108.199071 0 102
00:00:00.00>%0 ADDWPT 16.043475,108.198420 0 75
00:00:00.00>%0 ADDWPT 16.046143,108.198030 0 54
00:00:00.00>%0 ADDWPT 16.047922,108.197769 0 32
00:00:00.00>%0 ADDWPT 16.048687,108.197658 0 10
00:00:00.00>%0 ADDWPT 16.048950,108.198100 0 8
00:00:00.00>%0 ADDWPT 16.0489,108.1986 0 0
00:00:00.00>%0 ADDWPT 16.0489,108.2000 0 8
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST 16.0489,108.1986,0.015 PCALL _KB5GEN_STOP_HOLD %0 16.0489 108.1986 82.0
""")

add_file("_KB5GEN_ARR_EXIT_G6.scn", """# _KB5GEN_ARR_EXIT_G6.scn — giảm tốc sau chạm đất, thoát ly khu vực G6, dừng chờ
# Gọi: PCALL _KB5GEN_ARR_EXIT_G6 <acid>  (SAU _KB5GEN_ARR_APPROACH cùng acid)
00:00:00.00>%0 ADDWPT 16.034580,108.199721 0 128
00:00:00.00>%0 ADDWPT 16.039028,108.199071 0 115
00:00:00.00>%0 ADDWPT 16.043475,108.198420 0 100
00:00:00.00>%0 ADDWPT 16.047922,108.197769 0 83
00:00:00.00>%0 ADDWPT 16.052370,108.197119 0 61
00:00:00.00>%0 ADDWPT 16.055927,108.196598 0 34
00:00:00.00>%0 ADDWPT 16.057199,108.196412 0 10
00:00:00.00>%0 ADDWPT 16.057250,108.196800 0 8
00:00:00.00>%0 ADDWPT 16.0572,108.1974 0 0
00:00:00.00>%0 ADDWPT 16.0572,108.1988 0 8
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST 16.0572,108.1974,0.015 PCALL _KB5GEN_STOP_HOLD %0 16.0572 108.1974 82.0
""")

add_file("_KB5GEN_CROSS_G4.scn", """# _KB5GEN_CROSS_G4.scn — cắt qua 35R từ khu vực G4 về Gate 26
# Gọi: PCALL _KB5GEN_CROSS_G4 <acid>
# LƯU Ý 1: file này luôn được PCALL từ 1 điều kiện ATDIST (của DEP cùng cặp)
# TẠI ĐÚNG lúc tàu bay đích (ARR) đang dừng cứng do STOP_HOLD trước đó (LNAV
# OFF + MOVE, MOVE luôn đặt lại selspd=0). Đã kiểm chứng bằng repro cách ly:
# DELRTE + ADDWPT + LNAV ON + VNAV ON vẫn nạp đúng route/toạ độ mới, NHƯNG
# traf.actwp.spd không được refresh lại từ route mới trong đúng chu kỳ này
# (kẹt ở giá trị sentinel -999), nên VNAV không tự lấy được tốc độ đầu tiên
# -> tàu bay đứng yên vĩnh viễn dù LNAV/route đều đúng. Khắc phục: ép %0 SPD
# lại đúng tốc độ mốc đầu tiên NGAY SAU VNAV ON để "đánh thức" tốc độ.
# LƯU Ý 2: KHÔNG dùng ATDIST để đăng ký điểm dừng cuối (PCALL STOP_AND_DEL)
# như bản cũ -- đã kiểm chứng: đăng ký 1 điều kiện ATDIST MỚI từ BÊN TRONG
# 1 file đang được gọi bởi 1 điều kiện khác (2 tầng điều kiện lồng nhau) bị
# tính sai giá trị "khoảng cách ban đầu", khiến nó kích hoạt SAI ngay lập
# tức (tàu bay bị dừng+xoá giữa đường, chưa kịp lăn hết lộ trình -- đây
# chính là lỗi "ARR006 kẹt không lăn về bến" đã kiểm chứng). Thay bằng mốc
# THỜI GIAN cố định (~150s thật đo được theo tốc độ từng đoạn, dùng dư ra
# 200s cho an toàn) -- lịch theo thời gian không cần đăng ký điều kiện mới,
# không bị lỗi này.
00:00:00.00>%0 DELRTE
00:00:00.00>%0 ADDWPT 16.049068,108.200069 0 15.9
00:00:00.00>%0 ADDWPT 16.049103,108.200334 0 12.1
00:00:00.00>%0 ADDWPT 16.049126,108.200491 0 8.0
00:00:00.00>%0 ADDWPT 16.049149,108.200611 0 4.1
00:00:00.00>%0 ADDWPT 16.049263,108.200888 0 6.0
00:00:00.00>%0 ADDWPT 16.049801,108.200936 0 7.0
00:00:00.00>%0 ADDWPT 16.050431,108.200851 0 8.9
00:00:00.00>%0 ADDWPT 16.052090,108.200611 0 12.1
00:00:00.00>%0 ADDWPT 16.052759,108.200508 0 11.1
00:00:00.00>%0 ADDWPT 16.053155,108.200569 0 8.0
00:00:00.00>%0 ADDWPT 16.053257,108.200936 0 8.9
00:00:00.00>%0 ADDWPT 16.053280,108.201177 0 6.0
00:00:00.00>%0 ADDWPT 16.053349,108.201707 0 5.1
00:00:00.00>%0 ADDWPT 16.053376,108.201881 0 0.0
00:00:00.00>%0 ADDWPT 16.053400,108.202100 0 5.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 SPD 15.9
00:03:20.00>PCALL _KB5GEN_STOP_AND_DEL %0 16.053376 108.201881 82.0
""")

add_file("_KB5GEN_CROSS_G6.scn", """# _KB5GEN_CROSS_G6.scn — cắt qua 35R từ khu vực G6, lăn hướng 82 về Gate 11
# Gọi: PCALL _KB5GEN_CROSS_G6 <acid>
# LƯU Ý: xem giải thích đầy đủ ở _KB5GEN_CROSS_G4.scn -- ép %0 SPD lại ngay
# sau VNAV ON để tránh tàu bay đứng yên vĩnh viễn, và dùng mốc THỜI GIAN cố
# định (~23s thật, dùng dư 45s) thay cho ATDIST để tránh lỗi đăng ký điều
# kiện lồng 2 tầng (kích hoạt sai ngay lập tức, dừng+xoá tàu bay giữa đường).
00:00:00.00>%0 DELRTE
00:00:00.00>%0 ADDWPT 16.057402,108.198639 0 8.0
00:00:00.00>%0 ADDWPT 16.057604,108.199978 0 12.0
00:00:00.00>%0 ADDWPT 16.057809,108.201338 0 0.0
00:00:00.00>%0 ADDWPT 16.057850,108.201800 0 5.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 SPD 8.0
00:00:45.00>PCALL _KB5GEN_STOP_AND_DEL %0 16.057809 108.201338 82.0
""")

add_file("_KB5GEN_DEP_ENTER_RWY.scn", """# _KB5GEN_DEP_ENTER_RWY.scn — nối tiếp từ PRE_HOLD vào đầu 35R
# Gọi: PCALL _KB5GEN_DEP_ENTER_RWY <acid>
# Bỏ DELRTE để tàu bay đang lăn KHÔNG bị cắt ngang lộ trình và bay direct.
# Tàu bay sẽ tự động tiếp tục lăn hoặc đi tiếp từ PRE_HOLD.
00:00:00.00>%0 ADDWPT 16.029181,108.202508 0 5.0
00:00:00.00>%0 ADDWPT 16.029200,108.202500 0 5.0
00:00:00.00>%0 ADDWPT 16.030000,108.202000 0 5.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 SPD 5.0
""")

# _KB5GEN_DEP_ROLL_<DEP_ID>.scn — MỘT FILE RIÊNG CHO TỪNG CHUYẾN (SID ngẫu
# nhiên được gán riêng theo dep, xem "sid" trong pairs ở BƯỚC 1) -- chạy đà
# cất cánh tự nhiên bằng LNAV/VNAV (BADA), bay theo đúng SID RNAV RWY35LR
# thật (SID_CHAINS) thay vì hướng cố định về BUNTA như bản cũ.
def make_dep_roll_file_for_pair(p):
    sid = p["sid"]
    legs = SID_CHAINS[sid]
    lines_txt = "\n".join(
        f"00:00:30.00>%0 ADDWPT {lat:.6f},{lon:.6f} {alt} {spd}" for (lat, lon, alt, spd) in legs
    )
    add_file(f"_KB5GEN_DEP_ROLL_{p['dep_id']}.scn", f"""# _KB5GEN_DEP_ROLL_{p['dep_id']}.scn — chạy đà cất cánh tự nhiên bằng LNAV/VNAV (BADA)
# SID: {sid} (RNAV RWY35LR thật, xem SID_CHAINS trong generator)
# Gọi: PCALL _KB5GEN_DEP_ROLL_{p['dep_id']} <acid>   (từ "ARR... ATALT 0 PCALL ...")
# TAXIOFF ở đây chủ yếu cho DEP001 (chuyến đầu, lăn thẳng ra RWYHOLD, không
# qua _KB5GEN_DEP_ENTER_RWY) -- với DEP002+ thì đã TAXIOFF từ ENTER_RWY rồi,
# gọi lại ở đây là vô hại (không có gì để giải phóng thêm).
00:00:00.00>TAXIOFF %0
00:00:30.00>%0 DELRTE
{lines_txt}
00:00:30.00>%0 LNAV ON
00:00:30.00>%0 VNAV OFF
00:00:30.00>%0 SPD 250
00:00:30.00>%0 VS 2000
00:00:30.00>%0 ALT 10000
00:00:30.00>%0 ATALT 1500 PCALL _KB5GEN_VNAV_ON %0
""")

add_file("_KB5GEN_VNAV_ON.scn", """# _KB5GEN_VNAV_ON.scn — Bật lại VNAV sau khi cất cánh
# Gọi: PCALL _KB5GEN_VNAV_ON <acid>
00:00:00.00>%0 VNAV ON
""")

# _KB5GEN_RUNWAY_CLEARED*.scn ĐÃ BỊ LOẠI BỎ (lỗi thật đã kiểm chứng bằng
# headless sim + repro cách ly): khi 1 điều kiện ATDIST kích hoạt "PCALL fileA
# arg1 arg2" và fileA lại làm "PCALL %0 %1" (PCALL lồng 2 tầng), DELRTE bên
# trong file đích KHÔNG thực thi nếu tàu bay đích đang có route không rỗng
# (route cũ chưa DELRTE) -- lỗi âm thầm, không có echo/error nào, khiến tàu
# bay bị "kẹt" mãi tại điểm dừng cứng trước đó (đây chính là lỗi "ARR006
# không lăn về bến" đã được người dùng báo và kiểm chứng lại). PCALL lồng 1
# tầng (điều kiện -> PCALL trực tiếp file đích) thì luôn hoạt động đúng --
# nên bỏ hẳn lớp trung gian này, gọi {cross_tpl} trực tiếp từ ATDIST (xem
# dưới, dòng "ATDIST 16.0604,...").

# _KB5v2_DEL_AFTER10.scn đã có sẵn (dùng lại nguyên bản, không tạo lại):
#   00:00:10.00>DEL %0

# ================================================================
# 4 biến thể taxi-out (2 gate x 2 đích) -- toạ độ y hệt DEP001/DEP002 gốc
# ================================================================
TAXI_COMMON_G26 = [
    (16.052004, 108.200773, 10.0), (16.051764, 108.200781, 15.0), (16.051560, 108.200776, 15.0),
    (16.051307, 108.200786, 15.0), (16.049490, 108.200986, 15.0), (16.049218, 108.201025, 12.0),
    (16.044100, 108.201789, 18.0), (16.038291, 108.202625, 18.0), (16.030836, 108.203677, 15.0),
    (16.029967, 108.203803, 10.0), (16.029680, 108.203824, 8.0), (16.029490, 108.203744, 6.0),
    (16.029355, 108.203538, 5.0),
]
TAXI_COMMON_G27 = [
    (16.051764, 108.200781, 10.0), (16.051560, 108.200776, 15.0), (16.051307, 108.200786, 15.0),
    (16.049490, 108.200986, 15.0), (16.049218, 108.201025, 12.0), (16.044100, 108.201789, 18.0),
    (16.038291, 108.202625, 18.0), (16.030836, 108.203677, 15.0), (16.029967, 108.203803, 10.0),
    (16.029680, 108.203824, 8.0), (16.029490, 108.203744, 6.0), (16.029355, 108.203538, 5.0),
]

# Toạ độ bến 26/27 lấy theo "Toạ độ sân đỗ VVDN.pdf" (INS coordinates and
# elevation for aircraft stands, © 2022 Cục HKVN) -- bản được CHK VN chấp
# thuận, thay cho toạ độ dò theo KML/vệ tinh trước đây (bến 26 lệch 1.8m,
# bến 27 lệch 15.2m so với bản cũ -- đã kiểm tra qua Bash/haversine).
# Hướng mũi (80.9°) giữ nguyên vì PDF không cho hướng, và khớp với toàn bộ
# các bến khác cùng hàng (theo GeoJSON/apt.dat đã đối chiếu).
GATE26 = (16.052628, 108.201989, 80.9)
GATE27 = (16.052283, 108.202231, 80.9)
RWYHOLD = (16.029200, 108.202500, 352.1)
PREHOLD = (16.029259, 108.203066, 263.0)


def taxi_addwpt_lines(points):
    return "\n".join(f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} 0 {spd}" for lat, lon, spd in points)


def make_taxi_file(name, points, dest, dest_dummy):
    dlat, dlon, dhdg = dest
    # Thay vì dùng STOP_HOLD, ta cho lộ trình kết thúc bằng điểm đích (PRE_HOLD) với tốc độ 0 để tự dừng
    add_file(name, f"""# {name} -- tự sinh, lăn ra PRE_HOLD và dừng tự nhiên
# Gọi ngay sau CRE: PCALL {name} <acid>
{taxi_addwpt_lines(points)}
00:00:00.00>%0 ADDWPT {dlat:.6f},{dlon:.6f} 0 0.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
""")


make_taxi_file("_KB5GEN_TAXI_G26_RWYHOLD.scn", TAXI_COMMON_G26, RWYHOLD, (16.030000, 108.202000, 5.0))
make_taxi_file("_KB5GEN_TAXI_G27_RWYHOLD.scn", TAXI_COMMON_G27, RWYHOLD, (16.030000, 108.202000, 5.0))
make_taxi_file("_KB5GEN_TAXI_G26_PREHOLD.scn", TAXI_COMMON_G26, PREHOLD, (16.029000, 108.202800, 5.0))
make_taxi_file("_KB5GEN_TAXI_G27_PREHOLD.scn", TAXI_COMMON_G27, PREHOLD, (16.029000, 108.202800, 5.0))

# _KB5GEN_PUSHBACK_<GATE>.scn -- đẩy lùi khỏi vị trí đỗ trước khi lăn ra
# đường CHC (theo yêu cầu). BlueSky không mô phỏng động lực học lùi thật, nên
# dùng MOVE (như _KB5GEN_STOP_HOLD) để "kéo" tàu bay lùi ~35m dọc hướng đối
# diện mũi tàu tại bến đỗ (mũi vẫn giữ nguyên hướng bến trong lúc bị kéo lùi,
# đúng thực tế xe kéo không xoay đầu tàu), rồi mới xoay đầu theo hướng đường
# lăn và tiếp tục đúng lộ trình lăn đã định (PCALL %1, tên file taxi truyền
# vào qua tham số %1) -- gọi lại TAXION với chiều dài tàu bay (%2) NGAY TRƯỚC
# PCALL đó, vì MOVE luôn ghi đè traf.selspd về 0 dù speed=0.0.
# Gọi: PCALL _KB5GEN_PUSHBACK_<GATE> <acid> <tên_file_taxi_không_đuôi.scn> <chiều_dài_m>
def make_pushback_file(name, gate, taxi_first_point):
    glat, glon, ghdg = gate
    back_hdg = (ghdg + 180.0) % 360.0
    mid_lat, mid_lon = dest_point(glat, glon, back_hdg, 18.0)
    end_lat, end_lon = dest_point(glat, glon, back_hdg, 35.0)
    taxi_hdg = bearing_deg(end_lat, end_lon, taxi_first_point[0], taxi_first_point[1])
    add_file(name, f"""# {name} — đẩy lùi khỏi vị trí đỗ rồi quay đầu theo hướng đường lăn
# Gọi: PCALL {name} <acid> <tên_file_taxi> <chiều_dài_tàu_bay_m>
# LƯU Ý 1: MOVE với tốc độ khác 0.0 bị BlueSky hiểu nhầm đơn vị (số nhỏ ->
# Mach!) gây tăng tốc phi lý (đã kiểm chứng: "3.0" -> ~Mach 1.5 -> ~1020kt).
# Vì vậy CHỈ dùng 0.0 (dừng cứng tại từng điểm chờ) cho MOVE, giống đúng quy
# ước đã dùng ở _KB5GEN_STOP_HOLD -- việc "đẩy lùi" được thể hiện bằng 2 lần
# dịch vị trí tức thời (snapshot), không phải bay liên tục với tốc độ thật.
# LƯU Ý 2: MOVE (dù speed=0.0) VẪN ghi đè traf.selspd về 0 -- nên phải gọi
# TAXION lại SAU 2 lần MOVE (không phải trước, sẽ bị ghi đè mất) để tàu bay
# thực sự lăn đi khi vào lộ trình taxi (LNAV ON) ngay sau đó.
00:00:00.00>%0 LNAV OFF
00:00:00.00>%0 VNAV OFF
00:00:00.00>MOVE %0,{mid_lat:.6f},{mid_lon:.6f},0,{ghdg},0.0
00:00:05.00>MOVE %0,{end_lat:.6f},{end_lon:.6f},0,{taxi_hdg:.1f},0.0
00:00:07.00>TAXION %0 15 %2
00:00:07.00>PCALL %1 %0
""")


make_pushback_file("_KB5GEN_PUSHBACK_G26.scn", GATE26, TAXI_COMMON_G26[0])
make_pushback_file("_KB5GEN_PUSHBACK_G27.scn", GATE27, TAXI_COMMON_G27[0])

# ================================================================
# FILE KỊCH BẢN CHÍNH -- sinh N cặp ARR/DEP
# ================================================================
lines = []
lines.append(f"""# ================================================================
# KỊCH BẢN 5 -- BIẾN THỂ 6 ĐIỂM/CADAS 3 PHÚT (LẶP LẠI 1 GIỜ, TÀU BAY HỖN HỢP)
# -- KHAI THÁC PHỐI HỢP 35L/35R -- VVDN
#
# Sinh tự động bởi _gen_kb5_1hour_6pts_cadas3min.py (biến thể của
# _gen_kb5_1hour.py), LẶP LẠI đúng chu trình phối hợp đã kiểm chứng trong
# VVDN_KB5_35L35R_2ARR2DEP_v2.scn (touchdown->30s->roll, DEP bay hết đường
# CHC->cho ARR cắt + DEP kế tiếp vào CHC, DELRTE trước mọi lần ADDWPT lại sau
# khi đã MOVE, v.v.) cho {N_PAIRS} cặp ARR/DEP liên tiếp, trải trong ~1 giờ
# (ARR cách nhau {ARR_SPACING_S}s, DEP cách nhau {DEP_SPACING_S}s -- ĐÚNG nhịp độ của
# kịch bản gốc, không đổi).
#
# NGẪU NHIÊN (seed cố định {20260807} để tái tạo được):
#  - Loại tàu bay mỗi chuyến: 70% medium ({', '.join(MEDIUM_TYPES)}),
#    30% heavy ({', '.join(HEAVY_TYPES)}).
#  - Hướng thoát ly của mỗi tàu bay hạ cánh: G4 (về Gate 26) hoặc G6 (về Gate 11), 50/50.
#  - Điểm CRE của mỗi chuyến đến (trừ ARR001): ngẫu nhiên 1 trong 6 điểm theo
#    ĐÚNG tỉ lệ yêu cầu -- HAMIN 30%, SADIN 20%, VILOT 10%, PAPRA 15%,
#    BUNTA 20%, CQ 5% (xem STAR_IAF/STAR_CHAINS trong generator; SADIN/VILOT/
#    PAPRA/BUNTA là 4/9 STAR RNAV RWY35LR thật của VVDN, CQ là STAR RNAV thứ
#    9 -- trước đây bị loại khỏi bản gốc vì không qua TRACO -- HAMIN là 1
#    điểm ATS enroute thật (AIP ENR 3.1), nối vào CAHEO 2K thật qua đúng đoạn
#    đường bay công bố HAMIN->PHULU->CAHEO).
#  - SID của mỗi chuyến đi: ngẫu nhiên 1 trong 8 phương thức SID RNAV
#    RWY35LR thật của VVDN (KONCO/VIDEN/PHULU/BUNTA qua DN456; KUMUN/SADIN/
#    XAQUA/PAPRA qua DN450 -- xem SID_CHAINS trong generator). Không đổi so
#    với bản gốc (yêu cầu chỉ liên quan tàu bay đến).
#
# LUỒNG ĐẾN (ARR) -- MÔ PHỎNG "NÚT THẮT" CADAS THẬT:
#  - ARR001 xuất phát THẲNG tại điểm hội tụ CADAS, ĐÚNG 00:00:00 tuyệt đối
#    (không dịch chuyển kịch bản).
#  - ARR002-{N_PAIRS} được gán ngẫu nhiên 1 trong 6 điểm trên (tỉ lệ nêu trên),
#    CRE tại đúng toạ độ điểm đó, mực bay FL230 hoặc FL240 (ngẫu nhiên, theo
#    yêu cầu), rồi bay theo đúng chuỗi toạ độ+khống chế cao độ/tốc độ THẬT
#    của AIP (AD 2-VVDN STAR RNAV RWY35LR + ENR 3.1 cho đoạn HAMIN, không bịa
#    số liệu) tới CADAS. Thời gian bay điểm CRE->CADAS được ƯỚC LƯỢNG (không
#    ép cứng) để tính NGƯỢC ra thời điểm CRE (spawn), sao cho chuyến đến
#    CADAS cách ARR001 (và các chuyến trước) đúng giãn cách {ARR_SPACING_S}s (3 phút)
#    -- xem thuật toán ở BƯỚC 1.
#  - Từ CADAS tới khi chạm đất, tốc độ (IAS) tại các mốc 25/10/5NM RIÊNG theo
#    BADA của từng loại tàu bay (Vstall cấu hình AP/LD), rải vào đúng 3 dải:
#    200-230kt@25NM, 160-180kt@10NM, 150-160kt@5NM -- thời gian bay THỰC không
#    bị ép, phụ thuộc hoàn toàn vào động lực học BADA/OpenAP của engine.
#  - LƯU Ý VẬT LÝ: cả 6 điểm đều cần nhiều phút bay tới CADAS (HAMIN xa nhất,
#    >20 phút), dài hơn nhiều so với mục tiêu của vài slot ARR rất sớm (ví dụ
#    ARR002 mục tiêu chỉ 150s). Với các slot này, hệ thống tự CẮT BỎ đoạn xa
#    và CRE ngay tại một điểm nội suy TRÊN CHÍNH lộ trình đó (gần CADAS hơn,
#    giữ nguyên cao độ nội suy vật lý, KHÔNG áp FL230/240 vì không còn CRE
#    đúng tại điểm được đặt tên nữa) sao cho thời gian bay còn lại đúng bằng
#    target -- nhờ vậy MỌI chuyến (kể cả các slot rất sớm) đều đạt đúng giãn
#    cách {ARR_SPACING_S}s tại CADAS, không còn trễ (xem truncated_star_spawn()).
#
# ĐƠN GIẢN HOÁ CÓ CHỦ ĐÍCH (khác với kịch bản 2-cặp gốc):
#  - CHỈ dùng lại 2 vị trí đỗ (Gate 26, Gate 27) cho TẤT CẢ {N_PAIRS} chuyến cất
#    cánh, và 2 đích đến (Gate 26 nếu thoát G4, Gate 11 nếu thoát G6) cho TẤT
#    CẢ chuyến hạ cánh -- không dựng thêm lộ trình lăn cho từng gate khác
#    nhau (ngoài phạm vi khả thi của yêu cầu này).
#  - Tàu bay cất cánh ĐẦU TIÊN (DEP001) lăn thẳng ra đầu 35R (không qua
#    PRE_HOLD, vì chưa có ai chiếm đường CHC); TẤT CẢ các chuyến sau đều qua
#    PRE_HOLD rồi xếp hàng chờ chuyến trước bay hết đường CHC mới được vào.
#
# ĐẨY LÙI (PUSHBACK): mỗi DEP, khi tới lượt (giãn cách {DEP_SPACING_S}s giữa 2
# lần đẩy lùi liên tiếp), được CRE đứng yên tại bến rồi PCALL
# _KB5GEN_PUSHBACK_<gate> -- lùi ~35m dọc hướng đối diện mũi tàu (giữ nguyên
# hướng bến trong lúc bị kéo lùi, đúng thực tế xe kéo không xoay đầu), sau đó
# quay đầu theo hướng đường lăn và mới bắt đầu lăn theo lộ trình đã định.
#
# XẾP HÀNG KHÔNG ĐÈ LÊN NHAU (gate -> PRE_HOLD): dùng plugin SURFACETAXI
# (bluesky/plugins/surfacetaxi.py, thuật toán Stop&Go kiểu OpenTaxi, đã có
# sẵn trong engine nhưng trước đây chưa bật). Mỗi DEP được đặt dưới quyền
# điều phối của plugin này (TAXION) ngay khi rời bến -- nếu tàu phía trước
# (ưu tiên hơn, vì gần đích hơn) CHƯA thực sự rời vị trí, tàu sau tự động
# phanh (selspd=0) và giữ khoảng cách tối thiểu = nửa chiều dài 2 tàu +
# {20.0}m đúng tính từ ĐUÔI tàu trước -- không còn hội tụ về đúng 1 toạ độ
# PRE_HOLD cố định như trước (rủi ro chồng lấn nếu 2+ tàu cùng phải chờ).
# Khi được ATC cho vào đường CHC (PCALL _KB5GEN_DEP_ENTER_RWY), TAXIOFF được
# gọi để trả quyền điều khiển tốc độ lại cho chuỗi ADDWPT/LNAV có sẵn (tàu
# TIẾP TỤC ĐÚNG lộ trình đã lập kế hoạch, không đi tắt/direct tới đường CHC).
#
# CẢNH BÁO CỰ LY DEP-ĐÃ-CẤT-CÁNH vs ARR-TRÊN-FINAL: dùng plugin DEPARRALERT
# (bluesky/plugins/dep_arr_final_alert.py) -- mỗi giây kiểm tra MỌI cặp
# (DEP đã rời đất >400ft, ARR đang dưới 3000ft trên final), nếu cự ly ngang
# <3NM thì đánh dấu CẢ HAI "in conflict". KHÔNG bao giờ xét 2 tàu bay đang ở
# mặt đất (cả 2 điều kiện lọc đều yêu cầu đang bay). Ghi thẳng vào
# bs.traf.cd.inconf/tcpamax -- đúng 2 trường mà pipeline ACDATA có sẵn
# (ConflictsPanel + tô màu tàu bay trên bản đồ) đã đọc, nên hiện cảnh báo
# ngay trên UI mà không cần sửa gì ở frontend. An toàn cùng lúc với ASAS OFF
# vì CD method gốc khi OFF không đụng vào 2 mảng này.
# ================================================================

00:00:00.00>PLUGINS LOAD SURFACETAXI
00:00:00.00>PLUGINS LOAD DEPARRALERT
00:00:00.00>TRAILS ON
00:00:00.00>ASAS OFF
00:00:00.00>PAN 16.0400,108.2000
""")

# ================================================================
# BƯỚC 1: sinh lịch trình + THUẬT TOÁN TÍNH NGƯỢC THỜI GIAN XUẤT PHÁT (spawn)
# tại IAF của 8 STAR thật (đã bỏ CQ 2K), để MỌI chuyến đến "nút thắt" CADAS
# đúng giãn cách ARR_SPACING_S (2 phút 30 giây) TÍNH TỪ MỐC ARR001 TẠI CADAS
# LÚC 00:00:00 -- KHÔNG dịch chuyển cả dây chuyền (ARR001 luôn ở đúng T=0
# tuyệt đối trong kịch bản, không phải mốc tương đối rồi dịch như bản trước).
#
#     target_CADAS_time[i] = (i-1) * ARR_SPACING_S        (i=1 -> 0, đúng T=0)
#     spawn_time[i]         = target_CADAS_time[i] - thời_gian_bay_ước_lượng(IAF -> CADAS)
#
# thời_gian_bay_ước_lượng dùng CHÍNH toạ độ+tốc độ thật của STAR đó (không
# bịa) qua estimate_transit_s() -- CHỈ dùng để tính lịch xuất phát, KHÔNG ép
# cứng thời gian bay thật trong engine (BlueSky tự bay theo BADA/OpenAP).
#
# LƯU Ý VẬT LÝ: cả 8 STAR đều xa hơn 9 phút bay tới CADAS (STAR gần nhất
# CAHEO ~565s) -- nghĩa là với các slot ARR RẤT SỚM (i nhỏ, ví dụ ARR002 mục
# tiêu chỉ 150s), bay từ đúng IAF sẽ luôn quá trễ so với giãn cách quy định.
#
# GIẢI PHÁP: STAR vẫn được chọn NGẪU NHIÊN hoàn toàn trong 8 STAR (đúng như
# yêu cầu gốc). Nếu bay từ IAF vẫn kịp target (transit đầy đủ <= target) thì
# CRE tại chính IAF như trước. Nếu KHÔNG kịp, CRE tại một điểm NẰM TRÊN CHÍNH
# STAR đó (nội suy giữa 2 waypoint kế nhau của STAR) sao cho thời gian bay
# CÒN LẠI từ điểm đó tới CADAS đúng bằng target_cadas_t -- tức "bỏ qua đoạn
# xa" của STAR (đoạn IAF -> điểm nội suy), chỉ giữ lại đoạn gần CADAS hơn.
# Nhờ vậy MỌI chuyến (kể cả các slot rất sớm) đều đạt đúng giãn cách quy định
# tại CADAS, không còn trễ, mà vẫn dùng toạ độ/tốc độ thật của STAR (không bịa).
# ================================================================
_STAR_TRANSIT = {
    name: estimate_transit_s(_full_pre_cadas_chain(name) + [_CADAS_PLACEHOLDER], (STAR_IAF[name][0], STAR_IAF[name][1]))
    for name in STAR_IAF
}


def _star_nodes(star):
    iaf_lat, iaf_lon, iaf_alt, iaf_spd = STAR_IAF[star]
    return [(iaf_lat, iaf_lon, iaf_alt, iaf_spd)] + _full_pre_cadas_chain(star) + [_CADAS_PLACEHOLDER]


def _remaining_transit_per_node(nodes):
    """remaining[j] = thời gian bay ước lượng (TAS-corrected) từ nodes[j] tới
    nodes[-1] (luôn là CADAS) -- remaining[-1] = 0, remaining[0] = transit đầy đủ."""
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


pairs = []
for i in range(1, N_PAIRS + 1):
    arr_id = f"ARR{i:03d}"
    dep_id = f"DEP{i:03d}"
    dep_t = (i - 1) * DEP_SPACING_S
    exit_choice = pick_exit()
    arr_type = pick_type()
    dep_type = pick_type()
    sid = random.choice(SID_NAMES)
    gate = GATE26 if i % 2 == 1 else GATE27
    gate_name = "G26" if i % 2 == 1 else "G27"

    T_ADVANCE_S = 36
    target_cadas_t = (i - 1) * ARR_SPACING_S - T_ADVANCE_S
    cre_override = None
    cadas6_alt_override = None
    if i == 1:
        star = None
        arr_t = 0.0               # ARR001: CRE thẳng tại CADAS, đúng T=0 tuyệt đối
        transit_est_s = 0.0
    else:
        # Rút từ pool đã phân bổ đúng tỉ lệ (xem _quota_pool/_star_pool ở trên) --
        # KHÔNG dùng random.choices độc lập từng chuyến (mẫu 19 chuyến quá nhỏ,
        # dễ lệch xa tỉ lệ yêu cầu).
        star = pick_star()
        full_transit = _STAR_TRANSIT[star]
        if full_transit <= target_cadas_t:
            transit_est_s = full_transit
            arr_t = target_cadas_t - transit_est_s   # CRE tại điểm thật như cũ, vẫn kịp target
            # Mực bay FL230/FL240 (theo yêu cầu) CHỈ áp khi CRE ĐÚNG TẠI điểm
            # thật -- đây là trường hợp đó (tàu bay thực sự "xuất hiện tại"
            # HAMIN/SADIN/VILOT/PAPRA/BUNTA/CQ, không phải điểm nội suy).
            cadas6_alt_override = random.choice([23000, 24000])
        else:
            lat, lon, alt, spd, hdg, remaining_nodes = truncated_star_spawn(star, target_cadas_t)
            cre_override = {"lat": lat, "lon": lon, "alt": alt, "spd": spd, "hdg": hdg,
                             "remaining_nodes": remaining_nodes}
            transit_est_s = target_cadas_t
            arr_t = 0.0                               # CRE ngay T=0 tại điểm gần CADAS hơn trên chính STAR
            # KHÔNG áp FL230/240 ở đây: slot quá sớm, tàu bay CRE tại 1 điểm
            # nội suy gần CADAS hơn nhiều (không phải HAMIN/SADIN/... thật),
            # giữ nguyên cao độ nội suy vật lý hợp lý từ truncated_star_spawn.

    pairs.append({
        "i": i, "arr_id": arr_id, "dep_id": dep_id, "arr_t": arr_t, "dep_t": dep_t,
        "exit": exit_choice, "arr_type": arr_type, "dep_type": dep_type, "sid": sid,
        "gate": gate, "gate_name": gate_name, "star": star,
        "target_cadas_t": target_cadas_t, "transit_est_s": transit_est_s,
        "cre_override": cre_override, "cadas6_alt_override": cadas6_alt_override,
    })

for p in pairs:
    make_arr_approach_file_for_pair(p)
    make_dep_roll_file_for_pair(p)
    if p["star"]:
        expected_cadas_t = p["arr_t"] + p["transit_est_s"]
        late_by = expected_cadas_t - p["target_cadas_t"]
        flag = f"  *** LỆCH {late_by:.0f}s so với mục tiêu ***" if abs(late_by) > 1.0 else ""
        origin = "điểm CẮT GẦN CADAS hơn (bỏ đoạn xa)" if p["cre_override"] else "IAF đầy đủ"
        print(f"[debug] {p['arr_id']}: STAR={p['star']:6s} CRE tại {origin}, mục tiêu CADAS="
              f"{p['target_cadas_t']:.0f}s, spawn={p['arr_t']:.0f}s, CADAS dự kiến={expected_cadas_t:.0f}s{flag}")

for p in pairs:
    i = p["i"]
    arr_t_s = fmt_t(p["arr_t"])
    dep_t_s = fmt_t(p["dep_t"])
    glat, glon, ghdg = p["gate"]
    is_first_dep = (i == 1)
    taxi_tpl = f"_KB5GEN_TAXI_{p['gate_name']}_{'RWYHOLD' if is_first_dep else 'PREHOLD'}.scn".replace(".scn", "")
    cross_tpl = f"_KB5GEN_CROSS_{p['exit']}"
    exit_tpl = f"_KB5GEN_ARR_EXIT_{p['exit']}"

    if i < N_PAIRS:
        next_dep_id = pairs[i]["dep_id"]
        roll_trigger = f"{dep_t_s}>{p['dep_id']} ATDIST 16.030100,108.202372,0.025 PCALL _KB5GEN_DEP_ENTER_RWY {next_dep_id}"
    else:
        roll_trigger = f"# Không còn chuyến khởi hành nào sau {p['dep_id']}"

    if p["star"] is None:
        f = 0.4035
        lat = 15.618056 + f * (15.700556 - 15.618056)
        lon = 108.262500 + f * (108.250000 - 108.262500)
        alt = 6071.0 + f * (4921.0 - 6071.0)
        arr_cre_lat, arr_cre_lon, arr_cre_alt, arr_cre_spd, arr_cre_hdg = lat, lon, round(alt), 230, 353
        arr_origin_note = f"CRE qua CADAS 2NM cao độ {round(alt)}ft"
    elif p.get("cre_override"):
        co = p["cre_override"]
        arr_cre_lat, arr_cre_lon, arr_cre_alt, arr_cre_spd, arr_cre_hdg = co["lat"], co["lon"], co["alt"], co["spd"], co["hdg"]
        arr_origin_note = (f"CRE trên STAR {p['star']} tại điểm gần CADAS hơn (bỏ đoạn IAF xa) -- "
                            f"khớp đúng target {p['target_cadas_t']:.0f}s")
    else:
        arr_cre_lat, arr_cre_lon, arr_cre_alt, arr_cre_spd = STAR_IAF[p["star"]]
        if p.get("cadas6_alt_override") is not None:
            arr_cre_alt = p["cadas6_alt_override"]  # FL230/FL240 theo yêu cầu, ghi đè placeholder
        _first_lat, _first_lon, _first_alt, _first_spd = STAR_CHAINS[p["star"]][0]
        arr_cre_hdg = round(bearing_deg(arr_cre_lat, arr_cre_lon, _first_lat, _first_lon), 1)
        arr_origin_note = (f"CRE tại {p['star']} (bay ~{p['transit_est_s']:.0f}s ước lượng tới CADAS, "
                            f"FL{round(arr_cre_alt/100):03d})")

    lines.append(f"""
# ================================================================
# CẶP {i}/{N_PAIRS}: {p['arr_id']} ({p['arr_type']}, thoát ly {p['exit']}, {arr_origin_note}) + {p['dep_id']} ({p['dep_type']}, {p['gate_name']}, SID {p['sid']}{'  -- lăn thẳng ra 35R (chuyến đầu)' if is_first_dep else ' -- qua PRE_HOLD, xếp hàng'})
# ================================================================
{dep_t_s}>CRE {p['dep_id']},{p['dep_type']},{glat},{glon},{ghdg},0,0
{dep_t_s}>PCALL _KB5GEN_PUSHBACK_{p['gate_name']} {p['dep_id']} {taxi_tpl} {aircraft_length_m(p['dep_type']):.1f}
{roll_trigger}
{dep_t_s}>{p['dep_id']} ATDIST 16.0604,108.1980,0.15 PCALL {cross_tpl} {p['arr_id']}

{arr_t_s}>CRE {p['arr_id']},{p['arr_type']},{arr_cre_lat},{arr_cre_lon},{arr_cre_hdg},{arr_cre_alt},{arr_cre_spd}
{arr_t_s}>PCALL _KB5GEN_ARR_APPROACH_{p['arr_id']} {p['arr_id']}
{arr_t_s}>PCALL {exit_tpl} {p['arr_id']}
{arr_t_s}>{p['arr_id']} ATALT 0 PCALL _KB5GEN_DEP_ROLL_{p['dep_id']} {p['dep_id']}
""")

main_content = "\n".join(lines)
add_file("VVDN_KB5_1HOUR_6PTS_CADAS3MIN.scn", main_content)

# QUAN TRỌNG: backup TRƯỚC khi ghi đè -- backup phải lưu lại bản CŨ (kịch bản
# của lần chạy TRƯỚC, đang tồn tại trên đĩa) trước khi bị ghi đè bởi bản MỚI
# sắp sinh ra, không phải lưu lại bản MỚI sau khi đã ghi đè (như lỗi cũ, khiến
# không bao giờ tìm lại được bản trước đó -- mọi backup chỉ là bản sao của
# chính bản mới nhất). Nếu đây là lần chạy đầu tiên (chưa có file cũ), hàm tự
# bỏ qua các file không tồn tại, không lỗi.
# _KB5v2_DEL_AFTER10.scn: bản gốc dùng lại nguyên file đã có sẵn tại
# scenario/ gốc (không tự tạo lại), NHƯNG PCALL chỉ tìm file CÙNG thư mục với
# kịch bản đang chạy -- OUT_DIR của biến thể này là 1 thư mục HOÀN TOÀN MỚI
# (không phải scenario/ gốc, không phải Backup/ của _gen_kb5_1hour.py), nên
# PHẢI tự sinh file này vào ĐÂY, nếu không mọi lần DEL sau khi tàu bay hạ cánh
# xong sẽ lỗi "File not found" (đã kiểm chứng thật bằng headless sim -- lỗi
# xảy ra đúng 20/20 lần, 1 lần/chuyến, không ảnh hưởng thời điểm CADAS vì xảy
# ra SAU khi hạ cánh, nhưng khiến tàu bay không được dọn dẹp khỏi bến đỗ).
add_file("_KB5v2_DEL_AFTER10.scn", """# _KB5v2_DEL_AFTER10.scn — dùng chung, gọi bằng "PCALL _KB5v2_DEL_AFTER10 <ACID>"
# %0 được PCALL thay bằng acid truyền vào. Timestamp 10.00 (REL) = xoá tàu
# bay đúng 10 giây sau khi file này được gọi (tức 10s sau khi tàu bay đến vị
# trí đỗ).
00:00:10.00>DEL %0
""")
# backup disabled for this run

for fname, content in files.items():
    with open(f"{OUT_DIR}/{fname}", "w", encoding="utf-8") as f:
        f.write(content)

print(f"Đã sinh {len(files)} file trong {OUT_DIR}/")
print("Danh sách cặp:")
for p in pairs:
    print(f"  {p['i']:2d}. ARR t={fmt_t(p['arr_t'])} {p['arr_id']}({p['arr_type']},{p['exit']})  "
          f"DEP t={fmt_t(p['dep_t'])} {p['dep_id']}({p['dep_type']},{p['gate_name']})")
