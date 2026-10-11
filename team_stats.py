import json, sys
from pathlib import Path
from fotmob_fetch import LEAGUES, league_fixtures
from leagues import PRIOR_GPM, W_PRIOR, HOME_SHARE

K = 6  # bobot prior: setara 6 laga rata-rata liga


def parse_score(s):
    try:
        a, b = [int(x) for x in str(s).replace(" ", "").split("-")]
        return a, b
    except Exception:
        return None


def build(name, last_n=10):
    rows = []
    for r in league_fixtures(name):
        sc = parse_score(r["score"]) if r["finished"] else None
        if sc:
            rows.append((r, sc))
    rows.sort(key=lambda x: x[0]["utc"] or "")
    games = {}
    for r, (h, a) in rows:
        games.setdefault(r["home"], []).append(("H", h, a))
        games.setdefault(r["away"], []).append(("A", a, h))
    n_m = len(rows)
    lg_h = sum(s[0] for _, s in rows) / n_m
    lg_a = sum(s[1] for _, s in rows) / n_m
    lg = (lg_h + lg_a) / 2
    teams = {}
    for t, g in games.items():
        g = g[-last_n:]
        n = len(g)
        gf = sum(x[1] for x in g)
        ga = sum(x[2] for x in g)
        teams[t] = {
            "n": n,
            "n_home": sum(1 for x in g if x[0] == "H"),
            "gf": round(gf / n, 2),
            "ga": round(ga / n, 2),
            "att": round((gf + K * lg) / (n + K) / lg, 3),
            "def": round((ga + K * lg) / (n + K) / lg, 3),
        }
    gpm = lg_h + lg_a
    gpm_b = (n_m * gpm + W_PRIOR * PRIOR_GPM.get(name, gpm)) / (n_m + W_PRIOR)
    return {"liga": name, "matches": n_m, "lg_home": round(gpm_b * HOME_SHARE, 3),
            "lg_away": round(gpm_b * (1 - HOME_SHARE), 3), "teams": teams}


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "epl"
    st = build(name)
    Path("cache").mkdir(exist_ok=True)
    Path(f"cache/stats_{name}.json").write_text(json.dumps(st, indent=1))
    print(f"{name}: {st['matches']} laga selesai | rata gol kandang {st['lg_home']} tandang {st['lg_away']}")
    print("tim              n  gf   ga   att    def")
    for t, v in sorted(st["teams"].items(), key=lambda x: -x[1]["att"]):
        print(f"{t[:15]:15} {v['n']:2} {v['gf']:4} {v['ga']:4} {v['att']:5} {v['def']:5}")
