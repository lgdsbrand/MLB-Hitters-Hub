# MLB Hitters Hub — Full Feature Implementation Plan

Build a production-ready MLB Hitters Hub module: a dark-themed sports betting analytics dashboard with a FastAPI backend and Next.js frontend.

## Design Philosophy

The design follows **im4.png** (Bobby's Analytics dark dashboard):
- **Dark navy/charcoal background** (`#0d1117`, `#161b22`)
- **Teal/emerald accent** (`#00d97e`, `#10b981`) for positive indicators
- **White/light gray text** on dark cards
- **Rounded cards with subtle borders** (`border: 1px solid rgba(255,255,255,0.06)`)
- **Fire emoji (🔥)** for hit probability indicators
- **Glassmorphism card panels** with slight transparency
- Team logos displayed via ESPN CDN or similar public API

The page layout follows **im5.png** (the rough sketch):
- "Powered By" header
- Game selector dropdown + Bet Sheet button
- "Best Plays of the Day" hero section (top 3 consensus picks)
- Tab bar: Last 7 Days Hot Hitters | Hit Predictions | HR Predictions | TB Predictions | BvP Matchup
- Data table for selected tab
- "About Consensus Score" info panel

Per **im2.png** (Bet Sheet instructions):
- Every player/prop row has a **green ➕ button**
- Clicking adds to a **Bet Sheet** side panel
- Bet Sheet displays as a table view
- Clears at midnight each day (client-side `localStorage` date check)

---

## Proposed Changes

### Backend (FastAPI + Python)

#### [NEW] [main.py](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/backend/main.py)
FastAPI application entry point with CORS middleware and route imports.

#### [NEW] [routers/hitters.py](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/backend/routers/hitters.py)
Six API endpoints:
| Endpoint | Source CSV | Description |
|---|---|---|
| `GET /api/hitters/hits` | `hit_pred_full.csv` | Hit projections (excl. HRF & Trend columns) |
| `GET /api/hitters/hr` | `hr_pred_full.csv` | HR projections (excl. HRF & Trend columns) |
| `GET /api/hitters/tb` | `tb_pred_full.csv` | Total base projections (excl. HRF & Trend columns) |
| `GET /api/hitters/bvp` | `bvp_full.csv` | Batter vs Pitcher data (excl. HRF) |
| `GET /api/hitters/last7` | `last7_hitting_full.csv` | Last 7 day hot hitters |
| `GET /api/hitters/games` | Aggregated from hit/hr/tb CSVs | Unique game list |

All endpoints accept optional `?game=ANA @ ATH` query param for filtering (except `/last7` and `/games`).

#### [NEW] [services/data_service.py](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/backend/services/data_service.py)
Reusable pandas services:
- `load_csv(filename)` — reads CSV with error handling
- `parse_trend(trend_str)` → `list[int]` — parses `"1,3,1,1,1"` strings
- `get_unique_games()` → `list[str]`
- `get_100_club_hits()` — filters players where all 5 trend values beat O/U line
- `get_100_club_tb()` — filters players where all 5 trend values beat TB Line
- `get_5day_streak()` — filters players where all 5 trend values > 0 (hit_pred only)
- `get_best_plays()` — generates consensus scores from multiple data sources

#### [NEW] [services/consensus.py](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/backend/services/consensus.py)
Consensus scoring engine (0-100 scale):
- Combines hit prediction rank, last-7-days performance rank, hit probability (Pred column), and BvP matchup rank
- Returns top players sorted by consensus score

#### [NEW] [requirements.txt](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/backend/requirements.txt)
```
fastapi
uvicorn[standard]
pandas
```

---

### Frontend (Next.js + Tailwind CSS)

#### [NEW] [package.json](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/package.json)
Next.js project with dependencies: `next`, `react`, `react-dom`, `recharts`, `tailwindcss`.

#### [NEW] [app/page.tsx](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/app/page.tsx)
Main Hitters Hub page:
- Game selector dropdown (fetches from `/api/hitters/games`)
- Bet Sheet toggle button (top-right)
- "Best Plays of the Day" hero — top 3 consensus picks with score badges & fire indicators
- Tab navigation bar for 5 data views
- Active tab content (data table)
- "About Consensus Score" explainer panel

#### [NEW] [components/GameSelector.tsx](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/components/GameSelector.tsx)
Dropdown with team logos. Parses game strings (e.g. `ANA @ ATH`) and displays team logos via ESPN CDN (`https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/{abbr}.png`). Team abbreviation mapping included for CSV abbreviations → ESPN IDs.

#### [NEW] [components/BestPlays.tsx](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/components/BestPlays.tsx)
Hero section showing top 3 players with:
- Rank badge (1, 2, 3)
- Player name, position, team
- Consensus score (0-100) in a green badge
- Hit probability with fire emoji indicators

#### [NEW] [components/DataTable.tsx](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/components/DataTable.tsx)
Reusable table component for all 5 data views:
- Sortable columns
- Green ➕ button on each row to add to bet sheet
- Responsive horizontal scroll on mobile
- Columns vary per tab (no HRF or Trend columns per instructions)

#### [NEW] [components/ClubSection.tsx](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/components/ClubSection.tsx)
Shared component for:
- **100% Club** — two sub-tabs: Hits / Total Bases (no HRR)
- **5-Day Hit Streak Club** — players with all 5 trend values > 0

#### [NEW] [components/BetSheet.tsx](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/components/BetSheet.tsx)
Slide-out side panel:
- Table view of selected players
- Remove individual selection (✕ button)
- "Clear All" button
- Midnight auto-reset via `localStorage` date check
- localStorage schema: `{ date: "YYYY-MM-DD", selections: [...] }`

#### [NEW] [components/TabBar.tsx](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/components/TabBar.tsx)
Horizontal tab bar with 5 tabs:
1. Last 7 Days Hot Hitters
2. Hit Predictions
3. HR Predictions
4. TB Predictions
5. BvP Matchup

Styled with rounded pill buttons matching im5.png's green active state.

#### [NEW] [hooks/useBetSheet.ts](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/hooks/useBetSheet.ts)
Custom React hook:
- Manages bet sheet state with `localStorage`
- `addPlayer(player)`, `removePlayer(id)`, `clearAll()`
- Auto-clears when date changes (midnight reset)

#### [NEW] [hooks/useHittersData.ts](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/hooks/useHittersData.ts)
Data fetching hook:
- Fetches from all 6 API endpoints
- Manages loading/error states
- Filters data by selected game
- Caches responses

#### [NEW] [lib/teamLogos.ts](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/lib/teamLogos.ts)
Team abbreviation → logo URL mapping. Maps CSV abbreviations (ANA, ATH, CHA, CHN, LAN, NYA, NYN, SDN, SFN, TBA, WAS) to standard MLB team codes for ESPN CDN.

#### [NEW] [tailwind.config.ts](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/frontend/tailwind.config.ts)
Dark theme color palette matching im4.png:
```
colors: {
  bg: { primary: '#0d1117', secondary: '#161b22', card: '#1c2333' },
  accent: { green: '#00d97e', teal: '#10b981' },
  text: { primary: '#e6edf3', secondary: '#8b949e' },
  border: { subtle: 'rgba(255,255,255,0.06)' }
}
```

---

### Documentation

#### [MODIFY] [README.md](file:///c:/Users/PC/Desktop/MLB-Hitters-Hub-main/README.md)
Comprehensive README with:
- Project structure overview
- Local development setup (backend + frontend)
- FastAPI startup instructions (`uvicorn backend.main:app --reload`)
- Next.js startup instructions (`npm run dev`)
- CSV data directory setup
- Vercel deployment guide
- Troubleshooting section

---

## Open Questions

> [!IMPORTANT]
> **CSV file naming**: The current CSVs are named `*_full.csv` (e.g. `hit_pred_full.csv`). The PDF spec references `hit_pred.csv` etc. I'll code the backend to look for both `_full` and non-`_full` variants, preferring the `_full` versions that exist now. Does this work for your pipeline?

> [!IMPORTANT]
> **"Powered By" branding**: The im5.png sketch shows "POWERED BY" at the top. What should the branding text say — your company/site name, or should I leave it as a placeholder?

> [!NOTE]
> **Team logos**: I'll use ESPN CDN logos which are publicly available. The CSV uses non-standard abbreviations (e.g. `ATH` for Athletics, `CHN` for Cubs, `LAN` for Dodgers). I'll create a mapping table for all of these.

---

## Verification Plan

### Automated Tests
- `python -m pytest backend/tests/` — unit tests for data service and consensus scoring
- `npm run build` — verify Next.js build succeeds without errors

### Manual Verification
- Start FastAPI backend → verify all 6 endpoints return valid JSON
- Start Next.js frontend → verify dark theme renders correctly
- Test game selector filtering
- Test bet sheet: add, remove, clear, midnight reset
- Test 100% Club and 5-Day Streak calculations
- Verify mobile responsiveness
- Verify no HRF or Trend columns appear in frontend tables
