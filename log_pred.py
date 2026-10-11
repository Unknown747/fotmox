import csv, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fotmob_fetch import LEAGUES, league_fixtures
from team_stats import build, parse_score
from poisson import pois, over_under, lambdas

F = Path("predictions.csv")
COLS = ["id", "liga", "utc", "home", "away", "lam_h", "lam_a",
        "p_o15", "p_o25", "p_o35", "total"]


def load():
    if not F.exists():
        return []
    with F.open() as f:
        return list(csv.DictReader(f))


def save(rows):
    with F.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)


def run(names, days=3):
    rows = load()
    known = {r["id"] for r in rows}
    now = datetime.now(timezone.utc)
    now_s = now.strftime("%Y-%m-%dT%H:%M")
    lim_s = (now + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M")
    added = settled = 0
    for name in names:
        st = build(name)
        fx = league_fixtures(name)
        by_id = {str(r["id"]): r for r in fx}
        for r in fx:
            u = (r["utc"] or "")[:16]
            if r["finished"] or not (now_s < u <= lim_s) or str(r["id"]) in known:
                continue
            h, a = r["home"], r["away"]
            if h not in st["teams"] or a not in st["teams"]:
                continue
            lh, la = lambdas(st, h, a)
            pt = pois(lh + la)
            rows.append({
                "id": r["id"], "liga": name, "utc": r["utc"], "home": h, "away": a,
                "lam_h": round(lh, 3), "lam_a": round(la, 3),
                "p_o15": round(over_under(pt, 1.5)[0], 4),
                "p_o25": round(over_under(pt, 2.5)[0], 4),
                "p_o35": round(over_under(pt, 3.5)[0], 4),
                "total": "",
            })
            added += 1
        for row in rows:
            if row["liga"] == name and row["total"] == "":
                m = by_id.get(str(row["id"]))
                sc = parse_score(m["score"]) if m and m["finished"] else None
                if sc:
                    row["total"] = sc[0] + sc[1]
                    settled += 1
    save(rows)
    done = sum(1 for r in rows if r["total"] != "")
    print(f"tambah {added} prediksi, settle {settled} | total {len(rows)}, sudah ada hasil {done}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "epl"
    run(list(LEAGUES) if arg == "all" else [arg])
