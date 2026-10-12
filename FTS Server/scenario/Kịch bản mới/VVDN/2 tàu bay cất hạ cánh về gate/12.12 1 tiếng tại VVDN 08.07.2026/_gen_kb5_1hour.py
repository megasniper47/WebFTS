"""
Generator cho kịch bản VVDN_KB5_1HOUR_MIXED.scn — lặp lại chu trình phối hợp
35L/35R (ARR003_35L35R_2ARR2DEP_v2) cho N cặp ARR/DEP liên tiếp trong 1 giờ,
với loại tàu bay ngẫu nhiên (70% medium / 30% heavy) và hướng thoát ly ngẫu
nhiên (G4/G6) cho mỗi tàu bay hạ cánh.

Toạ độ/vật lý dùng lại NGUYÊN VẸN từ VVDN_KB5_35L35R_2ARR2DEP_v2.scn (đã kiểm
chứng chạy đúng qua nhiều lượt sửa lỗi) — không tự bịa số liệu mới, chỉ tái
cấu trúc thành template dùng chung (PCALL %0/%1/... ) để không phải lặp lại
hàng trăm dòng ADDWPT cho từng tàu bay.

Chạy: py _gen_kb5_1hour.py
"""
import random

random.seed(20260807)  # cố định để tái tạo được cùng kịch bản khi cần

OUT_DIR = "."

N_PAIRS = 20
ARR_SPACING_S = 180  # 3 phút, giữ đúng như kịch bản gốc
DEP_SPACING_S = 150  # 2 phút 30 giây, giữ đúng như kịch bản gốc

MEDIUM_TYPES = ["A320", "A321", "A20N", "A21N", "B738", "B38M", "B739", "E190"]
HEAVY_TYPES = ["A332", "A333", "A359", "B744", "B763", "B772", "B773", "B77W", "B788", "B789", "B748", "B78X"]


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


def fmt_t(seconds: float) -> str:
    seconds = round(seconds, 2)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


files = {}  # filename -> content, written at the end


def add_file(name, content):
    files[name] = content


# ================================================================
# TEMPLATE FILES (dùng chung, tham số hoá qua PCALL %0/%1/...)
# ================================================================

