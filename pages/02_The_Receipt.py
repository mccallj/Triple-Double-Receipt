"""
Page 2 — The Receipt
Hero view: receipt-style breakdown of a single triple-double game.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styles import inject_styles, render_app_banner, receipt_line_html
from utils.data_loader import (
    load_assist_sequences,
    load_triple_double_games,
    load_leaderboard,
    load_metadata,
    check_freshness,
    _hours_since,
    freshness_label,
)

st.set_page_config(
    page_title="The Receipt — Triple Double Receipt",
    page_icon="🧾",
    layout="wide",
)

inject_styles()
render_app_banner("receipt")

st.markdown(
    '<h2 style="font-family:\'IBM Plex Mono\',monospace;font-weight:700;'
    'color:#1A1A2E;margin-bottom:4px;">The Receipt</h2>'
    '<p style="color:#6B7280;font-size:13px;margin-top:0;">Full point contribution breakdown · Single game</p>',
    unsafe_allow_html=True,
)

check_freshness()

# ── Game ID resolution ────────────────────────────────────────────────────────
# Can come from session state (drill-through from Player Log) or a URL param / manual input

game_id = st.session_state.get("receipt_game_id", None)
player_id = st.session_state.get("receipt_player_id", None)
player_name_hint = st.session_state.get("receipt_player_name", None)

# Load all data first (needed for the selector too)
df_td = load_triple_double_games()
df_lb = load_leaderboard()
df_assist = load_assist_sequences()

if df_td is None or df_td.empty:
    st.info("No data found. Run `python data_pull.py` first.")
    st.stop()

# ── Manual game selector (always visible) ─────────────────────────────────────
st.markdown("**Select a game:**")
col_sel1, col_sel2 = st.columns([2, 3])

with col_sel1:
    lb_source = df_lb if (df_lb is not None and not df_lb.empty) else df_td
    lb_source = lb_source.copy()
    lb_source["label"] = (
        lb_source["player_name"].astype(str) + " | "
        + lb_source["game_date"].astype(str) + " vs "
        + lb_source["opponent_team"].astype(str)
        + " — " + lb_source["pts"].astype(str) + "/"
        + lb_source["ast"].astype(str) + "/"
        + lb_source["reb"].astype(str)
    )
    lb_source = lb_source.sort_values("game_date", ascending=False)

    # Pre-select from session state
    default_label = "— Select a game —"
    if game_id and player_id:
        mask = (
            lb_source["game_id"].astype(str) == str(game_id)
        ) & (
            lb_source["player_id"].astype(str) == str(player_id)
        )
        if mask.any():
            default_label = lb_source[mask].iloc[0]["label"]

    options = ["— Select a game —"] + lb_source["label"].tolist()
    try:
        default_idx = options.index(default_label)
    except ValueError:
        default_idx = 0

    selected_label = st.selectbox(
        "Game",
        options=options,
        index=default_idx,
        label_visibility="collapsed",
    )

if selected_label == "— Select a game —":
    st.markdown(
        '<div class="tdr-card" style="text-align:center;color:#6B7280;padding:40px;">'
        'Select a game above to view the receipt breakdown.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# Resolve game_id and player_id from selection
sel_row = lb_source[lb_source["label"] == selected_label].iloc[0]
game_id = str(sel_row["game_id"])
player_id = str(sel_row["player_id"])

# ── Pull game-level data ──────────────────────────────────────────────────────
game_td_row = df_td[
    (df_td["game_id"].astype(str) == game_id) &
    (df_td["player_id"].astype(str) == player_id)
]
if game_td_row.empty:
    st.error(f"Game data not found for game_id={game_id}, player_id={player_id}.")
    st.stop()

row = game_td_row.iloc[0]
player_name = str(row.get("player_name", "Unknown"))
game_date = str(row.get("game_date", ""))
opponent = str(row.get("opponent_team", ""))
result = str(row.get("team_result", ""))
own_pts = int(row.get("pts", 0))
ast = int(row.get("ast", 0))
reb = int(row.get("reb", 0))

# ── Pull assist sequences ─────────────────────────────────────────────────────
game_assists = pd.DataFrame()
pbp_unavailable = False

if df_assist is not None and not df_assist.empty:
    game_assists = df_assist[
        (df_assist["game_id"].astype(str) == game_id) &
        (df_assist["player_id"].astype(str) == player_id)
    ].copy()

    # Check for sentinel unavailable row
    if not game_assists.empty and (game_assists["shot_type"] == "PBP_UNAVAILABLE").all():
        pbp_unavailable = True
        game_assists = pd.DataFrame()

# ── Compute totals ────────────────────────────────────────────────────────────
pts_via_3pt = 0
pts_via_2pt = 0
pts_via_ft = 0

if not game_assists.empty:
    valid = game_assists[game_assists["shot_type"] != "PBP_UNAVAILABLE"].copy()
    valid["total_pts"] = (
        valid["points_scored"].fillna(0).astype(int) +
        valid["free_throw_points"].fillna(0).astype(int)
    )
    pts_via_3pt = int(valid[valid["shot_type"] == "3-pointer"]["total_pts"].sum())
    pts_via_2pt = int(valid[valid["shot_type"] == "2-pointer"]["total_pts"].sum())
    pts_via_ft  = int(valid[valid["shot_type"] == "Free throw"]["total_pts"].sum())

pts_via_assists = pts_via_3pt + pts_via_2pt + pts_via_ft
total_points_touched = own_pts + pts_via_assists

n_3pt = 0
n_2pt = 0
n_ft  = 0
if not game_assists.empty:
    n_3pt = int((valid["shot_type"] == "3-pointer").sum())
    n_2pt = int((valid["shot_type"] == "2-pointer").sum())
    n_ft  = int((valid["shot_type"] == "Free throw").sum())

# ── Freshness footer label ────────────────────────────────────────────────────
meta = load_metadata()
if meta:
    hours_old = _hours_since(str(meta.get("pull_timestamp", "")))
    footer_label = f"Last data refresh: {freshness_label(hours_old)}"
else:
    footer_label = "Data refresh time unknown"

# ── Render Receipt ────────────────────────────────────────────────────────────
_, center_col, _ = st.columns([1, 3, 1])
with center_col:

    # ── Header ─────────────────────────────────────────────────────────────
    result_display = f"{'✅ W' if result == 'W' else '❌ L' if result == 'L' else result}"
    header_html = f"""
