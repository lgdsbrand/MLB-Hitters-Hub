"""
MLB Batter vs Pitcher table scraper (v2 - verified against real page HTML)
---------------------------------------------------------------------------
Confirmed structure from real source:

<table id="searchable">
  <caption>Batter vs Pitcher (6/19/26)</caption>
  <tbody>
    <tr class="db dmre conf">              <!-- normal confirmed-lineup row -->
    <tr class="db dmre lnphd">              <!-- not-yet-confirmed lineup spot (e.g. IL'd player) -->
    <tr class="db dmre no_history conf">    <!-- confirmed but "no matchup history" vs that pitcher -->
    <tr class="trclt">                     <!-- in-table ad/promo row -- SKIP -->
  </tbody>
</table>

Each real data row has exactly 16 <td> cells in this fixed order:
  0  td.confirmed (or td.notlnup)  -> batter name, pos, hand; hidden div.tr_sub has L5 OPS
  1  td.tdimg.tdrec                -> recent hot/cold streak icons (green spans) + "L5" marker
  2  td.oppitcher                  -> <a> pitcher name/hand + href (date + pitcher slug);
                                        hidden div has pitcher's recent ERA trend
  3  td (no class)                 -> span.game_row (teams + weather + wind) and span.opteam (opp abbrev)
  4  td (no class)                 -> HRF -> span.fcasthrf (tooltip = weather HR boost note)
  5  td (no class)                 -> qAB%
  6  td (no class)                 -> HH%  (or "no matchup history" text when no_history)
  7  td (no class)                 -> AB  -> span.opatbats
  8  td (no class)                 -> H   -> span.ophits
  9  td.dmnrw                      -> 2B/3B
  10 td.dmnrw                      -> HR
  11 td.dmnrw                      -> BB
  12 td (no class)                 -> BA
  13 td (no class)                 -> OBP
  14 td.darkgreen (or plain td)    -> OPS
  15 td (no class)                 -> "more" link (ignored)

The hidden div.tr_sub on td[0] also carries a tooltip string like
"2, 3, 1, 2, 0 (times on base last 5 gms)" -- reused later for the
Streaks / 100% Club modules, captured here as `last5_times_on_base`.

---------------------------------------------------------------------------
HOW TEAM / WEATHER IMAGES WILL WORK IN THE FRONTEND HUB (read before editing)
---------------------------------------------------------------------------
The "Game" column's raw markup (team mini-icons via CSS classes like
<span class="team BOS">, plus a weather <img src="/images/icons/weather/...">)
is captured AS-IS in the `Game_HTML` field on each row. This field is only
emitted in --format html output -- CSV/JSON keep a clean plain-text "Game"
column (e.g. "BOS @ SEA") since markup doesn't belong in a data file.

Workflow once we build the actual hub frontend:
  1. Run download_assets.py (separate script) against this same saved HTML
     to pull every referenced icon/logo locally into an `assets/` folder.
  2. In the hub's HTML/React, instead of dropping Game_HTML verbatim, we
     swap any "/images/..." src path for "assets/images/..." (or whatever
     local path the downloader used) so the hub doesn't depend on hot-
     linking the original site -- this is a simple find/replace on the
     Game_HTML string, e.g.:
         game_html_local = row["Game_HTML"].replace(
             "/images/", "assets/images/"
         )
  3. The hub then renders that adjusted Game_HTML directly inside the
     table's "Game" <td>, alongside our own small CSS rules to reproduce
     the team-abbreviation styling (the original site uses CSS classes
     like .team.BOS as background-image sprites -- once we have the site's
     actual CSS rules for those classes, or the logo image files, we mirror
     them in the hub's stylesheet).
  4. If the source site uses *named* team logo image files (not just CSS
     sprite classes), step 1's downloader will grab those directly and step
     2's path-swap is all that's needed -- no extra CSS work.

For now this script only OUTPUTS the data + raw Game_HTML; no image
download or path-rewriting happens here. That logic lives in
download_assets.py and (later) in the hub's build step.
---------------------------------------------------------------------------

USAGE:
    python scrape_bvp.py --html bvp_page.html --mode test
    python scrape_bvp.py --url "https://www.fantasyinfocentral.com/mlb/daily-matchups" --mode full

    # Always fetch today's data (date auto-injected into URL):
    python scrape_bvp.py --url "https://www.fantasyinfocentral.com/mlb/daily-matchups" --today-only --mode full

    # Fetch a specific date and filter to only that date's rows:
    python scrape_bvp.py --url "https://..." --date 2026-06-19 --today-only --mode full
"""

