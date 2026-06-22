"""
MLB Home Run Prediction table scraper
--------------------------------------
Source: https://www.fantasyinfocentral.com/betting/mlb/hr-predictions

Confirmed table structure from real page HTML:

<table id="searchable" class="long hr_prob">
  <caption>Most likely to homer (6/19/26)</caption>
  <thead>
    <tr>
      <th>Batter</th>       [0]
      <th>Pitcher</th>      [1]
      <th>Game</th>         [2]  ← contains team icons + weather img + wind arrow
      <th>HRF</th>          [3]  ← HRForce weather index
      <th>HR Pred</th>      [4]  ← FIC HR prediction %
      <th>Trend</th>        [5]  ← bar-chart figure + HR-last-5 tooltip; HTML preserved
      <th>Odds</th>         [6]  ← sportsbook odds (Over 0.5 HR) + provider logo; HTML preserved
      <th>AB</th>           [7]
      <th>H</th>            [8]
      <th>HR</th>           [9]
      <th>BA</th>           [10]
      <th>OBP</th>          [11]
      <th>OPS</th>          [12]
      <th></th>             [13] ← "more" link (ignored)
    </tr>
  </thead>
  <tbody>
    <tr class="db conf">             ← confirmed lineup spot, has matchup history
    <tr class="db conf no_history">  ← confirmed spot, no prior AB vs this pitcher
    <tr class="db lnphd">           ← lineup not yet confirmed
    <tr class="db lnphd no_history"> ← unconfirmed + no history
    <tr class="trclt">              ← in-table promo row -- SKIP
  </tbody>
</table>

NOTE vs. the Hit Prediction table: there is no separate O/U column here --
the home run line is implicitly "Over 0.5 HR" and is baked into the Odds
cell, so this scraper has 14 <td>s per row instead of 15.

Field notes
-----------
td[0]  Batter name in text node; <small> holds ", <span.pos>POS</span> (HAND)"
       td class is "confirmed" when lineup is set, "notlnup" when not yet confirmed
       An optional <span.inj_desig> badge ("D"/"IL"/etc, classes "ques"/"out")
       with a data-tooltip carries injury status + est. return date -- captured
       as internal metadata (_injury_status / _injury_note), NOT a visible column.
td[1]  Pitcher name inside <a>; <small> holds "(HAND)"; href encodes date+slug
td[2]  Game cell: raw HTML preserved in Game_HTML (team CSS classes + weather img +
       wind arrow); plain-text "AWAY @ HOME" extracted into Game field
td[3]  HRF: inside <span.fcasthrf>; tooltip carries weather note
td[4]  HR Pred %: plain text
td[5]  Trend: raw HTML preserved in Trend_HTML (bar chart figure); structured data
       extracted as last5_hr list and last5_tooltip string from data-tooltip attr
       (tooltip text is "N, N, N, N, N (HRs last 5 gms)")
td[6]  Odds: raw HTML preserved in Odds_HTML; structured extraction:
         odds_line (e.g. "+210"), odds_provider (e.g. "caesars"),
         odds_provider_img (relative path to provider logo SVG).
         Cell is sometimes the literal text "--" when no line is posted --
         odds_line/provider/img are left None in that case.
td[7]  AB: inside <span.opatbats>; "never faced" for no_history rows
td[8]  H: inside <span.ophits>
td[9]  HR: plain text (inside td.dmnrw)
td[10] BA
td[11] OBP
td[12] OPS

HTML preservation policy
------------------------
Trend_HTML and Odds_HTML are captured as raw inner HTML for use in a future
frontend hub. The bar chart (Trend) uses CSS classes and inline styles defined
on the source site; the Odds cell contains provider logo <img> tags. Both need
the source site's CSS/assets to render correctly unless download_assets.py is
run first and paths are rewritten via localize_html().

Game_HTML follows the same pattern as the Hit Prediction scraper: team sprites
use CSS class names like <span class="team BOS"> which rely on background-image
rules from the site's stylesheet.

USAGE
-----
# Parse a saved HTML file (test mode = first 5 rows):
    python hr_pred.py --html MLB_Home_Run.html --mode test

# Live fetch with today's date auto-injected into URL:
    python hr_pred.py --url "https://www.fantasyinfocentral.com/betting/mlb/hr-predictions" --mode full

# Fetch with date filter + verify caption matches:
    python hr_pred.py --url "https://www.fantasyinfocentral.com/betting/mlb/hr-predictions" --today-only --mode full

# Output formats:
    python hr_pred.py --html file.html --format json --out hr_pred.json
    python hr_pred.py --html file.html --format html --out hr_pred.html
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

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
LOCKFILE = os.path.join(os.path.dirname(__file__), ".last_run_hr_pred")

# Output columns — exactly mirrors the visible table column headers:
#   Batter | Pitcher | Game | HRF | HR Pred | Trend | Odds | AB | H | HR | BA | OBP | OPS
#
# Batter  = "N. Kurtz, 1B (L)"  name + pos + hand combined, matching page display
# Pitcher = "J. Soriano (R)"     name + hand combined
# Game    = "ANA @ ATH"          plain text for CSV/JSON; Game_HTML carries icons
# Trend   = "0,2,0,0,0"          last-5 HR comma string; Trend_HTML carries bar chart
# Odds    = "+280"               odds line only (None if "--"); Odds_HTML carries provider logo
DATA_COLS = [
    "Batter", "Pitcher", "Game",
    "HRF", "HR Pred", "Trend", "Odds",
    "AB", "H", "HR", "BA", "OBP", "OPS",
]

# ---------------------------------------------------------------------------
# Rate-limit guard
# ---------------------------------------------------------------------------

def _enforce_min_interval():
    if os.path.exists(LOCKFILE):
        with open(LOCKFILE) as f:
            try:
                last = float(f.read().strip())
            except ValueError:
                last = 0
        elapsed = time.time() - last
        if elapsed < MIN_SECONDS_BETWEEN_RUNS:
            wait = MIN_SECONDS_BETWEEN_RUNS - elapsed
            print(f"[rate-limit guard] Ran {elapsed:.0f}s ago. Sleeping {wait:.0f}s.")
            time.sleep(wait)


def _record_run():
    with open(LOCKFILE, "w") as f:
        f.write(str(time.time()))


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

def fetch(url: str) -> str:
    _enforce_min_interval()
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
                _record_run()
                return resp.text
            if resp.status_code == 429:
                wait = BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 1)
                print(f"[429] Rate limited. Backing off {wait:.1f}s (attempt {attempt}/{MAX_RETRIES}).")
                time.sleep(wait)
                continue
            print(f"[warn] Status {resp.status_code} on attempt {attempt}.")
        except requests.RequestException as e:
            last_exc = e
            print(f"[warn] Request error on attempt {attempt}: {e}")
        wait = BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 1)
        time.sleep(wait)

    raise RuntimeError(
        f"Failed to fetch {url} after {MAX_RETRIES} attempts. Last error: {last_exc}"
    )


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def build_dated_url(url: str, date_str: str) -> str:
    """Inject or replace the 'date=' query param with date_str (YYYY-MM-DD)."""
    parsed = urlsplit(url)
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    found = False
    new_pairs = []
    for k, v in pairs:
        if k == "date":
            new_pairs.append((k, date_str))
            found = True
        else:
            new_pairs.append((k, v))
    if not found:
        new_pairs.append(("date", date_str))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(new_pairs), parsed.fragment))


# ---------------------------------------------------------------------------
# Caption-date extraction (for --today-only filter)
# ---------------------------------------------------------------------------

def parse_caption_date(html: str) -> date | None:
    """
    Extract the date from the table caption, e.g.
    "Most likely to homer (6/19/26)" → date(2026, 6, 19)
    Returns None if the caption or date cannot be found/parsed.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = (
        soup.find("table", id="searchable")
        or next(
            (t for t in soup.find_all("table")
             if t.find("caption") and "homer" in t.find("caption").get_text()),
            None,
        )
    )
    if not table:
        return None
    cap = table.find("caption")
    if not cap:
        return None
    m = re.search(r"\((\d{1,2})/(\d{1,2})/(\d{2,4})\)", cap.get_text())
    if not m:
        return None
    month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if year < 100:
        year += 2000
    try:
        return date(year, month, day)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _text(el) -> str:
    return el.get_text(strip=True) if el else ""


