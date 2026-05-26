"""
PsO Market Access Intelligence — Client Dashboard
A consulting-style Streamlit dashboard built on extracted prior-authorization
policy data, focused on TREMFYA vs. STELARA in plaque psoriasis.

To run:
    streamlit run app.py

Dependencies (also see requirements.txt):
    streamlit, pandas, numpy, plotly, openpyxl
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Optional, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================================
#  PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="PsO Market Access Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
#  DESIGN SYSTEM
# ============================================================================

# Core palette — clean dashboard, not editorial document
INK         = "#1F2937"
INK_SOFT    = "#4B5563"
SLATE       = "#6B7280"
LINE        = "#E5E7EB"
LINE_SOFT   = "#F1EFE9"
PAPER       = "#FBFAF6"   # soft warm white background
CARD        = "#FFFFFF"
NAVY        = "#1E293B"   # sidebar
AMBER       = "#D97706"   # accent
AMBER_SOFT  = "#FBBF24"

# Brand-specific palette — used consistently across every chart
TREMFYA_C       = "#047857"  # deep emerald
TREMFYA_LIGHT   = "#10B981"
STELARA_C       = "#6D28D9"  # deep violet
STELARA_LIGHT   = "#A78BFA"
OTHER_C         = "#94A3B8"  # muted slate for context brands

BRAND_COLORS = {
    "TREMFYA": TREMFYA_C,
    "STELARA": STELARA_C,
}

FOCUS_BRANDS = ["TREMFYA", "STELARA"]

# Access tier semantics (kept simple — restrictive vs moderate vs open)
ACCESS_TIER_ORDER = ["Highly Restrictive", "Restricted", "Moderate", "Open", "Highly Open"]
ACCESS_TIER_COLOR = {
    "Highly Restrictive": "#B91C1C",
    "Restricted":         "#EA580C",
    "Moderate":           "#CA8A04",
    "Open":               "#16A34A",
    "Highly Open":        "#047857",
    "Unscored":           "#94A3B8",
}

# Plotly base layout (NO `title` key — always set chart titles via Streamlit
# headers, never via Plotly, to avoid any "undefined" rendering)
PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Manrope, -apple-system, BlinkMacSystemFont, sans-serif",
              color=INK, size=13),
    margin=dict(l=10, r=10, t=20, b=10),
    xaxis=dict(showgrid=False, linecolor=LINE, ticks="outside",
               tickcolor=LINE, tickfont=dict(color=INK_SOFT, size=11)),
    yaxis=dict(gridcolor="#F0EDE5", linecolor=LINE, ticks="outside",
               tickcolor=LINE, zeroline=False,
               tickfont=dict(color=INK_SOFT, size=11)),
    legend=dict(font=dict(size=11, color=INK_SOFT), bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=LINE, font_family="Manrope",
                    font_color=INK),
)


def apply_layout(fig: go.Figure, **overrides) -> go.Figure:
    """Merge PLOTLY_BASE with chart-specific overrides (shallow merge on dicts)."""
    merged = {k: (dict(v) if isinstance(v, dict) else v) for k, v in PLOTLY_BASE.items()}
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v
    fig.update_layout(**merged)
    return fig


# ---------------------------------------------------------------------------- 
#  CSS — focused, dashboard-style (not document-style)
# ---------------------------------------------------------------------------- 
CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Manrope:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], button, input, select, textarea {{
    font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: {INK};
}}

.stApp {{
    background: {PAPER};
    color: {INK};
}}

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}

section.main > div.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 4rem;
    max-width: 1380px;
}}

/* ---------- Compact masthead ---------- */
.zs-masthead {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding-bottom: 14px;
    margin-bottom: 18px;
    border-bottom: 1px solid {LINE};
}}
.zs-masthead-left .eyebrow {{
    font-size: 10.5px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: {AMBER};
    font-weight: 700;
    margin-bottom: 4px;
}}
.zs-masthead-left h1 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 600;
    font-size: 30px;
    line-height: 1.15;
    letter-spacing: -0.015em;
    color: {INK};
    margin: 0 0 4px 0;
}}
.zs-masthead-left .deck {{
    font-size: 13px;
    color: {INK_SOFT};
    max-width: 700px;
    line-height: 1.45;
}}
.zs-masthead-right {{
    text-align: right;
    font-size: 11px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: {SLATE};
    font-weight: 500;
}}
.zs-masthead-right .pill {{
    display: inline-block;
    padding: 4px 10px;
    background: {NAVY};
    color: {PAPER};
    margin-left: 6px;
    border-radius: 2px;
    font-weight: 600;
    font-size: 10px;
    letter-spacing: 0.12em;
}}

/* ---------- Section heading ---------- */
.zs-h2 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 600;
    font-size: 21px;
    line-height: 1.2;
    letter-spacing: -0.01em;
    color: {INK};
    margin: 30px 0 4px 0;
}}
.zs-h2-deck {{
    font-size: 13px;
    color: {INK_SOFT};
    line-height: 1.5;
    margin-bottom: 16px;
    max-width: 820px;
}}

/* Question prompt above each chart — gives the consulting voice */
.zs-question {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 16px;
    font-weight: 500;
    font-style: italic;
    color: {INK};
    margin: 18px 0 4px 0;
    line-height: 1.4;
}}

/* ---------- KPI cards (Streamlit-native containers + custom CSS) ---------- */
.zs-kpi {{
    background: {CARD};
    border: 1px solid {LINE};
    border-radius: 4px;
    padding: 14px 16px;
    height: 100%;
    position: relative;
}}
.zs-kpi-accent {{
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: {AMBER};
    border-radius: 4px 0 0 4px;
}}
.zs-kpi-accent.tremfya {{ background: {TREMFYA_C}; }}
.zs-kpi-accent.stelara {{ background: {STELARA_C}; }}
.zs-kpi-accent.neutral {{ background: {SLATE}; }}

.zs-kpi-label {{
    font-size: 10.5px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {SLATE};
    font-weight: 600;
    margin-bottom: 6px;
}}
.zs-kpi-value {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 30px;
    font-weight: 600;
    line-height: 1.05;
    color: {INK};
    letter-spacing: -0.02em;
}}
.zs-kpi-value .unit {{
    font-size: 13px;
    color: {SLATE};
    font-family: 'Manrope', sans-serif !important;
    font-weight: 500;
    margin-left: 4px;
}}
.zs-kpi-foot {{
    font-size: 11.5px;
    color: {INK_SOFT};
    margin-top: 8px;
    line-height: 1.4;
    min-height: 1.4em;
}}

/* ---------- Observation tiles ---------- */
.zs-obs {{
    background: {CARD};
    border: 1px solid {LINE};
    border-left: 3px solid {AMBER};
    border-radius: 3px;
    padding: 14px 16px;
    height: 100%;
}}
.zs-obs.tremfya {{ border-left-color: {TREMFYA_C}; }}
.zs-obs.stelara {{ border-left-color: {STELARA_C}; }}
.zs-obs.neutral {{ border-left-color: {SLATE}; }}
.zs-obs-tag {{
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {AMBER};
    font-weight: 700;
    margin-bottom: 6px;
}}
.zs-obs.tremfya .zs-obs-tag {{ color: {TREMFYA_C}; }}
.zs-obs.stelara .zs-obs-tag {{ color: {STELARA_C}; }}
.zs-obs.neutral .zs-obs-tag {{ color: {SLATE}; }}
.zs-obs-text {{
    font-size: 13.5px;
    color: {INK};
    line-height: 1.55;
}}
.zs-obs-text b {{ color: {INK}; font-weight: 700; }}

/* ---------- Scorecard ---------- */
.zs-scorecard {{
    background: {CARD};
    border: 1px solid {LINE};
    border-top: 4px solid {TREMFYA_C};
    padding: 18px 20px;
    border-radius: 3px;
}}
.zs-scorecard.stelara {{ border-top-color: {STELARA_C}; }}
.zs-scorecard h3 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 22px;
    font-weight: 600;
    margin: 0;
    color: {INK};
    letter-spacing: -0.01em;
}}
.zs-scorecard .brand-strap {{
    font-size: 11px;
    color: {SLATE};
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 4px;
}}
.zs-scorecard .strap.tremfya {{ color: {TREMFYA_C}; }}
.zs-scorecard .strap.stelara {{ color: {STELARA_C}; }}

.zs-scorecard table {{
    width: 100%;
    margin-top: 14px;
    border-collapse: collapse;
}}
.zs-scorecard table td {{
    padding: 8px 0;
    border-bottom: 1px dashed {LINE};
    font-size: 13px;
    color: {INK};
}}
.zs-scorecard table tr:last-child td {{ border-bottom: none; }}
.zs-scorecard table td.label {{
    color: {INK_SOFT};
}}
.zs-scorecard table td.value {{
    text-align: right;
    font-weight: 600;
    color: {INK};
    font-variant-numeric: tabular-nums;
}}

/* ---------- Detail field ---------- */
.zs-field {{
    background: {CARD};
    border: 1px solid {LINE};
    border-radius: 3px;
    padding: 12px 14px;
    margin-bottom: 8px;
}}
.zs-field-label {{
    font-size: 10.5px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {SLATE};
    font-weight: 600;
    margin-bottom: 4px;
}}
.zs-field-value {{
    font-size: 13.5px;
    color: {INK};
    line-height: 1.5;
}}
.zs-field-value.mono {{
    font-family: 'Manrope', sans-serif;
    font-size: 12.5px;
    color: {INK_SOFT};
}}

/* ---------- Tabs ---------- */
div[data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 1px solid {LINE};
    background: transparent;
    padding-left: 0;
}}
button[data-baseweb="tab"] {{
    font-family: 'Manrope', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.02em !important;
    color: {SLATE} !important;
    background: transparent !important;
    padding: 12px 22px !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    margin-right: 2px;
}}
button[data-baseweb="tab"]:hover {{
    color: {INK} !important;
    background: rgba(217, 119, 6, 0.04) !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {INK} !important;
    border-bottom-color: {AMBER} !important;
    background: transparent !important;
}}
div[data-baseweb="tab-panel"] {{
    padding-top: 18px;
}}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {NAVY} 0%, #0F172A 100%);
}}
section[data-testid="stSidebar"] * {{
    color: #E5E7EB !important;
}}
section[data-testid="stSidebar"] label {{
    color: #FCD34D !important;
    font-size: 10.5px !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    font-weight: 700 !important;
}}
.zs-side-brand {{
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 18px;
}}
.zs-side-brand .eyebrow {{
    font-size: 10px;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: {AMBER_SOFT} !important;
    font-weight: 700;
    margin-bottom: 4px;
}}
.zs-side-brand .title {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 22px;
    font-weight: 600;
    color: #FFFFFF !important;
    line-height: 1.2;
}}
.zs-side-brand .strap {{
    font-size: 11.5px;
    color: rgba(229,231,235,0.65) !important;
    line-height: 1.4;
    margin-top: 6px;
}}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background-color: rgba(255,255,255,0.06) !important;
    border-color: rgba(255,255,255,0.15) !important;
    color: #FFFFFF !important;
}}
section[data-testid="stSidebar"] [data-baseweb="tag"] {{
    background-color: {AMBER} !important;
    color: {NAVY} !important;
}}
section[data-testid="stSidebar"] [data-baseweb="tag"] span {{
    color: {NAVY} !important;
    font-weight: 700;
}}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div {{
    background-color: {AMBER_SOFT} !important;
}}
section[data-testid="stSidebar"] [data-testid="stCheckbox"] label,
section[data-testid="stSidebar"] [data-testid="stToggle"] label {{
    color: #E5E7EB !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    font-weight: 500 !important;
    font-size: 13px !important;
}}

.zs-side-footer {{
    margin-top: 22px;
    padding-top: 14px;
    border-top: 1px solid rgba(255,255,255,0.1);
    font-size: 11px;
    color: rgba(229,231,235,0.55) !important;
    line-height: 1.5;
}}

/* ---------- Dataframe / table ---------- */
[data-testid="stDataFrame"] {{
    border: 1px solid {LINE};
    border-radius: 3px;
    background: {CARD};
}}

/* ---------- Expander ---------- */
.streamlit-expanderHeader {{
    font-family: 'Manrope', sans-serif !important;
    font-weight: 600 !important;
    color: {INK} !important;
    background: {CARD} !important;
    border: 1px solid {LINE} !important;
    border-radius: 3px !important;
}}

/* ---------- Plotly hover tweaks ---------- */
.js-plotly-plot .plotly .modebar {{ display: none !important; }}

/* ---------- Footer ---------- */
.zs-footer {{
    margin-top: 56px;
    padding-top: 16px;
    border-top: 1px solid {LINE};
    font-size: 11px;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: {SLATE};
    display: flex;
    justify-content: space-between;
}}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================================
#  DATA LOADING
# ============================================================================

DEFAULT_PATHS = [
    "PA_Gold_Standard_Dataset_v5.xlsx",
    "data/PA_Gold_Standard_Dataset_v5.xlsx",
    "./PA_Gold_Standard_Dataset_v5.xlsx",
    "/mnt/user-data/uploads/PA_Gold_Standard_Dataset_v5.xlsx",
]
SHEET_NAME = "Gold Standard"


def find_local_file() -> Optional[str]:
    for p in DEFAULT_PATHS:
        if Path(p).exists():
            return p
    return None


@st.cache_data(show_spinner=False)
def load_workbook_bytes(source_bytes: bytes, _label: str = "") -> Optional[pd.DataFrame]:
    """Read the Gold Standard sheet from raw xlsx bytes."""
    buf = io.BytesIO(source_bytes)
    try:
        return pd.read_excel(buf, sheet_name=SHEET_NAME, engine="openpyxl")
    except ValueError:
        buf.seek(0)
        return pd.read_excel(buf, engine="openpyxl")


def _read_source_bytes(source) -> Optional[bytes]:
    if source is None:
        return None
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes()
    if hasattr(source, "getvalue"):
        return source.getvalue()
    if hasattr(source, "read"):
        return source.read()
    return None


def load_with_friendly_errors(source, label: str) -> Optional[pd.DataFrame]:
    try:
        raw = _read_source_bytes(source)
        if raw is None:
            return None
        return load_workbook_bytes(raw, label)
    except ImportError as e:
        st.error(
            "**Missing dependency.** This deployment cannot read `.xlsx` because "
            "`openpyxl` is not installed.\n\n"
            "**Fix:** add the following to your `requirements.txt` and redeploy:\n\n"
            "```\nstreamlit>=1.32\npandas>=2.0\nnumpy>=1.24\nplotly>=5.18\nopenpyxl>=3.1\n```\n\n"
            f"(Underlying error: `{e}`)"
        )
        st.stop()
    except Exception as e:
        st.error(f"Could not read the workbook ({label}). Details: `{e}`")
        st.stop()


# ============================================================================
#  DATA PREPARATION
# ============================================================================

def _parse_duration(v):
    if pd.isna(v):
        return np.nan
    s = str(v).strip()
    if s == "" or s.lower() in {"unspecified", "n/a", "na", "none", "nan"}:
        return np.nan
    m = re.match(r"^\s*(\d+(?:\.\d+)?)", s)
    if m:
        try: return float(m.group(1))
        except: return np.nan
    return np.nan


def _yes_no(v):
    if pd.isna(v):
        return "Not specified"
    s = str(v).strip().lower()
    if s in {"yes", "y", "true"}: return "Yes"
    if s in {"no", "n", "false"}: return "No"
    return "Not specified"


def _has_text(v) -> bool:
    if pd.isna(v): return False
    s = str(v).strip()
    if s == "" or s.lower() in {"no", "none", "n/a", "na", "unspecified", "not specified", "nan"}:
        return False
    return len(s) > 3


def access_tier(score) -> str:
    if pd.isna(score): return "Unscored"
    s = float(score)
    if s <= 25: return "Highly Restrictive"
    if s <= 40: return "Restricted"
    if s <= 55: return "Moderate"
    if s <= 70: return "Open"
    return "Highly Open"


@st.cache_data(show_spinner=False)
def prepare(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()

    str_cols = [c for c in df.columns
                if df[c].dtype == object or pd.api.types.is_string_dtype(df[c])]
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip().replace(
            {"nan": np.nan, "NaN": np.nan, "None": np.nan, "": np.nan}
        )

    df["Brand"] = df["Brand"].fillna("Unknown").astype(str).str.upper()

    df["Access Score"] = pd.to_numeric(df["Access Score"], errors="coerce")
    df["Access Tier"]  = df["Access Score"].apply(access_tier)

    df["Initial Auth (months)"] = df["Initial Authorization Duration(in-months)"].apply(_parse_duration)
    df["Reauth (months)"]       = df["Reauthorization Duration(in-months)"].apply(_parse_duration)

    df["TB Test"]            = df["TB Test required"].apply(_yes_no)
    df["Phototherapy Step"]  = df["Step through-Phototherapy"].apply(_yes_no)
    df["Reauthorization"]    = df["Reauthorization Required"].apply(
        lambda v: "Required" if str(v).strip().lower() == "yes" else "Not specified"
    )

    def qlim_flag(v):
        if pd.isna(v): return "Not specified"
        s = str(v).strip().lower()
        if s == "no": return "No"
        if s == "yes" or len(str(v).strip()) > 10: return "Yes"
        return "Not specified"
    df["Quantity Limit"] = df["Quantity Limits"].apply(qlim_flag)

    df["Step Therapy"] = df["Step Therapy Requirements Documented in Policy"].apply(
        lambda v: "Required" if _has_text(v) else "Not documented"
    )

    df["Brand Steps"]   = pd.to_numeric(df["Number of Steps through Brands"], errors="coerce")
    df["Generic Steps"] = pd.to_numeric(df["Number of Steps through Generic"], errors="coerce")
    df["Total Steps"]   = df[["Brand Steps", "Generic Steps"]].sum(axis=1, min_count=1)

    df["Specialist Required"] = df["Specialist Types"].apply(
        lambda v: "Required" if _has_text(v) else "Not specified"
    )
    df["Specialist Detail"] = df["Specialist Types"].fillna("—")
    df["Age Criterion"]     = df["Age"].fillna("Not specified")

    df["Policy ID"] = df["Filename"].astype(str).str.replace(".pdf", "", regex=False)
    uniq = df["Policy ID"].drop_duplicates().reset_index(drop=True)
    rank_map = {pid: i + 1 for i, pid in enumerate(uniq)}
    df["Policy #"] = df["Policy ID"].map(rank_map).apply(lambda i: f"Policy {i:02d}")

    return df


# ============================================================================
#  ANALYSIS HELPERS
# ============================================================================

# Each restriction is (column, value-meaning-restricted, display label)
RESTRICTION_DEFS = [
    ("Step Therapy",        "Required",     "Step therapy required"),
    ("TB Test",             "Yes",          "TB test required"),
    ("Quantity Limit",      "Yes",          "Quantity limit imposed"),
    ("Specialist Required", "Required",     "Specialist prescriber required"),
    ("Phototherapy Step",   "Yes",          "Phototherapy step required"),
    ("Reauthorization",     "Required",     "Reauthorization required"),
]


def restriction_share(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(df)
    if n == 0:
        return pd.DataFrame(columns=["Restriction", "Count", "Share"])
    for col, val, label in RESTRICTION_DEFS:
        c = int((df[col] == val).sum())
        rows.append({"Restriction": label, "Count": c, "Share": c / n})
    return pd.DataFrame(rows)


def restriction_by_brand(df: pd.DataFrame, brands: List[str]) -> pd.DataFrame:
    rows = []
    for b in brands:
        sub = df[df["Brand"] == b]
        n = len(sub)
        for col, val, label in RESTRICTION_DEFS:
            share = (sub[col] == val).mean() if n else 0
            rows.append({"Brand": b, "Restriction": label, "Share": share, "Count": int((sub[col] == val).sum()), "N": n})
    return pd.DataFrame(rows)


def kpi_card(col, label: str, value: str, foot: str = "", flavor: str = ""):
    """Render a single KPI card inside a Streamlit column."""
    accent_cls = flavor if flavor in ("tremfya", "stelara", "neutral") else ""
    col.markdown(
        f"""