import argparse
import csv
import json
import os
import random
import re
import time
from datetime import datetime, date
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from curl_cffi import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

MIN_SECONDS_BETWEEN_RUNS = 30
MAX_RETRIES = 4
BASE_BACKOFF = 2.0
REQUEST_TIMEOUT = 15
LOCKFILE = os.path.join(os.path.dirname(__file__), ".last_run_bvp")


def enforce_min_interval():
    if os.path.exists(LOCKFILE):
        with open(LOCKFILE, "r") as f:
            try:
                last = float(f.read().strip())
            except ValueError:
                last = 0
        elapsed = time.time() - last
        if elapsed < MIN_SECONDS_BETWEEN_RUNS:
            wait = MIN_SECONDS_BETWEEN_RUNS - elapsed
            print(f"[rate-limit guard] Ran {elapsed:.0f}s ago. Sleeping {wait:.0f}s.")
            time.sleep(wait)


def record_run():
    with open(LOCKFILE, "w") as f:
        f.write(str(time.time()))


def fetch(url: str) -> str:
    enforce_min_interval()
    time.sleep(random.uniform(0.5, 2.0))

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, impersonate="chrome")
            if resp.status_code == 200:
                record_run()
                return resp.text
            if resp.status_code == 429:
                wait = BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 1)
                print(f"[429] Rate limited. Backing off {wait:.1f}s "
                      f"(attempt {attempt}/{MAX_RETRIES}).")
                time.sleep(wait)
                continue
            print(f"[warn] Status {resp.status_code} on attempt {attempt}.")
        except requests.RequestException as e:
            last_exc = e
            print(f"[warn] Request error on attempt {attempt}: {e}")

        wait = BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 1)
        time.sleep(wait)

    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts. "
                        f"Last error: {last_exc}")


def _text(el) -> str:
    return el.get_text(strip=True) if el else ""


def build_dated_url(url: str, date_str: str) -> str:
    """
    Ensure the given URL points at the requested date.
    - If the URL already has a 'date=' query param, replace its value.
    - If it has no query string at all, append '?date=YYYY-MM-DD'.
    - If it has other query params but no 'date=', append '&date=YYYY-MM-DD'.
    """
    parsed = urlsplit(url)
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)

    found = False
    new_pairs = []
    for k, v in query_pairs:
        if k == "date":
            new_pairs.append((k, date_str))
            found = True
        else:
            new_pairs.append((k, v))
    if not found:
        new_pairs.append(("date", date_str))

    new_query = urlencode(new_pairs)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))