def _localize_html(raw_html: str, local_prefix: str = "assets/images/") -> str:
    """
    Rewrite '/images/...' src paths to a local assets prefix.
    Call this after running download_assets.py to break the live-site dependency.
    """
    if not raw_html:
        return raw_html
    return re.sub(r'(?<=src=")/images/', local_prefix, raw_html)


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

def parse_hr_pred_table(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # Locate table
    table = soup.find("table", id="searchable")
    if table is None:
        for t in soup.find_all("table"):
            cap = t.find("caption")
            if cap and "homer" in cap.get_text():
                table = t
                break
    if table is None:
        raise ValueError("Could not locate the Home Run Prediction table (id='searchable').")

    tbody = table.find("tbody")
    if tbody is None:
        raise ValueError("Table found but no <tbody> present.")

    rows_out = []
    skipped_promo = 0

    for tr in tbody.find_all("tr", recursive=False):
        row_classes = tr.get("class") or []

        # Skip in-table promo/ad rows
        if "trclt" in row_classes:
            skipped_promo += 1
            continue

        tds = tr.find_all("td", recursive=False)
        if len(tds) < 14:
            continue  # malformed row

        no_history = "no_history" in row_classes

        # ------------------------------------------------------------------
        # td[0] — Batter
        # ------------------------------------------------------------------
        batter_td = tds[0]
        lineup_confirmed = "confirmed" in (batter_td.get("class") or [])

        # Injury badge (optional): <span.inj_desig ques|out> inside a tooltip
        # span carrying the status text + est. return date. Pull it out before
        # reading <small>/name text so it doesn't pollute either.
        injury_status, injury_note = None, None
        inj_span = batter_td.find("span", class_="inj_desig")
        if inj_span:
            inj_classes = [c for c in (inj_span.get("class") or []) if c != "inj_desig"]
            injury_status = inj_classes[0] if inj_classes else None  # "ques" / "out"
            tooltip_wrap = inj_span.find_parent(attrs={"data-tooltip": True})
            injury_note = tooltip_wrap.get("data-tooltip") if tooltip_wrap else None
            tooltip_wrap.extract() if tooltip_wrap else inj_span.extract()

        # Name is the first text chunk before the <small>
        small = batter_td.find("small")
        if small:
            small.extract()
        batter_name = batter_td.get_text(strip=True)
        pos, batter_hand = None, None
        if small:
            pos_span = small.find("span", class_="pos")
            pos = _text(pos_span) if pos_span else None
            hand_m = re.search(r"\(([A-Z])\)", small.get_text())
            batter_hand = hand_m.group(1) if hand_m else None

        # ------------------------------------------------------------------
        # td[1] — Pitcher
        # ------------------------------------------------------------------
        pitcher_td = tds[1]
        a = pitcher_td.find("a")
        pitcher_name, pitcher_hand, pitcher_url = None, None, None
        if a:
            pitcher_url = a.get("href")
            small_p = a.find("small")
            if small_p:
                hand_m = re.search(r"\(([A-Z])\)", small_p.get_text())
                pitcher_hand = hand_m.group(1) if hand_m else None
                small_p.extract()
            pitcher_name = a.get_text(strip=True)
        else:
            pitcher_name = _text(pitcher_td)

        # ------------------------------------------------------------------
        # td[2] — Game  (HTML preserved + plain-text extracted)
        # ------------------------------------------------------------------
        game_td = tds[2]
        game_html_raw = game_td.decode_contents()  # raw inner HTML for frontend use

        # Away team: first <span class="team X"> (no "after" class)
        # Home team: <span class="team after X">
        team_spans = game_td.select("span.gricons span.team")
        team_codes = []
        for ts in team_spans:
            cls = ts.get("class") or []
            code = [c for c in cls if c not in ("team", "after")]
            team_codes.append(code[0] if code else "")
        game_plain = f"{team_codes[0]} @ {team_codes[1]}" if len(team_codes) == 2 else ""

        # Weather: <img> title and src
        weather_img_tag = game_td.find("img")
        weather_title = weather_img_tag.get("title") if weather_img_tag else None
        weather_img_src = weather_img_tag.get("src") if weather_img_tag else None

        # Wind: the numeric text inside <span.grdeg> after the arrow sub-span
        wind_mph = None
        grdeg = game_td.find("span", class_="grdeg")
        if grdeg:
            # The visible text in grdeg is the wind speed; strip the nested arrow spans
            for sub in grdeg.find_all("span"):
                sub.decompose()
            wind_text = grdeg.get_text(strip=True)
            m = re.search(r"(\d+)", wind_text)
            wind_mph = int(m.group(1)) if m else None

        # ------------------------------------------------------------------
        # td[3] — HRF
        # ------------------------------------------------------------------
        hrf_td = tds[3]
        hrf_span = hrf_td.find("span", class_="fcasthrf")
        hrf_val = _text(hrf_span) if hrf_span else _text(hrf_td) or None
        hrf_note = hrf_span.get("data-tooltip") if hrf_span else None

        # ------------------------------------------------------------------
        # td[4] — HR Prediction %
        # ------------------------------------------------------------------
        hr_pred_pct = _text(tds[4]) or None

        # ------------------------------------------------------------------
        # td[5] — Trend  (HTML preserved + structured data extracted)
        # ------------------------------------------------------------------
        trend_td = tds[5]
        trend_html_raw = trend_td.decode_contents()  # bar chart + CSS classes

        # Tooltip carries "1, 1, 0, 0, 1 (HRs last 5 gms)"
        trend_tooltip_span = trend_td.find(attrs={"data-tooltip": re.compile(r"HRs last 5 gms")})
        last5_tooltip = trend_tooltip_span.get("data-tooltip") if trend_tooltip_span else None
        last5_hr: list[int] = []
        if last5_tooltip:
            nums = re.findall(r"\d+", last5_tooltip.split("(")[0])
            last5_hr = [int(n) for n in nums]

        # ------------------------------------------------------------------
        # td[6] — Odds  (HTML preserved + structured extraction)
        # ------------------------------------------------------------------
        odds_td = tds[6]
        odds_html_raw = odds_td.decode_contents()  # provider logo <img> + line

        odds_line, odds_provider, odds_provider_img = None, None, None
        genicons_span = odds_td.find("span", class_="genicons")
        if genicons_span:
            # Provider name is the non-"genicons" class on the span
            gi_classes = [c for c in (genicons_span.get("class") or []) if c != "genicons"]
            odds_provider = gi_classes[0] if gi_classes else None

            mline = genicons_span.find("span", class_="mline")
            if mline:
                # Strip nested <small> and grab the numeric odds text
                for sub in mline.find_all("small"):
                    sub.decompose()
                odds_line = mline.get_text(strip=True) or None

            logo_img = genicons_span.find("img", class_="tdbklgo")
            odds_provider_img = logo_img.get("src") if logo_img else None
        # else: cell is the literal placeholder "--" (no line posted) -- leave as None

        # ------------------------------------------------------------------
        # td[7-12] — Matchup stats vs this pitcher
        # ------------------------------------------------------------------
        ab_span = tds[7].find("span", class_="opatbats")
        ab = _text(ab_span) if ab_span else _text(tds[7]) or None
        # "never faced" string for no_history rows — keep as-is

        h_span = tds[8].find("span", class_="ophits")
        h = _text(h_span) if h_span else _text(tds[8]) or None

        hr  = _text(tds[9]) or None
        ba  = _text(tds[10]) or None
        obp = _text(tds[11]) or None
        ops = _text(tds[12]) or None

        # ------------------------------------------------------------------
        # td[13] — BvP detail link
        # ------------------------------------------------------------------
        bvp_link = tds[13].find("a") if len(tds) > 13 else None
        bvp_url = bvp_link.get("href") if bvp_link else None

        # ------------------------------------------------------------------
        # Assemble row — keys match DATA_COLS exactly (page header labels)
        # ------------------------------------------------------------------

        # Batter: "N. Kurtz, 1B (L)" — same format as shown in the page
        batter_display = batter_name
        if pos and batter_hand:
            batter_display = f"{batter_name}, {pos} ({batter_hand})"
        elif pos:
            batter_display = f"{batter_name}, {pos}"

        # Pitcher: "J. Soriano (R)"
        pitcher_display = pitcher_name
        if pitcher_hand:
            pitcher_display = f"{pitcher_name} ({pitcher_hand})"

        row = {
            # Visible columns — names match page headers exactly
            "Batter":   batter_display,          # "N. Kurtz, 1B (L)"
            "Pitcher":  pitcher_display,          # "J. Soriano (R)"
            "Game":     game_plain,               # "ANA @ ATH" (plain); Game_HTML has icons
            "HRF":      hrf_val,                  # "1.5" or "n/a"
            "HR Pred":  hr_pred_pct,               # "30%"
            "Trend":    ",".join(str(n) for n in last5_hr),  # "0,2,0,0,0"; Trend_HTML has bar chart
            "Odds":     odds_line,                # "+280" or None; Odds_HTML has provider logo
            "AB":       ab,
            "H":        h,
            "HR":       hr,
            "BA":       ba,
            "OBP":      obp,
            "OPS":      ops,
            # Raw HTML fields — used in --format html output and future frontend
            "Game_HTML":  game_html_raw,
            "Trend_HTML": trend_html_raw,
            "Odds_HTML":  odds_html_raw,
            # Internal metadata (not in output columns but available for filtering)
            "_confirmed":      lineup_confirmed,
            "_no_history":     no_history,
            "_bvp_url":        bvp_url,
            "_pitcher_url":    pitcher_url,
            "_hrf_note":       hrf_note,
            "_weather":        weather_title,
            "_weather_img":    weather_img_src,
            "_wind_mph":       wind_mph,
            "_odds_provider":      odds_provider,
            "_odds_provider_img":  odds_provider_img,
            "_injury_status":  injury_status,   # "ques" / "out" / None
            "_injury_note":    injury_note,     # e.g. "DAY-TO-DAY. Est. return: 6/21/26"
        }
        rows_out.append(row)

    if skipped_promo:
        print(f"[info] Skipped {skipped_promo} promo/ad row(s).")

    return rows_out


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _flatten_for_file(row: dict) -> dict:
    """Pick only DATA_COLS fields; all values are already plain strings or None."""
    return {c: (row.get(c) or "") for c in DATA_COLS}


def write_csv(rows: list, path: str):
    if not rows:
        print("No rows to write.")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DATA_COLS)
        writer.writeheader()
        for r in rows:
            writer.writerow(_flatten_for_file(r))
    print(f"Wrote {len(rows)} rows -> {path}")


