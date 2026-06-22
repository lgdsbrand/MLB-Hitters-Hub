"""
MLB Active Hit Streaks Scraper — breakawaystats.com

Two modes (set MODE below, or pass --today / --all on the command line):
  Option A — "all"   : All active streak players (~144 players).
                        No todayOnly param in the URL.
  Option B — "today" : Only players who have a game today (~20 players).
                        Adds &todayOnly=true to the URL.

URL: https://breakawaystats.com/mlb/streaks?playerType=hitter&sortBy=hit_streak
     &viewMode=streaks&streakFilter=hitStreak&lens=streak%3AhitStreak[&todayOnly=true]

Findings from debug_rendered.html analysis:
  - Players render as cards inside a CSS grid: div.grid.gap-4.lg:gap-6
  - Each card has a badge with title="<Player> has had a hit in N consecutive games"
  - Stats appear as alternating value|label pairs after the nav tabs
  - Page initially renders ~20 cards. Loading the rest requires clicking the
    "Load More Players" button repeatedly — it is NOT pure infinite scroll.
    The button sits in a div.mt-8.text-center below the grid and is text-matched.

Outputs:
  - data/hit_streaks_YYYY-MM-DD.json   (full structured data)
  - data/hit_streaks_latest.json        (always overwritten)
  - hit_streaks_YYYY-MM-DD.csv          (root folder)

Install:  pip install playwright beautifulsoup4
          playwright install chromium
"""

import json
import csv
import re
import sys
import time
import random
import logging
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ── Config ─────────────────────────────────────────────────────────────────
# MODE = "all"   -> Option A: every active hit-streak player (~144)
# MODE = "today" -> Option B: only players with a game today (~20)
MODE = "all"   # change to "today" for Option B

BASE_URL = (
    "https://breakawaystats.com/mlb/streaks"
    "?playerType=hitter"
    "&sortBy=hit_streak"
    "&viewMode=streaks"
    "&streakFilter=hitStreak"
    "&lens=streak%3AhitStreak"
)

# Allow overriding MODE from the command line: `python streak.py today` / `python streak.py all`
if len(sys.argv) > 1 and sys.argv[1].lower() in ("all", "today"):
    MODE = sys.argv[1].lower()

URL = BASE_URL + ("&todayOnly=true" if MODE == "today" else "")

OUTPUT_DIR = Path(".")  # write alongside the other scrapers' output, not a separate subfolder
TODAY      = date.today().isoformat()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# Stat labels that appear AFTER their value in the card text
STAT_LABELS = {
    "GP", "AB", "AVG", "H", "HR", "RBI", "R",
    "OPS", "SB", "OBP", "SLG", "BB", "2B", "3B", "K",
    "Hit Str", "HR Str", "RBI Str",
}

# Nav tab tokens that appear between player name and stats — used as boundary
NAV_TOKENS = {"Streaks", "BTS", "Models", "HR Due", "L10", "Last 10",
              "Statcast", "Lineup", "Props", "Splits", "Milestone"}


# ── Helpers ────────────────────────────────────────────────────────────────
def to_int(v: str) -> int | None:
    v = str(v).strip().replace(",", "")
    return int(v) if re.match(r"^\d+$", v) else None

def to_float(v: str) -> float | None:
    v = str(v).strip()
    # Handle both ".372" and "0.372"
    if re.match(r"^\.\d+$", v):
        v = "0" + v
    try:
        return round(float(v), 3)
    except ValueError:
        return None