def _parse_caption_date(html: str) -> date | None:
    """
    Extract the date from the table caption, e.g. "Batter vs Pitcher (6/19/26)".
    Returns a date object or None if unparseable.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try <table id="searchable"> first, then any BvP table
    table = soup.find("table", id="searchable")
    if table is None:
        for t in soup.find_all("table"):
            cap = t.find("caption")
            if cap and "Batter vs Pitcher" in cap.get_text():
                table = t
                break

    if table is None:
        return None

    cap = table.find("caption")
    if not cap:
        return None

    # Match patterns like (6/19/26) or (06/19/2026)
    m = re.search(r"\((\d{1,2})/(\d{1,2})/(\d{2,4})\)", cap.get_text())
    if not m:
        return None

    month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if year < 100:
        year += 2000  # 26 -> 2026
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _extract_last5_tob(batter_td):
    tip = batter_td.find(attrs={"data-tooltip": re.compile(r"times on base last 5 gms")})
    if not tip:
        return None
    raw = tip["data-tooltip"]
    nums = re.findall(r"\d+", raw.split("(")[0])
    return [int(n) for n in nums] if nums else None


def _extract_recent_ops(batter_td):
    sub = batter_td.find("div", class_="tr_sub")
    if not sub:
        return None
    lbl = sub.find("span", class_="tr_lbl")
    if not lbl:
        return None
    parts = lbl.get_text(separator="|", strip=True).split("|")
    if len(parts) >= 2 and parts[0] == "OPS":
        return parts[1]
    return None


def parse_bvp_table(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", id="searchable")
    if table is None:
        for t in soup.find_all("table"):
            cap = t.find("caption")
            if cap and "Batter vs Pitcher" in cap.get_text():
                table = t
                break
    if table is None:
        raise ValueError("Could not locate the Batter vs Pitcher table.")

    caption = _text(table.find("caption"))
    tbody = table.find("tbody")
    if tbody is None:
        raise ValueError("Table found but no <tbody> present.")

    rows_out = []
    skipped_promo = 0

    for tr in tbody.find_all("tr", recursive=False):
        row_classes = tr.get("class") or []

        if "trclt" in row_classes:
            skipped_promo += 1
            continue

        tds = tr.find_all("td", recursive=False)
        if len(tds) < 15:
            continue

        confirmed = "conf" in row_classes
        no_history = "no_history" in row_classes

        batter_td = tds[0]
        small = batter_td.find("small")
        name = batter_td.get_text(separator="|", strip=True).split("|")[0].strip()

        pos, hand = None, None
        if small:
            small_txt = small.get_text(strip=True)
            m = re.search(r",\s*([A-Z0-9/]+)\s*\(([A-Z])\)", small_txt)
            if m:
                pos, hand = m.group(1), m.group(2)
                name = f"{name}, {pos} ({hand})"

        injury_tag = None
        inj = batter_td.find("span", class_="inj_desig")
        if inj:
            injury_tag = _text(inj)

        pitcher_td = tds[2]
        a = pitcher_td.find("a")
        pitcher_hand = None
        if a:
            small_p = a.find("small")
            if small_p:
                m = re.search(r"\(([A-Z])\)", small_p.get_text())
                if m:
                    pitcher_hand = m.group(1)
                pitcher_name = a.get_text(separator="|", strip=True).split("|")[0].strip()
                if pitcher_hand:
                    pitcher_name = f"{pitcher_name} ({pitcher_hand})"
            else:
                pitcher_name = a.get_text(strip=True)
        else:
            pitcher_name = pitcher_td.get_text(separator="|", strip=True).split("|")[0].strip()
        pitcher_url = a["href"] if a and a.has_attr("href") else None

        opp_team_span = tds[3].find("span", class_="opteam")
        opp_team = _text(opp_team_span)

        team_spans = tds[3].select("span.gricons span.team")
        team_codes = []
        for ts in team_spans:
            cls = ts.get("class") or []
            code = [c for c in cls if c not in ("team", "after")]
            team_codes.append(code[0] if code else "")
        weather_img = tds[3].find("img")
        weather = weather_img.get("title") if weather_img else None
        wind_span = tds[3].find("span", class_="grdeg")
        wind = wind_span.get_text(strip=True)[-2:] if wind_span else None
        if len(team_codes) == 2:
            game_full = f"{team_codes[0]} @ {team_codes[1]}"
        else:
            game_full = opp_team
        game_html_raw = tds[3].decode_contents()  # exact original markup for this cell

        # Recent trend arrows (td[1]): green=up, red=down, gray=flat
        trend_span = tds[1].find("span", class_="recent")
        recent_trend = []
        if trend_span:
            for s in trend_span.find_all("span", recursive=False):
                cls = s.get("class") or []
                if "green" in cls:
                    recent_trend.append("up")
                elif "red" in cls:
                    recent_trend.append("down")
                elif "gray" in cls:
                    recent_trend.append("flat")

        hrf_span = tds[4].find("span", class_="fcasthrf")
        hrf = _text(hrf_span) if hrf_span else (_text(tds[4]) or None)

        qab_pct = _text(tds[5]) or None
        hh_pct_or_note = _text(tds[6]) or None

        ab_span = tds[7].find("span", class_="opatbats")
        h_span = tds[8].find("span", class_="ophits")
        ab = _text(ab_span) if ab_span else (_text(tds[7]) or None)
        h = _text(h_span) if h_span else (_text(tds[8]) or None)

        two_b_three_b = _text(tds[9]) or None
        hr = _text(tds[10]) or None
        bb = _text(tds[11]) or None
        ba = _text(tds[12]) or None
        obp = _text(tds[13]) or None
        ops = _text(tds[14]) or None

        row = {
            "Batter": name,
            "Icon": recent_trend,   # kept as list internally for HTML coloring; flattened for csv/json
            "Pitcher": pitcher_name,
            "Game": game_full,
            "Game_HTML": game_html_raw,
            "HRF": hrf,
            "qAB": qab_pct,
            "HH%": hh_pct_or_note,
            "AB": ab,
            "H": h,
            "2B/3B": two_b_three_b,
            "HR": hr,
            "BB": bb,
            "BA": ba,
            "OBP": obp,
            "OPS": ops,
        }
        rows_out.append(row)

    if skipped_promo:
        print(f"[info] Skipped {skipped_promo} promo/ad row(s).")

    return rows_out


def write_csv(rows, path):
    if not rows:
        print("No rows to write.")
        return
    cols = ["Batter", "Icon", "Pitcher", "Game", "HRF", "qAB", "HH%",
            "AB", "H", "2B/3B", "HR", "BB", "BA", "OBP", "OPS"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for r in rows:
            r2 = {c: r.get(c, "") for c in cols}
            if isinstance(r2.get("Icon"), list):
                r2["Icon"] = "".join("^" if t == "up" else ("v" if t == "down" else ">") for t in r2["Icon"])
            writer.writerow(r2)
    print(f"Wrote {len(rows)} rows -> {path}")


def write_json(rows, path):
    cols = ["Batter", "Icon", "Pitcher", "Game", "HRF", "qAB", "HH%",
            "AB", "H", "2B/3B", "HR", "BB", "BA", "OBP", "OPS"]
    flat = []
    for r in rows:
        r2 = {c: r.get(c, "") for c in cols}
        if isinstance(r2.get("Icon"), list):
            r2["Icon"] = "".join("^" if t == "up" else ("v" if t == "down" else ">") for t in r2["Icon"])
        flat.append(r2)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(flat, f, indent=2)
    print(f"Wrote {len(flat)} rows -> {path}")


ARROW_COLOR = {"up": "#1a7a32", "down": "#c0392b", "flat": "#888888"}
ARROW_CHAR = {"up": "▲", "down": "▼", "flat": "▶"}


def localize_game_html(game_html: str, local_prefix: str = "assets/images/") -> str:
    if not game_html:
        return game_html
    return re.sub(r'(?<=src=")\/images\/', local_prefix, game_html)


def write_html(rows, path, source_base_url=None, local_assets_prefix=None):
    cols = ["Batter", "Icon", "Pitcher", "Game", "HRF", "qAB", "HH%",
            "AB", "H", "2B/3B", "HR", "BB", "BA", "OBP", "OPS"]

    def render_icon(icons):
        spans = []
        for t in icons:
            color = ARROW_COLOR.get(t, "#888")
            char = ARROW_CHAR.get(t, "-")
            spans.append(f'<span style="color:{color};font-weight:bold;">{char}</span>')
        return "".join(spans)

    rows_html = []
    for r in rows:
        cells = []
        for c in cols:
            if c == "Game":
                val = r.get("Game_HTML", r.get("Game", ""))
                if local_assets_prefix:
                    val = localize_game_html(val, local_assets_prefix)
            elif c == "Icon":
                val = render_icon(r.get(c, []))
            else:
                val = r.get(c, "")
            cells.append(f"<td style='padding:6px 10px;border-bottom:1px solid #eee;'>{val}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    header_html = "".join(
        f"<th style='padding:6px 10px;text-align:left;background:#f4f4f4;'>{c}</th>" for c in cols
    )

    base_tag = f'<base href="{source_base_url}">' if source_base_url else ""

    html = f"""<html><head><meta charset="utf-8">{base_tag}</head>
