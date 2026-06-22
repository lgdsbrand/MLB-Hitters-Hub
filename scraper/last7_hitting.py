"""
MLB Last 7 Day Hitting Stats table scraper
---------------------------------------------
Source: https://razzball.com/last7dayhitting/   (Razzball "Last 7 Days" hitting stats)

Confirmed table structure from real page HTML:

<table id="neorazzstatstable" class="tablesorter">
  <thead>
    <tr>
      <th>#</th>      [0]  ← always empty in raw HTML; rank is JS-assigned client-side,
                            so this scraper assigns 1-based rank itself, in row order
      <th>Name</th>   [1]  ← player name inside <a href="https://razzball.com/player/...">
      <th>Team</th>   [2]  ← team code inside <a href="https://razzball.com/teams/...">
      <th>ESPN</th>   [3]  ← ESPN position eligibility (plain text)
      <th>Y!</th>     [4]  ← Yahoo position eligibility (plain text) -- can differ from ESPN
      <th>$</th>      [5]  ← season $ value
      <th>$/G</th>    [6]  ← $ value per game
      <th>G</th>      [7]
      <th>PA</th>     [8]
      <th>AB</th>     [9]
      <th>R</th>      [10]
      <th>H</th>      [11]
      <th>HR</th>     [12]
      <th>RBI</th>    [13]
      <th>SB</th>     [14]
      <th>CS</th>     [15]
      <th>BB</th>     [16]
      <th>SO</th>     [17]
      <th>AVG</th>    [18]
      <th>OBP</th>    [19]
      <th>SLG</th>    [20]
      <th>OPS</th>    [21]
      <th>R%</th>     [22]  ← rostered % (or similar "roster percentage" stat)
      <th>RazzID</th> [23]  ← Razzball internal player ID
    </tr>
  </thead>
  <tbody>
    <tr> ... </tr>  ← every row is a plain, unclassed <tr>; no promo/ad rows seen,
                       no lineup-confirmed states, no game/weather cells -- this is a
                       flat rolling-stats table, structurally much simpler than the
                       Hit/HR/TB prediction tables.
  </tbody>
</table>

Field notes
-----------
td[0]  Always empty in the saved HTML (<td></td>). The page's JS (tablesorter
       plugin) fills in the visible row rank 1, 2, 3... after sorting client-side.
       This scraper reproduces that by assigning rank = row's position in
       document order (1-indexed), which matches the page's default sort
       (already ranked by $ descending in the saved file).
td[1]  Name: text inside <a>; href is the player's Razzball profile page,
       captured as internal metadata (_player_url)
td[2]  Team: text inside <a>; href is the team's Razzball page,
       captured as internal metadata (_team_url)
td[3]  ESPN: plain text position eligibility string (e.g. "2B/3B/ OF")
td[4]  Y!: plain text position eligibility string -- NOT always identical to
       ESPN (different sites' position-eligibility rules diverge for some
       players), so both are extracted independently rather than deduped
td[5-22] All plain text numeric/decimal values, used as-is
td[23] RazzID: plain text numeric player ID

No caption/date marker exists on this page (it's a rolling "last 7 days"
window rather than a single calendar day), so there is no --today-only
equivalent here -- whatever the page currently shows IS "today's" 7-day
window as of fetch time.

No promo rows, no row-class states (confirmed/unconfirmed lineup, no_history,
etc.) appear in this table -- it is a flat stats grid, not a betting-odds
table, so there's nothing to skip.

Automation workflow (recommended)
---------------------------------
Cloudflare cannot be beaten headlessly every time, but you CAN automate with a
two-layer setup:

  Layer 1 - fast path (no browser): curl_cffi reuses saved cf_clearance cookies
  Layer 2 - reliable path: a Chrome instance kept open with --remote-debugging-port
            maintains a real session; scheduled runs attach via CDP silently

ONE-TIME SETUP (pass Cloudflare once, save session):
    python last7_hitting.py --bootstrap --mode full

  Chrome auto-launches and opens the page natively. Complete Cloudflare in that
  window, then press Enter in the terminal when the stats table is visible.
  If Cloudflare keeps looping, try Playwright with your installed Chrome:
    python last7_hitting.py --bootstrap --browser-headed --mode full

SCHEDULED / UNATTENDED RUNS (Task Scheduler, cron, GitHub Actions):
    python last7_hitting.py --auto --mode full

  Local: --auto tries CDP first (if Chrome is still running), then curl_cffi cookies.
  GitHub Actions: set secret LAST7_HITTING_COOKIES_JSON to contents of
  .last7_hitting_cookies.json (refresh locally when cookies expire).

Optional config file (.last7_hitting_config.json):
    {"url": "https://razzball.com/mlbhittingstats-last7days/",
     "cdp_url": "http://127.0.0.1:9222"}

Manual / debug flags (--browser-headed, --html, etc.) remain available.

USAGE
-----
# Parse a saved HTML file (test mode = first 5 rows):
    python last7_hitting.py --html "Last 7 Day Hitting Stats.html" --mode test

# Live fetch (PowerShell: keep the command on one line, or use backtick ` for continuation):
    python last7_hitting.py --url "https://razzball.com/mlbhittingstats-last7days/" --mode full

# Scheduled unattended run:
    python last7_hitting.py --auto --mode full

# Output formats:
    python last7_hitting.py --html file.html --format json --out last7_hitting.json
    python last7_hitting.py --html file.html --format html --out last7_hitting.html
"""

