# -*- coding: utf-8 -*-
"""
Monte Carlo batch runner -- Phase 1 (wind only), N runs of run_single.run_one,
parallelized across worker processes (each BlueSky headless sim needs its
own process; bs.init() is process-global state).

CLI args are all optional and default to the original hardcoded values, so
`python run_batch.py` with no arguments behaves exactly as before (1000 runs,
8 workers, fixed output file) -- this is relied on by the web-triggered job
runner (WebATM/server/monte_carlo_api.py), which passes --status-file/--out-file
per job, but must not change the standalone manual-CLI workflow.
"""
import sys
import os
import json
import time
import argparse
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))

N_RUNS = 1000
N_WORKERS = 8
OUT_FILE = os.path.join(os.path.dirname(__file__), "results", "wind_mc_1000.json")


def _atomic_write_json(path, data):
    """Write JSON atomically (temp file + os.replace), matching the
    safe_atomic_write convention used by WebATM/server/atwi_api.py -- kept
    as a private local copy here since this script must stay importable/
    runnable standalone without depending on the Flask app package."""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=d, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf, ensure_ascii=False, indent=2)
        tmp_name = tf.name
    os.replace(tmp_name, path)


def _worker(seed, run_one_kwargs):
    from run_single import run_one, load_wind_records
    wind_records = load_wind_records()
    return run_one(seed=seed, wind_records=wind_records, **run_one_kwargs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-runs", type=int, default=N_RUNS)
    parser.add_argument("--n-workers", type=int, default=N_WORKERS)
    parser.add_argument("--out-file", default=OUT_FILE)
    parser.add_argument("--status-file", default=None,
                         help="If set, incrementally write {done,total} progress here after every completed run.")
    parser.add_argument("--aircraft-type", default="B773")
    parser.add_argument("--p-wake-nm", type=float, default=6.065)
    parser.add_argument("--thr-lat", type=float, default=16.0290376)
    parser.add_argument("--thr-lon", type=float, default=108.202528)
    parser.add_argument("--rwy-hdg", type=float, default=352.10)
    args = parser.parse_args(argv)

    run_one_kwargs = {
        "aircraft_type": args.aircraft_type,
        "p_wake_nm": args.p_wake_nm,
        "thr_lat": args.thr_lat,
        "thr_lon": args.thr_lon,
        "rwy_hdg": args.rwy_hdg,
    }

    t0 = time.time()
    results = []
    done = 0
    n_runs = args.n_runs

    if args.status_file:
        _atomic_write_json(args.status_file, {"done": 0, "total": n_runs})

    with ProcessPoolExecutor(max_workers=args.n_workers) as ex:
        futures = {ex.submit(_worker, seed, run_one_kwargs): seed for seed in range(n_runs)}
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

    _atomic_write_json(args.out_file, results)

    total = time.time() - t0
    print(f"DONE. {len(results)} runs in {total:.0f}s -> {args.out_file}")


if __name__ == "__main__":
    main()
