# -*- coding: utf-8 -*-
"""
Aggregation for the 3NM/DER consecutive-departure Monte Carlo study
("Kich ban 3NM 2 tau bay cat canh lien tuc.docx"). Computes, per (WTC pair
group, M_candidate), the exact statistics table requested in Sec.6 of the
source document, and applies the M_recommended selection criteria from
Sec.5:
  - violation_rate_start ~ 0% (<=0.1%) AND D_start_P1 >= 3.0 NM
  - violation_rate_min   ~ 0% (<=0.1%) AND D_min_P1   >= 3.0 NM
  - if multiple M_candidates satisfy both, pick the SMALLEST (nearest to
    DER) to optimize runway throughput.
"""
import json
import os


def pct(data, p):
    s = sorted(data)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def stats_block(data):
    if not data:
        return None
    return {
        "mean": sum(data) / len(data),
        "p5": pct(data, 5),
        "p1": pct(data, 1),
    }


def summarize(mc_output):
    """mc_output is the dict written by run_batch.py:
    {"groups_def": [...], "runway_len_nm": ..., "results": [...]}"""
    results = mc_output["results"]
    groups_def = mc_output["groups_def"]
    group_names = [g[0] for g in groups_def]

    table = []
    for group_name in group_names:
        # collect all (m_candidate -> list of {d_start, d_min}) across iterations
        by_m = {}
        for r in results:
            if "error" in r:
                continue
            g = r.get("groups", {}).get(group_name)
            if not g:
                continue
            for m_str, entry in g.items():
                if "error" in entry:
                    continue
                by_m.setdefault(m_str, []).append(entry)

        for m_str, entries in sorted(by_m.items(), key=lambda kv: float(kv[0])):
            d_start_list = [e["d_start_nm"] for e in entries if e.get("d_start_nm") is not None]
            d_min_list = [e["d_min_nm"] for e in entries if e.get("d_min_nm") is not None]
            n = len(entries)
            n_violation_start = sum(1 for d in d_start_list if d < 3.0)
            n_violation_min = sum(1 for d in d_min_list if d < 3.0)

            row = {
                "group": group_name,
                "leader_type": entries[0]["leader_type"] if entries else None,
                "follower_type": entries[0]["follower_type"] if entries else None,
                "m_candidate_nm": float(m_str),
                "n_runs": n,
                "d_start": stats_block(d_start_list),
                "d_min": stats_block(d_min_list),
                "violation_rate_start_pct": (100.0 * n_violation_start / n) if n else None,
                "violation_rate_min_pct": (100.0 * n_violation_min / n) if n else None,
            }
            table.append(row)

    # M_recommended per group: smallest M meeting both criteria
    recommended = {}
    for group_name in group_names:
        rows = [r for r in table if r["group"] == group_name]
        rows.sort(key=lambda r: r["m_candidate_nm"])
        chosen = None
        for r in rows:
            ok_start = (r["violation_rate_start_pct"] is not None and r["violation_rate_start_pct"] <= 0.1
                        and r["d_start"] is not None and r["d_start"]["p1"] >= 3.0)
            ok_min = (r["violation_rate_min_pct"] is not None and r["violation_rate_min_pct"] <= 0.1
                      and r["d_min"] is not None and r["d_min"]["p1"] >= 3.0)
            if ok_start and ok_min:
                chosen = r
                break
        recommended[group_name] = chosen

    return {"table": table, "recommended": recommended, "runway_len_nm": mc_output.get("runway_len_nm")}


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "results", "mc_3nm_1000.json")
    with open(path, encoding="utf-8") as f:
        mc_output = json.load(f)

    summary = summarize(mc_output)

    print(f"runway_len_nm={summary['runway_len_nm']:.4f}")
    print()
    header = f"{'Group':<14} {'M(NM)':>6} {'N':>5} {'Dstart_mean':>12} {'Dstart_P1':>10} {'viol_start%':>12} {'Dmin_mean':>10} {'Dmin_P1':>8} {'viol_min%':>10}"
    print(header)
    for r in summary["table"]:
        ds = r["d_start"] or {}
        dm = r["d_min"] or {}
        print(f"{r['group']:<14} {r['m_candidate_nm']:>6.1f} {r['n_runs']:>5} "
              f"{ds.get('mean', float('nan')):>12.3f} {ds.get('p1', float('nan')):>10.3f} "
              f"{r['violation_rate_start_pct']:>12.2f} "
              f"{dm.get('mean', float('nan')):>10.3f} {dm.get('p1', float('nan')):>8.3f} "
              f"{r['violation_rate_min_pct']:>10.2f}")

    print()
    print("=== M_recommended per group ===")
    for group_name, chosen in summary["recommended"].items():
        if chosen:
            print(f"{group_name}: M_recommended={chosen['m_candidate_nm']} NM from DER "
                  f"(Dstart_P1={chosen['d_start']['p1']:.3f} Dmin_P1={chosen['d_min']['p1']:.3f})")
        else:
            print(f"{group_name}: NO M_candidate tested satisfies the criteria -- try larger M (1.8/2.0 NM)")