<div class="receipt-wrap">
  <div class="receipt-header">
    <div class="receipt-player">{player_name}</div>
    <div class="receipt-meta">{game_date} · vs {opponent} · {result_display}</div>
    <div class="receipt-meta" style="margin-top:6px;">
      <span class="mono" style="font-size:15px;font-weight:600;">{own_pts} PTS</span>
      &nbsp;·&nbsp;
      <span class="mono" style="font-size:15px;font-weight:600;">{ast} AST</span>
      &nbsp;·&nbsp;
      <span class="mono" style="font-size:15px;font-weight:600;">{reb} REB</span>
    </div>
  </div>
"""
    st.markdown(header_html, unsafe_allow_html=True)

    if pbp_unavailable:
        st.markdown(
            '<div style="padding:16px;text-align:center;color:#C0392B;font-size:13px;">'
            '⚠️ Play-by-play unavailable for this game. '
            'Re-run <code>python data_pull.py --game-id '
            + game_id +
            '</code> to retry.</div>',
            unsafe_allow_html=True,
        )
    elif game_assists.empty:
        st.markdown(
            '<div style="padding:16px;text-align:center;color:#6B7280;font-size:13px;">'
            'No assist sequences recorded for this game.</div>',
            unsafe_allow_html=True,
        )
    else:
        # ── Line items ─────────────────────────────────────────────────────
        lines_html = ""
        running_total = 0
        valid_sorted = valid.sort_values(["period", "time_remaining"], ascending=[True, False])

        for _, evt in valid_sorted.iterrows():
            period = str(evt.get("period", "?"))
            time_rem = str(evt.get("time_remaining", "?:??"))
            teammate = str(evt.get("assisted_player", "Teammate"))
            shot_type = str(evt.get("shot_type", "Field goal"))
            pts = int(evt.get("total_pts", evt.get("points_scored", 0)))
            is_and1 = bool(evt.get("is_and1", False))
            ft_pts = int(evt.get("free_throw_points", 0))

            label = shot_type
            if is_and1 and ft_pts > 0:
                label += f" + and-1 FT"

            lines_html += receipt_line_html(period, time_rem, teammate, label, pts)
            running_total += pts

        lines_html += f"""
