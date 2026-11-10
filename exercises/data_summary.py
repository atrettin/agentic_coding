"""Short summary of a station CSV, for a custom OpenCode tool: python3 data_summary.py data/munich_daily.csv

Prints the number of rows, the date range, and for each column the missing values (-999) and the range of the rest.
Only the standard library, so that it runs with any python3.
"""
import csv
import sys

MISSING = "-999"

with open(sys.argv[1], newline="") as f:
    rows = list(csv.DictReader(f))
print(f"{len(rows)} rows, {rows[0]['date']} to {rows[-1]['date']}")
for column in list(rows[0])[1:]:
    missing = [r["date"] for r in rows if r[column].strip() in (MISSING, MISSING + ".0", "")]
    values = [float(r[column]) for r in rows if r["date"] not in missing]
    print(f"{column}: min {min(values)}, max {max(values)}, {len(missing)} missing" + (f" ({', '.join(missing)})" if missing else ""))
