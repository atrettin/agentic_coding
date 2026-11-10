"""Monthly overview of the station data: prints a table and writes plots/temperature.png and plots/precip.png."""
from pathlib import Path

from weather.load import clean, read_csv
from weather.plot import plot_monthly
from weather.stats import monthly_means, monthly_totals

data = clean(read_csv("data/munich_daily.csv"))
tmax, tmin, precip = monthly_means(data, "tmax"), monthly_means(data, "tmin"), monthly_totals(data)

print("month     tmax   tmin  precip")
for (y, m) in tmax:
    print(f"{y}-{m:02d}  {tmax[y, m]:5.1f}  {tmin[y, m]:5.1f}  {precip[y, m]:6.1f}")

Path("plots").mkdir(exist_ok=True)
plot_monthly({"mean daily max": tmax, "mean daily min": tmin}, "temperature (°C)", "plots/temperature.png")
plot_monthly({"total": precip}, "precipitation (mm)", "plots/precip.png")
