"""
Page 1 — Player Season Log
Landing page for selecting a player and viewing all their triple-double games.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styles import inject_styles, render_brand_header, stat_banner_html
from utils.data_loader import (
    load_triple_double_games,
    load_leaderboard,
    check_freshness,
)

st.set_page_config(
    page_title="Player Log — Triple Double Receipt",
    page_icon="📋",
    layout="wide",
)

inject_styles()
render_brand_header()

st.markdown(
    '<h2 style="font-family:\'IBM Plex Mono\',monospace;font-weight:700;'
    'color:#1A1A2E;margin-bottom:4px;">Player Season Log</h2>'
    '<p style="color:#6B7280;font-size:13px;margin-top:0;">2024–25 Regular Season · Triple Double Performances</p>',
    unsafe_allow_html=True,
)

check_freshness()

# ── Load data ─────────────────────────────────────────────────────────────────
df_td = load_triple_double_games()
df_lb = load_leaderboard()

if df_td is None or df_td.empty:
    st.info("No triple-double game data available. Run `python data_pull.py` to populate.")
    st.stop()

# ── Player selector ───────────────────────────────────────────────────────────
player_names = sorted(df_td["player_name"].dropna().unique().tolist())

col_sel, col_spacer = st.columns([2, 3])
with col_sel:
    selected_player = st.selectbox(
        "Select a player",
        options=["— Choose a player —"] + player_names,
        label_visibility="collapsed",
    )

if selected_player == "— Choose a player —":
    st.markdown(
        '<div class="tdr-card" style="text-align:center;color:#6B7280;padding:40px;">'
        'Select a player above to view their triple-double season log.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Filter to selected player ─────────────────────────────────────────────────
df_player_td = df_td[df_td["player_name"] == selected_player].copy()
df_player_lb = (
    df_lb[df_lb["player_name"] == selected_player].copy()
    if df_lb is not None else None
)

# ── Summary stat banner ───────────────────────────────────────────────────────
total_tds = len(df_player_td)

if df_player_lb is not None and not df_player_lb.empty:
    avg_tpt = round(df_player_lb["total_points_touched"].mean(), 1)
    max_tpt = int(df_player_lb["total_points_touched"].max())
else:
    avg_tpt = "—"
    max_tpt = "—"

st.markdown(
    stat_banner_html([
        {"label": "Triple Doubles", "value": str(total_tds)},
        {"label": "Avg Total Pts Touched", "value": str(avg_tpt)},
        {"label": "Best Single Game", "value": str(max_tpt)},
    ]),
    unsafe_allow_html=True,
)

# ── Build display table ───────────────────────────────────────────────────────
import pandas as pd

if df_player_lb is not None and not df_player_lb.empty:
    display_df = df_player_lb[[
        c for c in [
            "game_date", "opponent_team", "team_result",
            "pts", "ast", "reb",
            "total_points_touched", "points_via_assists",
            "game_id", "player_id",
        ] if c in df_player_lb.columns
    ]].copy()
else:
    # Fall back to triple_double_games only (no assist data)
    display_df = df_player_td[[
        c for c in [
            "game_date", "opponent_team", "team_result",
            "pts", "ast", "reb", "game_id", "player_id",
        ] if c in df_player_td.columns
    ]].copy()
    display_df["total_points_touched"] = display_df.get("pts", 0)
    display_df["points_via_assists"] = 0

rename_map = {
    "game_date": "Date",
    "opponent_team": "Opponent",
    "team_result": "W/L",
    "pts": "PTS",
    "ast": "AST",
    "reb": "REB",
    "total_points_touched": "Total Pts Touched",
    "points_via_assists": "Pts via Assists",
}
display_df.rename(columns=rename_map, inplace=True)

# Sort by date descending
if "Date" in display_df.columns:
    display_df = display_df.sort_values("Date", ascending=False)

# ── Game selection for drill-through ─────────────────────────────────────────
st.markdown(
    '<p style="font-size:13px;color:#6B7280;margin-bottom:6px;">'
    'Select a game to view the full receipt breakdown ↓</p>',
    unsafe_allow_html=True,
)

# Use a selectbox for game drill-through (mobile-friendly)
game_options_df = display_df.copy()
game_options_df["label"] = (
    game_options_df.get("Date", "").astype(str) + " vs "
    + game_options_df.get("Opponent", "").astype(str)
    + " — " + game_options_df.get("PTS", 0).astype(str) + "/"
    + game_options_df.get("AST", 0).astype(str) + "/"
    + game_options_df.get("REB", 0).astype(str)
)

# Show the table
table_cols = [c for c in ["Date", "Opponent", "W/L", "PTS", "AST", "REB",
                            "Total Pts Touched", "Pts via Assists"]
              if c in display_df.columns]

st.dataframe(
    display_df[table_cols].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
)

# ── Drill-through to Receipt ──────────────────────────────────────────────────
st.divider()
col_drill1, col_drill2 = st.columns([3, 2])
with col_drill1:
    if "game_id" in display_df.columns and len(game_options_df) > 0:
        selected_game_label = st.selectbox(
            "Open a Receipt",
            options=["— Select a game —"] + game_options_df["label"].tolist(),
        )
        if selected_game_label != "— Select a game —":
            match = game_options_df[game_options_df["label"] == selected_game_label]
            if not match.empty:
                gid = str(match.iloc[0]["game_id"])
                pid = str(match.iloc[0].get("player_id", ""))
                st.session_state["receipt_game_id"] = gid
                st.session_state["receipt_player_id"] = pid
                st.session_state["receipt_player_name"] = selected_player

                st.markdown(
                    f'<div class="tdr-card" style="padding:16px;">'
                    f'<strong>Game selected:</strong> <code>{gid}</code><br>'
                    f'<span style="font-size:12px;color:#6B7280;">Navigate to <strong>The Receipt</strong> page to view the full breakdown.</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Share link helper
                st.markdown("**Copy game reference:**")
                st.code(f"game_id={gid} | player={selected_player}", language=None)

with col_drill2:
    if "game_id" in display_df.columns and len(game_options_df) > 0:
        st.markdown(
            '<div style="padding:16px;">'
            '<p style="font-size:13px;color:#6B7280;margin-bottom:8px;">'
            'After selecting a game above, go to:</p>',
            unsafe_allow_html=True,
        )
        st.page_link("pages/02_The_Receipt.py", label="→ Open The Receipt", icon="🧾")
