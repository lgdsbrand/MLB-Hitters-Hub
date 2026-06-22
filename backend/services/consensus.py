"""
Consensus scoring engine for MLB Hitters Hub.
Generates a 0-100 consensus score by combining multiple data signals:
  - Hit prediction rank
  - Last 7 day performance rank
  - Hit probability (Pred column)
  - Batter vs Pitcher matchup rank
"""

import pandas as pd
from typing import Optional
from .data_service import load_csv, filter_by_game, _clean_pred_value, parse_trend, _safe_val


def _normalize_name(name: str) -> str:
    """Normalize batter name for matching across CSVs."""
    if not name or pd.isna(name):
        return ""
    # Remove position info like ', SS (L)' or 'D' suffixes
    s = str(name).strip()
    # Remove trailing D (IL markers etc)
    parts = s.split(",")
    return parts[0].strip().rstrip("D").strip()


def _generate_reasoning(hit_score: float, l7_score: float, bvp_score: float, trend_score: float, consensus: float) -> str:
    """Generate AI reasoning text explaining the consensus score."""
    reasons = []
    
    # Analyze hit prediction probability
    if hit_score >= 70:
        reasons.append("Strong historical hit prediction signal")
    elif hit_score >= 50:
        reasons.append("Moderate hit prediction likelihood")
    else:
        reasons.append("Emerging hit prediction opportunity")
    
    # Analyze last 7 day performance
    if l7_score >= 70:
        reasons.append("Excellent recent form and OPS")
    elif l7_score >= 50:
        reasons.append("Solid recent performance trend")
    else:
        reasons.append("Building momentum from recent games")
    
    # Analyze BvP matchup
    if bvp_score >= 70:
        reasons.append("Favorable matchup history vs pitcher")
    elif bvp_score >= 50:
        reasons.append("Neutral to favorable pitcher matchup")
    else:
        reasons.append("Challenging pitcher matchup")
    
    # Analyze trend consistency
    if trend_score >= 70:
        reasons.append("Strong hitting consistency in trend")
    elif trend_score >= 50:
        reasons.append("Decent hit streak emerging")
    else:
        reasons.append("Early stage of potential streak")
    
    return " • ".join(reasons)


def calculate_consensus_scores(game: Optional[str] = None) -> list:
    """
    Calculate consensus scores for all hitters.
    Score is 0-100, combining:
      - Hit prediction probability (40% weight)
      - Last 7 day OPS ranking (25% weight)
      - BvP matchup quality (20% weight)
      - 5-game trend consistency (15% weight)
    """
    # Load data sources
    hit_df = load_csv("hit_pred")
    last7_df = load_csv("last7")
    bvp_df = load_csv("bvp")

    if hit_df.empty:
        return []

    hit_df = filter_by_game(hit_df, game)

    # 1) Hit prediction scores (Pred column)
    hit_scores = {}
    for _, row in hit_df.iterrows():
        batter = row.get("Batter", "")
        pred = _clean_pred_value(row.get("Pred", 0))
        hit_scores[batter] = pred

    # 2) Last 7 day OPS rankings
    last7_ops = {}
    if not last7_df.empty and "OPS" in last7_df.columns:
        last7_df["OPS_float"] = pd.to_numeric(last7_df["OPS"], errors="coerce").fillna(0)
        max_ops = last7_df["OPS_float"].max() if last7_df["OPS_float"].max() > 0 else 1.0
        name_col = "Name" if "Name" in last7_df.columns else last7_df.columns[1]
        for _, row in last7_df.iterrows():
            name = _normalize_name(row.get(name_col, ""))
            ops = row.get("OPS_float", 0)
            last7_ops[name] = (ops / max_ops) * 100 if max_ops > 0 else 0

    # 3) BvP matchup quality
    bvp_scores = {}
    if not bvp_df.empty:
        bvp_filtered = bvp_df[bvp_df["Batter"] != "---"].copy() if "Batter" in bvp_df.columns else bvp_df.copy()
        if game:
            bvp_filtered = filter_by_game(bvp_filtered, game)
        for _, row in bvp_filtered.iterrows():
            batter = row.get("Batter", "")
            ops_val = row.get("OPS", 0)
            try:
                ops_float = float(ops_val) if not pd.isna(ops_val) else 0
            except (ValueError, TypeError):
                ops_float = 0
            ba_val = row.get("BA", 0)
            try:
                ba_float = float(ba_val) if not pd.isna(ba_val) else 0
            except (ValueError, TypeError):
                ba_float = 0
            # BvP score: weighted combo of OPS and BA against this pitcher
            bvp_scores[batter] = min((ops_float * 40 + ba_float * 60), 100)

    # 4) Trend consistency score
    trend_scores = {}
    for _, row in hit_df.iterrows():
        batter = row.get("Batter", "")
        trend = parse_trend(row.get("Trend", ""))
        if len(trend) == 5:
            hits_in_trend = sum(1 for t in trend if t > 0)
            avg_hits = sum(trend) / 5
            trend_scores[batter] = min((hits_in_trend / 5) * 60 + min(avg_hits, 3) / 3 * 40, 100)
        else:
            trend_scores[batter] = 0

    # Combine scores
    results = []
    for _, row in hit_df.iterrows():
        batter = row.get("Batter", "")
        norm_name = _normalize_name(batter)

        hit_score = hit_scores.get(batter, 0)
        l7_score = last7_ops.get(norm_name, 0)
        bvp_score = bvp_scores.get(batter, 0)
        trend_score = trend_scores.get(batter, 0)

        # Weighted consensus (0-100)
        consensus = (
            hit_score * 0.40 +
            l7_score * 0.25 +
            bvp_score * 0.20 +
            trend_score * 0.15
        )
        consensus = min(round(consensus, 0), 100)

        # Hit probability as string
        pred_str = str(row.get("Pred", "")).strip()
        
        # Generate AI reasoning
        reasoning = _generate_reasoning(hit_score, l7_score, bvp_score, trend_score, consensus)

        results.append({
            "Batter": _safe_val(batter),
            "Pitcher": _safe_val(row.get("Pitcher", "")),
            "Game": _safe_val(row.get("Game", "")),
            "Consensus": int(consensus),
            "HitProb": _safe_val(pred_str),
            "Trend": _safe_val(row.get("Trend", "")),
            "AB": _safe_val(row.get("AB", "")),
            "H": _safe_val(row.get("H", "")),
            "BA": _safe_val(row.get("BA", "")),
            "OPS": _safe_val(row.get("OPS", "")),
            "AIReasoning": reasoning,
        })

    # Sort by consensus descending
    results.sort(key=lambda x: x["Consensus"], reverse=True)
    return results
