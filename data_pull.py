"""
data_pull.py — Triple Double Receipt data pipeline.
Run locally to pre-populate /data before deploying to Streamlit Community Cloud.

Usage:
  python data_pull.py                          # full pull
  python data_pull.py --game-id 0022401234     # refresh single game
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
LOG_FILE = DATA_DIR / "pull_errors.log"
SEASON = "2024-25"
SEASON_ID = "22024"  # nba_api season string format

# ── Logging ───────────────────────────────────────────────────────────────────
DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE),
    ],
)
log = logging.getLogger(__name__)


# ── Rate-limit helpers ────────────────────────────────────────────────────────

def nba_api_call(fn, *args, max_retries: int = 3, base_delay: float = 1.0, **kwargs):
    """
    Call an nba_api endpoint with exponential backoff.
    Raises RuntimeError after max_retries failures.
    """
    for attempt in range(1, max_retries + 1):
        try:
            time.sleep(0.6)  # be a good citizen — NBA API rate limits aggressively
            return fn(*args, **kwargs)
        except Exception as e:
            wait = base_delay * (2 ** (attempt - 1))
            log.warning(f"Attempt {attempt}/{max_retries} failed: {e}. Retrying in {wait:.1f}s")
            if attempt == max_retries:
                raise
            time.sleep(wait)


def log_error(context: str, error: Exception):
    with open(LOG_FILE, "a") as f:
        ts = datetime.now(timezone.utc).isoformat()
        f.write(f"{ts}  ERROR  [{context}]  {type(error).__name__}: {error}\n")
    log.error(f"[{context}] {error}")


# ── Step 1: Triple-double game logs ──────────────────────────────────────────

def fetch_triple_double_games() -> pd.DataFrame:
    """
    Pull every player's 2024-25 game log from nba_api.
    Filter rows where PTS >= 10 AND AST >= 10 AND REB >= 10.
    Write data/triple_double_games.csv.
    Returns the DataFrame.
    """
    log.info("=" * 60)
    log.info("STEP 1: Fetching triple-double game logs …")

    from nba_api.stats.endpoints import LeagueGameLog
    from nba_api.stats.static import players as nba_players

    records: list[dict] = []
    games_fetched = 0

    try:
        log.info(f"  Pulling full league game log for {SEASON} …")
        game_log = nba_api_call(
            LeagueGameLog,
            season=SEASON,
            season_type_all_star="Regular Season",
            player_or_team_abbreviation="P",
            timeout=60,
        )
        df_all = game_log.get_data_frames()[0]
        games_fetched = len(df_all)
        log.info(f"  Retrieved {games_fetched:,} player-game rows.")

        # Normalise column names (nba_api returns uppercase)
        col_map = {
            "GAME_ID": "game_id",
            "PLAYER_ID": "player_id",
            "PLAYER_NAME": "player_name",
            "GAME_DATE": "game_date",
            "MATCHUP": "matchup",
            "WL": "team_result",
            "PTS": "pts",
            "AST": "ast",
            "REB": "reb",
            "STL": "stl",
            "BLK": "blk",
            "TOV": "tov",
            "MIN": "minutes_played",
        }
        df_all.rename(columns={k: v for k, v in col_map.items() if k in df_all.columns}, inplace=True)

        # Triple-double filter
        td_mask = (df_all["pts"] >= 10) & (df_all["ast"] >= 10) & (df_all["reb"] >= 10)
        df_td = df_all[td_mask].copy()
        log.info(f"  Found {len(df_td)} triple-double games.")

        # Parse opponent and home/away from MATCHUP (e.g. "LAL vs. GSW" or "LAL @ GSW")
        def parse_matchup(matchup: str, player_team: str = "") -> tuple[str, str]:
            if " vs. " in matchup:
                parts = matchup.split(" vs. ")
                return parts[1].strip(), "Home"
            elif " @ " in matchup:
                parts = matchup.split(" @ ")
                return parts[1].strip(), "Away"
            return matchup, "Unknown"

        df_td["season"] = SEASON
        df_td[["opponent_team", "home_away"]] = pd.DataFrame(
            [parse_matchup(str(m)) for m in df_td.get("matchup", [""] * len(df_td))],
            index=df_td.index,
        )

        out_cols = [
            "game_id", "player_id", "player_name", "game_date", "season",
            "opponent_team", "home_away", "team_result",
            "pts", "ast", "reb", "stl", "blk", "tov", "minutes_played",
        ]
        df_out = df_td[[c for c in out_cols if c in df_td.columns]].copy()

        out_path = DATA_DIR / "triple_double_games.csv"
        df_out.to_csv(out_path, index=False)
        log.info(f"  ✓ Wrote {len(df_out)} rows → {out_path}")
        return df_out

    except Exception as e:
        log_error("fetch_triple_double_games", e)
        # Return empty DataFrame with correct schema so downstream steps don't crash
        return pd.DataFrame(columns=[
            "game_id", "player_id", "player_name", "game_date", "season",
            "opponent_team", "home_away", "team_result",
            "pts", "ast", "reb", "stl", "blk", "tov", "minutes_played",
        ])


# ── Step 2: Assist sequences from play-by-play ───────────────────────────────

def fetch_assist_sequences(df_td: pd.DataFrame) -> pd.DataFrame:
    """
    For each game in df_td, pull play-by-play and extract assist sequences.
    Write data/assist_sequences.csv.
    Returns the DataFrame.
    """
    log.info("=" * 60)
    log.info("STEP 2: Fetching play-by-play assist sequences …")

    if df_td.empty:
        log.warning("  No triple-double games found; skipping PBP step.")
        _write_empty_assist_sequences()
        return pd.DataFrame()

    from utils.pbp_parser import fetch_pbpstats_events, parse_assist_sequences

    all_rows: list[dict] = []
    success_count = 0
    fail_count = 0
    failed_games: list[str] = []

    unique_games = df_td[["game_id", "player_id", "player_name"]].drop_duplicates()
    total = len(unique_games)

    for idx, (_, row) in enumerate(unique_games.iterrows(), 1):
        game_id = str(row["game_id"])
        player_id = str(row["player_id"])
        player_name = str(row["player_name"])

        log.info(f"  [{idx}/{total}] {player_name} — game {game_id}")

        try:
            events = fetch_pbpstats_events(game_id)
            sequences = parse_assist_sequences(events, player_name)

            for seq in sequences:
                seq["game_id"] = game_id
                seq["player_id"] = player_id
                seq["player_name"] = player_name
                all_rows.append(seq)

            log.info(f"    → {len(sequences)} assist sequences parsed.")
            success_count += 1

        except Exception as e:
            log_error(f"PBP game {game_id} ({player_name})", e)
            fail_count += 1
            failed_games.append(game_id)
            # Write a sentinel row so the Receipt page can show "PBP unavailable"
            all_rows.append({
                "game_id": game_id,
                "player_id": player_id,
                "player_name": player_name,
                "period": None,
                "time_remaining": None,
                "assisted_player": None,
                "shot_type": "PBP_UNAVAILABLE",
                "shot_value": 0,
                "points_scored": 0,
                "is_and1": False,
                "free_throw_points": 0,
            })

    df_out = pd.DataFrame(all_rows)
    out_cols = [
        "game_id", "player_id", "player_name", "period", "time_remaining",
        "assisted_player", "shot_type", "shot_value", "points_scored",
        "is_and1", "free_throw_points",
    ]
    if not df_out.empty:
        df_out = df_out[[c for c in out_cols if c in df_out.columns]]

    out_path = DATA_DIR / "assist_sequences.csv"
    df_out.to_csv(out_path, index=False)
    log.info(f"  ✓ Wrote {len(df_out)} rows → {out_path}")
    log.info(f"  PBP: {success_count} success, {fail_count} failed.")
    if failed_games:
        log.warning(f"  Failed game IDs: {failed_games}")

    return df_out, success_count, fail_count


def _write_empty_assist_sequences():
    df = pd.DataFrame(columns=[
        "game_id", "player_id", "player_name", "period", "time_remaining",
        "assisted_player", "shot_type", "shot_value", "points_scored",
        "is_and1", "free_throw_points",
    ])
    df.to_csv(DATA_DIR / "assist_sequences.csv", index=False)


# ── Step 3: Player season stats ───────────────────────────────────────────────

def fetch_player_season_stats(df_td: pd.DataFrame) -> pd.DataFrame:
    """
    Pull season-level stats for every player in df_td.
    Tries basketball_reference_scraper first, falls back to nba_api.
    Write data/player_season_stats.csv.
    """
    log.info("=" * 60)
    log.info("STEP 3: Fetching player season stats …")

    if df_td.empty:
        log.warning("  No players found; skipping.")
        _write_empty_player_stats()
        return pd.DataFrame()

    players = df_td[["player_id", "player_name"]].drop_duplicates()
    td_counts = df_td.groupby("player_id").size().rename("triple_double_count")

    # Try nba_api PlayerCareerStats for the season
    stats_rows: list[dict] = []

    try:
        from nba_api.stats.endpoints import LeagueDashPlayerStats
        log.info("  Pulling league player stats from nba_api …")
        resp = nba_api_call(
            LeagueDashPlayerStats,
            season=SEASON,
            season_type_all_star="Regular Season",
            per_mode_detailed="PerGame",
            timeout=60,
        )
        df_league = resp.get_data_frames()[0]
        col_map = {
            "PLAYER_ID": "player_id",
            "PLAYER_NAME": "player_name",
            "TEAM_ABBREVIATION": "team",
            "GP": "games_played",
            "PTS": "pts_per_game",
            "AST": "ast_per_game",
            "REB": "reb_per_game",
        }
        df_league.rename(columns={k: v for k, v in col_map.items() if k in df_league.columns}, inplace=True)
        df_league["player_id"] = df_league["player_id"].astype(str)

        # Filter to our players
        our_ids = set(players["player_id"].astype(str))
        df_filtered = df_league[df_league["player_id"].isin(our_ids)].copy()

        for _, r in df_filtered.iterrows():
            stats_rows.append({
                "player_id": r.get("player_id"),
                "player_name": r.get("player_name"),
                "team": r.get("team", ""),
                "games_played": r.get("games_played", 0),
                "pts_per_game": round(float(r.get("pts_per_game", 0)), 1),
                "ast_per_game": round(float(r.get("ast_per_game", 0)), 1),
                "reb_per_game": round(float(r.get("reb_per_game", 0)), 1),
                "ts_pct": None,
                "usage_rate": None,
            })

    except Exception as e:
        log_error("fetch_player_season_stats (nba_api)", e)
        # Minimal fallback from df_td aggregates
        for _, p in players.iterrows():
            p_games = df_td[df_td["player_id"] == p["player_id"]]
            stats_rows.append({
                "player_id": p["player_id"],
                "player_name": p["player_name"],
                "team": "",
                "games_played": len(p_games),
                "pts_per_game": round(p_games["pts"].mean(), 1) if "pts" in p_games else 0,
                "ast_per_game": round(p_games["ast"].mean(), 1) if "ast" in p_games else 0,
                "reb_per_game": round(p_games["reb"].mean(), 1) if "reb" in p_games else 0,
                "ts_pct": None,
                "usage_rate": None,
            })

    # Try to get advanced stats (ts_pct, usage_rate) from basketball_reference_scraper
    try:
        from basketball_reference_scraper.seasons import get_roster_stats
        log.info("  Pulling advanced stats from basketball-reference …")
        df_adv = get_roster_stats(
            team=None, season=2025, data_format="ADVANCED"
        )
        if df_adv is not None and not df_adv.empty:
            adv_map = {r.get("player_id"): r for r in stats_rows}
            for _, adv_row in df_adv.iterrows():
                name = str(adv_row.get("PLAYER", "")).strip()
                for sr in stats_rows:
                    if sr["player_name"].lower() == name.lower():
                        sr["ts_pct"] = adv_row.get("TS%") or adv_row.get("TS_PCT")
                        sr["usage_rate"] = adv_row.get("USG%") or adv_row.get("USG_PCT")
                        break
    except Exception as e:
        log.warning(f"  basketball-reference advanced stats unavailable: {e}")

    df_out = pd.DataFrame(stats_rows)
    # Merge triple_double_count
    td_counts_df = td_counts.reset_index()
    td_counts_df["player_id"] = td_counts_df["player_id"].astype(str)
    df_out["player_id"] = df_out["player_id"].astype(str)
    df_out = df_out.merge(td_counts_df, on="player_id", how="left")

    out_cols = [
        "player_id", "player_name", "team", "games_played",
        "pts_per_game", "ast_per_game", "reb_per_game",
        "ts_pct", "usage_rate", "triple_double_count",
    ]
    df_out = df_out[[c for c in out_cols if c in df_out.columns]]
    out_path = DATA_DIR / "player_season_stats.csv"
    df_out.to_csv(out_path, index=False)
    log.info(f"  ✓ Wrote {len(df_out)} rows → {out_path}")
    return df_out


def _write_empty_player_stats():
    pd.DataFrame(columns=[
        "player_id", "player_name", "team", "games_played",
        "pts_per_game", "ast_per_game", "reb_per_game",
        "ts_pct", "usage_rate", "triple_double_count",
    ]).to_csv(DATA_DIR / "player_season_stats.csv", index=False)


# ── Step 4: Build leaderboard ─────────────────────────────────────────────────

def build_leaderboard(df_td: pd.DataFrame, df_assist: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Join triple_double_games + assist_sequences.
    Write data/leaderboard.csv.
    """
    log.info("=" * 60)
    log.info("STEP 4: Building leaderboard …")

    if df_td.empty:
        log.warning("  No triple-double data; writing empty leaderboard.")
        _write_empty_leaderboard()
        return pd.DataFrame()

    # Load assist data from disk if not passed in
    if df_assist is None:
        assist_path = DATA_DIR / "assist_sequences.csv"
        if assist_path.exists():
            df_assist = pd.read_csv(assist_path)
        else:
            df_assist = pd.DataFrame()

    if df_assist is not None and not df_assist.empty:
        # Remove sentinel unavailable rows
        df_valid_assist = df_assist[df_assist["shot_type"] != "PBP_UNAVAILABLE"].copy()
        df_valid_assist["total_pts"] = (
            df_valid_assist["points_scored"].fillna(0)
            + df_valid_assist["free_throw_points"].fillna(0)
        ).astype(int)

        # Points breakdown by shot type
        df_3pt = (
            df_valid_assist[df_valid_assist["shot_type"] == "3-pointer"]
            .groupby(["game_id", "player_id"])["total_pts"]
            .sum()
            .rename("pts_generated_3pt")
        )
        df_2pt = (
            df_valid_assist[df_valid_assist["shot_type"] == "2-pointer"]
            .groupby(["game_id", "player_id"])["total_pts"]
            .sum()
            .rename("pts_generated_2pt")
        )
        df_ft = (
            df_valid_assist[df_valid_assist["shot_type"] == "Free throw"]
            .groupby(["game_id", "player_id"])["total_pts"]
            .sum()
            .rename("pts_generated_ft")
        )
        df_total = (
            df_valid_assist.groupby(["game_id", "player_id"])["total_pts"]
            .sum()
            .rename("points_via_assists")
        )

        agg = (
            pd.concat([df_3pt, df_2pt, df_ft, df_total], axis=1)
            .fillna(0)
            .astype(int)
            .reset_index()
        )
    else:
        agg = pd.DataFrame(columns=["game_id", "player_id",
                                     "pts_generated_3pt", "pts_generated_2pt",
                                     "pts_generated_ft", "points_via_assists"])

    # Merge with triple-double games
    df_td["game_id"] = df_td["game_id"].astype(str)
    df_td["player_id"] = df_td["player_id"].astype(str)
    if not agg.empty:
        agg["game_id"] = agg["game_id"].astype(str)
        agg["player_id"] = agg["player_id"].astype(str)

    df_merged = df_td.merge(agg, on=["game_id", "player_id"], how="left")
    for col in ["pts_generated_3pt", "pts_generated_2pt", "pts_generated_ft", "points_via_assists"]:
        if col not in df_merged.columns:
            df_merged[col] = 0
        df_merged[col] = df_merged[col].fillna(0).astype(int)

    df_merged["total_points_touched"] = (
        df_merged["pts"].fillna(0).astype(int) + df_merged["points_via_assists"]
    )
    df_merged = df_merged.sort_values("total_points_touched", ascending=False).reset_index(drop=True)
    df_merged["rank"] = df_merged.index + 1

    out_cols = [
        "rank", "game_id", "player_id", "player_name", "game_date",
        "opponent_team", "pts", "ast", "reb",
        "points_via_assists", "pts_generated_3pt", "pts_generated_2pt",
        "pts_generated_ft", "total_points_touched", "team_result", "home_away",
    ]
    df_out = df_merged[[c for c in out_cols if c in df_merged.columns]]
    out_path = DATA_DIR / "leaderboard.csv"
    df_out.to_csv(out_path, index=False)
    log.info(f"  ✓ Wrote {len(df_out)} rows → {out_path}")
    return df_out


