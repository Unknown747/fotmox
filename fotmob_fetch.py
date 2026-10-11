import json, re, sys, time, urllib.request
from pathlib import Path

from leagues import LEAGUES
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36"
CACHE = Path("cache")
PAT = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def get_page(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def next_data(url, key, max_age=1800):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{key}.json"
    if f.exists() and time.time() - f.stat().st_mtime < max_age:
        return json.loads(f.read_text())
    m = PAT.search(get_page(url))
    if not m:
        raise RuntimeError("__NEXT_DATA__ tidak ketemu: " + url)
    data = json.loads(m.group(1))
    f.write_text(json.dumps(data))
    time.sleep(1.5)
    return data


def find_matches(node, out=None):
    out = [] if out is None else out
    if isinstance(node, dict):
        if {"home", "away", "status"} <= node.keys() and "id" in node:
            out.append(node)
        for v in node.values():
            find_matches(v, out)
    elif isinstance(node, list):
        for v in node:
            find_matches(v, out)
    return out


def norm(m):
    st = m.get("status") or {}
    h, a = m.get("home") or {}, m.get("away") or {}
    return {
        "id": m["id"],
        "home": h.get("name"), "home_id": h.get("id"),
        "away": a.get("name"), "away_id": a.get("id"),
        "utc": st.get("utcTime"),
        "finished": st.get("finished"),
        "score": st.get("scoreStr"),
    }


def league_fixtures(name):
    lid, slug = LEAGUES[name]
    url = f"https://www.fotmob.com/leagues/{lid}/fixtures/{slug}"
    data = next_data(url, f"liga_{name}")
    seen, rows = set(), []
    for m in find_matches(data):
        if m["id"] not in seen:
            seen.add(m["id"])
            rows.append(norm(m))
    return rows


def tree(node, depth=0, maxd=5, name="root"):
    pad = "  " * depth
    if isinstance(node, dict) and depth < maxd:
        print(f"{pad}{name} {{{len(node)}}}")
        for k, v in node.items():
            tree(v, depth + 1, maxd, k)
    elif isinstance(node, list) and depth < maxd:
        print(f"{pad}{name} [{len(node)}]")
        if node:
            tree(node[0], depth + 1, maxd, "[0]")
    else:
        print(f"{pad}{name}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fixtures"
    name = sys.argv[2] if len(sys.argv) > 2 else "epl"
    if cmd == "probe":
        lid, slug = LEAGUES[name]
        tree(next_data(f"https://www.fotmob.com/leagues/{lid}/fixtures/{slug}", f"liga_{name}"))
    else:
        rows = league_fixtures(name)
        up = sorted([r for r in rows if not r["finished"]], key=lambda r: r["utc"] or "")
        print(f"{name}: {len(rows)} laga total, {len(up)} belum selesai")
        for r in up[:10]:
            print(r["utc"], r["home"], "vs", r["away"])
