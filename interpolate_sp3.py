"""
interpolate_sp3.py - CubicSpline interpolation of SP3 positions at 30s intervals
Uses scipy.interpolate.CubicSpline for X,Y,Z interpolation

Author: F. Ahmadzade
"""

import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline
from get_time_range_sp3 import get_time_range

def interpolate_sp3_positions(sp3_csv: str, target_times_csv: str) -> pd.DataFrame:
    """
    Interpolate SP3 X,Y,Z positions using CubicSpline at target times
    
    Args:
        sp3_csv: Raw SP3 data (gps_time, X_km, Y_km, Z_km)
        target_times_csv: 30s target times
    
    Returns:
        DataFrame: gps_time, X_m, Y_m, Z_m (converted to meters)
    """
    # Load data
    sp3_df = pd.read_csv(sp3_csv, parse_dates=['gps_time'])
    target_df = pd.read_csv(target_times_csv, parse_dates=['gps_time'])
    
    # Convert SP3 times to numeric (seconds since epoch)
    sp3_times = (sp3_df['gps_time'] - sp3_df['gps_time'].min()).dt.total_seconds().values
    target_times = (target_df['gps_time'] - sp3_df['gps_time'].min()).dt.total_seconds().values
    
    # SP3 positions (km -> m)
    X_sp3 = sp3_df['X_km'].values * 1000
    Y_sp3 = sp3_df['Y_km'].values * 1000
    Z_sp3 = sp3_df['Z_km'].values * 1000
    
    # Create CubicSpline interpolators
    spline_X = CubicSpline(sp3_times, X_sp3)
    spline_Y = CubicSpline(sp3_times, Y_sp3)
    spline_Z = CubicSpline(sp3_times, Z_sp3)
    
    # Interpolate at target times
    X_interp = spline_X(target_times)
    Y_interp = spline_Y(target_times)
    Z_interp = spline_Z(target_times)
    
    # Create result DataFrame
    result_df = pd.DataFrame({
        'gps_time': target_df['gps_time'],
        'X_m': X_interp,
        'Y_m': Y_interp,
        'Z_m': Z_interp
    })
    
    return result_df

# Test function
if __name__ == "__main__":
    print("Interpolating SP3 positions...")
    
    # Input files
    sp3_file = 'g05_sp3_raw.csv'
    times_file = 'g05_target_times_30s.csv'
    
    # Interpolate
    interp_df = interpolate_sp3_positions(sp3_file, times_file)
    
    print(f"Interpolated {len(interp_df)} positions")
    print(interp_df.head())
    
    # Save interpolated positions
    interp_df.to_csv('g05_sp3_interp_30s.csv', index=False)
    print("Saved: g05_sp3_interp_30s.csv")
    
    # Verify units (should be meters)
    print(f"X range: {interp_df['X_m'].min():.0f} to {interp_df['X_m'].max():.0f} m")
    print(f"Y range: {interp_df['Y_m'].min():.0f} to {interp_df['Y_m'].max():.0f} m")
    print(f"Z range: {interp_df['Z_m'].min():.0f} to {interp_df['Z_m'].max():.0f} m")