"""
Plaque Psoriasis Market Access Intelligence
A ZS-style client-ready dashboard built on extracted prior-authorization policy data.

Single-file Streamlit application. To run locally:
    streamlit run app.py

The app loads `PA_Gold_Standard_Dataset_v5.xlsx` (sheet: "Gold Standard") from the
working directory by default; if not found, a file uploader is shown.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Optional

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
INK         = "#0E1B2C"   # deep navy, primary text
INK_SOFT    = "#2B3A52"
PAPER       = "#F6F1E6"   # cream background
PAPER_DEEP  = "#EDE6D4"   # subtle panel
BONE        = "#E1D9C5"
LINE        = "#C9BFA6"
AMBER       = "#C8954A"   # signature accent
AMBER_DEEP  = "#9C7330"
CORAL       = "#C25437"   # restriction signal
SAGE        = "#3F6B6B"   # open access signal
SLATE       = "#5B6B82"
GOLD_LIGHT  = "#E6CC95"

# Access tier palette — graduated from restrictive (warm) to open (cool)
ACCESS_TIER_ORDER = ["Highly Restrictive", "Restricted", "Moderate", "Open", "Highly Open"]
ACCESS_TIER_COLOR = {
    "Highly Restrictive": "#8B2E1F",
    "Restricted":         "#C25437",
    "Moderate":           "#C8954A",
    "Open":               "#6B8E6B",
    "Highly Open":        "#3F6B6B",
    "Unscored":           "#9A9A8B",
}

# Plotly theme aligned to the design system
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Manrope, -apple-system, BlinkMacSystemFont, sans-serif",
              color=INK, size=13),
    title=dict(font=dict(family="Fraunces, Georgia, serif", color=INK, size=18)),
    margin=dict(l=20, r=20, t=50, b=20),
    xaxis=dict(showgrid=False, linecolor=LINE, ticks="outside", tickcolor=LINE),
    yaxis=dict(gridcolor="rgba(201,191,166,0.35)", linecolor=LINE,
               ticks="outside", tickcolor=LINE, zeroline=False),
    legend=dict(font=dict(size=12, color=INK_SOFT), bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="#FFFBF0", bordercolor=AMBER, font_family="Manrope",
                    font_color=INK),
)


def apply_layout(fig: go.Figure, **overrides) -> go.Figure:
    """Merge PLOTLY_LAYOUT with per-chart overrides.

    Performs a shallow merge for dict-valued keys (xaxis, yaxis, legend, etc.)
    so chart-specific tweaks add to — rather than collide with — the defaults.
    """
    merged = {k: (dict(v) if isinstance(v, dict) else v) for k, v in PLOTLY_LAYOUT.items()}
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v
    fig.update_layout(**merged)
    return fig

# ----------------------------------------------------------------------------
#  Custom CSS — editorial, refined, consultant
# ----------------------------------------------------------------------------
CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Manrope:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"]  {{
    font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
    color: {INK};
}}

.stApp {{
    background:
      radial-gradient(1200px 600px at 0% -10%, rgba(200,149,74,0.10), transparent 60%),
      radial-gradient(900px 500px at 100% 0%, rgba(63,107,107,0.08), transparent 60%),
      linear-gradient(180deg, {PAPER} 0%, #F2ECDF 100%);
    color: {INK};
}}

/* Remove streamlit default chrome */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header[data-testid="stHeader"] {{
    background: transparent;
}}

/* Main container padding */
section.main > div.block-container {{
    padding-top: 1.2rem;
    padding-bottom: 4rem;
    max-width: 1400px;
}}

/* ---------- Editorial header ---------- */
.zs-masthead {{
    border-top: 4px solid {INK};
    border-bottom: 1px solid {LINE};
    padding: 22px 0 18px 0;
    margin-bottom: 28px;
}}
.zs-eyebrow {{
    font-family: 'Manrope', sans-serif;
    font-size: 11px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: {AMBER_DEEP};
    font-weight: 600;
    margin-bottom: 6px;
}}
.zs-title {{
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 600;
    font-size: 44px;
    line-height: 1.04;
    letter-spacing: -0.02em;
    color: {INK};
    margin: 0;
}}
.zs-title em {{
    font-style: italic;
    color: {AMBER_DEEP};
    font-weight: 500;
}}
.zs-subtitle {{
    font-family: 'Manrope', sans-serif;
    font-size: 15px;
    color: {SLATE};
    margin-top: 10px;
    max-width: 780px;
    line-height: 1.5;
}}
.zs-meta-row {{
    display: flex;
    gap: 28px;
    margin-top: 16px;
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {INK_SOFT};
    font-weight: 500;
}}
.zs-meta-row span b {{
    color: {INK};
    font-weight: 700;
}}

/* ---------- Section headers ---------- */
.zs-section {{
    margin: 36px 0 6px 0;
}}
.zs-section-eyebrow {{
    font-size: 11px;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: {AMBER_DEEP};
    font-weight: 700;
    margin-bottom: 4px;
}}
.zs-section-title {{
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 600;
    font-size: 26px;
    line-height: 1.15;
    letter-spacing: -0.01em;
    color: {INK};
    margin: 0 0 6px 0;
}}
.zs-section-deck {{
    font-size: 14px;
    color: {SLATE};
    max-width: 820px;
    line-height: 1.55;
    margin-bottom: 18px;
}}
.zs-divider {{
    border-top: 1px solid {LINE};
    margin: 28px 0 18px 0;
}}

/* ---------- KPI cards ---------- */
.zs-kpi {{
    background: {PAPER};
    border: 1px solid {LINE};
    border-radius: 2px;
    padding: 18px 20px 16px 20px;
    position: relative;
    overflow: hidden;
    height: 100%;
}}
.zs-kpi::before {{
    content: "";
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 3px;
    background: {AMBER};
}}
.zs-kpi-label {{
    font-size: 11px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {SLATE};
    font-weight: 600;
    margin-bottom: 8px;
    line-height: 1.3;
}}
.zs-kpi-value {{
    font-family: 'Fraunces', Georgia, serif;
    font-size: 38px;
    font-weight: 600;
    color: {INK};
    line-height: 1;
    letter-spacing: -0.02em;
}}
.zs-kpi-unit {{
    font-size: 14px;
    color: {SLATE};
    font-weight: 500;
    margin-left: 4px;
}}
.zs-kpi-foot {{
    font-size: 12px;
    color: {INK_SOFT};
    margin-top: 8px;
    line-height: 1.4;
}}
.zs-kpi.accent::before {{ background: {SAGE}; }}
.zs-kpi.warn::before    {{ background: {CORAL}; }}

/* ---------- Insight / narrative blocks ---------- */
.zs-pullquote {{
    border-left: 3px solid {AMBER};
    background: rgba(200,149,74,0.06);
    padding: 16px 18px 16px 22px;
    margin: 18px 0;
    font-family: 'Fraunces', Georgia, serif;
    font-size: 17px;
    line-height: 1.5;
    font-weight: 500;
    color: {INK};
    font-style: italic;
}}
.zs-pullquote strong {{
    color: {AMBER_DEEP};
    font-style: normal;
    font-weight: 700;
}}

.zs-caption {{
    font-size: 13.5px;
    line-height: 1.6;
    color: {INK_SOFT};
    margin: 6px 0 14px 0;
    max-width: 820px;
}}

.zs-finding {{
    background: {PAPER};
    border: 1px solid {LINE};
    border-left: 3px solid {INK};
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 13.5px;
    line-height: 1.55;
    color: {INK};
}}
.zs-finding b {{
    color: {INK};
    font-weight: 700;
}}
.zs-finding .tag {{
    display: inline-block;
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    background: {INK};
    color: {PAPER};
    padding: 3px 8px;
    margin-right: 10px;
    font-weight: 700;
}}

/* ---------- Tabs ---------- */
div[data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid {LINE};
    padding-bottom: 0;
}}
button[data-baseweb="tab"] {{
    font-family: 'Manrope', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.04em !important;
    color: {SLATE} !important;
    background: transparent !important;
    padding: 12px 18px !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {INK} !important;
    border-bottom-color: {AMBER} !important;
    background: transparent !important;
}}
div[data-baseweb="tab-panel"] {{
    padding-top: 20px;
}}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {INK} 0%, #1A2A42 100%);
    border-right: 1px solid {INK};
}}
section[data-testid="stSidebar"] * {{
    color: {PAPER} !important;
}}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {{
    color: {PAPER} !important;
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 600;
}}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMultiSelect label {{
    color: {GOLD_LIGHT} !important;
    font-size: 11px !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    font-weight: 600 !important;
}}
.zs-sidebar-eyebrow {{
    font-size: 10px !important;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: {AMBER} !important;
    font-weight: 700;
    margin-top: 8px;
    margin-bottom: 4px;
}}
.zs-sidebar-title {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-size: 22px;
    line-height: 1.15;
    font-weight: 600;
    color: {PAPER} !important;
    margin-bottom: 16px;
}}
.zs-sidebar-note {{
    font-size: 11.5px;
    color: rgba(246, 241, 230, 0.6) !important;
    line-height: 1.5;
    margin-top: 18px;
    border-top: 1px solid rgba(246,241,230,0.15);
    padding-top: 14px;
}}

/* Multiselect styling inside the dark sidebar */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background-color: rgba(255,255,255,0.06) !important;
    border-color: rgba(246,241,230,0.18) !important;
    color: {PAPER} !important;
}}
section[data-testid="stSidebar"] [data-baseweb="tag"] {{
    background-color: {AMBER} !important;
    color: {INK} !important;
}}
section[data-testid="stSidebar"] [data-baseweb="tag"] span {{
    color: {INK} !important;
    font-weight: 600;
}}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div > div {{
    background-color: {AMBER} !important;
}}

/* ---------- Dataframes ---------- */
[data-testid="stDataFrame"] {{
    background: {PAPER};
    border: 1px solid {LINE};
    border-radius: 2px;
}}

/* ---------- Footer ---------- */
.zs-footer {{
    margin-top: 56px;
    padding-top: 18px;
    border-top: 1px solid {LINE};
    font-size: 11.5px;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: {SLATE};
    display: flex;
    justify-content: space-between;
}}

/* Expander tweaks */
.streamlit-expanderHeader {{
    font-family: 'Manrope', sans-serif;
    font-weight: 600;
    color: {INK};
    background: {PAPER};
    border: 1px solid {LINE} !important;
    border-radius: 2px !important;
}}

/* Tighter spacing for metric rows */
.stColumn {{ padding: 0 8px; }}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================================
#  DATA LOADING & CLEANING
# ============================================================================

DEFAULT_PATHS = [
    "PA_Gold_Standard_Dataset_v5.xlsx",
    "data/PA_Gold_Standard_Dataset_v5.xlsx",
    "./PA_Gold_Standard_Dataset_v5.xlsx",
    "/mnt/user-data/uploads/PA_Gold_Standard_Dataset_v5.xlsx",
]

SHEET_NAME = "Gold Standard"


@st.cache_data(show_spinner=False)
def load_workbook(source_bytes: bytes, _source_label: str = "") -> Optional[pd.DataFrame]:
    """Load the gold-standard sheet from xlsx bytes.

    Caching keys on the file bytes (immutable) rather than on the UploadedFile
    object, which is safer across Streamlit reruns. `engine="openpyxl"` is
    pinned so the dependency is explicit; pair this with `openpyxl` in
    requirements.txt.
    """
    buf = io.BytesIO(source_bytes)
    try:
        return pd.read_excel(buf, sheet_name=SHEET_NAME, engine="openpyxl")
    except ValueError:
        # "Gold Standard" sheet not present in this workbook — fall back to first sheet
        buf.seek(0)
        return pd.read_excel(buf, engine="openpyxl")


def _read_source_bytes(source) -> Optional[bytes]:
    """Return the raw bytes for either a local path or an UploadedFile."""
    if source is None:
        return None
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes()
    # Streamlit UploadedFile
    if hasattr(source, "getvalue"):
        return source.getvalue()
    if hasattr(source, "read"):
        return source.read()
    return None


def find_local_file() -> Optional[str]:
    for p in DEFAULT_PATHS:
        if Path(p).exists():
            return p
    return None


def _parse_duration(v):
    """Parse a duration cell into a float number of months, or NaN."""
    if pd.isna(v):
        return np.nan
    s = str(v).strip()
    if s == "" or s.lower() in {"unspecified", "n/a", "na", "none", "nan"}:
        return np.nan
    # Pull leading number if present (e.g. "12 months" -> 12)
    m = re.match(r"^\s*(\d+(?:\.\d+)?)", s)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return np.nan
    return np.nan


def _yes_no_clean(v):
    if pd.isna(v):
        return "Not specified"
    s = str(v).strip().lower()
    if s in {"yes", "y", "true"}:
        return "Yes"
    if s in {"no", "n", "false"}:
        return "No"
    return "Not specified"


def _has_meaningful_text(v) -> bool:
    """True if the cell contains actual policy language (not blank / 'No')."""
    if pd.isna(v):
        return False
    s = str(v).strip()
    if s == "" or s.lower() in {"no", "none", "n/a", "na", "unspecified", "not specified", "nan"}:
        return False
    return len(s) > 3


def access_tier(score) -> str:
    if pd.isna(score):
        return "Unscored"
    s = float(score)
    if s <= 25:   return "Highly Restrictive"
    if s <= 40:   return "Restricted"
    if s <= 55:   return "Moderate"
    if s <= 70:   return "Open"
    return "Highly Open"


@st.cache_data(show_spinner=False)
def prepare(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()

    # Standardize strings (handle both legacy object and pandas-3 str dtypes)
    str_cols = [c for c in df.columns
                if df[c].dtype == object or pd.api.types.is_string_dtype(df[c])]
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": np.nan, "NaN": np.nan, "None": np.nan, "": np.nan})

    # Pretty brand
    if "Brand" in df.columns:
        df["Brand"] = df["Brand"].fillna("Unknown").astype(str).str.title()

    # Access Score numeric
    df["Access Score"] = pd.to_numeric(df["Access Score"], errors="coerce")
    df["Access Tier"]  = df["Access Score"].apply(access_tier)

    # Durations
    df["Initial Auth (months)"] = df["Initial Authorization Duration(in-months)"].apply(_parse_duration)
    df["Reauth (months)"]       = df["Reauthorization Duration(in-months)"].apply(_parse_duration)

    # Restriction flags ---------------------------------------------------
    df["TB Test"] = df["TB Test required"].apply(_yes_no_clean)

    df["Phototherapy Step"] = df["Step through-Phototherapy"].apply(_yes_no_clean)

    df["Reauthorization"] = df["Reauthorization Required"].apply(
        lambda v: "Required" if str(v).strip().lower() == "yes" else "Not specified"
    )

    # Quantity limit: meaningful text or "Yes"
    def qlim_flag(v):
        if pd.isna(v):
            return "Not specified"
        s = str(v).strip().lower()
        if s in {"yes"} or len(str(v).strip()) > 10:
            return "Yes"
        if s == "no":
            return "No"
        return "Not specified"
    df["Quantity Limit"] = df["Quantity Limits"].apply(qlim_flag)

    # Step therapy presence (real policy language, not blank/no)
    df["Step Therapy Documented"] = df["Step Therapy Requirements Documented in Policy"].apply(
        lambda v: "Yes" if _has_meaningful_text(v) else "No / Not specified"
    )

    # Step counts -> numeric
    df["Brand Steps"]   = pd.to_numeric(df["Number of Steps through Brands"], errors="coerce")
    df["Generic Steps"] = pd.to_numeric(df["Number of Steps through Generic"], errors="coerce")
    df["Total Steps"]   = df[["Brand Steps", "Generic Steps"]].sum(axis=1, min_count=1)

    # Specialist
    df["Specialist Required"] = df["Specialist Types"].apply(
        lambda v: "Yes" if _has_meaningful_text(v) else "Not specified"
    )

    # Age
    df["Age Criterion"] = df["Age"].fillna("Not specified")

    # Policy display label
    df["Policy ID"] = df["Filename"].astype(str).str.replace(".pdf", "", regex=False)

    # Sequential policy label: stable rank by first appearance
    unique_policies = df["Policy ID"].drop_duplicates().reset_index(drop=True)
    policy_rank = {pid: idx + 1 for idx, pid in enumerate(unique_policies)}
    df["Policy #"] = df["Policy ID"].map(policy_rank).apply(lambda i: f"Policy {i:02d}")

    return df


# ============================================================================
#  ANALYSIS HELPERS
# ============================================================================

RESTRICTION_FIELDS = [
    ("Step Therapy Documented", "Yes",      "Step therapy required"),
    ("TB Test",                  "Yes",      "TB test required"),
    ("Quantity Limit",           "Yes",      "Quantity limits imposed"),
    ("Specialist Required",      "Yes",      "Specialist prescriber required"),
    ("Phototherapy Step",        "Yes",      "Phototherapy step required"),
    ("Reauthorization",          "Required", "Reauthorization required"),
]


def restriction_prevalence(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(df)
    if n == 0:
        return pd.DataFrame(columns=["Restriction", "Count", "Share"])
    for col, val, label in RESTRICTION_FIELDS:
        c = int((df[col] == val).sum())
        rows.append({"Restriction": label, "Count": c, "Share": c / n})
    return pd.DataFrame(rows).sort_values("Share", ascending=True)


def restriction_count_per_row(df: pd.DataFrame) -> pd.Series:
    parts = []
    for col, val, _ in RESTRICTION_FIELDS:
        parts.append((df[col] == val).astype(int))
    return sum(parts) if parts else pd.Series([0] * len(df), index=df.index)


# ============================================================================
#  RENDERING HELPERS
# ============================================================================

def render_masthead(df: pd.DataFrame):
    n_policies = df["Policy ID"].nunique()
    n_brands   = df["Brand"].nunique()
    n_rows     = len(df)
    st.markdown(
        f"""
