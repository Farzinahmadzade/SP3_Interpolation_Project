"""
get_time_range_sp3.py - Extract time range for PRN from SP3 DataFrame

Author: F. Ahmadzade
"""

import pandas as pd
from typing import Tuple

def get_time_range(sp3_df: pd.DataFrame, prn: str) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Extract start and end gps_time for specified PRN from SP3 DataFrame

    Args:
        sp3_df (pd.DataFrame): DataFrame with 'gps_time' and 'prn' columns
        prn (str): PRN string e.g., 'G05'

    Returns:
        Tuple[pd.Timestamp, pd.Timestamp]: (start_time, end_time)
    """
    prn_data = sp3_df[sp3_df['prn'] == prn]
    if prn_data.empty:
        raise ValueError(f"No data found for PRN: {prn}")

    start_time = prn_data['gps_time'].min()
    end_time = prn_data['gps_time'].max()
    return start_time, end_time

# Test code
if __name__ == "__main__":
    import pandas as pd

    # بارگذاری داده نمونه g05_sp3_raw.csv
    file_path = r"K:\GitHub\sp3_interpolation_project\g05_sp3_raw.csv"
    df = pd.read_csv(file_path, parse_dates=['gps_time'])

    prn = 'G05'
    start, end = get_time_range(df, prn)
    print(f"PRN {prn} start time: {start}")
    print(f"PRN {prn} end time: {end}")