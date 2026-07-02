# MLB Hitters Hub — Analytics Dashboard

A production-ready sports betting analytics platform module for MLB hitters, featuring a dark-themed dashboard with hit/HR/TB projections, batter-vs-pitcher (BvP) data, 100% Club, and a local bet sheet.

## Architecture

- **Backend**: FastAPI (Python), Pandas for data processing. Serves data directly from daily CSV files.
- **Frontend**: Next.js (React), Tailwind CSS. Uses a custom proxy to communicate with the FastAPI backend.
- **Data Source**: Local CSV files (`hit_pred_full.csv`, `hr_pred_full.csv`, `tb_pred_full.csv`, `bvp_full.csv`, `last7_hitting_full.csv`).

## Project Structure

```
MLB-Hitters-Hub-main/
├── backend/                  # FastAPI Application
│   ├── main.py               # Entry point & CORS setup
│   ├── routers/              # API Route definitions
│   └── services/             # Pandas data processing logic
├── frontend/                 # Next.js Application
│   ├── app/                  # Pages & Layout
│   ├── components/           # Reusable UI components
│   ├── hooks/                # Custom React hooks (BetSheet, Data)
│   └── lib/                  # API client & Utilities
├── *.csv                     # Source data files
└── README.md
```

## Local Development Setup

### 1. Backend Setup

The backend requires Python 3.10+ and uses `pandas` for processing the CSV files.

```bash
# Navigate to the project root (where the CSV files are)
cd MLB-Hitters-Hub-main

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. You can view the interactive API documentation at `http://localhost:8000/docs`.

### 2. Frontend Setup

The frontend uses Next.js and expects the backend to be running on port 8000. It proxies `/api/*` requests to the backend.

```bash
# Navigate to the frontend directory
cd MLB-Hitters-Hub-main/frontend

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```

The application will be available at `http://localhost:3000`.

## Features

- **Game Selector**: Filter all data views by specific games.
- **Best Plays**: Consensus scoring engine combining hit probability, BvP quality, and recent performance.
- **100% Club & Streaks**: Automatically identifies players beating their prop lines consistently.
- **Bet Sheet**: Client-side storage (localStorage) for saving picks. Automatically resets at midnight.
- **Dark Theme**: Premium aesthetic with glassmorphism cards and fire emoji indicators.

## Deployment Guide (Vercel)

Deploying a monorepo with both a Next.js frontend and a FastAPI backend to Vercel requires specific configurations. Follow these steps carefully:

### Step 1: Create a `vercel.json` file
Vercel needs to know how to build both the Next.js app and the Python API. Create a new file named `vercel.json` in the **root** of your project with the following content:

```json
{
  "builds": [
    { "src": "frontend/package.json", "use": "@vercel/next" },
    { "src": "backend/main.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "backend/main.py" },
    { "src": "/(.*)", "dest": "frontend/$1" }
  ]
}
```

### Step 2: Push your code to GitHub
Make sure your code is committed and pushed to a GitHub repository. (See the git commands provided to you for help).
*Note: Ensure your CSV files are tracked in Git so Vercel can access the data at runtime.*

### Step 3: Deploy on Vercel
1. Go to your [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New** -> **Project**.
2. Select the GitHub repository you just pushed to and click **Import**.
3. **Important Configuration:**
   - Leave the **Root Directory** as the default (`./`), do NOT set it to `frontend/`. Vercel will use the `vercel.json` file to route things correctly.
4. Click **Deploy**. Vercel will automatically build the Next.js app using `frontend/package.json` and deploy the FastAPI endpoints from `backend/main.py`.

## Troubleshooting

- **No data appearing**: Check if the CSV files are named correctly (`*_full.csv` or standard `.csv`) and are located in the project root (one level above `backend`).
- **CORS Errors**: Ensure the backend `main.py` has your frontend domain listed in `allow_origins`.
- **Team Logos missing**: The app uses ESPN CDN logos mapped via `lib/teamLogos.ts`. If a team's abbreviation in the CSV doesn't match standard MLB codes, add it to the `TEAM_MAP` in that file.