# -*- coding: utf-8 -*-
"""
Monte Carlo batch runner for the 3NM/DER consecutive-departure study
("Kich ban 3NM 2 tau bay cat canh lien tuc.docx"). N iterations, parallelized
across worker processes (each BlueSky headless sim needs its own process).

Per iteration:
  1. Draw ONE real METAR wind observation (bootstrap resample, same technique
     as analysis/monte_carlo/run_single.py) -- shared by leader AND follower,
     since both depart under the same ambient wind in a given iteration.
  2. Draw ONE T_delay (ATC-clearance-to-brake-release latency). NOT backed by
     real VVDN data yet -- see ASSUMPTIONS below; flagged in the report.
  3. Simulate the FULL departure profile (run_profile.run_profile) for each
     of the 4 representative fleet types needed this iteration (slowest/
     fastest MEDIUM, slowest/fastest HEAVY, from fleet_ranking.json), under
     this iteration's wind. Each type is simulated only ONCE per iteration
     and reused across every group/M_candidate it participates in.
  4. For each (group, M_candidate) combination, compute D_start (separation
     when the follower begins its takeoff roll) and D_min (minimum
     separation from then until the follower reaches 6NM from DER), per the
     exact definitions in Sec.3.2 of the source document.

ASSUMPTIONS (no real VVDN data available yet -- flagged per this project's
"khong tu gia dinh, ghi ro con thieu du lieu gi" convention, see the P_wake
study's own "Bang du lieu con thieu" section for precedent):
  - T_delay ~ Uniform(3.0, 8.0) seconds (radio call + pilot readback + brake
    release reaction). Needs replacing with real ATC timing data if available.
  - VVDN's real fleet has no LIGHT aircraft (confirmed in
    VVDN-Trigger-Point-Consecutive-Departures.docx Sec.0), so the
    Medium-Light / Heavy-Light / Light-Light groups from the source document
    are not computed here -- they would be vacuous for this airport's real
    traffic. Medium-Heavy and Heavy-Heavy are added instead (real VVDN combos
    per the "cac cap khac neu co trong du lieu" clause in Sec.4).
"""
import sys
import os
import json
import time
import random
import argparse
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))

N_RUNS = 1000
N_WORKERS = 8
OUT_FILE = os.path.join(os.path.dirname(__file__), "results", "mc_3nm_1000.json")
FLEET_RANKING_FILE = os.path.join(os.path.dirname(__file__), "results", "fleet_ranking.json")
WIND_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "monte_carlo", "data", "wind_empirical.json")

M_CANDIDATES_NM = [0.8, 1.2, 1.6]
FOLLOWER_TARGET_FROM_DER_NM = 6.0
T_DELAY_MIN_S = 3.0
T_DELAY_MAX_S = 8.0
PROFILE_TMAX_S = 260.0  # matches analysis/monte_carlo/run_single.py's TMAX_S precedent
PROFILE_MAX_DIST_MARGIN_NM = 0.5  # stop shortly past the 6NM-from-DER follower target


def _atomic_write_json(path, data):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=d, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf, ensure_ascii=False, indent=2)
        tmp_name = tf.name
    os.replace(tmp_name, path)


