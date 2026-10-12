import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Change DEP001 spawn coordinates and note
old_dep001_spawn = """    if i == 1:
        # DEP001 cất cánh ngay đầu, không ai cản -> lăn thẳng ra 35R không dừng
        dep_cre_lat, dep_cre_lon = GATE_COORDS[gate]
        dep_hdg = GATE_HDG[gate]
        dep_origin_note = f"{gate}  -- lăn thẳng ra 35R (chuyến đầu)\""""
new_dep001_spawn = """    if i == 1:
        # DEP001: Xuất hiện trên đường lăn E1 (điểm chờ 35R) thay vì bến đỗ
        dep_cre_lat, dep_cre_lon = 16.029362, 108.203879
        dep_hdg = 250.0
        dep_origin_note = f"Taxiway E1 (Hold 35R)  -- lăn lên đường băng sau 5 phút\""""
content = content.replace(old_dep001_spawn, new_dep001_spawn)

# 2. Change DEP001 logic in the pairs block
old_dep001_logic = """        if i == 1:
            # DEP001: qua pushback rồi lăn luôn (không có lệnh dừng TAXIOFF)
            lines.append(f"{t_str}>CRE {dep_id},{dep_type},{p['dep_cre_lat']:.6f},{p['dep_cre_lon']:.6f},{p['dep_hdg']:.1f},0,0")
            lines.append(f"{t_str}>PCALL _KB5GEN_PUSHBACK_{p['gate']} {dep_id} _KB5GEN_TAXI_{p['gate']}_RWYHOLD {aircraft_length_m(dep_type)}")"""
new_dep001_logic = """        if i == 1:
            # DEP001: Spawn tại E1, đợi đến phút thứ 5 mới bò lên đường băng để không đứng trên RWY quá lâu
            lines.append(f"{t_str}>CRE {dep_id},{dep_type},{p['dep_cre_lat']:.6f},{p['dep_cre_lon']:.6f},{p['dep_hdg']:.1f},0,0")
            lines.append(f"00:05:00.00>PCALL _KB5GEN_TAXI_E1_RWYHOLD {dep_id}")"""
content = content.replace(old_dep001_logic, new_dep001_logic)

# 3. Prevent generating taxi file from G26 to RWYHOLD for DEP001, and generate E1 instead
old_make_dep_taxi = """def make_dep_taxi_file(dep_id, gate, is_first=False):
    # Lộ trình lăn
    if is_first:
        filename = f"_KB5GEN_TAXI_{gate}_RWYHOLD.scn"
        legs = TAXI_G26_TO_RWYHOLD if gate == "G26" else TAXI_G27_TO_RWYHOLD
        note = "lăn thẳng ra điểm chờ 35R (chuyến đầu, không qua PRE_HOLD)"
    else:"""
new_make_dep_taxi = """def make_dep_taxi_file(dep_id, gate, is_first=False):
    # Lộ trình lăn
    if is_first:
        filename = f"_KB5GEN_TAXI_E1_RWYHOLD.scn"
        legs = [
            (16.029184, 108.202510, 12),
            (16.028487, 108.202603, 8),
            (16.029200, 108.202500, 0),
        ]
        note = "từ điểm chờ E1 lên thẳng 35R (chuyến đầu)"
        # Bỏ qua logic cũ vì DEP001 không xuất phát từ Gate
        lines_txt = "\\n".join(
            f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} 0 {spd}" for (lat, lon, spd) in legs
        )
        add_file(filename, f\"\"\"# {filename} -- DEP001 {note}
{lines_txt}
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
\"\"\")
        return
    else:"""
content = content.replace(old_make_dep_taxi, new_make_dep_taxi)

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb5_1hour.py", "w", encoding="utf-8") as f:
    f.write(content)
