"""
Module Name : plot_3d_comparison.py
Description : Create 3D visualization showing precise SP3 orbit and broadcast orbit together for visual comparison.

Author      : F.Ahmadzade
"""

import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional


def plot_3d_orbits(
    sp3_csv: str,
    nav_csv: Optional[str] = None,
    prn: str = "G05",
    save_path: str = "G05_orbit_comparison_3d.png"
) -> None:

    sp3_df = pd.read_csv(sp3_csv, parse_dates=["gps_time"])

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot(
        sp3_df["X_m"],
        sp3_df["Y_m"],
        sp3_df["Z_m"],
        color="red",
        linewidth=1.0,
        label="SP3 precise orbit",
    )

    if nav_csv is not None:
        nav_df = pd.read_csv(nav_csv, parse_dates=["time"])
        ax.plot(
            nav_df["X"],
            nav_df["Y"],
            nav_df["Z"],
            color="blue",
            linewidth=0.8,
            alpha=0.7,
            label="Broadcast orbit (RINEX nav)",
        )

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_title(f"3D Orbit of {prn}: SP3 vs Navigation")

    ax.legend()
    ax.view_init(elev=20, azim=45)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"Saved 3D orbit plot to: {save_path}")


if __name__ == "__main__":
    plot_3d_orbits(
        sp3_csv=r"Data\g05_sp3_interp_30s.csv",
        nav_csv=r"Data\output_G05.csv",
        prn="G05",
        save_path="G05_SP3_vs_Nav_orbit_3d.png",
    )