"""
Shared CSS and card HTML templates for Triple Double Receipt.
NYT Games aesthetic — IBM Plex Mono for numbers, Inter for body.
"""

from __future__ import annotations

import base64
from pathlib import Path

_LOGO_PATH = Path(__file__).resolve().parent.parent / "Logo.PNG"

GOOGLE_FONTS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
"""

GLOBAL_CSS = """
<style>
  /* ── Base ── */
  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #1A1A2E;
  }

  /* ── Typography helpers (work with dark theme overrides) ── */
  .tdr-page-title {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 700;
    color: #1A1A2E;
    margin-bottom: 4px;
  }
  .tdr-subtitle {
    font-size: 13px;
    margin-top: 0;
    color: #6B7280;
  }
  .tdr-muted { color: #6B7280; }
  .tdr-caption { font-size: 12px; color: #6B7280; }
  .tdr-landing-tagline { font-size: 16px; color: #6B7280; max-width: 520px; margin: 0 auto 24px; }
  .tdr-landing-hint { font-size: 13px; color: #9CA3AF; }
  .tdr-hero-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 36px;
    font-weight: 700;
    color: #1B4332;
    margin-bottom: 12px;
  }
  .tdr-section-heading {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 16px;
    font-weight: 600;
    color: #1A1A2E;
    margin: 8px 0 12px 0;
  }
  .tdr-filter-heading {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #6B7280;
    margin-bottom: 8px;
  }
  .tdr-running-total {
    display: flex;
    justify-content: flex-end;
    font-size: 12px;
    color: #6B7280;
    padding-top: 8px;
    font-family: 'IBM Plex Mono', monospace;
  }
  .tdr-receipt-alert {
    padding: 16px;
    text-align: center;
    color: #C0392B;
    font-size: 13px;
  }
  .tdr-receipt-muted-box {
    padding: 16px;
    text-align: center;
    color: #6B7280;
    font-size: 13px;
  }
  .tdr-stat-inline { font-size: 15px; font-weight: 600; color: #1B4332; }

  /* ── Stat numbers ── */
  .mono { font-family: 'IBM Plex Mono', monospace; }

  /* ── Cards ── */
  .tdr-card {
    background: #FFFFFF;
    border: 1px solid #E8E8E4;
    border-radius: 12px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07);
    padding: 24px;
    margin-bottom: 16px;
  }

  /* ── Stat banner ── */
  .stat-banner {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 20px;
  }
  .stat-box {
    flex: 1;
    min-width: 120px;
    background: #FFFFFF;
    border: 1px solid #E8E8E4;
    border-radius: 12px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07);
    padding: 16px 20px;
    text-align: center;
  }
  .stat-box .stat-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6B7280;
    margin-bottom: 6px;
  }
  .stat-box .stat-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 28px;
    font-weight: 700;
    color: #1B4332;
  }

  /* ── Receipt ── */
  .receipt-wrap {
    background: #FFFFFF;
    border: 1px solid #E8E8E4;
    border-radius: 12px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07);
    padding: 28px 32px;
    max-width: 640px;
    margin: 0 auto 24px auto;
  }
  .receipt-header {
    text-align: center;
    border-bottom: 2px solid #E8E8E4;
    padding-bottom: 16px;
    margin-bottom: 20px;
  }
  .receipt-player {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 22px;
    font-weight: 700;
    color: #1A1A2E;
  }
  .receipt-meta {
    font-size: 13px;
    color: #6B7280;
    margin-top: 4px;
  }
  .receipt-meta .mono { color: #1B4332; }
  .tdr-receipt-emphasis { margin-top: 8px; font-weight: 600; color: #374151; }
  .tdr-pts-accent { color: #1B4332; }
  .receipt-line {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 6px 0;
    font-size: 13px;
    border-bottom: 1px solid #F3F3F0;
  }
  .receipt-line .line-desc { color: #374151; max-width: 78%; }
  .receipt-line .line-pts {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    color: #1B4332;
    white-space: nowrap;
  }
  .receipt-subtotal {
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px dashed #D1D5DB;
  }
  .receipt-subtotal-row {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    color: #6B7280;
    padding: 3px 0;
  }
  .receipt-subtotal-row .sub-val {
    font-family: 'IBM Plex Mono', monospace;
    color: #374151;
    font-weight: 500;
  }
  .receipt-divider {
    border: none;
    border-top: 2px solid #1A1A2E;
    margin: 16px 0;
  }
  .receipt-own-score {
    display: flex;
    justify-content: space-between;
    font-size: 15px;
    font-weight: 600;
    padding: 8px 0;
  }
  .receipt-own-score .own-val {
    font-family: 'IBM Plex Mono', monospace;
  }
  .receipt-total {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #F0FDF4;
    border: 2px solid #1B4332;
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 12px;
  }
  .receipt-total .total-label {
    font-size: 15px;
    font-weight: 700;
    color: #1B4332;
    letter-spacing: 0.03em;
    text-transform: uppercase;
  }
  .receipt-total .total-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 30px;
    font-weight: 700;
    color: #1B4332;
  }
  .receipt-footer {
    text-align: center;
    font-size: 11px;
    color: #9CA3AF;
    margin-top: 20px;
    padding-top: 12px;
    border-top: 1px solid #E8E8E4;
  }

  /* ── Leaderboard callout ── */
  .callout-card {
    background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%);
    border-radius: 12px;
    padding: 24px 28px;
    color: #FFFFFF;
    margin-bottom: 20px;
  }
  .callout-card .callout-label {
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    opacity: 0.75;
    margin-bottom: 6px;
  }
  .callout-card .callout-player {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 4px;
  }
  .callout-card .callout-meta {
    font-size: 13px;
    opacity: 0.85;
    margin-bottom: 14px;
  }
  .callout-card .callout-number {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 48px;
    font-weight: 700;
    line-height: 1;
  }
  .callout-card .callout-unit {
    font-size: 13px;
    opacity: 0.75;
    margin-top: 4px;
  }

  /* ── Warning / Error banners ── */
  .warn-banner {
    background: #FFFBEB;
    border: 1px solid #F59E0B;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    color: #92400E;
    margin-bottom: 16px;
  }
  .err-banner {
    background: #FEF2F2;
    border: 1px solid #C0392B;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    color: #7F1D1D;
    margin-bottom: 16px;
  }

  /* ── Sidebar ── */
  .sidebar-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 18px;
    font-weight: 700;
    color: #1B4332;
  }
  .sidebar-season {
    font-size: 12px;
    color: #6B7280;
    margin-top: 2px;
    margin-bottom: 12px;
  }
  .freshness-badge {
    display: inline-block;
    background: #F0FDF4;
    border: 1px solid #86EFAC;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    color: #166534;
    font-weight: 500;
  }
  .freshness-badge-warn {
    display: inline-block;
    background: #FFFBEB;
    border: 1px solid #FCD34D;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    color: #92400E;
    font-weight: 500;
  }

  /* ── Masthead (centered logo + primary nav) ── */
  .tdr-masthead-logo {
    text-align: center;
    margin: 4px 0 8px 0;
  }
  .tdr-masthead-logo img {
    max-height: clamp(40px, 14vw, 88px);
    width: auto;
    max-width: min(100%, 360px);
    height: auto;
    object-fit: contain;
    display: inline-block;
    vertical-align: middle;
  }
  hr.tdr-masthead-nav-sep {
    border: none;
    border-top: 3px double #1A1A2E;
    margin: 8px 0 12px 0;
    opacity: 0.88;
  }
  .tdr-masthead-spacer {
    margin-bottom: 16px;
    padding-bottom: 4px;
    border-bottom: 1px solid #E8E8E4;
  }

  /* Hide default multipage sidebar nav when using masthead (config + fallback) */
  [data-testid="stSidebarNav"] {
    display: none !important;
  }

  /* ── Mobile ── */
  @media (max-width: 480px) {
    .receipt-wrap { padding: 18px 16px; }
    .stat-box .stat-value { font-size: 22px; }
    .receipt-total .total-val { font-size: 24px; }
    .callout-card .callout-number { font-size: 36px; }
    .tdr-masthead-logo img {
      max-height: clamp(36px, 18vw, 72px);
    }
  }
</style>
"""

# Appended when user selects Dark mode in Streamlit Settings (st.context.theme.base == "dark")
DARK_THEME_CSS = """
<style>
  /* ── Dark theme (Streamlit Settings → Theme → Dark) ── */
  .tdr-page-title { color: #F9FAFB !important; }
  .tdr-subtitle, .tdr-muted, .tdr-caption { color: #9CA3AF !important; }
  .tdr-landing-tagline { color: #9CA3AF !important; }
  .tdr-landing-hint { color: #6B7280 !important; }
  .tdr-hero-title { color: #6EE7B7 !important; }
  .tdr-section-heading { color: #F9FAFB !important; }
  .tdr-filter-heading { color: #9CA3AF !important; }
  .tdr-running-total { color: #9CA3AF !important; }
  .tdr-receipt-alert { color: #F87171 !important; }
  .tdr-receipt-muted-box { color: #9CA3AF !important; }
  .tdr-stat-inline { color: #6EE7B7 !important; }

  .tdr-card, .stat-box, .receipt-wrap {
    background: #262730 !important;
    border-color: #3D3D4D !important;
    box-shadow: 0 1px 8px rgba(0,0,0,0.35) !important;
  }

  .stat-box .stat-label { color: #9CA3AF !important; }
  .stat-box .stat-value { color: #6EE7B7 !important; }

  .receipt-header { border-bottom-color: #3D3D4D !important; }
  .receipt-player { color: #F9FAFB !important; }
  .receipt-meta { color: #9CA3AF !important; }
  .receipt-meta .mono { color: #6EE7B7 !important; }
  .tdr-receipt-emphasis { color: #E8EAED !important; }
  .tdr-pts-accent { color: #6EE7B7 !important; }
  .receipt-line { border-bottom-color: #3D3D4D !important; }
  .receipt-line .line-desc { color: #D1D5DB !important; }
  .receipt-line .line-pts { color: #6EE7B7 !important; }
  .receipt-subtotal { border-top-color: #4B5563 !important; }
  .receipt-subtotal-row { color: #9CA3AF !important; }
  .receipt-subtotal-row .sub-val { color: #D1D5DB !important; }
  .receipt-divider { border-top-color: #9CA3AF !important; }
  .receipt-own-score { color: #E8EAED !important; }
  .receipt-total {
    background: rgba(16, 185, 129, 0.12) !important;
    border-color: #34D399 !important;
  }
  .receipt-total .total-label,
  .receipt-total .total-val { color: #6EE7B7 !important; }
  .receipt-footer { color: #6B7280 !important; border-top-color: #3D3D4D !important; }

  .callout-card {
    background: linear-gradient(135deg, #14532D 0%, #166534 100%) !important;
    color: #F9FAFB !important;
  }

  .warn-banner {
    background: #422006 !important;
    border-color: #D97706 !important;
    color: #FCD34D !important;
  }
  .err-banner {
    background: #450A0A !important;
    border-color: #DC2626 !important;
    color: #FECACA !important;
  }

  .sidebar-title { color: #6EE7B7 !important; }
  .sidebar-season { color: #9CA3AF !important; }
  .freshness-badge {
    background: rgba(16, 185, 129, 0.15) !important;
    border-color: #34D399 !important;
    color: #A7F3D0 !important;
  }
  .freshness-badge-warn {
    background: #422006 !important;
    border-color: #D97706 !important;
    color: #FCD34D !important;
  }

  hr.tdr-masthead-nav-sep {
    border-top-color: #6B7280 !important;
    opacity: 1 !important;
  }
  .tdr-masthead-spacer {
    border-bottom-color: #3D3D4D !important;
  }
</style>
"""


def _theme_is_dark() -> bool:
    """True when the user selects Dark in Streamlit Settings → Theme."""
    import streamlit as st

    try:
        theme = st.context.theme
        return theme is not None and getattr(theme, "base", None) == "dark"
    except Exception:
        return False


def plotly_layout_colors() -> dict[str, str]:
    """Paper/plot background and font color for Plotly to match Streamlit theme."""
    if _theme_is_dark():
        return {
            "paper_bgcolor": "#0E1117",
            "plot_bgcolor": "#262730",
            "font_color": "#E8EAED",
            "gridcolor": "#3D3D4D",
        }
    return {
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "font_color": "#1A1A2E",
        "gridcolor": "#F3F4F6",
    }


def inject_styles():
    """Call this at the top of every page to inject fonts + CSS."""
    import streamlit as st

    css = GOOGLE_FONTS + GLOBAL_CSS
    if _theme_is_dark():
        css += DARK_THEME_CSS
    st.markdown(css, unsafe_allow_html=True)


def render_app_banner(active: str | None = None) -> None:
    """
    NYT-style masthead: centered JAMN logo + one-tap primary nav.
    active: 'home' | 'player_log' | 'receipt' | 'leaderboard' | None
    """
    import streamlit as st

    if _LOGO_PATH.is_file():
        b64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
        st.markdown(
            f'<div class="tdr-masthead-logo">'
            f'<img src="data:image/png;base64,{b64}" alt="JAMN Sports Analytics" />'
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="tdr-masthead-nav-sep" />', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    nav = [
        (c1, "pages/01_Player_Log.py", "Player Log", "player_log"),
        (c2, "pages/02_The_Receipt.py", "The Receipt", "receipt"),
        (c3, "pages/03_Leaderboard.py", "Leaderboard", "leaderboard"),
    ]
    for col, page, label, key in nav:
        with col:
            st.page_link(
                page,
                label=label,
                use_container_width=True,
                disabled=(active == key),
            )

    st.markdown('<div class="tdr-masthead-spacer"></div>', unsafe_allow_html=True)


def stat_banner_html(stats: list[dict]) -> str:
    """
    Render a horizontal stat banner.
    stats = [{"label": "...", "value": "..."}, ...]
    """
    boxes = "".join(
        f'<div class="stat-box">'
        f'<div class="stat-label">{s["label"]}</div>'
        f'<div class="stat-value mono">{s["value"]}</div>'
        f'</div>'
        for s in stats
    )
    return f'<div class="stat-banner">{boxes}</div>'


def receipt_line_html(period: str, time_remaining: str, teammate: str,
                      shot_type: str, points: int) -> str:
    q_label = f"Q{period}" if str(period).isdigit() else period
    desc = f"{q_label} {time_remaining} — Assisted {teammate} → {shot_type}"
    pts_label = f"+{points} pt{'s' if points != 1 else ''}"
    return (
        f'<div class="receipt-line">'
        f'<span class="line-desc">{desc}</span>'
        f'<span class="line-pts">{pts_label}</span>'
        f'</div>'
    )


def callout_card_html(player: str, date: str, opponent: str,
                      result: str, total: int) -> str:
    return f"""
<div class="callout-card">
  <div class="callout-label">Season Leader — Total Points Touched</div>
  <div class="callout-player">{player}</div>
  <div class="callout-meta">{date} vs {opponent} &nbsp;·&nbsp; {result}</div>
  <div class="callout-number">{total}</div>
  <div class="callout-unit">Total Points Touched</div>
</div>
"""
