from leagues import LEAGUES, KANDIDAT
from fotmob_fetch import next_data, find_matches, norm
from team_stats import parse_score


def cek(name, lid, slug):
    url = f"https://www.fotmob.com/leagues/{lid}/fixtures/{slug}"
    data = next_data(url, f"liga_{name}")
    seen, rows = set(), []
    for m in find_matches(data):
        if m["id"] not in seen:
            seen.add(m["id"])
            rows.append(norm(m))
    done = [r for r in rows if r["finished"] and parse_score(r["score"])]
    cnt = {}
    for r in done:
        for t in (r["home"], r["away"]):
            cnt[t] = cnt.get(t, 0) + 1
    teams = {r["home"] for r in rows} | {r["away"] for r in rows}
    mn = min(cnt.values()) if cnt else 0
    gpm = sum(sum(parse_score(r["score"])) for r in done) / len(done) if done else 0
    ok = len(done) >= 30 and mn >= 4 and len(teams) >= 10
    print(f"{name:12} id={lid:<4} tim={len(teams):2} laga={len(rows):3} "
          f"selesai={len(done):3} min/tim={mn} gol/laga={gpm:.2f} {'OK' if ok else 'WARN'}")


for grup, d in (("AKTIF", LEAGUES), ("KANDIDAT", KANDIDAT)):
    print(f"--- {grup}")
    for name, (lid, slug) in d.items():
        try:
            cek(name, lid, slug)
        except Exception as e:
            print(f"{name:12} id={lid:<4} GAGAL: {str(e)[:60]}")
