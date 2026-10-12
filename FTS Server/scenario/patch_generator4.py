import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix post_cadas_legs to not use cadas_alt_ft and just use 6071
old_post = """def post_cadas_legs(actype, cadas_alt_ft):
    \"\"\"[(lat,lon,alt_ft,spd_kt), ...] từ CADAS tới ngưỡng
    35L -- tốc độ riêng theo BADA từng loại tàu bay (xem approach_speeds()).\"\"\"
    s25, s10, s5, std = approach_speeds(actype)
    s_20nm = interp_speed(s25, s10, (25.0 - 19.994) / (25.0 - 10.0))
    s_14_7nm = interp_speed(s25, s10, (25.0 - 14.675) / (25.0 - 10.0))
    s_4_4nm = interp_speed(s5, std, (5.0 - 4.42) / 5.0)
    return [
        (15.618056, 108.262500, round(cadas_alt_ft), s25),       # CADAS -- mốc 25NM"""

new_post = """def post_cadas_legs(actype):
    \"\"\"[(lat,lon,alt_ft,spd_kt), ...] từ CADAS tới ngưỡng
    35L -- tốc độ riêng theo BADA từng loại tàu bay (xem approach_speeds()).\"\"\"
    s25, s10, s5, std = approach_speeds(actype)
    s_20nm = interp_speed(s25, s10, (25.0 - 19.994) / (25.0 - 10.0))
    s_14_7nm = interp_speed(s25, s10, (25.0 - 14.675) / (25.0 - 10.0))
    s_4_4nm = interp_speed(s5, std, (5.0 - 4.42) / 5.0)
    return [
        (15.618056, 108.262500, 6071, s25),       # CADAS -- mốc 25NM"""
content = content.replace(old_post, new_post)

# 2. Fix the spawn altitude of ARR001 (i=1) and remove cadas_alt_ft references
old_arr001 = """alt = p["cadas_alt_ft"] + f * (4921.0 - p["cadas_alt_ft"])
        arr_cre_lat, arr_cre_lon, arr_cre_alt, arr_cre_spd, arr_cre_hdg = lat, lon, round(alt), 230, 353
        arr_origin_note = f"CRE qua CADAS 2NM cao độ {round(alt)}ft\""""

new_arr001 = """alt = 6071.0 + f * (4921.0 - 6071.0)
        arr_cre_lat, arr_cre_lon, arr_cre_alt, arr_cre_spd, arr_cre_hdg = lat, lon, round(alt), 230, 353
        arr_origin_note = f"CRE qua CADAS 2NM cao độ {round(alt)}ft\""""
content = content.replace(old_arr001, new_arr001)

# Remove cadas_alt_ft from pairs loop calculation
content = re.sub(r'cadas_alt_ft = 8000\.0 \+ \(i - 1\) \* \(11000\.0 - 8000\.0\) / \(N_PAIRS - 1\)', '', content)
content = re.sub(r', "cadas_alt_ft": cadas_alt_ft', '', content)

# 3. Fix make_arr_approach_file_for_pair to strictly enforce monotonic descent!
old_make = """def make_arr_approach_file_for_pair(p):
    actype = p["arr_type"]
    star = p.get("star")
    cadas_alt_ft = p["cadas_alt_ft"]
    post_legs = post_cadas_legs(actype, cadas_alt_ft)
    if star is None:
        legs = post_legs[1:]  # ARR001: CRE qua CADAS 2NM, bỏ điểm CADAS để không quay đầu lại
        star_note = f"CRE qua CADAS 2NM cao độ {round(cadas_alt_ft)}ft (T=0, không qua STAR)"
    elif p.get("cre_override"):
        pre_legs = p["cre_override"]["remaining_nodes"]
        legs = pre_legs + post_legs
        star_note = f"STAR {star} -- CRE tại điểm cắt gần CADAS hơn (bỏ đoạn IAF xa) -> CADAS {round(cadas_alt_ft)}ft -> ngưỡng 35L"
    else:
        pre_legs = _full_pre_cadas_chain(star)
        legs = pre_legs + post_legs
        star_note = f"STAR {star} (IAF -> CADAS {round(cadas_alt_ft)}ft -> ngưỡng 35L)"
    lines_txt = "\\n".join(
        f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} {alt} {spd}" for (lat, lon, alt, spd) in legs
    )"""

new_make = """def make_arr_approach_file_for_pair(p):
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

    lines_txt = "\\n".join(
        f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} {alt} {spd}" for (lat, lon, alt, spd) in legs
    )"""
content = content.replace(old_make, new_make)

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "w", encoding="utf-8") as f:
    f.write(content)
