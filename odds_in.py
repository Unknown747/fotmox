import csv, sys
from datetime import datetime, timezone
from pathlib import Path

F = Path("odds.csv")
COLS = ["id", "line", "over", "under", "waktu_utc", "sebelum_kickoff"]
CODE = {"15": 1.5, "25": 2.5, "35": 3.5}

args = sys.argv[1:]
t = None
if args and args[-1].startswith("t="):
    t = args.pop()[2:]
if len(args) < 4 or (len(args) - 1) % 3:
    raise SystemExit("pakai: python odds_in.py ID 25 1.93 1.93 [15 o u] [35 o u] [t=2026-10-11T12:50]")
mid, rest = args[0], args[1:]
pred = {r["id"]: r for r in csv.DictReader(open("predictions.csv"))}
if mid not in pred:
    raise SystemExit("id tidak ada di predictions.csv")
now = t or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
pre = 1 if now < pred[mid]["utc"][:16] else 0
new = not F.exists()
with F.open("a", newline="") as f:
    w = csv.writer(f)
    if new:
        w.writerow(COLS)
    for i in range(0, len(rest), 3):
        code, o, u = rest[i:i + 3]
        w.writerow([mid, CODE[code], float(o), float(u), now, pre])
p = pred[mid]
print(f"{p['home']} vs {p['away']}: {len(rest) // 3} line disimpan, "
      f"sebelum kickoff = {'ya' if pre else 'TIDAK (tidak dipakai evaluasi)'}")
