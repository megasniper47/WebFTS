"""
Generator: VVDN_KB5_1HR_G6ONLY.scn
Lặp lại chu trình KB5 v2, tất cả ARR thoát ly G6 → Gate 11.
Fleet mix: 70% medium / 30% heavy, seed 20260810.
"""
import os, sys, re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

here = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(here, "_gen_kb5_1hour.py")
with open(src_path, "r", encoding="utf-8") as f:
    src = f.read()

# 1. Seed mới
src = src.replace("random.seed(20260807)", "random.seed(20260810)", 1)

# 2. Tên file output
src = src.replace(
    'add_file("VVDN_KB5_1HOUR_MIXED.scn"',
    'add_file("VVDN_KB5_1HR_G6ONLY.scn"', 1)

# 3. Buộc tất cả ARR thoát ly G6
src = src.replace(
    'exit_choice = random.choice(["G4", "G6"])',
    'exit_choice = "G6"', 1)

# 4. Fix encoding
src = src.replace(
    'with open(f"{OUT_DIR}/{fname}", "w", encoding="utf-8") as f:',
    'with open(f"{OUT_DIR}/{fname}", "w", encoding="utf-8", errors="replace") as f:',
    1)

exec(compile(src, "_gen_kb5_g6only_exec", "exec"), {"__file__": src_path})
