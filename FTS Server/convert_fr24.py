#!/usr/bin/env python3
"""
Flightradar24 CSV to BlueSky Scenario (.scn) Converter
Author: Antigravity

This script converts Flightradar24 downloaded CSV files into a BlueSky scenario (.scn) file.
It supports:
1. Flight Path History CSV (single flight data points recorded over time).
2. Flight List CSV (multiple flights at a specific moment).

It also has a built-in feature to shift/offset coordinates to Vietnam (Hanoi/HCMC/Da Nang) 
if the original flights were recorded elsewhere!
"""

import os
import csv
import sys
import argparse

def convert_fr24_csv(input_csv, output_scn, shift_to_vietnam=False, callsign_filter=None):
    if not os.path.exists(input_csv):
        print(f"Error: Input file {input_csv} does not exist.")
        return False
        
    print(f"Reading Flightradar24 CSV from: {input_csv}")
    
    flights = []
    
    with open(input_csv, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        # Standardize field names by stripping spaces and converting to lowercase
        fields = {field.strip().lower(): field for field in reader.fieldnames} if reader.fieldnames else {}
        
        # Determine CSV Type
        is_path_history = 'position' in fields or ('latitude' in fields and 'longitude' in fields and 'timestamp' in fields)
        
        row_count = 0
        for row in reader:
            row_count += 1
            # Strip spaces from values
            row_clean = {k.strip(): v.strip() for k, v in row.items() if k is not None}
            
            # Extract basic variables
            callsign = ""
            for possible_key in ['callsign', 'flight', 'flight number', 'ident']:
                k = fields.get(possible_key)
                if k and row_clean.get(k):
                    callsign = row_clean[k]
                    break
                    
            if not callsign:
                callsign = f"FLT{row_count}"
                
            if callsign_filter and callsign_filter.lower() not in callsign.lower():
                continue
                
            ac_type = ""
            for possible_key in ['type', 'aircraft type', 'aircraft', 'model']:
                k = fields.get(possible_key)
                if k and row_clean.get(k):
                    ac_type = row_clean[k]
                    break
            if not ac_type:
                ac_type = "A320" # Default aircraft type
                
            # Altitude
            alt_val = 30000
            for possible_key in ['altitude', 'alt', 'altitude (ft)', 'flight_level']:
                k = fields.get(possible_key)
                if k and row_clean.get(k):
                    try:
                        val = int(row_clean[k])
                        if val < 500: # Could be in flight level already
                            alt_val = val * 100
                        else:
                            alt_val = val
                    except ValueError:
                        pass
                    break
            
            # Speed
            spd_val = 400
            for possible_key in ['speed', 'spd', 'speed (kt)', 'ground_speed']:
                k = fields.get(possible_key)
                if k and row_clean.get(k):
                    try:
                        spd_val = int(row_clean[k])
                    except ValueError:
                        pass
                    break
                    
            # Heading
            hdg_val = 0
            for possible_key in ['heading', 'hdg', 'direction', 'track']:
                k = fields.get(possible_key)
                if k and row_clean.get(k):
                    try:
                        hdg_val = int(row_clean[k])
                    except ValueError:
                        pass
                    break
                    
            # Latitude and Longitude
            lat, lon = None, None
            
            # Case 1: "Position" column (contains "lat,lon")
            pos_key = fields.get('position')
            if pos_key and row_clean.get(pos_key):
                pos_str = row_clean[pos_key]
                if ',' in pos_str:
                    try:
                        lat_s, lon_s = pos_str.split(',')
                        lat = float(lat_s.strip())
                        lon = float(lon_s.strip())
                    except ValueError:
                        pass
            
            # Case 2: Separate "Latitude" and "Longitude" columns
            if lat is None or lon is None:
                lat_key = fields.get('latitude') or fields.get('lat')
                lon_key = fields.get('longitude') or fields.get('lon')
                if lat_key and lon_key and row_clean.get(lat_key) and row_clean.get(lon_key):
                    try:
                        lat = float(row_clean[lat_key])
                        lon = float(row_clean[lon_key])
                    except ValueError:
                        pass
                        
            if lat is None or lon is None:
                continue # Skip row if coordinate invalid
                
            dest = "VVTS" # Default destination (Tan Son Nhat)
            dest_key = fields.get('destination') or fields.get('dest') or fields.get('to')
            if dest_key and row_clean.get(dest_key):
                dest = row_clean[dest_key]
                
            flights.append({
                'callsign': callsign,
                'type': ac_type,
                'lat': lat,
                'lon': lon,
                'alt': alt_val,
                'speed': spd_val,
                'heading': hdg_val,
                'dest': dest
            })

    if not flights:
        print("No valid flights found in the CSV file.")
        return False
        
    print(f"Successfully parsed {len(flights)} flight records.")
    
    # Optional: Shift Coordinates to Vietnam (Centered on Da Nang: Lat 16.0, Lon 108.0)
    if shift_to_vietnam:
        print("Shift coordinate feature is enabled! Repositioning flights over Vietnam Airspace.")
        # Find centroid of parsed flights
        lats = [f['lat'] for f in flights]
        lons = [f['lon'] for f in flights]
        avg_lat = sum(lats) / len(lats)
        avg_lon = sum(lons) / len(lons)
        
        # Target centroid in Central Vietnam (Da Nang)
        target_lat = 16.0
        target_lon = 108.0
        
        lat_shift = target_lat - avg_lat
        lon_shift = target_lon - avg_lon
        
        for f in flights:
            f['lat'] += lat_shift
            f['lon'] += lon_shift

    # Write the Scenario (.scn) File
    print(f"Writing BlueSky Scenario file to: {output_scn}")
    with open(output_scn, mode='w', encoding='utf-8') as out_f:
        out_f.write("0:00:00.00>noise off\n")
        if shift_to_vietnam:
            out_f.write("0:00:00.00>pan 16.0 108.0\n")
            out_f.write("0:00:00.00>zoom 5\n")
        else:
            # Pan to first flight location
            out_f.write(f"0:00:00.00>pan {flights[0]['lat']:.4f} {flights[0]['lon']:.4f}\n")
            out_f.write("0:00:00.00>zoom 5\n")
            
        out_f.write("0:00:00.00>call FIR/VV/ALL\n\n")
        out_f.write("# --- GENERATED FLIGHT DATA FROM FLIGHTRADAR24 CSV ---\n\n")
        
        for f in flights:
            alt_fl = f"FL{int(f['alt']/100)}" if f['alt'] >= 10000 else str(f['alt'])
            out_f.write(f"0:00:00.00>CRE {f['callsign']}, {f['type']}, {f['lat']:.5f}, {f['lon']:.5f}, {f['heading']}, {alt_fl}, {f['speed']}\n")
            out_f.write(f"0:00:00.00>DEST {f['callsign']}, {f['dest']}\n")
            
    print("Conversion completed successfully!")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert Flightradar24 CSV data to BlueSky Scenario (.scn)")
    parser.add_argument("input_csv", help="Path to input Flightradar24 CSV file")
    parser.add_argument("output_scn", help="Path to save generated .scn file")
    parser.add_argument("--vietnam", action="store_true", help="Shift flight coordinates dynamically to Vietnam airspace")
    parser.add_argument("--filter", default=None, help="Filter flights by callsign (case-insensitive)")
    
    args = parser.parse_args()
    convert_fr24_csv(args.input_csv, args.output_scn, args.vietnam, args.filter)
