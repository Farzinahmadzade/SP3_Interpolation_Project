"""
read_sp3.py - SP3 File Reader for Precise Orbit Data
Reads CODx SP3 files and extracts satellite positions (X,Y,Z) in ECEF

Author: F. Ahmadzade
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional
import re

def parse_sp3_time(time_str: str) -> np.datetime64:
    """
    Parse SP3 GPS time format: YYYY MM DD hh mm ss.sss
    Returns numpy datetime64
    """
    # Example: 2024  1 10  0  0  0.00000000
    parts = re.findall(r'(\d+)', time_str.strip())
    if len(parts) >= 6:
        year, month, day, hour, minute, second = map(int, parts[:6])
        return np.datetime64(f'{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}')
    raise ValueError(f"Cannot parse SP3 time: {time_str}")

def read_sp3(sp3_file_path: str) -> pd.DataFrame:
    """
    Read SP3 file and return structured DataFrame
    
    Columns: ['gps_time', 'prn', 'X_km', 'Y_km', 'Z_km', 'clock_offset']
    
    SP3 Format Example:
    *  2024  1 10  0  0  0.00000000
     PG01  12782.345678  15432.987654  13245.678901 -0.0000001234
    """
    data = []
    
    with open(sp3_file_path, 'r') as f:
        lines = f.readlines()
    
    epoch_times = []
    satellites = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for epoch header (* line)
        if line.startswith('*'):
            gps_time = parse_sp3_time(line)
            epoch_times.append(gps_time)
            
            # Next lines are satellite positions (PGxx, PExx, etc.)
            i += 1
            num_sats = int(line.split()[-1])  # Number of satellites in epoch
            
            for j in range(num_sats):
                if i < len(lines):
                    sat_line = lines[i].strip()
                    if len(sat_line) >= 20:
                        prn = sat_line[1:4]  # PG01, PE02, etc.
                        X = float(sat_line[4:18])
                        Y = float(sat_line[18:32])
                        Z = float(sat_line[32:46])
                        clock = float(sat_line[46:60])
                        
                        satellites.append({
                            'gps_time': gps_time,
                            'prn': prn,
                            'X_km': X,
                            'Y_km': Y,
                            'Z_km': Z,
                            'clock_offset': clock
                        })
                    i += 1
                else:
                    break
        else:
            i += 1
    
    df = pd.DataFrame(satellites)
    return df.sort_values(['prn', 'gps_time']).reset_index(drop=True)

def get_prn_data(sp3_df: pd.DataFrame, prn: str) -> pd.DataFrame:
    """
    Extract data for specific PRN (e.g., 'G05')
    Returns: DataFrame with gps_time, X_km, Y_km, Z_km
    """
    prn_data = sp3_df[sp3_df['prn'] == prn].copy()
    if prn_data.empty:
        raise ValueError(f"No data found for PRN: {prn}")
    return prn_data[['gps_time', 'X_km', 'Y_km', 'Z_km']]

# Test function
def test_read_sp3(sp3_file: str, prn: str = 'G05'):
    """Test SP3 reading and save sample"""
    print("Reading SP3 file...")
    df = read_sp3(sp3_file)
    print(f"Total epochs: {len(df)}")
    print(f"Unique PRNs: {sorted(df['prn'].unique())}")
    
    prn_df = get_prn_data(df, prn)
    print(f"{prn} epochs: {len(prn_df)}")
    print(prn_df.head())
    
    # Save raw data
    prn_df.to_csv(f'{prn.lower()}_sp3_raw.csv', index=False)
    print(f"Saved: {prn.lower()}_sp3_raw.csv")
    return df, prn_df

if __name__ == "__main__":
    sp3_file_path = r"K:\GitHub\sp3_interpolation_project\Data\COD0MGXFIN_2024001000001D_05M_ORB.SP3"
    df, g05_data = test_read_sp3(sp3_file_path, prn="G05")
    pass