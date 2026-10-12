import re
import sys

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb_35r_only.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Spacing and N_PAIRS
content = content.replace("ARR_SPACING_S = 180", "ARR_SPACING_S = 300")
content = content.replace("DEP_SPACING_S = 180", "DEP_SPACING_S = 300")

# 2. Exits
content = content.replace("""_exit_pool = ["G4"] * _n_g4 + ["G6"] * _n_g6""", """_n_e4 = round(N_PAIRS * 0.50)
_n_e6 = N_PAIRS - _n_e4
_exit_pool = ["E4"] * _n_e4 + ["E6"] * _n_e6""")

# 3. STAR Probabilities
old_weights = """        star_weights = {
            "HUE": 15, "CAHEO": 15,        # Bắc
            "KUMUN": 10, "SADIN": 10, "VILOT": 10, # Nam
            "BUNTA": 15,                   # Đông
            "LATOM": 7.5, "PAPRA": 7.5     # Tây
        }"""
new_weights = """        star_weights = {
            "HUE": 17.5, "CAHEO": 17.5,        # Bắc 35%
            "KUMUN": 8.75, "SADIN": 8.75, "VILOT": 8.75, "LATOM": 8.75, # Nam 35%
            "BUNTA": 15,                   # Đông 15%
            "PAPRA": 15                    # Tây 15%
        }"""
content = content.replace(old_weights, new_weights)

# 4. Exits E4 and E6 coordinates and logic
old_exit_g4 = """add_file("_KB5GEN_ARR_EXIT_G4.scn", \"\"\"# _KB5GEN_ARR_EXIT_G4.scn — giảm tốc sau chạm đất, thoát ly khu vực G4, dừng chờ
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
\"\"\")"""
new_exit_e4 = """add_file("_KB5GEN_ARR_EXIT_E4.scn", \"\"\"# _KB5GEN_ARR_EXIT_E4.scn — giảm tốc sau chạm đất, thoát ly khu vực E4
# Gọi: PCALL _KB5GEN_ARR_EXIT_E4 <acid>
00:00:00.00>%0 ADDWPT 16.035000,108.201200 0 120
00:00:00.00>%0 ADDWPT 16.040000,108.200700 0 90
00:00:00.00>%0 ADDWPT 16.045000,108.200200 0 60
00:00:00.00>%0 ADDWPT 16.047000,108.200000 0 30
00:00:00.00>%0 ADDWPT 16.048778,108.199684 0 15
00:00:00.00>%0 ADDWPT 16.048800,108.199800 0 10
00:00:00.00>%0 ADDWPT 16.049000,108.200500 0 5
00:00:00.00>%0 ADDWPT 16.049500,108.201500 0 0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST 16.049500,108.201500,0.025 PCALL _KB5GEN_STOP_AND_DEL %0 16.049500 108.201500 81.0
\"\"\")"""
content = content.replace(old_exit_g4, new_exit_e4)

old_exit_g6 = """add_file("_KB5GEN_ARR_EXIT_G6.scn", \"\"\"# _KB5GEN_ARR_EXIT_G6.scn — giảm tốc sau chạm đất, thoát ly khu vực G6, dừng chờ
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
\"\"\")"""
new_exit_e6 = """add_file("_KB5GEN_ARR_EXIT_E6.scn", \"\"\"# _KB5GEN_ARR_EXIT_E6.scn — giảm tốc sau chạm đất, thoát ly khu vực E6
# Gọi: PCALL _KB5GEN_ARR_EXIT_E6 <acid>
00:00:00.00>%0 ADDWPT 16.035000,108.201200 0 130
00:00:00.00>%0 ADDWPT 16.040000,108.200700 0 110
00:00:00.00>%0 ADDWPT 16.045000,108.200200 0 90
00:00:00.00>%0 ADDWPT 16.050000,108.199700 0 60
00:00:00.00>%0 ADDWPT 16.055000,108.199200 0 30
00:00:00.00>%0 ADDWPT 16.057400,108.198459 0 15
00:00:00.00>%0 ADDWPT 16.057500,108.198900 0 10
00:00:00.00>%0 ADDWPT 16.057800,108.200000 0 5
00:00:00.00>%0 ADDWPT 16.058300,108.202000 0 0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST 16.058300,108.202000,0.025 PCALL _KB5GEN_STOP_AND_DEL %0 16.058300 108.202000 81.0
\"\"\")"""
content = content.replace(old_exit_g6, new_exit_e6)

# 5. Remove CROSS scripts
content = re.sub(r'add_file\("_KB5GEN_CROSS_G4\.scn".*?\"\"\"\)', '', content, flags=re.DOTALL)
content = re.sub(r'add_file\("_KB5GEN_CROSS_G6\.scn".*?\"\"\"\)', '', content, flags=re.DOTALL)

# 6. Change landing runway 35L to 35R in post_cadas_legs
old_post_legs = """def post_cadas_legs(actype):
    \"\"\"[(lat,lon,alt_ft,spd_kt), ...] từ CADAS tới ngưỡng
    35L -- tốc độ riêng theo BADA từng loại tàu bay (xem approach_speeds()).\"\"\"
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
    ]"""
new_post_legs = """def post_cadas_legs(actype):
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
        (16.029200, 108.202500, 0, std),          # ngưỡng 35R
    ]"""
content = content.replace(old_post_legs, new_post_legs)

# 7. Modify DEP enter runway trigger (After arrival crosses threshold)
old_roll_trigger = """    if i < N_PAIRS:
        next_dep_id = pairs[i]["dep_id"]
        roll_trigger = f"{dep_t_s}>{p['dep_id']} ATDIST 16.030100,108.202372,0.025 PCALL _KB5GEN_DEP_ENTER_RWY {next_dep_id}"
    else:
        roll_trigger = f"# Không còn chuyến khởi hành nào sau {p['dep_id']}\""""
new_roll_trigger = """    roll_trigger = f"{arr_t_s}>{p['arr_id']} ATDIST 16.029200,108.202500,0.05 PCALL _KB5GEN_DEP_ENTER_RWY {p['dep_id']}\""""
content = content.replace(old_roll_trigger, new_roll_trigger)

# Remove the ATDIST for CROSS
old_cross = """{dep_t_s}>{p['dep_id']} ATDIST 16.0604,108.1980,0.15 PCALL {cross_tpl} {p['arr_id']}"""
new_cross = """"""
content = content.replace(old_cross, new_cross)

# 8. Output filename
content = content.replace("VVDN_KB5_1HOUR_MIXED.scn", "VVDN_KB5_35R_ONLY.scn")
content = content.replace("Đã sinh 55 file", "Đã sinh kịch bản 35R ONLY")

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb_35r_only.py", "w", encoding="utf-8") as f:
    f.write(content)
