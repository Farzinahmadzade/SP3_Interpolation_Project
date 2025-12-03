"""
Module Name : generate_times.py
Description : Generate a regular 30‑second time series between given start and end epochs and save as CSV.

Author      : F.Ahmadzade
"""

import pandas as pd
import numpy as np
from typing import List
from get_time_range_sp3 import get_time_range

def generate_times(start_time: pd.Timestamp, 
                  end_time: pd.Timestamp, 
                  step: int = 30) -> List[pd.Timestamp]:

    start_ns = int(start_time.value / 1e9)
    end_ns = int(end_time.value / 1e9)
    
    times = np.arange(start_ns, end_ns + step, step)
    
    timestamps = [pd.Timestamp.fromtimestamp(t) for t in times]
    
    return timestamps

if __name__ == "__main__":
    csv_file = 'g05_sp3_raw.csv'
    start, end = get_time_range(csv_file)
    
    print(f"Time range: {start} to {end}")
    
    target_times = generate_times(start, end, step=30)
    print(f"Generated {len(target_times)} timestamps")
    print(f"First 5: {target_times[:5]}")
    print(f"Last 5: {target_times[-5:]}")
    
    times_df = pd.DataFrame({'gps_time': target_times})
    times_df.to_csv('g05_target_times_30s.csv', index=False)
    print("Saved: g05_target_times_30s.csv")