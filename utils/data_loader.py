"""
CSV wrappers with freshness checks.
Every load function shows a warning banner if data is stale (>24h) or missing.
"""

import os
import pandas as pd
import streamlit as st
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STALE_HOURS = 24


def _csv_path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


def _hours_since(ts_str: str) -> float:
    """Return hours elapsed since an ISO-format timestamp string."""
    try:
        ts = datetime.fromisoformat(ts_str)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - ts).total_seconds() / 3600
    except Exception:
        return float("inf")


def load_metadata() -> dict:
    """
    Load pull_metadata.csv. Returns a dict with keys:
      pull_timestamp, season, data_through, games_fetched, players_fetched,
      pbp_games_success, pbp_games_failed, source_versions
    Returns None if file is missing.
    """
    path = _csv_path("pull_metadata.csv")
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        return df.iloc[-1].to_dict()
    except Exception:
        return None


def check_freshness():
    """
    Call at the top of every page. Shows warning/error banners.
    Returns hours_old (float) or None if metadata missing.
    """
    meta = load_metadata()
    if meta is None:
        st.markdown(
            '<div class="err-banner">⚠️ <strong>No data found.</strong> '
            'Run <code>python data_pull.py</code> to populate the data layer.</div>',
            unsafe_allow_html=True,
        )
        return None

    hours_old = _hours_since(str(meta.get("pull_timestamp", "")))
    if hours_old > STALE_HOURS:
        h = int(hours_old)
        st.markdown(
            f'<div class="warn-banner">🕐 Data is <strong>{h} hours old</strong>. '
            f'Run <code>python data_pull.py</code> to refresh.</div>',
            unsafe_allow_html=True,
        )
    return hours_old


def freshness_label(hours_old: float | None) -> str:
    """Return a human-readable freshness string for the sidebar."""
    if hours_old is None:
        return "No data"
    if hours_old < 1:
        return "< 1 hour ago"
    h = int(hours_old)
    return f"{h} hour{'s' if h != 1 else ''} ago"


def load_csv(filename: str, required_cols: list[str] | None = None) -> pd.DataFrame | None:
    """
    Generic CSV loader. Returns DataFrame or None with an error banner.
    """
    path = _csv_path(filename)
    if not os.path.exists(path):
        st.markdown(
            f'<div class="err-banner">❌ Missing file: <code>data/{filename}</code>. '
            f'Run <code>python data_pull.py</code> to generate it.</div>',
            unsafe_allow_html=True,
        )
        return None
    try:
        df = pd.read_csv(path)
        if required_cols:
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                st.markdown(
                    f'<div class="err-banner">❌ <code>data/{filename}</code> is missing columns: '
                    f'{", ".join(missing)}. Re-run <code>python data_pull.py</code>.</div>',
                    unsafe_allow_html=True,
                )
                return None
        return df
    except Exception as e:
        st.markdown(
            f'<div class="err-banner">❌ Could not read <code>data/{filename}</code>: {e}</div>',
            unsafe_allow_html=True,
        )
        return None


def load_triple_double_games() -> pd.DataFrame | None:
    return load_csv(
        "triple_double_games.csv",
        required_cols=["game_id", "player_id", "player_name", "game_date",
                       "opponent_team", "pts", "ast", "reb"],
    )


def load_assist_sequences() -> pd.DataFrame | None:
    return load_csv(
        "assist_sequences.csv",
        required_cols=["game_id", "player_id", "player_name", "period",
                       "time_remaining", "assisted_player", "shot_type",
                       "shot_value", "points_scored"],
    )


def load_player_season_stats() -> pd.DataFrame | None:
    return load_csv(
        "player_season_stats.csv",
        required_cols=["player_id", "player_name", "team",
                       "pts_per_game", "ast_per_game", "reb_per_game"],
    )


def load_leaderboard() -> pd.DataFrame | None:
    return load_csv(
        "leaderboard.csv",
        required_cols=["rank", "game_id", "player_id", "player_name",
                       "game_date", "opponent_team", "pts", "ast", "reb",
                       "points_via_assists", "total_points_touched"],
    )
