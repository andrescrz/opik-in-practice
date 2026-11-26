"""Regenerate data/solar_farm.csv (seeded, so the output is stable).

Four arrays, 91 days. Three anomalies are planted on top of normal noise:
  1. Array C: output falls ~35% from 2025-05-14 on while irradiance is
     unchanged (a soiling or string failure, not weather).
  2. Array B: an inverter fault burst on 2025-06-03..06-06 with near-zero output.
  3. 2025-05-21: every array reports 0 kWh in full sun (a grid curtailment day).
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ARRAYS = {"A": 5200, "B": 4800, "C": 5000, "D": 4600}  # nameplate kWh per full-sun day
START = date(2025, 4, 1)
DAYS = 91

random.seed(7)
rows = []
for d in range(DAYS):
    day = START + timedelta(days=d)
    irradiance = max(1.2, random.gauss(5.4, 1.3))  # kWh/m2 for the day
    if day == date(2025, 5, 21):
        irradiance = 7.1
    for array_id, nameplate in ARRAYS.items():
        kwh = nameplate * irradiance / 6.0 * random.gauss(0.97, 0.025)
        faults = 0 if random.random() > 0.04 else 1
        if array_id == "C" and day >= date(2025, 5, 14):
            kwh *= 0.65
        if array_id == "B" and date(2025, 6, 3) <= day <= date(2025, 6, 6):
            kwh *= 0.04
            faults = random.randint(5, 9)
        if day == date(2025, 5, 21):
            kwh, faults = 0.0, 0
        rows.append([day.isoformat(), array_id, round(kwh, 1), round(irradiance, 2), faults])

out = Path(__file__).parent / "data" / "solar_farm.csv"
with out.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "array_id", "kwh", "irradiance_kwh_m2", "inverter_faults"])
    w.writerows(rows)
print(f"wrote {len(rows)} rows to {out}")
