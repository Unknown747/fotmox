import csv

MIN_GAP = 0.05
COL = {1.5: "p_o15", 2.5: "p_o25", 3.5: "p_o35"}
pred = {r["id"]: r for r in csv.DictReader(open("predictions.csv"))}
odds = {}
for r in csv.DictReader(open("odds.csv")):
    if r["sebelum_kickoff"] == "1":
        odds[(r["id"], float(r["line"]))] = r  # entri terakhir menimpa

cand, laga = {}, set()
for (mid, ln), o in odds.items():
    if mid not in pred:
        continue
    laga.add(mid)
    po = float(pred[mid][COL[ln]])
    ov, un = float(o["over"]), float(o["under"])
    s = 1 / ov + 1 / un
    nv = (1 / ov) / s  # peluang Over menurut pasar, tanpa margin
    for side, pm, pk, od in (("Over", po, nv, ov), ("Under", 1 - po, 1 - nv, un)):
        ev = pm * od - 1
        gap = pm - pk
        if ev > 0 and gap >= MIN_GAP:
            row = (ev, ln, side, od, pm, pk, gap, s - 1)
            if mid not in cand or ev > cand[mid][0]:
                cand[mid] = row

print(f"{len(laga)} laga punya odds sebelum kickoff, {len(cand)} lolos saring "
      f"(EV>0, gap>=+{MIN_GAP * 100:.0f} poin)")
for mid, (ev, ln, side, od, pm, pk, gap, mg) in sorted(cand.items(), key=lambda x: -x[1][0]):
    p = pred[mid]
    warn = "  CURIGA-MODEL" if gap > 0.15 else ""
    print(f"{p['home']} vs {p['away']} | {side} {ln} @{od} | model {pm * 100:.0f}% "
          f"pasar {pk * 100:.0f}% | gap {gap * 100:+.1f} EV {ev * 100:+.1f}% "
          f"margin {mg * 100:.1f}%{warn}")
