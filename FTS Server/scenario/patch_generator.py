import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Variables
content = content.replace('N_PAIRS = 24', 'N_PAIRS = 20')
content = content.replace('ARR_SPACING_S = 150', 'ARR_SPACING_S = 180')
content = content.replace('DEP_SPACING_S = 150', 'DEP_SPACING_S = 180')
content = content.replace('OUT_DIR = "."', 'OUT_DIR = r"D:\\Coding\\Dự án FTS\\WebFTS v4\\FTS Server\\scenario\\Backup\\VVDN 2026-08-10_08-06-28 (bản 40)"')

# 2. Rename post_doten_legs to post_cadas_legs and adjust it
old_post = """def post_doten_legs(actype):
    \"\"\"[(lat,lon,alt_ft,spd_kt), ...] từ TRACO (ngay sau DOTEN) tới ngưỡng
    35L -- tốc độ riêng theo BADA từng loại tàu bay (xem approach_speeds()).\"\"\"
    s25, s10, s5, std = approach_speeds(actype)
    s_20nm = interp_speed(s25, s10, (25.0 - 19.994) / (25.0 - 10.0))
    s_14_7nm = interp_speed(s25, s10, (25.0 - 14.675) / (25.0 - 10.0))
    s_4_4nm = interp_speed(s5, std, (5.0 - 4.42) / 5.0)
    return [
        (15.601667, 108.142222, 7695, 230),       # TRACO
        (15.618056, 108.262500, 6071, s25),       # CADAS -- mốc 25NM"""

new_post = """def post_cadas_legs(actype, cadas_alt_ft):
    \"\"\"[(lat,lon,alt_ft,spd_kt), ...] từ CADAS tới ngưỡng
    35L -- tốc độ riêng theo BADA từng loại tàu bay (xem approach_speeds()).\"\"\"
    s25, s10, s5, std = approach_speeds(actype)
    s_20nm = interp_speed(s25, s10, (25.0 - 19.994) / (25.0 - 10.0))
    s_14_7nm = interp_speed(s25, s10, (25.0 - 14.675) / (25.0 - 10.0))
    s_4_4nm = interp_speed(s5, std, (5.0 - 4.42) / 5.0)
    return [
        (15.618056, 108.262500, round(cadas_alt_ft), s25),       # CADAS -- mốc 25NM"""

content = content.replace(old_post, new_post)

# Remove _override_doten_alt as it is no longer needed
content = re.sub(r'def _override_doten_alt.*?return pre_legs\[:-1\] \+ \[\(lat, lon, round\(doten_alt_ft\), spd\)\].*?\n\n', '', content, flags=re.DOTALL)

# 3. Update make_arr_approach_file_for_pair
old_make = """def make_arr_approach_file_for_pair(p):
    actype = p["arr_type"]
    star = p.get("star")
    post_legs = post_doten_legs(actype)
    doten_alt_ft = p["doten_alt_ft"]
    if star is None:
        legs = post_legs  # ARR001: CRE thẳng tại DOTEN (cao độ đã đặt ở CRE), không có chuỗi STAR riêng
        star_note = f"CRE thẳng tại DOTEN cao độ {round(doten_alt_ft)}ft (T=0, không qua STAR)"
    elif p.get("cre_override"):
        pre_legs = _override_doten_alt(p["cre_override"]["remaining_nodes"], doten_alt_ft)
        legs = pre_legs + post_legs  # bỏ đoạn xa, chỉ giữ phần gần DOTEN
        star_note = f"STAR {star} -- CRE tại điểm cắt gần DOTEN hơn (bỏ đoạn IAF xa) -> DOTEN {round(doten_alt_ft)}ft -> ngưỡng 35L"
    else:
        pre_legs = _override_doten_alt(STAR_CHAINS[star], doten_alt_ft)
        legs = pre_legs + post_legs
        star_note = f"STAR {star} (IAF -> DOTEN {round(doten_alt_ft)}ft -> ngưỡng 35L)"
    lines_txt = "\\n".join(
        f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} {alt} {spd}" for (lat, lon, alt, spd) in legs
    )
    add_file(f"_KB5GEN_ARR_APPROACH_{p['arr_id']}.scn", f\"\"\"# _KB5GEN_ARR_APPROACH_{p['arr_id']}.scn — {p['arr_id']} ({actype}) — {star_note}
# Toạ độ/khống chế cao độ+tốc độ TRƯỚC DOTEN lấy nguyên văn AIP STAR RNAV
# RWY35LR thật (xem STAR_CHAINS), TRỪ cao độ NGAY TẠI DOTEN được ghi đè riêng
# theo doten_alt_ft (phân tầng 8000ft-FL110 giữa các chuyến đến liên tiếp,
# chuyến trước thấp hơn chuyến sau, theo yêu cầu) -- tốc độ SAU DOTEN riêng
# theo BADA của {actype} (xem post_doten_legs) -- không ép cứng thời gian
# bay, chỉ ép cứng IAS theo từng mốc khoảng cách như đã làm trước đây.
# Gọi ngay sau CRE: PCALL _KB5GEN_ARR_APPROACH_{p['arr_id']} <acid>
{lines_txt}
\"\"\")"""