# ── Card parser ────────────────────────────────────────────────────────────
def parse_card(card_soup, rank: int) -> dict | None:
    """
    Parse one player card.
    Card text (pipe-separated) looks like:
      Hit Streak|12|SS • #11 •|NYY|Anthony|Volpe|Streaks|BTS|...|
      27|GP|86|AB|.267|AVG|23|H|1|HR|13|RBI|...|Hit Str|0|HR Str|0|RBI Str|
      Schedule|Playercard|Compare
    """
    # ── Player name + streak from badge title ─────────────────────────────
    badge = card_soup.find(attrs={"title": re.compile(r"has had a hit in \d+ consecutive", re.I)})
    if not badge:
        return None

    title = badge.get("title", "")
    m = re.search(r"(.+?) has had a hit in (\d+) consecutive", title, re.I)
    if not m:
        return None

    player     = m.group(1).strip()
    hit_streak = int(m.group(2))

    # ── Split card text into parts ────────────────────────────────────────
    parts = [p.strip() for p in card_soup.get_text(separator="|", strip=True).split("|") if p.strip()]

    # ── Team: first 2-4 uppercase-only token ─────────────────────────────
    team = ""
    for p in parts:
        if re.match(r"^[A-Z]{2,4}$", p):
            team = p
            break

    # ── Stats: scan for value|LABEL pairs after nav tabs ─────────────────
    # Find where the nav tabs end (last NAV_TOKEN before numeric stats)
    nav_end = 0
    for i, p in enumerate(parts):
        if p in NAV_TOKENS:
            nav_end = i

    stat_parts = parts[nav_end + 1:]  # everything after nav tabs

    # Walk pairs: value then label
    stats: dict[str, str] = {}
    i = 0
    while i < len(stat_parts) - 1:
        val   = stat_parts[i]
        label = stat_parts[i + 1]
        if label in STAT_LABELS:
            stats[label] = val
            i += 2
        else:
            i += 1

    # ── Build row ─────────────────────────────────────────────────────────
    return {
        "rank":         rank,
        "player":       player,
        "team":         team,
        "hit_streak":   hit_streak,
        "games":        to_int(stats.get("GP", "")),
        "at_bats":      to_int(stats.get("AB", "")),
        "avg":          to_float(stats.get("AVG", "")),
        "hits":         to_int(stats.get("H", "")),
        "home_runs":    to_int(stats.get("HR", "")),
        "rbi":          to_int(stats.get("RBI", "")),
        "runs":         to_int(stats.get("R", "")),
        "ops":          to_float(stats.get("OPS", "")),
        "sb":           to_int(stats.get("SB", "")),
        "obp":          to_float(stats.get("OBP", "")),
        "slg":          to_float(stats.get("SLG", "")),
        "bb":           to_int(stats.get("BB", "")),
        "doubles":      to_int(stats.get("2B", "")),
        "triples":      to_int(stats.get("3B", "")),
        "strikeouts":   to_int(stats.get("K", "")),
        "hit_str":      to_int(stats.get("Hit Str", "")),
        "hr_str":       to_int(stats.get("HR Str", "")),
        "rbi_str":      to_int(stats.get("RBI Str", "")),
        "scraped_date": TODAY,
    }


