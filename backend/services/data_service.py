"""
Data service for loading, parsing, and processing MLB hitter CSV data.
Provides reusable pandas-based utilities for all hitter endpoints.
"""

import os
import glob
import pandas as pd
from typing import Optional
from functools import lru_cache

# Base directory for CSV files (now inside backend so Vercel includes them)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)

# CSV file mapping — prefer *_full.csv, fall back to base name
CSV_FILES = {
    "hit_pred": ["hit_pred_full.csv", "hit_pred.csv"],
    "hr_pred": ["hr_pred_full.csv", "hr_pred.csv"],
    "tb_pred": ["tb_pred_full.csv", "tb_pred.csv"],
    "bvp": ["bvp_full.csv", "bvp.csv"],
    "last7": ["last7_hitting_full.csv", "last7hitting.csv", "last7_hitting.csv"],
    "hit_streaks": ["hit_streaks_all_*.csv"],  # Will match hit_streaks_all_YYYY-MM-DD.csv
}


def _find_csv_path(key: str) -> Optional[str]:
    """Find the first existing CSV file for a given key. Supports glob patterns."""
    candidates = CSV_FILES.get(key, [])
    for filename in candidates:
        # Check backend directory first (where files will be on Vercel)
        if "*" in filename:
            matches = glob.glob(os.path.join(BACKEND_DIR, filename))
            if matches:
                return sorted(matches)[-1]  # Return latest if multiple matches
            matches = glob.glob(os.path.join(ROOT_DIR, filename))
            if matches:
                return sorted(matches)[-1]
        else:
            path = os.path.join(BACKEND_DIR, filename)
            if os.path.exists(path):
                return path
            # Fallback to project root for local backward compatibility
            path = os.path.join(ROOT_DIR, filename)
            if os.path.exists(path):
                return path
    return None


def load_csv(key: str) -> pd.DataFrame:
    """
    Load a CSV file by key name.
    Returns empty DataFrame if file not found.
    """
    path = _find_csv_path(key)
    if path is None:
        print(f"Warning: No CSV found for key '{key}'")
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, encoding="utf-8")
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"Error loading CSV '{path}': {e}")
        return pd.DataFrame()


def parse_trend(trend_str: str) -> list:
    """
    Parse a trend string like '1,3,1,1,1' into a list of integers.
    Returns empty list on parse failure.
    """
    if not trend_str or pd.isna(trend_str):
        return []
    try:
        cleaned = str(trend_str).strip().strip('"')
        parts = [int(x.strip()) for x in cleaned.split(",") if x.strip()]
        return parts
    except (ValueError, AttributeError):
        return []


def _safe_val(val):
    """Return val as a JSON-safe value. NaN/inf become empty string."""
    if val is None:
        return ""
    try:
        if pd.isna(val):
            return ""
    except (ValueError, TypeError):
        pass
    return val


def get_unique_games() -> list:
    """
    Aggregate unique game strings from hit_pred, hr_pred, and tb_pred CSVs.
    Returns sorted list of unique games.
    """
    games = set()
    for key in ["hit_pred", "hr_pred", "tb_pred"]:
        df = load_csv(key)
        if "Game" in df.columns:
            game_values = df["Game"].dropna().unique()
            games.update(game_values)
    return sorted(list(games))


def filter_by_game(df: pd.DataFrame, game: Optional[str]) -> pd.DataFrame:
    """Filter a DataFrame by game if game is specified."""
    if game and "Game" in df.columns:
        return df[df["Game"] == game].copy()
    return df


def _clean_pred_value(val) -> float:
    """Clean prediction percentage strings like '80%' or '72%3.5' to float."""
    if pd.isna(val):
        return 0.0
    s = str(val).strip().rstrip("%")
    # Handle cases like '72%3.5' — take the first number
    try:
        return float(s)
    except ValueError:
        # Try to extract just the numeric part before any extra chars
        import re
        match = re.match(r"(\d+\.?\d*)", s)
        if match:
            return float(match.group(1))
        return 0.0


