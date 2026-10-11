import csv

rows = [r for r in csv.DictReader(open("predictions.csv")) if r["total"] != ""]
print(f"laga dengan hasil: {len(rows)}")
if not rows:
    raise SystemExit("belum ada hasil; jalankan log_pred.py all setelah laga selesai")

LINES = {"p_o15": 1.5, "p_o25": 2.5, "p_o35": 3.5}
BINS = [0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.01]


def hit(r, ln):
    return 1 if int(r["total"]) > ln else 0


for col, ln in LINES.items():
    print(f"\nOver {ln}")
    print("bin peluang     n  rata_model  hasil_nyata")
    for lo, hi in zip(BINS, BINS[1:]):
        b = [r for r in rows if lo <= float(r[col]) < hi]
        if not b:
            continue
        pm = sum(float(r[col]) for r in b) / len(b)
        ac = sum(hit(r, ln) for r in b) / len(b)
        print(f"{lo:.1f}-{min(hi, 1):.1f}      {len(b):4} {pm*100:8.1f}% {ac*100:10.1f}%")
    brier = sum((float(r[col]) - hit(r, ln)) ** 2 for r in rows) / len(rows)
    base = sum(hit(r, ln) for r in rows) / len(rows)
    brier0 = sum((base - hit(r, ln)) ** 2 for r in rows) / len(rows)
    print(f"Brier model {brier:.3f} vs tebak rata-rata {brier0:.3f} (lebih kecil = lebih baik)")
