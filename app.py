"""PsO Market Access Intelligence — TREMFYA vs STELARA."""

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
INK         = "#1F2937"
INK_SOFT    = "#4B5563"
SLATE       = "#6B7280"
LINE        = "#E5E7EB"
LINE_SOFT   = "#F1EFE9"
PAPER       = "#FBFAF6"
CARD        = "#FFFFFF"
NAVY        = "#1E293B"
AMBER       = "#D97706"
AMBER_SOFT  = "#FBBF24"

TREMFYA_C       = "#047857"
TREMFYA_LIGHT   = "#10B981"
STELARA_C       = "#6D28D9"
STELARA_LIGHT   = "#A78BFA"

BRAND_COLORS = {"TREMFYA": TREMFYA_C, "STELARA": STELARA_C}
FOCUS_BRANDS = ["TREMFYA", "STELARA"]

ACCESS_TIER_ORDER = ["Highly Restrictive", "Restricted", "Moderate", "Open", "Highly Open"]
ACCESS_TIER_COLOR = {
    "Highly Restrictive": "#B91C1C",
    "Restricted":         "#EA580C",
    "Moderate":           "#CA8A04",
    "Open":               "#16A34A",
    "Highly Open":        "#047857",
    "Unscored":           "#94A3B8",
}

ARCHETYPE_ORDER = ["Open access", "Standard access", "Tight access"]
ARCHETYPE_COLOR = {
    "Open access":     "#16A34A",
    "Standard access": "#CA8A04",
    "Tight access":    "#B91C1C",
}

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
    merged = {k: (dict(v) if isinstance(v, dict) else v) for k, v in PLOTLY_BASE.items()}
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v
    fig.update_layout(**merged)
    return fig


CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Manrope:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], button, input, select, textarea {{
    font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: {INK};
}}
.stApp {{ background: {PAPER}; color: {INK}; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
section.main > div.block-container {{ padding-top: 1.5rem; padding-bottom: 4rem; max-width: 1380px; }}

/* Masthead */
.zs-masthead {{
    display: flex; justify-content: space-between; align-items: flex-end;
    padding-bottom: 14px; margin-bottom: 18px; border-bottom: 1px solid {LINE};
}}
.zs-masthead-left .eyebrow {{
    font-size: 10.5px; letter-spacing: 0.22em; text-transform: uppercase;
    color: {AMBER}; font-weight: 700; margin-bottom: 4px;
}}
.zs-masthead-left h1 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 600; font-size: 28px; line-height: 1.15;
    letter-spacing: -0.015em; color: {INK}; margin: 0 0 4px 0;
}}
.zs-masthead-left .deck {{
    font-size: 13px; color: {INK_SOFT}; max-width: 720px; line-height: 1.45;
}}
.zs-masthead-right {{
    text-align: right; font-size: 11px; letter-spacing: 0.06em;
    text-transform: uppercase; color: {SLATE}; font-weight: 500;
}}
.zs-pill-tremfya, .zs-pill-stelara {{
    display: inline-block; padding: 4px 11px; margin-left: 6px;
    border-radius: 2px; font-weight: 700; font-size: 10px;
    letter-spacing: 0.14em; color: #FFFFFF;
}}
.zs-pill-tremfya {{ background: {TREMFYA_C}; }}
.zs-pill-stelara {{ background: {STELARA_C}; }}

/* Section heading */
.zs-h2 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 600; font-size: 20px; line-height: 1.2;
    letter-spacing: -0.01em; color: {INK}; margin: 30px 0 4px 0;
}}
.zs-h2-deck {{
    font-size: 13px; color: {INK_SOFT}; line-height: 1.5;
    margin-bottom: 16px; max-width: 820px;
}}

/* Question prompt */
.zs-question {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 15.5px; font-weight: 500; font-style: italic;
    color: {INK}; margin: 16px 0 6px 0; line-height: 1.4;
}}

/* KPI cards */
.zs-kpi {{
    background: {CARD}; border: 1px solid {LINE}; border-radius: 4px;
    padding: 14px 16px; height: 100%; position: relative;
}}
.zs-kpi-accent {{
    position: absolute; top: 0; left: 0; width: 4px; height: 100%;
    background: {AMBER}; border-radius: 4px 0 0 4px;
}}
.zs-kpi-accent.tremfya {{ background: {TREMFYA_C}; }}
.zs-kpi-accent.stelara {{ background: {STELARA_C}; }}
.zs-kpi-accent.neutral {{ background: {SLATE}; }}
.zs-kpi-label {{
    font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
    color: {SLATE}; font-weight: 600; margin-bottom: 6px;
}}
.zs-kpi-value {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 30px; font-weight: 600; line-height: 1.05;
    color: {INK}; letter-spacing: -0.02em;
}}
.zs-kpi-value .unit {{
    font-size: 13px; color: {SLATE}; font-family: 'Manrope', sans-serif !important;
    font-weight: 500; margin-left: 4px;
}}
.zs-kpi-foot {{
    font-size: 11.5px; color: {INK_SOFT}; margin-top: 8px;
    line-height: 1.4; min-height: 1.4em;
}}

/* Implication tiles */
.zs-obs {{
    background: {CARD}; border: 1px solid {LINE}; border-left: 3px solid {AMBER};
    border-radius: 3px; padding: 14px 16px; height: 100%;
}}
.zs-obs.tremfya {{ border-left-color: {TREMFYA_C}; }}
.zs-obs.stelara {{ border-left-color: {STELARA_C}; }}
.zs-obs.neutral {{ border-left-color: {SLATE}; }}
.zs-obs-tag {{
    font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase;
    color: {AMBER}; font-weight: 700; margin-bottom: 6px;
}}
.zs-obs.tremfya .zs-obs-tag {{ color: {TREMFYA_C}; }}
.zs-obs.stelara .zs-obs-tag {{ color: {STELARA_C}; }}
.zs-obs.neutral .zs-obs-tag {{ color: {SLATE}; }}
.zs-obs-text {{ font-size: 13.5px; color: {INK}; line-height: 1.55; }}
.zs-obs-text b {{ color: {INK}; font-weight: 700; }}

