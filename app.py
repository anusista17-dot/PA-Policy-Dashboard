"""
Payer Policy Intelligence — Executive Dashboard
H1'26 Hackathon | Designed in the ZS Associates analytical-product aesthetic

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import io
import re
import pathlib
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Payer Policy Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ZS DESIGN SYSTEM — CSS
# ============================================================
ZS_CSS = """
<style>
    /* === Type system === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Source+Serif+Pro:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #1A1A1A;
    }

    /* === Layout === */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px;
    }
    [data-testid="stSidebar"] {
        background: #FAFAFA;
        border-right: 1px solid #E5E5E5;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem !important;
    }

    /* === Hide Streamlit chrome === */
    #MainMenu, footer, header { visibility: hidden; }

    /* === Headlines === */
    h1, h2, h3 {
        font-family: 'Source Serif Pro', 'Inter', serif !important;
        color: #1A1A1A;
        letter-spacing: -0.01em;
    }
    h1 { font-weight: 700; font-size: 2.1rem !important; line-height: 1.2; }
    h2 { font-weight: 600; font-size: 1.45rem !important; margin-top: 1.5rem !important; }
    h3 { font-weight: 600; font-size: 1.15rem !important; }

    /* === Insight-led title pattern === */
    .insight-title {
        font-family: 'Source Serif Pro', serif;
        font-size: 1.5rem;
        line-height: 1.3;
        color: #1A1A1A;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    .insight-title .category {
        color: #FF6B35;
        font-weight: 700;
    }
    .insight-title .pipe {
        color: #999;
        margin: 0 0.4rem;
        font-weight: 300;
    }

    /* === KPI cards === */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1rem 0 2rem 0;
    }
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E5E5E5;
        border-radius: 6px;
        padding: 1.1rem 1.25rem;
        position: relative;
    }
    .kpi-card.accent { border-left: 3px solid #FF6B35; }
    .kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: #6B6B6B;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1A1A1A;
        line-height: 1;
    }
    .kpi-delta {
        font-size: 0.85rem;
        margin-top: 0.4rem;
        color: #6B6B6B;
    }
    .kpi-delta.neg { color: #DC3545; }
    .kpi-delta.pos { color: #28A745; }
    .kpi-sub { font-size: 0.85rem; color: #6B6B6B; margin-top: 0.4rem; }

    /* === Severity / confidence badges === */
    .badge {
        display: inline-block;
        padding: 0.18rem 0.55rem;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-right: 0.4rem;
        border: 1px solid transparent;
    }
    .badge-critical {
        background: #FBEAEC;
        color: #B92434;
        border-color: #F1B8BF;
    }
    .badge-warning {
        background: #FFF4E0;
        color: #C77700;
        border-color: #FFD89A;
    }
    .badge-monitor {
        background: #F0F0F0;
        color: #4A4A4A;
        border-color: #D5D5D5;
    }
    .badge-success {
        background: #E5F3E9;
        color: #1E7A35;
        border-color: #B8DEC2;
    }
    .badge-info {
        background: #E8F0F8;
        color: #2356A3;
        border-color: #C3D8EE;
    }
    .badge-confidence-high { background: #E5F3E9; color: #1E7A35; }
    .badge-confidence-medium { background: #FFF4E0; color: #C77700; }
    .badge-confidence-low { background: #F0F0F0; color: #4A4A4A; }

    /* === Insight card (AOI prototype-style) === */
    .insight-card {
        background: #FFFFFF;
        border: 1px solid #E5E5E5;
        border-left: 3px solid #999;
        border-radius: 6px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .insight-card.critical { border-left-color: #DC3545; }
    .insight-card.warning { border-left-color: #FFA500; }
    .insight-card.monitor { border-left-color: #4A4A4A; }
    .insight-card.success { border-left-color: #28A745; }
    .insight-card-meta {
        display: flex; align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
        font-size: 0.8rem; color: #6B6B6B;
    }
    .insight-card-headline {
        font-weight: 600;
        font-size: 1.02rem;
        color: #1A1A1A;
        line-height: 1.4;
        margin-bottom: 0.3rem;
    }
    .insight-card-body {
        font-size: 0.88rem;
        color: #4A4A4A;
        line-height: 1.5;
    }

    /* === Severity section header === */
    .severity-section {
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.5rem 0;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid #E5E5E5;
    }
    .severity-section.critical { color: #B92434; }
    .severity-section.warning { color: #C77700; }
    .severity-section.monitor { color: #4A4A4A; }
    .severity-section.success { color: #1E7A35; }

    /* === Footer callout bar (ZS pattern) === */
    .footer-callout {
        background: #2A2A2A;
        color: #FFFFFF;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        margin: 1.5rem 0;
        text-align: center;
        font-weight: 500;
        font-size: 0.95rem;
    }
    .footer-callout .highlight {
        color: #FFB380;
        font-weight: 600;
    }

    /* === Sub-callout / insight box === */
    .insight-box {
        background: #FFF8F2;
        border-left: 3px solid #FF6B35;
        padding: 0.85rem 1.1rem;
        margin: 1rem 0;
        font-size: 0.92rem;
        color: #4A4A4A;
        border-radius: 0 4px 4px 0;
    }
    .insight-box strong { color: #1A1A1A; }

    /* === Data table polish === */
    .stDataFrame {
        border: 1px solid #E5E5E5;
        border-radius: 4px;
    }

    /* === Source/footnote line === */
    .footnote {
        font-size: 0.72rem;
        color: #999;
        margin-top: 1rem;
        font-style: italic;
        border-top: 1px solid #E5E5E5;
        padding-top: 0.5rem;
    }

    /* === Tabs === */
    [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #E5E5E5;
    }
    [data-baseweb="tab"] {
        padding: 0.6rem 1.25rem !important;
        font-weight: 500 !important;
        color: #6B6B6B !important;
        border-bottom: 2px solid transparent !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        color: #FF6B35 !important;
        border-bottom-color: #FF6B35 !important;
    }

    /* === Metric overrides === */
    [data-testid="stMetricValue"] { font-size: 1.9rem; font-weight: 700; color: #1A1A1A; }
    [data-testid="stMetricLabel"] { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.07em; color: #6B6B6B; font-weight: 600; }
    [data-testid="stMetricDelta"] { font-size: 0.8rem; }

    /* === Sidebar polish === */
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #6B6B6B !important;
        font-weight: 600;
        margin-top: 1rem !important;
    }

    /* === Buttons === */
    .stButton button {
        background: #FF6B35;
        color: white;
        border: none;
        font-weight: 500;
    }
    .stButton button:hover {
        background: #E55A24;
    }
</style>
"""
st.markdown(ZS_CSS, unsafe_allow_html=True)


# ============================================================
# DATA LOADING
# ============================================================
@st.cache_data
def load_data_from_bytes(content: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(content), keep_default_na=False, na_values=[""])
    if "Access Score" in df.columns:
        df["Access Score"] = pd.to_numeric(df["Access Score"], errors="coerce").fillna(50).astype(int)
    return _enrich(df)


@st.cache_data
def load_data_from_path(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, keep_default_na=False, na_values=[""])
    if "Access Score" in df.columns:
        df["Access Score"] = pd.to_numeric(df["Access Score"], errors="coerce").fillna(50).astype(int)
    return _enrich(df)


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns: severity, payer display name, restrictiveness count."""
    df = df.copy()
    df["Policy ID"] = df["Filename"].str.replace(".pdf", "", regex=False)
    # Generate a display label like "Policy 01 — Tremfya (Payer 330109)"
    df["Display Name"] = df.apply(
        lambda r: f"{r['Brand'].title()} · {r['Filename'].split('-')[0]}", axis=1
    )
    df["Severity"] = df["Access Score"].apply(_severity_from_score)
    return df


def _severity_from_score(score: float) -> str:
    if score < 38: return "critical"
    if score < 50: return "warning"
    if score < 62: return "monitor"
    return "success"


def _severity_label(sev: str) -> str:
    return {"critical": "RESTRICTED", "warning": "GUARDED",
            "monitor": "AT PARITY", "success": "PREFERRED"}.get(sev, "")


def to_int(v, default: int = 0) -> int:
    try: return int(str(v).strip())
    except Exception: return default


def restrictiveness_signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Brand Steps"] = out["Number of Steps through Brands"].map(lambda v: to_int(v, 0))
    out["Generic Steps"] = out["Number of Steps through Generic"].map(lambda v: to_int(v, 0))
    out["Phototherapy"] = (out["Step through-Phototherapy"] == "Yes").astype(int)
    out["TB Test"] = (out["TB Test required"] == "Yes").astype(int)
    out["Specialist Required"] = (~out["Specialist Types"].isin(["NA", "No", ""])).astype(int)
    out["Total Restrictions"] = (
        out["Brand Steps"] + out["Generic Steps"] +
        out["Phototherapy"] + out["TB Test"] + out["Specialist Required"]
    )
    return out


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style='padding: 0 0 1.2rem 0; border-bottom: 1px solid #E5E5E5;'>
        <div style='font-family: "Source Serif Pro", serif; font-size: 1.4rem; font-weight: 700; color: #1A1A1A; line-height: 1.2;'>
            Payer Policy<br/>Intelligence
        </div>
        <div style='font-size: 0.78rem; color: #6B6B6B; margin-top: 0.3rem;'>
            Access quality monitoring for plaque-psoriasis biologics
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Data Source")
    uploaded = st.file_uploader("Upload `result.csv`", type=["csv"], label_visibility="collapsed")
    df: Optional[pd.DataFrame] = None

    if uploaded is not None:
        df = load_data_from_bytes(uploaded.getvalue())
    else:
        for p in ["result.csv", "outputs/result.csv"]:
            if pathlib.Path(p).exists():
                df = load_data_from_path(p)
                break

    if df is None:
        st.warning("Upload a `result.csv` to begin.")
        st.stop()

    st.caption(f"**{len(df)}** rows loaded · {df['Brand'].nunique()} brands · {df['Filename'].nunique()} unique policies")

    st.markdown("### Filters")
    all_brands = sorted(df["Brand"].dropna().unique())
    brands_sel = st.multiselect("Brand", all_brands, default=all_brands, label_visibility="collapsed")
    score_range = st.slider("Access Score range", 0, 100,
                            (int(df["Access Score"].min()), int(df["Access Score"].max())))

    severity_filter = st.multiselect(
        "Severity",
        ["critical", "warning", "monitor", "success"],
        default=["critical", "warning", "monitor", "success"],
        format_func=lambda s: {"critical": "🔴 Restricted",
                              "warning": "🟠 Guarded",
                              "monitor": "⚪ At parity",
                              "success": "🟢 Preferred"}.get(s, s),
    )

    df_view = df[
        df["Brand"].isin(brands_sel)
        & df["Access Score"].between(*score_range)
        & df["Severity"].isin(severity_filter)
    ].copy()

    st.caption(f"`{len(df_view)} of {len(df)} rows match filters`")

    st.markdown("---")
    st.markdown("### About")
    st.caption("Built for the H1'26 hackathon. Pipeline: PDF → Gemini 2.5 Flash → deterministic Access Score (0–100). "
               "Every claim is evidence-grounded and auditable.")


# ============================================================
# HEADER
# ============================================================
n_critical = (df_view["Severity"] == "critical").sum()
n_warning = (df_view["Severity"] == "warning").sum()
n_monitor = (df_view["Severity"] == "monitor").sum()
n_success = (df_view["Severity"] == "success").sum()
avg_score = df_view["Access Score"].mean() if len(df_view) else 0
parity_delta = avg_score - 50

st.markdown(f"""
<div class='insight-title'>
    <span class='category'>Executive view</span>
    <span class='pipe'>|</span>
    {len(df_view)} payer policies analyzed across {df_view['Brand'].nunique()} brands;
    average access is <strong>{abs(parity_delta):.1f} points {'below' if parity_delta < 0 else 'above'} FDA parity</strong>
</div>
""", unsafe_allow_html=True)


# ============================================================
# TABS
# ============================================================
tab_exec, tab_explore, tab_detail, tab_compare, tab_data, tab_method = st.tabs([
    "Executive Summary", "Policy Explorer", "Policy Detail",
    "Side-by-Side Compare", "Raw Data", "Methodology"
])


# ----------------------------------------------------------------
# TAB 1: EXECUTIVE SUMMARY
# ----------------------------------------------------------------
with tab_exec:
    # KPI ROW
    st.markdown(f"""
    <div class='kpi-grid'>
        <div class='kpi-card accent'>
            <div class='kpi-label'>Policies analyzed</div>
            <div class='kpi-value'>{len(df_view)}</div>
            <div class='kpi-sub'>{df_view['Filename'].nunique()} unique payer documents</div>
        </div>
        <div class='kpi-card'>
            <div class='kpi-label'>Average access score</div>
            <div class='kpi-value'>{avg_score:.1f}</div>
            <div class='kpi-delta {"neg" if parity_delta < 0 else "pos"}'>
                {'↓' if parity_delta < 0 else '↑'} {abs(parity_delta):.1f} vs FDA parity (50)
            </div>
        </div>
        <div class='kpi-card'>
            <div class='kpi-label'>Restricted policies</div>
            <div class='kpi-value' style='color: #B92434;'>{n_critical}</div>
            <div class='kpi-sub'>{100*n_critical/max(1,len(df_view)):.0f}% of book — score &lt; 38</div>
        </div>
        <div class='kpi-card'>
            <div class='kpi-label'>Preferred policies</div>
            <div class='kpi-value' style='color: #1E7A35;'>{n_success}</div>
            <div class='kpi-sub'>{100*n_success/max(1,len(df_view)):.0f}% of book — score ≥ 62</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KEY FINDINGS (3 insight cards)
    st.markdown("<h2>Key findings</h2>", unsafe_allow_html=True)

    # Compute findings dynamically
    brand_means = df_view.groupby("Brand")["Access Score"].agg(["mean","count"]).round(1)
    brand_means = brand_means[brand_means["count"] >= 2].sort_values("mean")  # brands with >=2 policies
    if len(brand_means):
        worst_brand = brand_means.index[0]
        best_brand = brand_means.index[-1]
        gap = brand_means["mean"].iloc[-1] - brand_means["mean"].iloc[0]
    else:
        worst_brand, best_brand, gap = "—", "—", 0

    sig = restrictiveness_signals(df_view)
    tb_share = (sig["TB Test"] == 1).mean() * 100
    photo_share = (sig["Phototherapy"] == 1).mean() * 100
    step_burdened = (sig["Brand Steps"] + sig["Generic Steps"] >= 2).mean() * 100

    findings_col1, findings_col2 = st.columns(2)
    with findings_col1:
        st.markdown(f"""
        <div class='insight-card critical'>
            <div class='insight-card-meta'>
                <span class='badge badge-critical'>Finding 1</span>
                <span>Brand-level gap</span>
            </div>
            <div class='insight-card-headline'>
                {best_brand.title()} secures {gap:.1f}-point higher access than {worst_brand.title()} across the same payer mix
            </div>
            <div class='insight-card-body'>
                Identical FDA indications, materially different payer treatment.
                Negotiation leverage opportunity for the under-performing brand.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='insight-card warning'>
            <div class='insight-card-meta'>
                <span class='badge badge-warning'>Finding 2</span>
                <span>Step-therapy burden</span>
            </div>
            <div class='insight-card-headline'>
                {step_burdened:.0f}% of policies require 2+ prior-therapy failures before approval
            </div>
            <div class='insight-card-body'>
                The most common access friction. Each additional brand-step deducts ~5 points from
                the policy's Access Score and adds weeks to time-to-therapy.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with findings_col2:
        st.markdown(f"""
        <div class='insight-card warning'>
            <div class='insight-card-meta'>
                <span class='badge badge-warning'>Finding 3</span>
                <span>Clinical gating</span>
            </div>
            <div class='insight-card-headline'>
                {tb_share:.0f}% of policies require TB testing; {photo_share:.0f}% require phototherapy step
            </div>
            <div class='insight-card-body'>
                Standard but high-friction requirements. Reducing either could meaningfully
                shift the access-score distribution upward.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Compute a top "preferred" payer for highlight
        if n_success > 0:
            preferred_examples = df_view[df_view["Severity"] == "success"].head(1)
            example_brand = preferred_examples.iloc[0]["Brand"]
            example_policy = preferred_examples.iloc[0]["Policy ID"]
        else:
            example_brand, example_policy = "—", "—"

        st.markdown(f"""
        <div class='insight-card success'>
            <div class='insight-card-meta'>
                <span class='badge badge-success'>Finding 4</span>
                <span>Best-in-class access</span>
            </div>
            <div class='insight-card-headline'>
                {n_success} policies score &ge; 62 — these are template wins to study for negotiation pattern
            </div>
            <div class='insight-card-body'>
                Highest-access policies typically combine: no step therapy, 12-month authorization,
                broad specialist eligibility, and absence of TB requirement.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # DISTRIBUTION CHART
    st.markdown("<h2>Access score distribution by brand</h2>", unsafe_allow_html=True)

    fig_dist = go.Figure()
    brand_order = df_view.groupby("Brand")["Access Score"].mean().sort_values().index.tolist()
    for brand in brand_order:
        b_data = df_view[df_view["Brand"] == brand]["Access Score"]
        fig_dist.add_trace(go.Box(
            y=b_data, x=[brand] * len(b_data),
            name=brand,
            marker_color="#FF6B35",
            line_color="#1A1A1A",
            boxpoints="all", jitter=0.4, pointpos=0,
            marker=dict(size=6, opacity=0.7, line=dict(width=1, color="#1A1A1A")),
            showlegend=False,
        ))
    fig_dist.add_hline(y=50, line_dash="dash", line_color="#6B6B6B", line_width=1.5,
                       annotation_text="FDA parity (50)", annotation_position="right",
                       annotation_font=dict(size=11, color="#6B6B6B"))
    fig_dist.add_hrect(y0=0, y1=38, fillcolor="#FBEAEC", opacity=0.3, layer="below", line_width=0)
    fig_dist.add_hrect(y0=62, y1=100, fillcolor="#E5F3E9", opacity=0.3, layer="below", line_width=0)
    fig_dist.update_layout(
        height=440,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12, color="#1A1A1A"),
        yaxis=dict(title="Access Score", range=[0, 100],
                  gridcolor="#F0F0F0", zerolinecolor="#E5E5E5"),
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False})

    st.markdown("""
    <div class='insight-box'>
        <strong>Read:</strong> Green band = preferred access (score ≥ 62). Red band = restricted (&lt; 38).
        Brands are ordered left-to-right by average access score, lowest first.
        Each point is one (payer policy, brand) combination.
    </div>
    """, unsafe_allow_html=True)

    # FOOTER CALLOUT
    st.markdown(f"""
    <div class='footer-callout'>
        Of {len(df_view)} policies analyzed, <span class='highlight'>{n_critical + n_warning}</span> show access friction below FDA parity
        — concentrated in step therapy, TB testing, and specialist gating. The pipeline surfaces these systematically;
        the patterns above are the levers to negotiate against.
    </div>
    """, unsafe_allow_html=True)

    # FOOTNOTE
    st.markdown(f"""
    <div class='footnote'>
        Source: 70 publicly available US payer Prior Authorization PDFs, extracted via Gemini 2.5 Flash with
        Pydantic schema enforcement. Access Score is computed by a deterministic rules-based formula (0–100),
        calibrated against the problem-statement anchors. n={len(df_view)} (filename, brand) combinations.
        Pipeline run: {pd.Timestamp.now().strftime('%Y-%m-%d')}.
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------
# TAB 2: POLICY EXPLORER (cards grouped by severity)
# ----------------------------------------------------------------
with tab_explore:
    st.markdown(f"""
    <div class='insight-title'>
        <span class='category'>Policy explorer</span>
        <span class='pipe'>|</span>
        Browse all {len(df_view)} policies grouped by access severity
    </div>
    """, unsafe_allow_html=True)

    severities = [("critical", "Restricted access (score < 38)", "Score below FDA parity by 12+ points"),
                  ("warning",  "Guarded access (38–49)", "Below FDA parity"),
                  ("monitor",  "At-parity access (50–61)", "Aligned with FDA label"),
                  ("success",  "Preferred access (≥ 62)", "Above FDA parity")]

    for sev_key, sev_label, sev_desc in severities:
        sev_df = df_view[df_view["Severity"] == sev_key]
        if not len(sev_df):
            continue
        st.markdown(f"""
        <div class='severity-section {sev_key}'>
            {sev_label} &nbsp;·&nbsp; <span style='color: #6B6B6B; font-weight: 500; text-transform: none; letter-spacing: 0;'>{sev_desc}</span> &nbsp;·&nbsp; <span style='color: #6B6B6B;'>{len(sev_df)} policies</span>
        </div>
        """, unsafe_allow_html=True)

        # Render cards 2 per row
        sev_df = sev_df.sort_values("Access Score", ascending=(sev_key in ["critical","warning"]))
        for i in range(0, len(sev_df), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j >= len(sev_df): break
                row = sev_df.iloc[i + j]
                # Build restrictions summary
                rests = []
                bs = to_int(row["Number of Steps through Brands"], 0)
                gs = to_int(row["Number of Steps through Generic"], 0)
                if bs > 0: rests.append(f"{bs} brand step{'s' if bs > 1 else ''}")
                if gs > 0: rests.append(f"{gs} generic step{'s' if gs > 1 else ''}")
                if row["TB Test required"] == "Yes": rests.append("TB test")
                if row["Step through-Phototherapy"] == "Yes": rests.append("phototherapy")
                rests_str = " · ".join(rests) if rests else "No major restrictions"

                with col:
                    st.markdown(f"""
                    <div class='insight-card {sev_key}'>
                        <div class='insight-card-meta'>
                            <span class='badge badge-{sev_key}'>{_severity_label(sev_key)}</span>
                            <span><strong>{row['Brand']}</strong></span>
                            <span>· Score {row['Access Score']}</span>
                        </div>
                        <div class='insight-card-headline'>
                            Payer policy {row['Policy ID']}
                        </div>
                        <div class='insight-card-body'>
                            <strong>Restrictions:</strong> {rests_str}<br>
                            <strong>Age eligibility:</strong> {row['Age']} ·
                            <strong>Initial auth:</strong> {row['Initial Authorization Duration(in-months)']} months
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='footnote'>
        Cards grouped by severity band. Within each band, sorted by Access Score
        (lowest first for restricted/guarded, highest first for at-parity/preferred).
        Switch to Policy Detail tab for evidence-grounded drill-down.
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------
# TAB 3: POLICY DETAIL (AOI prototype-style drill-down)
# ----------------------------------------------------------------
with tab_detail:
    if not len(df_view):
        st.info("No rows match the current filters.")
    else:
        df_v = df_view.reset_index(drop=True).copy()
        df_v["__key"] = df_v["Display Name"] + "  (" + df_v["Filename"] + ")"
        sel = st.selectbox("Select a policy to inspect", options=df_v["__key"].tolist(), label_visibility="collapsed")
        row = df_v[df_v["__key"] == sel].iloc[0]

        sev = row["Severity"]
        sev_label = _severity_label(sev)

        # Dark header (AOI-style)
        st.markdown(f"""
        <div style='background: #1F1F1F; border-radius: 6px; padding: 1.5rem 1.75rem; margin: 1rem 0;'>
            <div style='display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.7rem;'>
                <span class='badge badge-{sev}'>{sev_label}</span>
                <span style='color: #FF6B35; font-weight: 600; font-size: 0.85rem;'>{row['Brand']}</span>
                <span style='color: #999; font-size: 0.8rem;'>·</span>
                <span style='color: #999; font-size: 0.8rem;'>Payer policy {row['Policy ID']}</span>
            </div>
            <div style='font-family: "Source Serif Pro", serif; font-size: 1.4rem; color: #FFFFFF; font-weight: 600; line-height: 1.3; margin-bottom: 0.85rem;'>
                Access Score <strong style='color: #FFB380;'>{row['Access Score']}</strong> ·
                {abs(row['Access Score'] - 50)} points {"below" if row['Access Score'] < 50 else "above"} FDA parity
            </div>
            <div style='display: flex; gap: 0.5rem;'>
                <span class='badge badge-confidence-high'>Deterministic score</span>
                <span class='badge badge-info'>{row['Brand']} indication: PsO</span>
                <span class='badge badge-monitor'>Source: PDF extraction</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Sub-tabs
        sub_overview, sub_params, sub_score = st.tabs(["Overview", "All 12 parameters", "Score breakdown"])

        with sub_overview:
            c1, c2, c3 = st.columns(3)
            brand_avg = df[df["Brand"] == row["Brand"]]["Access Score"].mean()
            overall_avg = df["Access Score"].mean()
            with c1:
                st.metric("vs Brand average", f"{row['Access Score']}",
                         f"{row['Access Score'] - brand_avg:+.1f} vs {brand_avg:.1f}")
            with c2:
                st.metric("vs Overall average", f"{row['Access Score']}",
                         f"{row['Access Score'] - overall_avg:+.1f} vs {overall_avg:.1f}")
            with c3:
                pct = int(round((df[df["Brand"] == row["Brand"]]["Access Score"] <= row["Access Score"]).mean() * 100))
                suffix = "th" if 11 <= (pct % 100) <= 13 else {1:"st",2:"nd",3:"rd"}.get(pct % 10, "th")
                st.metric("Brand percentile", f"{pct}{suffix}")

            # Quick visual: where this score sits in the distribution
            fig_pos = go.Figure()
            all_scores = df["Access Score"].values
            fig_pos.add_trace(go.Histogram(
                x=all_scores, nbinsx=20,
                marker=dict(color="#E5E5E5", line=dict(width=0)),
                showlegend=False, hoverinfo="skip"
            ))
            fig_pos.add_vline(x=row["Access Score"], line_color="#FF6B35", line_width=3,
                             annotation_text=f"This policy: {row['Access Score']}",
                             annotation_position="top",
                             annotation_font=dict(size=12, color="#FF6B35", family="Inter"))
            fig_pos.add_vline(x=50, line_dash="dash", line_color="#999", line_width=1.5,
                             annotation_text="FDA parity", annotation_position="bottom")
            fig_pos.update_layout(
                height=200, plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Inter", color="#1A1A1A"),
                margin=dict(t=20, b=20, l=10, r=10),
                xaxis=dict(title="Access Score", gridcolor="#F0F0F0"),
                yaxis=dict(title="Policy count", gridcolor="#F0F0F0"),
                showlegend=False,
            )
            st.markdown("**This policy in the context of all 79**")
            st.plotly_chart(fig_pos, use_container_width=True, config={"displayModeBar": False})

            # Headline insight summarizing this policy
            rests = []
            bs = to_int(row["Number of Steps through Brands"], 0)
            gs = to_int(row["Number of Steps through Generic"], 0)
            if bs > 0: rests.append(f"{bs} brand step{'s' if bs > 1 else ''}")
            if gs > 0: rests.append(f"{gs} generic step{'s' if gs > 1 else ''}")
            if row["TB Test required"] == "Yes": rests.append("TB testing")
            if row["Step through-Phototherapy"] == "Yes": rests.append("phototherapy step")
            if row["Specialist Types"] not in ["NA", "No", ""]:
                rests.append(f"specialty restriction ({row['Specialist Types']})")

            rest_text = "; ".join(rests) if rests else "no major access restrictions"
            st.markdown(f"""
            <div class='insight-box'>
                <strong>Summary:</strong> This {row['Brand']} policy from payer {row['Policy ID']} imposes {rest_text}.
                Initial authorization runs {row['Initial Authorization Duration(in-months)']} months;
                reauthorization is {'required' if row['Reauthorization Required'] == 'Yes' else 'not required'}.
                Age eligibility: {row['Age']}.
            </div>
            """, unsafe_allow_html=True)

        with sub_params:
            # Two-column parameter listing
            params_left = ["Age", "Number of Steps through Brands", "Number of Steps through Generic",
                          "Step through-Phototherapy", "TB Test required", "Specialist Types"]
            params_right = ["Initial Authorization Duration(in-months)",
                           "Reauthorization Duration(in-months)",
                           "Reauthorization Required", "Quantity Limits"]

            pcol_l, pcol_r = st.columns(2)
            for col_list, col_widget in [(params_left, pcol_l), (params_right, pcol_r)]:
                with col_widget:
                    for c in col_list:
                        val = str(row[c])
                        # Color the value by sentiment
                        val_color = "#1A1A1A"
                        if val == "Yes" and c in ("TB Test required", "Step through-Phototherapy"):
                            val_color = "#B92434"
                        elif val == "No" and c in ("TB Test required", "Step through-Phototherapy"):
                            val_color = "#1E7A35"
                        elif c.startswith("Number of Steps") and val.isdigit() and int(val) > 0:
                            val_color = "#B92434"
                        elif val == "No" and c.startswith("Number of Steps"):
                            val_color = "#1E7A35"

                        st.markdown(f"""
                        <div style='padding: 0.6rem 0; border-bottom: 1px dashed #E5E5E5;'>
                            <div style='font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #6B6B6B;'>{c}</div>
                            <div style='font-size: 0.95rem; font-weight: 500; color: {val_color}; margin-top: 0.2rem;'>{val}</div>
                        </div>
                        """, unsafe_allow_html=True)

            # Verbatim language
            st.markdown("##### Verbatim policy language extracted")
            with st.expander("Step Therapy Requirements (verbatim)", expanded=False):
                st.write(row["Step Therapy Requirements Documented in Policy"])
            with st.expander("Reauthorization Requirements (verbatim)", expanded=False):
                st.write(row["Reauthorization Requirements Documented in Policy"])

        with sub_score:
            # Score waterfall
            st.markdown("**How this Access Score was computed**")
            st.caption("Deterministic rules-based formula. Starts at 50 (FDA parity), then adjusts by each parameter.")

            deductions = []
            additions = []
            base = 50

            bs = to_int(row["Number of Steps through Brands"], 0)
            gs = to_int(row["Number of Steps through Generic"], 0)
            if bs > 0: deductions.append((f"Brand step therapy × {bs}", -5.0 * min(bs, 5)))
            if gs > 0: deductions.append((f"Generic step therapy × {gs}", -2.5 * min(gs, 5)))
            if row["Step through-Phototherapy"] == "Yes": deductions.append(("Phototherapy step required", -5.0))
            if row["TB Test required"] == "Yes": deductions.append(("TB testing required", -3.5))
            spec = str(row["Specialist Types"])
            if spec not in ("NA", "No", ""):
                n_sp = len([s for s in spec.split(";") if s.strip()])
                if n_sp <= 1: deductions.append((f"Single specialty restriction ({spec})", -3.5))
                elif n_sp <= 2: deductions.append((f"2-specialty restriction", -2.5))
                else: deductions.append(("Broad specialty list", -1.5))
            if str(row["Quantity Limits"]) not in ("No", "NA", ""):
                deductions.append(("Quantity limits", -2.0))

            ia = to_int(row["Initial Authorization Duration(in-months)"])
            if ia >= 12: additions.append(("Initial auth ≥ 12 months", 6.0))
            elif ia >= 6: additions.append((f"Initial auth {ia} months", 2.0))
            elif 0 < ia < 6: deductions.append((f"Short initial auth ({ia} mo)", -3.0))

            rd = to_int(row["Reauthorization Duration(in-months)"])
            if rd >= 12: additions.append(("Reauth ≥ 12 months", 4.0))
            elif rd >= 6: additions.append((f"Reauth {rd} months", 1.0))
            elif 0 < rd < 6: deductions.append((f"Short reauth ({rd} mo)", -2.0))

            if row["Reauthorization Required"] == "No": additions.append(("No reauthorization required", 3.0))

            # Show in table form
            wcol1, wcol2 = st.columns(2)
            with wcol1:
                st.markdown("**Deductions (restrictions)**")
                if deductions:
                    for label, val in deductions:
                        st.markdown(f"<div style='display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px dashed #E5E5E5;'><span style='color: #4A4A4A;'>{label}</span><span style='color: #B92434; font-weight: 600;'>{val:.1f}</span></div>", unsafe_allow_html=True)
                else:
                    st.caption("No deductions applied")
            with wcol2:
                st.markdown("**Additions (access-friendly)**")
                if additions:
                    for label, val in additions:
                        st.markdown(f"<div style='display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px dashed #E5E5E5;'><span style='color: #4A4A4A;'>{label}</span><span style='color: #1E7A35; font-weight: 600;'>+{val:.1f}</span></div>", unsafe_allow_html=True)
                else:
                    st.caption("No additions applied")

            net = sum(v for _, v in deductions) + sum(v for _, v in additions)
            final = max(0, min(100, base + net))
            st.markdown(f"""
            <div style='background: #FFF8F2; border-left: 3px solid #FF6B35; padding: 1rem 1.25rem; margin-top: 1rem; border-radius: 0 4px 4px 0;'>
                <div style='font-size: 0.95rem; color: #4A4A4A;'>
                    <strong>50</strong> baseline (FDA parity)
                    {'-' if net < 0 else '+'} <strong>{abs(net):.1f}</strong> net adjustment
                    = <strong style='color: #FF6B35; font-size: 1.15rem;'>{int(round(final))}</strong> final Access Score
                </div>
            </div>
            """, unsafe_allow_html=True)


# ----------------------------------------------------------------
# TAB 4: SIDE-BY-SIDE COMPARE
# ----------------------------------------------------------------
with tab_compare:
    st.markdown(f"""
    <div class='insight-title'>
        <span class='category'>Comparison view</span>
        <span class='pipe'>|</span>
        Diff 2–3 policies on every parameter
    </div>
    """, unsafe_allow_html=True)

    if len(df_view) < 2:
        st.info("Need at least 2 rows in the filter to compare.")
    else:
        df_v = df_view.reset_index(drop=True).copy()
        df_v["__key"] = df_v["Display Name"] + "  (" + df_v["Filename"] + ")"
        selected = st.multiselect("Pick 2–3 policies to compare",
                                  df_v["__key"].tolist(),
                                  default=df_v["__key"].tolist()[:2],
                                  max_selections=3)

        if len(selected) >= 2:
            picked = df_v[df_v["__key"].isin(selected)].copy()
            display_cols = ["Brand", "Access Score", "Age",
                "Number of Steps through Brands", "Number of Steps through Generic",
                "Step through-Phototherapy", "TB Test required", "Quantity Limits",
                "Specialist Types",
                "Initial Authorization Duration(in-months)",
                "Reauthorization Duration(in-months)",
                "Reauthorization Required"]
            comp = picked.set_index("__key")[display_cols].astype(str).T

            # Compute which rows differ
            diff_mask = comp.apply(lambda r: len(set(r.values)) > 1, axis=1)
            n_diffs = diff_mask.sum()

            st.markdown(f"""
            <div class='insight-box'>
                <strong>{n_diffs} of {len(comp)} parameters</strong> differ across the selected policies, highlighted below.
            </div>
            """, unsafe_allow_html=True)

            # Render styled table
            def highlight_diffs(row):
                vals = [str(v).strip() for v in row.values]
                if len(set(vals)) > 1:
                    return ["background-color: #FFF8F2; color: #1A1A1A;"] * len(row)
                return ["color: #6B6B6B;"] * len(row)

            styled = comp.style.apply(highlight_diffs, axis=1)
            st.dataframe(styled, use_container_width=True, height=520)

            # Radar
            st.markdown("##### Restrictiveness profile")
            radar_axes = ["Brand Steps", "Generic Steps", "Phototherapy", "TB Test", "Specialist Required"]
            radar_df = restrictiveness_signals(picked).set_index("__key")[radar_axes].copy()
            radar_df["Brand Steps"] = (radar_df["Brand Steps"] / 5).clip(0, 1)
            radar_df["Generic Steps"] = (radar_df["Generic Steps"] / 5).clip(0, 1)

            fig_radar = go.Figure()
            zs_colors = ["#FF6B35", "#1A1A1A", "#6B6B6B"]
            for i, (key, vals) in enumerate(radar_df.iterrows()):
                fig_radar.add_trace(go.Scatterpolar(
                    r=list(vals.values) + [vals.values[0]],
                    theta=radar_axes + [radar_axes[0]],
                    fill="toself",
                    name=key.split("(")[0].strip(),
                    opacity=0.45,
                    line=dict(color=zs_colors[i % len(zs_colors)], width=2),
                ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(range=[0, 1], visible=True, gridcolor="#E5E5E5", tickfont=dict(size=10)),
                    angularaxis=dict(gridcolor="#E5E5E5", tickfont=dict(size=11, color="#1A1A1A"))
                ),
                showlegend=True,
                legend=dict(orientation="h", y=-0.15, font=dict(size=11)),
                height=420,
                font=dict(family="Inter", color="#1A1A1A"),
                margin=dict(t=20, b=20, l=40, r=40),
                paper_bgcolor="white",
            )
            st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

            st.markdown(f"""
            <div class='footnote'>
                Restrictiveness signals normalized to 0–1 scale (step counts divided by 5).
                A larger polygon = more restrictive policy.
            </div>
            """, unsafe_allow_html=True)


# ----------------------------------------------------------------
# TAB 5: RAW DATA
# ----------------------------------------------------------------
with tab_data:
    st.markdown(f"""
    <div class='insight-title'>
        <span class='category'>Raw data</span>
        <span class='pipe'>|</span>
        Filtered extraction output ({len(df_view)} rows)
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input("Search (filename or brand)", "")
    df_show = df_view.drop(columns=["__key", "Severity", "Display Name", "Policy ID"], errors="ignore")
    if search:
        mask = (
            df_show["Filename"].str.contains(search, case=False, na=False)
            | df_show["Brand"].str.contains(search, case=False, na=False)
        )
        df_show = df_show[mask]

    st.dataframe(df_show, use_container_width=True, height=540)

    col_dl, col_info = st.columns([1, 3])
    with col_dl:
        st.download_button(
            "📥 Download filtered CSV",
            data=df_show.to_csv(index=False).encode("utf-8"),
            file_name="result_filtered.csv",
            mime="text/csv",
        )
    with col_info:
        st.caption(f"Showing {len(df_show)} of {len(df)} rows. Use `keep_default_na=False` when loading in pandas — \"NA\" is a literal value, not a null.")


# ----------------------------------------------------------------
# TAB 6: METHODOLOGY
# ----------------------------------------------------------------
with tab_method:
    st.markdown(f"""
    <div class='insight-title'>
        <span class='category'>Methodology</span>
        <span class='pipe'>|</span>
        How the pipeline produces auditable, reproducible results
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ##### Pipeline at a glance

    The pipeline reads US payer Prior Authorization PDFs and extracts 12 structured business parameters per (filename, brand) combination, then computes a continuous Access Score (0–100).

    | Stage | Process | Output |
    |---|---|---|
    | 1 | PDF text extraction (pdfplumber + pdftotext fallback, hash-cached) | Raw text per document |
    | 2 | Hierarchical brand scoping (section detection + cross-brand negative filtering) | Brand-specific excerpts |
    | 3 | Brand-stratified few-shot retrieval (2 same-brand + 1 cross-brand from 439 gold rows) | Top-3 examples per call |
    | 4 | Gemini 2.5 Flash extraction with Pydantic schema enforcement | Structured JSON: value + evidence + confidence |
    | 5 | 3-layer validation: formatting → business rules → contradiction detection | Cleaned values + issue flags |
    | 6 | Deterministic Access Score (monotonic rules-based, 0–100) | Single integer per row |

    ##### Why deterministic scoring

    Earlier versions of the pipeline blended a Gemini-rated score (30%) with the rules-based score (70%). For a leaderboard task this introduced a reproducibility hazard: same notebook + same data could produce slightly different scores across runs because LLM responses vary ~5% even at temperature 0.

    The current implementation uses **rules-only scoring** — same inputs always produce the same output, every restriction monotonically decreases the score, and every relaxation monotonically increases it.

    ##### Why evidence-grounded extraction

    Each parameter the LLM returns includes three fields: `value`, `evidence` (a verbatim 1–3 sentence quote from the policy), and `confidence` (high/medium/low). The schema is enforced via Pydantic so this structure is guaranteed. This makes hallucinations visible during spot-check and identifies which rows are most worth manual review.

    ##### Access Score calibration

    | Anchor | Reference | Example |
    |---|---|---|
    | 0   | No access | Drug excluded from formulary entirely |
    | 25  | Restricted | 3 brand steps + TB test + specialty + age threshold + 6mo auth |
    | 50  | FDA parity | Mirrors FDA label, no extra restrictions |
    | 75  | Preferred | No step therapy, 12mo auth, broad eligibility |
    | 100 | Best possible | No restrictions whatsoever |

    The continuous scale is preserved — anchors are reference points, not bucketed outputs.
    """)

    st.markdown("""
    <div class='footer-callout'>
        Design choices prioritize <span class='highlight'>structured problem-solving, robustness, and interpretability</span> over raw model power
        — every claim is traceable, every score is auditable, every restriction is named and weighted.
    </div>
    """, unsafe_allow_html=True)
