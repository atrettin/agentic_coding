"""Writes the synthetic station data for the OpenCode exercise (exercises/weather_station/data/munich_daily.csv).

Daily max/min temperature (°C) and precipitation (mm), 2023-2025, with a seasonal cycle and noise.
Planted on purpose:
- two heat waves (tmax above 30 °C for 5 and 4 days); everywhere else tmax stays below 30 °C,
- the logger's missing-value marker -999: tmax on 3 days in 2023, tmin on 2 days in July 2025, precip on 1 day in March 2024.
clean() in the project removes -999 from tmax only, so the July 2025 mean of tmin comes out near -50 °C.

Run from the repo root: .venv/bin/python demos/make_weather_data.py
"""
import csv
import datetime as dt
import math
import random

random.seed(7)
HEAT_WAVES = {dt.date(2024, 8, 10) + dt.timedelta(i) for i in range(5)} | {dt.date(2025, 7, 1) + dt.timedelta(i) for i in range(4)}
MISSING = {("tmax", dt.date(2023, 2, 14)), ("tmax", dt.date(2023, 2, 15)), ("tmax", dt.date(2023, 11, 3)),
           ("tmin", dt.date(2025, 7, 18)), ("tmin", dt.date(2025, 7, 19)), ("precip", dt.date(2024, 3, 5))}

rows = []
day = dt.date(2023, 1, 1)
while day.year < 2026:
    mean = 9 + 10 * math.sin(2 * math.pi * (day.timetuple().tm_yday - 110) / 365)
    tmax = mean + 5 + random.gauss(0, 2.5)
    tmax = 31 + random.random() * 3 if day in HEAT_WAVES else min(tmax, 29.5)
    tmin = min(mean - 4 + random.gauss(0, 2.5), tmax - 3) if day not in HEAT_WAVES else 18 + random.random() * 3
    precip = random.expovariate(1 / 6) if random.random() < 0.4 else 0.0
    values = {"tmax": round(tmax, 1), "tmin": round(tmin, 1), "precip": round(precip, 1)}
    for col in values:
        if (col, day) in MISSING:
            values[col] = -999
    rows.append({"date": day.isoformat(), **values})
    day += dt.timedelta(1)

with open("exercises/weather_station/data/munich_daily.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["date", "tmax", "tmin", "precip"])
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows")
