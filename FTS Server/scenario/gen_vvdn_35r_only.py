import os
import random
import math
import shutil
import datetime

# --- CONFIGURATION ---
OUT_DIR = r"D:\Coding\Dự án FTS\WebFTS v4\FTS Server\scenario\VVDN_35R_ONLY"
os.makedirs(OUT_DIR, exist_ok=True)

random.seed(20260811)
N_PAIRS = 20
ARR_SPACING_S = 300
DEP_SPACING_S = 300

MEDIUM_TYPES = ["A320", "A321", "A20N", "A21N", "B738", "B38M", "B739"]
HEAVY_TYPES = ["A332", "A333", "A359", "B744", "B763", "B772", "B773", "B77W", "B788", "B789", "B748", "B78X"]

AIRCRAFT_LENGTH_M = {
    "A320": 37.57, "A321": 44.51, "A20N": 37.57, "A21N": 44.51,
    "B738": 39.47, "B38M": 39.47, "B739": 42.11, "E190": 36.24,
    "A332": 58.82, "A333": 63.67, "A359": 66.80, "B744": 70.66,
    "B763": 54.94, "B772": 63.73, "B773": 73.86, "B77W": 73.86,
    "B788": 56.72, "B789": 62.81, "B748": 76.30, "B78X": 68.28,
}
def aircraft_length_m(actype):
    return AIRCRAFT_LENGTH_M.get(actype, 45.0 if actype in MEDIUM_TYPES else 65.0)

# Approach speeds
MEDIUM_APPROACH_SPEEDS = { "A320": (205, 165, 150, 130), "A321": (205, 165, 155, 135), "A20N": (205, 165, 150, 130), "A21N": (215, 170, 155, 140), "B738": (210, 165, 155, 140), "B38M": (225, 175, 160, 160), "B739": (215, 170, 155, 145), "E190": (200, 160, 150, 120) }
HEAVY_APPROACH_SPEEDS = { "A332": (210, 165, 155, 135), "A333": (205, 165, 150, 130), "A359": (215, 170, 155, 145), "B744": (225, 175, 160, 155), "B763": (220, 175, 160, 155), "B772": (210, 165, 155, 135), "B773": (220, 175, 155, 145), "B77W": (230, 180, 160, 160), "B788": (215, 170, 155, 145), "B789": (215, 170, 155, 145), "B748": (225, 180, 160, 160), "B78X": (230, 180, 160, 160) }
APPROACH_SPEEDS = {**MEDIUM_APPROACH_SPEEDS, **HEAVY_APPROACH_SPEEDS}
def approach_speeds(actype): return APPROACH_SPEEDS[actype]

def interp_speed(spd_a, spd_b, frac):
    raw = spd_a + (spd_b - spd_a) * frac
    return int(round(raw / 5.0) * 5)

_total_aircraft = 2 * N_PAIRS
_n_medium = round(_total_aircraft * 0.70)
_n_heavy = _total_aircraft - _n_medium
_type_pool = ([random.choice(MEDIUM_TYPES) for _ in range(_n_medium)] + [random.choice(HEAVY_TYPES) for _ in range(_n_heavy)])
random.shuffle(_type_pool)
_type_pool_iter = iter(_type_pool)
def pick_type(): return next(_type_pool_iter)

_n_e4 = round(N_PAIRS * 0.50)
_n_e6 = N_PAIRS - _n_e4
_exit_pool = ["E4"] * _n_e4 + ["E6"] * _n_e6
random.shuffle(_exit_pool)
_exit_pool_iter = iter(_exit_pool)
def pick_exit(): return next(_exit_pool_iter)

