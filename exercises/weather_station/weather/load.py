"""Read and clean the daily data of the weather station."""
import csv
import datetime as dt

import numpy as np

MISSING = -999  # the station logger writes this when a sensor fails


def read_csv(path):
    """Read the station CSV into a dict of arrays."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    data = {"date": np.array([dt.date.fromisoformat(r["date"]) for r in rows])}
    for column in ("tmax", "tmin", "precip"):
        data[column] = np.array([float(r[column]) for r in rows])
    return data


def clean(data):
    """Replace the missing-value marker with NaN."""
    data = dict(data)
    tmax = data["tmax"].copy()
    tmax[tmax == MISSING] = np.nan
    data["tmax"] = tmax
    return data
