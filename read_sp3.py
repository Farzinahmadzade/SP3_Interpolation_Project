"""
Module Name : read_sp3.py
Description : Stand‑alone utilities to parse SP3 files and extract raw ECEF positions for selected satellites.

Author      : F.Ahmadzade
"""

import pandas as pd
import numpy as np
import re

def parse_sp3_time(time_str: str) -> np.datetime64:

    parts = re.findall(r'(\d+)', time_str.strip())
    if len(parts) >= 6:
        year, month, day, hour, minute, second = map(int, parts[:6])
        return np.datetime64(f'{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}')
    raise ValueError(f"Cannot parse SP3 time: {time_str}")

def read_sp3(sp3_file_path: str) -> pd.DataFrame:

    data = []
    with open(sp3_file_path, 'r') as f:
        lines = f.readlines()

    current_epoch_time = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('*'):
            current_epoch_time = parse_sp3_time(line)
            i += 1
            while i < len(lines) and not lines[i].startswith('*'):
                sat_line = lines[i].strip()
                if len(sat_line) >= 20 and (sat_line.startswith('P') or sat_line.startswith('G') or sat_line.startswith('R') or sat_line.startswith('E')):
                    prn = sat_line[1:4]
                    try:
                        X = float(sat_line[4:18])
                        Y = float(sat_line[18:32])
                        Z = float(sat_line[32:46])
                        clock = float(sat_line[46:60])
                    except ValueError:
                        i += 1
                        continue
                    data.append({
                        'gps_time': current_epoch_time,
                        'prn': prn,
                        'X_km': X,
                        'Y_km': Y,
                        'Z_km': Z,
                        'clock_offset': clock
                    })
                i += 1
        else:
            i += 1

    df = pd.DataFrame(data)
    return df.sort_values(['prn', 'gps_time']).reset_index(drop=True)

def get_prn_data(sp3_df: pd.DataFrame, prn: str) -> pd.DataFrame:

    prn_data = sp3_df[sp3_df['prn'] == prn].copy()
    if prn_data.empty:
        raise ValueError(f"No data found for PRN: {prn}")
    return prn_data[['gps_time', 'X_km', 'Y_km', 'Z_km']]

def test_read_sp3(sp3_file: str, prn: str = 'G05'):
    print("Reading SP3 file...")
    df = read_sp3(sp3_file)
    print(f"Total epochs: {len(df)}")
    print(f"Unique PRNs: {sorted(df['prn'].unique())}")
    
    prn_df = get_prn_data(df, prn)
    print(f"{prn} epochs: {len(prn_df)}")
    print(prn_df.head())
    
    prn_df.to_csv(f'{prn.lower()}_sp3_raw.csv', index=False)
    print(f"Saved: {prn.lower()}_sp3_raw.csv")
    return df, prn_df

if __name__ == "__main__":
    sp3_file_path = r"K:\GitHub\sp3_interpolation_project\Data\COD0MGXFIN_20240010000_01D_05M_ORB.SP3"
    df, g05_data = test_read_sp3(sp3_file_path, prn="G05")