def _write_empty_leaderboard():
    pd.DataFrame(columns=[
        "rank", "game_id", "player_id", "player_name", "game_date",
        "opponent_team", "pts", "ast", "reb",
        "points_via_assists", "pts_generated_3pt", "pts_generated_2pt",
        "pts_generated_ft", "total_points_touched",
    ]).to_csv(DATA_DIR / "leaderboard.csv", index=False)


# ── Step 5: Metadata ──────────────────────────────────────────────────────────

def write_metadata(
    games_fetched: int,
    players_fetched: int,
    pbp_success: int,
    pbp_failed: int,
):
    """Write pull_metadata.csv."""
    log.info("=" * 60)
    log.info("STEP 5: Writing metadata …")

    # Collect package versions
    versions: dict[str, str] = {}
    for pkg in ["nba_api", "pbpstats", "pandas", "requests"]:
        try:
            import importlib.metadata
            versions[pkg] = importlib.metadata.version(pkg)
        except Exception:
            versions[pkg] = "unknown"

    row = {
        "pull_timestamp": datetime.now(timezone.utc).isoformat(),
        "season": SEASON,
        "games_fetched": games_fetched,
        "players_fetched": players_fetched,
        "pbp_games_success": pbp_success,
        "pbp_games_failed": pbp_failed,
        "source_versions": json.dumps(versions),
    }
    df = pd.DataFrame([row])
    out_path = DATA_DIR / "pull_metadata.csv"
    df.to_csv(out_path, index=False)
    log.info(f"  ✓ Wrote pull_metadata.csv")


