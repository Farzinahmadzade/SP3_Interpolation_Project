"""
Module Name : main.py
Description : Command‑line entry point; orchestrates SP3 + RINEX processing, comparison, CSV export, and plotting.

Author      : F.Ahmadzade
"""

import argparse
import os
from process_prn_sp3 import process_prn
from compare_orbits import (
    compute_orbit_differences,
    save_comparison_csv,
    plot_component_differences,
    plot_3d_error,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare precise (SP3) and broadcast (RINEX nav) orbits for a given PRN."
    )
    parser.add_argument("sp3", help="Path to SP3 precise orbit file.")
    parser.add_argument("nav", help="Path to RINEX navigation file.")
    parser.add_argument("prn", help="Satellite PRN (e.g., G05 or 05).")
    parser.add_argument(
        "--step",
        type=int,
        default=300,
        help="Time step [seconds] for comparison grid (default: 300).",
    )
    parser.add_argument(
        "--outdir",
        default="orbit_comparison",
        help="Output directory for CSV and plots (default: orbit_comparison).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    raw_prn = args.prn.strip().upper()
    if raw_prn.startswith("G"):
        prn = raw_prn
    else:
        prn = f"G{raw_prn.zfill(2)}"

    print(f"Processing PRN {prn} ...")
    print("Reading SP3 and navigation files ...")

    orbit = process_prn(args.sp3, args.nav, prn, step_seconds=args.step)

    print("Computing orbit differences ...")
    comp = compute_orbit_differences(orbit)

    base_name = f"{prn}_step{args.step}"
    csv_path = os.path.join(args.outdir, f"{base_name}_comparison.csv")

    print(f"Saving CSV to {csv_path} ...")
    save_comparison_csv(orbit, comp, csv_path)

    print("Generating plots ...")
    out_prefix = os.path.join(args.outdir, base_name)
    plot_component_differences(comp, prn, out_prefix)
    plot_3d_error(comp, prn, out_prefix)

    print("Statistics:")
    for k, v in comp.stats.items():
        print(f"  {k}: {v:.4f} m")

    print("DONE.")

if __name__ == "__main__":
    main()