<body style="font-family:Arial,sans-serif;">
<table style="border-collapse:collapse;width:100%;">
<thead><tr>{header_html}</tr></thead>
<tbody>{''.join(rows_html)}</tbody>
</table>
</body></html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {len(rows)} rows -> {path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape Batter vs Pitcher table.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="Full URL of the BvP page (live fetch). "
                                    "The 'date=' param is auto-set/overwritten using --date "
                                    "(defaults to today) unless --no-date-override is passed.")
    src.add_argument("--html", help="Path to a locally saved HTML file (no network call).")
    parser.add_argument("--date", default=None,
                         help="Date to scrape in YYYY-MM-DD format. Defaults to TODAY. "
                              "Only applies when using --url (ignored for --html).")
    parser.add_argument("--no-date-override", action="store_true",
                         help="Use --url exactly as given, without inserting/overwriting "
                              "its date= parameter.")
    parser.add_argument("--today-only", action="store_true",
                         help="Only keep rows whose page caption date matches the target date "
                              "(today, or the date given via --date). Rows from other dates "
                              "are dropped. When using --url this is redundant if the site "
                              "always returns a single day, but useful as a safety net or "
                              "when reading a saved --html file that may contain multiple days.")
    parser.add_argument("--mode", choices=["test", "full"], default="test",
                         help="'test' = first 5 rows only, 'full' = all rows.")
    parser.add_argument("--out", default=None, help="Output file path.")
    parser.add_argument("--format", choices=["csv", "json", "html"], default="csv")
    parser.add_argument("--source-url", default=None,
                         help="Original page URL, used as <base href> in HTML export so "
                              "relative image paths (team/weather icons) resolve correctly.")
    parser.add_argument("--local-assets", default=None,
                         help="If set, rewrites '/images/...' src paths in the Game column "
                              "to this local prefix (e.g. 'assets/images/') instead of "
                              "linking the live site. Use after running download_assets.py.")
    args = parser.parse_args()

    # ------------------------------------------------------------------ #
    #  Resolve the target date (used for URL injection + today-only filter)
    # ------------------------------------------------------------------ #
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            parser.error(f"--date must be YYYY-MM-DD, got: {args.date!r}")
    else:
        target_date = date.today()

    target_date_str = target_date.strftime("%Y-%m-%d")
    print(f"[info] Target date: {target_date_str}")

    # ------------------------------------------------------------------ #
    #  Fetch / read HTML
    # ------------------------------------------------------------------ #
    if args.html:
        print(f"[info] Reading local file {args.html} ...")
        with open(args.html, encoding="utf-8", errors="ignore") as f:
            html = f.read()
    else:
        # Inject date into URL unless user explicitly opted out
        fetch_url = args.url
        if not args.no_date_override:
            fetch_url = build_dated_url(args.url, target_date_str)
            if fetch_url != args.url:
                print(f"[info] URL rewritten with date param -> {fetch_url}")
        print(f"[info] Fetching {fetch_url} ...")
        html = fetch(fetch_url)

    # ------------------------------------------------------------------ #
    #  Parse
    # ------------------------------------------------------------------ #
    print("[info] Parsing table ...")
    rows = parse_bvp_table(html)
    print(f"[info] Parsed {len(rows)} total data rows.")

    # ------------------------------------------------------------------ #
    #  --today-only filter: verify the caption date matches target_date
    # ------------------------------------------------------------------ #
    if args.today_only:
        caption_date = _parse_caption_date(html)
        if caption_date is None:
            print("[warn] --today-only: could not parse a date from the table caption. "
                  "No rows will be filtered out (assuming all rows are current).")
        elif caption_date != target_date:
            print(f"[warn] --today-only: caption date {caption_date} != target date "
                  f"{target_date}. Dropping all {len(rows)} row(s) — "
                  "the page does not appear to contain today's data.")
            rows = []
        else:
            print(f"[info] --today-only: caption date {caption_date} matches target. "
                  f"Keeping all {len(rows)} row(s).")

    # ------------------------------------------------------------------ #
    #  Test-mode truncation
    # ------------------------------------------------------------------ #
    if args.mode == "test":
        rows = rows[:5]
        print("[info] TEST MODE: truncated to first 5 rows.")

    # ------------------------------------------------------------------ #
    #  Output
    # ------------------------------------------------------------------ #
    out_path = args.out
    if out_path is None:
        suffix = "test" if args.mode == "test" else "full"
        ext = {"csv": "csv", "json": "json", "html": "html"}[args.format]
        out_path = f"bvp_{suffix}.{ext}"

    if args.format == "csv":
        write_csv(rows, out_path)
    elif args.format == "json":
        write_json(rows, out_path)
    else:
        write_html(rows, out_path, source_base_url=args.source_url or args.url,
                   local_assets_prefix=args.local_assets)

    for r in rows[:5]:
        print(r)


if __name__ == "__main__":
    main()