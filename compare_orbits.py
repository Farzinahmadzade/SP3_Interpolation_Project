"""
Module Name : compare_orbits.py
Description : Compute SP3 vs broadcast orbit differences, statistics, and generate comparison plots.

Author      : F.Ahmadzade
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from process_prn_sp3 import OrbitData


@dataclass
class OrbitComparison:

    time: pd.DatetimeIndex
    dX: np.ndarray
    dY: np.ndarray
    dZ: np.ndarray
    d3d: np.ndarray
    stats: Dict[str, float]


def compute_orbit_differences(orbit: OrbitData) -> OrbitComparison:

    d = orbit.r_sp3 - orbit.r_nav
    dX = d[:, 0]
    dY = d[:, 1]
    dZ = d[:, 2]
    d3d = np.linalg.norm(d, axis=1)

    valid = np.isfinite(d3d)
    d3d_valid = d3d[valid]

    stats = {
        "max_3d": float(np.nanmax(d3d_valid)),
        "rms_3d": float(np.sqrt(np.nanmean(d3d_valid ** 2))),
        "mean_3d": float(np.nanmean(d3d_valid)),
    }

    return OrbitComparison(
        time=orbit.time,
        dX=dX,
        dY=dY,
        dZ=dZ,
        d3d=d3d,
        stats=stats,
    )


def save_comparison_csv(orbit: OrbitData, comp: OrbitComparison, out_path: str) -> None:

    df = pd.DataFrame(
        {
            "time": orbit.time,
            "X_sp3": orbit.r_sp3[:, 0],
            "Y_sp3": orbit.r_sp3[:, 1],
            "Z_sp3": orbit.r_sp3[:, 2],
            "X_nav": orbit.r_nav[:, 0],
            "Y_nav": orbit.r_nav[:, 1],
            "Z_nav": orbit.r_nav[:, 2],
            "dX": comp.dX,
            "dY": comp.dY,
            "dZ": comp.dZ,
            "d3d": comp.d3d,
        }
    )
    df.to_csv(out_path, index=False)


def plot_component_differences(comp: OrbitComparison, prn: str, out_prefix: str) -> None:

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    t = comp.time

    axes[0].plot(t, comp.dX / 1e3, label="dX")
    axes[0].set_ylabel("dX [km]")
    axes[0].grid(True)

    axes[1].plot(t, comp.dY / 1e3, label="dY", color="orange")
    axes[1].set_ylabel("dY [km]")
    axes[1].grid(True)

    axes[2].plot(t, comp.dZ / 1e3, label="dZ", color="green")
    axes[2].set_ylabel("dZ [km]")
    axes[2].set_xlabel("Time [UTC]")
    axes[2].grid(True)

    fig.suptitle(f"Orbit Component Differences (SP3 - NAV) for PRN {prn}")
    fig.autofmt_xdate()
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])

    fig.savefig(f"{out_prefix}_components.png", dpi=200)
    plt.close(fig)


def plot_3d_error(comp: OrbitComparison, prn: str, out_prefix: str) -> None:

    fig, ax = plt.subplots(figsize=(10, 4))
    t = comp.time
    ax.plot(t, comp.d3d, label="3D error")
    ax.set_ylabel("||Δr|| [m]")
    ax.set_xlabel("Time [UTC]")
    ax.grid(True)
    ax.set_title(f"3D Orbit Error (SP3 - NAV) for PRN {prn}")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(f"{out_prefix}_3d_error.png", dpi=200)
    plt.close(fig)