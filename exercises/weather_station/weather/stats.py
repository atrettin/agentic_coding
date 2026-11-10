"""Monthly statistics of the station data."""
import numpy as np


def _months(data):
    return [(d.year, d.month) for d in data["date"]]


def monthly_means(data, column):
    """Mean of a column for each month."""
    months = _months(data)
    values = data[column]
    return {m: float(np.nanmean(values[[k == m for k in months]])) for m in sorted(set(months))}


def monthly_totals(data, column="precip"):
    """Sum of a column for each month."""
    months = _months(data)
    values = data[column]
    return {m: float(np.nansum(values[[k == m for k in months]])) for m in sorted(set(months))}


def anomaly(means, baseline_years):
    """Difference of each monthly mean from the baseline mean of the same calendar month."""
    baseline = {}
    for month in {m for _, m in means}:
        baseline[month] = np.mean([v for (y, m), v in means.items() if m == month and y in baseline_years])
    return {(y, m): v - baseline[m] for (y, m), v in means.items()}