# ── Single-game refresh ───────────────────────────────────────────────────────

def refresh_single_game(game_id: str):
    """
    Re-fetch PBP for a single game_id and update assist_sequences.csv
    and leaderboard.csv in place.
    """
    log.info(f"Single-game refresh for game_id={game_id}")

    td_path = DATA_DIR / "triple_double_games.csv"
    if not td_path.exists():
        log.error("triple_double_games.csv not found. Run full data_pull first.")
        sys.exit(1)

    df_td = pd.read_csv(td_path)
    df_td["game_id"] = df_td["game_id"].astype(str)
    game_rows = df_td[df_td["game_id"] == game_id]

    if game_rows.empty:
        log.error(f"game_id {game_id} not found in triple_double_games.csv.")
        sys.exit(1)

    # Re-fetch PBP for each player in that game
    from utils.pbp_parser import fetch_pbpstats_events, parse_assist_sequences

    new_rows: list[dict] = []
    for _, row in game_rows.iterrows():
        player_id = str(row["player_id"])
        player_name = str(row["player_name"])
        try:
            events = fetch_pbpstats_events(game_id)
            seqs = parse_assist_sequences(events, player_name)
            for s in seqs:
                s.update({"game_id": game_id, "player_id": player_id, "player_name": player_name})
                new_rows.append(s)
            log.info(f"  {player_name}: {len(seqs)} sequences.")
        except Exception as e:
            log_error(f"refresh_single_game {game_id} ({player_name})", e)

    # Update assist_sequences.csv
    assist_path = DATA_DIR / "assist_sequences.csv"
    if assist_path.exists():
        df_old = pd.read_csv(assist_path)
        df_old["game_id"] = df_old["game_id"].astype(str)
        df_old = df_old[df_old["game_id"] != game_id]
    else:
        df_old = pd.DataFrame()

    df_new_assist = pd.concat([df_old, pd.DataFrame(new_rows)], ignore_index=True)
    df_new_assist.to_csv(assist_path, index=False)
    log.info(f"  Updated assist_sequences.csv.")

    # Rebuild leaderboard
    build_leaderboard(df_td, df_new_assist)
    log.info("  Single-game refresh complete.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Triple Double Receipt — data pull")
    parser.add_argument("--game-id", type=str, default=None,
                        help="Refresh PBP for a single game ID only")
    args = parser.parse_args()

    if args.game_id:
        refresh_single_game(args.game_id)
        return

    start = time.time()
    log.info("╔══════════════════════════════════════════════════════════╗")
    log.info("║  Triple Double Receipt — Full Data Pull                 ║")
    log.info(f"║  Season: {SEASON}                                         ║")
    log.info("╚══════════════════════════════════════════════════════════╝")

    # Step 1
    df_td = fetch_triple_double_games()
    games_fetched = len(df_td)
    players_fetched = df_td["player_id"].nunique() if not df_td.empty else 0

    # Step 2
    pbp_success, pbp_failed = 0, 0
    df_assist = pd.DataFrame()
    try:
        result = fetch_assist_sequences(df_td)
        if isinstance(result, tuple):
            df_assist, pbp_success, pbp_failed = result
        else:
            df_assist = result
    except Exception as e:
        log_error("fetch_assist_sequences outer", e)

    # Step 3
    try:
        fetch_player_season_stats(df_td)
    except Exception as e:
        log_error("fetch_player_season_stats outer", e)

    # Step 4
    try:
        build_leaderboard(df_td, df_assist if not df_assist.empty else None)
    except Exception as e:
        log_error("build_leaderboard outer", e)

    # Step 5
    write_metadata(games_fetched, players_fetched, pbp_success, pbp_failed)

    elapsed = time.time() - start
    log.info("")
    log.info("══════════════════════ SUMMARY ══════════════════════════")
    log.info(f"  Games fetched:      {games_fetched}")
    log.info(f"  Unique players:     {players_fetched}")
    log.info(f"  PBP success:        {pbp_success}")
    log.info(f"  PBP failed:         {pbp_failed}")
    log.info(f"  CSVs written:       5 (in {DATA_DIR})")
    log.info(f"  Total time:         {elapsed:.1f}s")
    if pbp_failed:
        log.info(f"  Error log:          {LOG_FILE}")
    log.info("═════════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