<div class="zs-masthead">
  <div class="zs-eyebrow">Market Access Intelligence · Plaque Psoriasis</div>
  <h1 class="zs-title">The shape of <em>access</em> in plaque-psoriasis policies</h1>
  <div class="zs-subtitle">
    A consultant view of the prior-authorization signals extracted from payer policy
    documents — quantifying how restrictively brands are managed, where utilization
    barriers cluster, and which brands win or lose on access.
  </div>
  <div class="zs-meta-row">
    <span><b>{n_policies}</b> &nbsp;policies analyzed</span>
    <span><b>{n_brands}</b> &nbsp;brands covered</span>
    <span><b>{n_rows}</b> &nbsp;brand-policy observations</span>
    <span>Source · Extracted PA policy corpus</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def section_header(eyebrow: str, title: str, deck: str = ""):
    st.markdown(
        f"""
<div class="zs-section">
  <div class="zs-section-eyebrow">{eyebrow}</div>
  <h2 class="zs-section-title">{title}</h2>
  {f'<div class="zs-section-deck">{deck}</div>' if deck else ''}
</div>
""",
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, unit: str = "", foot: str = "", flavor: str = ""):
    cls = "zs-kpi"
    if flavor == "accent": cls += " accent"
    if flavor == "warn":   cls += " warn"
    st.markdown(
        f"""
<div class="{cls}">
  <div class="zs-kpi-label">{label}</div>
  <div class="zs-kpi-value">{value}<span class="zs-kpi-unit">{unit}</span></div>
  <div class="zs-kpi-foot">{foot}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def pullquote(html: str):
    st.markdown(f'<div class="zs-pullquote">{html}</div>', unsafe_allow_html=True)


def caption(html: str):
    st.markdown(f'<div class="zs-caption">{html}</div>', unsafe_allow_html=True)


def finding(tag: str, html: str):
    st.markdown(
        f'<div class="zs-finding"><span class="tag">{tag}</span>{html}</div>',
        unsafe_allow_html=True,
    )


# ============================================================================
#  DATA INGESTION (sidebar / fallback uploader)
# ============================================================================

st.sidebar.markdown('<div class="zs-sidebar-eyebrow">ZS · Market Access</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="zs-sidebar-title">PsO Policy Lens</div>', unsafe_allow_html=True)

local_path = find_local_file()
df_raw: Optional[pd.DataFrame] = None

def _load_with_friendly_errors(source, label: str) -> Optional[pd.DataFrame]:
    """Read xlsx bytes through load_workbook with user-friendly error handling."""
    try:
        raw = _read_source_bytes(source)
        if raw is None:
            return None
        return load_workbook(raw, label)
    except ImportError as e:
        st.error(
            "**Missing dependency.** This deployment can't read `.xlsx` files because "
            "`openpyxl` is not installed.\n\n"
            "**Fix:** add a `requirements.txt` to the repo with:\n\n"
            "```\nstreamlit>=1.32\npandas>=2.0\nnumpy>=1.24\nplotly>=5.18\nopenpyxl>=3.1\n```\n\n"
            "Then redeploy. (Underlying error: `" + str(e) + "`)"
        )
        st.stop()
    except Exception as e:
        st.error(f"Could not read the workbook ({label}). Details: `{e}`")
        st.stop()

if local_path is not None:
    df_raw = _load_with_friendly_errors(local_path, local_path)
else:
    st.sidebar.markdown("##### Upload data")
    upl = st.sidebar.file_uploader(
        "Gold-standard extract",
        type=["xlsx"],
        help="Expecting the `Gold Standard` sheet from the PA extraction workbook.",
        label_visibility="collapsed",
    )
    if upl is not None:
        df_raw = _load_with_friendly_errors(upl, upl.name)

if df_raw is None:
    render_masthead(pd.DataFrame({"Policy ID": [], "Brand": []}))
    st.warning(
        "No dataset found in the working directory. Upload "
        "`PA_Gold_Standard_Dataset_v5.xlsx` from the sidebar to begin."
    )
    st.stop()

df_all = prepare(df_raw)

# ============================================================================
#  SIDEBAR FILTERS
# ============================================================================

st.sidebar.markdown("---")
st.sidebar.markdown('<div class="zs-sidebar-eyebrow">Refine the view</div>', unsafe_allow_html=True)

brand_options = sorted(df_all["Brand"].dropna().unique().tolist())
default_brands = brand_options  # show all by default

selected_brands = st.sidebar.multiselect(
    "Brand",
    options=brand_options,
    default=default_brands,
    help="Filter to specific PsO brands.",
)

tier_options = [t for t in ACCESS_TIER_ORDER + ["Unscored"] if t in df_all["Access Tier"].unique()]
selected_tiers = st.sidebar.multiselect(
    "Access tier",
    options=tier_options,
    default=tier_options,
)

score_min, score_max = int(df_all["Access Score"].min(skipna=True) or 0), int(df_all["Access Score"].max(skipna=True) or 80)
score_range = st.sidebar.slider(
    "Access score range",
    min_value=score_min, max_value=score_max,
    value=(score_min, score_max), step=5,
)

restriction_choices = [label for _, _, label in RESTRICTION_FIELDS]
selected_restrictions = st.sidebar.multiselect(
    "Must include restriction",
    options=restriction_choices,
    default=[],
    help="Narrow to policies that include the selected restrictions.",
)

st.sidebar.markdown(
    f'<div class="zs-sidebar-note">'
    f'Filters apply across all tabs. Reset by selecting all options.<br><br>'
    f'<b>{len(df_all)}</b> total brand–policy rows · '
    f'<b>{df_all["Policy ID"].nunique()}</b> unique policies'
    f'</div>',
    unsafe_allow_html=True,
)


# Apply filters
mask = (
    df_all["Brand"].isin(selected_brands) &
    df_all["Access Tier"].isin(selected_tiers) &
    df_all["Access Score"].between(score_range[0], score_range[1])
)
for label in selected_restrictions:
    for col, val, lbl in RESTRICTION_FIELDS:
        if lbl == label:
            mask &= (df_all[col] == val)
            break

df = df_all[mask].copy()

# ============================================================================
#  MASTHEAD
# ============================================================================

render_masthead(df_all)

if df.empty:
    st.info("No rows match the current filter combination. Loosen filters in the sidebar to continue.")
    st.stop()

# ============================================================================
#  TABS
# ============================================================================

tab_summary, tab_landscape, tab_brands, tab_restrictions, tab_explorer = st.tabs([
    "Executive Summary",
    "Access Landscape",
    "Brand Comparison",
    "Restriction Patterns",
    "Policy Explorer",
])

# ----------------------------------------------------------------------------
#  TAB 1 — EXECUTIVE SUMMARY
# ----------------------------------------------------------------------------
with tab_summary:

    section_header(
        "01 · The headline",
        "Where access stands today",
        "A single-page brief: how restrictive plaque-psoriasis policies are on average, "
        "which brands feel the most pressure, and what utilization-management levers payers "
        "are pulling most often."
    )

    # ---- KPI strip ---------------------------------------------------------
    n_policies = df["Policy ID"].nunique()
    n_brands   = df["Brand"].nunique()
    mean_score = df["Access Score"].mean()
    median_score = df["Access Score"].median()
    pct_restrictive = (df["Access Tier"].isin(["Highly Restrictive", "Restricted"])).mean() * 100
    pct_open        = (df["Access Tier"].isin(["Open", "Highly Open"])).mean() * 100
    avg_steps = df["Total Steps"].mean()

    most_common_restr = restriction_prevalence(df).sort_values("Share", ascending=False).iloc[0] if len(df) else None

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Mean access score", f"{mean_score:.1f}", "/ 80",
                 f"Median {median_score:.0f} · range 0–80")
    with c2:
        kpi_card("Restrictive share", f"{pct_restrictive:.0f}", "%",
                 "Policies scoring ≤ 40 — meaningful barriers to start", flavor="warn")
    with c3:
        kpi_card("Open-access share", f"{pct_open:.0f}", "%",
                 "Policies scoring > 55 — favorable terms", flavor="accent")
    with c4:
        kpi_card("Avg step-therapy hurdles", f"{avg_steps:.1f}" if pd.notna(avg_steps) else "—",
                 " steps", "Across brand + generic steps")
    with c5:
        if most_common_restr is not None:
            kpi_card("Most common UM lever",
                     f"{most_common_restr['Share']*100:.0f}",
                     "%",
                     f"{most_common_restr['Restriction']}")
        else:
            kpi_card("Most common UM lever", "—", "", "")

    # ---- Headline narrative ------------------------------------------------
    # Pick a real, data-driven pullquote
    top_brand_by_count = df.groupby("Brand")["Policy ID"].nunique().sort_values(ascending=False)
    leading_brand = top_brand_by_count.index[0] if len(top_brand_by_count) else "—"

    brand_means = df.groupby("Brand")["Access Score"].mean().dropna()
    qualifying = df.groupby("Brand").size()
    brand_means = brand_means[qualifying.reindex(brand_means.index).fillna(0) >= 3]
    if len(brand_means) >= 2:
        most_restricted_brand = brand_means.idxmin()
        most_open_brand       = brand_means.idxmax()
        gap = brand_means.max() - brand_means.min()
        gap_line = (f"<strong>{most_open_brand}</strong> enjoys the most favorable terms "
                    f"({brand_means.max():.0f}), while <strong>{most_restricted_brand}</strong> "
                    f"faces the tightest ({brand_means.min():.0f}) — a "
                    f"<strong>{gap:.0f}-point</strong> access gap.")
    else:
        gap_line = "Brand-level coverage volume is uneven; comparable means require ≥ 3 policies per brand."

    pullquote(
        f"The market-access picture is <strong>tilted toward restriction</strong>: "
        f"the typical PsO policy scores <strong>{mean_score:.0f}/80</strong>, with "
        f"<strong>{pct_restrictive:.0f}%</strong> of policies imposing meaningful step-therapy or "
        f"utilization barriers. {gap_line}"
    )

    # ---- The big-picture chart: access score distribution by tier ---------
    section_header(
        "02 · The access curve",
        "How policy access scores are distributed",
        "Each bar is a five-point bin of policy access scores. The color tells the access tier; "
        "the shape of the distribution tells the story."
    )

    # Build histogram
    df_hist = df.dropna(subset=["Access Score"]).copy()
    df_hist["Bin"] = pd.cut(df_hist["Access Score"], bins=np.arange(0, 86, 5), right=False)
    df_hist["BinCenter"] = df_hist["Bin"].apply(lambda b: b.left + 2.5 if pd.notna(b) else np.nan)
    hist_data = (
        df_hist.groupby(["BinCenter", "Access Tier"])
        .size()
        .reset_index(name="Count")
    )

    fig_hist = px.bar(
        hist_data,
        x="BinCenter", y="Count",
        color="Access Tier",
        color_discrete_map=ACCESS_TIER_COLOR,
        category_orders={"Access Tier": ACCESS_TIER_ORDER},
    )
    fig_hist.update_traces(marker_line_width=0)
    apply_layout(fig_hist,
                xaxis_title="Access Score (0 = most restrictive, 80 = most open)",
        yaxis_title="Number of policies",
        bargap=0.18,
        height=380,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=12, color=INK_SOFT)),
    )
    fig_hist.add_vline(x=mean_score, line_dash="dot", line_color=INK,
                       annotation_text=f"  Mean {mean_score:.1f}",
                       annotation_position="top right",
                       annotation_font_color=INK,
                       annotation_font_size=12)
    st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

    caption(
        "Read the curve: a left-skewed distribution would suggest payers are tightening access; "
        "a right-skewed one would signal accommodation. The current shape clusters around the "
        "moderate-to-restricted bands, with a notable tail of highly restrictive policies."
    )

    # ---- Two-column: restriction prevalence + tier mix ---------------------
    col_a, col_b = st.columns([1.2, 1.0], gap="large")

    with col_a:
        section_header(
            "03 · Payer toolkit",
            "Which utilization levers appear most often",
            "Share of policies imposing each type of restriction."
        )
        rp = restriction_prevalence(df)
        fig_rp = go.Figure()
        fig_rp.add_trace(go.Bar(
            y=rp["Restriction"],
            x=rp["Share"] * 100,
            orientation="h",
            marker=dict(color=AMBER, line=dict(color=AMBER_DEEP, width=0.5)),
            hovertemplate="<b>%{y}</b><br>%{x:.0f}%% of policies<extra></extra>",
            text=[f"{v*100:.0f}%" for v in rp["Share"]],
            textposition="outside",
            textfont=dict(color=INK, size=12),
        ))
        apply_layout(fig_rp,
                        height=320,
            xaxis_title="% of policies", yaxis_title="",
            xaxis=dict(range=[0, max(105, rp["Share"].max()*100 + 15)],
                       showgrid=False, ticksuffix="%", linecolor=LINE),
            showlegend=False,
        )
        st.plotly_chart(fig_rp, use_container_width=True, config={"displayModeBar": False})

    with col_b:
        section_header(
            "04 · The mix",
            "Access tier composition",
            "Where the corpus sits on the restriction spectrum."
        )
        tier_counts = df["Access Tier"].value_counts().reindex(
            ACCESS_TIER_ORDER + ["Unscored"]).dropna()
        fig_donut = go.Figure(go.Pie(
            labels=tier_counts.index,
            values=tier_counts.values,
            hole=0.62,
            marker=dict(colors=[ACCESS_TIER_COLOR.get(t, SLATE) for t in tier_counts.index],
                        line=dict(color=PAPER, width=2)),
            textinfo="percent",
            textfont=dict(color=PAPER, size=13, family="Manrope"),
            hovertemplate="<b>%{label}</b><br>%{value} policies (%{percent})<extra></extra>",
            sort=False,
        ))
        apply_layout(
            fig_donut,
            height=320,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05,
                        font=dict(size=12, color=INK_SOFT)),
            annotations=[dict(
                text=f"<b>{len(df)}</b><br><span style='font-size:11px;color:{SLATE}'>obs</span>",
                x=0.5, y=0.5, font=dict(family="Fraunces", size=22, color=INK),
                showarrow=False,
            )],
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})


# ----------------------------------------------------------------------------
#  TAB 2 — ACCESS LANDSCAPE
# ----------------------------------------------------------------------------
with tab_landscape:

    section_header(
        "01 · Where the variation lives",
        "Access scores vary more within brands than across them",
        "Each dot is a single payer policy. Brands with wide spreads carry significant "
        "policy-to-policy access volatility — meaning a patient's experience depends heavily "
        "on which plan they're on, not just which drug their doctor chose."
    )

    # Strip plot by brand sorted by mean score, only brands with ≥ 1 row
    brand_summary = df.groupby("Brand").agg(
        mean_score=("Access Score", "mean"),
        median_score=("Access Score", "median"),
        count=("Policy ID", "nunique"),
        min_score=("Access Score", "min"),
        max_score=("Access Score", "max"),
    ).reset_index().sort_values("mean_score", ascending=True)

    # Plot brands in order of mean score
    df_strip = df.copy()
    df_strip["Brand"] = pd.Categorical(df_strip["Brand"],
                                        categories=brand_summary["Brand"].tolist(),
                                        ordered=True)
    df_strip = df_strip.sort_values("Brand")

    fig_strip = px.strip(
        df_strip,
        x="Access Score", y="Brand",
        color="Access Tier",
        color_discrete_map=ACCESS_TIER_COLOR,
        category_orders={"Access Tier": ACCESS_TIER_ORDER,
                         "Brand": brand_summary["Brand"].tolist()},
        stripmode="overlay",
        hover_data={"Policy #": True, "Brand": False, "Access Tier": True, "Access Score": True},
    )
    fig_strip.update_traces(jitter=0.35, marker=dict(size=11, opacity=0.85,
                                                      line=dict(color=INK, width=0.4)))
    # Overlay brand mean dashes
    for _, row in brand_summary.iterrows():
        if pd.notna(row["mean_score"]):
            fig_strip.add_shape(
                type="line",
                x0=row["mean_score"], x1=row["mean_score"],
                y0=row["Brand"], y1=row["Brand"],
                xref="x", yref="y",
                line=dict(color=INK, width=0),
            )
    # Brand mean as a separate trace
    fig_strip.add_trace(go.Scatter(
        x=brand_summary["mean_score"],
        y=brand_summary["Brand"],
        mode="markers",
        marker=dict(symbol="line-ns", color=INK, size=18, line=dict(width=3, color=INK)),
        name="Brand mean",
        hovertemplate="<b>%{y}</b><br>Mean score: %{x:.1f}<extra></extra>",
        showlegend=True,
    ))
    apply_layout(fig_strip,
                height=max(380, 30 * len(brand_summary) + 120),
        xaxis_title="Access Score",
        yaxis_title="",
        xaxis=dict(range=[-5, 85], showgrid=True, gridcolor="rgba(201,191,166,0.35)",
                   linecolor=LINE, ticks="outside", tickcolor=LINE),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=11, color=INK_SOFT)),
    )
    st.plotly_chart(fig_strip, use_container_width=True, config={"displayModeBar": False})

    # Narrative findings ------------------------------------------------------
    bs = brand_summary.dropna(subset=["mean_score"]).copy()
    if len(bs) >= 2:
        bs_qual = bs[bs["count"] >= 3]
        if len(bs_qual) >= 2:
            best  = bs_qual.iloc[-1]
            worst = bs_qual.iloc[0]
            finding(
                "Brand spread",
                f"Among brands with sufficient coverage, <b>{best['Brand']}</b> "
                f"averages <b>{best['mean_score']:.0f}</b> on access vs. "
                f"<b>{worst['Brand']}</b> at <b>{worst['mean_score']:.0f}</b> — a "
                f"<b>{best['mean_score']-worst['mean_score']:.0f}-point</b> swing that "
                f"materially affects start rates, time-to-fill, and abandonment risk."
            )

        widest = bs[bs["count"] >= 2].assign(spread=lambda d: d["max_score"] - d["min_score"]).sort_values("spread", ascending=False)
        if len(widest):
            top = widest.iloc[0]
            finding(
                "Policy volatility",
                f"<b>{top['Brand']}</b> shows the widest policy-to-policy access spread "
                f"(<b>{top['spread']:.0f} points</b>, from {top['min_score']:.0f} to "
                f"{top['max_score']:.0f}) — suggesting account-level negotiation, not "
                f"clinical guidelines, is the swing factor."
            )

    # ---- Access vs. cumulative restrictions scatter ------------------------
    section_header(
        "02 · Restriction density vs. score",
        "The more levers a policy pulls, the lower the access score",
        "Validating the access-score logic: policies stacking multiple UM levers consistently "
        "cluster in the restrictive end of the spectrum."
    )

    df_sc = df.copy()
    df_sc["Restriction Count"] = restriction_count_per_row(df_sc)
    df_sc_n = df_sc.dropna(subset=["Access Score"])

    # Aggregate jitter for readability
    fig_sc = px.scatter(
        df_sc_n,
        x="Restriction Count", y="Access Score",
        color="Access Tier",
        color_discrete_map=ACCESS_TIER_COLOR,
        category_orders={"Access Tier": ACCESS_TIER_ORDER},
        hover_data={"Brand": True, "Policy #": True, "Restriction Count": True,
                    "Access Score": True, "Access Tier": False},
    )
    fig_sc.update_traces(marker=dict(size=12, opacity=0.78,
                                      line=dict(color=INK, width=0.5)))
    # Trend line via simple group means
    trend = df_sc_n.groupby("Restriction Count")["Access Score"].mean().reset_index()
    fig_sc.add_trace(go.Scatter(
        x=trend["Restriction Count"], y=trend["Access Score"],
        mode="lines+markers",
        line=dict(color=INK, width=2, dash="dot"),
        marker=dict(color=INK, size=8, symbol="diamond"),
        name="Mean by lever count",
        hovertemplate="<b>%{x} levers</b><br>Mean score: %{y:.1f}<extra></extra>",
    ))
    apply_layout(fig_sc,
                height=420,
        xaxis_title="Number of UM levers pulled in the policy",
        yaxis_title="Access Score",
        xaxis=dict(dtick=1, range=[-0.5, len(RESTRICTION_FIELDS) + 0.5], linecolor=LINE,
                   showgrid=False),
        yaxis=dict(range=[-5, 85], gridcolor="rgba(201,191,166,0.35)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=11, color=INK_SOFT)),
    )
    st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

    caption(
        "Every additional utilization-management lever drives the mean access score down — "
        "consistent with the scoring rubric and a useful sanity check for the extraction pipeline."
    )


# ----------------------------------------------------------------------------
#  TAB 3 — BRAND COMPARISON
# ----------------------------------------------------------------------------
with tab_brands:

    section_header(
        "01 · Head-to-head",
        "How brands stack up on access",
        "Brand-level averages, coverage volume, and access composition. Brands with very few "
        "policies are flagged for interpretive caution."
    )

    # Brand summary -----------------------------------------------------------
    bs = df.groupby("Brand").agg(
        Policies=("Policy ID", "nunique"),
        Mean=("Access Score", "mean"),
        Median=("Access Score", "median"),
        Min=("Access Score", "min"),
        Max=("Access Score", "max"),
    ).reset_index().sort_values("Mean", ascending=False)

    bs["Coverage"] = bs["Policies"].apply(
        lambda n: "✦ broad" if n >= 10 else ("◆ moderate" if n >= 3 else "· thin")
    )

    # Brand ranking chart -----------------------------------------------------
    fig_br = go.Figure()
    fig_br.add_trace(go.Bar(
        y=bs["Brand"],
        x=bs["Mean"],
        orientation="h",
        marker=dict(
            color=[ACCESS_TIER_COLOR.get(access_tier(v), AMBER) for v in bs["Mean"]],
            line=dict(color=INK, width=0.4),
        ),
        text=[f"{v:.0f}" for v in bs["Mean"]],
        textposition="outside",
        textfont=dict(color=INK, size=12, family="Manrope"),
        hovertemplate=("<b>%{y}</b><br>"
                       "Mean access score: %{x:.1f}<br>"
                       "Policies: %{customdata[0]}<br>"
                       "Range: %{customdata[1]:.0f}–%{customdata[2]:.0f}<extra></extra>"),
        customdata=bs[["Policies", "Min", "Max"]].values,
        showlegend=False,
    ))
    apply_layout(fig_br,
                height=max(360, 26 * len(bs) + 80),
        xaxis_title="Mean access score (higher = more open)",
        yaxis_title="",
        xaxis=dict(range=[0, 90], linecolor=LINE),
        yaxis=dict(categoryorder="array", categoryarray=bs["Brand"].tolist()[::-1],
                   linecolor=LINE),
    )
    fig_br.add_vline(x=df["Access Score"].mean(), line_dash="dot", line_color=INK_SOFT,
                     annotation_text=f"Corpus mean {df['Access Score'].mean():.0f}",
                     annotation_position="top right",
                     annotation_font_color=INK_SOFT, annotation_font_size=11)
    st.plotly_chart(fig_br, use_container_width=True, config={"displayModeBar": False})

    # Brand summary table -----------------------------------------------------
    section_header(
        "02 · Coverage & spread",
        "The numbers behind the chart",
        ""
    )
    show = bs.copy()
    show["Mean"]   = show["Mean"].round(1)
    show["Median"] = show["Median"].round(0)
    show["Range"]  = show.apply(lambda r: f"{r['Min']:.0f}–{r['Max']:.0f}" if pd.notna(r["Min"]) else "—", axis=1)
    show = show[["Brand", "Policies", "Coverage", "Mean", "Median", "Range"]]
    show = show.rename(columns={"Mean": "Mean score", "Median": "Median score"})
    st.dataframe(
        show,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Brand":        st.column_config.TextColumn("Brand", width="medium"),
            "Policies":     st.column_config.NumberColumn("Policies", help="Unique payer policies"),
            "Coverage":     st.column_config.TextColumn("Coverage depth"),
            "Mean score":   st.column_config.ProgressColumn(
                                "Mean score", format="%.1f", min_value=0, max_value=80,
                            ),
            "Median score": st.column_config.NumberColumn("Median", format="%.0f"),
            "Range":        st.column_config.TextColumn("Score range"),
        },
    )

    caption(
        "Brands with fewer than three policies should be read directionally — their averages "
        "can swing significantly with one additional observation."
    )

    # Brand restriction signature heatmap -------------------------------------
    section_header(
        "03 · Restriction signatures",
        "What each brand contends with",
        "For brands with enough coverage to compare, the cell shows the share of that brand's "
        "policies imposing each restriction. Darker = more pervasive."
    )

    brand_qual = bs[bs["Policies"] >= 2]["Brand"].tolist()
    if len(brand_qual) >= 2:
        rows = []
        for b in brand_qual:
            sub = df[df["Brand"] == b]
            n = len(sub)
            for col, val, label in RESTRICTION_FIELDS:
                share = (sub[col] == val).mean() if n else 0
                rows.append({"Brand": b, "Restriction": label, "Share": share})
        heat = pd.DataFrame(rows).pivot(index="Brand", columns="Restriction", values="Share")
        # Order brands by mean score descending
        heat = heat.reindex(bs[bs["Brand"].isin(brand_qual)]
                            .sort_values("Mean", ascending=False)["Brand"].tolist())
        # Order columns by overall prevalence
        col_order = restriction_prevalence(df).sort_values("Share", ascending=False)["Restriction"].tolist()
        heat = heat[[c for c in col_order if c in heat.columns]]

        fig_h = go.Figure(go.Heatmap(
            z=heat.values * 100,
            x=heat.columns,
            y=heat.index,
            colorscale=[[0, PAPER], [0.5, GOLD_LIGHT], [1, AMBER_DEEP]],
            zmin=0, zmax=100,
            text=[[f"{v:.0f}%" for v in row] for row in heat.values * 100],
            texttemplate="%{text}",
            textfont=dict(color=INK, size=11, family="Manrope"),
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.0f}%%<extra></extra>",
            colorbar=dict(title=dict(text="Share", font=dict(color=INK_SOFT, size=11)),
                          tickfont=dict(color=INK_SOFT, size=10),
                          ticksuffix="%", thickness=12, len=0.6, x=1.02),
        ))
        apply_layout(fig_h,
                        height=max(280, 32 * len(heat) + 140),
            xaxis=dict(side="top", tickangle=-22, linecolor=LINE),
            yaxis=dict(autorange="reversed", linecolor=LINE),
        )
        st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Need at least two brands with ≥ 2 policies to render the restriction-signature heatmap.")


# ----------------------------------------------------------------------------
#  TAB 4 — RESTRICTION PATTERNS
# ----------------------------------------------------------------------------
with tab_restrictions:

    section_header(
        "01 · The UM playbook",
        "How payers actually limit access",
        "A composite view of utilization management levers across the corpus — what's used, "
        "how intensely, and what it implies for the patient journey."
    )

    rp = restriction_prevalence(df).sort_values("Share", ascending=False).reset_index(drop=True)

    cols = st.columns(3)
    for i, (_, row) in enumerate(rp.iterrows()):
        with cols[i % 3]:
            kpi_card(
                row["Restriction"],
                f"{row['Share']*100:.0f}",
                "%",
                f"{int(row['Count'])} of {len(df)} brand-policy rows",
                flavor=("warn" if row["Share"] > 0.5 else ""),
            )

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

    # Step therapy intensity --------------------------------------------------
    section_header(
        "02 · Step therapy intensity",
        "How many therapies must a patient try first?",
        "Among policies that document step therapy, how many branded and generic steps are required."
    )

    steps_df = df.dropna(subset=["Total Steps"]).copy()
    if not steps_df.empty:
        col_l, col_r = st.columns([1.0, 1.0], gap="large")

        with col_l:
            # Total steps distribution
            sd = steps_df["Total Steps"].astype(int).value_counts().reset_index()
            sd.columns = ["Steps", "Count"]
            sd = sd.sort_values("Steps")
            fig_steps = go.Figure(go.Bar(
                x=sd["Steps"], y=sd["Count"],
                marker=dict(color=AMBER, line=dict(color=AMBER_DEEP, width=0.4)),
                text=sd["Count"], textposition="outside",
                textfont=dict(color=INK, size=12),
                hovertemplate="<b>%{x} step(s)</b><br>%{y} policies<extra></extra>",
            ))
            apply_layout(fig_steps,
                                height=320,
                xaxis_title="Total steps required",
                yaxis_title="Policies",
                xaxis=dict(dtick=1, linecolor=LINE),
                showlegend=False,
            )
            st.plotly_chart(fig_steps, use_container_width=True, config={"displayModeBar": False})

        with col_r:
            # Brand vs generic step composition
            comp = pd.DataFrame({
                "Type": ["Brand / biologic steps", "Generic / oral steps"],
                "Mean": [steps_df["Brand Steps"].mean(),
                         steps_df["Generic Steps"].mean()],
            })
            fig_comp = go.Figure(go.Bar(
                x=comp["Mean"], y=comp["Type"],
                orientation="h",
                marker=dict(color=[CORAL, SAGE],
                            line=dict(color=INK, width=0.4)),
                text=[f"{v:.1f}" for v in comp["Mean"]],
                textposition="outside",
                textfont=dict(color=INK, size=13),
                hovertemplate="<b>%{y}</b><br>Avg: %{x:.2f}<extra></extra>",
            ))
            apply_layout(fig_comp,
                                height=320,
                xaxis_title="Average number of steps",
                yaxis_title="",
                xaxis=dict(linecolor=LINE),
            )
            st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})

        caption(
            "Branded-biologic step-throughs are the dominant lever — typical of a "
            "competitive immunology category where payers steer toward preferred brands "
            "before approving newer entrants."
        )
    else:
        st.info("No step-count data available in the current filter.")

    # Authorization duration --------------------------------------------------
    section_header(
        "03 · Authorization duration",
        "How long is the leash?",
        "Shorter initial-authorization periods mean more frequent reauthorization touchpoints — "
        "an indirect access barrier that drives administrative burden for prescribers."
    )

    col_a, col_b = st.columns(2, gap="large")
    auth_df = df.dropna(subset=["Initial Auth (months)"]).copy()
    if not auth_df.empty:
        with col_a:
            ad = auth_df["Initial Auth (months)"].astype(int).value_counts().reset_index()
            ad.columns = ["Months", "Count"]
            ad = ad.sort_values("Months")
            fig_ad = go.Figure(go.Bar(
                x=ad["Months"].astype(str), y=ad["Count"],
                marker=dict(color=AMBER, line=dict(color=AMBER_DEEP, width=0.4)),
                text=ad["Count"], textposition="outside",
                textfont=dict(color=INK, size=12),
                hovertemplate="<b>%{x} mo</b><br>%{y} policies<extra></extra>",
            ))
            apply_layout(fig_ad,
                                height=300,
                title="Initial authorization (months)",
                xaxis_title="Months",
                yaxis_title="Policies",
                xaxis=dict(linecolor=LINE),
            )
            st.plotly_chart(fig_ad, use_container_width=True, config={"displayModeBar": False})

    reauth_df = df.dropna(subset=["Reauth (months)"]).copy()
    if not reauth_df.empty:
        with col_b:
            rd = reauth_df["Reauth (months)"].astype(int).value_counts().reset_index()
            rd.columns = ["Months", "Count"]
            rd = rd.sort_values("Months")
            fig_rd = go.Figure(go.Bar(
                x=rd["Months"].astype(str), y=rd["Count"],
                marker=dict(color=SAGE, line=dict(color="#2D5050", width=0.4)),
                text=rd["Count"], textposition="outside",
                textfont=dict(color=INK, size=12),
                hovertemplate="<b>%{x} mo</b><br>%{y} policies<extra></extra>",
            ))
            apply_layout(fig_rd,
                                height=300,
                title="Reauthorization duration (months)",
                xaxis_title="Months",
                yaxis_title="Policies",
                xaxis=dict(linecolor=LINE),
            )
            st.plotly_chart(fig_rd, use_container_width=True, config={"displayModeBar": False})

    if not auth_df.empty:
        median_init = auth_df["Initial Auth (months)"].median()
        share_short = (auth_df["Initial Auth (months)"] <= 6).mean() * 100
        finding(
            "Time on therapy",
            f"Median initial authorization is <b>{median_init:.0f} months</b>; "
            f"<b>{share_short:.0f}%</b> of scoring policies grant only six months or less, "
            f"compounding administrative friction at re-approval."
        )


# ----------------------------------------------------------------------------
#  TAB 5 — POLICY EXPLORER
# ----------------------------------------------------------------------------
with tab_explorer:

    section_header(
        "01 · Drill down",
        "Inspect specific brand–policy combinations",
        "A clean view of the underlying records, with full policy text available on expand. "
        "Use the search and sort to locate specific brand-policy combinations."
    )

    # Searchable filter ---------------------------------------------------
    q = st.text_input("Search by brand or policy text",
                      placeholder="e.g. STELARA, dermatologist, BSA, methotrexate…",
                      label_visibility="visible")

    df_expl = df.copy()
    if q.strip():
        qlow = q.strip().lower()
        text_cols = ["Brand", "Policy ID",
                     "Step Therapy Requirements Documented in Policy",
                     "Reauthorization Requirements Documented in Policy",
                     "Specialist Types", "Quantity Limits", "Age Criterion"]
        cond = pd.Series(False, index=df_expl.index)
        for c in text_cols:
            if c in df_expl.columns:
                cond |= df_expl[c].astype(str).str.lower().str.contains(qlow, na=False)
        df_expl = df_expl[cond]

    sort_col, sort_dir = st.columns([1, 1])
    with sort_col:
        sort_by = st.selectbox(
            "Sort by",
            options=["Access Score", "Brand", "Initial Auth (months)", "Total Steps"],
            index=0,
        )
    with sort_dir:
        order = st.selectbox("Order", options=["Most restrictive first", "Most open first"], index=0)

    asc = (order == "Most restrictive first")
    df_expl = df_expl.sort_values(sort_by, ascending=asc, na_position="last")

    # Compact view -----------------------------------------------------
    view = df_expl[[
        "Brand", "Policy #", "Policy ID", "Access Score", "Access Tier",
        "Age Criterion", "TB Test", "Quantity Limit", "Specialist Required",
        "Phototherapy Step", "Brand Steps", "Generic Steps",
        "Initial Auth (months)", "Reauth (months)",
    ]].rename(columns={
        "Policy ID": "Source policy",
    })

    st.dataframe(
        view,
        hide_index=True,
        use_container_width=True,
        height=420,
        column_config={
            "Brand":            st.column_config.TextColumn("Brand", width="medium"),
            "Policy #":         st.column_config.TextColumn("Policy", width="small"),
            "Source policy":    st.column_config.TextColumn("Source policy", width="medium",
                                                            help="Underlying PDF identifier"),
            "Access Score":     st.column_config.ProgressColumn(
                                    "Access score", format="%d", min_value=0, max_value=80),
            "Access Tier":      st.column_config.TextColumn("Tier"),
            "Age Criterion":    st.column_config.TextColumn("Age"),
            "Brand Steps":      st.column_config.NumberColumn("Brand steps", format="%.0f"),
            "Generic Steps":    st.column_config.NumberColumn("Generic steps", format="%.0f"),
            "Initial Auth (months)": st.column_config.NumberColumn("Initial auth (mo)", format="%.0f"),
            "Reauth (months)":  st.column_config.NumberColumn("Reauth (mo)", format="%.0f"),
        },
    )

    # Detailed inspector ----------------------------------------------
    section_header(
        "02 · Policy detail",
        "Full extraction for a single brand–policy",
        "Pick a row to see the raw policy language — useful for due diligence on the extraction."
    )

    if len(df_expl) == 0:
        st.info("No records match the current filters / search.")
    else:
        df_expl["__label"] = df_expl["Brand"] + " · " + df_expl["Policy #"] + \
                              " · score " + df_expl["Access Score"].astype("Int64").astype(str)
        choice = st.selectbox(
            "Choose a record",
            options=df_expl["__label"].tolist(),
            label_visibility="visible",
        )
        row = df_expl[df_expl["__label"] == choice].iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Brand", row["Brand"], "", row["Policy #"])
        with c2: kpi_card("Access score", f"{int(row['Access Score'])}" if pd.notna(row['Access Score']) else "—",
                          "", row["Access Tier"])
        with c3: kpi_card("Initial auth",
                          f"{int(row['Initial Auth (months)'])}" if pd.notna(row['Initial Auth (months)']) else "—",
                          " mo", "Months of coverage on approval")
        with c4: kpi_card("Reauth",
                          f"{int(row['Reauth (months)'])}" if pd.notna(row['Reauth (months)']) else "—",
                          " mo", "Months until reassessment")

        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

        with st.expander("Step therapy language", expanded=True):
            txt = row.get("Step Therapy Requirements Documented in Policy")
            if pd.notna(txt) and str(txt).strip().lower() not in {"no", "nan"}:
                st.write(txt)
            else:
                st.caption("No step therapy language extracted.")

        with st.expander("Reauthorization requirements"):
            txt = row.get("Reauthorization Requirements Documented in Policy")
            if pd.notna(txt):
                st.write(txt)
            else:
                st.caption("No reauthorization language extracted.")

        with st.expander("Quantity limit language"):
            txt = row.get("Quantity Limits")
            if pd.notna(txt) and str(txt).strip().lower() not in {"no", "nan"}:
                st.write(txt)
            else:
                st.caption("No quantity limit specified, or recorded as 'No'.")

        with st.expander("Specialist & age criteria"):
            st.write(f"**Specialist:** {row.get('Specialist Types') or '—'}")
            st.write(f"**Age:** {row.get('Age Criterion') or '—'}")

        with st.expander("Underlying file"):
            st.code(row["Policy ID"] + ".pdf", language="text")


# ============================================================================
#  FOOTER
# ============================================================================
st.markdown(
    f"""
<div class="zs-footer">
  <span>ZS · Market Access Practice · Plaque Psoriasis Policy Lens</span>
  <span>Generated from extracted PA policy corpus</span>
</div>
""",
    unsafe_allow_html=True,
)
