import datetime as dt

import numpy as np

from weather.load import clean, read_csv
from weather.stats import anomaly, monthly_means, monthly_totals


def small_data():
    dates = [dt.date(2024, 1, 30), dt.date(2024, 1, 31), dt.date(2024, 2, 1)]
    return {"date": np.array(dates), "tmax": np.array([2.0, 4.0, 10.0]),
            "tmin": np.array([-4.0, -2.0, 1.0]), "precip": np.array([1.0, 0.0, 5.5])}


def test_monthly_means():
    assert monthly_means(small_data(), "tmax") == {(2024, 1): 3.0, (2024, 2): 10.0}


def test_monthly_totals():
    assert monthly_totals(small_data()) == {(2024, 1): 1.0, (2024, 2): 5.5}


def test_clean_tmax():
    data = small_data()
    data["tmax"][0] = -999
    assert monthly_means(clean(data), "tmax") == {(2024, 1): 4.0, (2024, 2): 10.0}


def test_anomaly():
    means = {(2023, 7): 20.0, (2024, 7): 22.0, (2025, 7): 24.0}
    assert anomaly(means, baseline_years=[2023, 2024]) == {(2023, 7): -1.0, (2024, 7): 1.0, (2025, 7): 3.0}


def test_read_csv():
    data = read_csv("data/munich_daily.csv")
    assert len(data["date"]) == 1096
    assert data["date"][0] == dt.date(2023, 1, 1)
