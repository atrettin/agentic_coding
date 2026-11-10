# Weather station

Monthly statistics of the daily data from one weather station. Python 3, numpy, matplotlib; no pandas.

## Commands
- Tests: `.venv/bin/pytest -q`
- Monthly table and plots: `.venv/bin/python run.py`

## Data
- `data/munich_daily.csv` is the only copy of the station's measurements. Never edit it.
- `-999` means missing (the sensor failed). `weather.load.clean()` turns it into NaN; every analysis works on cleaned data.

## Conventions
- Every function gets a numpy-style docstring (`Parameters`, `Returns`), with the unit of every physical quantity, e.g. `tmax : ndarray` / `Daily maximum temperature in °C.`
- Every new function in `weather/` gets a test in `tests/`, on small hand-made data, not on the CSV.
