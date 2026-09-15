"""BlueSentra Streamlit design system — Calm Precision."""

from __future__ import annotations

import html
from datetime import UTC, datetime

import streamlit as st

# Tokens
CANVAS = "#F5F8FC"
SURFACE = "#FFFFFF"
BLUE_PRIMARY = "#2563EB"
DEEP_BLUE = "#15345B"
TEXT_MAIN = "#172B4D"
TEXT_MUTED = "#526580"
BORDER = "#E2EAF3"
SELECTED_BG = "#EAF2FF"

BYTE_UNITS_NOTE = (
    "Displayed sizes use decimal (SI) units: 1 KB = 1,000 bytes, 1 MB = 1,000,000 bytes. "
    "Raw byte counts from Zeek are shown when values are small."
)

FONT_STACK = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', "
    "Arial, sans-serif"
)
MONO_STACK = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"

SHIELD_MARK = """
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M12 2.5L5 5.8V11.2C5 15.8 8.1 20 12 20.8C15.9 20 19 15.8 19 11.2V5.8L12 2.5Z"
        stroke="#2563EB" stroke-width="1.5" fill="#EAF2FF"/>
</svg>
"""

ICON_LINK = """<svg class="bs-icon" viewBox="0 0 16 16" fill="none"><path d="M6 3h7v7M13 3L3 13" stroke="#2563EB" stroke-width="1.4" stroke-linecap="round"/></svg>"""
ICON_GLOBE = """<svg class="bs-icon" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5" stroke="#2563EB" stroke-width="1.3"/><path d="M3 8h10M8 3c1.5 1.8 1.5 8.2 0 10M8 3c-1.5 1.8-1.5 8.2 0 10" stroke="#2563EB" stroke-width="1.2"/></svg>"""
ICON_UP = """<svg class="bs-icon" viewBox="0 0 16 16" fill="none"><path d="M8 12V4M8 4L5 7M8 4l3 3" stroke="#2563EB" stroke-width="1.4" stroke-linecap="round"/></svg>"""
ICON_DOWN = """<svg class="bs-icon" viewBox="0 0 16 16" fill="none"><path d="M8 4v8M8 12l-3-3M8 12l3-3" stroke="#2563EB" stroke-width="1.4" stroke-linecap="round"/></svg>"""


