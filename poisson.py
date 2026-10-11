import math, sys
from fotmob_fetch import league_fixtures
from team_stats import build

LINES = [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5]


def pois(lam, kmax=15):
    p = [math.exp(-lam)]
    for k in range(1, kmax + 1):
        p.append(p[-1] * lam / k)
    return p


def comps(line):
    # line seperempat (.25/.75) dipecah jadi dua taruhan setengah stake
    return [line - 0.25, line + 0.25] if (line * 4) % 2 == 1 else [line]


def over_under(pt, line):
    cs = comps(line)
    pw = pl = 0.0
    for x in cs:
        pw += sum(p for k, p in enumerate(pt) if k > x)
        pl += sum(p for k, p in enumerate(pt) if k < x)
    return pw / len(cs), pl / len(cs)  # (menang over, kalah over)


def lambdas(st, h, a):
    T = st["teams"]
    lh = st["lg_home"] * T[h]["att"] * T[a]["def"]
    la = st["lg_away"] * T[a]["att"] * T[h]["def"]
    return lh, la


def show(st, h, a):
    lh, la = lambdas(st, h, a)
    pt = pois(lh + la)
    print(f"{h} vs {a} | gol model {lh:.2f} - {la:.2f} | total {lh + la:.2f}")
    print("line   Over%  odds_adil | Under% odds_adil")
    for ln in LINES:
        pw, pl = over_under(pt, ln)
        pw, pl = max(pw, 1e-9), max(pl, 1e-9)
        print(f"{ln:<5} {pw*100:5.1f}  {1 + pl/pw:6.2f}    | {pl*100:5.1f}  {1 + pw/pl:6.2f}")
    print("(sisa persen = push; odds_adil = odds impas tanpa margin)")


def upcoming(name, n=12):
    st = build(name)
    rows = sorted([r for r in league_fixtures(name) if not r["finished"]],
                  key=lambda r: r["utc"] or "")[:n]
    for r in rows:
        h, a = r["home"], r["away"]
        if h in st["teams"] and a in st["teams"]:
            lh, la = lambdas(st, h, a)
            po, _ = over_under(pois(lh + la), 2.5)
            print(f"{r['utc'][:16]} {h} vs {a} | total {lh+la:.2f} | O2.5 {po*100:.0f}%")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "epl"
    if len(sys.argv) >= 4:
        show(build(name), sys.argv[2], sys.argv[3])
    else:
        upcoming(name)
