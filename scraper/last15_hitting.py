"""
FantasyPros MLB Hitter Stats - Last 15 Days Scraper
-----------------------------------------------------
Source: https://www.fantasypros.com/mlb/stats/hitters.php?range=15

Table structure (id="data"):
  <thead>
    <tr>
      <th>VBR</th>        [0]  ← rank/value-based ranking
      <th>Player</th>     [1]  ← player name + team + positions
      <th>AB</th>         [2]
      <th>R</th>          [3]
      <th>HR</th>         [4]
      <th>RBI</th>        [5]
      <th>SB</th>         [6]
      <th>AVG</th>        [7]
      <th>OBP</th>        [8]
      <th>H</th>          [9]
      <th>2B</th>         [10]
      <th>3B</th>         [11]
      <th>BB</th>         [12]
      <th>K</th>          [13]
      <th>SLG</th>        [14]
      <th>OPS</th>        [15]
      <th>Rost%</th>      [16]  ← label only; actual data spans 3 cells:
      (no header)         [17]     Yahoo Rost%
      (no header)         [18]     ESPN Rost%
    </tr>
  </thead>

Player cell (td[1]) structure:
  <a class="fp-player-link fp-id-XXXX" fp-player-name="..." href="/mlb/stats/...">Name</a>
  <small>(<a href="/mlb/teams/...">TEAM</a> - POS1,POS2)</small>

Rost% cells (td[16-18]):
  td[16]: class="own consensus-own"  -> Consensus Rost%
  td[17]: class="own yahoo-own"      -> Yahoo Rost%
  td[18]: class="own espn-own"       -> ESPN Rost%

GitHub Actions usage:
  python last15_hitting.py --auto

Local test (saved HTML):
  python last15_hitting.py --html MLB_Hitter_Stats___Last_15_Days___FantasyPros.html --mode test

Output: outputs/last15_days_YYYY-MM-DD.csv  (and latest symlink/copy)
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import date

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_URL = "https://www.fantasypros.com/mlb/stats/hitters.php?range=15"
TABLE_ID = "data"
OUTPUT_DIR = "."

DATA_COLS = [
    "date",
    "rank",
    "player_name",
    "team",
    "positions",
    "fp_player_id",
    "AB", "R", "HR", "RBI", "SB",
    "AVG", "OBP", "H", "2B", "3B", "BB", "K",
    "SLG", "OPS",
    "rost_pct_consensus",
    "rost_pct_yahoo",
    "rost_pct_espn",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

REQUEST_TIMEOUT = 20

# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def _build_headers() -> dict:
    import random
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.fantasypros.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def fetch_html(url: str) -> str:
    """
    Fetch the page. FantasyPros is accessible without Cloudflare anti-bot,
    so standard requests work. Falls back to curl_cffi if needed.
    """
    # Try requests first (fast, no extra deps)
    try:
        import requests
        session = requests.Session()
        resp = session.get(url, headers=_build_headers(), timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        if _page_has_table(resp.text):
            print(f"[info] Fetched via requests (status {resp.status_code}).")
            return resp.text
        print("[warn] requests: page returned 200 but table not found.")
    except Exception as e:
        print(f"[warn] requests failed: {e}")

    # Fallback: curl_cffi (Chrome TLS fingerprint)
    try:
        from curl_cffi import requests as cffi_requests
        for profile in ("chrome124", "chrome120", "edge101"):
            try:
                resp = cffi_requests.get(
                    url, headers=_build_headers(), timeout=REQUEST_TIMEOUT,
                    impersonate=profile,
                )
                if resp.status_code == 200 and _page_has_table(resp.text):
                    print(f"[info] Fetched via curl_cffi/{profile}.")
                    return resp.text
            except Exception as e:
                print(f"[warn] curl_cffi/{profile}: {e}")
    except ImportError:
        print("[hint] Install curl_cffi for better anti-bot bypass: pip install curl_cffi")

    raise RuntimeError(
        f"Failed to fetch {url} after all attempts.\n"
        "Try running with --html to parse a locally saved file."
    )


def _page_has_table(html: str) -> bool:
    return 'id="data"' in html or "id='data'" in html


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------

def _text(el) -> str:
    return el.get_text(strip=True) if el else ""


_FP_ID_RE = re.compile(r"fp-id-(\d+)")
_TEAM_POS_RE = re.compile(r"\((.+?)\s*-\s*(.+?)\)")


def parse_table(html: str, run_date: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id=TABLE_ID)
    if table is None:
        raise ValueError(f"Could not find <table id='{TABLE_ID}'> in the page.")

    tbody = table.find("tbody")
    if tbody is None:
        raise ValueError("Table has no <tbody>.")

    rows_out = []
    for tr in tbody.find_all("tr", recursive=False):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 17:
            continue  # skip malformed / ad rows

        # --- td[0]: rank ---
        rank = _text(tds[0]) or None

        # --- td[1]: player ---
        player_cell = tds[1]
        player_a = player_cell.find("a", class_="fp-player-link")
        player_name = _text(player_a) if player_a else _text(player_cell)

        fp_id = None
        if player_a:
            cls_str = " ".join(player_a.get("class", []))
            m = _FP_ID_RE.search(cls_str)
            if m:
                fp_id = m.group(1)

        small = player_cell.find("small")
        team = None
        positions = None
        if small:
            team_a = small.find("a")
            if team_a:
                team = _text(team_a)
            small_text = _text(small)            # e.g. "(PHI - LF,DH)"
            m = _TEAM_POS_RE.search(small_text)
            if m:
                positions = m.group(2).strip()

        # --- td[2-15]: stats ---
        ab  = _text(tds[2])  or None
        r   = _text(tds[3])  or None
        hr  = _text(tds[4])  or None
        rbi = _text(tds[5])  or None
        sb  = _text(tds[6])  or None
        avg = _text(tds[7])  or None
        obp = _text(tds[8])  or None
        h   = _text(tds[9])  or None
        d2b = _text(tds[10]) or None
        d3b = _text(tds[11]) or None
        bb  = _text(tds[12]) or None
        k   = _text(tds[13]) or None
        slg = _text(tds[14]) or None
        ops = _text(tds[15]) or None

        # --- td[16-18]: Rost% (consensus, yahoo, espn) ---
        rost_consensus = _text(tds[16]) if len(tds) > 16 else None
        rost_yahoo     = _text(tds[17]) if len(tds) > 17 else None
        rost_espn      = _text(tds[18]) if len(tds) > 18 else None

        rows_out.append({
            "date":               run_date,
            "rank":               rank,
            "player_name":        player_name,
            "team":               team,
            "positions":          positions,
            "fp_player_id":       fp_id,
            "AB":                 ab,
            "R":                  r,
            "HR":                 hr,
            "RBI":                rbi,
            "SB":                 sb,
            "AVG":                avg,
            "OBP":                obp,
            "H":                  h,
            "2B":                 d2b,
            "3B":                 d3b,
            "BB":                 bb,
            "K":                  k,
            "SLG":                slg,
            "OPS":                ops,
            "rost_pct_consensus": rost_consensus,
            "rost_pct_yahoo":     rost_yahoo,
            "rost_pct_espn":      rost_espn,
        })

    return rows_out


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _flat(row: dict) -> dict:
    return {c: (row.get(c) if row.get(c) is not None else "") for c in DATA_COLS}


def write_csv(rows: list, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DATA_COLS)
        writer.writeheader()
        for r in rows:
            writer.writerow(_flat(r))
    print(f"[info] Wrote {len(rows)} rows -> {path}")


def write_json(rows: list, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([_flat(r) for r in rows], f, indent=2)
    print(f"[info] Wrote {len(rows)} rows -> {path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scrape FantasyPros MLB Hitter Stats - Last 15 Days."
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--url",  default=DEFAULT_URL, help="Live URL to fetch (default: FantasyPros last-15 page).")
    src.add_argument("--html", default=None,        help="Path to a locally saved HTML file (no network call).")
    src.add_argument("--auto", action="store_true", help="Unattended mode for GitHub Actions (uses --url).")

    parser.add_argument("--mode",   choices=["test", "full"], default="full",
                        help="'test' = first 5 rows; 'full' = all rows (default).")
    parser.add_argument("--format", choices=["csv", "json"],  default="csv")
    parser.add_argument("--out",    default=None,
                        help="Output file path. Default: outputs/last15_days_YYYY-MM-DD.csv")
    parser.add_argument("--date",   default=None,
                        help="Override run date label (YYYY-MM-DD). Default: today.")
    args = parser.parse_args()

    run_date = args.date or str(date.today())

    # Resolve output path
    if args.out:
        out_path = args.out
    else:
        ext = args.format
        out_path = f"last15_days_{run_date}.{ext}"

    # Fetch HTML
    if args.html:
        print(f"[info] Reading local file: {args.html}")
        with open(args.html, encoding="utf-8", errors="ignore") as f:
            html = f.read()
    else:
        url = args.url if not args.auto else DEFAULT_URL
        print(f"[info] Fetching {url} ...")
        html = fetch_html(url)

    # Parse
    print("[info] Parsing table ...")
    rows = parse_table(html, run_date)
    print(f"[info] Parsed {len(rows)} rows.")

    if args.mode == "test":
        rows = rows[:5]
        print("[info] TEST MODE: truncated to first 5 rows.")

    # Write
    if args.format == "csv":
        write_csv(rows, out_path)
    else:
        write_json(rows, out_path)

    # Preview first 3 rows
    print("\n[preview] First 3 rows:")
    for r in rows[:3]:
        print({c: r.get(c) for c in ["rank", "player_name", "team", "AB", "HR", "AVG", "OPS"]})

    sys.exit(0)


if __name__ == "__main__":
    main()