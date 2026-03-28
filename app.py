"""
Triple Double Receipt — main entry point.
Handles sidebar navigation, freshness banner, and global layout.
"""

import streamlit as st

st.set_page_config(
    page_title="Triple Double Receipt",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from utils.styles import inject_styles, render_app_banner, GOOGLE_FONTS, GLOBAL_CSS
from utils.data_loader import load_metadata, check_freshness, freshness_label

# ── Inject global styles ──────────────────────────────────────────────────────
inject_styles()

# ── Main: masthead + primary nav (also on each page script) ───────────────────
render_app_banner("home")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(GOOGLE_FONTS, unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-title">Triple Double<br>Receipt</div>'
        '<div class="sidebar-season">2024–25 Regular Season</div>',
        unsafe_allow_html=True,
    )

    # Freshness badge
    meta = load_metadata()
    if meta is not None:
        from utils.data_loader import _hours_since
        hours_old = _hours_since(str(meta.get("pull_timestamp", "")))
        label = freshness_label(hours_old)
        badge_class = "freshness-badge" if hours_old <= 24 else "freshness-badge-warn"
        st.markdown(
            f'<span class="{badge_class}">Last updated: {label}</span>',
            unsafe_allow_html=True,
        )
        st.caption(f"Season: {meta.get('season', '2024-25')} · "
                   f"{int(meta.get('games_fetched', 0))} games")
    else:
        st.markdown(
            '<span class="freshness-badge-warn">No data — run data_pull.py</span>',
            unsafe_allow_html=True,
        )

    st.divider()

    with st.expander("How it works"):
        st.markdown(
            """
**Total Points Touched** is the full accounting of a player's impact on
the scoreboard in a single game.

It adds together:
- **Their own points** scored
- **Every point their assists directly created** — broken down by 3-pointers,
  2-pointers, and free throws (including and-1 conversions)

A triple double often undersells a player's real impact. The receipt shows
the invoice underneath the headline.

*Data sourced from NBA Stats API and play-by-play logs. Play-by-play
is parsed to trace each assist to the exact shot type it produced.*
            """
        )

    st.divider()
    st.caption("Use the banner links to move between sections.")

# ── Landing page content (redirects user to Player Log) ──────────────────────
st.markdown(
    """
<div class="tdr-card" style="text-align:center; padding: 40px 24px;">
  <div style="font-family:'IBM Plex Mono',monospace; font-size:36px;
              font-weight:700; color:#1B4332; margin-bottom:12px;">
    Triple Double Receipt
  </div>
  <div style="font-size:16px; color:#6B7280; max-width:520px; margin:0 auto 24px;">
    A triple double is a headline.<br>
    This app shows the invoice underneath it.
  </div>
  <div style="font-size:13px; color:#9CA3AF;">
    Use the banner above → <strong>Player Log</strong> · <strong>The Receipt</strong> · <strong>Leaderboard</strong>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Global freshness check — shows banner across all pages via session state
check_freshness()
