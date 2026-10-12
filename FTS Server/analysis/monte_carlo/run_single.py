# -*- coding: utf-8 -*-
"""
Single Monte Carlo run: B773 (the confirmed worst-case real HEAVY type for
the P_wake marker, per VVDN-Trigger-Point-Consecutive-Departures.docx Sec.2)
takes off from the real RWY 35R threshold under a real, bootstrap-resampled
METAR wind observation. Reuses the exact headless-BlueSky technique already
verified in _debug_takeoff_perf_batch.py (CRE at rest at the threshold, then
ALT+SPD+LNAV OFF+VNAV OFF lets BlueSky's live BADA performance model run the
ground-roll/climb physics for real) -- only NEW element is the WIND command.

Records: time and altitude at which the aircraft's distance from the
threshold reaches 6.065 NM (P_wake) -- this is what mattered for the
confirmed HEAVY->MEDIUM wake-turbulence trigger point.
"""
import sys
import os
import json
import math
import random

# FTS Server/analysis/monte_carlo/run_single.py -> up 2 levels = FTS Server/
BS_ROOT = os.environ.get("WEBFTS_BS_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
sys.path.insert(0, BS_ROOT)

THR_LAT, THR_LON, THR_HDG = 16.0290376, 108.202528, 352.10
P_WAKE_NM = 6.065
TMAX_S = 260.0


def load_wind_records():
    path = os.path.join(os.path.dirname(__file__), "data", "wind_empirical.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["records"]


def dist_nm(lat1, lon1, lat2, lon2):
    R = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def run_one(
    seed,
    wind_records,
    aircraft_type="B773",
    p_wake_nm=P_WAKE_NM,
    thr_lat=THR_LAT,
    thr_lon=THR_LON,
    rwy_hdg=THR_HDG,
):
    """One headless BlueSky run under a bootstrap-resampled real wind obs.

    NOTE: bs.init() is idempotent within a worker process (ProcessPoolExecutor
    reuses each worker for many tasks), so it does NOT reset simulation state
    between calls. Must explicitly RESET (matching the proven pattern in
    _debug_takeoff_perf_batch.py's loop over 9 aircraft types in one process)
    or leftover aircraft/wind-field/simt state from a prior task in the same
    worker corrupts this run -- confirmed live: without RESET, batch runs
    gave liftoff_t_s == marker_t_s (~146s) for most seeds, while the exact
    same seed run in isolation correctly gave liftoff_t_s=39.75/marker_t_s=119.2.

    aircraft_type/p_wake_nm/thr_lat/thr_lon/rwy_hdg default to the confirmed
    VVDN RWY35R HEAVY(B773)->MEDIUM P_wake case; overridable per-call so the
    web-triggered job runner can parameterize other aircraft/WTC pairs
    without touching the validated defaults used by direct CLI invocation.
    """
    os.chdir(BS_ROOT)
    import bluesky as bs
    bs.init(mode="sim", detached=True)
    bs.stack.stack("RESET")
    for _ in range(5):
        bs.sim.step()

    rng = random.Random(seed)
    w = rng.choice(wind_records)
    wind_dir = w["dir_deg"] if w["dir_deg"] is not None else rng.uniform(0, 360)
    wind_spd = w["speed_kt"]

    bs.stack.stack(f"WIND {thr_lat},{thr_lon},{wind_dir:.0f},{wind_spd:.0f}")
    bs.stack.stack(f"CRE TST01,{aircraft_type},{thr_lat},{thr_lon},{rwy_hdg},0,0")
    for _ in range(3):
        bs.sim.step()
    bs.stack.stack("TST01 ALT 5000")
    bs.stack.stack("TST01 SPD 250")
    bs.stack.stack("TST01 LNAV OFF")
    bs.stack.stack("TST01 VNAV OFF")

    liftoff_t = None
    marker_t = None
    marker_alt = None
    deleted_early = False
    while bs.sim.simt < TMAX_S:
        bs.sim.step()
        idx = bs.traf.id2idx("TST01")
        if idx < 0:
            deleted_early = True
            break
        alt_ft = bs.traf.alt[idx] * 3.28084
        d = dist_nm(thr_lat, thr_lon, bs.traf.lat[idx], bs.traf.lon[idx])
        if liftoff_t is None and alt_ft > 5:
            liftoff_t = bs.sim.simt
        if marker_t is None and d >= p_wake_nm and alt_ft > 0:
            marker_t = bs.sim.simt
            marker_alt = alt_ft
            break

    return {
        "seed": seed,
        "wind_dir_deg": wind_dir,
        "wind_spd_kt": wind_spd,
        "wind_source_ts": w.get("ts"),
        "liftoff_t_s": liftoff_t,
        "marker_t_s": marker_t,
        "marker_alt_ft": marker_alt,
        "deleted_early": deleted_early,
    }


if __name__ == "__main__":
    import time as _time
    wind_records = load_wind_records()
    t0 = _time.time()
    result = run_one(seed=1, wind_records=wind_records)
    wall_s = _time.time() - t0
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"WALL_CLOCK_SECONDS={wall_s:.2f}")
