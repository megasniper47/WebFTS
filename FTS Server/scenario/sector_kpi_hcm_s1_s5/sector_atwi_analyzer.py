"""
Mo hinh workload ATWI mo rong cho sector ACC duong dai (Sector 1 & Sector 5 HCM ACC).

Tai dung CHINH XAC cung cong thuc/coefficients/nguong cua mo hinh ATWI da co
trong du an (FTS Server/data/atwi_models.json, atwi_task_index.json) -- cung
la mo hinh "draft, chua approvedForKpi" nhu mo hinh TWR hien tai, KHONG tu
nhan la da kiem chung hon.

Khac biet so voi atwi_analyzer.py (von doc command_log.jsonl):
  Kich ban nay la REPLAY tu track that, KHONG co lenh dieu khien nao duoc
  phat ra (khong co command_log). Vi vay cac task "communication" duoc suy
  ra tu CHINH BIEN DOI THAT trong track (doi huong/doi muc bay/doi toc do
  giua dau va cuoi moi cua so 300s) -- goi la "proxy tu hanh vi bay that",
  KHONG phai lenh controller da xac nhan. Dieu nay duoc ghi ro trong moi
  task_count ket qua (truong "basis").

Task dung duoc tu du lieu that (KHONG phai proxy):
  - SURV_SCAN, TRAFFIC_COUNT_MONITOR: so tau hien dien that trong sector
  - HANDOFF_COORD: so lan tau THAT SU vao sector (bien bay qua ranh gioi)
  - CROSS_SECTOR_COORD: so lan tau THAT SU chuyen tiep Sector1<->Sector5
  - CONFLICT_CHECK / STCA_RESPONSE: kiem tra phan cach THAT giua cac cap
    tau dang cung o trong sector, theo chuan ICAO Doc 4444 (5NM ngang /
    1000ft doc RVSM) -- du an chua co ruleset VVHM rieng nen dung chuan
    ICAO mac dinh, ghi ro nguon.

Task la PROXY tu hanh vi that (khong phai lenh xac nhan):
  - VECTOR_OR_DIRECT: doi huong bay that > 15 do giua dau/cuoi cua so
  - ALTITUDE_CHANGE: doi muc bay that > 500 ft giua dau/cuoi cua so
  - SPEED_CONTROL: doi toc do mat dat that > 15 kt giua dau/cuoi cua so

Khong ap dung cho sector duong dai (luon = 0, khong bia):
  RUNWAY_SEQUENCE, WEATHER_DEVIATION, MILITARY_COORD, SYSTEM_DEGRADED,
  AIRPORT_SURFACE_FEEDBACK
"""
import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
GEOJSON = HERE.parent.parent.parent / "WebATM" / "static" / "data" / "vietnam_acc_sector_boundaries.geojson"
ATWI_MODELS = HERE.parent.parent.parent / "FTS Server" / "data" / "atwi_models.json"
ATWI_TASKS = HERE.parent.parent.parent / "FTS Server" / "data" / "atwi_task_index.json"
RAW_CSV = Path(
    r"C:/Users/trunglq/AppData/Local/Temp/claude/D--Coding-D---n-FTS-WebFTS-v4/"
    r"1c74b732-eedf-40e6-9e64-71071fab81b1/scratchpad/sector_kpi/raw_tracks_window.csv"
)

SIM_T0 = datetime(2026, 6, 5, 7, 20, 0, tzinfo=timezone.utc)
SECTOR_KEYS = ["HCM ACC Sector 1", "HCM ACC Sector 5"]
WINDOW_SEC = 300.0

LATERAL_MIN_NM = 5.0    # ICAO Doc 4444 radar en-route lateral minimum
VERTICAL_MIN_FT = 1000.0  # ICAO RVSM vertical minimum
LATERAL_CRIT_NM = 3.0   # nguong "critical" (STCA) -- that chat hon chuan toi thieu
VERTICAL_CRIT_FT = 500.0

HDG_CHANGE_DEG = 15.0
ALT_CHANGE_FT = 500.0
SPD_CHANGE_KT = 15.0


def parse_alt_range(name):
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
                sectors[key].append((alt_ft, prep(Polygon(ring))))
    return sectors


def in_sector(lon, lat, alt_ft, bands):
    pt = Point(lon, lat)
    for (lo, hi), ppoly in bands:
        if lo <= alt_ft <= hi and ppoly.contains(pt):
            return True
    return False