def parse_html(html: str) -> list[dict]:
    """Parse all player cards from rendered HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # The grid container: div with classes including 'grid' and 'gap-4'
    grid = soup.find("div", class_=lambda c: c and "grid" in c and "gap-4" in c)
    if not grid:
        log.error("Grid container not found in HTML.")
        return []

    card_wrappers = grid.find_all("div", recursive=False)
    log.info(f"Card wrappers in grid: {len(card_wrappers)}")

    rows = []
    for i, wrapper in enumerate(card_wrappers, 1):
        row = parse_card(wrapper, i)
        if row:
            rows.append(row)

    return rows


# ── Playwright: load page + scroll until all cards visible ─────────────────
def scrape() -> list[dict]:
    mode_desc = "all active streaks" if MODE == "all" else "today's games only"
    log.info(f"Mode: {MODE.upper()}  ({mode_desc})")
    log.info("Launching Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )

        # The site sits behind Vercel's bot-protection challenge
        # (/.well-known/vercel/security/...). On a shared/datacenter IP like
        # a GitHub Actions runner, that challenge can come back as a 429 (or
        # simply abort) before the page ever renders a single card. A single
        # attempt with no retry turns what is often a transient block into a
        # hard failure for the whole run, so we retry a few times with
        # backoff and a brand-new browser context (fresh cookies/fingerprint)
        # before giving up and writing debug artifacts.
        MAX_NAV_ATTEMPTS = 3
        NAV_RETRY_BACKOFF = [45, 120]  # seconds to wait before attempt 2 / 3
        page = None
        target_total = None

        for nav_attempt in range(1, MAX_NAV_ATTEMPTS + 1):
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass

            ctx = browser.new_context(
                viewport={"width": 1600, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                timezone_id="America/New_York",
            )
            ctx.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins',   { get: () => [1, 2, 3] });
            """)

            page = ctx.new_page()
            blocked = {"hit": False}  # set when we see a 429 / aborted challenge

            def _on_console(msg, _blocked=blocked):
                if msg.type == "error":
                    log.warning(f"  [browser console:{msg.type}] {msg.text}")
                    if "429" in msg.text:
                        _blocked["hit"] = True

            def _on_request_failed(req, _blocked=blocked):
                log.warning(f"  [request failed] {req.url} — {req.failure}")
                if "request-challenge" in req.url or "vercel/security" in req.url:
                    _blocked["hit"] = True

            page.on("console", _on_console)
            page.on("requestfailed", _on_request_failed)

            # Log XHR/fetch calls (skip static assets/analytics) so we can see
            # what API the "Load More" button actually calls — useful if UI
            # clicking ever proves unreliable and we need to call the API directly.
            def log_api_request(req):
                if req.resource_type in ("xhr", "fetch") and "breakawaystats.com" in req.url:
                    log.info(f"  [api request] {req.method} {req.url}")

            def log_api_response(resp, _blocked=blocked):
                if resp.request.resource_type in ("xhr", "fetch") and "breakawaystats.com" in resp.url:
                    log.info(f"  [api response] {resp.status} {resp.url}")
                if resp.status == 429:
                    _blocked["hit"] = True

            page.on("request", log_api_request)
            page.on("response", log_api_response)

            # A short, randomized pause before navigating instead of firing
            # the request the instant the browser is up.
            time.sleep(random.uniform(1.5, 4.0))

            # ── Navigate ──────────────────────────────────────────────────
            log.info(f"Loading {URL} (attempt {nav_attempt}/{MAX_NAV_ATTEMPTS})...")
            try:
                resp = page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
                if resp is not None and resp.status == 429:
                    blocked["hit"] = True
            except PWTimeout:
                log.error("Navigation timed out.")
                if nav_attempt < MAX_NAV_ATTEMPTS:
                    delay = NAV_RETRY_BACKOFF[nav_attempt - 1]
                    log.warning(f"Retrying in {delay}s with a fresh session...")
                    time.sleep(delay)
                    continue
                browser.close()
                return []

            # ── Wait for first cards to appear ────────────────────────────
            log.info("Waiting for player cards to render...")
            CARD_SELECTOR = "div.grid [title*='consecutive']"
            try:
                page.wait_for_selector(CARD_SELECTOR, timeout=30_000, state="visible")
                log.info("First cards visible.")
            except PWTimeout:
                log.warning("Cards not found via badge title — waiting 10s...")
                time.sleep(10)

            # Next.js apps render the SSR shell first, then hydrate client-side —
            # the "Load More Players" button doesn't exist in the DOM until
            # hydration finishes. Give it a moment to settle before looking for it.
            time.sleep(2.0)

            initial_count = page.evaluate(
                "() => document.querySelectorAll(\"[title*='consecutive']\").length"
            )
            if initial_count > 0:
                break  # real content rendered — proceed with this session

            blocked_reason = (
                "blocked by rate-limiting/bot-challenge (HTTP 429 or an aborted "
                "challenge request)" if blocked["hit"] else
                "no cards rendered (slow hydration or a layout change)"
            )
            log.warning(f"No player cards loaded — {blocked_reason}.")

            if nav_attempt < MAX_NAV_ATTEMPTS:
                delay = NAV_RETRY_BACKOFF[nav_attempt - 1]
                log.warning(
                    f"Backing off {delay}s and retrying with a brand-new browser "
                    f"session (attempt {nav_attempt + 1}/{MAX_NAV_ATTEMPTS})..."
                )
                time.sleep(delay)
                continue
            else:
                log.error(f"All {MAX_NAV_ATTEMPTS} attempts failed ({blocked_reason}).")
                try:
                    page.screenshot(path="debug_load_more_failure.png", full_page=True)
                    Path("debug_load_more_failure.html").write_text(page.content(), encoding="utf-8")
                    log.warning("Saved debug_load_more_failure.png / .html")
                except Exception as e:
                    log.warning(f"Could not save debug artifacts: {e}")
                browser.close()
                return []

        # ── Read the page's own "N players" total, if present ──────────────
        # e.g. "144 players • Updated daily for 2026 season"
        try:
            page_text = page.evaluate("() => document.body.innerText")
            m = re.search(r"([\d,]+)\s+players\b", page_text, re.I)
            if m:
                target_total = int(m.group(1).replace(",", ""))
                log.info(f"Page reports a target total of {target_total} players.")
        except Exception as e:
            log.warning(f"Could not read target player count: {e}")

        # ── Click "Load More Players" until all cards are loaded ──────────
        # The site only does pure infinite scroll for the first ~20 cards;
        # the rest require repeatedly clicking the "Load More Players" button.
        log.info("Clicking 'Load More Players' until all players are loaded...")

        LOAD_MORE_SELECTOR = "button:has-text('Load More Players')"
        prev_count = 0
        stable_rounds = 0
        consecutive_click_failures = 0
        max_clicks = 80
        max_click_failures = 5   # tolerate transient timeouts before giving up
        clean_finish = False   # True if the site's own pagination ran out, not a stuck button

        def find_load_more():
            """Retry-with-backoff check for the Load More button, since it
            can briefly vanish/re-render after each click while React re-renders."""
            loc = page.locator(LOAD_MORE_SELECTOR)
            for attempt in range(4):
                try:
                    if loc.count() > 0 and loc.first.is_visible():
                        return loc
                except Exception:
                    pass
                time.sleep(0.5 * (attempt + 1))
            return None

        def current_count():
            return page.evaluate(
                "() => document.querySelectorAll(\"[title*='consecutive']\").length"
            )

        for click_step in range(max_clicks):
            count = current_count()

            if count != prev_count:
                log.info(f"  After {click_step} click(s): {count} cards loaded")
                stable_rounds = 0
                prev_count = count
            else:
                stable_rounds += 1

            # Reached (or passed) the page's own reported total → done.
            if target_total is not None and count >= target_total:
                log.info(f"Reached target of {target_total} players ({count} loaded).")
                break

            # No new cards for several rounds in a row → stop instead of
            # spinning all the way to max_clicks. This used to only trigger
            # once we were within 95% of target_total, so a button that got
            # stuck early (e.g. permanently overlapped by a sticky banner)
            # would loop pointlessly for the rest of the run.
            if stable_rounds >= 5:
                if target_total is not None and count >= target_total * 0.95:
                    log.info(f"Card count stable at {count} (near target) — stopping.")
                else:
                    log.warning(
                        f"No new cards after {stable_rounds} attempts (stuck at "
                        f"{count}" + (f"/{target_total}" if target_total else "") +
                        ") — stopping early instead of spinning to max_clicks. "
                        "Saving debug artifacts for inspection."
                    )
                break

            load_more = find_load_more()
            if load_more is None:
                # No more button present after retries. If the last click
                # round actually added new cards (stable_rounds == 0), this
                # is the site's own pagination telling us it's exhausted —
                # not a glitch. The page header's "N players" text can be
                # stale/inaccurate and not match what this specific filtered
                # endpoint actually serves, so don't treat count < target
                # as suspicious by itself.
                if target_total is not None and count < target_total and stable_rounds > 0:
                    log.warning(
                        f"'Load More Players' button gone at {count}/{target_total} "
                        "while card count was already stalled — may be a transient "
                        "render issue, not necessarily done."
                    )
                elif target_total is not None and count < target_total:
                    log.info(
                        f"'Load More Players' button gone — {count} cards loaded. "
                        f"(Page header says {target_total}, but that figure can be "
                        "stale/inaccurate for this filter; the site itself stopped "
                        "serving new pages, so this is likely the true total.)"
                    )
                else:
                    log.info(f"'Load More Players' button gone — {count} cards total.")
                break

            # Diagnostics: is the button disabled / what does its state look like?
            try:
                btn_state = load_more.first.evaluate(
                    "el => ({disabled: el.disabled, text: el.textContent.trim(), "
                    "ariaDisabled: el.getAttribute('aria-disabled'), "
                    "classes: el.className})"
                )
                if btn_state.get("disabled") or btn_state.get("ariaDisabled") == "true":
                    log.info("  Button is disabled (likely loading) — waiting before click...")
                    time.sleep(2.0)
            except Exception as e:
                log.warning(f"  Could not inspect button state: {e}")

            try:
                load_more.first.scroll_into_view_if_needed(timeout=8_000)
                time.sleep(0.3)

                pre_click_count = count

                # Dispatch a native DOM click directly on the element via JS.
                # This fires the button's own onClick handler immediately and
                # is immune to sticky banners/overlays — those only intercept
                # *simulated mouse* clicks (which Playwright's normal click,
                # and even force=True click, perform at real screen
                # coordinates). A real promo banner sitting on top of the
                # button was swallowing those clicks, which is why the count
                # stopped increasing even though "force click" reported no
                # error.
                load_more.first.evaluate("el => el.click()")

                # Poll for new cards instead of a fixed sleep, so we don't
                # wait longer than necessary or move on too early.
                clicked_ok = False
                for _ in range(10):
                    time.sleep(0.5)
                    if current_count() > pre_click_count:
                        clicked_ok = True
                        break

                if not clicked_ok:
                    # JS click didn't move the count — fall back to a real
                    # Playwright click in case the handler needs a trusted
                    # event, then give it one more moment to render.
                    log.info("  JS click had no effect — trying a forced Playwright click...")
                    try:
                        load_more.first.click(timeout=4_000, force=True)
                    except Exception:
                        pass
                    time.sleep(1.5)

                consecutive_click_failures = 0
            except PWTimeout:
                consecutive_click_failures += 1
                log.warning(
                    f"Timed out clicking 'Load More Players' "
                    f"(failure {consecutive_click_failures}/{max_click_failures}) — retrying..."
                )
                time.sleep(2.0)
                if consecutive_click_failures >= max_click_failures:
                    log.warning("Too many consecutive click timeouts — stopping.")
                    break
                continue
            except Exception as e:
                consecutive_click_failures += 1
                log.warning(
                    f"Could not click 'Load More Players' ({e}) "
                    f"(failure {consecutive_click_failures}/{max_click_failures}) — retrying..."
                )
                time.sleep(2.0)
                if consecutive_click_failures >= max_click_failures:
                    log.warning("Too many consecutive click failures — stopping.")
                    break
                continue

        # Final count
        total = current_count()
        log.info(f"Total cards in DOM: {total}")

        if target_total is not None and total < target_total:
            log.warning(
                f"Only scraped {total}/{target_total} players. "
                "Site may have throttled loading or layout changed — "
                "saving debug screenshot + HTML for inspection."
            )
            try:
                page.screenshot(path="debug_load_more_failure.png", full_page=True)
                Path("debug_load_more_failure.html").write_text(page.content(), encoding="utf-8")
                log.warning("Saved debug_load_more_failure.png / .html")
            except Exception as e:
                log.warning(f"Could not save debug artifacts: {e}")
        elif MODE == "all" and total <= 21:
            log.warning(
                f"Only {total} cards loaded in ALL mode and no target total was found. "
                "Saving a debug screenshot + HTML dump for inspection."
            )
            try:
                page.screenshot(path="debug_load_more_failure.png", full_page=True)
                Path("debug_load_more_failure.html").write_text(page.content(), encoding="utf-8")
                log.warning("Saved debug_load_more_failure.png / .html")
            except Exception as e:
                log.warning(f"Could not save debug artifacts: {e}")

        # ── Grab rendered HTML and parse ──────────────────────────────────
        html = page.content()
        browser.close()

    return parse_html(html)


# ── Save ───────────────────────────────────────────────────────────────────
def save(rows: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / f"hit_streaks_{MODE}_{TODAY}.json"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    log.info(f"Saved → {json_path}")

    latest = OUTPUT_DIR / f"hit_streaks_{MODE}_latest.json"
    latest.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    log.info(f"Saved → {latest}")

    if rows:
        csv_path = Path(f"hit_streaks_{MODE}_{TODAY}.csv")
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        log.info(f"Saved → {csv_path}")

    log.info(f"✓ Total players scraped: {len(rows)}")


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rows = scrape()
    if not rows:
        log.error("No data scraped.")
        sys.exit(1)
    save(rows)
    print(f"\n── Preview (top 10 of {len(rows)}) ──────────────────────────────")
    for r in rows[:10]:
        print(
            f"  #{r['rank']:>3}  {r['player']:<24}  {r['team']:<4}"
            f"  Streak:{r['hit_streak']:>3}G"
            f"  AVG:{str(r.get('avg') or ''):>6}"
            f"  H:{str(r.get('hits') or ''):>4}"
            f"  GP:{str(r.get('games') or ''):>4}"
        )