import argparse
import csv
import json
import os
import random
import subprocess
import sys
import time
from urllib.parse import urlparse

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
LOCKFILE = os.path.join(os.path.dirname(__file__), ".last_run_last7_hitting")
COOKIE_FILE = os.path.join(os.path.dirname(__file__), ".last7_hitting_cookies.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), ".last7_hitting_config.json")
BROWSER_PROFILE = os.path.join(os.path.dirname(__file__), ".last7_hitting_browser_profile")
CDP_PROFILE = os.path.join(os.path.dirname(__file__), ".last7_hitting_cdp_profile")
DEFAULT_URL = "https://razzball.com/mlbhittingstats-last7days/"
DEFAULT_CDP_URL = "http://127.0.0.1:9222"
COOKIES_ENV_VAR = "LAST7_HITTING_COOKIES_JSON"
CFFI_IMPERSONATE_PROFILES = ("chrome131", "chrome124", "chrome120", "edge101")
TABLE_SELECTOR = "table#neorazzstatstable"
AUTO_CDP_TIMEOUT = 90
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NEEDS_BOOTSTRAP = 2


class NeedsBootstrapError(RuntimeError):
    """Raised when automated fetch fails and a manual --bootstrap run is required."""


def _is_ci() -> bool:
    return os.environ.get("CI", "").lower() in ("1", "true", "yes") or bool(
        os.environ.get("GITHUB_ACTIONS")
    )


def _cdp_port(cdp_url: str) -> int:
    parsed = urlparse(cdp_url)
    if parsed.port:
        return parsed.port
    return 9222


def _find_chrome_executable() -> str | None:
    candidates: list[str] = []
    if sys.platform == "win32":
        for env_var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(env_var)
            if base:
                candidates.append(
                    os.path.join(base, "Google", "Chrome", "Application", "chrome.exe")
                )
    elif sys.platform == "darwin":
        candidates.append(
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
    else:
        for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
            candidates.append(name)

    for candidate in candidates:
        if sys.platform != "win32" and os.path.sep not in candidate:
            from shutil import which

            found = which(candidate)
            if found:
                return found
        elif os.path.isfile(candidate):
            return candidate
    return None


def _is_cdp_reachable(cdp_url: str, timeout: float = 2.0) -> bool:
    try:
        from curl_cffi import requests as cffi_requests

        resp = cffi_requests.get(
            cdp_url.rstrip("/") + "/json/version",
            timeout=timeout,
            impersonate=CFFI_IMPERSONATE_PROFILES[0],
        )
        return resp.status_code == 200
    except Exception:
        return False


def _launch_chrome_debugging(
    cdp_url: str,
    profile_dir: str | None = None,
    start_url: str | None = None,
) -> bool:
    chrome = _find_chrome_executable()
    if not chrome:
        print("[warn] Could not find Chrome to auto-launch.")
        return False

    port = _cdp_port(cdp_url)
    profile = profile_dir or CDP_PROFILE
    os.makedirs(profile, exist_ok=True)
    args = [
        chrome,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if start_url:
        args.append(start_url)
    else:
        args.append("about:blank")
    print(
        f"[info] Launching Chrome with remote debugging on port {port} "
        f"(profile: {profile}) ..."
    )
    try:
        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "DETACHED_PROCESS", 0)
        subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            start_new_session=sys.platform != "win32",
        )
        return True
    except OSError as e:
        print(f"[warn] Failed to launch Chrome: {e}")
        return False


def _ensure_cdp_browser(
    cdp_url: str,
    *,
    auto_launch: bool,
    wait_timeout: int = 45,
    start_url: str | None = None,
) -> bool:
    if _is_cdp_reachable(cdp_url):
        return True
    if not auto_launch:
        return False

    if not _launch_chrome_debugging(cdp_url, start_url=start_url):
        return False

    deadline = time.time() + wait_timeout
    while time.time() < deadline:
        if _is_cdp_reachable(cdp_url):
            print(f"[info] Chrome CDP endpoint is ready at {cdp_url}.")
            return True
        time.sleep(1)

    print(f"[warn] Timed out waiting for Chrome CDP at {cdp_url}.")
    return False


def _load_cookies_from_env() -> dict[str, str]:
    raw = os.environ.get(COOKIES_ENV_VAR, "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[warn] {COOKIES_ENV_VAR} is not valid JSON: {e}")
        return {}
    if isinstance(data, dict) and "cookies" in data:
        cookies = data.get("cookies") or {}
    elif isinstance(data, dict):
        cookies = data
    elif isinstance(data, list):
        return _cookies_from_playwright(data)
    else:
        print(f"[warn] {COOKIES_ENV_VAR} has unsupported format.")
        return {}
    if isinstance(cookies, dict):
        return {str(k): str(v) for k, v in cookies.items()}
    return {}


# Output columns — exactly mirrors the visible table column headers, in order:
#   # | Name | Team | ESPN | Y! | $ | $/G | G | PA | AB | R | H | HR | RBI |
#   SB | CS | BB | SO | AVG | OBP | SLG | OPS | R% | RazzID
DATA_COLS = [
    "#", "Name", "Team", "ESPN", "Y!", "$", "$/G",
    "G", "PA", "AB", "R", "H", "HR", "RBI", "SB", "CS", "BB", "SO",
    "AVG", "OBP", "SLG", "OPS", "R%", "RazzID",
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

def _is_cloudflare_challenge(resp) -> bool:
    if getattr(resp, "headers", None) and resp.headers.get("cf-mitigated") == "challenge":
        return True
    snippet = (getattr(resp, "text", "") or "")[:2000].lower()
    markers = (
        "just a moment",
        "cf-browser-verification",
        "cf_chl",
        "challenge-platform",
        "attention required! | cloudflare",
    )
    return any(m in snippet for m in markers)


def _print_block_diagnostics(resp) -> None:
    """
    Print whatever the response actually contains on a 403 so we can tell
    which WAF is involved and whether it's a TLS-fingerprint check, a JS
    challenge, or a flat IP-level block -- instead of guessing blind.
    """
    print("    --- diagnostic info ---")
    interesting_headers = [
        "server", "cf-ray", "cf-mitigated", "cf-cache-status",
        "x-sucuri-id", "x-sucuri-cache", "x-wf-status", "x-firewall",
        "retry-after", "content-type",
    ]
    found_any = False
    for h in interesting_headers:
        if h in resp.headers:
            print(f"    {h}: {resp.headers[h]}")
            found_any = True
    if not found_any:
        print("    (no recognizable WAF/CDN headers in the response)")
    body_snippet = resp.text[:300].replace("\n", " ").strip()
    print(f"    body starts with: {body_snippet!r}")
    lowered = body_snippet.lower()
    if "just a moment" in lowered or "cf-browser-verification" in lowered or "cf_chl" in lowered:
        print("    -> looks like a Cloudflare JS challenge page (needs a real browser to solve).")
    elif "wordfence" in lowered:
        print("    -> looks like a Wordfence block page (often a temporary IP-based ban).")
    elif "sucuri" in lowered:
        print("    -> looks like a Sucuri WAF block page.")
    elif "access denied" in lowered or "forbidden" in lowered:
        print("    -> generic 'Access Denied' page -- could be IP reputation or a simple rule match.")
    print("    -----------------------")


def _build_headers(user_agent: str | None = None) -> dict:
    ua = user_agent or random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Referer": "https://razzball.com/",
    }


def _load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {"url": DEFAULT_URL, "cdp_url": DEFAULT_CDP_URL}
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {
                "url": data.get("url") or DEFAULT_URL,
                "cdp_url": data.get("cdp_url") or DEFAULT_CDP_URL,
            }
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return {"url": DEFAULT_URL, "cdp_url": DEFAULT_CDP_URL}


def _save_config(url: str, cdp_url: str) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"url": url, "cdp_url": cdp_url}, f, indent=2)