<div class="zs-kpi">
  <div class="zs-kpi-accent {accent_cls}"></div>
  <div class="zs-kpi-label">{label}</div>
  <div class="zs-kpi-value">{value}</div>
  <div class="zs-kpi-foot">{foot}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def observation_tile(col, tag: str, html: str, flavor: str = ""):
    cls = "zs-obs"
    if flavor in ("tremfya", "stelara", "neutral"):
        cls += f" {flavor}"
    col.markdown(
        f"""
<div class="{cls}">
  <div class="zs-obs-tag">{tag}</div>
  <div class="zs-obs-text">{html}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def section_h2(title: str, deck: str = ""):
    st.markdown(f'<div class="zs-h2">{title}</div>', unsafe_allow_html=True)
    if deck:
        st.markdown(f'<div class="zs-h2-deck">{deck}</div>', unsafe_allow_html=True)


def question(text: str):
    """Render the consulting-style 'business question' prompt above each chart."""
    st.markdown(f'<div class="zs-question">{text}</div>', unsafe_allow_html=True)


# ============================================================================
#  DATA INGESTION
# ============================================================================

# Sidebar branding
st.sidebar.markdown(
    f"""
<div class="zs-side-brand">
  <div class="eyebrow">ZS · Market Access</div>
  <div class="title">PsO Policy Lens</div>
  <div class="strap">Prior-authorization intelligence for the plaque-psoriasis market.</div>
</div>
""",
    unsafe_allow_html=True,
)

local_path = find_local_file()
df_raw: Optional[pd.DataFrame] = None

if local_path is not None:
    df_raw = load_with_friendly_errors(local_path, local_path)
else:
    st.sidebar.markdown("##### Upload data")
    upl = st.sidebar.file_uploader(
        "Gold-standard extract",
        type=["xlsx"],
        help="Expecting the Gold Standard sheet from the PA extraction workbook.",
        label_visibility="collapsed",
    )
    if upl is not None:
        df_raw = load_with_friendly_errors(upl, upl.name)

if df_raw is None:
    st.warning("Upload the gold-standard workbook from the sidebar to begin.")
    st.stop()

df_all = prepare(df_raw)


# ============================================================================
#  SIDEBAR — Brand focus + filters
# ============================================================================

st.sidebar.markdown("**Brand focus**")
brand_mode = st.sidebar.radio(
    "Brand focus",
    options=["TREMFYA + STELARA (default)", "TREMFYA only", "STELARA only", "All brands"],
    index=0,
    label_visibility="collapsed",
)

mode_to_brands = {
    "TREMFYA + STELARA (default)": ["TREMFYA", "STELARA"],
    "TREMFYA only":                 ["TREMFYA"],
    "STELARA only":                 ["STELARA"],
    "All brands":                   sorted(df_all["Brand"].unique().tolist()),
}
focus_brands = mode_to_brands[brand_mode]

include_context = st.sidebar.toggle(
    "Show other brands as context",
    value=False,
    help="When on, charts show non-focus brands in muted gray for context.",
)

st.sidebar.markdown("**Access score range**")
score_lo, score_hi = int(df_all["Access Score"].min()), int(df_all["Access Score"].max())
score_range = st.sidebar.slider(
    "Access score range",
    min_value=score_lo, max_value=score_hi,
    value=(score_lo, score_hi), step=5,
    label_visibility="collapsed",
)

st.sidebar.markdown("**Filter by access tier**")
tier_options = [t for t in ACCESS_TIER_ORDER if t in df_all["Access Tier"].unique()]
selected_tiers = st.sidebar.multiselect(
    "Filter by access tier",
    options=tier_options,
    default=tier_options,
    label_visibility="collapsed",
)

st.sidebar.markdown(
    f"""
<div class="zs-side-footer">
Filters apply across all sections. Brand focus controls which brands appear as the
primary lens; toggling on "context" adds other brands as muted reference points.
<br><br>
<b>{df_all["Policy ID"].nunique()}</b> policies · <b>{df_all["Brand"].nunique()}</b> brands · <b>{len(df_all)}</b> brand-policy rows
</div>
""",
    unsafe_allow_html=True,
)

# Apply filters — build two views:
#   df_focus: rows from focus brands only (use for primary visuals)
#   df_context: focus + other brands, used when 'include context' is on
base_mask = df_all["Access Score"].between(score_range[0], score_range[1]) & \
            df_all["Access Tier"].isin(selected_tiers)

df_focus   = df_all[base_mask & df_all["Brand"].isin(focus_brands)].copy()
df_context = df_all[base_mask].copy()

if df_focus.empty:
    st.warning("No rows match the current filters. Loosen them from the sidebar to continue.")
    st.stop()


# ============================================================================
#  MASTHEAD
# ============================================================================

st.markdown(
    f"""
<div class="zs-masthead">
  <div class="zs-masthead-left">
    <div class="eyebrow">Plaque Psoriasis · Market Access Intelligence</div>
    <h1>How payers manage access to TREMFYA and STELARA</h1>
    <div class="deck">A consultant view of prior-authorization signals extracted from {df_all['Policy ID'].nunique()} payer policy documents — quantifying restriction patterns and access differentials between the two market-leading biologics in plaque psoriasis.</div>
  </div>
  <div class="zs-masthead-right">
    Focus brands<span class="pill">TREMFYA</span><span class="pill">STELARA</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================================
#  TABS
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Executive Summary",
    "Brand Comparison",
    "Parameter-Level Insights",
    "Policy Deep Dive",
])


