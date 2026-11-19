"""
Tinh KPI theo sector tu track mo phong (hoac track that):
- So tau trong sector theo thoi gian (timeseries + peak)
- Dwell time (thoi gian bay trong sector) tung tau, tung lan vao/ra
- Chi so workload don gian theo occupancy (KHONG phai mo hinh ATWI da duoc kiem
  chung cho TWR - du an chua co mo hinh task-time rieng cho sector ACC duong dai,
  nen o day chi dung occupancy count lam chi bao workload tho, ghi ro gioi han).

Nguon polygon+dai muc bay: WebATM/static/data/vietnam_acc_sector_boundaries.geojson
(da doi chieu khop AIRAC AIP SUP A37/23).
"""
import json
import re
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
GEOJSON = HERE.parent.parent.parent / "WebATM" / "static" / "data" / "vietnam_acc_sector_boundaries.geojson"
TRACK_JSON = HERE / "HCM_S1S5_KPI_20260605_0730-0750.track.json"

SECTOR_KEYS = ["HCM ACC Sector 1", "HCM ACC Sector 5"]


def parse_alt_range(name: str):
    m = re.search(r"<=FL(\d+)$", name)
    if m:
        return (0, int(m.group(1)) * 100)
    m = re.search(r"FL(\d+)-FL(\d+)$", name)
    if m:
        return (int(m.group(1)) * 100, int(m.group(2)) * 100)
    return None


def load_sectors():
    with open(GEOJSON, encoding="utf-8") as f:
        d = json.load(f)
    sectors = {k: [] for k in SECTOR_KEYS}
    for feat in d["features"]:
        name = feat["properties"]["name"]
        for key in SECTOR_KEYS:
            if name.startswith(key):
                alt_ft = parse_alt_range(name)
                ring = feat["geometry"]["coordinates"][0]
                poly = prep(Polygon(ring))
                sectors[key].append((alt_ft, poly, name))
    return sectors


def point_in_sector(lon, lat, alt_ft, bands):
    pt = Point(lon, lat)
    for (lo, hi), ppoly, _name in bands:
        if lo <= alt_ft <= hi and ppoly.contains(pt):
            return True
    return False


def analyze(t_end=None, bin_sec=60.0):
    sectors = load_sectors()
    with open(TRACK_JSON, encoding="utf-8") as f:
        track = json.load(f)

    result = {}
    for sector_name, bands in sectors.items():
        occ_snapshot = {}  # t -> set(acid)
        dwell_events = {}  # acid -> list of [t_in, t_out]

        for acid, pts in track.items():
            inside_prev = False
            t_in = None
            for sample in pts:
                t, lat, lon, alt_ft, gs_kt, hdg = sample
                if t_end is not None and t > t_end:
                    break
                inside = point_in_sector(lon, lat, alt_ft, bands)
                if inside:
                    occ_snapshot.setdefault(t, set()).add(acid)
                if inside and not inside_prev:
                    t_in = t
                if inside_prev and not inside:
                    dwell_events.setdefault(acid, []).append([t_in, t])
                inside_prev = inside
            if inside_prev and t_in is not None:
                last_t = pts[-1][0]
                dwell_events.setdefault(acid, []).append([t_in, last_t])

        # binned occupancy timeseries
        all_t = sorted(occ_snapshot)
        max_t = all_t[-1] if all_t else 0.0
        n_bins = int(max_t // bin_sec) + 1 if all_t else 0
        timeseries = []
        for b in range(n_bins):
            b_start, b_end = b * bin_sec, (b + 1) * bin_sec
            ids_in_bin = set()
            for t in all_t:
                if b_start <= t < b_end:
                    ids_in_bin |= occ_snapshot[t]
            timeseries.append({
                "bin_start_s": b_start,
                "bin_end_s": b_end,
                "aircraft_count": len(ids_in_bin),
                "callsigns": sorted(ids_in_bin),
            })

        peak_count = max((len(v) for v in occ_snapshot.values()), default=0)
        peak_t = None
        for t, v in occ_snapshot.items():
            if len(v) == peak_count:
                peak_t = t
                break

        dwell_summary = []
        for acid, events in dwell_events.items():
            total = sum(e[1] - e[0] for e in events)
            dwell_summary.append({
                "callsign": acid,
                "entries": len(events),
                "total_dwell_s": round(total, 1),
                "events": [[round(e[0], 1), round(e[1], 1)] for e in events],
            })
        dwell_summary.sort(key=lambda r: -r["total_dwell_s"])

        result[sector_name] = {
            "distinct_aircraft": len(dwell_events),
            "peak_count": peak_count,
            "peak_time_s": peak_t,
            "avg_dwell_s": round(
                sum(r["total_dwell_s"] for r in dwell_summary) / len(dwell_summary), 1
            ) if dwell_summary else 0.0,
            "timeseries": timeseries,
            "dwell_detail": dwell_summary,
        }

    return result


if __name__ == "__main__":
    r = analyze()
    for name, data in r.items():
        print(f"\n=== {name} ===")
        print("so tau khac nhau di qua:", data["distinct_aircraft"])
        print("dinh dong thoi (peak):", data["peak_count"], "tai t=", data["peak_time_s"], "s")
        print("dwell trung binh (s):", data["avg_dwell_s"])
    out = HERE / "sector_kpi_result.json"
    json.dump(r, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\nDa ghi", out)
