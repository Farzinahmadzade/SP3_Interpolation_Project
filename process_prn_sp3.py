"""
Module Name : process_prn_sp3.py
Description : Core processing pipeline for one PRN: read SP3 and RINEX nav, build common time grid, compute orbits.

Author      : F.Ahmadzade
"""

import datetime as dt
from dataclasses import dataclass
from typing import List
import numpy as np
import pandas as pd


def _rinex_float(s: str) -> float:

    return float(s.replace("D", "E").replace("d", "e"))


# ---------------- Data containers ---------------- #

@dataclass
class OrbitData:

    time: pd.DatetimeIndex
    r_sp3: np.ndarray
    r_nav: np.ndarray
    prn: str


def read_sp3_for_prn(sp3_path: str, prn: str) -> pd.DataFrame:

    records: List[dict] = []
    current_epoch = None

    with open(sp3_path, "r") as f:
        for line in f:
            if not line.strip():
                continue

            if line.startswith("*"):
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

            if (line[0] in ("P", "V")) and current_epoch is not None:
                sat_prn = line[1:4].strip()
                if sat_prn != prn:
                    continue

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

MU_EARTH = 3.986005e14
OMEGA_E_DOT = 7.2921151467e-5


@dataclass
class BroadcastEphemeris:

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
    toe: float
    af0: float
    af1: float
    af2: float


def read_rinex_nav_for_prn(nav_path: str, prn: str) -> List[BroadcastEphemeris]:

    eph_list: List[BroadcastEphemeris] = []

    prn_clean = prn.upper()
    if prn_clean.startswith("G"):
        prn_num = prn_clean[1:]
    else:
        prn_num = prn_clean
    prn_num2 = prn_num.zfill(2)

    with open(nav_path, "r") as f:
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

        sat_id_raw = line[0:3].strip()
        if sat_id_raw.upper().startswith("G"):
            sat_num = sat_id_raw[1:]
        else:
            sat_num = sat_id_raw
        sat_num2 = sat_num.zfill(2)

        if sat_num2 == prn_num2:
            year = int(line[3:5])
            year += 2000 if year < 80 else 1900
            month = int(line[6:8])
            day = int(line[9:11])
            hour = int(line[12:14])
            minute = int(line[15:17])
            sec = float(line[18:22])
            toc = dt.datetime(year, month, day, hour, minute, int(sec),
                              tzinfo=dt.timezone.utc)

            af0 = _rinex_float(line[22:41])
            af1 = _rinex_float(line[41:60])
            af2 = _rinex_float(line[60:79])

            l2 = lines[i + 1]
            l3 = lines[i + 2]
            l4 = lines[i + 3]
            l5 = lines[i + 4]
            l6 = lines[i + 5]
            l7 = lines[i + 6]
            l8 = lines[i + 7]

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

    candidates = [e for e in eph_list if e.toc <= t]
    if not candidates:
        return eph_list[0]
    return candidates[-1]


def compute_ecef_from_nav(eph: BroadcastEphemeris, t: dt.datetime) -> np.ndarray:

    tk = (t - eph.toc).total_seconds()

    a = eph.sqrt_a ** 2
    n0 = np.sqrt(MU_EARTH / a ** 3)
    n = n0 + eph.delta_n

    M = eph.m0 + n * tk

    E = M
    for _ in range(10):
        E = M + eph.e * np.sin(E)

    v = np.arctan2(np.sqrt(1 - eph.e ** 2) * np.sin(E),
                   np.cos(E) - eph.e)

    phi = v + eph.w

    du = eph.cus * np.sin(2 * phi) + eph.cuc * np.cos(2 * phi)
    dr = eph.crs * np.sin(2 * phi) + eph.crc * np.cos(2 * phi)
    di = eph.cis * np.sin(2 * phi) + eph.cic * np.cos(2 * phi)

    u = phi + du
    r = a * (1 - eph.e * np.cos(E)) + dr
    i = eph.i0 + di + eph.idot * tk

    omega = eph.omega0 + (eph.omega_dot - OMEGA_E_DOT) * tk - OMEGA_E_DOT * eph.toe

    x_orb = r * np.cos(u)
    y_orb = r * np.sin(u)

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

    t_start = sp3_df.index[0]
    t_end = sp3_df.index[-1]
    time_index = pd.date_range(
        t_start, t_end, freq=f"{step_seconds}s", tz=dt.timezone.utc
    )

    r_sp3 = np.zeros((len(time_index), 3))
    r_nav = np.zeros((len(time_index), 3))

    for k, t in enumerate(time_index):
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

        eph = _select_eph_for_time(eph_list, t.to_pydatetime())
        r_nav[k, :] = compute_ecef_from_nav(eph, t.to_pydatetime())

    return OrbitData(time=time_index, r_sp3=r_sp3, r_nav=r_nav, prn=prn)


def process_prn(
    sp3_path: str,
    nav_path: str,
    prn: str,
    step_seconds: int = 300,
) -> OrbitData:

    sp3_df = read_sp3_for_prn(sp3_path, prn)
    eph_list = read_rinex_nav_for_prn(nav_path, prn)
    orbit = build_common_orbit(sp3_df, eph_list, prn, step_seconds=step_seconds)
    return orbit