#!/usr/bin/env python3
"""Print the epoch seconds of the next weekday time-slot after now.
Usage: next_slot.py 8:0 11:0 13:0   (H:M pairs, local time). Skips Sat/Sun."""
import datetime, sys

slots = []
for a in sys.argv[1:]:
    h, m = a.split(":")
    slots.append((int(h), int(m)))

now = datetime.datetime.now()
cands = []
for d in range(0, 8):
    day = now.date() + datetime.timedelta(days=d)
    if day.weekday() >= 5:  # skip Sat(5)/Sun(6)
        continue
    for h, m in slots:
        t = datetime.datetime(day.year, day.month, day.day, h, m)
        if t > now:
            cands.append(t)

print(int(min(cands).timestamp()))