/* Verdict band */
.zs-verdict {{
    background: linear-gradient(90deg, {TREMFYA_C} 0%, {TREMFYA_LIGHT} 100%);
    color: #FFFFFF; padding: 14px 22px; border-radius: 4px; margin-top: 6px;
    display: flex; align-items: center; justify-content: space-between;
}}
.zs-verdict.stelara {{ background: linear-gradient(90deg, {STELARA_C} 0%, {STELARA_LIGHT} 100%); }}
.zs-verdict.parity {{ background: linear-gradient(90deg, {SLATE} 0%, #94A3B8 100%); }}
.zs-verdict .label {{
    font-size: 10.5px; letter-spacing: 0.22em; text-transform: uppercase;
    font-weight: 700; opacity: 0.85;
}}
.zs-verdict .text {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 19px; font-weight: 600; line-height: 1.25; margin-top: 4px;
}}
.zs-verdict .number {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 38px; font-weight: 700; line-height: 1; letter-spacing: -0.02em;
}}
.zs-verdict .number .small {{ font-size: 14px; font-weight: 500; opacity: 0.85; }}

/* Scorecard */
.zs-scorecard {{
    background: {CARD}; border: 1px solid {LINE}; border-top: 4px solid {TREMFYA_C};
    padding: 18px 20px; border-radius: 3px;
}}
.zs-scorecard.stelara {{ border-top-color: {STELARA_C}; }}
.zs-scorecard h3 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 22px; font-weight: 600; margin: 0; color: {INK};
    letter-spacing: -0.01em;
}}
.zs-scorecard .strap {{
    font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
    font-weight: 700; margin-bottom: 4px;
}}
.zs-scorecard .strap.tremfya {{ color: {TREMFYA_C}; }}
.zs-scorecard .strap.stelara {{ color: {STELARA_C}; }}
.zs-scorecard table {{ width: 100%; margin-top: 14px; border-collapse: collapse; }}
.zs-scorecard table td {{
    padding: 8px 0; border-bottom: 1px dashed {LINE};
    font-size: 13px; color: {INK};
}}
.zs-scorecard table tr:last-child td {{ border-bottom: none; }}
.zs-scorecard table td.label {{ color: {INK_SOFT}; }}
.zs-scorecard table td.value {{
    text-align: right; font-weight: 600; color: {INK};
    font-variant-numeric: tabular-nums;
}}

/* Archetype card */
.zs-arch {{
    background: {CARD}; border: 1px solid {LINE}; border-top: 4px solid {SLATE};
    border-radius: 3px; padding: 14px 16px; height: 100%;
}}
.zs-arch.open {{ border-top-color: {ACCESS_TIER_COLOR['Open']}; }}
.zs-arch.std  {{ border-top-color: {ACCESS_TIER_COLOR['Moderate']}; }}
.zs-arch.tight{{ border-top-color: {ACCESS_TIER_COLOR['Highly Restrictive']}; }}
.zs-arch .name {{
    font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase;
    color: {SLATE}; font-weight: 700; margin-bottom: 4px;
}}
.zs-arch .count {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 28px; font-weight: 600; color: {INK}; line-height: 1;
}}
.zs-arch .count .u {{ font-size: 13px; color: {SLATE}; font-family: 'Manrope', sans-serif !important; margin-left: 4px; }}
.zs-arch .desc {{ font-size: 12px; color: {INK_SOFT}; margin-top: 6px; line-height: 1.4; }}
.zs-arch .mix {{
    margin-top: 10px; padding-top: 10px; border-top: 1px dashed {LINE};
    display: flex; justify-content: space-between; font-size: 12px;
}}
.zs-arch .mix .t {{ color: {TREMFYA_C}; font-weight: 700; }}
.zs-arch .mix .s {{ color: {STELARA_C}; font-weight: 700; }}

/* Field */
.zs-field {{
    background: {CARD}; border: 1px solid {LINE}; border-radius: 3px;
    padding: 12px 14px; margin-bottom: 8px;
}}
.zs-field-label {{
    font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
    color: {SLATE}; font-weight: 600; margin-bottom: 4px;
}}
.zs-field-value {{ font-size: 13.5px; color: {INK}; line-height: 1.5; }}

/* Tabs */
div[data-baseweb="tab-list"] {{
    gap: 0; border-bottom: 1px solid {LINE}; background: transparent; padding-left: 0;
}}
button[data-baseweb="tab"] {{
    font-family: 'Manrope', sans-serif !important; font-weight: 600 !important;
    font-size: 13px !important; letter-spacing: 0.02em !important;
    color: {SLATE} !important; background: transparent !important;
    padding: 12px 22px !important; border-radius: 0 !important;
    border-bottom: 2px solid transparent !important; margin-right: 2px;
}}
button[data-baseweb="tab"]:hover {{
    color: {INK} !important; background: rgba(217, 119, 6, 0.04) !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {INK} !important; border-bottom-color: {AMBER} !important;
}}
div[data-baseweb="tab-panel"] {{ padding-top: 18px; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {NAVY} 0%, #0F172A 100%);
}}
section[data-testid="stSidebar"] * {{ color: #E5E7EB !important; }}
section[data-testid="stSidebar"] label {{
    color: #FCD34D !important; font-size: 10.5px !important;
    letter-spacing: 0.16em !important; text-transform: uppercase !important;
    font-weight: 700 !important;
}}
.zs-side-brand {{
    padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 18px;
}}
.zs-side-brand .eyebrow {{
    font-size: 10px; letter-spacing: 0.24em; text-transform: uppercase;
    color: {AMBER_SOFT} !important; font-weight: 700; margin-bottom: 4px;
}}
.zs-side-brand .title {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 22px; font-weight: 600; color: #FFFFFF !important; line-height: 1.2;
}}
.zs-side-brand .strap {{
    font-size: 11.5px; color: rgba(229,231,235,0.65) !important;
    line-height: 1.4; margin-top: 6px;
}}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background-color: rgba(255,255,255,0.06) !important;
    border-color: rgba(255,255,255,0.15) !important; color: #FFFFFF !important;
}}
section[data-testid="stSidebar"] [data-baseweb="tag"] {{
    background-color: {AMBER} !important; color: {NAVY} !important;
}}
section[data-testid="stSidebar"] [data-baseweb="tag"] span {{
    color: {NAVY} !important; font-weight: 700;
}}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div {{
    background-color: {AMBER_SOFT} !important;
}}
.zs-side-footer {{
    margin-top: 22px; padding-top: 14px;
    border-top: 1px solid rgba(255,255,255,0.1);
    font-size: 11px; color: rgba(229,231,235,0.55) !important; line-height: 1.5;
}}

/* Dataframe / expander */
[data-testid="stDataFrame"] {{
    border: 1px solid {LINE}; border-radius: 3px; background: {CARD};
}}
.streamlit-expanderHeader {{
    font-family: 'Manrope', sans-serif !important; font-weight: 600 !important;
    color: {INK} !important; background: {CARD} !important;
    border: 1px solid {LINE} !important; border-radius: 3px !important;
}}

.js-plotly-plot .plotly .modebar {{ display: none !important; }}

