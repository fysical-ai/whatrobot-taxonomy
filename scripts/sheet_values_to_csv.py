"""Convert a Google Sheets `values.get` JSON response (e.g. the review sheet's '01 Terms' tab) into a review CSV.

Usage: python scripts/sheet_values_to_csv.py response.json review.csv
The header row is kept as it is; `whatrobot-taxonomy l10n import` understands the sheet's display headers
("Key", "English", "Dansk (DA)", "DA ✓", "中文 (ZH)", "ZH ✓", ...). Licence: MIT.
"""
import csv
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
values = data.get("values") or data["valueRanges"][0]["values"]
width = len(values[0])
with open(sys.argv[2], "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    for row in values:
        w.writerow(row + [""] * (width - len(row)))
print(f"wrote {len(values) - 1} rows")