# ----------------------------------------------------------------------------
#  TAB 1 — EXECUTIVE SUMMARY
# ----------------------------------------------------------------------------
with tab1:

    # ----- KPI strip -----
    tremfya_df = df_focus[df_focus["Brand"] == "TREMFYA"]
    stelara_df = df_focus[df_focus["Brand"] == "STELARA"]

    n_policies_focus = df_focus["Policy ID"].nunique()
    tremfya_mean = tremfya_df["Access Score"].mean() if len(tremfya_df) else np.nan
    stelara_mean = stelara_df["Access Score"].mean() if len(stelara_df) else np.nan
    overall_mean = df_focus["Access Score"].mean()
    pct_restricted = (df_focus["Access Tier"].isin(["Highly Restrictive", "Restricted"])).mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Policies in focus", f"{n_policies_focus}",
             foot=f"Across {len(focus_brands)} brand(s), {len(df_focus)} observations", flavor="neutral")
    kpi_card(c2, "TREMFYA · mean access score",
             f"{tremfya_mean:.1f}" if not np.isnan(tremfya_mean) else "—",
             foot=f"{len(tremfya_df)} policies covered", flavor="tremfya")
    kpi_card(c3, "STELARA · mean access score",
             f"{stelara_mean:.1f}" if not np.isnan(stelara_mean) else "—",
             foot=f"{len(stelara_df)} policies covered", flavor="stelara")
    kpi_card(c4, "Share scoring restrictive", f"{pct_restricted:.0f}<span class='unit'>%</span>",
             foot="Policies with score ≤ 40 — material barriers to start")

    # ----- Hero: access score positioning -----
    section_h2(
        "Access Overview",
        "Where every TREMFYA and STELARA policy sits on the 0–80 access spectrum. "
        "Each dot is one policy; brand-mean markers anchor the comparison."
    )
    question("How does payer access differ between TREMFYA and STELARA across the policy corpus?")

    plot_df = df_context.copy() if include_context else df_focus.copy()
    plot_df = plot_df.dropna(subset=["Access Score"]).copy()
    plot_df["Color group"] = plot_df["Brand"].apply(
        lambda b: b if b in focus_brands else "Other brands"
    )

    # Build the hero strip plot
    cat_order = focus_brands + (["Other brands"] if include_context and "Other brands" in plot_df["Color group"].values else [])
    color_map = {b: BRAND_COLORS.get(b, OTHER_C) for b in focus_brands}
    color_map["Other brands"] = OTHER_C

    fig_hero = px.strip(
        plot_df,
        x="Access Score",
        y="Color group",
        color="Color group",
        color_discrete_map=color_map,
        category_orders={"Color group": cat_order},
        hover_data={"Brand": True, "Policy #": True, "Access Score": True,
                    "Access Tier": True, "Color group": False},
        stripmode="overlay",
    )
    fig_hero.update_traces(
        jitter=0.45,
        marker=dict(size=13, opacity=0.85, line=dict(color="#FFFFFF", width=1)),
    )

    # Overlay brand means as crisp lines
    for b in focus_brands:
        bsub = plot_df[plot_df["Brand"] == b]
        if len(bsub):
            m = bsub["Access Score"].mean()
            fig_hero.add_trace(go.Scatter(
                x=[m, m],
                y=[b, b],
                mode="markers",
                marker=dict(symbol="line-ns", color=INK, size=28,
                            line=dict(width=3, color=INK)),
                name=f"{b} mean",
                hovertemplate=f"<b>{b} mean</b><br>%{{x:.1f}}<extra></extra>",
                showlegend=False,
            ))
            fig_hero.add_annotation(
                x=m, y=b,
                text=f"<b>{m:.1f}</b>",
                showarrow=False,
                yshift=22,
                font=dict(color=INK, size=12, family="Manrope"),
            )

    apply_layout(
        fig_hero,
        height=max(280, 90 * len(cat_order) + 80),
        xaxis=dict(range=[-5, 85], title="Access Score (0 = most restrictive, 80 = most open)",
                   title_font=dict(size=12, color=INK_SOFT)),
        yaxis=dict(title="", showgrid=False),
        showlegend=False,
    )
    st.plotly_chart(fig_hero, use_container_width=True, config={"displayModeBar": False})

    # ----- Key observations -----
    section_h2("Key Observations")

    # Build observations dynamically from the data
    obs_cols = st.columns(3)

    if not np.isnan(tremfya_mean) and not np.isnan(stelara_mean):
        gap = tremfya_mean - stelara_mean
        direction = "more open" if gap > 0 else "more restricted"
        observation_tile(
            obs_cols[0], "Access Differential",
            f"<b>TREMFYA scores {abs(gap):.1f} points {direction}</b> than STELARA on average "
            f"({tremfya_mean:.0f} vs. {stelara_mean:.0f}). The gap is modest but consistent "
            f"across the corpus.",
            flavor="tremfya" if gap > 0 else "stelara",
        )

    # Variability story
    if len(tremfya_df) and len(stelara_df):
        t_range = tremfya_df["Access Score"].max() - tremfya_df["Access Score"].min()
        s_range = stelara_df["Access Score"].max() - stelara_df["Access Score"].min()
        observation_tile(
            obs_cols[1], "Within-Brand Variability",
            f"Both brands span the full restriction spectrum (TREMFYA: {t_range:.0f}-point range, "
            f"STELARA: {s_range:.0f}-point range). <b>Payer choice drives access more than "
            f"brand choice</b> — account-level negotiation matters.",
            flavor="neutral",
        )

    # Top restriction
    rs = restriction_share(df_focus).sort_values("Share", ascending=False)
    if len(rs):
        top = rs.iloc[0]
        observation_tile(
            obs_cols[2], "Dominant Restriction Lever",
            f"<b>{top['Restriction']}</b> is the most prevalent restriction — applied in "
            f"<b>{top['Share']*100:.0f}%</b> of focus-brand policies. Reducing this single "
            f"barrier would meaningfully expand patient access.",
            flavor="neutral",
        )

    # ----- Restriction landscape (secondary view) -----
    section_h2(
        "Restriction Landscape",
        "Frequency of each prior-authorization lever across the focus brands."
    )
    question("Which utilization-management levers do payers use most often?")

    rb = restriction_by_brand(df_focus, focus_brands)
    rs_overall = restriction_share(df_focus).sort_values("Share", ascending=True)
    order = rs_overall["Restriction"].tolist()

    fig_r = go.Figure()
    for b in focus_brands:
        sub = rb[rb["Brand"] == b].set_index("Restriction").reindex(order).reset_index()
        fig_r.add_trace(go.Bar(
            y=sub["Restriction"],
            x=sub["Share"] * 100,
            orientation="h",
            name=b,
            marker=dict(color=BRAND_COLORS.get(b, OTHER_C),
                        line=dict(color="#FFFFFF", width=0.5)),
            hovertemplate=f"<b>{b}</b><br>%{{y}}<br>%{{x:.0f}}%% of {b} policies<extra></extra>",
            text=[f"{v*100:.0f}%" for v in sub["Share"]],
            textposition="outside",
            textfont=dict(size=11, color=INK),
        ))
    apply_layout(
        fig_r,
        height=max(320, 50 * len(order) + 80),
        barmode="group",
        xaxis=dict(range=[0, 115], ticksuffix="%",
                   title="Share of policies imposing this restriction",
                   title_font=dict(size=12, color=INK_SOFT)),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})