new_make = """def make_arr_approach_file_for_pair(p):
    actype = p["arr_type"]
    star = p.get("star")
    cadas_alt_ft = p["cadas_alt_ft"]
    post_legs = post_cadas_legs(actype, cadas_alt_ft)
    if star is None:
        legs = post_legs  # ARR001: CRE thẳng tại CADAS
        star_note = f"CRE thẳng tại CADAS cao độ {round(cadas_alt_ft)}ft (T=0, không qua STAR)"
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
    )
    add_file(f"_KB5GEN_ARR_APPROACH_{p['arr_id']}.scn", f\"\"\"# _KB5GEN_ARR_APPROACH_{p['arr_id']}.scn — {p['arr_id']} ({actype}) — {star_note}
# Toạ độ/khống chế lấy nguyên văn AIP STAR RNAV, điều chỉnh giãn cách tại CADAS.
# Gọi ngay sau CRE: PCALL _KB5GEN_ARR_APPROACH_{p['arr_id']} <acid>
{lines_txt}
\"\"\")"""

content = content.replace(old_make, new_make)

# 4. _STAR_TRANSIT and _star_nodes
content = re.sub(
    r'_STAR_TRANSIT = \{(.*?)\}',
    r'_STAR_TRANSIT = {\n    name: estimate_transit_s(_full_pre_cadas_chain(name) + [_CADAS_PLACEHOLDER], (STAR_IAF[name][0], STAR_IAF[name][1]))\n    for name in STAR_IAF\n}',
    content, flags=re.DOTALL
)

content = re.sub(
    r'def _star_nodes\(star\):\n    iaf_lat, iaf_lon, iaf_alt, iaf_spd = STAR_IAF\[star\]\n    return \[\(iaf_lat, iaf_lon, iaf_alt, iaf_spd\)\] \+ STAR_CHAINS\[star\]',
    r'def _star_nodes(star):\n    iaf_lat, iaf_lon, iaf_alt, iaf_spd = STAR_IAF[star]\n    return [(iaf_lat, iaf_lon, iaf_alt, iaf_spd)] + _full_pre_cadas_chain(star) + [_CADAS_PLACEHOLDER]',
    content
)

# 5. truncated_star_spawn and DOTEN -> CADAS loops
old_trunc = """def truncated_star_spawn(star, target_doten_t):
    \"\"\"Tìm điểm nội suy trên chính STAR sao cho thời gian bay còn lại tới
    DOTEN đúng bằng target_doten_t -- trả về (lat, lon, alt_ft, spd_kt,
    hdg_deg, waypoints_còn_lại) để CRE trực tiếp tại đó (bỏ đoạn IAF->điểm
    này) và chỉ ADDWPT phần còn lại (điểm kế tiếp -> ... -> DOTEN).\"\"\"
    nodes = _star_nodes(star)
    remaining = _remaining_transit_per_node(nodes)
    n = len(nodes)
    for j in range(n - 1):
        if remaining[j] >= target_doten_t >= remaining[j + 1]:
            lat0, lon0, alt0, _spd0 = nodes[j]
            lat1, lon1, alt1, spd1 = nodes[j + 1]
            leg_t = remaining[j] - remaining[j + 1]
            frac = 0.0 if leg_t <= 0 else (remaining[j] - target_doten_t) / leg_t
            frac = min(max(frac, 0.0), 1.0)
            lat = lat0 + (lat1 - lat0) * frac
            lon = lon0 + (lon1 - lon0) * frac
            alt = round(alt0 + (alt1 - alt0) * frac)
            hdg = round(bearing_deg(lat, lon, lat1, lon1), 1)
            return lat, lon, alt, spd1, hdg, nodes[j + 1:]
    # target_doten_t <= 0 (không nên xảy ra vì i>1 luôn có target>=ARR_SPACING_S) --
    # fallback an toàn: CRE ngay tại DOTEN, không còn waypoint STAR nào.
    lat, lon, alt, spd = nodes[-1]
    return lat, lon, alt, spd, 173.0, []"""

new_trunc = """def truncated_star_spawn(star, target_cadas_t):
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
    return lat, lon, alt, spd, round(bearing_deg(lat, lon, nodes[-1][0], nodes[-1][1]), 1), []"""

content = content.replace(old_trunc, new_trunc)

# Replace target_doten_t -> target_cadas_t in the pairs generation
content = content.replace('target_doten_t', 'target_cadas_t')
content = content.replace('expected_doten_t', 'expected_cadas_t')
content = content.replace('doten_alt_ft', 'cadas_alt_ft')
content = content.replace('DOTEN', 'CADAS')

# Make sure to disable the backup creation so we don't spam the Backup folder when running this script
content = content.replace('backup_generated_files(OUT_DIR, list(files.keys()) + ["_KB5v2_DEL_AFTER10.scn"])', '# backup disabled for this run')

# Fix CADAS ARR001 spawn heading (should be 353 instead of 173 which is DOTEN's old hdg to TRACO)
content = content.replace('15.767222, 108.118333, round(p["cadas_alt_ft"]), 250, 173', 'CADAS[0], CADAS[1], round(p["cadas_alt_ft"]), 250, 353')

# Fix _gen_kb5_1hour.py unicode print
content = "import sys\nimport io\nsys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')\n" + content

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "w", encoding="utf-8") as f:
    f.write(content)
