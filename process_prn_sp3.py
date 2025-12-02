"""
process_prn_sp3.py

Pipeline for:
1) Reading SP3 precise orbit file.
2) Reading broadcast navigation (RINEX nav) file.
3) Generating satellite ECEF coordinates from both sources
   on a common time grid for a given PRN.
"""

import datetime as dt
from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd


def _rinex_float(s: str) -> float:
    """
    Convert RINEX navigation float with D/E exponent to Python float.
    Example: '-0.544348731637D-04' -> -5.44348731637e-05
    """
    return float(s.replace("D", "E").replace("d", "e"))


# ---------------- Data containers ---------------- #

@dataclass
class OrbitData:
    """
    Container for orbit series of a single satellite on a common time grid.
    time: pandas.DatetimeIndex (UTC)
    r_sp3: np.ndarray, shape (N, 3)   (X,Y,Z) from SP3 [m]
    r_nav: np.ndarray, shape (N, 3)   (X,Y,Z) from broadcast ephemeris [m]
    prn:   PRN string, e.g. "G05"
    """
    time: pd.DatetimeIndex
    r_sp3: np.ndarray
    r_nav: np.ndarray
    prn: str


def parse_sp3_time(date_str: str, time_str: str) -> dt.datetime:
    """
    Parse SP3 epoch header line fields to Python datetime (UTC).
    Assumes format: *  yyyy mm dd hh mm ss.sss...
    """
    year = int(date_str[0:4])
    month = int(date_str[5:7])
    day = int(date_str[8:10])
    hour = int(time_str[0:2])
    minute = int(time_str[3:5])
    sec = float(time_str[6:])
    sec_int = int(sec)
    micro = int((sec - sec_int) * 1e6)
    return dt.datetime(year, month, day, hour, minute, sec_int, micro, tzinfo=dt.timezone.utc)


def read_sp3_for_prn(sp3_path: str, prn: str) -> pd.DataFrame:
    """
    Read SP3 file and extract ECEF coordinates for the given PRN.

    Args:
        sp3_path: path to SP3 file.
        prn: satellite identifier exactly as in SP3 (e.g. "G05").

    Returns:
        DataFrame indexed by datetime (UTC) with columns ['X', 'Y', 'Z'] in meters.

    Notes:
        - Assumes IGS-style SP3-C/SP3-D (km units for positions).
        - Converts km -> m.
    """
    records: List[dict] = []
    current_epoch = None

    with open(sp3_path, "r") as f:
        for line in f:
            if not line.strip():
                continue

            # Epoch line
            if line.startswith("*"):
                # Example epoch: *  2021 09 15 00 00 00.00000000
                # year(3:7), month(8:10), day(11:13), hour(14:16), min(17:19), sec(20:31)
                year = int(line[3:7])
                month = int(line[8:10])
                day = int(line[11:13])
                hour = int(line[14:16])
                minute = int(line[17:19])
                sec = float(line[20:31])
                sec_int = int(sec)
                micro = int((sec - sec_int) * 1e6)
                current_epoch = dt.datetime(
                    year, month, day, hour, minute, sec_int, micro,
                    tzinfo=dt.timezone.utc
                )
                continue

            # Satellite record line (position or velocity)
            if (line[0] in ("P", "V")) and current_epoch is not None:
                # In SP3-C/D, columns 2-4 are satellite ID, e.g. "G05"
                sat_prn = line[1:4].strip()
                if sat_prn != prn:
                    continue

                # X,Y,Z in 14.6 (km); clock not needed here
                x_km = float(line[4:18])
                y_km = float(line[18:32])
                z_km = float(line[32:46])

                records.append(
                    {
                        "time": current_epoch,
                        "X": x_km * 1000.0,
                        "Y": y_km * 1000.0,
                        "Z": z_km * 1000.0,
                    }
                )

    if not records:
        raise ValueError(f"No SP3 data found for PRN {prn} in {sp3_path}")

    df = pd.DataFrame.from_records(records)
    df.set_index("time", inplace=True)
    df.sort_index(inplace=True)
    return df


# ---------------- Broadcast ephemeris part (simplified, GPS-like) ---------------- #

# Physical constants (WGS‑84 / GPS)
MU_EARTH = 3.986005e14         # [m^3/s^2]
OMEGA_E_DOT = 7.2921151467e-5  # [rad/s]