def inject_global_styles() -> None:
    st.markdown(
        f"""
<style>
  :root {{
    --bs-canvas: {CANVAS};
    --bs-surface: {SURFACE};
    --bs-primary: {BLUE_PRIMARY};
    --bs-deep: {DEEP_BLUE};
    --bs-text: {TEXT_MAIN};
    --bs-muted: {TEXT_MUTED};
    --bs-border: {BORDER};
    --bs-selected: {SELECTED_BG};
  }}
  @media (prefers-reduced-motion: reduce) {{
    * {{ transition: none !important; animation: none !important; }}
  }}
  .stApp {{
    background-color: var(--bs-canvas);
    font-family: {FONT_STACK};
    color: var(--bs-text);
  }}
  [data-testid="stSidebar"] {{
    background: var(--bs-surface);
    border-right: 1px solid var(--bs-border);
  }}
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
  [data-testid="stSidebar"] label {{
    color: var(--bs-text);
  }}
  [data-testid="stSidebar"] div[role="radiogroup"] label {{
    border-radius: 10px;
    padding: 0.45rem 0.55rem;
    margin: 0.15rem 0;
    border: 1px solid transparent;
    transition: background-color 150ms ease, border-color 150ms ease;
  }}
  [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
    background: var(--bs-selected);
    border-color: var(--bs-border);
    font-weight: 600;
    color: var(--bs-deep);
  }}
  [data-testid="stSidebar"] div[role="radiogroup"] label:focus-within {{
    outline: 2px solid var(--bs-primary);
    outline-offset: 2px;
  }}
  .bs-brand-title {{
    color: var(--bs-deep);
    font-size: 1.02rem;
    font-weight: 650;
    margin: 0;
    letter-spacing: -0.01em;
  }}
  .bs-brand-sub {{
    color: var(--bs-muted);
    font-size: 0.76rem;
    margin: 0.12rem 0 0 0;
  }}
  .bs-sidebar-footer {{
    margin-top: 1.5rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--bs-border);
  }}
  .bs-env-pill {{
    display: inline-block;
    padding: 0.22rem 0.55rem;
    border-radius: 999px;
    background: var(--bs-canvas);
    border: 1px solid var(--bs-border);
    color: var(--bs-muted);
    font-size: 0.72rem;
  }}
  .bs-detail-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
    gap: 0.65rem 1.25rem;
    margin: 0.5rem 0 0.75rem 0;
  }}
  .bs-detail-item {{
    font-size: 0.84rem;
    line-height: 1.4;
  }}
  .bs-detail-k {{
    color: var(--bs-muted);
    font-size: 0.74rem;
    font-weight: 600;
    margin: 0 0 0.15rem 0;
  }}
  .bs-detail-v {{
    color: var(--bs-deep);
    margin: 0;
    font-variant-numeric: tabular-nums;
  }}
  .bs-detail-v.mono {{
    font-family: {MONO_STACK};
    font-size: 0.82rem;
  }}
  .bs-page-title {{
    color: var(--bs-deep);
    font-size: 1.55rem;
    font-weight: 650;
    margin: 0 0 0.35rem 0;
    letter-spacing: -0.02em;
  }}
  .bs-page-sub {{
    color: var(--bs-muted);
    font-size: 0.94rem;
    margin: 0 0 1.25rem 0;
    max-width: 52rem;
  }}
  .bs-context-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
    margin: 0 0 1.5rem 0;
  }}
  .bs-chip {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.65rem;
    border-radius: 10px;
    background: var(--bs-surface);
    border: 1px solid var(--bs-border);
    color: var(--bs-text);
    font-size: 0.8rem;
    box-shadow: 0 1px 2px rgba(21, 52, 91, 0.04);
  }}
  .bs-chip-label {{
    color: var(--bs-muted);
    font-weight: 500;
  }}
  .bs-chip-value {{
    color: var(--bs-deep);
    font-weight: 600;
  }}
  .bs-chip-utc {{
    background: var(--bs-selected);
    border-color: #D6E6FF;
  }}
  .bs-demo-badge {{
    display: inline-block;
    padding: 0.22rem 0.55rem;
    border-radius: 8px;
    background: #FFF8F1;
    color: #9A4B1A;
    border: 1px solid #F3DEC8;
    font-size: 0.74rem;
    font-weight: 600;
    margin-bottom: 0.45rem;
  }}
  .bs-section-label {{
    color: var(--bs-muted);
    font-size: 0.74rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    margin: 0 0 0.5rem 0;
  }}
  .bs-section-title {{
    color: var(--bs-deep);
    font-size: 1.02rem;
    font-weight: 650;
    margin: 1.75rem 0 0.35rem 0;
  }}
  .bs-metric-card {{
    background: var(--bs-surface);
    border: 1px solid var(--bs-border);
    border-radius: 16px;
    padding: 1rem 1.05rem;
    box-shadow: 0 1px 3px rgba(21, 52, 91, 0.05);
    min-height: 104px;
    transition: box-shadow 150ms ease;
  }}
  .bs-metric-card:hover {{
    box-shadow: 0 2px 8px rgba(21, 52, 91, 0.07);
  }}
  .bs-metric-head {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-bottom: 0.45rem;
  }}
  .bs-icon {{
    width: 14px;
    height: 14px;
    flex-shrink: 0;
  }}
  .bs-metric-label {{
    color: var(--bs-muted);
    font-size: 0.78rem;
    margin: 0;
    font-weight: 500;
  }}
  .bs-metric-value {{
    color: var(--bs-deep);
    font-size: 1.35rem;
    font-weight: 650;
    margin: 0;
    line-height: 1.15;
    font-variant-numeric: tabular-nums;
  }}
  .bs-help {{
    color: var(--bs-muted);
    font-size: 0.8rem;
    margin: 0.5rem 0 0 0;
    line-height: 1.45;
  }}
  .bs-freshness-panel {{
    background: var(--bs-surface);
    border: 1px solid var(--bs-border);
    border-radius: 14px;
    padding: 0.85rem 1rem 1rem 1rem;
    margin: 0 0 1.25rem 0;
    box-shadow: 0 1px 3px rgba(21, 52, 91, 0.04);
  }}
  .bs-table-shell {{
    margin-top: 0.35rem;
  }}
  div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 16px !important;
    border-color: var(--bs-border) !important;
    box-shadow: 0 1px 3px rgba(21, 52, 91, 0.04);
  }}
  .stButton > button {{
    border-radius: 10px;
    min-height: 2.35rem;
    transition: background-color 150ms ease, border-color 150ms ease;
  }}
  .stButton > button:focus-visible {{
    outline: 2px solid var(--bs-primary);
    outline-offset: 2px;
  }}
  .stButton > button[kind="primary"] {{
    background-color: var(--bs-primary);
    border: 1px solid #1D4ED8;
  }}
  .stButton > button[kind="primary"]:hover {{
    background-color: #1D4ED8;
  }}
  div[data-baseweb="select"] > div,
  div[data-baseweb="input"] > div {{
    border-radius: 10px !important;
    border-color: var(--bs-border) !important;
  }}
  [data-testid="stMainBlockContainer"] {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
  }}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    st.markdown(
        f"""
<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.25rem;">
  {SHIELD_MARK}
  <div>
    <p class="bs-brand-title">BlueSentra</p>
    <p class="bs-brand-sub">Network visibility</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer() -> None:
    st.markdown(
        """
<div class="bs-sidebar-footer">
  <span class="bs-env-pill">Local environment · 127.0.0.1 only</span>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_page_intro(*, title: str, subtitle: str, demo_badge: str | None = None) -> None:
    if demo_badge:
        st.markdown(
            f'<span class="bs-demo-badge">{html.escape(demo_badge)}</span>',
            unsafe_allow_html=True,
        )
    st.markdown(f'<h1 class="bs-page-title">{html.escape(title)}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="bs-page-sub">{html.escape(subtitle)}</p>', unsafe_allow_html=True)


def format_utc_display(moment: datetime | None) -> str:
    if moment is None:
        return "No imported events"
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def render_data_freshness_panel(
    *,
    scope_label: str,
    latest_event_display: str,
    latest_event_age: str,
    latest_ingestion_display: str,
    latest_ingestion_age: str,
    table_filter_note: str | None,
) -> None:
    note_html = ""
    if table_filter_note:
        note_html = (
            f'<p class="bs-help">{html.escape(table_filter_note)}</p>'
        )
    st.markdown(
        f"""
<div class="bs-freshness-panel">
  <p class="bs-section-label">Data freshness</p>
  <p class="bs-help">Scope: {html.escape(scope_label)}. Based on stored records only; duplicate-only imports are not reflected.</p>
  <div class="bs-detail-grid">
    <div class="bs-detail-item">
      <p class="bs-detail-k">Latest observed activity</p>
      <p class="bs-detail-v">{html.escape(latest_event_display)}</p>
      <p class="bs-help">{html.escape(latest_event_age)}</p>
    </div>
    <div class="bs-detail-item">
      <p class="bs-detail-k">Latest stored-event ingestion</p>
      <p class="bs-detail-v">{html.escape(latest_ingestion_display)}</p>
      <p class="bs-help">{html.escape(latest_ingestion_age)}</p>
    </div>
  </div>
  {note_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def render_context_bar(
    *,
    customer: str,
    site: str,
    sensor: str,
    utc_window: str,
    last_refresh: datetime | None,
) -> bool:
    """Context chips + refresh. Returns True if refresh clicked."""
    st.markdown(
        f"""
<div class="bs-context-bar">
  <span class="bs-chip"><span class="bs-chip-label">Customer</span>
    <span class="bs-chip-value">{html.escape(customer)}</span></span>
  <span class="bs-chip"><span class="bs-chip-label">Site</span>
    <span class="bs-chip-value">{html.escape(site)}</span></span>
  <span class="bs-chip"><span class="bs-chip-label">Sensor</span>
    <span class="bs-chip-value">{html.escape(sensor)}</span></span>
  <span class="bs-chip bs-chip-utc"><span class="bs-chip-label">UTC</span>
    <span class="bs-chip-value">{html.escape(utc_window)}</span></span>
</div>
        """,
        unsafe_allow_html=True,
    )
    meta_col, btn_col = st.columns([3, 1])
    with meta_col:
        if last_refresh is not None:
            st.caption(
                "Last refreshed: "
                + last_refresh.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            )
    with btn_col:
        return st.button("Refresh", type="primary", use_container_width=True)
    return False


def format_bytes(value: int | None) -> str:
    if value is None:
        return "—"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} GB"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f} MB"
    if value >= 1_000:
        return f"{value / 1_000:.1f} KB"
    return f"{value} B"


def render_metric_card(label: str, value: str, icon_svg: str, *, help_text: str | None = None) -> None:
    title_attr = f' title="{html.escape(help_text)}"' if help_text else ""
    st.markdown(
        f"""
<div class="bs-metric-card"{title_attr}>
  <div class="bs-metric-head">{icon_svg}<p class="bs-metric-label">{html.escape(label)}</p></div>
  <p class="bs-metric-value">{html.escape(value)}</p>
</div>
        """,
        unsafe_allow_html=True,
    )


# Backward-compatible alias
page_header = render_page_intro
