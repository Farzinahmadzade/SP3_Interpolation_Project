"""
generate_times.py - Generate 30-second time series between start/end
Compatible with Project 1 structure

Author: F. Ahmadzade
"""

import pandas as pd
import numpy as np
from typing import List

def generate_times(start_time: pd.Timestamp, 
                  end_time: pd.Timestamp, 
                  step: int = 30) -> List[pd.Timestamp]:
    """
    Generate timestamp list with fixed step interval
    
    Args:
        start_time: Start GPS time
        end_time: End GPS time  
        step: Seconds between timestamps (default: 30s)
    
    Returns:
        List of pd.Timestamp with regular intervals
    """
    # Convert to unix timestamps for arithmetic
    start_ns = int(start_time.value / 1e9)  # nanoseconds to seconds
    end_ns = int(end_time.value / 1e9)
    
    # Generate times with step
    times = np.arange(start_ns, end_ns + step, step)
    
    # Convert back to pd.Timestamp
    timestamps = [pd.Timestamp.fromtimestamp(t) for t in times]
    
    return timestamps

# Test function
if __name__ == "__main__":
    from get_time_range_sp3 import get_time_range
    
    # Load SP3 data
    df = pd.read_csv('g05_sp3_raw.csv', parse_dates=['gps_time'])
    
    # Get time range
    start, end = get_time_range(df, 'G05')
    print(f"Time range: {start} to {end}")
    
    # Generate 30s times
    target_times = generate_times(start, end, step=30)
    print(f"Generated {len(target_times)} timestamps")
    print(f"First 5: {target_times[:5]}")
    print(f"Last 5: {target_times[-5:]}")
    
    # Save times
    times_df = pd.DataFrame({'gps_time': target_times})
    times_df.to_csv('g05_target_times_30s.csv', index=False)
    print("Saved: g05_target_times_30s.csv")
