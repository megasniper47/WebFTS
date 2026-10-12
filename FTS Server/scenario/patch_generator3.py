import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update target_cadas_t calculation
old_target = 'target_cadas_t = (i - 1) * ARR_SPACING_S\n    cre_override = None'
new_target = 'T_ADVANCE_S = 36\n    target_cadas_t = (i - 1) * ARR_SPACING_S - T_ADVANCE_S\n    cre_override = None'
content = content.replace(old_target, new_target)

# 2. Update ARR001 spawn coordinates
old_spawn = 'arr_cre_lat, arr_cre_lon, arr_cre_alt, arr_cre_spd, arr_cre_hdg = CADAS[0], CADAS[1], round(p["cadas_alt_ft"]), 250, 353\n        arr_origin_note = f"CRE thẳng tại CADAS cao độ {round(p[\'cadas_alt_ft\'])}ft"'
new_spawn = 'f = 0.4035\n        lat = 15.618056 + f * (15.700556 - 15.618056)\n        lon = 108.262500 + f * (108.250000 - 108.262500)\n        alt = p["cadas_alt_ft"] + f * (4921.0 - p["cadas_alt_ft"])\n        arr_cre_lat, arr_cre_lon, arr_cre_alt, arr_cre_spd, arr_cre_hdg = lat, lon, round(alt), 230, 353\n        arr_origin_note = f"CRE qua CADAS 2NM cao độ {round(alt)}ft"'
content = content.replace(old_spawn, new_spawn)

# 3. Update make_arr_approach_file_for_pair logic for ARR001
old_make = 'legs = post_legs  # ARR001: CRE thẳng tại CADAS\n        star_note = f"CRE thẳng tại CADAS cao độ {round(cadas_alt_ft)}ft (T=0, không qua STAR)"'
new_make = 'legs = post_legs[1:]  # ARR001: CRE qua CADAS 2NM, bỏ điểm CADAS để không quay đầu lại\n        star_note = f"CRE qua CADAS 2NM cao độ {round(cadas_alt_ft)}ft (T=0, không qua STAR)"'
content = content.replace(old_make, new_make)

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "w", encoding="utf-8") as f:
    f.write(content)
