# SP3 Orbit Interpolation & Comparison

## Overview

This project interpolates precise GNSS satellite orbits from SP3 files and compares them with broadcast orbits computed from RINEX navigation data. The workflow focuses on GPS satellite G05 for day 2021‑09‑15 and is built as a modular, reproducible Python pipeline. It reads real SP3 and RINEX files, generates a common time grid, interpolates the precise orbit, propagates the broadcast orbit, and produces both tabular and visual outputs for scientific analysis.

Because the first assignment in this course used our **own real data set** (RINEX observation `tehn2580.21o` and navigation `brdc2580.21n`), this project also uses the **matching precise SP3 file for the same day and satellites** (`GBM0MGXRAP_20212580000_01D_05M_ORB.SP3`) to keep the comparison fully consistent.

---

## Project Objectives

- Read and parse a precise IGS‑style SP3 orbit file.
- Extract the 3D ECEF trajectory of a selected satellite (G05).
- Build a 30‑second time grid over the valid SP3 interval and interpolate \(X,Y,Z\) using cubic splines.
- Reuse broadcast ephemerides from `brdc2580.21n` to compute the broadcast orbit for the same satellite and time span.
- Construct a common time grid (e.g., 300 s) and compare precise vs broadcast orbits.
- Produce:
  - Science‑ready CSV files (SP3 raw, interpolated SP3, comparison data).
  - 3D plots: SP3‑only orbit and SP3 vs broadcast orbit.
- Quantify the differences (max, RMS, mean 3D error) and interpret why SP3 orbits are smoother and more accurate.

---

## Used Libraries and Packages

- **numpy**  
  Numerical computations, vectorized math, orbit equations, and array operations.

- **pandas**  
  Time‑indexed tables for SP3 data, interpolated orbits, and comparison outputs; convenient CSV I/O.

- **matplotlib**  
  3D visualization of satellite paths; plots of component differences and 3D error.

- **Python standard library**  
  - `datetime`: handling GPS/UTC times and epoch differences.  
  - `dataclasses`: defining clear containers (`OrbitData`, `BroadcastEphemeris`) for typed orbit data.

No external GNSS‑specific library is used; all parsing and orbital computations are implemented explicitly for educational transparency.

---

## Module Structure and Functionality

| Module/File              | Description                                                                                          |
|--------------------------|------------------------------------------------------------------------------------------------------|
| `main.py`                | High‑level pipeline orchestrator; parses CLI args, normalizes PRN, runs processing and plotting.    |
| `process_prn_sp3.py`     | Core logic: SP3 reading, RINEX nav reading, broadcast orbit computation, common‑grid orbit builder. |
| `read_sp3.py` (optional) | Stand‑alone SP3 reader used earlier to generate raw CSV for G05.                                     |
| `get_time_range_sp3.py`  | Reads SP3 data for G05 and extracts the first and last valid epochs.                                |
| `generate_times.py`      | Generates regular time stamps with 30‑second spacing between SP3 start and end times.               |
| `interpolate_sp3.py`     | Builds cubic splines for X, Y, Z from SP3 epochs and evaluates them on the 30‑second grid.          |
| `compare_orbits.py`      | Computes component differences, 3D error, summary statistics, and comparison plots.                 |
| `plot_sp3_only.py`       | Produces a 3D plot of the interpolated SP3 orbit (Figure 1 in the report).                          |
| `requirements.txt`       | Lists Python dependencies (numpy, pandas, matplotlib).                                              |

You can keep `read_sp3.py` separate or consider it conceptually merged into the `read_sp3_for_prn` routine inside `process_prn_sp3.py`.

---

## Project Progression (Development Roadmap)

1. **Starting from Assignment 1**

   - The initial project computed satellite orbits purely from a RINEX navigation file (`brdc2580.21n`) using broadcast ephemerides and a 30‑second time step.
   - Real observation data (`tehn2580.21o`) were already in use, so we decided to keep the same day and satellite (G05) for the precise‑orbit comparison.

2. **Adding Precise SP3 Data**

   - To match the existing data set, the precise orbit file `GBM0MGXRAP_20212580000_01D_05M_ORB.SP3` was manually downloaded.
   - A first parser was written (`read_sp3.py`) to:
     - Identify epoch lines (starting with `*`) and convert them into UTC datetimes.
     - Extract satellite position records (lines starting with `P`) for G05.
     - Save the result to `g05_sp3_raw.csv` with columns like `gps_time`, `X_m`, `Y_m`, `Z_m`.

3. **Time Range Extraction and Grid Generation**

   - `get_time_range_sp3.py` reads
