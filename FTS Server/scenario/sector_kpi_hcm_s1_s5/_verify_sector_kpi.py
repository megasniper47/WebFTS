"""
Kiem chung DOC LAP ket qua sector_kpi_analyzer.py.

Quy uoc du an (HUONG_DAN_TAO_KICH_BAN.md): script kiem chung phai doc lai
du lieu nguon (geojson, track) tu dau va TU TINH LAI, KHONG duoc tai dung
ham cua sector_kpi_analyzer.py. O day dung thuat toan point-in-polygon
rieng (ray casting), khong dung shapely, de dam bao hai duong tinh doc lap
ve mat thuat toan.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEOJSON = HERE.parent.parent.parent / "WebATM" / "static" / "data" / "vietnam_acc_sector_boundaries.geojson"
TRACK_JSON = HERE / "HCM_S1S5_KPI_20260605_0730-0750.track.json"
RESULT_JSON = HERE / "sector_kpi_result.json"

SECTOR_KEYS = ["HCM ACC Sector 1", "HCM ACC Sector 5"]


def ray_cast_point_in_poly(x, y, ring):
    """Thuat toan ray-casting chuan, viet moi, khong dung thu vien ngoai."""
    n = len(ring)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def parse_alt_range(name: str):
    m = re.search(r"<=FL(\d+)$", name)
    if m:
        return (0, int(m.group(1)) * 100)
    m = re.search(r"FL(\d+)-FL(\d+)$", name)
    if m:
        return (int(m.group(1)) * 100, int(m.group(2)) * 100)
    raise ValueError(f"khong parse duoc dai muc bay tu ten: {name}")


def load_sectors_independent():
    with open(GEOJSON, encoding="utf-8") as f:
        d = json.load(f)
    sectors = {k: [] for k in SECTOR_KEYS}
    found_names = set()
    for feat in d["features"]:
        name = feat["properties"]["name"]
        for key in SECTOR_KEYS:
            if name.startswith(key):
                alt_ft = parse_alt_range(name)
                ring = feat["geometry"]["coordinates"][0]
                sectors[key].append((alt_ft, ring))
                found_names.add(name)
    return sectors, found_names


def in_sector(lon, lat, alt_ft, bands):
    for (lo, hi), ring in bands:
        if lo <= alt_ft <= hi and ray_cast_point_in_poly(lon, lat, ring):
            return True
    return False


def main():
    sectors, found_names = load_sectors_independent()
    print("Cac polygon sector doc duoc (doc lap voi analyzer):")
    for n in sorted(found_names):
        print("  -", n)
    expect = {
        "HCM ACC Sector 1 <=FL265",
        "HCM ACC Sector 1 FL265-FL460",
        "HCM ACC Sector 5 <=FL460",
        "HCM ACC Sector 5 FL305-FL460",
        "HCM ACC Sector 5 FL265-FL460",
    }
    missing = expect - found_names
    assert not missing, f"THIEU polygon: {missing}"

    with open(TRACK_JSON, encoding="utf-8") as f:
        track = json.load(f)
    with open(RESULT_JSON, encoding="utf-8") as f:
        prev_result = json.load(f)

    errors = []
    for sector_name, bands in sectors.items():
        distinct = set()
        peak_count = 0
        peak_t = None
        dwell_total = {}
        occ_at_t = {}

        for acid, pts in track.items():
            inside_prev = False
            t_in = None
            total_dwell = 0.0
            for sample in pts:
                t, lat, lon, alt_ft = sample[0], sample[1], sample[2], sample[3]
                inside = in_sector(lon, lat, alt_ft, bands)
                if inside:
                    distinct.add(acid)
                    occ_at_t.setdefault(t, set()).add(acid)
                if inside and not inside_prev:
                    t_in = t
                if inside_prev and not inside:
                    total_dwell += t - t_in
                inside_prev = inside
            if inside_prev and t_in is not None:
                total_dwell += pts[-1][0] - t_in
            if total_dwell > 0:
                dwell_total[acid] = total_dwell

        for t, s in occ_at_t.items():
            if len(s) > peak_count:
                peak_count = len(s)
                peak_t = t

        avg_dwell = round(sum(dwell_total.values()) / len(dwell_total), 1) if dwell_total else 0.0

        print(f"\n=== KIEM CHUNG DOC LAP: {sector_name} ===")
        print("  so tau khac nhau (tu tinh lai):", len(distinct))
        print("  dinh dong thoi (tu tinh lai):", peak_count, "tai t=", peak_t)
        print("  dwell trung binh (tu tinh lai):", avg_dwell)

        prev = prev_result[sector_name]
        checks = [
            ("distinct_aircraft", len(distinct), prev["distinct_aircraft"]),
            ("peak_count", peak_count, prev["peak_count"]),
            ("avg_dwell_s", avg_dwell, prev["avg_dwell_s"]),
        ]
        for field, new_val, old_val in checks:
            ok = abs(new_val - old_val) < 1e-6 if isinstance(new_val, float) else new_val == old_val
            status = "KHOP" if ok else "LECH!!"
            print(f"    {field}: doc_lap={new_val}  analyzer={old_val}  -> {status}")
            if not ok:
                errors.append((sector_name, field, new_val, old_val))

    print("\n" + "=" * 50)
    if errors:
        print(f"KIEM CHUNG THAT BAI: {len(errors)} truong khong khop")
        for e in errors:
            print("  ", e)
        return 1
    else:
        print("KIEM CHUNG THANH CONG: toan bo so lieu doc lap khop voi sector_kpi_analyzer.py")
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
