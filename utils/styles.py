"""
Shared CSS and card HTML templates for Triple Double Receipt.
NYT Games aesthetic — IBM Plex Mono for numbers, Inter for body.
"""

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

  /* ── Mobile ── */
  @media (max-width: 480px) {
    .receipt-wrap { padding: 18px 16px; }
    .stat-box .stat-value { font-size: 22px; }
    .receipt-total .total-val { font-size: 24px; }
    .callout-card .callout-number { font-size: 36px; }
  }
</style>
"""


def inject_styles():
    """Call this at the top of every page to inject fonts + CSS."""
    import streamlit as st
    st.markdown(GOOGLE_FONTS + GLOBAL_CSS, unsafe_allow_html=True)


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