def _load_session() -> tuple[dict[str, str], str | None, str | None]:
    """
    Return (cookies, pinned_user_agent, pinned_impersonate_profile).
    Supports legacy plain cookie dict files for backward compatibility.
    """
    if not os.path.exists(COOKIE_FILE):
        return {}, None, None
    try:
        with open(COOKIE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "cookies" in data:
            cookies = data.get("cookies") or {}
            if isinstance(cookies, dict):
                cookies = {str(k): str(v) for k, v in cookies.items()}
            else:
                cookies = {}
            ua = data.get("user_agent")
            profile = data.get("impersonate")
            return cookies, str(ua) if ua else None, str(profile) if profile else None
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}, None, None
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return {}, None, None


def _save_session(
    cookies: dict[str, str],
    *,
    user_agent: str | None = None,
    impersonate: str | None = None,
) -> None:
    payload = {
        "saved_at": time.time(),
        "user_agent": user_agent,
        "impersonate": impersonate or CFFI_IMPERSONATE_PROFILES[0],
        "cookies": cookies,
    }
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[info] Saved session ({len(cookies)} cookie(s)) -> {COOKIE_FILE}")


def _load_saved_cookies() -> dict[str, str]:
    cookies, _, _ = _load_session()
    return cookies


def _save_cookies(
    cookies: dict[str, str],
    *,
    user_agent: str | None = None,
    impersonate: str | None = None,
) -> None:
    _save_session(cookies, user_agent=user_agent, impersonate=impersonate)