@dataclass
class BroadcastEphemeris:
    """
    Minimal GPS broadcast ephemeris for one epoch of one PRN.
    """
    toc: dt.datetime
    sqrt_a: float
    e: float
    i0: float
    omega0: float
    w: float
    m0: float
    delta_n: float
    idot: float
    omega_dot: float
    cuc: float
    cus: float
    crc: float
    crs: float
    cic: float
    cis: float
    toe: float  # seconds of GPS week
    af0: float
    af1: float
    af2: float


def read_rinex_nav_for_prn(nav_path: str, prn: str) -> List[BroadcastEphemeris]:
    """
    Parse RINEX navigation file (GPS-like) and return list of ephemerides for the PRN.

    Supports:
        - RINEX 2.x: PRN in columns 1-2 (e.g. "05").
        - RINEX 3.x: "Gxx" etc. (handled via numeric part).

    Args:
        nav_path: path to RINEX navigation file.
        prn: normalized PRN, e.g. "G05".

    Returns:
        List of BroadcastEphemeris objects sorted by toc.
    """
    eph_list: List[BroadcastEphemeris] = []

    # Normalize to numeric part "05"
    prn_clean = prn.upper()
    if prn_clean.startswith("G"):
        prn_num = prn_clean[1:]
    else:
        prn_num = prn_clean
    prn_num2 = prn_num.zfill(2)

    with open(nav_path, "r") as f:
        # Skip header
        for line in f:
            if "END OF HEADER" in line:
                break
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        # RINEX 2: PRN in columns 1-2; RINEX 3: "Gxx" etc.
        sat_id_raw = line[0:3].strip()
        # Extract numeric part for comparison
        if sat_id_raw.upper().startswith("G"):
            sat_num = sat_id_raw[1:]
        else:
            sat_num = sat_id_raw
        sat_num2 = sat_num.zfill(2)

        if sat_num2 == prn_num2:
            # Toc etc.
            year = int(line[3:5])
            year += 2000 if year < 80 else 1900
            month = int(line[6:8])
            day = int(line[9:11])
            hour = int(line[12:14])
            minute = int(line[15:17])
            sec = float(line[18:22])
            toc = dt.datetime(year, month, day, hour, minute, int(sec),
                              tzinfo=dt.timezone.utc)

            # First line after time: af0, af1, af2
            af0 = _rinex_float(line[22:41])
            af1 = _rinex_float(line[41:60])
            af2 = _rinex_float(line[60:79])

            # Lines 2-8
            l2 = lines[i + 1]
            l3 = lines[i + 2]
            l4 = lines[i + 3]
            l5 = lines[i + 4]
            l6 = lines[i + 5]
            l7 = lines[i + 6]
            l8 = lines[i + 7]

            # Parse parameters
            iode = _rinex_float(l2[3:22])  # not used here
            crs = _rinex_float(l2[22:41])
            delta_n = _rinex_float(l2[41:60])
            m0 = _rinex_float(l2[60:79])

            cuc = _rinex_float(l3[3:22])
            e = _rinex_float(l3[22:41])
            cus = _rinex_float(l3[41:60])
            sqrt_a = _rinex_float(l3[60:79])

            toe = _rinex_float(l4[3:22])
            cic = _rinex_float(l4[22:41])
            omega0 = _rinex_float(l4[41:60])
            cis = _rinex_float(l4[60:79])

            i0 = _rinex_float(l5[3:22])
            crc = _rinex_float(l5[22:41])
            w = _rinex_float(l5[41:60])
            omega_dot = _rinex_float(l5[60:79])

            idot = _rinex_float(l6[3:22])
            # rest of l6 + l7 + l8 ignored

            eph = BroadcastEphemeris(
                toc=toc,
                sqrt_a=sqrt_a,
                e=e,
                i0=i0,
                omega0=omega0,
                w=w,
                m0=m0,
                delta_n=delta_n,
                idot=idot,
                omega_dot=omega_dot,
                cuc=cuc,
                cus=cus,
                crc=crc,
                crs=crs,
                cic=cic,
                cis=cis,
                toe=toe,
                af0=af0,
                af1=af1,
                af2=af2,
            )
            eph_list.append(eph)
            i += 8
        else:
            i += 1

    eph_list.sort(key=lambda e: e.toc)
    if not eph_list:
        raise ValueError(f"No navigation ephemeris found for PRN {prn} in {nav_path}")

    return eph_list


def _select_eph_for_time(eph_list: List[BroadcastEphemeris],
                         t: dt.datetime) -> BroadcastEphemeris:
    """
    Pick the broadcast ephemeris whose toc is last before time t.
    """
    candidates = [e for e in eph_list if e.toc <= t]
    if not candidates:
        return eph_list[0]
    return candidates[-1]


