"""
Kiem chung DOC LAP ket qua sector_atwi_analyzer.py.

Doc lai du lieu nguon tu dau va TU TINH LAI bang code viet rieng (khong goi
ham cua sector_atwi_analyzer.py), tap trung vao 3 diem de sai nhat:
  1. HANDOFF_COORD khong duoc tinh trung voi episode bi cat cut dau du lieu
     (left-censored) -- dem lai bang tay cho tung tau.
  2. CONFLICT_CHECK = 0 co that khong -- kiem tra VET CAN moi cap mau that
     (khong lay mau 30s nhu analyzer) trong toan bo khung 40 phut cho ca 2
     sector, dam bao khong bo sot vi lay mau thua.
  3. Cong thuc ATWI% cho 1 cua so cu the (window 0, Sector 1) tu tinh lai
     tu dau, so voi gia tri analyzer da ghi.
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
RESULT_JSON = HERE / "sector_atwi_result.json"
SIM_T0 = datetime(2026, 6, 5, 7, 20, 0, tzinfo=timezone.utc)
LATERAL_MIN_NM, VERTICAL_MIN_FT = 5.0, 1000.0


def parse_alt_range(name):
    m = re.search(r"<=FL(\d+)$", name)
    if m:
        return (0, int(m.group(1)) * 100)
    m = re.search(r"FL(\d+)-FL(\d+)$", name)
    return (int(m.group(1)) * 100, int(m.group(2)) * 100)


def load_sectors():
    d = json.load(open(GEOJSON, encoding="utf-8"))
    sectors = {"HCM ACC Sector 1": [], "HCM ACC Sector 5": []}
    for feat in d["features"]:
        name = feat["properties"]["name"]
        for key in sectors:
            if name.startswith(key):
                alt = parse_alt_range(name)
                ring = feat["geometry"]["coordinates"][0]
                sectors[key].append((alt, prep(Polygon(ring))))
    return sectors


def in_sector(lon, lat, alt_ft, bands):
    pt = Point(lon, lat)
    return any(lo <= alt_ft <= hi and poly.contains(pt) for (lo, hi), poly in bands)


def haversine_nm(lat1, lon1, lat2, lon2):
    R = 3440.065
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_tracks():
    by_cs = {}
    for row in csv.DictReader(open(RAW_CSV, encoding="utf-8")):
        try:
            lat, lon = float(row["lat"]), float(row["lon"])
            fl = float(row["flight_level"])
        except (ValueError, KeyError):
            continue
        t = datetime.fromisoformat(row["received_at_utc"].replace("Z", "+00:00"))
        rel_t = (t - SIM_T0).total_seconds()
        by_cs.setdefault(row["callsign"], []).append((rel_t, lat, lon, fl * 100.0))
    for cs in by_cs:
        by_cs[cs].sort(key=lambda r: r[0])
    return by_cs


def main():
    sectors = load_sectors()
    by_cs = load_tracks()
    prev = json.load(open(RESULT_JSON, encoding="utf-8"))
    errors = []

    print("### 1. Kiem chung HANDOFF_COORD (loai bo episode left-censored) ###")
    for sname, bands in sectors.items():
        total_handoff = 0
        for acid, pts in by_cs.items():
            inside_prev = False
            t_in = None
            for i, (t, lat, lon, alt_ft) in enumerate(pts):
                inside = in_sector(lon, lat, alt_ft, bands)
                if inside and not inside_prev:
                    t_in = t
                if inside_prev and not inside:
                    if t_in != pts[0][0]:
                        total_handoff += 1
                inside_prev = inside
            if inside_prev and t_in is not None and t_in != pts[0][0]:
                total_handoff += 1
        prev_total = prev[sname]["overallTaskCounts"]["HANDOFF_COORD"]
        ok = total_handoff == prev_total
        print(f"  {sname}: doc_lap={total_handoff}  analyzer={prev_total}  -> {'KHOP' if ok else 'LECH!!'}")
        if not ok:
            errors.append((sname, "HANDOFF_COORD", total_handoff, prev_total))

    print("\n### 2. Kiem chung CONFLICT_CHECK (vet can MOI CAP MAU THAT, khong lay mau 30s) ###")
    for sname, bands in sectors.items():
        # per-sector membership intervals already known from part 1; here just
        # check every real sample of every aircraft against every other
        # aircraft's real samples within +-10s (typical radar cross-check window)
        samples = []  # (acid, t, lat, lon, alt_ft)
        for acid, pts in by_cs.items():
            for (t, lat, lon, alt_ft) in pts:
                if in_sector(lon, lat, alt_ft, bands):
                    samples.append((acid, t, lat, lon, alt_ft))
        samples.sort(key=lambda s: s[1])
        conflicts_found = 0
        n = len(samples)
        for i in range(n):
            a = samples[i]
            for j in range(i + 1, n):
                b = samples[j]
                if b[1] - a[1] > 10.0:
                    break
                if a[0] == b[0]:
                    continue
                lat_nm = haversine_nm(a[2], a[3], b[2], b[3])
                vert_ft = abs(a[4] - b[4])
                if lat_nm < LATERAL_MIN_NM and vert_ft < VERTICAL_MIN_FT:
                    conflicts_found += 1
        prev_total = prev[sname]["overallTaskCounts"]["CONFLICT_CHECK"]
        print(f"  {sname}: so cap mau vi pham phan cach phat hien doc lap (exhaustive, +-10s)={conflicts_found}  analyzer(CONFLICT_CHECK, lay mau 30s)={prev_total}")
        if conflicts_found > 0 and prev_total == 0:
            errors.append((sname, "CONFLICT_CHECK", conflicts_found, prev_total))

    print("\n### 3. Kiem chung cong thuc ATWI% cho Sector 1, window 0 (t=0-300s) ###")
    model = json.load(open(ATWI_MODELS, encoding="utf-8"))[0]
    tasks = {t["code"]: t for t in json.load(open(ATWI_TASKS, encoding="utf-8"))}
    w0 = prev["HCM ACC Sector 1"]["timeseries"][0]
    coeffs = model["coefficients"]
    complexity_factor = min(3.0, w0["activeAircraftCount"] / 10.0)
    handoff_present = w0["taskCounts"]["HANDOFF_COORD"] > 0
    load = 0.0
    for code, count in w0["taskCounts"].items():
        if code not in tasks or count == 0:
            continue
        base = tasks[code]["baseEffortSec"]
        localized = base * (1.0 + coeffs["complexityCoeff"] * complexity_factor + coeffs["coordinationCoeff"] * (1.0 if handoff_present else 0.0))
        load += localized * count
    capacity = (300.0 / 3600.0) * model["atcoOnPosition"] * model["availableSecondsPerAtcoPerHour"]
    atwi = round(min(150.0, max(0.0, load / capacity * 100)), 2)
    ok = abs(atwi - w0["atwiPercent"]) < 0.5
    print(f"  doc_lap: load={load:.1f}s capacity={capacity:.1f}s atwi%={atwi}  analyzer={w0['atwiPercent']}  -> {'KHOP' if ok else 'LECH!!'}")
    if not ok:
        errors.append(("Sector1_window0", "atwiPercent", atwi, w0["atwiPercent"]))

    print("\n" + "=" * 50)
    if errors:
        print(f"KIEM CHUNG PHAT HIEN {len(errors)} DIEM LECH:")
        for e in errors:
            print(" ", e)
        return 1
    print("KIEM CHUNG THANH CONG: toan bo diem kiem tra khop voi sector_atwi_analyzer.py")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