<div style="display:flex;justify-content:flex-end;font-size:12px;
            color:#6B7280;padding-top:8px;font-family:'IBM Plex Mono',monospace;">
  Running total: {running_total} pts
</div>
"""
        st.markdown(lines_html, unsafe_allow_html=True)

    # ── Subtotal block ──────────────────────────────────────────────────────
    subtotal_html = f"""
<div class="receipt-subtotal">
  <div class="receipt-subtotal-row">
    <span>Assisted 3-pointers ({n_3pt} makes × 3 pts)</span>
    <span class="sub-val">{pts_via_3pt} pts</span>
  </div>
  <div class="receipt-subtotal-row">
    <span>Assisted 2-pointers ({n_2pt} makes × 2 pts)</span>
    <span class="sub-val">{pts_via_2pt} pts</span>
  </div>
  <div class="receipt-subtotal-row">
    <span>Assisted free throws ({n_ft} makes × 1 pt)</span>
    <span class="sub-val">{pts_via_ft} pts</span>
  </div>
  <div class="receipt-subtotal-row" style="margin-top:8px;font-weight:600;color:#374151;">
    <span>Points Generated via Assists</span>
    <span class="sub-val" style="color:#1B4332;">{pts_via_assists} pts</span>
  </div>
</div>

<hr class="receipt-divider">

<div class="receipt-own-score">
  <span>Player's own scoring</span>
  <span class="own-val mono">{own_pts} pts</span>
</div>

<div class="receipt-total">
  <span class="total-label">Total Points Touched</span>
  <span class="total-val">{total_points_touched}</span>
</div>

<div class="receipt-footer">{footer_label}</div>
</div>
"""
    st.markdown(subtotal_html, unsafe_allow_html=True)

# ── Stacked bar chart ─────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<h3 style="font-family:\'IBM Plex Mono\',monospace;font-size:16px;'
    'color:#1A1A2E;">Point Breakdown</h3>',
    unsafe_allow_html=True,
)

fig = go.Figure()

segments = [
    ("Own Scoring", own_pts, "#1B4332"),
    ("3PT Assisted", pts_via_3pt, "#2D6A4F"),
    ("2PT Assisted", pts_via_2pt, "#52B788"),
    ("FT Assisted",  pts_via_ft,  "#95D5B2"),
]

for name, val, color in segments:
    if val > 0:
        fig.add_trace(go.Bar(
            name=name,
            x=[val],
            y=[player_name],
            orientation="h",
            marker_color=color,
            text=f"<b>{name}</b><br>{val} pts",
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate=f"{name}: {val} pts<extra></extra>",
            showlegend=False,
        ))

fig.update_layout(
    barmode="stack",
    plot_bgcolor="white",
    paper_bgcolor="white",
    height=120,
    margin=dict(l=0, r=0, t=10, b=10),
    xaxis=dict(
        showgrid=True,
        gridcolor="#F3F4F6",
        gridwidth=1,
        zeroline=False,
        showticklabels=True,
        tickfont=dict(family="IBM Plex Mono", size=11),
    ),
    yaxis=dict(showticklabels=False, showgrid=False),
    font=dict(family="Inter", size=12, color="#1A1A2E"),
)

st.plotly_chart(fig, use_container_width=True)

# ── Copy game link helper ─────────────────────────────────────────────────────
st.divider()
st.markdown("**Copy game reference:**")
st.code(f"game_id={game_id} | player={player_name}", language=None)
