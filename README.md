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

   - `get_time_range_sp3.py` reads the raw SP3 data for G05 and finds:
     - The first epoch where G05 appears in the SP3 file.
     - The last epoch where G05 appears.
   - This defines the exact time window over which interpolation and comparison are valid (no extrapolation beyond SP3 coverage).

   - `generate_times.py` then:
     - Builds a regular time grid from `start_time` to `end_time` with a 30‑second step.
     - Saves this grid as `g05_target_times_30s.csv` for later use by the interpolation module.

4. **Cubic Spline Interpolation of SP3**

   - `interpolate_sp3.py` takes:
     - The original SP3 epochs and positions (`g05_sp3_raw.csv`), already converted to meters.
     - The 30‑second time grid (`g05_target_times_30s.csv`).
   - For each coordinate component (X, Y, Z):
     - A global cubic spline is built over the full SP3 time series.
     - The spline is evaluated at every 30‑second epoch.
   - The interpolated precise orbit is stored in `g05_sp3_interp_30s.csv` with columns:
     - `gps_time`, `X_m`, `Y_m`, `Z_m`.
   - This file is later used both for visualization (SP3‑only 3D path) and for comparison with the broadcast orbit.

5. **Broadcast Orbit Reconstruction (Reuse from Assignment 1)**

   - From Assignment 1, the broadcast orbit of G05 was already computed using:
     - Navigation file `brdc2580.21n` (RINEX 2).
     - A custom parser that:
       - Reads ephemeris blocks for G05.
       - Handles RINEX 2 formatting quirks such as `D` exponents.
       - Extracts classical GPS orbital parameters (sqrt(A), e, i0, Ω0, ω, M0, Δn, etc.).
     - Classical GPS orbit equations to obtain ECEF coordinates at 30‑second steps.
   - In this project, that logic is re‑implemented and integrated into `process_prn_sp3.py` as:
     - `read_rinex_nav_for_prn(nav_path, prn)`
     - `compute_ecef_from_nav(eph, t)`
   - This ensures both SP3 and broadcast orbits are computed within a single, consistent pipeline.

6. **Unified Processing for SP3 + Nav**

   - `process_prn_sp3.py` ties everything together for a single PRN:
     - `read_sp3_for_prn(sp3_path, prn)`  
       Returns a time‑indexed DataFrame with SP3 positions.
     - `read_rinex_nav_for_prn(nav_path, prn)`  
       Returns a sorted list of `BroadcastEphemeris` records for the same PRN.
     - `build_common_orbit(sp3_df, eph_list, prn, step_seconds)`  
       - Creates a regular comparison grid (e.g. 300 s).
       - Linearly interpolates SP3 positions on that grid.
       - Selects the appropriate broadcast ephemeris for each epoch and computes the broadcast ECEF position.
       - Produces an `OrbitData` object with:
         - `time`, `r_sp3`, `r_nav`, `prn`.

7. **Orbit Comparison and Visualization**

   - `compare_orbits.py`:
     - Takes `OrbitData` and computes:
       - Component differences ΔX, ΔY, ΔZ.
       - 3D error norm: `err_3d = sqrt(ΔX² + ΔY² + ΔZ²)`.
     - Calculates summary statistics:
       - `max_3d` – maximum 3D error.
       - `rms_3d` – root‑mean‑square 3D error.
       - `mean_3d` – mean 3D error.
     - Saves a comparison table (e.g. `out_test/G05_step300_comparison.csv`) containing:
       - Time, SP3 coordinates, broadcast coordinates, and error columns.

   - Plotting scripts:
     - `plot_sp3_only.py`  
       - Reads `g05_sp3_interp_30s.csv`.  
       - Produces a 3D plot of the SP3 orbit only (`G05_SP3_orbit_3d.png`).
     - Plot functions inside `compare_orbits.py`  
       - Generate a 3D plot with both SP3 and broadcast orbits (`G05_SP3_vs_Nav_orbit_3d.png`).  
       - Optionally plot time series of component errors and/or 3D error vs time.

---

## Usage Instructions

1. Place the data files in the `Data/` directory:

   - `Data/GBM0MGXRAP_20212580000_01D_05M_ORB.SP3`
   - `Data/brdc2580.21n`
   - (Optionally) `Data/tehn2580.21o` from Assignment 1.

2. Install Python dependencies:
```
pip install -r requirements.txt
```

3. Run the main comparison pipeline for G05:

```
python main.py Data/GBM0MGXRAP_20212580000_01D_05M_ORB.SP3 Data/brdc2580.21n G05 --step 300 --outdir out_test
```

4. This will:

- Read SP3 and navigation data for G05.
- Build a common 300‑second grid.
- Interpolate the precise orbit and compute the broadcast orbit.
- Save `G05_step300_comparison.csv` in `out_test/`.
- Generate comparison plots in `out_test/`.
- Print 3D error statistics to the console.

5. To generate the SP3‑only 3D orbit (Figure 1):
```
python plot_sp3_only.py
```

This reads `Data/g05_sp3_interp_30s.csv` and saves `G05_SP3_orbit_3d.png`.

---

## Example Outputs and Analysis

- **CSV outputs**

- `g05_sp3_raw.csv`  
 Raw precise orbit from SP3 at 5‑minute epochs (ECEF, meters).

- `g05_sp3_interp_30s.csv`  
 SP3 orbit interpolated at 30‑second spacing.

- `out_test/G05_step300_comparison.csv`  
 Side‑by‑side SP3 and broadcast orbits every 300 s, with ΔX, ΔY, ΔZ and 3D error.

- **Figures (suggested for the report)**

- *Figure 1*: 3D orbit of G05 from interpolated SP3 (30 s).  
 - Shows a smooth, continuous ECEF trajectory without sharp kinks.

- *Figure 2*: 3D orbit of G05 from broadcast ephemerides (Assignment 1).  
 - Very similar overall shape, but small differences in position at each epoch.

- *Figure 3*: 3D orbit of G05 – SP3 vs Navigation.  
 - SP3 orbit (red) and broadcast orbit (blue) plotted together.  
 - The curves are close but not identical, illustrating meter‑level deviations.

- **Numerical differences (typical for G05, step 300 s)**

- `max_3d` ≈ 2.0 m  
- `rms_3d` ≈ 1.2 m  
- `mean_3d` ≈ 1.2 m  

These values are consistent with expectations:
- Broadcast orbits are designed for real‑time navigation with meter‑level accuracy, so a few meters of 3D difference are normal.
- SP3 precise orbits aim at centimeter‑level accuracy and are generated using global networks and advanced dynamic models, so they provide a much smoother and more accurate reference trajectory for scientific analysis.

## References & Further Reading

- SP3 orbit format and IGS precise products documentation
- RINEX, GNSS, GPS format documentation and standards
- Matplotlib: https://matplotlib.org/
- Pandas: https://pandas.pydata.org/docs/
- Numpy: https://numpy.org/
- Scipy Interpolation (CubicSpline): https://docs.scipy.org/doc/scipy/reference/interpolate.html
- «جزوه تعیین موقعیت پیشرفته»، دکتر سعید فرزانه، دانشگاه تهران
- «نقشه‌برداری به روش تعیین موقعیت ماهواره‌ای» (ترجمه‌ی فارسی کتاب Hubert J. Leick)
- منابع آنلاین مربوط به محصولات دقیق GNSS (IGS precise orbits and clocks)
- Technical documentation on GNSS precise ephemerides and orbit interpolation

## Author & Maintainer

Author: F.Ahmadzade  
Contact: farzinahmadzade@ut.ac.ir | farzinahmadzade909@gmail.com