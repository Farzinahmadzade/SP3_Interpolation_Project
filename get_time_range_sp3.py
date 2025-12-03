"""
Module Name : get_time_range_sp3.py
Description : Read SP3 data for a given PRN and extract the first and last valid epochs for that satellite.

Author      : F.Ahmadzade
"""

import pandas as pd
from typing import Tuple

def get_time_range(sp3_csv_path: str) -> Tuple[pd.Timestamp, pd.Timestamp]:

    df = pd.read_csv(sp3_csv_path, parse_dates=['gps_time'])
    
    if df.empty:
        raise ValueError("Empty SP3 CSV file")
    
    start_time = df['gps_time'].min()
    end_time = df['gps_time'].max()
    return start_time, end_time

if __name__ == "__main__":
    file_path = r"K:\GitHub\sp3_interpolation_project\g05_sp3_raw.csv"
    
    start, end = get_time_range(file_path)
    print(f"G05 SP3 time range:")
    print(f"  Start: {start}")
    print(f"  End:   {end}")
    print(f"  Duration: {(end - start).total_seconds() / 3600:.1f} hours")
