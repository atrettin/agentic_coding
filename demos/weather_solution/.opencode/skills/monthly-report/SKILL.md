---
name: monthly-report
description: Writes the standard one-page report for one month of station data to reports/YYYY-MM.md. Use when the user asks for a report, summary or overview of a month.
---
1. Load the data with `clean(read_csv("data/munich_daily.csv"))` from `weather.load`. Don't read the CSV yourself.
2. Compute everything with the functions in `weather.stats`, in one short Python snippet run with `.venv/bin/python`. If a function you need is missing, say so instead of writing a new one.
3. Write `reports/YYYY-MM.md` in exactly this format, temperatures with one decimal:

   ```markdown
   # Station report YYYY-MM

   | Quantity | Value |
   | --- | --- |
   | Mean daily maximum | 24.8 °C |
   | Mean daily minimum | 16.1 °C |
   | Anomaly of the mean maximum (baseline 2023–2024) | +1.2 °C |
   | Total precipitation | 80.1 mm |
   | Missing days (tmax / tmin / precip) | 0 / 2 / 0 |
   | Heat waves | 2025-07-01 to 2025-07-04 |
   ```

   Write "none" if there is no heat wave in the month.
4. Answer with the path of the report and one sentence on what stands out.