def get_hit_predictions(game: Optional[str] = None) -> list:
    """Get hit predictions, optionally filtered by game."""
    df = load_csv("hit_pred")
    if df.empty:
        return []
    df = filter_by_game(df, game)

    # Remove HRF and Trend columns per spec
    drop_cols = [c for c in ["HRF", "Trend"] if c in df.columns]
    df = df.drop(columns=drop_cols)

    # Clean Pred column
    if "Pred" in df.columns:
        df["Pred_Value"] = df["Pred"].apply(_clean_pred_value)
        df = df.sort_values("Pred_Value", ascending=False)
        df = df.drop(columns=["Pred_Value"])

    return df.fillna("").to_dict(orient="records")


def get_hr_predictions(game: Optional[str] = None) -> list:
    """Get HR predictions, optionally filtered by game."""
    df = load_csv("hr_pred")
    if df.empty:
        return []
    df = filter_by_game(df, game)

    drop_cols = [c for c in ["HRF", "Trend"] if c in df.columns]
    df = df.drop(columns=drop_cols)

    if "HR Pred" in df.columns:
        df["Pred_Value"] = df["HR Pred"].apply(_clean_pred_value)
        df = df.sort_values("Pred_Value", ascending=False)
        df = df.drop(columns=["Pred_Value"])

    return df.fillna("").to_dict(orient="records")


def get_tb_predictions(game: Optional[str] = None) -> list:
    """Get total base predictions, optionally filtered by game."""
    df = load_csv("tb_pred")
    if df.empty:
        return []
    df = filter_by_game(df, game)

    drop_cols = [c for c in ["HRF", "Trend"] if c in df.columns]
    df = df.drop(columns=drop_cols)

    if "TB Pred" in df.columns:
        df["Pred_Value"] = df["TB Pred"].apply(lambda x: float(x) if not pd.isna(x) else 0.0)
        df = df.sort_values("Pred_Value", ascending=False)
        df = df.drop(columns=["Pred_Value"])

    return df.fillna("").to_dict(orient="records")


def get_bvp_data(game: Optional[str] = None) -> list:
    """Get batter vs pitcher data, optionally filtered by game."""
    df = load_csv("bvp")
    if df.empty:
        return []
    df = filter_by_game(df, game)

    # Remove HRF column per spec
    drop_cols = [c for c in ["HRF"] if c in df.columns]
    df = df.drop(columns=drop_cols)

    # Filter out separator rows (e.g., rows where Batter is '---')
    if "Batter" in df.columns:
        df = df[df["Batter"] != "---"]

    return df.fillna("").to_dict(orient="records")


def get_last7_hitters() -> list:
    """Get last 7 day hot hitters, sorted by AVG descending."""
    df = load_csv("last7")
    if df.empty:
        return []

    # Remove columns not needed per spec (HRF, Trend don't exist here)
    # Keep the key stats columns
    if "AVG" in df.columns:
        df["AVG_float"] = pd.to_numeric(df["AVG"], errors="coerce").fillna(0)
        df = df.sort_values("AVG_float", ascending=False)
        df = df.drop(columns=["AVG_float"])

    return df.fillna("").to_dict(orient="records")


def get_100_club_hits(game: Optional[str] = None) -> list:
    """
    100% Club for Hits.
    Player qualifies if ALL five trend games beat the O/U line.
    """
    df = load_csv("hit_pred")
    if df.empty:
        return []
    df = filter_by_game(df, game)

    qualifying = []
    for _, row in df.iterrows():
        trend = parse_trend(row.get("Trend", ""))
        ou_val = row.get("O/U", None)

        if len(trend) != 5 or pd.isna(ou_val):
            continue

        try:
            line = float(ou_val)
        except (ValueError, TypeError):
            continue

        # Check if all 5 games beat the prop line
        if all(t > line for t in trend):
            qualifying.append({
                "Batter": _safe_val(row.get("Batter", "")),
                "Pitcher": _safe_val(row.get("Pitcher", "")),
                "Game": _safe_val(row.get("Game", "")),
                "Pred": _safe_val(row.get("Pred", "")),
                "O/U": _safe_val(ou_val),
                "Trend": _safe_val(row.get("Trend", "")),
                "Record": "5/5",
                "AB": _safe_val(row.get("AB", "")),
                "H": _safe_val(row.get("H", "")),
                "BA": _safe_val(row.get("BA", "")),
                "OBP": _safe_val(row.get("OBP", "")),
                "OPS": _safe_val(row.get("OPS", "")),
            })

    return qualifying


