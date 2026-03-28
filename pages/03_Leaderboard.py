"""
Page 3 — Season Leaderboard
Ranked table of all triple-double performances by Total Points Touched.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.styles import inject_styles, render_brand_header, callout_card_html
from utils.data_loader import load_leaderboard, check_freshness

st.set_page_config(
    page_title="Leaderboard — Triple Double Receipt",
    page_icon="🏆",
    layout="wide",
)

inject_styles()
render_brand_header()

st.markdown(
    '<h2 style="font-family:\'IBM Plex Mono\',monospace;font-weight:700;'
    'color:#1A1A2E;margin-bottom:4px;">Season Leaderboard</h2>'
    '<p style="color:#6B7280;font-size:13px;margin-top:0;">2024–25 Regular Season · Ranked by Total Points Touched</p>',
    unsafe_allow_html=True,
)

check_freshness()

# ── Load data ─────────────────────────────────────────────────────────────────
df_lb = load_leaderboard()

if df_lb is None or df_lb.empty:
    st.info("No leaderboard data found. Run `python data_pull.py` to populate.")
    st.stop()

df_lb = df_lb.copy()

# Ensure numeric types
for col in ["pts", "ast", "reb", "total_points_touched", "points_via_assists",
            "pts_generated_3pt", "pts_generated_2pt", "pts_generated_ft"]:
    if col in df_lb.columns:
        df_lb[col] = pd.to_numeric(df_lb[col], errors="coerce").fillna(0).astype(int)

# ── #1 Callout card ───────────────────────────────────────────────────────────
top = df_lb.sort_values("total_points_touched", ascending=False).iloc[0]
st.markdown(
    callout_card_html(
        player=str(top.get("player_name", "")),
        date=str(top.get("game_date", "")),
        opponent=str(top.get("opponent_team", "")),
        result=str(top.get("team_result", "")),
        total=int(top.get("total_points_touched", 0)),
    ),
    unsafe_allow_html=True,
)

# ── Filters ───────────────────────────────────────────────────────────────────
st.markdown(
    '<p style="font-size:12px;font-weight:600;letter-spacing:.06em;'
    'text-transform:uppercase;color:#6B7280;margin-bottom:8px;">Filters</p>',
    unsafe_allow_html=True,
)

col_f1, col_f2, col_f3 = st.columns([1, 1, 2])

with col_f1:
    min_ast = st.slider(
        "Min Assists",
        min_value=10,
        max_value=int(df_lb["ast"].max()) if df_lb["ast"].max() > 10 else 20,
        value=10,
        step=1,
    )

with col_f2:
    min_reb = st.slider(
        "Min Rebounds",
        min_value=10,
        max_value=int(df_lb["reb"].max()) if df_lb["reb"].max() > 10 else 20,
        value=10,
        step=1,
    )

with col_f3:
    if "game_date" in df_lb.columns:
        dates = pd.to_datetime(df_lb["game_date"], errors="coerce").dropna()
        if not dates.empty:
            min_date = dates.min().date()
            max_date = dates.max().date()
            date_range = st.slider(
                "Date Range",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
            )
        else:
            date_range = None
    else:
        date_range = None

# Apply filters (client-side — pure pandas)
df_filtered = df_lb.copy()
df_filtered = df_filtered[df_filtered["ast"] >= min_ast]
df_filtered = df_filtered[df_filtered["reb"] >= min_reb]

if date_range is not None and "game_date" in df_filtered.columns:
    df_filtered["game_date_dt"] = pd.to_datetime(df_filtered["game_date"], errors="coerce")
    df_filtered = df_filtered[
        (df_filtered["game_date_dt"].dt.date >= date_range[0]) &
        (df_filtered["game_date_dt"].dt.date <= date_range[1])
    ].drop(columns=["game_date_dt"])

# Re-rank after filtering
df_filtered = df_filtered.sort_values("total_points_touched", ascending=False).reset_index(drop=True)
df_filtered["rank"] = df_filtered.index + 1

st.markdown(
    f'<p style="font-size:12px;color:#6B7280;margin:8px 0;">'
    f'Showing {len(df_filtered)} performances</p>',
    unsafe_allow_html=True,
)

# ── Display table ─────────────────────────────────────────────────────────────
display_cols_map = {
    "rank": "#",
    "player_name": "Player",
    "game_date": "Date",
    "opponent_team": "Opponent",
    "team_result": "W/L",
    "pts": "PTS",
    "ast": "AST",
    "reb": "REB",
    "points_via_assists": "Pts via Assists",
    "total_points_touched": "Total Pts Touched",
}
available = {k: v for k, v in display_cols_map.items() if k in df_filtered.columns}
df_display = df_filtered[list(available.keys())].rename(columns=available)

st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Total Pts Touched": st.column_config.NumberColumn(
            "Total Pts Touched",
            format="%d",
            help="Player's own points + points generated via assists",
        ),
        "Pts via Assists": st.column_config.NumberColumn(
            "Pts via Assists",
            format="%d",
        ),
    },
)

# ── Drill-through to Receipt ──────────────────────────────────────────────────
st.divider()
st.markdown(
    '<p style="font-size:13px;color:#6B7280;">Open a Receipt for any performance:</p>',
    unsafe_allow_html=True,
)

col_d1, col_d2 = st.columns([3, 2])

with col_d1:
    df_for_select = df_filtered.copy()
    df_for_select["label"] = (
        "#" + df_for_select["rank"].astype(str) + " — "
        + df_for_select["player_name"].astype(str) + " | "
        + df_for_select["game_date"].astype(str) + " vs "
        + df_for_select["opponent_team"].astype(str)
        + " (" + df_for_select["total_points_touched"].astype(str) + " TPT)"
    )

    selected_lb_game = st.selectbox(
        "Select performance",
        options=["— Select a performance —"] + df_for_select["label"].tolist(),
        label_visibility="collapsed",
    )

    if selected_lb_game != "— Select a performance —":
        match = df_for_select[df_for_select["label"] == selected_lb_game]
        if not match.empty:
            r = match.iloc[0]
            st.session_state["receipt_game_id"] = str(r["game_id"])
            st.session_state["receipt_player_id"] = str(r["player_id"])
            st.session_state["receipt_player_name"] = str(r["player_name"])
            st.markdown(
                f'<div class="tdr-card" style="padding:14px;">'
                f'<strong>Selected:</strong> {r["player_name"]} · {r["game_date"]}<br>'
                f'<span style="font-size:12px;color:#6B7280;">'
                f'Navigate to <strong>The Receipt</strong> to view breakdown.</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.code(f"game_id={r['game_id']} | player={r['player_name']}", language=None)

with col_d2:
    if selected_lb_game != "— Select a performance —":
        st.markdown("<br>", unsafe_allow_html=True)
        st.page_link("pages/02_The_Receipt.py", label="→ Open The Receipt", icon="🧾")

# ── Bar chart: top 10 performances ───────────────────────────────────────────
st.divider()
st.markdown(
    '<h3 style="font-family:\'IBM Plex Mono\',monospace;font-size:16px;color:#1A1A2E;">'
    'Top Performances — Total Points Touched</h3>',
    unsafe_allow_html=True,
)

top10 = df_filtered.head(10).copy()
if not top10.empty:
    top10["label"] = top10["player_name"] + "\n" + top10["game_date"].astype(str)

    fig = go.Figure()

    own_pts_vals = top10["pts"].tolist()
    assist_pts_vals = top10["points_via_assists"].tolist() if "points_via_assists" in top10 else [0]*len(top10)
    labels = top10["label"].tolist()

    fig.add_trace(go.Bar(
        name="Own Scoring",
        y=labels,
        x=own_pts_vals,
        orientation="h",
        marker_color="#1B4332",
        text=[f"<b>{v}</b>" if v > 3 else "" for v in own_pts_vals],
        textposition="inside",
        insidetextanchor="middle",
        hovertemplate="Own Scoring: %{x} pts<extra></extra>",
        showlegend=False,
    ))

    fig.add_trace(go.Bar(
        name="Via Assists",
        y=labels,
        x=assist_pts_vals,
        orientation="h",
        marker_color="#95D5B2",
        text=[f"<b>+{v}</b>" if v > 3 else "" for v in assist_pts_vals],
        textposition="inside",
        insidetextanchor="middle",
        hovertemplate="Via Assists: %{x} pts<extra></extra>",
        showlegend=False,
    ))

    fig.update_layout(
        barmode="stack",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=max(300, len(top10) * 50),
        margin=dict(l=140, r=20, t=10, b=30),
        xaxis=dict(
            showgrid=True,
            gridcolor="#F3F4F6",
            gridwidth=1,
            zeroline=False,
            tickfont=dict(family="IBM Plex Mono", size=11),
            title=dict(text="Points", font=dict(family="Inter", size=12)),
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(family="IBM Plex Mono", size=11),
            autorange="reversed",
        ),
        font=dict(family="Inter", size=12, color="#1A1A2E"),
    )

    st.plotly_chart(fig, use_container_width=True)
