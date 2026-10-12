# -*- coding: utf-8 -*-
"""
Single-aircraft departure profile from RWY 35R threshold under a given wind,
for the 3NM/DER consecutive-departure study ("Kich ban 3NM 2 tau bay cat canh
lien tuc.docx"). Reuses the exact CRE/ALT/SPD/LNAV-OFF/VNAV-OFF technique
already verified in analysis/monte_carlo/run_single.py (BlueSky's live BADA
performance model runs the real ground-roll/climb physics) -- the only
difference is that this records the FULL (t, dist_from_threshold, alt_ft)
trajectory instead of a single snapshot, because the 3NM study needs to
compare TWO aircraft's positions over time (leader vs. follower), not just
one marker crossing.

Both the leader and the follower in a given Monte Carlo iteration are assumed
to depart under the SAME ambient wind (same iteration = same simulated
moment in time), so run_batch.py calls this once per (aircraft_type, wind
draw) and reuses the resulting profile for every role (leader/follower,
every M_candidate, every group) that type plays in that iteration.
"""
import sys
import os
import math

BS_ROOT = os.environ.get("WEBFTS_BS_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
sys.path.insert(0, BS_ROOT)

THR_LAT, THR_LON, THR_HDG = 16.0290376, 108.202528, 352.10
# DER (departure end of RWY 35R) = threshold of the opposite designator 17L,
# per FTS Server/data/runway_geometry/VVDN.json (status "verified").
DER_LAT, DER_LON = 16.0603655, 108.1980039


def dist_nm(lat1, lon1, lat2, lon2):
    R = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


RUNWAY_LEN_NM = dist_nm(THR_LAT, THR_LON, DER_LAT, DER_LON)


def run_profile(seed, wind_dir_deg, wind_spd_kt, aircraft_type, tmax_s=700.0, sample_dt=1.0, max_dist_nm=None):
    """Runs one headless BlueSky departure and returns a list of
    (t, dist_from_threshold_nm, alt_ft) samples from brake-release to tmax_s
    (or until the aircraft is deleted, e.g. flew out of the simulated area).

    seed is accepted only for API symmetry with the wind-bootstrap callers in
    run_batch.py / fleet_ranking.py -- wind is passed in pre-resolved
    (wind_dir_deg/wind_spd_kt) since the caller already drew it from the real
    METAR bootstrap (or fixed 0/0 for the deterministic characterization
    pass), so this function itself makes no random choices.

    max_dist_nm, if given, stops the simulation as soon as the aircraft's
    distance from the threshold reaches it (plus the current sample) --
    run_batch.py's Monte Carlo never needs a profile past the follower's own
    6NM-from-DER target, so this avoids paying for hundreds of unneeded
    cruise-climb seconds per run across N=1000 iterations x 4 fleet types.
    """
    os.chdir(BS_ROOT)
    import bluesky as bs
    bs.init(mode="sim", detached=True)
    bs.stack.stack("RESET")
    for _ in range(5):
        bs.sim.step()

    bs.stack.stack(f"WIND {THR_LAT},{THR_LON},{wind_dir_deg:.0f},{wind_spd_kt:.0f}")
    bs.stack.stack(f"CRE TST01,{aircraft_type},{THR_LAT},{THR_LON},{THR_HDG},0,0")
    for _ in range(3):
        bs.sim.step()
    bs.stack.stack("TST01 ALT 5000")
    bs.stack.stack("TST01 SPD 250")
    bs.stack.stack("TST01 LNAV OFF")
    bs.stack.stack("TST01 VNAV OFF")

    profile = []
    next_sample = 0.0
    while bs.sim.simt < tmax_s:
        bs.sim.step()
        idx = bs.traf.id2idx("TST01")
        if idx < 0:
            break
        if bs.sim.simt >= next_sample:
            alt_ft = bs.traf.alt[idx] * 3.28084
            d = dist_nm(THR_LAT, THR_LON, bs.traf.lat[idx], bs.traf.lon[idx])
            profile.append((round(bs.sim.simt, 2), d, alt_ft))
            if max_dist_nm is not None and d >= max_dist_nm:
                break
            next_sample += sample_dt

    return profile


def interp_dist(profile, t):
    """Linear interpolation of dist_from_threshold_nm at time t from a
    (t, dist, alt) profile. Returns None if t is outside the profile's range
    (e.g. the aircraft was deleted/flew out of range before t)."""
    if not profile:
        return None
    if t <= profile[0][0]:
        return profile[0][1]
    if t >= profile[-1][0]:
        return None if t > profile[-1][0] + 5.0 else profile[-1][1]
    lo, hi = 0, len(profile) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if profile[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    t0, d0, _ = profile[lo]
    t1, d1, _ = profile[hi]
    if t1 == t0:
        return d0
    frac = (t - t0) / (t1 - t0)
    return d0 + frac * (d1 - d0)


if __name__ == "__main__":
    import time as _time
    t0 = _time.time()
    profile = run_profile(seed=1, wind_dir_deg=0, wind_spd_kt=0, aircraft_type="B773", tmax_s=300.0)
    wall_s = _time.time() - t0
    print(f"RUNWAY_LEN_NM={RUNWAY_LEN_NM:.4f}")
    print(f"samples={len(profile)} wall_clock_s={wall_s:.2f}")
    print("first 5:", profile[:5])
    print("last 5:", profile[-5:])
