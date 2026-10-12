# -*- coding: utf-8 -*-
"""
Characterization pass -- ranks every real VVDN fleet type (per
VVDN-Trigger-Point-Consecutive-Departures.docx Sec.0/2 and the KB5 generator's
own fleet list) by climb-out speed, so the 3NM/DER Monte Carlo study (Sec.4 of
"Kich ban 3NM 2 tau bay cat canh lien tuc.docx") can pick, for each WTC pair
group, the WORST-CASE representative pair instead of exhaustively simulating
every real type combination.

Physical reasoning for "worst case" here (different from the P_wake study):
P_wake only ever needed the single fastest aircraft in a WTC class (bigger
lead = later marker, and any slower aircraft would need an earlier one, so
"lead = fastest" covers the whole class). This study instead measures the GAP
between two aircraft, so the tightest (smallest) separation happens when the
LEADER is the slowest type in its class (falls behind least "credit") and the
FOLLOWER is the fastest type in its class (closes the gap quickest). So each
group's representative pair = (slowest type of leader's class, fastest type
of follower's class).

Ranking metric: distance from the RWY 35R threshold at a fixed reference time
(REF_T = 200s after brake release, deterministic run, zero wind) -- chosen to
be safely past every real type's liftoff (35.6-43.2s per the trigger-point
doc's Appendix) so the ranking reflects sustained climb speed, not just
ground-roll acceleration.
"""
import sys
import os
import json

BS_ROOT = os.environ.get("WEBFTS_BS_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
sys.path.insert(0, BS_ROOT)

sys.path.insert(0, os.path.dirname(__file__))
from run_profile import run_profile, THR_LAT, THR_LON, THR_HDG  # noqa: E402

MEDIUM_TYPES = ["A320", "A321", "A20N", "A21N", "B739", "B38M"]
HEAVY_TYPES = ["A332", "A333", "A359", "B744", "B763", "B772", "B773", "B77W", "B788", "B789", "B748", "B78X"]

REF_T = 200.0


def rank_types(types):
    """Returns list of (type, dist_from_thr_nm_at_REF_T) sorted ascending (slowest first)."""
    out = []
    for ac_type in types:
        profile = run_profile(seed=None, wind_dir_deg=0, wind_spd_kt=0, aircraft_type=ac_type, tmax_s=REF_T + 5)
        # distance at the last sample <= REF_T
        d_ref = None
        for (t, d, alt) in profile:
            if t <= REF_T:
                d_ref = d
            else:
                break
        out.append((ac_type, d_ref))
    out.sort(key=lambda x: (x[1] if x[1] is not None else -1))
    return out


if __name__ == "__main__":
    medium_ranked = rank_types(MEDIUM_TYPES)
    heavy_ranked = rank_types(HEAVY_TYPES)

    print("=== MEDIUM ranked by distance-from-threshold at t=200s (slowest -> fastest) ===")
    for t, d in medium_ranked:
        print(f"  {t}: {d:.4f} NM" if d is not None else f"  {t}: FAILED")

    print("=== HEAVY ranked by distance-from-threshold at t=200s (slowest -> fastest) ===")
    for t, d in heavy_ranked:
        print(f"  {t}: {d:.4f} NM" if d is not None else f"  {t}: FAILED")

    result = {
        "ref_t_s": REF_T,
        "medium_ranked": medium_ranked,
        "heavy_ranked": heavy_ranked,
        "slowest_medium": medium_ranked[0][0],
        "fastest_medium": medium_ranked[-1][0],
        "slowest_heavy": heavy_ranked[0][0],
        "fastest_heavy": heavy_ranked[-1][0],
    }
    out_path = os.path.join(os.path.dirname(__file__), "results", "fleet_ranking.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {out_path}")
    print(f"slowest_medium={result['slowest_medium']} fastest_medium={result['fastest_medium']}")
    print(f"slowest_heavy={result['slowest_heavy']} fastest_heavy={result['fastest_heavy']}")
