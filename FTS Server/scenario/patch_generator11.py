import sys

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb_35r_only.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Modify the takeoff roll trigger
old_trigger = """{arr_t_s}>{p['arr_id']} ATALT 0 PCALL _KB5GEN_DEP_ROLL_{p['dep_id']} {p['dep_id']}"""
new_trigger = """{dep_t_s}>{p['dep_id']} ATDIST 16.030000,108.202000,0.02 PCALL _KB5GEN_DEP_ROLL_{p['dep_id']} {p['dep_id']}"""
content = content.replace(old_trigger, new_trigger)

# 2. Modify the first departure. Since DEP001 doesn't wait for any ARR, it can enter the runway directly
# Wait, for DEP001, it is already on the runway threshold!
# If I use ATDIST 16.030000,108.202000 for DEP001, it will work because it taxies there!

with open("d:/Coding/Dự án FTS/WebFTS v4/FTS Server/scenario/_gen_kb_35r_only.py", "w", encoding="utf-8") as f:
    f.write(content)