def compute_ecef_from_nav(eph: BroadcastEphemeris, t: dt.datetime) -> np.ndarray:
    """
    Compute satellite ECEF coordinates from minimal broadcast ephemeris at time t.

    Returns:
        np.array([X, Y, Z]) in meters.
    """
    # Time from ephemeris reference epoch (approx using toc).
    tk = (t - eph.toc).total_seconds()

    # Semi-major axis
    a = eph.sqrt_a ** 2
    n0 = np.sqrt(MU_EARTH / a ** 3)
    n = n0 + eph.delta_n

    # Mean anomaly
    M = eph.m0 + n * tk

    # Solve Kepler for eccentric anomaly E (simple iteration)
    E = M
    for _ in range(10):
        E = M + eph.e * np.sin(E)

    # True anomaly
    v = np.arctan2(np.sqrt(1 - eph.e ** 2) * np.sin(E),
                   np.cos(E) - eph.e)

    # Argument of latitude
    phi = v + eph.w

    # Second-order harmonic corrections
    du = eph.cus * np.sin(2 * phi) + eph.cuc * np.cos(2 * phi)
    dr = eph.crs * np.sin(2 * phi) + eph.crc * np.cos(2 * phi)
    di = eph.cis * np.sin(2 * phi) + eph.cic * np.cos(2 * phi)

    u = phi + du
    r = a * (1 - eph.e * np.cos(E)) + dr
    i = eph.i0 + di + eph.idot * tk

    # Corrected longitude of ascending node
    omega = eph.omega0 + (eph.omega_dot - OMEGA_E_DOT) * tk - OMEGA_E_DOT * eph.toe

    # Position in orbital plane
    x_orb = r * np.cos(u)
    y_orb = r * np.sin(u)

    # ECEF coordinates
    cos_o = np.cos(omega)
    sin_o = np.sin(omega)
    cos_i = np.cos(i)
    sin_i = np.sin(i)

    X = x_orb * cos_o - y_orb * cos_i * sin_o
    Y = x_orb * sin_o + y_orb * cos_i * cos_o
    Z = y_orb * sin_i

    return np.array([X, Y, Z])


def build_common_orbit(
    sp3_df: pd.DataFrame,
    eph_list: List[BroadcastEphemeris],
    prn: str,
    step_seconds: int = 300,
) -> OrbitData:
    """
    Build OrbitData on a regular time grid covering the SP3 interval.
    """
    t_start = sp3_df.index[0]
    t_end = sp3_df.index[-1]
    time_index = pd.date_range(
        t_start, t_end, freq=f"{step_seconds}s", tz=dt.timezone.utc
    )

    r_sp3 = np.zeros((len(time_index), 3))
    r_nav = np.zeros((len(time_index), 3))

    # SP3: linear interpolation between epochs
    for k, t in enumerate(time_index):
        # SP3 interpolation
        if t in sp3_df.index:
            r_sp3[k, :] = sp3_df.loc[t, ["X", "Y", "Z"]].to_numpy()
        else:
            before = sp3_df.index[sp3_df.index <= t]
            after = sp3_df.index[sp3_df.index >= t]
            if not len(before) or not len(after):
                r_sp3[k, :] = np.nan
            else:
                t0 = before[-1]
                t1 = after[0]
                if t0 == t1:
                    r_sp3[k, :] = sp3_df.loc[t0, ["X", "Y", "Z"]].to_numpy()
                else:
                    f = (t - t0).total_seconds() / (t1 - t0).total_seconds()
                    p0 = sp3_df.loc[t0, ["X", "Y", "Z"]].to_numpy()
                    p1 = sp3_df.loc[t1, ["X", "Y", "Z"]].to_numpy()
                    r_sp3[k, :] = (1 - f) * p0 + f * p1

        # Broadcast orbit
        eph = _select_eph_for_time(eph_list, t.to_pydatetime())
        r_nav[k, :] = compute_ecef_from_nav(eph, t.to_pydatetime())

    return OrbitData(time=time_index, r_sp3=r_sp3, r_nav=r_nav, prn=prn)


def process_prn(
    sp3_path: str,
    nav_path: str,
    prn: str,
    step_seconds: int = 300,
) -> OrbitData:
    """
    High-level helper:
      1) read SP3 for PRN
      2) read nav for PRN
      3) build common OrbitData.
    """
    sp3_df = read_sp3_for_prn(sp3_path, prn)
    eph_list = read_rinex_nav_for_prn(nav_path, prn)
    orbit = build_common_orbit(sp3_df, eph_list, prn, step_seconds=step_seconds)
    return orbit