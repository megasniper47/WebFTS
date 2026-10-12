import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Sửa file _KB5GEN_DEP_ENTER_RWY.scn: bỏ TAXIOFF và DELRTE, chỉ ADDWPT để nối tiếp đường lăn
old_enter_rwy = """add_file("_KB5GEN_DEP_ENTER_RWY.scn", \"\"\"# _KB5GEN_DEP_ENTER_RWY.scn — lăn từ PRE_HOLD vào đầu 35R
# Gọi: PCALL _KB5GEN_DEP_ENTER_RWY <acid>
# TAXIOFF trước tiên: đã được ATC cho phép vào đường CHC, trả lại quyền điều
# khiển tốc độ cho chuỗi ADDWPT/LNAV có sẵn dưới đây (SurfaceTaxiController
# chỉ quản lý pha xếp hàng gate->PRE_HOLD, không can thiệp từ đây trở đi).
# LƯU Ý: file này được PCALL từ điều kiện ATDIST của DEP phía trước, đúng lúc
# tàu bay đích đang dừng cứng tại PRE_HOLD (STOP_HOLD, LNAV OFF + MOVE) --
# giống hệt trường hợp CROSS_G4/G6, VNAV ON không tự lấy lại tốc độ từ route
# mới (actwp.spd không refresh đúng) nên phải ép %0 SPD lại để tàu bay thực
# sự lăn tiếp, và dùng mốc THỜI GIAN cố định (đoạn này chỉ ~2m, dùng dư 10s)
# thay cho ATDIST để tránh lỗi đăng ký điều kiện lồng 2 tầng (xem giải thích
# đầy đủ ở _KB5GEN_CROSS_G4.scn).
00:00:00.00>TAXIOFF %0
00:00:00.00>%0 DELRTE
00:00:00.00>%0 ADDWPT 16.029181,108.202508 0 5.0
00:00:00.00>%0 ADDWPT 16.0292,108.2025 0 0.0
00:00:00.00>%0 ADDWPT 16.030000,108.202000 0 5.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 SPD 5.0
00:00:10.00>PCALL _KB5GEN_STOP_HOLD %0 16.029200 108.202500 352.1
\"\"\")"""

new_enter_rwy = """add_file("_KB5GEN_DEP_ENTER_RWY.scn", \"\"\"# _KB5GEN_DEP_ENTER_RWY.scn — nối tiếp từ PRE_HOLD vào đầu 35R
# Gọi: PCALL _KB5GEN_DEP_ENTER_RWY <acid>
# Bỏ DELRTE để tàu bay đang lăn KHÔNG bị cắt ngang lộ trình và bay direct.
# Tàu bay sẽ tự động tiếp tục lăn hoặc đi tiếp từ PRE_HOLD.
00:00:00.00>%0 ADDWPT 16.029181,108.202508 0 5.0
00:00:00.00>%0 ADDWPT 16.029200,108.202500 0 5.0
00:00:00.00>%0 ADDWPT 16.030000,108.202000 0 5.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
\"\"\")"""
content = content.replace(old_enter_rwy, new_enter_rwy)

# 2. Sửa TAXI_COMMON_G26 và G27: cắt ngắn tới điểm trước PRE_HOLD
old_taxi26 = """TAXI_COMMON_G26 = [
    (16.052004, 108.200773, 10.0), (16.051764, 108.200781, 15.0), (16.051560, 108.200776, 15.0),
    (16.051307, 108.200786, 15.0), (16.049490, 108.200986, 15.0), (16.049218, 108.201025, 12.0),
    (16.044100, 108.201789, 18.0), (16.038291, 108.202625, 18.0), (16.030836, 108.203677, 15.0),
    (16.029967, 108.203803, 10.0), (16.029680, 108.203824, 8.0), (16.029490, 108.203744, 6.0),
    (16.029355, 108.203538, 5.0), (16.029272, 108.203047, 5.0), (16.029181, 108.202508, 5.0),
]"""
new_taxi26 = """TAXI_COMMON_G26 = [
    (16.052004, 108.200773, 10.0), (16.051764, 108.200781, 15.0), (16.051560, 108.200776, 15.0),
    (16.051307, 108.200786, 15.0), (16.049490, 108.200986, 15.0), (16.049218, 108.201025, 12.0),
    (16.044100, 108.201789, 18.0), (16.038291, 108.202625, 18.0), (16.030836, 108.203677, 15.0),
    (16.029967, 108.203803, 10.0), (16.029680, 108.203824, 8.0), (16.029490, 108.203744, 6.0),
    (16.029355, 108.203538, 5.0),
]"""
content = content.replace(old_taxi26, new_taxi26)

old_taxi27 = """TAXI_COMMON_G27 = [
    (16.051764, 108.200781, 10.0), (16.051560, 108.200776, 15.0), (16.051307, 108.200786, 15.0),
    (16.049490, 108.200986, 15.0), (16.049218, 108.201025, 12.0), (16.044100, 108.201789, 18.0),
    (16.038291, 108.202625, 18.0), (16.030836, 108.203677, 15.0), (16.029967, 108.203803, 10.0),
    (16.029680, 108.203824, 8.0), (16.029490, 108.203744, 6.0), (16.029355, 108.203538, 5.0),
]"""
new_taxi27 = """TAXI_COMMON_G27 = [
    (16.051764, 108.200781, 10.0), (16.051560, 108.200776, 15.0), (16.051307, 108.200786, 15.0),
    (16.049490, 108.200986, 15.0), (16.049218, 108.201025, 12.0), (16.044100, 108.201789, 18.0),
    (16.038291, 108.202625, 18.0), (16.030836, 108.203677, 15.0), (16.029967, 108.203803, 10.0),
    (16.029680, 108.203824, 8.0), (16.029490, 108.203744, 6.0), (16.029355, 108.203538, 5.0),
]"""
content = content.replace(old_taxi27, new_taxi27)

# 3. Sửa hàm make_taxi_file để KHÔNG gọi STOP_HOLD nữa, dừng tự nhiên bằng cách nối điểm đích
old_make_taxi = """def make_taxi_file(name, points, dest, dest_dummy):
    dlat, dlon, dhdg = dest
    dumlat, dumlon, dumspd = dest_dummy
    add_file(name, f\"\"\"# {name} -- tự sinh, toạ độ y hệt taxi-out gốc trong VVDN_KB5_35L35R_2ARR2DEP_v2
# Gọi ngay sau CRE: PCALL {name} <acid>
{taxi_addwpt_lines(points)}
00:00:00.00>%0 ADDWPT {dumlat:.6f},{dumlon:.6f} 0 {dumspd}
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST {dlat:.6f},{dlon:.6f},0.01 PCALL _KB5GEN_STOP_HOLD %0 {dlat:.6f} {dlon:.6f} {dhdg}
\"\"\")"""

new_make_taxi = """def make_taxi_file(name, points, dest, dest_dummy):
    dlat, dlon, dhdg = dest
    # Thay vì dùng STOP_HOLD, ta cho lộ trình kết thúc bằng điểm đích (PRE_HOLD) với tốc độ 0 để tự dừng
    add_file(name, f\"\"\"# {name} -- tự sinh, lăn ra PRE_HOLD và dừng tự nhiên
# Gọi ngay sau CRE: PCALL {name} <acid>
{taxi_addwpt_lines(points)}
00:00:00.00>%0 ADDWPT {dlat:.6f},{dlon:.6f} 0 0.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
\"\"\")"""
content = content.replace(old_make_taxi, new_make_taxi)

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "w", encoding="utf-8") as f:
    f.write(content)
