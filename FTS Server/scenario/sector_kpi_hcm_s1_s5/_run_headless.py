"""
Chay kich ban HCM_S1S5_KPI_20260605_0730-0750.scn qua BlueSky headless,
ghi track (t, lat, lon, alt_ft, gs_kt, hdg_deg) moi 2 giay mo phong ra JSON.

Theo dung pattern da dung trong _verify_vvdn_xenke.py (run_headless()).
"""
import os
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FTS = HERE.parent.parent  # FTS Server/

SCN_NAME = "HCM_S1S5_KPI_20260605_0730-0750"
T_END = 2400.0  # 07:20 -> 08:00 UTC = 40 phut
DT_LOG = 2.0


def run_headless(t_end, dt_log=2.0):
    os.chdir(FTS)
    sys.path.insert(0, str(FTS))
    import bluesky as bs

    bs.init(mode="sim", detached=True)
    bs.stack.stack(f"IC sector_kpi_hcm_s1_s5/{SCN_NAME}")
    bs.sim.op()

    track = {}
    next_log = 0.0
    n_steps = 0
    while bs.sim.simt < t_end:
        bs.sim.step()
        n_steps += 1
        if bs.sim.simt >= next_log:
            for i, acid in enumerate(bs.traf.id):
                track.setdefault(acid, []).append((
                    round(float(bs.sim.simt), 2),
                    float(bs.traf.lat[i]),
                    float(bs.traf.lon[i]),
                    float(bs.traf.alt[i]) / 0.3048,
                    float(bs.traf.gs[i]) / 0.514444,
                    float(bs.traf.hdg[i]),
                ))
            next_log += dt_log
    return track, n_steps


def main():
    print(f"Dang chay headless {SCN_NAME} den t={T_END}s ...", flush=True)
    track, n_steps = run_headless(T_END, DT_LOG)
    print(f"Hoan tat: {n_steps} step, {len(track)} may bay co track.")
    out = HERE / f"{SCN_NAME}.track.json"
    json.dump(track, open(out, "w", encoding="utf-8"), separators=(",", ":"))
    print(f"Da ghi {out}")
    for acid, pts in list(track.items())[:3]:
        print(acid, "diem dau:", pts[0], "diem cuoi:", pts[-1], "so mau:", len(pts))


if __name__ == "__main__":
    main()