add_file("_KB5GEN_STOP_HOLD.scn", """# _KB5GEN_STOP_HOLD.scn — dừng cứng tại 1 điểm bằng MOVE (dùng chung mọi điểm chờ)
# Gọi: PCALL _KB5GEN_STOP_HOLD <acid> <lat> <lon> <hdg>
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

add_file("_KB5GEN_ARR_APPROACH.scn", """# _KB5GEN_ARR_APPROACH.scn — DOTEN -> STAR chung 35L/R -> IAP ILS V 35L -> chạm 35L
# Gọi ngay sau CRE: PCALL _KB5GEN_ARR_APPROACH <acid>
# Toạ độ/độ cao/tốc độ y hệt VVDN_KB5_35L35R_2ARR2DEP_v2.scn (DOTEN ở FL100 chung
# cho mọi tàu bay trong kịch bản lặp -- không phân tầng riêng theo cặp như bản 2-cặp).
00:00:00.00>%0 ADDWPT 15.601667,108.142222 7695 230
00:00:00.00>%0 ADDWPT 15.618056,108.262500 6071 220
00:00:00.00>%0 ADDWPT 15.700556,108.250000 4921 210
00:00:00.00>%0 ADDWPT 15.788333,108.237500 4429 200
00:00:00.00>%0 ADDWPT 15.873556,108.223083 2592 180
00:00:00.00>%0 ADDWPT 15.947115,108.212410 1611 160
00:00:00.00>%0 ADDWPT 15.957222,108.210944 1476 155
00:00:00.00>%0 ADDWPT 16.030133,108.200372 0 140
""")

add_file("_KB5GEN_ARR_EXIT_G4.scn", """# _KB5GEN_ARR_EXIT_G4.scn — giảm tốc sau chạm đất, thoát ly khu vực G4, dừng chờ
# Gọi: PCALL _KB5GEN_ARR_EXIT_G4 <acid>  (SAU _KB5GEN_ARR_APPROACH cùng acid)
00:00:00.00>%0 ADDWPT 16.034580,108.199721 0 122
00:00:00.00>%0 ADDWPT 16.039028,108.199071 0 102
00:00:00.00>%0 ADDWPT 16.043475,108.198420 0 75
00:00:00.00>%0 ADDWPT 16.046143,108.198030 0 54
00:00:00.00>%0 ADDWPT 16.047922,108.197769 0 32
00:00:00.00>%0 ADDWPT 16.048687,108.197658 0 15
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
00:00:00.00>%0 ADDWPT 16.057199,108.196412 0 15
00:00:00.00>%0 ADDWPT 16.057250,108.196800 0 8
00:00:00.00>%0 ADDWPT 16.0572,108.1974 0 0
00:00:00.00>%0 ADDWPT 16.0572,108.1988 0 8
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST 16.0572,108.1974,0.015 PCALL _KB5GEN_STOP_HOLD %0 16.0572 108.1974 82.0
""")

add_file("_KB5GEN_CROSS_G4.scn", """# _KB5GEN_CROSS_G4.scn — cắt qua 35R từ khu vực G4 về Gate 26
# Gọi: PCALL _KB5GEN_CROSS_G4 <acid>
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
00:00:00.00>%0 ATDIST 16.053376,108.201881,0.01 PCALL _KB5GEN_STOP_AND_DEL %0 16.053376 108.201881 82.0
""")

add_file("_KB5GEN_CROSS_G6.scn", """# _KB5GEN_CROSS_G6.scn — cắt qua 35R từ khu vực G6, lăn hướng 82 về Gate 11
# Gọi: PCALL _KB5GEN_CROSS_G6 <acid>
00:00:00.00>%0 DELRTE
00:00:00.00>%0 ADDWPT 16.057402,108.198639 0 8.0
00:00:00.00>%0 ADDWPT 16.057604,108.199978 0 12.0
00:00:00.00>%0 ADDWPT 16.057809,108.201338 0 0.0
00:00:00.00>%0 ADDWPT 16.057850,108.201800 0 5.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST 16.057809,108.201338,0.02 PCALL _KB5GEN_STOP_AND_DEL %0 16.057809 108.201338 82.0
""")

add_file("_KB5GEN_DEP_ENTER_RWY.scn", """# _KB5GEN_DEP_ENTER_RWY.scn — lăn từ PRE_HOLD vào đầu 35R
# Gọi: PCALL _KB5GEN_DEP_ENTER_RWY <acid>
00:00:00.00>%0 DELRTE
00:00:00.00>%0 ADDWPT 16.029181,108.202508 0 5.0
00:00:00.00>%0 ADDWPT 16.0292,108.2025 0 0.0
00:00:00.00>%0 ADDWPT 16.030000,108.202000 0 5.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST 16.029200,108.202500,0.01 PCALL _KB5GEN_STOP_HOLD %0 16.029200 108.202500 352.1
""")

add_file("_KB5GEN_DEP_ROLL.scn", """# _KB5GEN_DEP_ROLL.scn — chạy đà + leo + SID BUNTA 2G (30s sau khi ARR cặp mình chạm đất)
# Gọi: PCALL _KB5GEN_DEP_ROLL <acid>   (từ "ARR... ATALT 0 PCALL ...")
00:00:30.00>%0 LNAV OFF
00:00:30.00>%0 VNAV OFF
00:00:30.00>MOVE %0,16.029200,108.202500,0,352.1,0.0
00:00:38.00>MOVE %0,16.029573,108.202446,0,352.1,20.4
00:00:46.00>MOVE %0,16.030690,108.202285,0,352.1,40.7
00:00:54.00>MOVE %0,16.032553,108.202016,0,352.1,61.0
00:01:02.00>MOVE %0,16.035159,108.201640,0,352.1,81.4
00:01:10.00>MOVE %0,16.038514,108.201155,0,352.1,101.7
00:01:18.00>MOVE %0,16.042616,108.200563,0,352.1,122.0
00:01:26.00>MOVE %0,16.047469,108.199862,0,352.1,142.4
00:01:29.00>MOVE %0,16.049442,108.199582,0,352.1,150.0
00:01:38.00>MOVE %0,16.055778,108.198667,375,352.1,157.5
00:01:47.00>MOVE %0,16.062422,108.197708,750,352.1,165.0
00:01:56.00>MOVE %0,16.069382,108.196704,1125,352.1,172.5
00:02:05.00>MOVE %0,16.076637,108.195656,1500,352.1,180.0
00:02:05.00>%0 DELRTE
00:02:05.00>%0 ADDWPT 16.334167,108.192500 7500 250
00:02:05.00>%0 ADDWPT 16.451111,108.578611 10500 280
00:02:05.00>%0 ADDWPT 16.559722,108.973056 24000 310
00:02:05.00>%0 ADDWPT 16.833333,109.395000 34000 320
00:02:05.00>%0 LNAV ON
00:02:05.00>%0 VNAV ON
""")

add_file("_KB5GEN_RUNWAY_CLEARED.scn", """# _KB5GEN_RUNWAY_CLEARED.scn — DEP đã bay hết đường CHC 35R:
# cho ARR cặp mình cắt 35R (theo template G4/G6) VÀ cho DEP kế tiếp vào 35R.
# Gọi: PCALL _KB5GEN_RUNWAY_CLEARED <cross_template> <arr_acid> <next_dep_acid>
00:00:00.00>PCALL %0 %1
00:00:00.00>PCALL _KB5GEN_DEP_ENTER_RWY %2
""")

add_file("_KB5GEN_RUNWAY_CLEARED_LAST.scn", """# _KB5GEN_RUNWAY_CLEARED_LAST.scn — như trên nhưng không còn DEP kế tiếp để gọi
# (dùng cho cặp cuối cùng trong kịch bản)
# Gọi: PCALL _KB5GEN_RUNWAY_CLEARED_LAST <cross_template> <arr_acid>
00:00:00.00>PCALL %0 %1
""")

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
    (16.029355, 108.203538, 5.0), (16.029272, 108.203047, 5.0), (16.029181, 108.202508, 5.0),
]
TAXI_COMMON_G27 = [
    (16.051764, 108.200781, 10.0), (16.051560, 108.200776, 15.0), (16.051307, 108.200786, 15.0),
    (16.049490, 108.200986, 15.0), (16.049218, 108.201025, 12.0), (16.044100, 108.201789, 18.0),
    (16.038291, 108.202625, 18.0), (16.030836, 108.203677, 15.0), (16.029967, 108.203803, 10.0),
    (16.029680, 108.203824, 8.0), (16.029490, 108.203744, 6.0), (16.029355, 108.203538, 5.0),
]

GATE26 = (16.052622, 108.201973, 80.9)
GATE27 = (16.052259, 108.202091, 80.9)
RWYHOLD = (16.029200, 108.202500, 352.1)
PREHOLD = (16.029259, 108.203066, 263.0)


def taxi_addwpt_lines(points):
    return "\n".join(f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} 0 {spd}" for lat, lon, spd in points)


def make_taxi_file(name, points, dest, dest_dummy):
    dlat, dlon, dhdg = dest
    dumlat, dumlon, dumspd = dest_dummy
    add_file(name, f"""# {name} -- tự sinh, toạ độ y hệt taxi-out gốc trong VVDN_KB5_35L35R_2ARR2DEP_v2
# Gọi ngay sau CRE: PCALL {name} <acid>
{taxi_addwpt_lines(points)}
00:00:00.00>%0 ADDWPT {dumlat:.6f},{dumlon:.6f} 0 {dumspd}
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST {dlat:.6f},{dlon:.6f},0.01 PCALL _KB5GEN_STOP_HOLD %0 {dlat:.6f} {dlon:.6f} {dhdg}
""")


make_taxi_file("_KB5GEN_TAXI_G26_RWYHOLD.scn", TAXI_COMMON_G26, RWYHOLD, (16.030000, 108.202000, 5.0))
make_taxi_file("_KB5GEN_TAXI_G27_RWYHOLD.scn", TAXI_COMMON_G27, RWYHOLD, (16.030000, 108.202000, 5.0))
make_taxi_file("_KB5GEN_TAXI_G26_PREHOLD.scn", TAXI_COMMON_G26, PREHOLD, (16.029000, 108.202800, 5.0))
make_taxi_file("_KB5GEN_TAXI_G27_PREHOLD.scn", TAXI_COMMON_G27, PREHOLD, (16.029000, 108.202800, 5.0))

# ================================================================
# FILE KỊCH BẢN CHÍNH -- sinh N cặp ARR/DEP
# ================================================================
lines = []
lines.append(f"""# ================================================================
# KỊCH BẢN 5 (LẶP LẠI 1 GIỜ, TÀU BAY HỖN HỢP) -- KHAI THÁC PHỐI HỢP 35L/35R -- VVDN
#
# Sinh tự động bởi _gen_kb5_1hour.py, LẶP LẠI đúng chu trình phối hợp đã kiểm
# chứng trong VVDN_KB5_35L35R_2ARR2DEP_v2.scn (touchdown->30s->roll, DEP bay
# hết đường CHC->cho ARR cắt + DEP kế tiếp vào CHC, DELRTE trước mọi lần
# ADDWPT lại sau khi đã MOVE, v.v.) cho {N_PAIRS} cặp ARR/DEP liên tiếp, trải
# trong ~1 giờ (ARR cách nhau {ARR_SPACING_S}s, DEP cách nhau {DEP_SPACING_S}s -- ĐÚNG
# nhịp độ của kịch bản gốc, không đổi).
#
# NGẪU NHIÊN (seed cố định {20260807} để tái tạo được):
#  - Loại tàu bay mỗi chuyến: 70% medium ({', '.join(MEDIUM_TYPES)}),
#    30% heavy ({', '.join(HEAVY_TYPES)}).
#  - Hướng thoát ly của mỗi tàu bay hạ cánh: G4 (về Gate 26) hoặc G6 (về Gate 11), 50/50.
#
# ĐƠN GIẢN HOÁ CÓ CHỦ ĐÍCH (khác với kịch bản 2-cặp gốc):
#  - DOTEN dùng 1 mức FL100 (10000ft) chung cho MỌI tàu bay (kịch bản gốc
#    dùng FL090/FL110 riêng cho ARR001/ARR002 để phân tầng 2 chuyến cụ thể --
#    không còn ý nghĩa khi có {N_PAIRS} chuyến nối tiếp cùng 1 trục tiếp cận).
#  - Tốc độ kiểm soát tiếp cận (25/10/5NM) dùng giá trị AN TOÀN CHUNG cho cả
#    medium và heavy (180kt@10NM, 160kt@5NM) thay vì tách riêng theo loại --
#    vì mỗi chuyến giờ có loại ngẫu nhiên, không biết trước để tách khi sinh
#    template chung.
#  - CHỈ dùng lại 2 vị trí đỗ (Gate 26, Gate 27) cho TẤT CẢ {N_PAIRS} chuyến cất
#    cánh, và 2 đích đến (Gate 26 nếu thoát G4, Gate 11 nếu thoát G6) cho TẤT
#    CẢ chuyến hạ cánh -- không dựng thêm lộ trình lăn cho từng gate khác
#    nhau (ngoài phạm vi khả thi của yêu cầu này).
#  - Tàu bay cất cánh ĐẦU TIÊN (DEP001) lăn thẳng ra đầu 35R (không qua
#    PRE_HOLD, vì chưa có ai chiếm đường CHC); TẤT CẢ các chuyến sau đều qua
#    PRE_HOLD rồi xếp hàng chờ chuyến trước bay hết đường CHC mới được vào.
# ================================================================

00:00:00.00>TRAILS ON
00:00:00.00>ASAS OFF
00:00:00.00>PAN 16.0400,108.2000
""")

pairs = []
for i in range(1, N_PAIRS + 1):
    arr_id = f"ARR{i:03d}"
    dep_id = f"DEP{i:03d}"
    arr_t = (i - 1) * ARR_SPACING_S
    dep_t = (i - 1) * DEP_SPACING_S
    exit_choice = random.choice(["G4", "G6"])
    arr_type = pick_type()
    dep_type = pick_type()
    gate = GATE26 if i % 2 == 1 else GATE27
    gate_name = "G26" if i % 2 == 1 else "G27"
    pairs.append({
        "i": i, "arr_id": arr_id, "dep_id": dep_id, "arr_t": arr_t, "dep_t": dep_t,
        "exit": exit_choice, "arr_type": arr_type, "dep_type": dep_type,
        "gate": gate, "gate_name": gate_name,
    })

for p in pairs:
    i = p["i"]
    arr_t_s = fmt_t(p["arr_t"])
    dep_t_s = fmt_t(p["dep_t"])
    glat, glon, ghdg = p["gate"]
    is_first_dep = (i == 1)
    taxi_tpl = f"_KB5GEN_TAXI_{p['gate_name']}_{'RWYHOLD' if is_first_dep else 'PREHOLD'}.scn".replace(".scn", "")
    cross_tpl = f"_KB5GEN_CROSS_{p['exit']}"
    exit_tpl = f"_KB5GEN_ARR_EXIT_{p['exit']}"

    if i == N_PAIRS:
        cleared_proc = "_KB5GEN_RUNWAY_CLEARED_LAST"
        cleared_args = f"{cross_tpl} {p['arr_id']}"
    else:
        next_dep_id = pairs[i]["dep_id"]  # pairs[i] (0-indexed) == pair number i+1
        cleared_proc = "_KB5GEN_RUNWAY_CLEARED"
        cleared_args = f"{cross_tpl} {p['arr_id']} {next_dep_id}"

    lines.append(f"""
# ================================================================
# CẶP {i}/{N_PAIRS}: {p['arr_id']} ({p['arr_type']}, thoát ly {p['exit']}) + {p['dep_id']} ({p['dep_type']}, {p['gate_name']}{'  -- lăn thẳng ra 35R (chuyến đầu)' if is_first_dep else ' -- qua PRE_HOLD, xếp hàng'})
# ================================================================
{dep_t_s}>CRE {p['dep_id']},{p['dep_type']},{glat},{glon},{ghdg},0,15
{dep_t_s}>PCALL {taxi_tpl} {p['dep_id']}
{dep_t_s}>{p['dep_id']} ATDIST 16.0604,108.1980,0.15 PCALL {cleared_proc} {cleared_args}

{arr_t_s}>CRE {p['arr_id']},{p['arr_type']},15.767222,108.118333,173,10000,250
{arr_t_s}>PCALL _KB5GEN_ARR_APPROACH {p['arr_id']}
{arr_t_s}>PCALL {exit_tpl} {p['arr_id']}
{arr_t_s}>{p['arr_id']} ATALT 0 PCALL _KB5GEN_DEP_ROLL {p['dep_id']}
""")

main_content = "\n".join(lines)
add_file("VVDN_KB5_1HOUR_MIXED.scn", main_content)

for fname, content in files.items():
    with open(f"{OUT_DIR}/{fname}", "w", encoding="utf-8") as f:
        f.write(content)

print(f"Đã sinh {len(files)} file trong {OUT_DIR}/")
print("Danh sách cặp:")
for p in pairs:
    print(f"  {p['i']:2d}. ARR t={fmt_t(p['arr_t'])} {p['arr_id']}({p['arr_type']},{p['exit']})  "
          f"DEP t={fmt_t(p['dep_t'])} {p['dep_id']}({p['dep_type']},{p['gate_name']})")