def write_json(rows: list, path: str):
    flat = [_flatten_for_file(r) for r in rows]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(flat, f, indent=2)
    print(f"Wrote {len(flat)} rows -> {path}")


def write_html(rows: list, path: str,
               source_base_url: str | None = None,
               local_assets_prefix: str | None = None):
    """
    Emit an HTML table with column headers matching the source page exactly.
    Game, Trend, and Odds cells use their raw HTML so team sprites, bar charts,
    and provider logos render (requires source site CSS, or run download_assets.py
    first and pass --local-assets to rewrite /images/ paths).
    Pass --source-url to add a <base href> so relative paths resolve live.
    """
    # Columns whose cell content is the raw inner HTML from the source page
    RAW_HTML_CELLS = {"Game": "Game_HTML", "Trend": "Trend_HTML", "Odds": "Odds_HTML"}

    def _cell(col, row):
        if col in RAW_HTML_CELLS:
            markup = row.get(RAW_HTML_CELLS[col]) or ""
            if local_assets_prefix:
                markup = _localize_html(markup, local_assets_prefix)
            return markup
        val = row.get(col)
        return str(val) if val is not None else ""

    header_html = "".join(
        f"<th style='padding:6px 10px;background:#f4f4f4;white-space:nowrap;border-bottom:2px solid #ccc;'>{c}</th>"
        for c in DATA_COLS
    )
    rows_html = []
    for r in rows:
        cells = "".join(
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;vertical-align:middle;'>{_cell(c, r)}</td>"
            for c in DATA_COLS
        )
        rows_html.append(f"<tr>{cells}</tr>")

    base_tag = f'<base href="{source_base_url}">' if source_base_url else ""
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{base_tag}
<style>
  body {{ font-family: Arial, sans-serif; font-size: 13px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border-right: 1px solid #eee; text-align: left; }}
  tr:hover {{ background: #f9f9f9; }}
  /* Minimal bar-chart styles so Trend column renders without the source stylesheet */
  figure.chart-stats.chbar {{ display:flex; flex-direction:column; overflow:hidden;
                               height:35px; width:65px; margin:0; box-shadow:none; }}
  .bars {{ flex:1; display:flex; align-items:flex-end; overflow:hidden; gap:1px; position:relative; }}
  .bar {{ flex:1; background:#888; min-width:6px; }}
  .bar.gold {{ background:#e6ac00; }}
  .y-axis {{ position:absolute; left:0; right:0; border-top:1px dashed #ccc; }}
  .y-label {{ font-size:9px; color:#999; }}
  /* Hide tooltip wrapper border */
  td span.tooltip {{ border-bottom: none; }}
</style>
</head>
<body>
<table>
<thead><tr>{header_html}</tr></thead>
<tbody>{''.join(rows_html)}</tbody>
</table>
</body></html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {len(rows)} rows -> {path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scrape the MLB Home Run Prediction table from Fantasy Info Central."
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url",  help="Live URL to fetch. Date is auto-injected unless --no-date-override.")
    src.add_argument("--html", help="Path to a locally saved HTML file (no network call).")

    parser.add_argument(
        "--date", default=None,
        help="Target date in YYYY-MM-DD. Defaults to TODAY. Used for URL injection and "
             "--today-only filtering. Ignored for --html (no URL to rewrite).",
    )
    parser.add_argument(
        "--no-date-override", action="store_true",
        help="Use --url exactly as given without injecting a date= param.",
    )
    parser.add_argument(
        "--today-only", action="store_true",
        help="Drop all rows when the table caption date does not match the target date "
             "(today, or --date). Useful as a safety net when the page might cache "
             "yesterday's data, or when parsing a saved --html file to confirm it is current.",
    )
    parser.add_argument(
        "--mode", choices=["test", "full"], default="test",
        help="'test' = first 5 rows; 'full' = all rows.",
    )
    parser.add_argument("--out",    default=None, help="Output file path.")
    parser.add_argument("--format", choices=["csv", "json", "html"], default="csv")
    parser.add_argument(
        "--source-url", default=None,
        help="Original page URL; added as <base href> in HTML output so relative "
             "asset paths (team sprites, weather icons) resolve against the live site.",
    )
    parser.add_argument(
        "--local-assets", default=None,
        help="After running download_assets.py, pass the local prefix here "
             "(e.g. 'assets/images/') to rewrite /images/... src paths in HTML output.",
    )
    args = parser.parse_args()

    # ---- Resolve target date -----------------------------------------------
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            parser.error(f"--date must be YYYY-MM-DD, got: {args.date!r}")
    else:
        target_date = date.today()
    target_date_str = target_date.strftime("%Y-%m-%d")
    print(f"[info] Target date: {target_date_str}")

    # ---- Fetch / read HTML -------------------------------------------------
    if args.html:
        print(f"[info] Reading local file: {args.html}")
        with open(args.html, encoding="utf-8", errors="ignore") as f:
            html = f.read()
    else:
        fetch_url = args.url
        if not args.no_date_override:
            fetch_url = build_dated_url(args.url, target_date_str)
            if fetch_url != args.url:
                print(f"[info] URL rewritten with date param -> {fetch_url}")
        print(f"[info] Fetching {fetch_url} ...")
        html = fetch(fetch_url)

    # ---- Parse -------------------------------------------------------------
    print("[info] Parsing table ...")
    rows = parse_hr_pred_table(html)
    print(f"[info] Parsed {len(rows)} total data rows.")

    # ---- --today-only filter -----------------------------------------------
    if args.today_only:
        caption_date = parse_caption_date(html)
        if caption_date is None:
            print("[warn] --today-only: could not parse a date from the caption. "
                  "Keeping all rows (assuming data is current).")
        elif caption_date != target_date:
            print(f"[warn] --today-only: caption date {caption_date} != target date "
                  f"{target_date}. Dropping all {len(rows)} row(s) — page is not current.")
            rows = []
        else:
            print(f"[info] --today-only: caption date {caption_date} matches. "
                  f"Keeping all {len(rows)} row(s).")

    # ---- Test-mode truncation ----------------------------------------------
    if args.mode == "test":
        rows = rows[:5]
        print("[info] TEST MODE: truncated to first 5 rows.")

    # ---- Output ------------------------------------------------------------
    if not args.out:
        suffix = "test" if args.mode == "test" else "full"
        ext = {"csv": "csv", "json": "json", "html": "html"}[args.format]
        args.out = f"hr_pred_{suffix}.{ext}"

    if args.format == "csv":
        write_csv(rows, args.out)
    elif args.format == "json":
        write_json(rows, args.out)
    else:
        write_html(
            rows, args.out,
            source_base_url=args.source_url or (args.url if not args.html else None),
            local_assets_prefix=args.local_assets,
        )

    # Preview first few rows (output columns only)
    for r in rows[:3]:
        print({c: r.get(c) for c in DATA_COLS})


if __name__ == "__main__":
    main()