def _cookies_from_playwright(raw_cookies: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for cookie in raw_cookies:
        name = cookie.get("name")
        value = cookie.get("value")
        if name and value is not None:
            out[str(name)] = str(value)
    return out


def _page_has_table(html: str) -> bool:
    return TABLE_SELECTOR.replace("table#", "") in html


def _fetch_via_curl_cffi(
    url: str,
    headers: dict,
    cookies: dict[str, str] | None = None,
    *,
    label: str = "curl_cffi",
    impersonate_first: str | None = None,
) -> tuple[str | None, dict[str, str] | None]:
    """
    Primary HTTP fetch for razzball.com. Impersonates Chrome's TLS/HTTP2
    fingerprint. Handles TLS-only blocks but not JS challenges by itself.
    """
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        print(
            "[hint] curl_cffi is required for live fetches from razzball.com.\n"
            "        Try:  pip install curl_cffi"
        )
        return None, None

    cookie_jar = dict(cookies or {})
    last_resp = None
    profiles = list(CFFI_IMPERSONATE_PROFILES)
    if impersonate_first and impersonate_first in profiles:
        profiles.remove(impersonate_first)
        profiles.insert(0, impersonate_first)
    elif impersonate_first:
        profiles.insert(0, impersonate_first)

    for profile in profiles:
        try:
            session = cffi_requests.Session(impersonate=profile)
            if cookie_jar:
                resp = session.get(url, headers=headers, cookies=cookie_jar, timeout=REQUEST_TIMEOUT)
            else:
                session.get("https://razzball.com/", headers=headers, timeout=REQUEST_TIMEOUT)
                resp = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            last_resp = resp
            if resp.status_code == 200 and _page_has_table(resp.text):
                print(f"[info] {label} succeeded via {profile} (200).")
                merged = {**cookie_jar, **dict(resp.cookies)}
                return resp.text, merged or None
            if resp.status_code == 200:
                print(f"[info] {label} got 200 via {profile} but page looks unexpected.")
                merged = {**cookie_jar, **dict(resp.cookies)}
                return resp.text, merged or None
            if resp.status_code in (403, 503) and _is_cloudflare_challenge(resp):
                print(f"[warn] {label} hit Cloudflare challenge via {profile} (status {resp.status_code}).")
                break
            print(f"[warn] {label} status {resp.status_code} via {profile}.")
        except Exception as e:
            print(f"[warn] {label} error via {profile}: {e}")

    if last_resp is not None and last_resp.status_code in (403, 503):
        _print_block_diagnostics(last_resp)
    return None, None


def _load_cookies_file(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return {str(k): str(v) for k, v in data.items()}
    if isinstance(data, list):
        return _cookies_from_playwright(data)
    raise ValueError(f"Unsupported cookie file format in {path}")


def _html_is_cloudflare_challenge(html: str) -> bool:
    snippet = (html or "")[:2000].lower()
    markers = (
        "just a moment",
        "cf-browser-verification",
        "cf_chl",
        "challenge-platform",
        "attention required! | cloudflare",
        "performing security verification",
        "verify you are human",
    )
    return any(m in snippet for m in markers)


def _cdp_open_tab(cdp_url: str, url: str) -> bool:
    """Open a tab via Chrome's native CDP HTTP API (not Playwright navigation)."""
    from urllib.parse import quote

    endpoint = cdp_url.rstrip("/") + "/json/new?" + quote(url, safe="")
    try:
        from curl_cffi import requests as cffi_requests

        for method in (cffi_requests.put, cffi_requests.get):
            try:
                resp = method(endpoint, timeout=15, impersonate=CFFI_IMPERSONATE_PROFILES[0])
                if resp.status_code == 200:
                    print("[info] Opened stats page in Chrome (native tab, not Playwright).")
                    return True
            except Exception:
                continue
    except ImportError:
        pass

    try:
        import urllib.request

        req = urllib.request.Request(endpoint, method="PUT")
        with urllib.request.urlopen(req, timeout=15):
            print("[info] Opened stats page in Chrome (native tab, not Playwright).")
            return True
    except Exception as e:
        print(f"[warn] Could not open tab via CDP: {e}")
        return False


def _pick_razzball_page(context, url: str):
    page = None
    for candidate in context.pages:
        if "razzball.com" in candidate.url and "mlbhittingstats" in candidate.url:
            page = candidate
            break
    if page is None:
        for candidate in context.pages:
            if "razzball.com" in candidate.url:
                page = candidate
                break
    if page is None and context.pages:
        page = context.pages[-1]
    return page


def _wait_for_user_confirmation(headed: bool, cdp: bool) -> None:
    if cdp:
        print(
            "\n[action] In the Chrome window that opened:\n"
            "  1) Wait for Cloudflare to finish (do NOT refresh the page yourself)\n"
            "  2) If it keeps looping, close that window and run:\n"
            '       python last7_hitting.py --bootstrap --browser-headed --mode full\n'
            "  3) When the stats table is fully visible, return here and press Enter\n"
        )
    elif headed:
        print(
            "\n[action] In the browser window Playwright opened:\n"
            "  1) Complete the Cloudflare check if shown\n"
            "  2) Wait until the stats table loads (not 'Just a moment...')\n"
            "  3) Return here and press Enter\n"
            "\n"
            "Tip: if CAPTCHA keeps looping, use --browser-cdp with your real Chrome instead.\n"
        )
    else:
        return
    try:
        input("Press Enter when the stats table is visible ... ")
    except EOFError:
        pass


def _safe_page_content(page) -> str | None:
    try:
        return page.content()
    except Exception as e:
        print(f"[warn] Lost connection to browser page: {e}")
        return None


def _fetch_via_cdp(
    url: str,
    cdp_url: str,
    *,
    wait_for_user: bool = True,
    auto_timeout: int = AUTO_CDP_TIMEOUT,
    auto_launch_chrome: bool = False,
    readonly: bool = False,
) -> tuple[str | None, dict[str, str] | None, str | None]:
    """
    Attach to the user's already-running Chrome. Cloudflare trusts a normal
    browser session far more than Playwright's isolated automation profile.

    When readonly=True (bootstrap / auto), never navigate via Playwright —
    only read tabs opened natively by Chrome, which avoids Cloudflare loops.

    Returns (html, cookies, user_agent).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[hint] pip install playwright")
        return None, None, None

    if not _ensure_cdp_browser(
        cdp_url,
        auto_launch=auto_launch_chrome,
        start_url=url if auto_launch_chrome else None,
    ):
        print(
            f"[warn] Could not connect to Chrome at {cdp_url}.\n"
            "        Start Chrome manually with:\n"
            "          chrome.exe --remote-debugging-port=9222 "
            f'--user-data-dir="{CDP_PROFILE}"\n'
            "        Or re-run bootstrap without --no-auto-launch-chrome."
        )
        return None, None, None

    print(f"[info] Connecting to Chrome at {cdp_url} ...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            print(
                f"[warn] Could not connect to Chrome at {cdp_url}: {e}\n"
                "        Start Chrome with:  chrome.exe --remote-debugging-port=9222"
            )
            return None, None, None

        if not browser.contexts:
            print("[warn] Connected to Chrome but no browser contexts were found.")
            return None, None, None

        context = browser.contexts[0]
        page = _pick_razzball_page(context, url)

        if page is None and readonly:
            _cdp_open_tab(cdp_url, url)
            time.sleep(2)
            page = _pick_razzball_page(context, url)
        elif page is None:
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
        elif not readonly and page.url != url:
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
        elif readonly and page.url != url and "razzball.com" not in page.url:
            _cdp_open_tab(cdp_url, url)
            time.sleep(2)
            page = _pick_razzball_page(context, url)

        if page is None:
            print("[warn] No browser tab available to read.")
            return None, None, None

        if wait_for_user:
            html = _safe_page_content(page)
            if html is None:
                return None, None, None
            if not _page_has_table(html):
                _wait_for_user_confirmation(headed=False, cdp=True)
            html = _safe_page_content(page)
        else:
            print(
                "[action] Waiting for the stats table in Chrome "
                "(will not reload the page) ..."
            )
            deadline = time.time() + auto_timeout
            html = _safe_page_content(page)
            while html is not None and time.time() < deadline:
                if _page_has_table(html) and not _html_is_cloudflare_challenge(html):
                    break
                time.sleep(2)
                page = _pick_razzball_page(context, url) or page
                html = _safe_page_content(page)

        if html and _page_has_table(html) and not _html_is_cloudflare_challenge(html):
            cookies = _cookies_from_playwright(context.cookies())
            try:
                user_agent = page.evaluate("() => navigator.userAgent")
            except Exception:
                user_agent = None
            print("[info] CDP fetch succeeded; table found.")
            return html, cookies, user_agent

        if wait_for_user:
            print(
                "[warn] Connected to Chrome but the stats table was not found.\n"
                "        Open https://razzball.com/mlbhittingstats-last7days/ in that "
                "Chrome window, pass Cloudflare, then re-run."
            )
        else:
            print(
                "[warn] CDP auto-fetch timed out waiting for the stats table.\n"
                "        Make sure Chrome is running with --remote-debugging-port=9222 "
                "and has a valid Razzball session."
            )
    return None, None, None


def _fetch_via_playwright(
    url: str,
    *,
    headed: bool = False,
    profile_dir: str | None = None,
    wait_for_user: bool = True,
) -> tuple[str | None, dict[str, str] | None, str | None]:
    """
    Use a real Chromium engine to get past Cloudflare's JS challenge. Cookies
    are persisted in the browser profile and exported for curl_cffi reuse.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "[hint] Cloudflare JS challenge detected. Install Playwright:\n"
            "        pip install playwright\n"
            "        playwright install chromium"
        )
        return None, None, None

    profile = profile_dir or BROWSER_PROFILE
    os.makedirs(profile, exist_ok=True)
    print(f"[info] Opening browser ({'headed' if headed else 'headless'}) to pass Cloudflare ...")

    with sync_playwright() as p:
        launch_kwargs = {
            "headless": not headed,
            "args": ["--disable-blink-features=AutomationControlled"],
            "user_agent": random.choice(USER_AGENTS),
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
        }
        for channel in ("chrome", "msedge", None):
            try:
                if channel:
                    context = p.chromium.launch_persistent_context(
                        profile, channel=channel, **launch_kwargs
                    )
                else:
                    context = p.chromium.launch_persistent_context(profile, **launch_kwargs)
                break
            except Exception:
                context = None
        if context is None:
            print("[warn] Could not launch Chromium/Chrome/Edge for Playwright.")
            return None, None, None

        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            if not wait_for_user:
                page.goto(url, wait_until="domcontentloaded", timeout=90000)

            if headed and wait_for_user:
                if page.url != url or not context.pages:
                    page.goto(url, wait_until="domcontentloaded", timeout=90000)
                _wait_for_user_confirmation(headed=True, cdp=False)
                html = page.content()
                if _page_has_table(html):
                    cookies = _cookies_from_playwright(context.cookies())
                    try:
                        user_agent = page.evaluate("() => navigator.userAgent")
                    except Exception:
                        user_agent = None
                    print("[info] Playwright fetch succeeded; table found.")
                    return html, cookies, user_agent
            else:
                deadline = time.time() + (180 if headed else 90)
                while time.time() < deadline:
                    html = page.content()
                    if _page_has_table(html):
                        cookies = _cookies_from_playwright(context.cookies())
                        try:
                            user_agent = page.evaluate("() => navigator.userAgent")
                        except Exception:
                            user_agent = None
                        print("[info] Playwright fetch succeeded; table found.")
                        return html, cookies, user_agent

                    title = page.title().lower()
                    if "attention required" in title and not headed:
                        print("[warn] Cloudflare hard-blocked this IP in headless mode.")
                        break
                    time.sleep(2)

            if headed:
                print(
                    "[hint] Playwright kept hitting Cloudflare CAPTCHA.\n"
                    "        Use your real Chrome instead:\n"
                    "          chrome.exe --remote-debugging-port=9222\n"
                    "          python last7_hitting.py --url \"...\" --browser-cdp http://127.0.0.1:9222"
                )
            elif not headed:
                print(
                    "[hint] Headless browser could not clear Cloudflare. Re-run once with:\n"
                    "        python last7_hitting.py --url \"...\" --mode full --browser-headed"
                )
        finally:
            context.close()

    return None, None, None


def _persist_fetch_result(
    text: str,
    cookies: dict[str, str] | None,
    *,
    user_agent: str | None,
    impersonate: str | None = None,
) -> str:
    if cookies:
        _save_cookies(cookies, user_agent=user_agent, impersonate=impersonate)
    _record_run()
    return text


def fetch(
    url: str,
    diagnose_only: bool = False,
    *,
    auto: bool = False,
    bootstrap: bool = False,
    browser_headed: bool = False,
    no_browser: bool = False,
    browser_cdp: str | None = None,
    cookies_file: str | None = None,
    browser_auto_wait: bool = False,
    auto_launch_chrome: bool = True,
) -> str:
    _enforce_min_interval()
    time.sleep(random.uniform(0.5, 2.0))

    session_cookies, session_ua, session_profile = _load_session()
    env_cookies = _load_cookies_from_env()
    if env_cookies:
        session_cookies.update(env_cookies)
        print(f"[info] Loaded cookie(s) from {COOKIES_ENV_VAR} env var")
    if cookies_file:
        session_cookies.update(_load_cookies_file(cookies_file))
        print(f"[info] Loaded cookie(s) from {cookies_file}")

    user_agent = session_ua or USER_AGENTS[0]
    headers = _build_headers(user_agent)

    if bootstrap:
        cdp_url = browser_cdp or DEFAULT_CDP_URL
        print(
            "[info] Bootstrap mode: pass Cloudflare once; session will be saved for --auto runs.\n"
            "[info] Chrome opens the page natively — do not use --browser-auto-wait for bootstrap."
        )

        text = cookies = detected_ua = None
        if not browser_headed:
            text, cookies, detected_ua = _fetch_via_cdp(
                url,
                cdp_url,
                wait_for_user=True,
                auto_launch_chrome=auto_launch_chrome,
                readonly=True,
            )
        if text is None and not no_browser:
            if not browser_headed:
                print("[info] CDP bootstrap failed; trying Playwright with real Chrome ...")
            text, cookies, detected_ua = _fetch_via_playwright(
                url,
                headed=True,
                wait_for_user=True,
            )
        if text is None:
            raise NeedsBootstrapError(
                "Bootstrap failed. Options:\n"
                "  A) Auto-launch Chrome (default):\n"
                "       python last7_hitting.py --bootstrap --mode full\n"
                "     Complete Cloudflare in the Chrome window that opens.\n"
                "  B) Use your own Chrome:\n"
                "       chrome.exe --remote-debugging-port=9222 "
                f'--user-data-dir="{CDP_PROFILE}"\n'
                "       python last7_hitting.py --bootstrap --browser-cdp http://127.0.0.1:9222"
            )
        _save_config(url, cdp_url)
        return _persist_fetch_result(
            text,
            cookies,
            user_agent=detected_ua or user_agent,
            impersonate=session_profile or CFFI_IMPERSONATE_PROFILES[0],
        )

    if auto:
        skip_cdp = _is_ci()
        if skip_cdp:
            print("[info] Auto mode (CI): skipping CDP; using saved/env cookies only ...")
        else:
            cdp_url = browser_cdp or _load_config()["cdp_url"]
            print(f"[info] Auto mode: trying CDP ({cdp_url}), then saved cookies ...")
            text, cookies, detected_ua = _fetch_via_cdp(
                url,
                cdp_url,
                wait_for_user=False,
                auto_timeout=AUTO_CDP_TIMEOUT,
                auto_launch_chrome=False,
                readonly=True,
            )
            if text is not None:
                return _persist_fetch_result(
                    text,
                    cookies,
                    user_agent=detected_ua or user_agent,
                    impersonate=session_profile or CFFI_IMPERSONATE_PROFILES[0],
                )

        if session_cookies:
            print("[info] Auto mode: CDP unavailable/expired; trying curl_cffi with saved session ...")
            text, cookies = _fetch_via_curl_cffi(
                url,
                headers,
                session_cookies,
                label="curl_cffi (auto)",
                impersonate_first=session_profile,
            )
            if text is not None:
                return _persist_fetch_result(
                    text,
                    cookies,
                    user_agent=user_agent,
                    impersonate=session_profile or CFFI_IMPERSONATE_PROFILES[0],
                )

        raise NeedsBootstrapError(
            "Automated fetch failed (CDP unreachable and saved cookies expired).\n"
            "Re-bootstrap locally, then store cookies for GitHub Actions:\n"
            "  1) python last7_hitting.py --bootstrap --mode full\n"
            f"  2) Add .last7_hitting_cookies.json contents to GitHub secret {COOKIES_ENV_VAR}\n"
            "Then schedule unattended runs with:\n"
            "  python last7_hitting.py --auto --mode full"
        )

    if browser_cdp and not diagnose_only:
        text, cookies, detected_ua = _fetch_via_cdp(
            url,
            browser_cdp,
            wait_for_user=not browser_auto_wait,
            auto_launch_chrome=auto_launch_chrome,
        )
        if text is not None:
            return _persist_fetch_result(
                text,
                cookies,
                user_agent=detected_ua or user_agent,
                impersonate=session_profile or CFFI_IMPERSONATE_PROFILES[0],
            )

    max_attempts = 1 if diagnose_only else MAX_RETRIES

    for attempt in range(1, max_attempts + 1):
        print(f"[info] Fetch attempt {attempt}/{max_attempts} via curl_cffi ...")
        text, cookies = _fetch_via_curl_cffi(
            url,
            headers,
            session_cookies,
            label="curl_cffi",
            impersonate_first=session_profile,
        )
        if text is not None:
            return _persist_fetch_result(
                text,
                cookies,
                user_agent=user_agent,
                impersonate=session_profile or CFFI_IMPERSONATE_PROFILES[0],
            )

        if diagnose_only:
            print("[info] --diagnose-only: stopping after a single attempt.")
            break

        if no_browser:
            continue

        if browser_cdp:
            text, cookies, detected_ua = _fetch_via_cdp(
                url,
                browser_cdp,
                wait_for_user=not browser_auto_wait,
                auto_launch_chrome=auto_launch_chrome,
            )
        else:
            text, cookies, detected_ua = _fetch_via_playwright(
                url,
                headed=browser_headed,
                wait_for_user=not browser_auto_wait,
            )
        if text is not None:
            return _persist_fetch_result(
                text,
                cookies,
                user_agent=detected_ua or user_agent,
                impersonate=session_profile or CFFI_IMPERSONATE_PROFILES[0],
            )

        if cookies:
            session_cookies.update(cookies)
            text, cookies = _fetch_via_curl_cffi(
                url,
                headers,
                session_cookies,
                label="curl_cffi after browser",
                impersonate_first=session_profile,
            )
            if text is not None:
                return _persist_fetch_result(
                    text,
                    cookies,
                    user_agent=user_agent,
                    impersonate=session_profile or CFFI_IMPERSONATE_PROFILES[0],
                )

        if attempt < max_attempts:
            wait = BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 1)
            time.sleep(wait)

    raise RuntimeError(
        f"Failed to fetch {url}. Cloudflare blocked automated access.\n"
        "For repeatable automation, bootstrap once then use --auto:\n"
        "  python last7_hitting.py --bootstrap --browser-cdp http://127.0.0.1:9222\n"
        "  python last7_hitting.py --auto --mode full"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _text(el) -> str:
    return el.get_text(strip=True) if el else ""


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

def parse_last7_hitting_table(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", id="neorazzstatstable")
    if table is None:
        raise ValueError("Could not locate the stats table (id='neorazzstatstable').")

    tbody = table.find("tbody")
    if tbody is None:
        raise ValueError("Table found but no <tbody> present.")

    rows_out = []

    for i, tr in enumerate(tbody.find_all("tr", recursive=False), start=1):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 24:
            continue  # malformed row

        # ------------------------------------------------------------------
        # td[0] — Rank (always empty in raw HTML; assign by row order)
        # ------------------------------------------------------------------
        rank = i

        # ------------------------------------------------------------------
        # td[1] — Name
        # ------------------------------------------------------------------
        name_a = tds[1].find("a")
        name = _text(name_a) if name_a else _text(tds[1])
        player_url = name_a.get("href") if name_a else None

        # ------------------------------------------------------------------
        # td[2] — Team
        # ------------------------------------------------------------------
        team_a = tds[2].find("a")
        team = _text(team_a) if team_a else _text(tds[2])
        team_url = team_a.get("href") if team_a else None

        # ------------------------------------------------------------------
        # td[3-23] — plain text stat columns
        # ------------------------------------------------------------------
        espn   = _text(tds[3])  or None
        yahoo  = _text(tds[4])  or None
        dollar = _text(tds[5])  or None
        dpg    = _text(tds[6])  or None
        g      = _text(tds[7])  or None
        pa     = _text(tds[8])  or None
        ab     = _text(tds[9])  or None
        r      = _text(tds[10]) or None
        h      = _text(tds[11]) or None
        hr     = _text(tds[12]) or None
        rbi    = _text(tds[13]) or None
        sb     = _text(tds[14]) or None
        cs     = _text(tds[15]) or None
        bb     = _text(tds[16]) or None
        so     = _text(tds[17]) or None
        avg    = _text(tds[18]) or None
        obp    = _text(tds[19]) or None
        slg    = _text(tds[20]) or None
        ops    = _text(tds[21]) or None
        rpct   = _text(tds[22]) or None
        razzid = _text(tds[23]) or None

        row = {
            "#":       rank,
            "Name":    name,
            "Team":    team,
            "ESPN":    espn,
            "Y!":      yahoo,
            "$":       dollar,
            "$/G":     dpg,
            "G":       g,
            "PA":      pa,
            "AB":      ab,
            "R":       r,
            "H":       h,
            "HR":      hr,
            "RBI":     rbi,
            "SB":      sb,
            "CS":      cs,
            "BB":      bb,
            "SO":      so,
            "AVG":     avg,
            "OBP":     obp,
            "SLG":     slg,
            "OPS":     ops,
            "R%":      rpct,
            "RazzID":  razzid,
            # Internal metadata (not in output columns but available for filtering)
            "_player_url": player_url,
            "_team_url":   team_url,
        }
        rows_out.append(row)

    return rows_out


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _flatten_for_file(row: dict) -> dict:
    """Pick only DATA_COLS fields; all values are already plain strings/ints or None."""
    return {c: (row.get(c) if row.get(c) is not None else "") for c in DATA_COLS}


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


def write_html(rows: list, path: str, source_base_url: str | None = None):
    """
    Emit a plain HTML table with column headers matching the source page exactly.
    Unlike the prediction-table scrapers, there's no team-sprite/bar-chart HTML
    to preserve here -- every cell is plain text (or a player/team link), so a
    simple text-cell render is sufficient.
    """
    header_html = "".join(
        f"<th style='padding:6px 10px;background:#962e2e;color:#fff;white-space:nowrap;'>{c}</th>"
        for c in DATA_COLS
    )
    rows_html = []
    for r in rows:
        cells = "".join(
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;'>{r.get(c) if r.get(c) is not None else ''}</td>"
            for c in DATA_COLS
        )
        rows_html.append(f"<tr>{cells}</tr>")

    base_tag = f'<base href="{source_base_url}">' if source_base_url else ""
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{base_tag}
<style>
  body {{ font-family: Arial, sans-serif; font-size: 13px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ text-align: left; }}
  tr:nth-child(even) {{ background: #f0f0f0; }}
  tr:hover {{ background: #ffffcc; }}
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
        description="Scrape the Razzball Last 7 Day Hitting Stats table."
    )
    src = parser.add_mutually_exclusive_group(required=False)
    src.add_argument("--url", help="Live URL to fetch.")
    src.add_argument("--html", help="Path to a locally saved HTML file (no network call).")
    src.add_argument(
        "--auto", action="store_true",
        help="Unattended scheduled fetch. Tries CDP Chrome first, then saved cookies. "
             "Use after a successful --bootstrap run.",
    )
    src.add_argument(
        "--bootstrap", action="store_true",
        help="One-time setup: pass Cloudflare in real Chrome, save session cookies "
             "for later --auto runs. Auto-launches Chrome with CDP if needed.",
    )

    parser.add_argument(
        "--mode", choices=["test", "full"], default="test",
        help="'test' = first 5 rows; 'full' = all rows.",
    )
    parser.add_argument("--out",    default=None, help="Output file path.")
    parser.add_argument("--format", choices=["csv", "json", "html"], default="csv")
    parser.add_argument(
        "--source-url", default=None,
        help="Original page URL; added as <base href> in HTML output.",
    )
    parser.add_argument(
        "--diagnose-only", action="store_true",
        help="Make a single curl_cffi request (no retries, no browser fallback), "
             "print full diagnostic info on any Cloudflare block, and stop.",
    )
    parser.add_argument(
        "--browser-headed", action="store_true",
        help="Open a Playwright browser window. You complete Cloudflare, then press "
             "Enter in the terminal. Prefer --browser-cdp if CAPTCHA loops.",
    )
    parser.add_argument(
        "--browser-cdp",
        default=None,
        help="Connect to your real Chrome via remote debugging, e.g. "
             "http://127.0.0.1:9222. Start Chrome with: "
             "chrome.exe --remote-debugging-port=9222",
    )
    parser.add_argument(
        "--cookies-file",
        default=None,
        help="JSON file with cookies (dict or list). Export cf_clearance from "
             "Chrome DevTools -> Application -> Cookies -> razzball.com.",
    )
    parser.add_argument(
        "--browser-auto-wait", action="store_true",
        help="With --browser-headed, poll automatically instead of waiting for Enter.",
    )
    parser.add_argument(
        "--no-auto-launch-chrome", action="store_true",
        help="Do not auto-launch Chrome when --browser-cdp is unreachable. "
             "Use if you prefer to start Chrome manually.",
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="Do not use Playwright even if Cloudflare returns a JS challenge.",
    )
    args = parser.parse_args()

    if not any((args.html, args.url, args.auto, args.bootstrap)):
        parser.error("one of --html, --url, --auto, or --bootstrap is required")

    config = _load_config()
    live_url = args.url or config["url"]

    try:
        if args.html:
            print(f"[info] Reading local file: {args.html}")
            with open(args.html, encoding="utf-8", errors="ignore") as f:
                html = f.read()
            source_url = args.source_url or args.url
        else:
            print(f"[info] Fetching {live_url} ...")
            html = fetch(
                live_url,
                diagnose_only=args.diagnose_only,
                auto=args.auto,
                bootstrap=args.bootstrap,
                browser_headed=args.browser_headed,
                no_browser=args.no_browser,
                browser_cdp=args.browser_cdp,
                cookies_file=args.cookies_file,
                browser_auto_wait=args.browser_auto_wait,
                auto_launch_chrome=not args.no_auto_launch_chrome,
            )
            source_url = args.source_url or live_url

        print("[info] Parsing table ...")
        rows = parse_last7_hitting_table(html)
        print(f"[info] Parsed {len(rows)} total data rows.")

        if args.mode == "test":
            rows = rows[:5]
            print("[info] TEST MODE: truncated to first 5 rows.")

        if not args.out:
            suffix = "test" if args.mode == "test" else "full"
            ext = {"csv": "csv", "json": "json", "html": "html"}[args.format]
            args.out = f"last7_hitting_{suffix}.{ext}"

        if args.format == "csv":
            write_csv(rows, args.out)
        elif args.format == "json":
            write_json(rows, args.out)
        else:
            write_html(rows, args.out, source_base_url=source_url)

        for r in rows[:3]:
            print({c: r.get(c) for c in DATA_COLS})

    except NeedsBootstrapError as e:
        print(f"[bootstrap-required] {e}")
        sys.exit(EXIT_NEEDS_BOOTSTRAP)
    except Exception:
        raise

    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()