import datetime
import random

def sec_to_hms(seconds):
    return str(datetime.timedelta(seconds=int(seconds))).zfill(8)

def generate_scenario():
    output_lines = [
        "00:00:00>PAN 16.030 108.201",
        "00:00:00>ZOOM 11",
        "",
        "# Bat tinh nang canh bao xung dot (STCA / ASAS)",
        "00:00:00>ASAS ON",
        "00:00:00>ZONER 3",
        "00:00:00>ZONEDH 1000",
        ""
    ]

    # Fleet mix from FPL data
    ac_types = [
        {"type": "A321", "v_app": 140, "v_1": 151, "rod": -750, "weight": 4},
        {"type": "A21N", "v_app": 140, "v_1": 151, "rod": -750, "weight": 3},
        {"type": "B38M", "v_app": 142, "v_1": 155, "rod": -760, "weight": 1},
        {"type": "B788", "v_app": 145, "v_1": 160, "rod": -780, "weight": 1},
        {"type": "AT72", "v_app": 115, "v_1": 110, "rod": -620, "weight": 1}
    ]
    
    # Precise ARINC 424 Routes extracted from PDFs
    sids_routes = {
        "VIDEN 2G": ["DN456", "LAIKA", "PHULU", "TRABE", "VIDEN"],
        "BUNTA 2G": ["DN456", "HOKIN", "BINKU", "BUNTA"],
        "PAPRA 2G": ["DN450", "DN451", "DN452", "DN453", "DN454", "DN455", "TANNA", "PAPRA"],
        "KUMUN 1G": ["DN450", "DN451", "DN452", "DN453", "KEMSY", "KUMUN"],
        "SADIN 1G": ["DN450", "DN451", "DN452", "DN453", "KEMSY", "SADIN"],
        "XAQUA 1G": ["DN450", "DN451", "DN452", "DN453", "KEMSY", "SADIN", "XAQUA"],
        "PHULU 1G": ["DN456", "LAIKA", "PHULU"]
    }

    sid_names = list(sids_routes.keys())

    pop_ac = []
    for ac in ac_types:
        pop_ac.extend([ac] * ac["weight"])

    for i in range(20):
        t_off = i * 180
        callsign_arr = f"HVN35L_{i+1}"
        
        ac_arr = random.choice(pop_ac)
        ac_dep = random.choice(pop_ac)
        sid_name = random.choice(sid_names)
        sid_waypoints = sids_routes[sid_name]

        t_cre_arr = sec_to_hms(t_off)
        t_spd150_arr = sec_to_hms(t_off + 60)
        t_faf_sec = t_off + 118
        t_faf_arr = sec_to_hms(t_faf_sec)
        
        dist_faf_td = 4.6
        time_to_td = (dist_faf_td / ac_arr["v_app"]) * 3600
        t_td_sec = t_faf_sec + time_to_td
        t_td_arr = sec_to_hms(t_td_sec)
        
        t_del_arr = sec_to_hms(t_td_sec + 100)

        output_lines.extend([
            f"# =========================================================================",
            f"# CAP {i+1} - HA CANH ({ac_arr['type']} - {t_cre_arr})",
            f"# =========================================================================",
            f"{t_cre_arr}>CRE {callsign_arr} {ac_arr['type']} 15.865355 108.224434 352.0 3000 180",
            f"{t_cre_arr}>ALT {callsign_arr} 1600 -800",
            f"{t_spd150_arr}>SPD {callsign_arr} 150",
            f"{t_faf_arr}>SPD {callsign_arr} {ac_arr['v_app']}",
            f"{t_faf_arr}>ALT {callsign_arr} 33 {ac_arr['rod']}",
            f"{t_td_arr}>SPD {callsign_arr} 30",
            f"{t_del_arr}>DEL {callsign_arr}",
            ""
        ])

        # TAKEOFF
        callsign_dep = f"HVN35R_{i+1}"
        t_cre_dep_sec = t_td_sec + 20
        t_roll_dep_sec = t_td_sec + 30
        
        time_to_v1 = (ac_dep["v_1"] / 150) * 35 
        t_rot_dep_sec = t_roll_dep_sec + time_to_v1
        
        t_turn_sec = t_rot_dep_sec + 45
        
        t_cre_dep = sec_to_hms(t_cre_dep_sec)
        t_roll_dep = sec_to_hms(t_roll_dep_sec)
        t_rot_dep = sec_to_hms(t_rot_dep_sec)
        t_turn_dep = sec_to_hms(t_turn_sec)
        t_del_dep = sec_to_hms(t_rot_dep_sec + 300)

        output_lines.extend([
            f"# CAP {i+1} - CAT CANH ({ac_dep['type']} - {t_roll_dep}) - SID {sid_name}",
            f"{t_cre_dep}>CRE {callsign_dep} {ac_dep['type']} 16.0292 108.2025 352.0 33 0",
            f"{t_roll_dep}>ALT {callsign_dep} 33",
            f"{t_roll_dep}>SPD {callsign_dep} {ac_dep['v_1']}",
            f"{t_roll_dep}>HDG {callsign_dep} 352.0",
            f"{t_rot_dep}>ALT {callsign_dep} 10000",
            f"{t_rot_dep}>SPD {callsign_dep} 250",
        ])
        
        # Add full SID waypoints
        for wpt in sid_waypoints:
            output_lines.append(f"{t_turn_dep}>ADDWPT {callsign_dep} {wpt}")
            
        output_lines.extend([
            f"{t_turn_dep}>LNAV {callsign_dep} ON",
            f"{t_del_dep}>DEL {callsign_dep}",
            ""
        ])

    with open(r"FTS Server\scenario\vvdn_60min_real.scn", "w") as f:
        f.write("\n".join(output_lines))
    print("Scenario vvdn_60min_real.scn generated successfully with full SID trajectories.")

if __name__ == "__main__":
    generate_scenario()