def get_100_club_tb(game: Optional[str] = None) -> list:
    """
    100% Club for Total Bases.
    Player qualifies if ALL five trend games exceed the Line.
    """
    df = load_csv("tb_pred")
    if df.empty:
        return []
    df = filter_by_game(df, game)

    qualifying = []
    for _, row in df.iterrows():
        trend = parse_trend(row.get("Trend", ""))
        line_val = row.get("Line", None)

        if len(trend) != 5 or pd.isna(line_val):
            continue

        try:
            line = float(line_val)
        except (ValueError, TypeError):
            continue

        # Check if all 5 games exceed the line
        if all(t > line for t in trend):
            qualifying.append({
                "Batter": _safe_val(row.get("Batter", "")),
                "Pitcher": _safe_val(row.get("Pitcher", "")),
                "Game": _safe_val(row.get("Game", "")),
                "TB Pred": _safe_val(row.get("TB Pred", "")),
                "Line": _safe_val(line_val),
                "Trend": _safe_val(row.get("Trend", "")),
                "Record": "5/5",
                "AB": _safe_val(row.get("AB", "")),
                "H": _safe_val(row.get("H", "")),
                "BA": _safe_val(row.get("BA", "")),
                "OBP": _safe_val(row.get("OBP", "")),
                "OPS": _safe_val(row.get("OPS", "")),
            })

    return qualifying


def get_5day_hit_streak(game: Optional[str] = None) -> list:
    """
    5-Day Hit Streak Club.
    Uses hit_pred.csv only. Player qualifies if all 5 trend values > 0.
    """
    df = load_csv("hit_pred")
    if df.empty:
        return []
    df = filter_by_game(df, game)

    qualifying = []
    for _, row in df.iterrows():
        trend = parse_trend(row.get("Trend", ""))

        if len(trend) != 5:
            continue

        # All 5 games must have at least one hit
        if all(x > 0 for x in trend):
            qualifying.append({
                "Batter": _safe_val(row.get("Batter", "")),
                "Pitcher": _safe_val(row.get("Pitcher", "")),
                "Game": _safe_val(row.get("Game", "")),
                "Pred": _safe_val(row.get("Pred", "")),
                "Trend": _safe_val(row.get("Trend", "")),
                "Streak": "5/5",
                "AB": _safe_val(row.get("AB", "")),
                "H": _safe_val(row.get("H", "")),
                "BA": _safe_val(row.get("BA", "")),
                "OBP": _safe_val(row.get("OBP", "")),
                "OPS": _safe_val(row.get("OPS", "")),
            })

    return qualifying


def get_hit_streaks() -> list:
    """Get all active hit streaks from hit_streaks_all CSV."""
    df = load_csv("hit_streaks")
    if df.empty:
        return []
    
    # Normalize column names to lowercase for matching
    df.columns = df.columns.str.lower()
    
    # Select relevant columns for display
    relevant_cols = ["player", "team", "hit_streak", "games", "avg", "hits", "home_runs", "rbi", "runs", "ops"]
    available_cols = [col for col in relevant_cols if col in df.columns]
    
    if not available_cols:
        return []
    
    df = df[available_cols]
    
    # Rename columns to display-friendly names
    col_mapping = {
        "player": "Player",
        "team": "Team",
        "hit_streak": "Streak",
        "games": "Games",
        "avg": "AVG",
        "hits": "Hits",
        "home_runs": "HR",
        "rbi": "RBI",
        "runs": "Runs",
        "ops": "OPS",
    }
    
    df = df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns})
    
    # Sort by streak (descending)
    if "Streak" in df.columns:
        df["Streak_num"] = pd.to_numeric(df["Streak"], errors="coerce").fillna(0)
        df = df.sort_values("Streak_num", ascending=False)
        df = df.drop(columns=["Streak_num"])
    
    return df.fillna("").to_dict(orient="records")
