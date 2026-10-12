# -*- coding: utf-8 -*-
"""
Parse real METAR wind reports for VVDN and build an empirical wind
distribution, decomposed into headwind/crosswind components relative to
RWY 35R true heading (352.10 deg, VVDN.json "verified"). No fitted/assumed
distribution shape -- Monte Carlo sampling will bootstrap-resample directly
from these real observations.
"""
import re
import math
import json

RAW_FILE = "data/metar_vvdn_raw.txt"
OUT_FILE = "data/wind_empirical.json"
RWY35R_HDG = 352.10

METAR_WIND_RE = re.compile(r"METAR VVDN (\d{6})Z (\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?KT")


def parse_metar_wind(line):
    m = METAR_WIND_RE.search(line)
    if not m:
        return None
    ts, dirs, spd, gust = m.groups()
    speed_kt = int(spd)
    if dirs == "VRB":
        direction = None  # variable direction, unknown
    else:
        direction = int(dirs)
    gust_kt = int(gust) if gust else None
    return {"ts": ts, "dir_deg": direction, "speed_kt": speed_kt, "gust_kt": gust_kt}


def headwind_crosswind(dir_deg, speed_kt, rwy_hdg=RWY35R_HDG):
    """Positive headwind = wind blowing toward the runway threshold from
    ahead (helps deceleration on landing, hinders takeoff groundspeed vs
    airspeed build-up is actually HELPED aerodynamically, but ground roll
    distance for a given TAS is shorter with headwind -- standard
    convention: angle 0 = pure headwind."""
    if dir_deg is None:
        return None, None
    angle = math.radians(dir_deg - rwy_hdg)
    headwind = speed_kt * math.cos(angle)
    crosswind = speed_kt * math.sin(angle)
    return headwind, crosswind


def main():
    with open(RAW_FILE, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    records = []
    n_calm = 0
    n_vrb = 0
    n_parsed_fail = 0
    for line in lines:
        w = parse_metar_wind(line)
        if w is None:
            n_parsed_fail += 1
            continue
        if w["speed_kt"] == 0:
            n_calm += 1
            records.append({**w, "headwind_kt": 0.0, "crosswind_kt": 0.0})
            continue
        if w["dir_deg"] is None:
            n_vrb += 1
            # Variable direction: conservatively treat as worst-case for
            # crosswind (full speed as crosswind, zero headwind) since real
            # direction is unknown -- disclosed assumption, not fabricated
            # precision.
            records.append({**w, "headwind_kt": 0.0, "crosswind_kt": float(w["speed_kt"]), "vrb_worst_case": True})
            continue
        hw, cw = headwind_crosswind(w["dir_deg"], w["speed_kt"])
        records.append({**w, "headwind_kt": hw, "crosswind_kt": cw})

    speeds = [r["speed_kt"] for r in records]
    headwinds = [r["headwind_kt"] for r in records]
    crosswinds = [r["crosswind_kt"] for r in records]

    def pct(data, p):
        s = sorted(data)
        k = (len(s) - 1) * p / 100.0
        f = int(k)
        c = min(f + 1, len(s) - 1)
        if f == c:
            return s[f]
        return s[f] + (s[c] - s[f]) * (k - f)

    summary = {
        "source": "real METAR VVDN, user-provided, 2026-01-01 to 2026-09-03 (covers dry/cool season Jan-Mar plus summer/transition Jul-Sep; still no Oct-Dec northeast-monsoon peak data)",
        "n_reports": len(records),
        "n_calm": n_calm,
        "n_variable_direction": n_vrb,
        "n_unparsed": n_parsed_fail,
        "speed_kt": {
            "min": min(speeds), "max": max(speeds),
            "p50": pct(speeds, 50), "p90": pct(speeds, 90), "p95": pct(speeds, 95), "p99": pct(speeds, 99),
        },
        "headwind_kt_rwy35r": {
            "min": min(headwinds), "max": max(headwinds),
            "p50": pct(headwinds, 50), "p05": pct(headwinds, 5), "p95": pct(headwinds, 95),
        },
        "crosswind_kt_rwy35r": {
            "min": min(crosswinds), "max": max(crosswinds),
            "p50": pct(crosswinds, 50), "p90": pct(crosswinds, 90), "p95": pct(crosswinds, 95), "p99": pct(crosswinds, 99),
        },
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "records": records}, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