# ----------------------------------------------------------------------------
#  TAB 2 — BRAND COMPARISON
# ----------------------------------------------------------------------------
with tab2:

    section_h2(
        "Brand Scorecards",
        "Side-by-side metrics for TREMFYA and STELARA across the filtered policy set."
    )

    def scorecard_metrics(sub: pd.DataFrame) -> dict:
        if len(sub) == 0:
            return {}
        return {
            "Policies covered": len(sub),
            "Mean access score": f"{sub['Access Score'].mean():.1f}",
            "Median access score": f"{sub['Access Score'].median():.0f}",
            "Score range": f"{sub['Access Score'].min():.0f}–{sub['Access Score'].max():.0f}",
            "Step therapy required": f"{(sub['Step Therapy']=='Required').mean()*100:.0f}%",
            "TB test required": f"{(sub['TB Test']=='Yes').mean()*100:.0f}%",
            "Quantity limit imposed": f"{(sub['Quantity Limit']=='Yes').mean()*100:.0f}%",
            "Specialist required": f"{(sub['Specialist Required']=='Required').mean()*100:.0f}%",
            "Median initial authorization": (
                f"{sub['Initial Auth (months)'].median():.0f} mo"
                if sub["Initial Auth (months)"].notna().any() else "—"
            ),
            "Median reauthorization": (
                f"{sub['Reauth (months)'].median():.0f} mo"
                if sub["Reauth (months)"].notna().any() else "—"
            ),
        }

    sc_cols = st.columns(2)
    for col, brand in zip(sc_cols, ["TREMFYA", "STELARA"]):
        sub = df_all[df_all["Brand"] == brand]
        # apply other filters but always show focus brands
        sub = sub[sub["Access Score"].between(score_range[0], score_range[1])]
        sub = sub[sub["Access Tier"].isin(selected_tiers)]
        m = scorecard_metrics(sub)
        css_cls = "stelara" if brand == "STELARA" else ""
        strap_cls = "stelara" if brand == "STELARA" else "tremfya"

        rows_html = "".join(
            f'<tr><td class="label">{k}</td><td class="value">{v}</td></tr>'
            for k, v in m.items()
        )
        with col:
            st.markdown(
                f"""
<div class="zs-scorecard {css_cls}">
  <div class="brand-strap strap {strap_cls}">Brand scorecard</div>
  <h3>{brand}</h3>
  <table>{rows_html}</table>
</div>
""",
                unsafe_allow_html=True,
            )

    # ----- Restriction prevalence butterfly chart -----
    section_h2(
        "Restriction Patterns by Brand",
        "Where the two brands face the same versus different utilization-management treatment."
    )
    question("Which restrictions hit one brand harder than the other?")

    rb = restriction_by_brand(df_all, ["TREMFYA", "STELARA"])
    rb_pivot = rb.pivot(index="Restriction", columns="Brand", values="Share").reset_index()
    rb_pivot["Gap"] = (rb_pivot.get("TREMFYA", 0) - rb_pivot.get("STELARA", 0)) * 100
    rb_pivot = rb_pivot.sort_values("Gap")

    fig_bf = go.Figure()
    fig_bf.add_trace(go.Bar(
        y=rb_pivot["Restriction"],
        x=-rb_pivot["STELARA"] * 100,
        orientation="h",
        name="STELARA",
        marker=dict(color=STELARA_C, line=dict(color="#FFFFFF", width=0.5)),
        text=[f"{v*100:.0f}%" for v in rb_pivot["STELARA"]],
        textposition="outside",
        textfont=dict(size=11, color=INK),
        hovertemplate="<b>STELARA</b><br>%{y}<br>%{customdata:.0f}% of policies<extra></extra>",
        customdata=rb_pivot["STELARA"] * 100,
    ))
    fig_bf.add_trace(go.Bar(
        y=rb_pivot["Restriction"],
        x=rb_pivot["TREMFYA"] * 100,
        orientation="h",
        name="TREMFYA",
        marker=dict(color=TREMFYA_C, line=dict(color="#FFFFFF", width=0.5)),
        text=[f"{v*100:.0f}%" for v in rb_pivot["TREMFYA"]],
        textposition="outside",
        textfont=dict(size=11, color=INK),
        hovertemplate="<b>TREMFYA</b><br>%{y}<br>%{x:.0f}% of policies<extra></extra>",
    ))
    max_x = max(rb_pivot["TREMFYA"].max(), rb_pivot["STELARA"].max()) * 100 + 25
    apply_layout(
        fig_bf,
        height=max(360, 50 * len(rb_pivot) + 80),
        barmode="overlay",
        xaxis=dict(
            range=[-max_x, max_x],
            tickvals=[-100, -75, -50, -25, 0, 25, 50, 75, 100],
            ticktext=["100%", "75%", "50%", "25%", "0", "25%", "50%", "75%", "100%"],
            title="← STELARA share         |         TREMFYA share →",
            title_font=dict(size=12, color=INK_SOFT),
            zeroline=True,
            zerolinecolor=INK,
            zerolinewidth=1.5,
        ),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig_bf, use_container_width=True, config={"displayModeBar": False})

    # ----- Paired within-policy comparison -----
    section_h2(
        "Paired Policy Comparison",
        "When the same payer policy covers both TREMFYA and STELARA, how does the access score compare?"
    )

    paired = df_all[df_all["Brand"].isin(["TREMFYA", "STELARA"])].copy()
    grp = paired.groupby("Policy ID")["Brand"].nunique()
    paired_ids = grp[grp == 2].index.tolist()
    paired = paired[paired["Policy ID"].isin(paired_ids)]

    if len(paired_ids) >= 2:
        pivot = paired.pivot_table(index=["Policy ID", "Policy #"],
                                    columns="Brand", values="Access Score").reset_index()
        pivot = pivot.dropna(subset=["TREMFYA", "STELARA"])
        pivot["delta"] = pivot["TREMFYA"] - pivot["STELARA"]
        pivot = pivot.sort_values("delta")

        question(f"In the {len(pivot)} policies covering both brands, which receives the better access terms?")

        fig_dumb = go.Figure()
        # Connector lines
        for _, r in pivot.iterrows():
            fig_dumb.add_trace(go.Scatter(
                x=[r["STELARA"], r["TREMFYA"]],
                y=[r["Policy #"], r["Policy #"]],
                mode="lines",
                line=dict(color=LINE, width=2),
                showlegend=False,
                hoverinfo="skip",
            ))
        # STELARA dots
        fig_dumb.add_trace(go.Scatter(
            x=pivot["STELARA"], y=pivot["Policy #"],
            mode="markers",
            name="STELARA",
            marker=dict(color=STELARA_C, size=14, line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate="<b>STELARA</b><br>%{y}<br>Score: %{x:.0f}<extra></extra>",
        ))
        fig_dumb.add_trace(go.Scatter(
            x=pivot["TREMFYA"], y=pivot["Policy #"],
            mode="markers",
            name="TREMFYA",
            marker=dict(color=TREMFYA_C, size=14, line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate="<b>TREMFYA</b><br>%{y}<br>Score: %{x:.0f}<extra></extra>",
        ))
        apply_layout(
            fig_dumb,
            height=max(280, 35 * len(pivot) + 80),
            xaxis=dict(range=[-5, 85],
                       title="Access Score",
                       title_font=dict(size=12, color=INK_SOFT)),
            yaxis=dict(title=""),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        st.plotly_chart(fig_dumb, use_container_width=True, config={"displayModeBar": False})

        # Summary callout
        tremfya_higher = int((pivot["delta"] > 0).sum())
        stelara_higher = int((pivot["delta"] < 0).sum())
        equal = int((pivot["delta"] == 0).sum())
        avg_delta = pivot["delta"].mean()

        c1, c2, c3 = st.columns(3)
        observation_tile(
            c1, "TREMFYA advantage",
            f"<b>{tremfya_higher} of {len(pivot)}</b> shared policies score TREMFYA higher than STELARA.",
            flavor="tremfya",
        )
        observation_tile(
            c2, "STELARA advantage",
            f"<b>{stelara_higher} of {len(pivot)}</b> shared policies score STELARA higher than TREMFYA.",
            flavor="stelara",
        )
        observation_tile(
            c3, "Average within-policy gap",
            f"Mean access-score advantage for TREMFYA: <b>{avg_delta:+.1f}</b> points within the same policy.",
            flavor="neutral",
        )
    else:
        st.info("Insufficient policies covering both brands for a paired comparison in the current filter set.")

    # ----- Authorization durations -----
    section_h2(
        "Authorization Durations",
        "Length of approval windows — shorter durations mean more frequent reauthorization touchpoints."
    )
    question("How long is the leash on each brand?")

    auth_rows = []
    for b in ["TREMFYA", "STELARA"]:
        sub = df_all[df_all["Brand"] == b]
        auth_rows.append({
            "Brand": b, "Type": "Initial authorization",
            "Median months": sub["Initial Auth (months)"].median(),
        })
        auth_rows.append({
            "Brand": b, "Type": "Reauthorization",
            "Median months": sub["Reauth (months)"].median(),
        })
    auth_df = pd.DataFrame(auth_rows)

    fig_auth = go.Figure()
    for b in ["TREMFYA", "STELARA"]:
        sub = auth_df[auth_df["Brand"] == b]
        fig_auth.add_trace(go.Bar(
            x=sub["Type"], y=sub["Median months"],
            name=b,
            marker=dict(color=BRAND_COLORS[b], line=dict(color="#FFFFFF", width=0.5)),
            text=[f"{v:.0f} mo" if pd.notna(v) else "—" for v in sub["Median months"]],
            textposition="outside",
            textfont=dict(size=12, color=INK),
            hovertemplate=f"<b>{b}</b><br>%{{x}}<br>Median %{{y:.0f}} months<extra></extra>",
        ))
    apply_layout(
        fig_auth,
        height=320,
        barmode="group",
        xaxis=dict(title=""),
        yaxis=dict(title="Median months", title_font=dict(size=12, color=INK_SOFT)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        bargap=0.4,
    )
    st.plotly_chart(fig_auth, use_container_width=True, config={"displayModeBar": False})


# ----------------------------------------------------------------------------
#  TAB 3 — PARAMETER-LEVEL INSIGHTS
# ----------------------------------------------------------------------------
with tab3:

    section_h2(
        "Parameter-Level Insights",
        "Interactive exploration of each extracted parameter. Select a category, then a parameter, "
        "to see how it varies across the focus brands and what it implies for access."
    )

    # Parameter groups
    PARAM_GROUPS = {
        "Eligibility & screening": [
            ("Age Criterion",         "categorical", "Age criterion"),
            ("TB Test",               "yesno",       "TB test required"),
            ("Specialist Required",   "yesno",       "Specialist prescriber required"),
        ],
        "Step therapy & pre-treatment": [
            ("Step Therapy",         "yesno",       "Step therapy documented"),
            ("Brand Steps",          "numeric",     "Number of brand/biologic steps"),
            ("Generic Steps",        "numeric",     "Number of generic/oral steps"),
            ("Phototherapy Step",    "yesno",       "Phototherapy step required"),
        ],
        "Utilization management": [
            ("Quantity Limit",       "yesno",       "Quantity limit imposed"),
            ("Initial Auth (months)","numeric",     "Initial authorization duration"),
            ("Reauth (months)",      "numeric",     "Reauthorization duration"),
            ("Reauthorization",      "yesno",       "Reauthorization required"),
        ],
    }

    PARAM_INSIGHTS = {
        "Age Criterion": "Age thresholds shape the eligible patient pool. Policies citing 'FDA approved age' default to the label, while explicit thresholds (e.g., ≥18, ≥6) may exclude pediatric or young-adult populations.",
        "TB Test": "TB screening is a clinical safety prerequisite for biologic immunomodulators. Universal adoption would be expected; gaps indicate inconsistent policy documentation rather than waived screening.",
        "Specialist Required": "Specialist-only prescribing concentrates approval workflow with dermatologists and rheumatologists, adding referral friction but ensuring appropriate diagnosis.",
        "Step Therapy": "Step therapy is the single most material access barrier. Required in most policies; the depth of required step-throughs varies meaningfully by payer.",
        "Brand Steps": "Branded biologic step-throughs (commonly anti-TNFs or preferred IL inhibitors) delay initiation by weeks to months and drive abandonment risk.",
        "Generic Steps": "Generic / oral systemic step-throughs (methotrexate, cyclosporine, acitretin) typically apply earlier in the patient journey.",
        "Phototherapy Step": "Phototherapy step requirements are uncommon but consequential — they require access to clinic-administered UVB/PUVA before biologic approval.",
        "Quantity Limit": "Quantity limits cap units per fill, indirectly enforcing adherence checks and limiting off-label dose escalation.",
        "Initial Auth (months)": "Shorter initial authorization windows (≤6 months) increase administrative friction and can trigger early discontinuation if reauthorization documentation lapses.",
        "Reauth (months)": "Reauthorization cadence determines ongoing administrative burden. 12-month cycles are standard; shorter cycles signal tighter ongoing utilization management.",
        "Reauthorization": "Near-universal reauthorization requirement is expected for specialty biologics — the question is duration and documentation depth, not whether it's required.",
    }

    cat_col, param_col = st.columns([1, 2])
    with cat_col:
        category = st.selectbox(
            "Parameter category",
            options=list(PARAM_GROUPS.keys()),
            index=0,
        )
    with param_col:
        param_options = [(label, col, kind) for col, kind, label in PARAM_GROUPS[category]]
        chosen_label = st.selectbox(
            "Parameter",
            options=[label for label, _, _ in param_options],
            index=0,
        )
    sel = next((c, k) for label, c, k in param_options if label == chosen_label)
    sel_col, sel_kind = sel

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

    # Build the two-panel view depending on data type
    left, right = st.columns([1, 1])

    # ---- Left panel: overall distribution ----
    with left:
        question(f"What does '{chosen_label}' look like across the corpus?")
        if sel_kind == "numeric":
            d = df_focus[sel_col].dropna()
            if len(d) == 0:
                st.info("No data available for this parameter under current filters.")
            else:
                vc = d.astype(int).value_counts().sort_index()
                fig = go.Figure(go.Bar(
                    x=vc.index, y=vc.values,
                    marker=dict(color=AMBER, line=dict(color="#FFFFFF", width=0.5)),
                    text=vc.values, textposition="outside",
                    textfont=dict(size=11, color=INK),
                    hovertemplate=f"<b>{chosen_label}</b><br>%{{x}}<br>%{{y}} policies<extra></extra>",
                    name=chosen_label,
                ))
                apply_layout(
                    fig, height=300,
                    xaxis=dict(title=chosen_label, title_font=dict(size=12, color=INK_SOFT)),
                    yaxis=dict(title="Policies", title_font=dict(size=12, color=INK_SOFT)),
                    showlegend=False, bargap=0.25,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            vc = df_focus[sel_col].fillna("Not specified").value_counts()
            fig = go.Figure(go.Bar(
                y=vc.index.tolist(), x=vc.values,
                orientation="h",
                marker=dict(color=AMBER, line=dict(color="#FFFFFF", width=0.5)),
                text=vc.values, textposition="outside",
                textfont=dict(size=11, color=INK),
                hovertemplate=f"<b>{chosen_label}</b><br>%{{y}}<br>%{{x}} policies<extra></extra>",
                name=chosen_label,
            ))
            apply_layout(
                fig, height=max(220, 50 * len(vc) + 80),
                xaxis=dict(title="Policies", title_font=dict(size=12, color=INK_SOFT),
                           range=[0, vc.max() * 1.2]),
                yaxis=dict(title=""),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ---- Right panel: split by brand ----
    with right:
        question(f"How does '{chosen_label}' differ between TREMFYA and STELARA?")
        if sel_kind == "numeric":
            sub = df_all[df_all["Brand"].isin(["TREMFYA", "STELARA"])].copy()
            sub = sub[sub[sel_col].notna()]
            sub = sub[sub["Access Score"].between(score_range[0], score_range[1])]
            if len(sub) == 0:
                st.info("No data available for the focus brands.")
            else:
                fig = go.Figure()
                for b in ["TREMFYA", "STELARA"]:
                    bsub = sub[sub["Brand"] == b]
                    if len(bsub):
                        fig.add_trace(go.Box(
                            x=bsub[sel_col],
                            name=b,
                            marker=dict(color=BRAND_COLORS[b]),
                            line=dict(color=BRAND_COLORS[b]),
                            fillcolor=BRAND_COLORS[b],
                            opacity=0.6,
                            boxmean=True,
                            orientation="h",
                            hovertemplate=f"<b>{b}</b><br>%{{x}}<extra></extra>",
                        ))
                apply_layout(
                    fig, height=300,
                    xaxis=dict(title=chosen_label, title_font=dict(size=12, color=INK_SOFT)),
                    yaxis=dict(title=""),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            sub = df_all[df_all["Brand"].isin(["TREMFYA", "STELARA"])].copy()
            sub[sel_col] = sub[sel_col].fillna("Not specified")
            cross = sub.groupby(["Brand", sel_col]).size().reset_index(name="n")
            totals = sub.groupby("Brand").size()
            cross["pct"] = cross.apply(lambda r: r["n"] / totals[r["Brand"]] * 100, axis=1)

            fig = go.Figure()
            for b in ["TREMFYA", "STELARA"]:
                bsub = cross[cross["Brand"] == b]
                fig.add_trace(go.Bar(
                    x=bsub[sel_col], y=bsub["pct"],
                    name=b,
                    marker=dict(color=BRAND_COLORS[b], line=dict(color="#FFFFFF", width=0.5)),
                    text=[f"{v:.0f}%" for v in bsub["pct"]],
                    textposition="outside",
                    textfont=dict(size=11, color=INK),
                    hovertemplate=f"<b>{b}</b><br>%{{x}}<br>%{{y:.0f}}%<extra></extra>",
                ))
            apply_layout(
                fig, height=300, barmode="group",
                xaxis=dict(title=chosen_label, title_font=dict(size=12, color=INK_SOFT)),
                yaxis=dict(title="% of brand's policies", title_font=dict(size=12, color=INK_SOFT),
                           ticksuffix="%"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ---- Interpretation strip ----
    interp = PARAM_INSIGHTS.get(sel_col, "")
    if interp:
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        observation_tile(
            st.container(), "Business Implication",
            interp,
            flavor="neutral",
        )

    # ----- Cross-parameter view (heatmap) -----
    section_h2(
        "Cross-Parameter Restriction Map",
        "Brand-by-restriction map showing how often each lever is applied. Darker = more pervasive."
    )

    cross_brands = ["TREMFYA", "STELARA"]
    if include_context:
        # Add a couple of other brands with coverage
        other_counts = df_all[~df_all["Brand"].isin(cross_brands)].groupby("Brand").size().sort_values(ascending=False)
        cross_brands += other_counts[other_counts >= 2].index.tolist()[:6]

    rb_full = restriction_by_brand(df_all, cross_brands)
    pivot_h = rb_full.pivot(index="Brand", columns="Restriction", values="Share")
    # Order brands by mean restriction share descending
    pivot_h = pivot_h.loc[pivot_h.mean(axis=1).sort_values(ascending=False).index]
    # Order restrictions by mean share descending
    pivot_h = pivot_h[pivot_h.mean(axis=0).sort_values(ascending=False).index]

    fig_hm = go.Figure(go.Heatmap(
        z=pivot_h.values * 100,
        x=pivot_h.columns,
        y=pivot_h.index,
        colorscale=[[0, "#FFF8E1"], [0.4, "#F9C56A"], [1, "#9A6610"]],
        zmin=0, zmax=100,
        text=[[f"{v:.0f}%" for v in row] for row in pivot_h.values * 100],
        texttemplate="%{text}",
        textfont=dict(color=INK, size=11),
        hovertemplate="<b>%{y}</b><br>%{x}<br>%{z:.0f}% of policies<extra></extra>",
        colorbar=dict(title=dict(text="Share", font=dict(color=INK_SOFT, size=11)),
                      tickfont=dict(color=INK_SOFT, size=10), ticksuffix="%",
                      thickness=12, len=0.65, x=1.02),
    ))
    apply_layout(
        fig_hm,
        height=max(260, 36 * len(pivot_h) + 130),
        xaxis=dict(side="top", tickangle=-20, showgrid=False),
        yaxis=dict(showgrid=False, autorange="reversed"),
    )
    st.plotly_chart(fig_hm, use_container_width=True, config={"displayModeBar": False})


# ----------------------------------------------------------------------------
#  TAB 4 — POLICY DEEP DIVE
# ----------------------------------------------------------------------------
with tab4:

    section_h2(
        "Policy Deep Dive",
        "Brand-first navigation into the underlying policy records. Select a brand, then a policy, "
        "to see the full extracted parameter set. Optionally compare two policies side by side."
    )

    # Brand pill selector
    nav_col1, nav_col2 = st.columns([1, 3])
    with nav_col1:
        deep_brand = st.radio(
            "Brand",
            options=["TREMFYA", "STELARA"],
            index=0,
            horizontal=False,
        )
    with nav_col2:
        sort_choice = st.radio(
            "Sort policies by",
            options=["Most restrictive first", "Most open first", "Policy ID"],
            index=0,
            horizontal=True,
        )

    sub = df_all[df_all["Brand"] == deep_brand].copy()
    sub = sub[sub["Access Score"].between(score_range[0], score_range[1])]
    sub = sub[sub["Access Tier"].isin(selected_tiers)]

    if sort_choice == "Most restrictive first":
        sub = sub.sort_values("Access Score", ascending=True, na_position="last")
    elif sort_choice == "Most open first":
        sub = sub.sort_values("Access Score", ascending=False, na_position="last")
    else:
        sub = sub.sort_values("Policy ID")

    if len(sub) == 0:
        st.info("No policies match the current filters for this brand.")
    else:
        # Build readable labels for the selectbox
        def policy_label(row):
            score = f"{int(row['Access Score'])}" if pd.notna(row["Access Score"]) else "—"
            return f"{row['Policy #']}  ·  Access score {score}  ·  {row['Access Tier']}"

        sub["__label"] = sub.apply(policy_label, axis=1)

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        compare = st.toggle("Compare two policies side by side", value=False)

        if not compare:
            chosen = st.selectbox(
                f"Select a {deep_brand} policy",
                options=sub["__label"].tolist(),
                index=0,
            )
            row = sub[sub["__label"] == chosen].iloc[0]
            render_policy_panels = [row]
        else:
            cc1, cc2 = st.columns(2)
            with cc1:
                c1 = st.selectbox(
                    "Policy A",
                    options=sub["__label"].tolist(),
                    index=0,
                    key="policy_a",
                )
            with cc2:
                default_b = 1 if len(sub) > 1 else 0
                c2 = st.selectbox(
                    "Policy B",
                    options=sub["__label"].tolist(),
                    index=default_b,
                    key="policy_b",
                )
            render_policy_panels = [
                sub[sub["__label"] == c1].iloc[0],
                sub[sub["__label"] == c2].iloc[0],
            ]

        st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

        cols_panel = st.columns(len(render_policy_panels), gap="medium")

        for panel_col, row in zip(cols_panel, render_policy_panels):
            with panel_col:
                # Header card
                score = int(row["Access Score"]) if pd.notna(row["Access Score"]) else None
                tier = row["Access Tier"]
                tier_color = ACCESS_TIER_COLOR.get(tier, SLATE)
                brand_color = BRAND_COLORS.get(row["Brand"], SLATE)
                score_html = f"{score}" if score is not None else "—"

                st.markdown(
                    f"""
<div style="background:{CARD}; border:1px solid {LINE}; border-top:4px solid {brand_color};
            border-radius:3px; padding:16px 18px; margin-bottom:12px;">
  <div style="font-size:10.5px; letter-spacing:0.18em; text-transform:uppercase;
              color:{brand_color}; font-weight:700;">{row['Brand']} · {row['Policy #']}</div>
  <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
    <div>
      <div style="font-family:'Fraunces',serif; font-size:32px; font-weight:600; color:{INK}; line-height:1;">{score_html}<span style="font-size:14px; color:{SLATE}; font-family:Manrope; margin-left:6px;">/ 80</span></div>
      <div style="font-size:11px; color:{SLATE}; margin-top:4px; letter-spacing:0.08em; text-transform:uppercase; font-weight:600;">Access score</div>
    </div>
    <div style="background:{tier_color}; color:#FFFFFF; padding:5px 12px; border-radius:2px;
                font-size:11px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;">{tier}</div>
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )

                # Parameter fields
                def field(label, value, mono=False):
                    if pd.isna(value) or str(value).strip() in ("", "nan", "None"):
                        value = "—"
                    cls = "zs-field-value mono" if mono else "zs-field-value"
                    return f"""
<div class="zs-field">
  <div class="zs-field-label">{label}</div>
  <div class="{cls}">{value}</div>
</div>
"""

                init_auth = (f"{int(row['Initial Auth (months)'])} months"
                             if pd.notna(row['Initial Auth (months)']) else
                             str(row.get('Initial Authorization Duration(in-months)') or '—'))
                reauth = (f"{int(row['Reauth (months)'])} months"
                          if pd.notna(row['Reauth (months)']) else
                          str(row.get('Reauthorization Duration(in-months)') or '—'))

                fields_html = "".join([
                    field("Age criterion", row["Age Criterion"]),
                    field("Specialist", row["Specialist Detail"]),
                    field("Step therapy", row["Step Therapy"]),
                    field("Brand steps required",
                          f"{int(row['Brand Steps'])}" if pd.notna(row['Brand Steps']) else "—"),
                    field("Generic steps required",
                          f"{int(row['Generic Steps'])}" if pd.notna(row['Generic Steps']) else "—"),
                    field("Phototherapy step", row["Phototherapy Step"]),
                    field("TB test", row["TB Test"]),
                    field("Quantity limit", row["Quantity Limit"]),
                    field("Initial authorization", init_auth),
                    field("Reauthorization duration", reauth),
                ])
                st.markdown(fields_html, unsafe_allow_html=True)

                # Policy language expanders
                step_text = row.get("Step Therapy Requirements Documented in Policy")
                reauth_text = row.get("Reauthorization Requirements Documented in Policy")
                qty_text = row.get("Quantity Limits")

                if pd.notna(step_text) and str(step_text).strip().lower() not in ("no", "nan", ""):
                    with st.expander("Step therapy language (verbatim)"):
                        st.write(step_text)
                if pd.notna(reauth_text):
                    with st.expander("Reauthorization requirements (verbatim)"):
                        st.write(reauth_text)
                if pd.notna(qty_text) and len(str(qty_text).strip()) > 10:
                    with st.expander("Quantity limit language (verbatim)"):
                        st.write(qty_text)

                with st.expander("Source policy identifier"):
                    st.code(row["Policy ID"] + ".pdf", language="text")


# ============================================================================
#  FOOTER
# ============================================================================
st.markdown(
    f"""
<div class="zs-footer">
  <span>ZS · Market Access Practice · Plaque Psoriasis Policy Lens</span>
  <span>Generated from extracted PA policy corpus · {df_all['Policy ID'].nunique()} policies, {df_all['Brand'].nunique()} brands</span>
</div>
""",
    unsafe_allow_html=True,
)
