import csv, json, os, sys, time, unicodedata, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path

from leagues import ODDS_KEYS, TIER_A

BASE = "https://api.the-odds-api.com/v4"
RESERVE = 20      # sisa kredit minimal yang dijaga
WINDOW_JAM = 36   # hanya laga yang kickoff-nya dalam N jam ke depan
CACHE = Path("cache")
ODDS = Path("odds.csv")
LOG = Path("odds_api_log.csv")
COLS = ["id", "line", "over", "under", "waktu_utc", "sebelum_kickoff"]
DROP = {"fc", "afc", "cf", "sc", "ac", "as", "ssc", "fk", "sk", "bk", "club",
        "calcio", "the", "ud", "cd", "rc", "rcd", "sv", "vfb", "vfl", "tsg", "fsv", "us", "ss"}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    for ch in ".'-&":
        s = s.replace(ch, " ")
    return " ".join(t for t in s.split() if t not in DROP)


def sim(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 0.95
    return SequenceMatcher(None, a, b).ratio()


def parse_t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def sisa(rem):
    try:
        return int(float(rem))
    except (TypeError, ValueError):
        return None


def load_key():
    key = os.environ.get("ODDS_KEY")
    if key:
        return key
    p = Path(".env")
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith("ODDS_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def api(path, **params):
    key = load_key()
    if not key:
        raise SystemExit("ODDS_KEY tidak ditemukan (isi file .env atau export ODDS_KEY)")
    q = "".join(f"&{k}={v}" for k, v in params.items())
    url = f"{BASE}{path}?apiKey={key}{q}"
    with urllib.request.urlopen(url, timeout=25) as r:
        return json.loads(r.read().decode()), r.headers.get("x-requests-remaining")


def odds_liga(sport, max_age=3 * 3600):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"oddsapi_{sport}.json"
    if f.exists() and time.time() - f.stat().st_mtime < max_age:
        return json.loads(f.read_text()), None
    data, rem = api(f"/sports/{sport}/odds/", regions="eu", markets="totals", oddsFormat="decimal")
    f.write_text(json.dumps(data))
    return data, rem


def best_25(ev):
    best = None
    for b in ev.get("bookmakers", []):
        for m in b.get("markets", []):
            if m.get("key") != "totals":
                continue
            ov = un = None
            for o in m.get("outcomes", []):
                if o.get("point") == 2.5:
                    if o.get("name") == "Over":
                        ov = o.get("price")
                    elif o.get("name") == "Under":
                        un = o.get("price")
            if ov and un:
                mg = 1 / ov + 1 / un - 1
                if best is None or mg < best[0]:
                    best = (mg, b.get("key"), ov, un)  # bandar dengan margin terendah
    return best


def main():
    dry = "dry" in sys.argv
    nums = [a for a in sys.argv[1:] if a.isdigit()]
    maks = int(nums[0]) if nums else 4
    now = datetime.now(timezone.utc)
    lim = now + timedelta(hours=WINDOW_JAM)
    target = {}
    for r in csv.DictReader(open("predictions.csv")):
        if r["total"] != "" or r["liga"] not in ODDS_KEYS:
            continue
        if now < parse_t(r["utc"]) <= lim:
            target.setdefault(r["liga"], []).append(r)
    ligas = sorted(target, key=lambda l: (l not in TIER_A, -len(target[l])))[:maks]
    print(f"liga dengan laga <= {WINDOW_JAM} jam: {len(target)} | dipanggil: {ligas} "
          f"(~{len(ligas)} kredit)")
    if dry or not ligas:
        return
    try:
        _, rem = api("/sports/")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} saat cek kredit (401 = ODDS_KEY salah atau masih placeholder)")
    print("sisa kredit:", rem)
    if sisa(rem) is not None and sisa(rem) - len(ligas) < RESERVE:
        raise SystemExit(f"kredit terlalu tipis (cadangan {RESERVE}); kurangi jumlah liga")
    new = not ODDS.exists()
    nw = nl = 0
    with ODDS.open("a", newline="") as fo, LOG.open("a", newline="") as fl:
        wo, wl = csv.writer(fo), csv.writer(fl)
        if new:
            wo.writerow(COLS)
        if LOG.stat().st_size == 0:
            wl.writerow(["id", "bandar", "margin", "over", "under", "waktu_utc"])
        for liga in ligas:
            sport = ODDS_KEYS[liga]
            try:
                data, rem = odds_liga(sport)
            except urllib.error.HTTPError as e:
                print(f"{liga}: HTTP {e.code}, berhenti (401 key salah; 422/429 kuota atau batas)")
                break
            except Exception as e:
                print(f"{liga}: gagal {str(e)[:60]}")
                continue
            wkt = datetime.fromtimestamp((CACHE / f"oddsapi_{sport}.json").stat().st_mtime, timezone.utc)
            print(f"{liga}: {'dari cache' if rem is None else 'dipanggil, sisa kredit ' + str(rem)}")
            for r in target[liga]:
                tk = parse_t(r["utc"])
                cand = []
                for ev in data:
                    if abs((parse_t(ev["commence_time"]) - tk).total_seconds()) <= 900:
                        sc = sim(r["home"], ev["home_team"]) + sim(r["away"], ev["away_team"])
                        cand.append((sc, ev))
                cand.sort(key=lambda x: -x[0])
                if not cand or cand[0][0] < 1.1 or (len(cand) > 1 and cand[0][0] - cand[1][0] < 0.05):
                    nl += 1
                    print(f"  tidak cocok: {r['home']} vs {r['away']}")
                    continue
                best = best_25(cand[0][1])
                if not best or wkt >= tk:
                    nl += 1
                    print(f"  tanpa odds 2.5: {r['home']} vs {r['away']}")
                    continue
                mg, bk, ov, un = best
                ws = wkt.strftime("%Y-%m-%dT%H:%M")
                wo.writerow([r["id"], 2.5, ov, un, ws, 1])
                wl.writerow([r["id"], bk, round(mg, 4), ov, un, ws])
                nw += 1
            if sisa(rem) is not None and sisa(rem) < RESERVE:
                print("kredit di bawah cadangan, berhenti")
                break
    print(f"selesai: {nw} laga tersimpan ke odds.csv, {nl} dilewati")


if __name__ == "__main__":
    main()