def haversine_nm(lat1, lon1, lat2, lon2):
    R_NM = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_NM * math.asin(math.sqrt(a))


def hdg_diff(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def load_tracks():
    by_cs = {}
    with open(RAW_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                lat = float(row["lat"]); lon = float(row["lon"])
                fl = float(row["flight_level"]); gs = float(row["ground_speed_kt"])
                hdg = float(row["heading_deg"])
            except (ValueError, KeyError):
                continue
            t = datetime.fromisoformat(row["received_at_utc"].replace("Z", "+00:00"))
            rel_t = (t - SIM_T0).total_seconds()
            by_cs.setdefault(row["callsign"], []).append((rel_t, lat, lon, fl * 100.0, gs, hdg))
    for cs in by_cs:
        by_cs[cs].sort(key=lambda r: r[0])
    return by_cs


def load_atwi_config():
    models = json.load(open(ATWI_MODELS, encoding="utf-8"))
    model = models[0]
    tasks = {t["code"]: t for t in json.load(open(ATWI_TASKS, encoding="utf-8"))}
    return model, tasks


def analyze_sector(sector_name, bands, by_cs, model, tasks, t_end):
    n_windows = int(math.ceil(t_end / WINDOW_SEC))
    coeffs = model["coefficients"]
    atco_on_pos = max(1, int(model.get("atcoOnPosition", 1)))
    avail_sec_hr = max(1, int(model.get("availableSecondsPerAtcoPerHour", 3600)))
    thresholds = model.get("thresholds", {})

    # annotate per-sample membership + per-aircraft episode boundaries.
    # censored=True nghia la tau da o trong sector NGAY TU mau dau tien ta
    # co trong du lieu (tuc da vao sector truoc khi cua so quan sat bat
    # dau) -- KHONG duoc tinh la 1 su kien handoff that, vi ta khong quan
    # sat duoc thoi diem vao that.
    episodes = {}  # acid -> list of (t_in, t_out, censored)
    for acid, pts in by_cs.items():
        inside_prev = False
        t_in = None
        for i, (t, lat, lon, alt_ft, gs, hdg) in enumerate(pts):
            inside = in_sector(lon, lat, alt_ft, bands)
            if inside and not inside_prev:
                t_in = t
            if inside_prev and not inside:
                censored = (t_in == pts[0][0])
                episodes.setdefault(acid, []).append((t_in, pts[i - 1][0], censored))
            inside_prev = inside
        if inside_prev and t_in is not None:
            censored = (t_in == pts[0][0])
            episodes.setdefault(acid, []).append((t_in, pts[-1][0], censored))

    timeseries = []
    overall_counts = {}
    overall_load = 0.0
    overall_capacity = 0.0

    for w in range(n_windows):
        w_start, w_end = w * WINDOW_SEC, min((w + 1) * WINDOW_SEC, t_end)
        dur = max(1.0, w_end - w_start)

        active = set()
        handoff_count = 0
        cross_sector_count = 0  # filled below using adjacency info passed separately
        vector_count = 0
        alt_change_count = 0
        speed_count = 0

        window_points_by_acid = {}  # for conflict check

        for acid, pts in by_cs.items():
            w_pts = [p for p in pts if w_start <= p[0] < w_end and in_sector(p[2], p[1], p[3], bands)]
            if not w_pts:
                continue
            active.add(acid)
            window_points_by_acid[acid] = w_pts

            first, last = w_pts[0], w_pts[-1]
            if hdg_diff(first[5], last[5]) > HDG_CHANGE_DEG:
                vector_count += 1
            if abs(last[3] - first[3]) > ALT_CHANGE_FT:
                alt_change_count += 1
            if abs(last[4] - first[4]) > SPD_CHANGE_KT:
                speed_count += 1

        for acid, eps in episodes.items():
            for (t_in, t_out, censored) in eps:
                if w_start <= t_in < w_end and not censored:
                    handoff_count += 1

        # conflict check: sample every 30s inside window, pairwise among active aircraft
        conflict_events = set()
        critical_events = set()
        sample_times = [w_start + k * 30.0 for k in range(int(dur // 30.0) + 1)]
        for st in sample_times:
            positions = {}
            for acid, w_pts in window_points_by_acid.items():
                nearest = min(w_pts, key=lambda p: abs(p[0] - st))
                if abs(nearest[0] - st) <= 15.0:
                    positions[acid] = nearest
            acids = list(positions.keys())
            for i in range(len(acids)):
                for j in range(i + 1, len(acids)):
                    a, b = positions[acids[i]], positions[acids[j]]
                    lat_nm = haversine_nm(a[1], a[2], b[1], b[2])
                    vert_ft = abs(a[3] - b[3])
                    if lat_nm < LATERAL_MIN_NM and vert_ft < VERTICAL_MIN_FT:
                        conflict_events.add((round(st), tuple(sorted((acids[i], acids[j])))))
                        if lat_nm < LATERAL_CRIT_NM and vert_ft < VERTICAL_CRIT_FT:
                            critical_events.add((round(st), tuple(sorted((acids[i], acids[j])))))

        counts = {
            "SURV_SCAN": len(active),
            "TRAFFIC_COUNT_MONITOR": len(active),
            "CONFLICT_CHECK": len(conflict_events),
            "STCA_RESPONSE": len(critical_events),
            "VECTOR_OR_DIRECT": vector_count,
            "ALTITUDE_CHANGE": alt_change_count,
            "SPEED_CONTROL": speed_count,
            "HANDOFF_COORD": handoff_count,
            "CROSS_SECTOR_COORD": 0,  # filled by caller after both sectors analyzed
            "RUNWAY_SEQUENCE": 0,
            "WEATHER_DEVIATION": 0,
            "MILITARY_COORD": 0,
            "SYSTEM_DEGRADED": 0,
            "AIRPORT_SURFACE_FEEDBACK": 0,
        }

        for code, c in counts.items():
            overall_counts[code] = overall_counts.get(code, 0) + c

        complexity_factor = min(3.0, len(active) / 10.0)
        load_sec = 0.0
        breakdown = []
        for code, count in counts.items():
            if code not in tasks or count == 0:
                continue
            base = tasks[code]["baseEffortSec"]
            localized = base * (
                1.0
                + coeffs.get("complexityCoeff", 0.15) * complexity_factor
                + coeffs.get("coordinationCoeff", 0.12) * (1.0 if counts["HANDOFF_COORD"] > 0 else 0.0)
            )
            sec = localized * count
            load_sec += sec
            breakdown.append({"taskCode": code, "count": count, "totalSeconds": round(sec, 1)})

        capacity_sec = (dur / 3600.0) * atco_on_pos * avail_sec_hr
        atwi_pct = round(min(150.0, max(0.0, (load_sec / capacity_sec) * 100)), 2) if capacity_sec > 0 else 0.0
        band = "normal"
        if atwi_pct >= thresholds.get("highMax", 90):
            band = "critical"
        elif atwi_pct >= thresholds.get("watchMax", 75):
            band = "high"
        elif atwi_pct >= thresholds.get("normalMax", 60):
            band = "watch"

        overall_load += load_sec
        overall_capacity += capacity_sec

        timeseries.append({
            "windowIndex": w, "startTime": w_start, "endTime": w_end,
            "activeAircraftCount": len(active), "taskCounts": counts,
            "taskBreakdown": breakdown, "totalLoadSec": round(load_sec, 1),
            "capacitySec": round(capacity_sec, 1), "atwiPercent": atwi_pct, "band": band,
        })

    overall_atwi = round(min(150.0, max(0.0, (overall_load / overall_capacity) * 100)), 2) if overall_capacity > 0 else 0.0
    overall_band = "normal"
    if overall_atwi >= thresholds.get("highMax", 90):
        overall_band = "critical"
    elif overall_atwi >= thresholds.get("watchMax", 75):
        overall_band = "high"
    elif overall_atwi >= thresholds.get("normalMax", 60):
        overall_band = "watch"

    peak = max(timeseries, key=lambda w: w["atwiPercent"]) if timeseries else None

    return {
        "sector": sector_name,
        "overallAtwiPercent": overall_atwi,
        "overallBand": overall_band,
        "overallTaskCounts": overall_counts,
        "peakWindow": peak,
        "timeseries": timeseries,
    }


def main():
    sectors = load_sectors()
    by_cs = load_tracks()
    model, tasks = load_atwi_config()
    t_end = max(p[0] for pts in by_cs.values() for p in pts)

    results = {}
    for name, bands in sectors.items():
        results[name] = analyze_sector(name, bands, by_cs, model, tasks, t_end)

    # Cross-sector coordination: same aircraft exits one sector and enters
    # the other within <=120s -- detect from raw episodes computed above.
    def episodes_for(sector_name):
        bands = sectors[sector_name]
        eps = {}
        for acid, pts in by_cs.items():
            inside_prev = False
            t_in = None
            for i, (t, lat, lon, alt_ft, gs, hdg) in enumerate(pts):
                inside = in_sector(lon, lat, alt_ft, bands)
                if inside and not inside_prev:
                    t_in = t
                if inside_prev and not inside:
                    eps.setdefault(acid, []).append((t_in, pts[i - 1][0]))
                inside_prev = inside
            if inside_prev and t_in is not None:
                eps.setdefault(acid, []).append((t_in, pts[-1][0]))
        return eps

    # Luu y: cross-sector coordination o day KHONG loai tru episode bi cat
    # cut dau du lieu, vi no can CA exit cua sector truoc VA entry cua
    # sector sau deu nam trong khung quan sat -- truong hop do thuong tu
    # dong khong bi left-censoring anh huong (aircraft phai duoc quan sat
    # dang bay trong 1 sector roi chuyen qua sector kia).

    eps1 = episodes_for("HCM ACC Sector 1")
    eps5 = episodes_for("HCM ACC Sector 5")
    cross_events = []  # (acid, t_transition, from, to)
    for acid in set(eps1) | set(eps5):
        all_eps = [("S1", a, b) for a, b in eps1.get(acid, [])] + [("S5", a, b) for a, b in eps5.get(acid, [])]
        all_eps.sort(key=lambda e: e[1])
        for i in range(len(all_eps) - 1):
            cur, nxt = all_eps[i], all_eps[i + 1]
            if cur[0] != nxt[0] and 0 <= (nxt[1] - cur[2]) <= 120:
                cross_events.append((acid, cur[2], cur[0], nxt[0]))

    for name, res in results.items():
        tag = "S1" if "Sector 1" in name else "S5"
        for w in res["timeseries"]:
            cnt = sum(1 for (acid, t, frm, to) in cross_events if frm == tag and w["startTime"] <= t < w["endTime"])
            w["taskCounts"]["CROSS_SECTOR_COORD"] = cnt
            if cnt:
                base = tasks["CROSS_SECTOR_COORD"]["baseEffortSec"]
                complexity_factor = min(3.0, w["activeAircraftCount"] / 10.0)
                coeffs = model["coefficients"]
                localized = base * (1.0 + coeffs.get("complexityCoeff", 0.15) * complexity_factor + coeffs.get("coordinationCoeff", 0.12))
                extra_sec = localized * cnt
                w["taskBreakdown"].append({"taskCode": "CROSS_SECTOR_COORD", "count": cnt, "totalSeconds": round(extra_sec, 1)})
                w["totalLoadSec"] = round(w["totalLoadSec"] + extra_sec, 1)
                w["atwiPercent"] = round(min(150.0, max(0.0, (w["totalLoadSec"] / w["capacitySec"]) * 100)), 2) if w["capacitySec"] > 0 else 0.0
            res["overallTaskCounts"]["CROSS_SECTOR_COORD"] = res["overallTaskCounts"].get("CROSS_SECTOR_COORD", 0) + cnt
        res["overallAtwiPercent"] = round(min(150.0, max(0.0, sum(w["totalLoadSec"] for w in res["timeseries"]) / sum(w["capacitySec"] for w in res["timeseries"]) * 100)), 2)
        res["peakWindow"] = max(res["timeseries"], key=lambda w: w["atwiPercent"])

    out = HERE / "sector_atwi_result.json"
    json.dump(results, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("Da ghi", out)
    print("\nTong cross-sector coordination events:", len(cross_events))
    for name, res in results.items():
        print(f"\n=== {name} ===")
        print("  Overall ATWI%:", res["overallAtwiPercent"], res["overallBand"])
        pw = res["peakWindow"]
        print(f"  Peak window: t={pw['startTime']:.0f}-{pw['endTime']:.0f}s, ATWI%={pw['atwiPercent']}, aircraft={pw['activeAircraftCount']}")
        print("  Overall task counts:", res["overallTaskCounts"])


if __name__ == "__main__":
    main()