def load_wind_records():
    with open(WIND_DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["records"]


def load_fleet_ranking():
    with open(FLEET_RANKING_FILE, encoding="utf-8") as f:
        return json.load(f)


def _time_at_distance(profile, target_dist_nm):
    """First time (linearly interpolated) at which the profile's
    dist_from_threshold crosses target_dist_nm. None if never reached."""
    prev = None
    for (t, d, alt) in profile:
        if d >= target_dist_nm:
            if prev is None:
                return t
            t0, d0 = prev
            if d == d0:
                return t
            frac = (target_dist_nm - d0) / (d - d0)
            return t0 + frac * (t - t0)
        prev = (t, d)
    return None


def _worker(seed, groups, runway_len_nm, m_candidates=None, t_delay_min=T_DELAY_MIN_S, t_delay_max=T_DELAY_MAX_S):
    from run_profile import run_profile, interp_dist

    if m_candidates is None:
        m_candidates = M_CANDIDATES_NM

    wind_records = load_wind_records()
    rng = random.Random(seed)
    w = rng.choice(wind_records)
    wind_dir = w["dir_deg"] if w["dir_deg"] is not None else rng.uniform(0, 360)
    wind_spd = w["speed_kt"]
    t_delay = rng.uniform(t_delay_min, t_delay_max)

    needed_types = sorted({t for (_, leader, follower) in groups for t in (leader, follower)})
    # Every profile in this study only ever needs to be read up to the
    # follower's own 6NM-from-DER target (plus enough slack for T_delay
    # pushing the leader's read-out point a few seconds later) -- capping
    # the simulation there instead of at PROFILE_TMAX_S saves most of the
    # per-run wall-clock cost across N=1000 iterations x 4 fleet types.
    max_dist_nm = runway_len_nm + FOLLOWER_TARGET_FROM_DER_NM + PROFILE_MAX_DIST_MARGIN_NM
    profiles = {}
    for ac_type in needed_types:
        profiles[ac_type] = run_profile(
            seed=None, wind_dir_deg=wind_dir, wind_spd_kt=wind_spd,
            aircraft_type=ac_type, tmax_s=PROFILE_TMAX_S, max_dist_nm=max_dist_nm,
        )

    out = {
        "seed": seed,
        "wind_dir_deg": wind_dir,
        "wind_spd_kt": wind_spd,
        "wind_source_ts": w.get("ts"),
        "t_delay_s": t_delay,
        "groups": {},
    }

    follower_target_dist_nm = runway_len_nm + FOLLOWER_TARGET_FROM_DER_NM

    for (group_name, leader_type, follower_type) in groups:
        leader_profile = profiles[leader_type]
        follower_profile = profiles[follower_type]
        group_result = {}
        for m in m_candidates:
            target_dist_leader = runway_len_nm + m
            t_m = _time_at_distance(leader_profile, target_dist_leader)
            if t_m is None:
                group_result[str(m)] = {"error": "leader never reached M within TMAX"}
                continue
            t_start_roll_f = t_m + t_delay

            d_start = None
            d_min = None
            t_at_dmin = None
            for (t_offset, f_dist, f_alt) in follower_profile:
                l_dist = interp_dist(leader_profile, t_start_roll_f + t_offset)
                if l_dist is None:
                    break
                d = l_dist - f_dist
                if d_start is None:
                    # First follower sample (t_offset ~0, still essentially at
                    # brake-release) -- this IS D_start per Sec.3.2.
                    d_start = d
                if d_min is None or d < d_min:
                    d_min = d
                    t_at_dmin = t_offset
                if f_dist >= follower_target_dist_nm:
                    break

            group_result[str(m)] = {
                "leader_type": leader_type,
                "follower_type": follower_type,
                "t_m_s": t_m,
                "t_start_roll_f_s": t_start_roll_f,
                "d_start_nm": d_start,
                "d_min_nm": d_min,
                "t_offset_at_dmin_s": t_at_dmin,
            }
        out["groups"][group_name] = group_result

    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-runs", type=int, default=N_RUNS)
    parser.add_argument("--n-workers", type=int, default=N_WORKERS)
    parser.add_argument("--out-file", default=OUT_FILE)
    parser.add_argument("--status-file", default=None)
    parser.add_argument("--m-candidates", default=None,
                         help="Comma-separated list of M distances from DER, e.g. '0.8,1.2,1.6' (default: built-in list).")
    parser.add_argument("--t-delay-min", type=float, default=T_DELAY_MIN_S)
    parser.add_argument("--t-delay-max", type=float, default=T_DELAY_MAX_S)
    args = parser.parse_args(argv)

    m_candidates = (
        [float(x) for x in args.m_candidates.split(",") if x.strip()]
        if args.m_candidates else M_CANDIDATES_NM
    )

    from run_profile import RUNWAY_LEN_NM
    ranking = load_fleet_ranking()
    sm, fm = ranking["slowest_medium"], ranking["fastest_medium"]
    sh, fh = ranking["slowest_heavy"], ranking["fastest_heavy"]
    groups = [
        ("Medium-Medium", sm, fm),
        ("Heavy-Medium", sh, fm),
        ("Medium-Heavy", sm, fh),
        ("Heavy-Heavy", sh, fh),
    ]
    print("Groups (leader -> follower, worst-case representative types):")
    for (name, leader, follower) in groups:
        print(f"  {name}: {leader} -> {follower}")
    print(f"M_candidates={m_candidates} T_delay=[{args.t_delay_min}, {args.t_delay_max}]s")

    n_runs = args.n_runs
    t0 = time.time()
    results = []
    done = 0

    if args.status_file:
        _atomic_write_json(args.status_file, {"done": 0, "total": n_runs})

    with ProcessPoolExecutor(max_workers=args.n_workers) as ex:
        futures = {
            ex.submit(_worker, seed, groups, RUNWAY_LEN_NM, m_candidates, args.t_delay_min, args.t_delay_max): seed
            for seed in range(n_runs)
        }
        for fut in as_completed(futures):
            try:
                r = fut.result()
                results.append(r)
            except Exception as e:
                results.append({"seed": futures[fut], "error": str(e)})
            done += 1
            if args.status_file:
                _atomic_write_json(args.status_file, {"done": done, "total": n_runs})
            if done % 50 == 0:
                elapsed = time.time() - t0
                rate = done / elapsed
                eta = (n_runs - done) / rate if rate > 0 else float("nan")
                print(f"[{done}/{n_runs}] elapsed={elapsed:.0f}s eta={eta:.0f}s", flush=True)

    _atomic_write_json(args.out_file, {"groups_def": groups, "runway_len_nm": RUNWAY_LEN_NM, "results": results})

    total = time.time() - t0
    print(f"DONE. {len(results)} runs in {total:.0f}s -> {args.out_file}")


if __name__ == "__main__":
    main()
