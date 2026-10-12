import sys, os, re
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, '_gen_kb5_1hour.py'), 'r', encoding='utf-8') as f:
    src = f.read()

# 1. DEP spacing 150s -> 180s
src = src.replace('DEP_SPACING_S = 150', 'DEP_SPACING_S = 180', 1)

# 2. Tìm dòng block.append ATDIST 16.0604 trong main loop và chèn roll-start trigger sau.
#    Đồng thời đổi template từ RUNWAY_CLEARED (có cả DEP enter) -> RUNWAY_CLEARED_LAST (chỉ ARR cross).
OLD_LINE = (
    "    block.append(f\"{dep_t_s}>{p['dep_id']} ATDIST 16.0604,108.1980,0.15 "
    "PCALL {cleared_proc} {cleared_args}\".rstrip())"
)
NEW_LINES = """\
    # Far-end (16.0604): chi ARR cross, khong advance DEP nua.
    # Dung RUNWAY_CLEARED_LAST hoac NOCROSS_LAST tuy arr_delayed.
    arr_delayed_local = p["waits_for_arr"] is not None
    if arr_delayed_local:
        _fc_proc = "_KB5GEN_RUNWAY_CLEARED_NOCROSS_LAST"
        _fc_args = ""
    else:
        _fc_proc = "_KB5GEN_RUNWAY_CLEARED_LAST"
        _fc_args = f"{cross_tpl} {p['arr_id']}"
    block.append(f"{dep_t_s}>{p['dep_id']} ATDIST 16.0604,108.1980,0.15 PCALL {_fc_proc} {_fc_args}".rstrip())

    # Roll-start trigger ~100m tren CHC 35R:
    # khi DEP[i] bat dau chay da qua diem nay -> DEP[i+1] tien len RWYHOLD.
    if i < N_PAIRS:
        _next_p = pairs[i]
        _, _next_c = make_queue_aware_procs(_next_p)
        _next_dep = _next_p["dep_id"]
        block.append(f"{dep_t_s}>{p['dep_id']} ATDIST 16.030100,108.202372,0.025 "
                     f"PCALL {_next_c} {_next_dep}")\
"""
src = src.replace(OLD_LINE, NEW_LINES, 1)
found = NEW_LINES[:40] in src
print(f"[info] roll-start trigger injected: {found}")

# 3. Encoding fix
src = src.replace(
    'with open(f"{OUT_DIR}/{fname}", "w", encoding="utf-8") as f:',
    'with open(f"{OUT_DIR}/{fname}", "w", encoding="utf-8", errors="replace") as f:', 1)

exec(compile(src, '_patch', 'exec'), {'__file__': os.path.join(here, '_gen_kb5_1hour.py')})
