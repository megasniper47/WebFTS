import json


def pct(data, p):
    s = sorted(data)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def summarize_results(results):
    """Aggregate a list of run_single.run_one() result dicts into percentile
    summaries + worst/best case. Pulled out of the module-level script body
    so both this file's CLI (unchanged behavior, fixed default path) and
    WebATM/server/monte_carlo_api.py's GET /jobs/<id>/results route can call
    it against any job's own results.json."""
    n_total = len(results)
    n_error = sum(1 for r in results if "error" in r)
    n_deleted = sum(1 for r in results if r.get("deleted_early"))
    n_no_marker = sum(1 for r in results if r.get("marker_t_s") is None and "error" not in r)
    valid = [r for r in results if r.get("marker_t_s") is not None]

    marker_t = [r["marker_t_s"] for r in valid]
    marker_alt = [r["marker_alt_ft"] for r in valid]
    liftoff_t = [r["liftoff_t_s"] for r in valid if r.get("liftoff_t_s") is not None]
    wind_spd = [r["wind_spd_kt"] for r in results if "wind_spd_kt" in r]

    def stats_block(data):
        if not data:
            return None
        return {
            "min": min(data), "p05": pct(data, 5), "p50": pct(data, 50),
            "p95": pct(data, 95), "p99": pct(data, 99), "max": max(data),
        }

    worst = max(valid, key=lambda r: r["marker_t_s"]) if valid else None
    best = min(valid, key=lambda r: r["marker_t_s"]) if valid else None

    return {
        "nTotal": n_total,
        "nError": n_error,
        "nDeletedEarly": n_deleted,
        "nNoMarkerReached": n_no_marker,
        "nValid": len(valid),
        "markerTimeS": stats_block(marker_t),
        "markerAltFt": stats_block(marker_alt),
        "liftoffTimeS": stats_block(liftoff_t),
        "windSpdKtSampled": stats_block(wind_spd),
        "worstCase": worst,
        "bestCase": best,
    }


if __name__ == "__main__":
    with open("results/wind_mc_1000.json", encoding="utf-8") as f:
        results = json.load(f)

    summary = summarize_results(results)

    print(f"n_total={summary['nTotal']} n_error={summary['nError']} "
          f"n_deleted_early={summary['nDeletedEarly']} "
          f"n_no_marker_reached={summary['nNoMarkerReached']} n_valid={summary['nValid']}")
    print()

    mt = summary["markerTimeS"]
    print("marker_t_s (thoi gian tu brake-release toi khi dat 6.065NM):")
    print(f"  min={mt['min']:.2f} p05={mt['p05']:.2f} p50={mt['p50']:.2f} "
          f"p95={mt['p95']:.2f} p99={mt['p99']:.2f} max={mt['max']:.2f}")
    print()

    ma = summary["markerAltFt"]
    print("marker_alt_ft (do cao khi dat marker 6.065NM):")
    print(f"  min={ma['min']:.1f} p05={ma['p05']:.1f} p50={ma['p50']:.1f} "
          f"p95={ma['p95']:.1f} p99={ma['p99']:.1f} max={ma['max']:.1f}")
    print()

    lt = summary["liftoffTimeS"]
    print("liftoff_t_s:")
    print(f"  min={lt['min']:.2f} p50={lt['p50']:.2f} p95={lt['p95']:.2f} max={lt['max']:.2f}")
    print()

    ws = summary["windSpdKtSampled"]
    print(f"wind_spd_kt sampled: min={ws['min']} p50={ws['p50']:.1f} max={ws['max']}")

    print()
    print("WORST CASE (longest marker_t_s):", json.dumps(summary["worstCase"], ensure_ascii=False))
    print("BEST CASE (shortest marker_t_s):", json.dumps(summary["bestCase"], ensure_ascii=False))
