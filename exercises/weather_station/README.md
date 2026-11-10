# Weather station

Monthly statistics of the daily data from our weather station in Munich (2023–2025).

- `data/munich_daily.csv`: one row per day: `date`, `tmax` and `tmin` (°C), `precip` (mm).
- `weather/`: reading and cleaning the data, monthly statistics, plots.
- `run.py`: prints a table of monthly values and writes the plots to `plots/`.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py
.venv/bin/pytest -q
```