def fmt_t(seconds: float) -> str:
    seconds = round(seconds, 2)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def bearing_deg(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def dest_point(lat, lon, bearing_deg_, dist_m):
    R = 6371000.0
    br = math.radians(bearing_deg_)
    lat1, lon1 = math.radians(lat), math.radians(lon)
    dr = dist_m / R
    lat2 = math.asin(math.sin(lat1) * math.cos(dr) + math.cos(lat1) * math.sin(dr) * math.cos(br))
    lon2 = lon1 + math.atan2(math.sin(br) * math.sin(dr) * math.cos(lat1), math.cos(dr) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)

def leg_times_s(points_with_spd_kt, start_latlon):
    KT = 0.514444
    total_t = 0.0
    prev = start_latlon
    prev_spd = None
    for lat, lon, spd in points_with_spd_kt:
        d = haversine_m(prev[0], prev[1], lat, lon)
        v0 = prev_spd if prev_spd else spd
        avg_v = max(((v0 + spd) / 2) * KT, 1.0)
        total_t += d / avg_v
        prev = (lat, lon)
        prev_spd = spd
    return total_t

def tas_correction(alt_ft): return 1.0 + 0.00002 * max(alt_ft, 0.0)

def estimate_transit_s(chain_with_alt, start_latlon):
    legs = [(lat, lon, spd * tas_correction(alt)) for (lat, lon, alt, spd) in chain_with_alt]
    return leg_times_s(legs, start_latlon)

CADAS = (15.618056, 108.262500)

STAR_IAF = {
    "HUE": (16.402222, 107.701667, 24000, 280),
    "CAHEO": (16.536389, 107.965278, 24000, 280),
    "BUNTA": (16.833333, 109.395000, 24000, 280),
    "KUMUN": (14.971389, 108.807500, 25000, 280),
    "SADIN": (15.080000, 108.177222, 25000, 280),
    "VILOT": (15.038611, 108.111667, 25000, 280),
    "LATOM": (14.879444, 107.843611, 25000, 280),
    "PAPRA": (15.766667, 107.183333, 25000, 280),
}

_CHAIN_HINTA_ONWARD = [ (16.167500, 108.048611, 15000, 280), (16.020000, 108.081667, 12000, 250), (15.854722, 108.105278, 8000, 250), (15.767222, 108.118333, 6070, 250) ]
_CHAIN_NOCKA_ONWARD = [ (15.419444, 108.046667, 16000, 280), (15.585278, 108.022500, 12000, 280), (15.750833, 107.998611, 8500, 250), (15.767222, 108.118333, 6070, 250) ]

STAR_CHAINS = {
    "HUE": _CHAIN_HINTA_ONWARD, "CAHEO": _CHAIN_HINTA_ONWARD,
    "BUNTA": [ (16.354167, 108.664722, 24000, 280), (16.258056, 108.507222, 22000, 280), (15.908611, 108.512500, 15000, 250), (15.820556, 108.512778, 12000, 240), (15.799722, 108.358056, 9500, 230), (15.633889, 108.381667, 8000, 225) ],
    "KUMUN": _CHAIN_NOCKA_ONWARD,
    "SADIN": [(15.262778, 108.106944, 20000, 280)] + _CHAIN_NOCKA_ONWARD,
    "VILOT": [(15.254444, 108.074722, 20000, 280)] + _CHAIN_NOCKA_ONWARD,
    "LATOM": [(15.262500, 107.987500, 20000, 280)] + _CHAIN_NOCKA_ONWARD,
    "PAPRA": [ (15.748611, 107.733056, 14000, 280), (15.750833, 107.998611, 8500, 250), (15.767222, 108.118333, 6070, 250) ],
}

_TRACO = (15.601667, 108.142222, 7695, 230)
_CADAS_PLACEHOLDER = (CADAS[0], CADAS[1], 6071, 225)

def _full_pre_cadas_chain(star):
    if star == "BUNTA": return STAR_CHAINS[star]
    return STAR_CHAINS[star] + [_TRACO]

_SID_INITIAL = (16.076637, 108.195656, 1500, 180)
_SID_DN456 = (16.334167, 108.192500, 8038, 250)
_SID_DN450 = (16.174444, 108.194722, 4000, 200)

_SID_NORTH_TRUNK = [ _SID_DN456, (16.586667, 108.135278, 11000, 260), (16.694722, 107.888611, 14000, 280) ]
_SID_SOUTH_TRUNK = [ _SID_DN450, (16.177222, 108.387778, 6000, 250), (16.093333, 108.388889, 7054, 240), (15.909444, 108.391389, 10000, 260) ]

SID_CHAINS = {
    "PHULU": [_SID_INITIAL] + _SID_NORTH_TRUNK,
    "KONCO": [_SID_INITIAL] + _SID_NORTH_TRUNK + [ (16.895833, 107.426944, 18000, 300), (17.000000, 107.186944, 21000, 310) ],
    "VIDEN": [_SID_INITIAL] + _SID_NORTH_TRUNK + [ (16.895833, 107.426944, 18000, 300), (17.020556, 107.365556, 21000, 310) ],
    "BUNTA": [_SID_INITIAL, _SID_DN456, (16.451111, 108.578611, 11000, 260), (16.559722, 108.973056, 16000, 290), (16.833333, 109.395000, 20000, 310) ],
    "KUMUN": [_SID_INITIAL] + _SID_SOUTH_TRUNK + [ (15.543333, 108.395833, 14000, 280), (14.971389, 108.807500, 18000, 300) ],
    "SADIN": [_SID_INITIAL] + _SID_SOUTH_TRUNK + [ (15.543333, 108.395833, 14000, 280), (15.080000, 108.177222, 17000, 290) ],
    "XAQUA": [_SID_INITIAL] + _SID_SOUTH_TRUNK + [ (15.543333, 108.395833, 14000, 280), (15.080000, 108.177222, 17000, 290), (14.919444, 108.101667, 19000, 300) ],
    "PAPRA": [_SID_INITIAL] + _SID_SOUTH_TRUNK + [ (15.906944, 108.061944, 18000, 290), (15.905833, 107.931111, 20000, 300), (15.903333, 107.658889, 21000, 300), (15.766667, 107.183333, 22000, 310) ],
}
SID_NAMES = list(SID_CHAINS.keys())

def post_cadas_legs(actype):
    s25, s10, s5, std = approach_speeds(actype)
    s_20nm = interp_speed(s25, s10, (25.0 - 19.994) / (25.0 - 10.0))
    s_14_7nm = interp_speed(s25, s10, (25.0 - 14.675) / (25.0 - 10.0))
    s_4_4nm = interp_speed(s5, std, (5.0 - 4.42) / 5.0)
    return [
        (15.618056, 108.262500, 6071, s25),
        (15.700556, 108.250000, 4921, s_20nm),
        (15.788333, 108.237500, 4429, s_14_7nm),
        (15.865171, 108.224271, 2592, s10),
        (15.947115, 108.212410, 1611, s5),
        (15.957222, 108.210944, 1476, s_4_4nm),
        (16.029200, 108.202500, 0, std), # Threshold 35R
    ]

files = {}
def add_file(name, content):
    files[name] = content

add_file("_KB5GEN_STOP_HOLD.scn", """# _KB5GEN_STOP_HOLD.scn
00:00:00.00>%0 LNAV OFF
00:00:00.00>%0 VNAV OFF
00:00:00.00>MOVE %0,%1,%2,0,%3,0.0
""")

add_file("_KB5GEN_STOP_AND_DEL.scn", """# _KB5GEN_STOP_AND_DEL.scn — dừng cứng tại bến đỗ rồi xoá sau 10s
00:00:00.00>%0 LNAV OFF
00:00:00.00>%0 VNAV OFF
00:00:00.00>MOVE %0,%1,%2,0,%3,0.0
00:00:00.00>PCALL _KB5v2_DEL_AFTER10 %0
""")

add_file("_KB5v2_DEL_AFTER10.scn", """# Xóa sau 10 giây
00:00:10.00>DEL %0
""")

def make_arr_approach_file_for_pair(p):
    actype = p["arr_type"]
    star = p.get("star")
    post_legs = post_cadas_legs(actype)
    if star is None:
        legs = post_legs[1:]
    elif p.get("cre_override"):
        pre_legs = p["cre_override"]["remaining_nodes"]
        legs = pre_legs + post_legs
    else:
        pre_legs = _full_pre_cadas_chain(star)
        legs = pre_legs + post_legs
    
    new_legs = []
    prev_alt = 99999
    for (lat, lon, alt, spd) in legs:
        alt = min(alt, prev_alt)
        new_legs.append((lat, lon, alt, spd))
        prev_alt = alt
    legs = new_legs
    lines_txt = "\n".join(f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} {alt} {spd}" for (lat, lon, alt, spd) in legs)
    add_file(f"_KB5GEN_ARR_APPROACH_{p['arr_id']}.scn", f"""# Khống chế giảm độ cao mượt
{lines_txt}
""")

# Thoát ly E4 về Gate 24
add_file("_KB5GEN_ARR_EXIT_E4.scn", """# E4 Exit to Gate 24
00:00:00.00>%0 ADDWPT 16.035000,108.201700 0 120
00:00:00.00>%0 ADDWPT 16.040000,108.201000 0 90
00:00:00.00>%0 ADDWPT 16.045000,108.200300 0 60
00:00:00.00>%0 ADDWPT 16.049007,108.199646 0 15
00:00:00.00>%0 ADDWPT 16.049200,108.201005 0 10
00:00:00.00>%0 ADDWPT 16.051000,108.202500 0 0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST 16.051000,108.202500,0.025 PCALL _KB5GEN_STOP_AND_DEL %0 16.051000 108.202500 81.0
""")

# Thoát ly E6 về Gate 11
add_file("_KB5GEN_ARR_EXIT_E6.scn", """# E6 Exit to Gate 11
00:00:00.00>%0 ADDWPT 16.035000,108.201700 0 130
00:00:00.00>%0 ADDWPT 16.045000,108.200300 0 90
00:00:00.00>%0 ADDWPT 16.055000,108.198800 0 30
00:00:00.00>%0 ADDWPT 16.057400,108.198411 0 15
00:00:00.00>%0 ADDWPT 16.057596,108.199801 0 10
00:00:00.00>%0 ADDWPT 16.058500,108.201500 0 0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 ATDIST 16.058500,108.201500,0.025 PCALL _KB5GEN_STOP_AND_DEL %0 16.058500 108.201500 81.0
""")

add_file("_KB5GEN_DEP_ENTER_RWY.scn", """# Lên 35R
00:00:00.00>%0 ADDWPT 16.029181,108.202508 0 5.0
00:00:00.00>%0 ADDWPT 16.029200,108.202500 0 5.0
00:00:00.00>%0 ADDWPT 16.030000,108.202000 0 5.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
00:00:00.00>%0 SPD 5.0
""")

def make_dep_roll_file_for_pair(p):
    sid = p["sid"]
    legs = SID_CHAINS[sid]
    lines_txt = "\n".join(f"00:00:30.00>%0 ADDWPT {lat:.6f},{lon:.6f} {alt} {spd}" for (lat, lon, alt, spd) in legs)
    add_file(f"_KB5GEN_DEP_ROLL_{p['dep_id']}.scn", f"""# Cất cánh
00:00:00.00>TAXIOFF %0
00:00:30.00>%0 DELRTE
{lines_txt}
00:00:30.00>%0 LNAV ON
00:00:30.00>%0 VNAV OFF
00:00:30.00>%0 SPD 250
00:00:30.00>%0 VS 2000
00:00:30.00>%0 ALT 10000
00:00:30.00>%0 ATALT 1500 PCALL _KB5GEN_VNAV_ON %0
""")

add_file("_KB5GEN_VNAV_ON.scn", """00:00:00.00>%0 VNAV ON\n""")

GATE24 = (16.051000, 108.202500, 80.9)
GATE11 = (16.058500, 108.201500, 80.9)
RWYHOLD = (16.029200, 108.202500, 352.1)
PREHOLD = (16.029259, 108.203066, 263.0)

TAXI_COMMON = [
    (16.049490, 108.200986, 15.0), (16.044100, 108.201789, 18.0),
    (16.038291, 108.202625, 18.0), (16.030836, 108.203677, 15.0),
    (16.029967, 108.203803, 10.0), (16.029680, 108.203824, 8.0),
    (16.029490, 108.203744, 6.0), (16.029355, 108.203538, 5.0)
]
def make_taxi_file(name, points, dest):
    dlat, dlon, dhdg = dest
    add_file(name, f"""# Lăn ra
{chr(10).join(f"00:00:00.00>%0 ADDWPT {lat:.6f},{lon:.6f} 0 {spd}" for lat, lon, spd in points)}
00:00:00.00>%0 ADDWPT {dlat:.6f},{dlon:.6f} 0 0.0
00:00:00.00>%0 LNAV ON
00:00:00.00>%0 VNAV ON
""")

make_taxi_file("_KB5GEN_TAXI_G24_RWYHOLD.scn", [(16.049200, 108.201005, 10.0)] + TAXI_COMMON, RWYHOLD)
make_taxi_file("_KB5GEN_TAXI_G11_RWYHOLD.scn", [(16.057596, 108.199801, 10.0), (16.049200, 108.201005, 15.0)] + TAXI_COMMON, RWYHOLD)
make_taxi_file("_KB5GEN_TAXI_G24_PREHOLD.scn", [(16.049200, 108.201005, 10.0)] + TAXI_COMMON, PREHOLD)
make_taxi_file("_KB5GEN_TAXI_G11_PREHOLD.scn", [(16.057596, 108.199801, 10.0), (16.049200, 108.201005, 15.0)] + TAXI_COMMON, PREHOLD)

def make_pushback_file(name, gate, taxi_first_point):
    glat, glon, ghdg = gate
    back_hdg = (ghdg + 180.0) % 360.0
    mid_lat, mid_lon = dest_point(glat, glon, back_hdg, 18.0)
    end_lat, end_lon = dest_point(glat, glon, back_hdg, 35.0)
    taxi_hdg = bearing_deg(end_lat, end_lon, taxi_first_point[0], taxi_first_point[1])
    add_file(name, f"""00:00:00.00>%0 LNAV OFF
00:00:00.00>%0 VNAV OFF
00:00:00.00>MOVE %0,{mid_lat:.6f},{mid_lon:.6f},0,{ghdg},0.0
00:00:05.00>MOVE %0,{end_lat:.6f},{end_lon:.6f},0,{taxi_hdg:.1f},0.0
00:00:07.00>TAXION %0 15 %2
00:00:07.00>PCALL %1 %0
""")
make_pushback_file("_KB5GEN_PUSHBACK_G24.scn", GATE24, (16.049200, 108.201005))
make_pushback_file("_KB5GEN_PUSHBACK_G11.scn", GATE11, (16.057596, 108.199801))

# SPATIAL LOGIC
_STAR_TRANSIT = {name: estimate_transit_s(_full_pre_cadas_chain(name) + [_CADAS_PLACEHOLDER], (STAR_IAF[name][0], STAR_IAF[name][1])) for name in STAR_IAF}
def _star_nodes(star): return [(STAR_IAF[star][0], STAR_IAF[star][1], STAR_IAF[star][2], STAR_IAF[star][3])] + _full_pre_cadas_chain(star) + [_CADAS_PLACEHOLDER]
def _remaining_transit_per_node(nodes):
    n = len(nodes)
    remaining = [0.0] * n
    for j in range(n - 2, -1, -1):
        lat0, lon0, _alt0, _spd0 = nodes[j]
        lat1, lon1, alt1, spd1 = nodes[j + 1]
        remaining[j] = haversine_m(lat0, lon0, lat1, lon1) / (spd1 * tas_correction(alt1) * 0.514444) + remaining[j + 1]
    return remaining
def truncated_star_spawn(star, target_cadas_t):
    nodes = _star_nodes(star)
    remaining = _remaining_transit_per_node(nodes)
    for j in range(len(nodes) - 1):
        if remaining[j] >= target_cadas_t >= remaining[j + 1]:
            lat0, lon0, alt0, _spd0 = nodes[j]
            lat1, lon1, alt1, spd1 = nodes[j + 1]
            leg_t = remaining[j] - remaining[j + 1]
            frac = min(max(0.0 if leg_t <= 0 else (remaining[j] - target_cadas_t) / leg_t, 0.0), 1.0)
            return (lat0 + (lat1 - lat0) * frac, lon0 + (lon1 - lon0) * frac, round(alt0 + (alt1 - alt0) * frac), spd1, round(bearing_deg(lat0 + (lat1 - lat0) * frac, lon0 + (lon1 - lon0) * frac, lat1, lon1), 1), nodes[j + 1:-1])
    return (nodes[-2][0], nodes[-2][1], nodes[-2][2], nodes[-2][3], round(bearing_deg(nodes[-2][0], nodes[-2][1], nodes[-1][0], nodes[-1][1]), 1), [])

pairs = []
for i in range(1, N_PAIRS + 1):
    arr_id, dep_id = f"ARR{i:03d}", f"DEP{i:03d}"
    dep_t = (i - 1) * DEP_SPACING_S
    exit_choice = pick_exit()
    star = random.choices(["HUE", "CAHEO", "KUMUN", "SADIN", "VILOT", "LATOM", "BUNTA", "PAPRA"], weights=[17.5, 17.5, 8.75, 8.75, 8.75, 8.75, 15, 15], k=1)[0]
    gate, gate_name = (GATE24, "G24") if i % 2 == 1 else (GATE11, "G11")
    target_cadas_t = (i - 1) * ARR_SPACING_S - 36
    cre_override = None
    if i == 1: star, arr_t, transit_est_s = None, 0.0, 0.0
    else:
        if _STAR_TRANSIT[star] <= target_cadas_t: transit_est_s, arr_t = _STAR_TRANSIT[star], target_cadas_t - _STAR_TRANSIT[star]
        else:
            lat, lon, alt, spd, hdg, r_nodes = truncated_star_spawn(star, target_cadas_t)
            cre_override, transit_est_s, arr_t = {"lat": lat, "lon": lon, "alt": alt, "spd": spd, "hdg": hdg, "remaining_nodes": r_nodes}, target_cadas_t, 0.0
    pairs.append({"i": i, "arr_id": arr_id, "dep_id": dep_id, "arr_t": arr_t, "dep_t": dep_t, "exit": exit_choice, "arr_type": pick_type(), "dep_type": pick_type(), "sid": random.choice(SID_NAMES), "gate": gate, "gate_name": gate_name, "star": star, "cre_override": cre_override})

for p in pairs:
    make_arr_approach_file_for_pair(p)
    make_dep_roll_file_for_pair(p)

lines = ["00:00:00.00>PLUGINS LOAD SURFACETAXI", "00:00:00.00>PLUGINS LOAD DEPARRALERT", "00:00:00.00>TRAILS ON", "00:00:00.00>ASAS OFF", "00:00:00.00>PAN 16.0400,108.2000"]
for p in pairs:
    i, arr_t_s, dep_t_s = p["i"], fmt_t(p["arr_t"]), fmt_t(p["dep_t"])
    is_first_dep = (i == 1)
    taxi_tpl = f"_KB5GEN_TAXI_{p['gate_name']}_{'RWYHOLD' if is_first_dep else 'PREHOLD'}"
    if p["star"] is None: arr_cre = f"15.6513,108.2575,353,5607,230"
    elif p.get("cre_override"): arr_cre = f"{p['cre_override']['lat']},{p['cre_override']['lon']},{p['cre_override']['hdg']},{p['cre_override']['alt']},{p['cre_override']['spd']}"
    else: arr_cre = f"{STAR_IAF[p['star']][0]},{STAR_IAF[p['star']][1]},{round(bearing_deg(STAR_IAF[p['star']][0], STAR_IAF[p['star']][1], STAR_CHAINS[p['star']][0][0], STAR_CHAINS[p['star']][0][1]), 1)},{STAR_IAF[p['star']][2]},{STAR_IAF[p['star']][3]}"
    
    lines.append(f"""
{dep_t_s}>CRE {p['dep_id']},{p['dep_type']},{p['gate'][0]},{p['gate'][1]},{p['gate'][2]},0,0
{dep_t_s}>PCALL _KB5GEN_PUSHBACK_{p['gate_name']} {p['dep_id']} {taxi_tpl} {aircraft_length_m(p['dep_type']):.1f}
{arr_t_s}>CRE {p['arr_id']},{p['arr_type']},{arr_cre}
{arr_t_s}>PCALL _KB5GEN_ARR_APPROACH_{p['arr_id']} {p['arr_id']}
{arr_t_s}>PCALL _KB5GEN_ARR_EXIT_{p['exit']} {p['arr_id']}
{arr_t_s}>{p['arr_id']} ATDIST 16.029200,108.202500,0.05 PCALL _KB5GEN_DEP_ENTER_RWY {p['dep_id']}
{dep_t_s}>{p['dep_id']} ATDIST 16.030000,108.202000,0.02 PCALL _KB5GEN_DEP_ROLL_{p['dep_id']} {p['dep_id']}
""")

add_file("VVDN_35R_ONLY.scn", "\n".join(lines))

for fname, content in files.items():
    with open(f"{OUT_DIR}/{fname}", "w", encoding="utf-8") as f:
        f.write(content)
print(f"DONE. Generated {len(files)} files in {OUT_DIR}.")