.zs-footer {{
    margin-top: 56px; padding-top: 16px; border-top: 1px solid {LINE};
    font-size: 11px; letter-spacing: 0.10em; text-transform: uppercase;
    color: {SLATE}; display: flex; justify-content: space-between;
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

RESTRICTION_DEFS = [
    ("Step Therapy",        "Required",     "Step therapy required"),
    ("TB Test",             "Yes",          "TB test required"),
    ("Quantity Limit",      "Yes",          "Quantity limit imposed"),
    ("Specialist Required", "Required",     "Specialist prescriber required"),
    ("Phototherapy Step",   "Yes",          "Phototherapy step required"),
    ("Reauthorization",     "Required",     "Reauthorization required"),
]


def restriction_count(df: pd.DataFrame) -> pd.Series:
    s = pd.Series(0, index=df.index)
    for col, val, _ in RESTRICTION_DEFS:
        s = s + (df[col] == val).astype(int)
    return s


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
            rows.append({"Brand": b, "Restriction": label, "Share": share,
                         "Count": int((sub[col] == val).sum()), "N": n})
    return pd.DataFrame(rows)


def archetype_label(count):
    if pd.isna(count): return "Unknown"
    if count <= 2: return "Open access"
    if count <= 4: return "Standard access"
    return "Tight access"


def kpi_card(col, label: str, value: str, foot: str = "", flavor: str = ""):
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


def implication_tile(col, tag: str, html: str, flavor: str = ""):
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
    st.markdown(f'<div class="zs-question">{text}</div>', unsafe_allow_html=True)


# ============================================================================
#  DATA INGESTION
# ============================================================================

st.sidebar.markdown(
    """
<div class="zs-side-brand">
  <div class="eyebrow">ZS · Market Access</div>
  <div class="title">PsO Policy Lens</div>
  <div class="strap">Prior-authorization intelligence: TREMFYA vs STELARA.</div>
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

df_all_raw = prepare(df_raw)

# Restrict to focus brands across the entire app
df_focus_all = df_all_raw[df_all_raw["Brand"].isin(FOCUS_BRANDS)].copy()


# ============================================================================
#  SIDEBAR FILTERS
# ============================================================================

st.sidebar.markdown("**Brand lens**")
brand_lens = st.sidebar.radio(
    "Brand lens",
    options=["TREMFYA + STELARA", "TREMFYA only", "STELARA only"],
    index=0,
    label_visibility="collapsed",
)

lens_to_brands = {
    "TREMFYA + STELARA": ["TREMFYA", "STELARA"],
    "TREMFYA only":      ["TREMFYA"],
    "STELARA only":      ["STELARA"],
}
active_brands = lens_to_brands[brand_lens]

st.sidebar.markdown("**Access score range**")
score_lo, score_hi = int(df_focus_all["Access Score"].min()), int(df_focus_all["Access Score"].max())
score_range = st.sidebar.slider(
    "Access score range",
    min_value=score_lo, max_value=score_hi,
    value=(score_lo, score_hi), step=5,
    label_visibility="collapsed",
)

st.sidebar.markdown("**Filter by access tier**")
tier_options = [t for t in ACCESS_TIER_ORDER if t in df_focus_all["Access Tier"].unique()]
selected_tiers = st.sidebar.multiselect(
    "Filter by access tier",
    options=tier_options,
    default=tier_options,
    label_visibility="collapsed",
)

st.sidebar.markdown(
    f"""
<div class="zs-side-footer">
The dashboard focuses exclusively on TREMFYA and STELARA. Filters apply consistently
across every section.
<br><br>
<b>{df_focus_all["Policy ID"].nunique()}</b> policies covering one or both brands · <b>{len(df_focus_all)}</b> brand-policy observations
</div>
""",
    unsafe_allow_html=True,
)

# Apply filters
base_mask = df_focus_all["Access Score"].between(score_range[0], score_range[1]) & \
            df_focus_all["Access Tier"].isin(selected_tiers)

df = df_focus_all[base_mask & df_focus_all["Brand"].isin(active_brands)].copy()
df_pair = df_focus_all[base_mask].copy()  # always both brands for paired views

if df.empty:
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
    <h1>How payer policies shape access to TREMFYA and STELARA</h1>
    <div class="deck">A consulting view of prior-authorization signals extracted from {df_focus_all['Policy ID'].nunique()} payer policies — quantifying where access opens, where it tightens, and what payer behaviors drive the difference.</div>
  </div>
  <div class="zs-masthead-right">
    Focus brands<span class="zs-pill-tremfya">TREMFYA</span><span class="zs-pill-stelara">STELARA</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================================
#  TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Executive Summary",
    "Brand Comparison",
    "Key Drivers",
    "Policy Insights",
    "Policy Explorer",
])


# ----------------------------------------------------------------------------
#  TAB 1 — EXECUTIVE SUMMARY
# ----------------------------------------------------------------------------
with tab1:

    tremfya_df = df_pair[df_pair["Brand"] == "TREMFYA"]
    stelara_df = df_pair[df_pair["Brand"] == "STELARA"]

    tremfya_mean = tremfya_df["Access Score"].mean() if len(tremfya_df) else np.nan
    stelara_mean = stelara_df["Access Score"].mean() if len(stelara_df) else np.nan
    diff = tremfya_mean - stelara_mean if not (np.isnan(tremfya_mean) or np.isnan(stelara_mean)) else np.nan

    # KPI strip
    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Policies analyzed", f"{df_pair['Policy ID'].nunique()}",
             foot=f"{len(df_pair)} brand-policy observations", flavor="neutral")
    kpi_card(c2, "TREMFYA · mean access score",
             f"{tremfya_mean:.1f}" if not np.isnan(tremfya_mean) else "—",
             foot=f"{len(tremfya_df)} policies covering TREMFYA", flavor="tremfya")
    kpi_card(c3, "STELARA · mean access score",
             f"{stelara_mean:.1f}" if not np.isnan(stelara_mean) else "—",
             foot=f"{len(stelara_df)} policies covering STELARA", flavor="stelara")
    if not np.isnan(diff):
        leader = "TREMFYA" if diff > 0 else ("STELARA" if diff < 0 else "Parity")
        sign = "+" if diff > 0 else ""
        flav = "tremfya" if diff > 0 else ("stelara" if diff < 0 else "neutral")
        kpi_card(c4, "Access differential",
                 f"{sign}{diff:.1f}<span class='unit'>pts</span>",
                 foot=f"{leader} advantage on a 0–80 scale", flavor=flav)
    else:
        kpi_card(c4, "Access differential", "—", "", flavor="neutral")

    # Verdict band
    if not np.isnan(diff):
        if abs(diff) < 1:
            verdict_cls = "parity"
            verdict_label = "Access verdict"
            verdict_text = "TREMFYA and STELARA face statistically similar access conditions across the corpus."
            verdict_num = f"≈ Parity"
        elif diff > 0:
            verdict_cls = ""
            verdict_label = "Access leader · TREMFYA"
            verdict_text = "TREMFYA enjoys a measurable access advantage over STELARA on a corpus-mean basis."
            verdict_num = f"+{diff:.1f}<span class='small'> pts</span>"
        else:
            verdict_cls = "stelara"
            verdict_label = "Access leader · STELARA"
            verdict_text = "STELARA enjoys a measurable access advantage over TREMFYA on a corpus-mean basis."
            verdict_num = f"+{abs(diff):.1f}<span class='small'> pts</span>"
        st.markdown(
            f"""
<div class="zs-verdict {verdict_cls}">
  <div>
    <div class="label">{verdict_label}</div>
    <div class="text">{verdict_text}</div>
  </div>
  <div class="number">{verdict_num}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    # Access distribution
    section_h2(
        "Access Overview",
        "Distribution of access scores across all in-scope policies for each brand. "
        "Wider shapes signal more variability; the position of the mass tells the story."
    )
    question("Which brand sits where on the 0–80 access spectrum?")

    fig_dist = go.Figure()
    for b in active_brands:
        bsub = df[df["Brand"] == b].dropna(subset=["Access Score"])
        if len(bsub) == 0:
            continue
        fig_dist.add_trace(go.Violin(
            x=bsub["Access Score"],
            y=[b] * len(bsub),
            name=b,
            orientation="h",
            side="positive",
            line_color=BRAND_COLORS[b],
            fillcolor=BRAND_COLORS[b],
            opacity=0.55,
            box_visible=True,
            meanline_visible=True,
            points="all",
            pointpos=-0.6,
            jitter=0.25,
            marker=dict(color=BRAND_COLORS[b], size=6, opacity=0.85,
                        line=dict(color="#FFFFFF", width=0.5)),
            hoveron="points",
            hovertemplate=f"<b>{b}</b><br>Score: %{{x}}<extra></extra>",
            scalemode="count",
            spanmode="hard",
        ))
    apply_layout(
        fig_dist,
        height=max(300, 130 * len(active_brands) + 80),
        xaxis=dict(range=[-5, 85],
                   title="Access Score (0 = most restrictive, 80 = most open)",
                   title_font=dict(size=12, color=INK_SOFT)),
        yaxis=dict(title="", showgrid=False),
        showlegend=False,
        violinmode="group",
    )
    st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False})

    # Business implications
    section_h2("Business Implications")

    rs = restriction_share(df_pair).sort_values("Share", ascending=False)
    top_restr = rs.iloc[0] if len(rs) else None

    t_range = (tremfya_df["Access Score"].max() - tremfya_df["Access Score"].min()) if len(tremfya_df) else 0
    s_range = (stelara_df["Access Score"].max() - stelara_df["Access Score"].min()) if len(stelara_df) else 0

    impl_cols = st.columns(3)
    if not np.isnan(diff):
        direction = "more open" if diff > 0 else ("more restricted" if diff < 0 else "comparable")
        leader = "TREMFYA" if diff > 0 else "STELARA"
        flav   = "tremfya" if diff > 0 else "stelara"
        implication_tile(
            impl_cols[0], "Brand positioning",
            f"<b>{leader} holds a {abs(diff):.1f}-point access edge</b> across the corpus. "
            f"While modest, the gap is directionally consistent and aligns with payers' tendency "
            f"to apply tighter management to older entrants in the IL class.",
            flavor=flav,
        )
    implication_tile(
        impl_cols[1], "Payer variability",
        f"Within-brand access varies by <b>{max(t_range, s_range):.0f} points</b> from least to most "
        f"restrictive policy. <b>Payer choice drives access more than brand choice</b> — pull-through "
        f"strategy should focus on lifting access at the lowest-scoring accounts.",
        flavor="neutral",
    )
    if top_restr is not None:
        implication_tile(
            impl_cols[2], "Dominant barrier",
            f"<b>{top_restr['Restriction']}</b> is the most prevalent utilization management lever, "
            f"applied in <b>{top_restr['Share']*100:.0f}%</b> of policies. Negotiation effort targeted "
            f"at this single lever could materially expand the addressable patient pool.",
            flavor="neutral",
        )


# ----------------------------------------------------------------------------
#  TAB 2 — BRAND COMPARISON
# ----------------------------------------------------------------------------
with tab2:

    section_h2(
        "Brand Comparison",
        "A direct comparison of TREMFYA and STELARA on access score, tier composition, "
        "and within-policy treatment."
    )

    # Scorecards
    sc_cols = st.columns(2)
    for col, brand in zip(sc_cols, FOCUS_BRANDS):
        sub = df_focus_all[df_focus_all["Brand"] == brand]
        sub = sub[sub["Access Score"].between(score_range[0], score_range[1])]
        sub = sub[sub["Access Tier"].isin(selected_tiers)]

        if len(sub) == 0:
            with col:
                st.info(f"No {brand} policies match the current filters.")
            continue

        metrics = {
            "Policies covered":            len(sub),
            "Mean access score":           f"{sub['Access Score'].mean():.1f}",
            "Median access score":         f"{sub['Access Score'].median():.0f}",
            "Score range":                 f"{sub['Access Score'].min():.0f}–{sub['Access Score'].max():.0f}",
            "Step therapy required":       f"{(sub['Step Therapy']=='Required').mean()*100:.0f}%",
            "TB test required":            f"{(sub['TB Test']=='Yes').mean()*100:.0f}%",
            "Quantity limit imposed":      f"{(sub['Quantity Limit']=='Yes').mean()*100:.0f}%",
            "Specialist required":         f"{(sub['Specialist Required']=='Required').mean()*100:.0f}%",
            "Median initial authorization": (
                f"{sub['Initial Auth (months)'].median():.0f} months"
                if sub["Initial Auth (months)"].notna().any() else "—"
            ),
            "Median reauthorization":      (
                f"{sub['Reauth (months)'].median():.0f} months"
                if sub["Reauth (months)"].notna().any() else "—"
            ),
        }
        css_cls = "stelara" if brand == "STELARA" else ""
        strap_cls = "stelara" if brand == "STELARA" else "tremfya"
        rows_html = "".join(
            f'<tr><td class="label">{k}</td><td class="value">{v}</td></tr>'
            for k, v in metrics.items()
        )
        with col:
            st.markdown(
                f"""
<div class="zs-scorecard {css_cls}">
  <div class="strap {strap_cls}">Brand scorecard</div>
  <h3>{brand}</h3>
  <table>{rows_html}</table>
</div>
""",
                unsafe_allow_html=True,
            )

    # Tier composition stacked
    section_h2(
        "Access Tier Composition",
        "Share of each brand's policies that fall into each access tier."
    )
    question("Where does each brand's policy mass concentrate on the restriction spectrum?")

    tier_data = []
    for b in FOCUS_BRANDS:
        sub = df_pair[df_pair["Brand"] == b]
        n = len(sub)
        if n == 0: continue
        vc = sub["Access Tier"].value_counts(normalize=True)
        for t in ACCESS_TIER_ORDER:
            tier_data.append({"Brand": b, "Tier": t, "Share": vc.get(t, 0.0)})
    tier_df = pd.DataFrame(tier_data)

    fig_tier = go.Figure()
    for t in ACCESS_TIER_ORDER:
        sub = tier_df[tier_df["Tier"] == t]
        fig_tier.add_trace(go.Bar(
            y=sub["Brand"],
            x=sub["Share"] * 100,
            orientation="h",
            name=t,
            marker=dict(color=ACCESS_TIER_COLOR[t], line=dict(color="#FFFFFF", width=1)),
            hovertemplate=f"<b>{t}</b><br>%{{y}}: %{{x:.0f}}%% of policies<extra></extra>",
        ))
    apply_layout(
        fig_tier,
        barmode="stack",
        height=260,
        xaxis=dict(range=[0, 100], ticksuffix="%",
                   title="Share of policies", title_font=dict(size=12, color=INK_SOFT)),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig_tier, use_container_width=True, config={"displayModeBar": False})

    # Paired comparison
    section_h2(
        "Paired Policy Analysis",
        "Within the same payer policy, which brand receives the more favorable treatment?"
    )

    paired = df_focus_all.copy()
    grp = paired.groupby("Policy ID")["Brand"].nunique()
    paired_ids = grp[grp == 2].index.tolist()
    paired_filt = paired[paired["Policy ID"].isin(paired_ids)]
    paired_filt = paired_filt[paired_filt["Access Score"].between(score_range[0], score_range[1])]
    paired_filt = paired_filt[paired_filt["Access Tier"].isin(selected_tiers)]
    pivot = paired_filt.pivot_table(index=["Policy ID", "Policy #"],
                                     columns="Brand", values="Access Score").reset_index()
    pivot = pivot.dropna(subset=["TREMFYA", "STELARA"])
    pivot["delta"] = pivot["TREMFYA"] - pivot["STELARA"]
    pivot = pivot.sort_values("delta")

    if len(pivot) >= 2:
        question(f"In the {len(pivot)} policies that cover both brands, who scores higher?")

        fig_pair = go.Figure()
        for _, r in pivot.iterrows():
            fig_pair.add_trace(go.Scatter(
                x=[r["STELARA"], r["TREMFYA"]],
                y=[r["Policy #"], r["Policy #"]],
                mode="lines",
                line=dict(color=LINE, width=2),
                showlegend=False, hoverinfo="skip", name="connector",
            ))
        fig_pair.add_trace(go.Scatter(
            x=pivot["STELARA"], y=pivot["Policy #"], mode="markers",
            name="STELARA",
            marker=dict(color=STELARA_C, size=14, line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate="<b>STELARA</b><br>%{y}<br>Score: %{x:.0f}<extra></extra>",
        ))
        fig_pair.add_trace(go.Scatter(
            x=pivot["TREMFYA"], y=pivot["Policy #"], mode="markers",
            name="TREMFYA",
            marker=dict(color=TREMFYA_C, size=14, line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate="<b>TREMFYA</b><br>%{y}<br>Score: %{x:.0f}<extra></extra>",
        ))
        apply_layout(
            fig_pair,
            height=max(280, 32 * len(pivot) + 80),
            xaxis=dict(range=[-5, 85], title="Access Score",
                       title_font=dict(size=12, color=INK_SOFT)),
            yaxis=dict(title=""),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        st.plotly_chart(fig_pair, use_container_width=True, config={"displayModeBar": False})

        t_higher = int((pivot["delta"] > 0).sum())
        s_higher = int((pivot["delta"] < 0).sum())
        avg_d = pivot["delta"].mean()

        c1, c2, c3 = st.columns(3)
        implication_tile(c1, "TREMFYA wins",
                         f"<b>{t_higher} of {len(pivot)}</b> shared policies score TREMFYA above STELARA.",
                         flavor="tremfya")
        implication_tile(c2, "STELARA wins",
                         f"<b>{s_higher} of {len(pivot)}</b> shared policies score STELARA above TREMFYA.",
                         flavor="stelara")
        implication_tile(c3, "Within-policy gap",
                         f"Average within-policy advantage for TREMFYA: <b>{avg_d:+.1f}</b> points.",
                         flavor="neutral")
    else:
        st.info("Insufficient policies covering both brands for a paired comparison in the current filters.")


# ----------------------------------------------------------------------------
#  TAB 3 — KEY DRIVERS
# ----------------------------------------------------------------------------
with tab3:

    section_h2(
        "Restriction Patterns",
        "The prior-authorization levers payers apply most often — and whether they hit one brand harder."
    )
    question("Which restrictions are most prevalent, and where do the brands diverge?")

    rb = restriction_by_brand(df_pair, FOCUS_BRANDS)
    overall = restriction_share(df_pair).sort_values("Share", ascending=True)
    order = overall["Restriction"].tolist()

    fig_r = go.Figure()
    for b in FOCUS_BRANDS:
        sub = rb[rb["Brand"] == b].set_index("Restriction").reindex(order).reset_index()
        fig_r.add_trace(go.Bar(
            y=sub["Restriction"],
            x=sub["Share"] * 100,
            orientation="h",
            name=b,
            marker=dict(color=BRAND_COLORS[b], line=dict(color="#FFFFFF", width=0.5)),
            hovertemplate=f"<b>{b}</b><br>%{{y}}<br>%{{x:.0f}}%% of {b} policies<extra></extra>",
        ))
    apply_layout(
        fig_r,
        height=max(340, 56 * len(order) + 60),
        barmode="group",
        xaxis=dict(range=[0, 105], ticksuffix="%",
                   title="Share of policies imposing the restriction",
                   title_font=dict(size=12, color=INK_SOFT)),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        bargap=0.18,
    )
    st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})

    # Step therapy intensity
    section_h2(
        "Step Therapy Intensity",
        "Step therapy is the single most material access barrier — how many hurdles must a patient clear?"
    )
    question("How many therapies must a patient try before accessing each brand?")

    step_rows = []
    for b in FOCUS_BRANDS:
        sub = df_pair[df_pair["Brand"] == b]
        sub = sub.dropna(subset=["Total Steps"])
        for _, r in sub.iterrows():
            step_rows.append({"Brand": b, "Steps": int(r["Total Steps"])})
    step_df = pd.DataFrame(step_rows)

    if not step_df.empty:
        max_s = int(step_df["Steps"].max())
        all_steps = list(range(0, max_s + 1))
        fig_steps = go.Figure()
        for b in FOCUS_BRANDS:
            sb = step_df[step_df["Brand"] == b]
            vc = sb["Steps"].value_counts().reindex(all_steps, fill_value=0)
            fig_steps.add_trace(go.Bar(
                x=vc.index, y=vc.values,
                name=b,
                marker=dict(color=BRAND_COLORS[b], line=dict(color="#FFFFFF", width=0.5)),
                hovertemplate=f"<b>{b}</b><br>%{{x}} steps · %{{y}} policies<extra></extra>",
            ))
        apply_layout(
            fig_steps,
            height=300,
            barmode="group",
            xaxis=dict(title="Total step-therapy hurdles required",
                       title_font=dict(size=12, color=INK_SOFT), dtick=1),
            yaxis=dict(title="Number of policies", title_font=dict(size=12, color=INK_SOFT)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            bargap=0.25,
        )
        st.plotly_chart(fig_steps, use_container_width=True, config={"displayModeBar": False})

    # Authorization windows
    section_h2(
        "Authorization Windows",
        "Approval durations — shorter windows mean more frequent administrative touchpoints."
    )
    question("How long are the approval cycles for each brand?")

    auth_rows = []
    for b in FOCUS_BRANDS:
        sub = df_pair[df_pair["Brand"] == b]
        auth_rows.append({"Brand": b, "Type": "Initial authorization",
                           "Median months": sub["Initial Auth (months)"].median()})
        auth_rows.append({"Brand": b, "Type": "Reauthorization",
                           "Median months": sub["Reauth (months)"].median()})
    auth_df = pd.DataFrame(auth_rows)

    fig_auth = go.Figure()
    for b in FOCUS_BRANDS:
        sub = auth_df[auth_df["Brand"] == b]
        fig_auth.add_trace(go.Bar(
            x=sub["Type"], y=sub["Median months"],
            name=b,
            marker=dict(color=BRAND_COLORS[b], line=dict(color="#FFFFFF", width=0.5)),
            hovertemplate=f"<b>{b}</b><br>%{{x}}<br>Median %{{y:.0f}} months<extra></extra>",
        ))
    apply_layout(
        fig_auth,
        height=300,
        barmode="group",
        xaxis=dict(title=""),
        yaxis=dict(title="Median months", title_font=dict(size=12, color=INK_SOFT)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        bargap=0.4,
    )
    st.plotly_chart(fig_auth, use_container_width=True, config={"displayModeBar": False})

    # Interactive parameter explorer
    section_h2(
        "Parameter Explorer",
        "Drill into any individual parameter to see how it varies between TREMFYA and STELARA."
    )

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
        ],
    }

    PARAM_INSIGHTS = {
        "Age Criterion": "Age thresholds determine the eligible population. Policies citing 'FDA approved age' default to the label; explicit thresholds (≥6, ≥18) may carve out specific cohorts.",
        "TB Test": "Universal TB screening is the clinical norm for biologics; gaps typically reflect documentation inconsistency rather than waived screening.",
        "Specialist Required": "Specialist-only prescribing adds referral friction but ensures appropriate diagnosis and dosing.",
        "Step Therapy": "Step therapy is the single most material access barrier and is required in the vast majority of policies.",
        "Brand Steps": "Branded biologic step-throughs delay biologic initiation by weeks to months — the strongest predictor of abandonment.",
        "Generic Steps": "Oral systemics (methotrexate, cyclosporine, acitretin) typically appear earlier in the step ladder.",
        "Phototherapy Step": "Phototherapy step requirements are uncommon but consequential — they require clinic-administered UVB/PUVA access.",
        "Quantity Limit": "Quantity limits cap units per fill, indirectly enforcing adherence and limiting dose escalation.",
        "Initial Auth (months)": "Short initial windows (≤6 months) increase administrative friction and elevate early-discontinuation risk.",
        "Reauth (months)": "Reauthorization cadence sets ongoing administrative burden — 12 months is the prevailing standard.",
    }

    pcat_col, ppar_col = st.columns([1, 2])
    with pcat_col:
        category = st.selectbox("Parameter category", options=list(PARAM_GROUPS.keys()), index=0)
    with ppar_col:
        opts = [(label, col, kind) for col, kind, label in PARAM_GROUPS[category]]
        chosen_label = st.selectbox("Parameter", options=[lbl for lbl, _, _ in opts], index=0)
    sel_col, sel_kind = next((c, k) for lbl, c, k in opts if lbl == chosen_label)

    left, right = st.columns(2)
    with left:
        question(f"How does '{chosen_label}' vary across the corpus?")
        if sel_kind == "numeric":
            d = df_pair[sel_col].dropna()
            if len(d) == 0:
                st.info("No data available for this parameter.")
            else:
                vc = d.astype(int).value_counts().sort_index()
                fig_p = go.Figure(go.Bar(
                    x=vc.index, y=vc.values,
                    marker=dict(color=AMBER, line=dict(color="#FFFFFF", width=0.5)),
                    hovertemplate=f"<b>{chosen_label}</b>: %{{x}}<br>%{{y}} policies<extra></extra>",
                    name=chosen_label,
                ))
                apply_layout(
                    fig_p, height=300,
                    xaxis=dict(title=chosen_label, title_font=dict(size=12, color=INK_SOFT)),
                    yaxis=dict(title="Policies", title_font=dict(size=12, color=INK_SOFT)),
                    showlegend=False, bargap=0.22,
                )
                st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})
        else:
            vc = df_pair[sel_col].fillna("Not specified").value_counts()
            fig_p = go.Figure(go.Bar(
                y=vc.index.tolist(), x=vc.values,
                orientation="h",
                marker=dict(color=AMBER, line=dict(color="#FFFFFF", width=0.5)),
                hovertemplate=f"<b>{chosen_label}</b>: %{{y}}<br>%{{x}} policies<extra></extra>",
                name=chosen_label,
            ))
            apply_layout(
                fig_p, height=max(220, 50 * len(vc) + 80),
                xaxis=dict(title="Policies", title_font=dict(size=12, color=INK_SOFT)),
                yaxis=dict(title=""),
                showlegend=False,
            )
            st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})

    with right:
        question(f"How does '{chosen_label}' differ between the two brands?")
        if sel_kind == "numeric":
            sub = df_pair.dropna(subset=[sel_col])
            if len(sub) == 0:
                st.info("No data available for the focus brands.")
            else:
                fig_b = go.Figure()
                for b in FOCUS_BRANDS:
                    bsub = sub[sub["Brand"] == b]
                    if len(bsub):
                        fig_b.add_trace(go.Box(
                            x=bsub[sel_col],
                            name=b,
                            marker=dict(color=BRAND_COLORS[b]),
                            line=dict(color=BRAND_COLORS[b]),
                            fillcolor=BRAND_COLORS[b],
                            opacity=0.55,
                            boxmean=True, orientation="h",
                            hovertemplate=f"<b>{b}</b><br>%{{x}}<extra></extra>",
                        ))
                apply_layout(
                    fig_b, height=300,
                    xaxis=dict(title=chosen_label, title_font=dict(size=12, color=INK_SOFT)),
                    yaxis=dict(title=""),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                )
                st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar": False})
        else:
            sub = df_pair.copy()
            sub[sel_col] = sub[sel_col].fillna("Not specified")
            cross = sub.groupby(["Brand", sel_col]).size().reset_index(name="n")
            totals = sub.groupby("Brand").size()
            cross["pct"] = cross.apply(lambda r: r["n"] / totals[r["Brand"]] * 100, axis=1)

            fig_b = go.Figure()
            for b in FOCUS_BRANDS:
                bsub = cross[cross["Brand"] == b]
                fig_b.add_trace(go.Bar(
                    x=bsub[sel_col], y=bsub["pct"],
                    name=b,
                    marker=dict(color=BRAND_COLORS[b], line=dict(color="#FFFFFF", width=0.5)),
                    hovertemplate=f"<b>{b}</b><br>%{{x}}: %{{y:.0f}}%%<extra></extra>",
                ))
            apply_layout(
                fig_b, height=300, barmode="group",
                xaxis=dict(title=chosen_label, title_font=dict(size=12, color=INK_SOFT)),
                yaxis=dict(title="% of brand's policies", title_font=dict(size=12, color=INK_SOFT),
                           ticksuffix="%"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            )
            st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar": False})

    interp = PARAM_INSIGHTS.get(sel_col, "")
    if interp:
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        implication_tile(st.container(), "Business Implication", interp, flavor="neutral")


# ----------------------------------------------------------------------------
#  TAB 4 — POLICY INSIGHTS (VARIABILITY)
# ----------------------------------------------------------------------------
with tab4:

    section_h2(
        "Policy Archetypes",
        "Every policy is classified into an access archetype based on how many utilization-management "
        "levers it imposes. The archetype mix reveals how concentrated the corpus is on the restrictive end."
    )

    df_arch = df_pair.copy()
    df_arch["Restriction count"] = restriction_count(df_arch)
    df_arch["Archetype"] = df_arch["Restriction count"].apply(archetype_label)

    arch_summary = (df_arch.groupby("Archetype")
                    .agg(Policies=("Policy ID", "count"),
                         MeanScore=("Access Score", "mean"))
                    .reindex(ARCHETYPE_ORDER).fillna(0))
    arch_brand = (df_arch.groupby(["Archetype", "Brand"]).size()
                  .unstack(fill_value=0).reindex(ARCHETYPE_ORDER).fillna(0))
    arch_brand = arch_brand.reindex(columns=FOCUS_BRANDS, fill_value=0)

    arch_cls = {"Open access": "open", "Standard access": "std", "Tight access": "tight"}
    arch_desc = {
        "Open access":     "≤ 2 utilization-management levers · most permissive policies",
        "Standard access": "3–4 levers · the prevailing payer template",
        "Tight access":    "≥ 5 levers · most restrictive policies in the corpus",
    }

    arch_cols = st.columns(3)
    for col, a in zip(arch_cols, ARCHETYPE_ORDER):
        n = int(arch_summary.loc[a, "Policies"])
        mean_s = arch_summary.loc[a, "MeanScore"]
        t_count = int(arch_brand.loc[a, "TREMFYA"])
        s_count = int(arch_brand.loc[a, "STELARA"])
        col.markdown(
            f"""
<div class="zs-arch {arch_cls[a]}">
  <div class="name">{a}</div>
  <div class="count">{n}<span class="u">policies</span></div>
  <div class="desc">{arch_desc[a]}<br>Mean access score: <b>{mean_s:.1f}</b></div>
  <div class="mix">
    <span class="t">TREMFYA · {t_count}</span>
    <span class="s">STELARA · {s_count}</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # Archetype mix stacked
    question("How is each brand's coverage distributed across access archetypes?")

    arch_pct = arch_brand.div(arch_brand.sum(axis=0), axis=1).fillna(0)
    fig_amix = go.Figure()
    for a in ARCHETYPE_ORDER:
        fig_amix.add_trace(go.Bar(
            y=FOCUS_BRANDS,
            x=arch_pct.loc[a, FOCUS_BRANDS].values * 100,
            orientation="h",
            name=a,
            marker=dict(color=ARCHETYPE_COLOR[a], line=dict(color="#FFFFFF", width=1)),
            hovertemplate=f"<b>{a}</b><br>%{{y}}: %{{x:.0f}}%% of policies<extra></extra>",
        ))
    apply_layout(
        fig_amix,
        barmode="stack",
        height=260,
        xaxis=dict(range=[0, 100], ticksuffix="%",
                   title="Share of brand's policies",
                   title_font=dict(size=12, color=INK_SOFT)),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig_amix, use_container_width=True, config={"displayModeBar": False})

    # Variability — restriction alignment in shared policies
    section_h2(
        "Restriction Alignment in Shared Policies",
        "For policies covering both brands, do payers apply the same restrictions to TREMFYA and "
        "STELARA, or do they differentiate?"
    )

    paired = df_focus_all.copy()
    grp = paired.groupby("Policy ID")["Brand"].nunique()
    paired_ids = grp[grp == 2].index.tolist()
    shared = paired[paired["Policy ID"].isin(paired_ids)]

    if len(paired_ids) >= 2:
        question(f"Across the {len(paired_ids)} shared policies, where do payers diverge between brands?")

        alignment_rows = []
        for col, val, label in RESTRICTION_DEFS:
            both = trem_only = stel_only = neither = 0
            for pid in paired_ids:
                p = shared[shared["Policy ID"] == pid]
                t_has = (p[p["Brand"] == "TREMFYA"][col] == val).any()
                s_has = (p[p["Brand"] == "STELARA"][col] == val).any()
                if t_has and s_has:   both += 1
                elif t_has:            trem_only += 1
                elif s_has:            stel_only += 1
                else:                  neither += 1
            total = both + trem_only + stel_only + neither
            if total == 0: continue
            alignment_rows.append({
                "Restriction": label,
                "Both brands restricted":   both / total * 100,
                "TREMFYA only":             trem_only / total * 100,
                "STELARA only":             stel_only / total * 100,
                "Neither":                  neither / total * 100,
            })
        align_df = pd.DataFrame(alignment_rows)
        align_df["_sort"] = align_df["Both brands restricted"] + \
                            align_df["TREMFYA only"] + align_df["STELARA only"]
        align_df = align_df.sort_values("_sort").drop(columns=["_sort"])

        align_segments = [
            ("Both brands restricted", "#475569"),
            ("TREMFYA only",            TREMFYA_C),
            ("STELARA only",            STELARA_C),
            ("Neither",                 LINE_SOFT),
        ]
        fig_align = go.Figure()
        for seg, color in align_segments:
            fig_align.add_trace(go.Bar(
                y=align_df["Restriction"],
                x=align_df[seg],
                orientation="h",
                name=seg,
                marker=dict(color=color, line=dict(color="#FFFFFF", width=1)),
                hovertemplate=f"<b>{seg}</b><br>%{{y}}: %{{x:.0f}}%% of shared policies<extra></extra>",
            ))
        apply_layout(
            fig_align,
            barmode="stack",
            height=max(280, 48 * len(align_df) + 80),
            xaxis=dict(range=[0, 100], ticksuffix="%",
                       title="Share of shared policies",
                       title_font=dict(size=12, color=INK_SOFT)),
            yaxis=dict(title=""),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        st.plotly_chart(fig_align, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Insufficient policies covering both brands to compute alignment.")

    # Variability score
    section_h2("Business Implications")

    t_std = df_focus_all[df_focus_all["Brand"] == "TREMFYA"]["Access Score"].std()
    s_std = df_focus_all[df_focus_all["Brand"] == "STELARA"]["Access Score"].std()

    impl_cols = st.columns(3)
    tight_share = arch_summary.loc["Tight access", "Policies"] / max(arch_summary["Policies"].sum(), 1) * 100
    implication_tile(impl_cols[0], "Restriction concentration",
                     f"<b>{tight_share:.0f}%</b> of policies fall in the Tight Access archetype "
                     f"(≥5 levers). The corpus is concentrated on the restrictive end — open-access "
                     f"policies are the exception, not the rule.",
                     flavor="neutral")
    if not np.isnan(t_std) and not np.isnan(s_std):
        more_var = "TREMFYA" if t_std > s_std else "STELARA"
        implication_tile(impl_cols[1], "Access predictability",
                         f"<b>{more_var}</b> shows greater policy-to-policy variability "
                         f"(standard deviation: TREMFYA {t_std:.1f} vs STELARA {s_std:.1f}). "
                         f"Plan-level access for the more variable brand is harder to predict.",
                         flavor="tremfya" if more_var == "TREMFYA" else "stelara")
    implication_tile(impl_cols[2], "Targeted intervention",
                     "Focus negotiation effort on payers in the Tight Access archetype — "
                     "moving even a subset of these to Standard Access archetype would meaningfully "
                     "expand the addressable patient population.",
                     flavor="neutral")


# ----------------------------------------------------------------------------
#  TAB 5 — POLICY EXPLORER
# ----------------------------------------------------------------------------
with tab5:

    section_h2(
        "Policy Explorer",
        "Drill into individual policy records. Select a brand, then a policy, to see the full "
        "extracted parameter set in a clean format."
    )

    nav1, nav2 = st.columns([1, 3])
    with nav1:
        explore_brand = st.radio(
            "Brand",
            options=FOCUS_BRANDS,
            index=0,
            horizontal=False,
        )
    with nav2:
        sort_choice = st.radio(
            "Sort policies by",
            options=["Most restrictive first", "Most open first", "Policy ID"],
            index=0,
            horizontal=True,
        )

    sub = df_focus_all[df_focus_all["Brand"] == explore_brand].copy()
    sub = sub[sub["Access Score"].between(score_range[0], score_range[1])]
    sub = sub[sub["Access Tier"].isin(selected_tiers)]

    if sort_choice == "Most restrictive first":
        sub = sub.sort_values("Access Score", ascending=True, na_position="last")
    elif sort_choice == "Most open first":
        sub = sub.sort_values("Access Score", ascending=False, na_position="last")
    else:
        sub = sub.sort_values("Policy ID")

    if len(sub) == 0:
        st.info(f"No {explore_brand} policies match the current filters.")
    else:
        def policy_label(row):
            score = f"{int(row['Access Score'])}" if pd.notna(row["Access Score"]) else "—"
            return f"{row['Policy #']}  ·  Score {score}  ·  {row['Access Tier']}"

        sub["__label"] = sub.apply(policy_label, axis=1)

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        compare = st.toggle("Compare two policies side by side", value=False)

        if not compare:
            chosen = st.selectbox(
                f"Select a {explore_brand} policy",
                options=sub["__label"].tolist(),
                index=0,
            )
            panels = [sub[sub["__label"] == chosen].iloc[0]]
        else:
            cc1, cc2 = st.columns(2)
            with cc1:
                c1 = st.selectbox("Policy A", options=sub["__label"].tolist(), index=0, key="pa")
            with cc2:
                idx_b = 1 if len(sub) > 1 else 0
                c2 = st.selectbox("Policy B", options=sub["__label"].tolist(), index=idx_b, key="pb")
            panels = [sub[sub["__label"] == c1].iloc[0], sub[sub["__label"] == c2].iloc[0]]

        st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

        cols_panel = st.columns(len(panels), gap="medium")
        for panel_col, row in zip(cols_panel, panels):
            with panel_col:
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
      <div style="font-family:'Fraunces',serif; font-size:32px; font-weight:600;
                  color:{INK}; line-height:1;">{score_html}<span style="font-size:14px;
                  color:{SLATE}; font-family:Manrope; margin-left:6px;">/ 80</span></div>
      <div style="font-size:11px; color:{SLATE}; margin-top:4px; letter-spacing:0.08em;
                  text-transform:uppercase; font-weight:600;">Access score</div>
    </div>
    <div style="background:{tier_color}; color:#FFFFFF; padding:5px 12px; border-radius:2px;
                font-size:11px; font-weight:700; letter-spacing:0.08em;
                text-transform:uppercase;">{tier}</div>
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )

                def field_html(label, value):
                    if pd.isna(value) or str(value).strip() in ("", "nan", "None"):
                        value = "—"
                    return f"""
<div class="zs-field">
  <div class="zs-field-label">{label}</div>
  <div class="zs-field-value">{value}</div>
</div>
"""

                init_auth = (f"{int(row['Initial Auth (months)'])} months"
                             if pd.notna(row['Initial Auth (months)']) else
                             str(row.get('Initial Authorization Duration(in-months)') or '—'))
                reauth = (f"{int(row['Reauth (months)'])} months"
                          if pd.notna(row['Reauth (months)']) else
                          str(row.get('Reauthorization Duration(in-months)') or '—'))

                fields = "".join([
                    field_html("Age criterion", row["Age Criterion"]),
                    field_html("Specialist", row["Specialist Detail"]),
                    field_html("Step therapy", row["Step Therapy"]),
                    field_html("Brand-step requirements",
                               f"{int(row['Brand Steps'])}" if pd.notna(row['Brand Steps']) else "—"),
                    field_html("Generic-step requirements",
                               f"{int(row['Generic Steps'])}" if pd.notna(row['Generic Steps']) else "—"),
                    field_html("Phototherapy step", row["Phototherapy Step"]),
                    field_html("TB test", row["TB Test"]),
                    field_html("Quantity limit", row["Quantity Limit"]),
                    field_html("Initial authorization", init_auth),
                    field_html("Reauthorization duration", reauth),
                ])
                st.markdown(fields, unsafe_allow_html=True)

                step_text   = row.get("Step Therapy Requirements Documented in Policy")
                reauth_text = row.get("Reauthorization Requirements Documented in Policy")
                qty_text    = row.get("Quantity Limits")

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
  <span>{df_focus_all['Policy ID'].nunique()} policies analyzed · TREMFYA & STELARA in focus</span>
</div>
""",
    unsafe_allow_html=True,
)
