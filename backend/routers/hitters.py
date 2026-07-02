"""
FastAPI router for all MLB Hitters Hub endpoints.
"""

from fastapi import APIRouter, Query
from typing import Optional
from services.data_service import (
    get_unique_games,
    get_hit_predictions,
    get_hr_predictions,
    get_tb_predictions,
    get_bvp_data,
    get_last7_hitters,
    get_last15_hitters,
    get_100_club_hits,
    get_100_club_tb,
    get_5day_hit_streak,
    get_hit_streaks,
)
from services.consensus import calculate_consensus_scores

router = APIRouter(prefix="/api/hitters", tags=["hitters"])


@router.get("/games")
def list_games():
    """Return all unique games from prediction CSVs."""
    games = get_unique_games()
    return {"games": games}


@router.get("/hits")
def hits(game: Optional[str] = Query(None, description="Filter by game (e.g. 'ANA @ ATH')")):
    """Return hit projections, optionally filtered by game."""
    data = get_hit_predictions(game)
    return {"data": data, "count": len(data)}


@router.get("/hr")
def hr(game: Optional[str] = Query(None, description="Filter by game")):
    """Return HR projections, optionally filtered by game."""
    data = get_hr_predictions(game)
    return {"data": data, "count": len(data)}


@router.get("/tb")
def tb(game: Optional[str] = Query(None, description="Filter by game")):
    """Return total base projections, optionally filtered by game."""
    data = get_tb_predictions(game)
    return {"data": data, "count": len(data)}


@router.get("/bvp")
def bvp(game: Optional[str] = Query(None, description="Filter by game")):
    """Return batter vs pitcher data, optionally filtered by game."""
    data = get_bvp_data(game)
    return {"data": data, "count": len(data)}


@router.get("/last7")
def last7():
    """Return last 7 day hot hitters."""
    data = get_last7_hitters()
    return {"data": data, "count": len(data)}


@router.get("/last15")
def last15():
    """Return last 15 day hot hitters."""
    data = get_last15_hitters()
    return {"data": data, "count": len(data)}


@router.get("/consensus")
def consensus(game: Optional[str] = Query(None, description="Filter by game")):
    """Return consensus-scored best plays of the day."""
    data = calculate_consensus_scores(game)
    return {"data": data, "count": len(data)}


@router.get("/club/hits")
def club_hits(game: Optional[str] = Query(None, description="Filter by game")):
    """Return 100% Club for hits (players who beat their prop in all 5 games)."""
    data = get_100_club_hits(game)
    return {"data": data, "count": len(data)}


@router.get("/club/tb")
def club_tb(game: Optional[str] = Query(None, description="Filter by game")):
    """Return 100% Club for total bases."""
    data = get_100_club_tb(game)
    return {"data": data, "count": len(data)}


@router.get("/streak")
def streak(game: Optional[str] = Query(None, description="Filter by game")):
    """Return 5-Day Hit Streak Club."""
    data = get_5day_hit_streak(game)
    return {"data": data, "count": len(data)}


@router.get("/hit-streaks")
def hit_streaks():
    """Return all active hit streaks."""
    data = get_hit_streaks()
    return {"data": data, "count": len(data)}
