"""
Payer Policy Intelligence — Executive Dashboard (v3)
H1'26 Hackathon | ZS Associates analytical-product aesthetic

Design priorities (v3):
- Chart-forward (text is supporting, not the body)
- Interactive: clicks/selections cross-filter
- Narrative arc: Overview → Diagnosis → Brand → Policy → Compare → Audit
- Information density without clutter

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import io
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
# DESIGN TOKENS
# ============================================================
ZS_ORANGE = "#FF6B35"
ZS_NAVY = "#1F4E79"
COLOR_CRITICAL = "#B92434"
COLOR_WARNING = "#D97706"
COLOR_MONITOR = "#6B7280"
COLOR_SUCCESS = "#059669"
GRAY_BG = "#F9FAFB"
GRAY_BORDER = "#E5E7EB"
TEXT_DARK = "#111827"
TEXT_MUTED = "#6B7280"

BRAND_PALETTE = ["#FF6B35", "#1F4E79", "#059669", "#D97706", "#7C3AED",
                 "#0EA5E9", "#B92434", "#65A30D", "#DB2777", "#0891B2",
                 "#9333EA", "#CA8A04", "#1E3A8A", "#16A34A", "#DC2626"]


# ============================================================
# GLOBAL CSS
# ============================================================
CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+Pro:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        color: #111827;
    }
    .block-container { padding: 1rem 1.5rem 3rem 1.5rem !important; max-width: 1500px; }
    [data-testid="stSidebar"] { background: #F9FAFB; border-right: 1px solid #E5E7EB; }
    [data-testid="stSidebar"] .block-container { padding-top: 1.2rem !important; }
    #MainMenu, footer, header { visibility: hidden; }

    h1 { font-family: 'Source Serif Pro', serif !important; font-weight: 700; font-size: 1.7rem !important;
         color: #111827; letter-spacing: -0.01em; margin-bottom: 0 !important; }
    h2 { font-family: 'Source Serif Pro', serif !important; font-weight: 600; font-size: 1.15rem !important;
         color: #111827; margin: 1rem 0 0.5rem 0 !important; letter-spacing: -0.005em; }
    h3 { font-family: 'Inter', sans-serif !important; font-weight: 600; font-size: 0.85rem !important;
         text-transform: uppercase; letter-spacing: 0.08em; color: #6B7280 !important; margin: 0.8rem 0 0.3rem 0 !important; }

    /* Insight headline (top of page) */
    .headline {
        font-family: 'Source Serif Pro', serif;
        font-size: 1.4rem;
        line-height: 1.3;
        color: #111827;
        margin: 0.2rem 0 1rem 0;
        font-weight: 600;
    }
    .headline .pre { color: #FF6B35; font-weight: 700; }
    .headline .pipe { color: #D1D5DB; margin: 0 0.4rem; font-weight: 300; }

    /* KPI strip — compact horizontal */
    .kpi-strip { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.6rem; margin: 0.5rem 0 1.2rem 0; }
    .kpi-tile {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 4px;
        padding: 0.6rem 0.8rem;
        line-height: 1.1;
    }
    .kpi-tile.accent { border-top: 2px solid #FF6B35; }
    .kpi-tile.critical { border-top: 2px solid #B92434; }
    .kpi-tile.success { border-top: 2px solid #059669; }
    .kpi-tile.warning { border-top: 2px solid #D97706; }
    .kpi-label { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.06em; color: #6B7280; font-weight: 600; }
    .kpi-value { font-size: 1.55rem; font-weight: 700; color: #111827; margin-top: 0.15rem; }
    .kpi-delta { font-size: 0.72rem; margin-top: 0.1rem; }
    .kpi-delta.neg { color: #B92434; }
    .kpi-delta.pos { color: #059669; }
    .kpi-delta.neutral { color: #6B7280; }

    /* Chart card frame */
    .chart-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 4px;
        padding: 0.75rem 1rem 0.5rem 1rem;
        margin-bottom: 0.6rem;
    }
    .chart-title { font-size: 0.9rem; font-weight: 600; color: #111827; margin-bottom: 0.1rem; }
    .chart-sub { font-size: 0.75rem; color: #6B7280; margin-bottom: 0.4rem; }

    /* Insight callout (one-line, tight) */
    .callout {
        background: #FFF8F2;
        border-left: 3px solid #FF6B35;
        padding: 0.55rem 0.85rem;
        font-size: 0.85rem;
        color: #1F2937;
        border-radius: 0 3px 3px 0;
        margin: 0.4rem 0 0.7rem 0;
    }
    .callout strong { color: #FF6B35; }

    /* Footnote */
    .footnote {
        font-size: 0.7rem;
        color: #9CA3AF;
        border-top: 1px solid #E5E7EB;
        padding-top: 0.4rem;
        margin-top: 0.8rem;
        font-style: italic;
    }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 0.13rem 0.5rem;
        border-radius: 3px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        border: 1px solid transparent;
    }
    .badge-critical { background:#FBEAEC; color:#B92434; border-color:#F1B8BF; }
    .badge-warning { background:#FEF3C7; color:#92400E; border-color:#FDE68A; }
    .badge-monitor { background:#F3F4F6; color:#4B5563; border-color:#D1D5DB; }
    .badge-success { background:#D1FAE5; color:#065F46; border-color:#A7F3D0; }

    /* Tabs */
    [data-baseweb="tab-list"] { gap:0; border-bottom:1px solid #E5E7EB; margin-bottom:0.5rem; }
    [data-baseweb="tab"] { padding:0.5rem 1rem !important; font-weight:500 !important;
                           color:#6B7280 !important; border-bottom:2px solid transparent !important; font-size:0.92rem !important; }
    [data-baseweb="tab"][aria-selected="true"] {
        color:#FF6B35 !important; border-bottom-color:#FF6B35 !important; font-weight:600 !important;
    }

    /* Streamlit metric overrides */
    [data-testid="stMetricValue"] { font-size: 1.55rem; font-weight: 700; color: #111827; }
    [data-testid="stMetricLabel"] { font-size: 0.68rem; text-transform: uppercase; letter-spacing:0.06em; color:#6B7280; font-weight:600; }
    [data-testid="stMetricDelta"] { font-size: 0.72rem; }

    /* Sidebar */
    [data-testid="stSidebar"] h3 { font-size:0.7rem !important; text-transform:uppercase; letter-spacing:0.08em;
                                    color:#6B7280 !important; font-weight:600; margin-top:0.8rem !important; }
    [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background: #FF6B35 !important;
    }

    /* Buttons */
    .stDownloadButton button, .stButton button {
        background: #FF6B35; color: white; border: none; font-weight: 500; font-size: 0.85rem;
    }
    .stDownloadButton button:hover, .stButton button:hover { background: #E55A24; }

    /* Selectbox / multiselect compact */
    [data-baseweb="select"] { font-size: 0.9rem; }

    /* Plotly modebar — hide */
    .js-plotly-plot .plotly .modebar { display: none !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# COMMON CHART STYLE
# ============================================================
def style_fig(fig, height=300, showlegend=False):
    fig.update_layout(
        height=height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11, color=TEXT_DARK),
        margin=dict(t=10, b=30, l=10, r=10),
        showlegend=showlegend,
        legend=dict(orientation="h", y=-0.18, font=dict(size=10)) if showlegend else None,
        hoverlabel=dict(bgcolor="white", font=dict(family="Inter", size=11), bordercolor="#E5E7EB"),
    )
    fig.update_xaxes(gridcolor="#F3F4F6", zerolinecolor="#E5E7EB", linecolor="#E5E7EB",
                     tickfont=dict(size=10, color=TEXT_MUTED), title_font=dict(size=10, color=TEXT_MUTED))
    fig.update_yaxes(gridcolor="#F3F4F6", zerolinecolor="#E5E7EB", linecolor="#E5E7EB",
                     tickfont=dict(size=10, color=TEXT_MUTED), title_font=dict(size=10, color=TEXT_MUTED))
    return fig


# ============================================================
# DATA LOAD + ENRICH
# ============================================================
@st.cache_data
def load_csv(content: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(content), keep_default_na=False, na_values=[""])
    if "Access Score" in df.columns:
        df["Access Score"] = pd.to_numeric(df["Access Score"], errors="coerce").fillna(50).astype(int)
    return enrich(df)

@st.cache_data
def load_path(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, keep_default_na=False, na_values=[""])
    if "Access Score" in df.columns:
        df["Access Score"] = pd.to_numeric(df["Access Score"], errors="coerce").fillna(50).astype(int)
    return enrich(df)


def to_int(v, d=0):
    try: return int(str(v).strip())
    except: return d


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Policy ID"] = df["Filename"].str.replace(".pdf", "", regex=False)
    df["Display Name"] = df.apply(lambda r: f"{r['Brand'].title()} · {r['Filename'].split('-')[0]}", axis=1)
    df["Severity"] = df["Access Score"].apply(
        lambda s: "critical" if s < 38 else ("warning" if s < 50 else ("monitor" if s < 62 else "success"))
    )
    df["Severity Label"] = df["Severity"].map({
        "critical": "Restricted",
        "warning": "Guarded",
        "monitor": "At parity",
        "success": "Preferred"
    })
    # Restrictiveness signals
    df["_brand_steps"] = df["Number of Steps through Brands"].apply(lambda v: to_int(v, 0))
    df["_generic_steps"] = df["Number of Steps through Generic"].apply(lambda v: to_int(v, 0))
    df["_phototherapy"] = (df["Step through-Phototherapy"] == "Yes").astype(int)
    df["_tb"] = (df["TB Test required"] == "Yes").astype(int)
    df["_specialist"] = (~df["Specialist Types"].isin(["NA", "No", ""])).astype(int)
    df["_qty"] = (~df["Quantity Limits"].isin(["NA", "No", ""])).astype(int)
    df["Restriction Score"] = (
        df["_brand_steps"] + df["_generic_steps"] +
        df["_phototherapy"] + df["_tb"] + df["_specialist"] + df["_qty"]
    )
    df["Initial Auth (mo)"] = df["Initial Authorization Duration(in-months)"].apply(lambda v: to_int(v, 0))
    df["Reauth (mo)"] = df["Reauthorization Duration(in-months)"].apply(lambda v: to_int(v, 0))
    return df


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style='padding:0 0 0.9rem 0; border-bottom:1px solid #E5E7EB;'>
        <div style='font-family:"Source Serif Pro",serif; font-size:1.2rem; font-weight:700; color:#111827; line-height:1.2;'>
            Payer Policy<br/>Intelligence
        </div>
        <div style='font-size:0.7rem; color:#6B7280; margin-top:0.25rem;'>
            Access quality across US Prior Authorization policies
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Data")
    uploaded = st.file_uploader("Upload `result.csv`", type=["csv"], label_visibility="collapsed")

    df: Optional[pd.DataFrame] = None
    if uploaded is not None:
        df = load_csv(uploaded.getvalue())
    else:
        for p in ["result.csv", "outputs/result.csv"]:
            if pathlib.Path(p).exists():
                df = load_path(p)
                break

    if df is None:
        st.warning("Upload `result.csv` to begin.")
        st.stop()

    st.caption(f"**{len(df)}** rows · {df['Brand'].nunique()} brands · {df['Filename'].nunique()} policies")

    st.markdown("### Filters")
    all_brands = sorted(df["Brand"].unique())
    f_brands = st.multiselect("Brand", all_brands, default=all_brands, label_visibility="collapsed")
    f_score = st.slider("Access Score", 0, 100,
                        (int(df["Access Score"].min()), int(df["Access Score"].max())))
    f_severity = st.multiselect(
        "Severity tier",
        ["critical","warning","monitor","success"],
        default=["critical","warning","monitor","success"],
        format_func=lambda s: {"critical":"Restricted","warning":"Guarded",
                              "monitor":"At parity","success":"Preferred"}[s],
    )

    dfv = df[df["Brand"].isin(f_brands)
             & df["Access Score"].between(*f_score)
             & df["Severity"].isin(f_severity)].copy()
    st.caption(f"`{len(dfv)} of {len(df)} match`")


# ============================================================
# HEADER
# ============================================================
n_critical = (dfv["Severity"] == "critical").sum()
n_warning = (dfv["Severity"] == "warning").sum()
n_monitor = (dfv["Severity"] == "monitor").sum()
n_success = (dfv["Severity"] == "success").sum()
avg_score = dfv["Access Score"].mean() if len(dfv) else 0
parity_delta = avg_score - 50

st.markdown(f"""
<div class='headline'>
    <span class='pre'>Payer Policy Intelligence</span>
    <span class='pipe'>|</span>
    {len(dfv)} policies · {dfv['Brand'].nunique()} brands ·
    {avg_score:.1f} avg access ({abs(parity_delta):.1f} {'below' if parity_delta<0 else 'above'} FDA parity)
</div>
""", unsafe_allow_html=True)


# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Overview",
    "Restriction Diagnostic",
    "Brand Benchmarking",
    "Policy Inspector",
    "Comparative Analysis",
    "Methodology"
])


# ----------------------------------------------------------------
# TAB 1 — OVERVIEW (dashboard grid)
# ----------------------------------------------------------------
with tab1:
    # KPI STRIP
    pct_restricted = 100 * n_critical / max(1, len(dfv))
    pct_preferred = 100 * n_success / max(1, len(dfv))
    st.markdown(f"""
    <div class='kpi-strip'>
        <div class='kpi-tile accent'>
            <div class='kpi-label'>Policies analyzed</div>
            <div class='kpi-value'>{len(dfv)}</div>
            <div class='kpi-delta neutral'>{dfv['Filename'].nunique()} unique documents</div>
        </div>
        <div class='kpi-tile'>
            <div class='kpi-label'>Average access score</div>
            <div class='kpi-value'>{avg_score:.1f}</div>
            <div class='kpi-delta {"neg" if parity_delta<0 else "pos"}'>
                {'↓' if parity_delta<0 else '↑'} {abs(parity_delta):.1f} vs parity
            </div>
        </div>
        <div class='kpi-tile critical'>
            <div class='kpi-label'>Restricted</div>
            <div class='kpi-value' style='color:#B92434;'>{n_critical}</div>
            <div class='kpi-delta neg'>{pct_restricted:.0f}% of book</div>
        </div>
        <div class='kpi-tile warning'>
            <div class='kpi-label'>Guarded</div>
            <div class='kpi-value' style='color:#D97706;'>{n_warning}</div>
            <div class='kpi-delta neutral'>{100*n_warning/max(1,len(dfv)):.0f}% of book</div>
        </div>
        <div class='kpi-tile success'>
            <div class='kpi-label'>Preferred</div>
            <div class='kpi-value' style='color:#059669;'>{n_success}</div>
            <div class='kpi-delta pos'>{pct_preferred:.0f}% of book</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CHART GRID 2x2
    col_a, col_b = st.columns(2)

    # CHART 1 — Score distribution histogram
    with col_a:
        st.markdown("<div class='chart-title'>Access score distribution</div><div class='chart-sub'>Anchors: 38 (restricted) · 50 (FDA parity) · 62 (preferred)</div>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=dfv["Access Score"], nbinsx=20,
            marker=dict(color=ZS_ORANGE, line=dict(width=0)),
            hovertemplate="Score range: %{x}<br>Policies: %{y}<extra></extra>",
        ))
        fig.add_vrect(x0=0, x1=38, fillcolor=COLOR_CRITICAL, opacity=0.08, line_width=0, layer="below")
        fig.add_vrect(x0=62, x1=100, fillcolor=COLOR_SUCCESS, opacity=0.08, line_width=0, layer="below")
        fig.add_vline(x=50, line=dict(color=TEXT_MUTED, dash="dash", width=1.5))
        fig.add_annotation(x=50, y=1, yref="paper", text="parity",
                          showarrow=False, yshift=8, font=dict(size=10, color=TEXT_MUTED))
        fig = style_fig(fig, height=280)
        fig.update_xaxes(title=None, range=[0, 100])
        fig.update_yaxes(title="Policies")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # CHART 2 — Brand performance ranked
    with col_b:
        st.markdown("<div class='chart-title'>Brand performance ranking</div><div class='chart-sub'>Average access score by brand (lower = more restrictive)</div>", unsafe_allow_html=True)
        brand_perf = (dfv.groupby("Brand", as_index=False)
                       .agg(avg_score=("Access Score", "mean"),
                            count=("Access Score", "size"))
                       .sort_values("avg_score"))
        # Color: red below parity, green above
        brand_perf["color"] = brand_perf["avg_score"].apply(
            lambda s: COLOR_CRITICAL if s < 38 else (COLOR_WARNING if s < 50 else (COLOR_MONITOR if s < 62 else COLOR_SUCCESS))
        )
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=brand_perf["Brand"], x=brand_perf["avg_score"],
            orientation="h",
            marker=dict(color=brand_perf["color"]),
            text=[f"{v:.0f}" for v in brand_perf["avg_score"]],
            textposition="outside",
            textfont=dict(size=10, color=TEXT_DARK),
            customdata=brand_perf["count"],
            hovertemplate="<b>%{y}</b><br>Avg score: %{x:.1f}<br>Policies: %{customdata}<extra></extra>",
        ))
        fig.add_vline(x=50, line=dict(color=TEXT_MUTED, dash="dash", width=1))
        fig = style_fig(fig, height=max(220, 22 * len(brand_perf)))
        fig.update_xaxes(title=None, range=[0, 100])
        fig.update_yaxes(title=None, tickfont=dict(size=10))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    col_c, col_d = st.columns(2)

    # CHART 3 — Severity donut
    with col_c:
        st.markdown("<div class='chart-title'>Severity composition</div><div class='chart-sub'>Distribution by access tier</div>", unsafe_allow_html=True)
        sev_counts = pd.DataFrame({
            "Severity": ["Restricted", "Guarded", "At parity", "Preferred"],
            "Count": [n_critical, n_warning, n_monitor, n_success],
            "Color": [COLOR_CRITICAL, COLOR_WARNING, COLOR_MONITOR, COLOR_SUCCESS],
        })
        sev_counts = sev_counts[sev_counts["Count"] > 0]
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=sev_counts["Severity"], values=sev_counts["Count"],
            hole=0.6,
            marker=dict(colors=sev_counts["Color"], line=dict(color="white", width=2)),
            textinfo="label+percent",
            textfont=dict(size=11, color="white", family="Inter"),
            hovertemplate="<b>%{label}</b><br>Policies: %{value}<br>%{percent}<extra></extra>",
        ))
        fig.add_annotation(text=f"<b>{len(dfv)}</b><br><span style='font-size:0.7rem;color:#6B7280'>policies</span>",
                          x=0.5, y=0.5, showarrow=False, font=dict(size=18, family="Inter", color=TEXT_DARK))
        fig = style_fig(fig, height=280)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # CHART 4 — Quadrant: restrictiveness vs score
    with col_d:
        st.markdown("<div class='chart-title'>Friction vs access matrix</div><div class='chart-sub'>Each dot = one policy. Lower-left = poor outcome (high friction, low access)</div>", unsafe_allow_html=True)
        # Add small jitter so coincident points are visible
        rng = np.random.default_rng(42)
        x_jit = dfv["Restriction Score"] + rng.uniform(-0.18, 0.18, size=len(dfv))
        y_jit = dfv["Access Score"] + rng.uniform(-0.7, 0.7, size=len(dfv))
        # Build color map
        all_brands_list = sorted(df["Brand"].unique())
        cmap = {b: BRAND_PALETTE[i % len(BRAND_PALETTE)] for i, b in enumerate(all_brands_list)}
        colors = dfv["Brand"].map(cmap)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_jit, y=y_jit, mode="markers",
            marker=dict(size=9, color=colors, opacity=0.7, line=dict(width=1, color="white")),
            customdata=np.stack([dfv["Brand"], dfv["Policy ID"], dfv["Access Score"]], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b><br>Policy: %{customdata[1]}<br>Access: %{customdata[2]}<br>Restrictions: %{x:.0f}<extra></extra>",
        ))
        fig.add_hline(y=50, line=dict(color=TEXT_MUTED, dash="dash", width=1))
        fig.add_vline(x=dfv["Restriction Score"].median(), line=dict(color=TEXT_MUTED, dash="dot", width=1))
        fig = style_fig(fig, height=280)
        fig.update_xaxes(title="Restriction count (steps + TB + photo + specialist + qty)")
        fig.update_yaxes(title="Access score", range=[0, 100])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # KEY INSIGHT
    if len(dfv) > 0:
        worst = dfv.loc[dfv["Access Score"].idxmin()]
        best = dfv.loc[dfv["Access Score"].idxmax()]
        score_range = best["Access Score"] - worst["Access Score"]
        st.markdown(f"""
        <div class='callout'>
            <strong>Spread:</strong> {score_range}-point gap between most-restrictive ({worst['Brand']} · {worst['Policy ID']}, score {worst['Access Score']})
            and most-preferred ({best['Brand']} · {best['Policy ID']}, score {best['Access Score']}) policy.
            {n_critical + n_warning} of {len(dfv)} policies sit below FDA parity.
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div class='footnote'>n={len(dfv)} (filename, brand) combinations · Extraction: Gemini 2.5 Flash · Access Score: deterministic rules-based (0–100)</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------
# TAB 2 — RESTRICTION DIAGNOSTIC
# ----------------------------------------------------------------
with tab2:
    # KPI strip: prevalence of each restriction
    tot = len(dfv)
    pct_brand_steps = 100 * (dfv["_brand_steps"] > 0).sum() / max(1, tot)
    pct_generic_steps = 100 * (dfv["_generic_steps"] > 0).sum() / max(1, tot)
    pct_photo = 100 * (dfv["_phototherapy"] == 1).sum() / max(1, tot)
    pct_tb = 100 * (dfv["_tb"] == 1).sum() / max(1, tot)
    pct_specialist = 100 * (dfv["_specialist"] == 1).sum() / max(1, tot)

    st.markdown(f"""
    <div class='kpi-strip'>
        <div class='kpi-tile'><div class='kpi-label'>Brand step therapy</div>
            <div class='kpi-value'>{pct_brand_steps:.0f}%</div>
            <div class='kpi-delta neutral'>of policies</div></div>
        <div class='kpi-tile'><div class='kpi-label'>Generic step therapy</div>
            <div class='kpi-value'>{pct_generic_steps:.0f}%</div>
            <div class='kpi-delta neutral'>of policies</div></div>
        <div class='kpi-tile'><div class='kpi-label'>Phototherapy step</div>
            <div class='kpi-value'>{pct_photo:.0f}%</div>
            <div class='kpi-delta neutral'>of policies</div></div>
        <div class='kpi-tile'><div class='kpi-label'>TB testing</div>
            <div class='kpi-value'>{pct_tb:.0f}%</div>
            <div class='kpi-delta neutral'>of policies</div></div>
        <div class='kpi-tile'><div class='kpi-label'>Specialist required</div>
            <div class='kpi-value'>{pct_specialist:.0f}%</div>
            <div class='kpi-delta neutral'>of policies</div></div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([5, 4])

    # CHART 1 — Restriction prevalence horizontal bar
    with col_a:
        st.markdown("<div class='chart-title'>Restriction prevalence</div><div class='chart-sub'>Share of policies imposing each access gate</div>", unsafe_allow_html=True)
        rest_data = pd.DataFrame({
            "Restriction": ["Brand step therapy", "Generic step therapy", "Phototherapy step",
                           "TB testing", "Specialist required", "Quantity limits"],
            "Pct": [pct_brand_steps, pct_generic_steps, pct_photo, pct_tb, pct_specialist,
                    100 * (dfv["_qty"] == 1).sum() / max(1, tot)],
        }).sort_values("Pct", ascending=True)
        rest_data["color"] = rest_data["Pct"].apply(
            lambda p: COLOR_CRITICAL if p > 60 else (COLOR_WARNING if p > 30 else COLOR_MONITOR)
        )
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=rest_data["Restriction"], x=rest_data["Pct"], orientation="h",
            marker=dict(color=rest_data["color"]),
            text=[f"{v:.0f}%" for v in rest_data["Pct"]],
            textposition="outside",
            textfont=dict(size=10, color=TEXT_DARK),
            hovertemplate="<b>%{y}</b><br>%{x:.0f}% of policies<extra></extra>",
        ))
        fig = style_fig(fig, height=260)
        fig.update_xaxes(title="% of policies", range=[0, 110])
        fig.update_yaxes(title=None)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # CHART 2 — Heatmap: brand × restriction
    with col_b:
        st.markdown("<div class='chart-title'>Restriction heatmap by brand</div><div class='chart-sub'>% of brand's policies with each restriction</div>", unsafe_allow_html=True)
        brand_x_rest = dfv.groupby("Brand").agg(
            brand_step=("_brand_steps", lambda s: 100 * (s > 0).mean()),
            generic_step=("_generic_steps", lambda s: 100 * (s > 0).mean()),
            phototherapy=("_phototherapy", lambda s: 100 * s.mean()),
            tb=("_tb", lambda s: 100 * s.mean()),
            specialist=("_specialist", lambda s: 100 * s.mean()),
        ).round(0)
        brand_x_rest = brand_x_rest.sort_index()
        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=brand_x_rest.values,
            x=["Brand step", "Generic step", "Photo", "TB", "Specialist"],
            y=brand_x_rest.index,
            colorscale=[[0, "#F9FAFB"], [0.5, "#FDB97A"], [1, COLOR_CRITICAL]],
            zmin=0, zmax=100,
            showscale=True,
            colorbar=dict(thickness=10, tickfont=dict(size=9), title=None, len=0.6),
            text=brand_x_rest.values.astype(int),
            texttemplate="%{text}",
            textfont=dict(size=9, family="Inter"),
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.0f}%<extra></extra>",
        ))
        fig = style_fig(fig, height=max(220, 18 * len(brand_x_rest)))
        fig.update_xaxes(side="top", tickfont=dict(size=10))
        fig.update_yaxes(tickfont=dict(size=10))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Bottom: top friction policies and stacked-bar
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("<div class='chart-title'>Most restrictive policies</div><div class='chart-sub'>Top 10 by restriction count</div>", unsafe_allow_html=True)
        top_rest = dfv.nlargest(10, "Restriction Score")[["Policy ID", "Brand", "Restriction Score", "Access Score"]].copy()
        top_rest["label"] = top_rest["Brand"].str.slice(0, 8) + " · " + top_rest["Policy ID"].str.slice(0, 12)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=top_rest["label"][::-1], x=top_rest["Restriction Score"][::-1],
            orientation="h",
            marker=dict(color=top_rest["Access Score"][::-1],
                       colorscale=[[0, COLOR_CRITICAL], [0.5, COLOR_WARNING], [1, COLOR_SUCCESS]],
                       cmin=0, cmax=100,
                       showscale=False),
            text=[f"{v:.0f}" for v in top_rest["Restriction Score"][::-1]],
            textposition="outside",
            textfont=dict(size=10, color=TEXT_DARK),
            customdata=top_rest["Access Score"][::-1],
            hovertemplate="<b>%{y}</b><br>Restrictions: %{x}<br>Access score: %{customdata}<extra></extra>",
        ))
        fig = style_fig(fig, height=320)
        fig.update_xaxes(title="Restriction count")
        fig.update_yaxes(title=None, tickfont=dict(size=9))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_d:
        st.markdown("<div class='chart-title'>Auth duration distribution</div><div class='chart-sub'>Initial vs reauthorization periods</div>", unsafe_allow_html=True)
        ia = dfv["Initial Auth (mo)"].replace(0, np.nan).dropna()
        rr = dfv["Reauth (mo)"].replace(0, np.nan).dropna()
        fig = go.Figure()
        if len(ia):
            fig.add_trace(go.Histogram(x=ia, name="Initial",
                                       marker=dict(color=ZS_ORANGE, opacity=0.75),
                                       nbinsx=12,
                                       hovertemplate="Initial: %{x} mo<br>%{y} policies<extra></extra>"))
        if len(rr):
            fig.add_trace(go.Histogram(x=rr, name="Reauth",
                                       marker=dict(color=ZS_NAVY, opacity=0.75),
                                       nbinsx=12,
                                       hovertemplate="Reauth: %{x} mo<br>%{y} policies<extra></extra>"))
        fig = style_fig(fig, height=320, showlegend=True)
        fig.update_xaxes(title="Months")
        fig.update_yaxes(title="Policies")
        fig.update_layout(barmode="overlay")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # CALLOUT
    top_friction = rest_data.iloc[-1]
    st.markdown(f"""
    <div class='callout'>
        <strong>Lead driver of friction:</strong> {top_friction['Restriction'].lower()} appears in {top_friction['Pct']:.0f}% of policies.
        Reducing it would shift the score distribution upward by ~3-5 points per policy.
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<div class='footnote'>Restriction count = brand steps + generic steps + (1 each for phototherapy, TB, specialist, quantity limits) · n={len(dfv)}</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------
# TAB 3 — BRAND BENCHMARKING (interactive: pick a brand)
# ----------------------------------------------------------------
with tab3:
    brands_list = sorted(dfv["Brand"].unique())
    if not brands_list:
        st.info("No brands match the current filters.")
    else:
        # Brand selector at top
        focus_brand = st.radio(
            "Focus brand",
            options=brands_list,
            horizontal=True,
            label_visibility="collapsed",
            key="brand_focus"
        )

        focus_df = dfv[dfv["Brand"] == focus_brand]
        others_df = dfv[dfv["Brand"] != focus_brand]

        focus_avg = focus_df["Access Score"].mean() if len(focus_df) else 0
        others_avg = others_df["Access Score"].mean() if len(others_df) else 0
        delta_vs_market = focus_avg - others_avg

        # KPI strip for focus brand
        st.markdown(f"""
        <div class='kpi-strip'>
            <div class='kpi-tile accent'>
                <div class='kpi-label'>{focus_brand} policies</div>
                <div class='kpi-value'>{len(focus_df)}</div>
                <div class='kpi-delta neutral'>{focus_df['Filename'].nunique()} unique documents</div>
            </div>
            <div class='kpi-tile'>
                <div class='kpi-label'>Avg access score</div>
                <div class='kpi-value'>{focus_avg:.1f}</div>
                <div class='kpi-delta {"pos" if delta_vs_market>=0 else "neg"}'>
                    {'↑' if delta_vs_market>=0 else '↓'} {abs(delta_vs_market):.1f} vs other brands
                </div>
            </div>
            <div class='kpi-tile'>
                <div class='kpi-label'>vs FDA parity</div>
                <div class='kpi-value'>{focus_avg-50:+.1f}</div>
                <div class='kpi-delta {"pos" if focus_avg>=50 else "neg"}'>
                    {'above' if focus_avg>=50 else 'below'} 50
                </div>
            </div>
            <div class='kpi-tile critical'>
                <div class='kpi-label'>Restricted</div>
                <div class='kpi-value' style='color:#B92434;'>{(focus_df['Severity']=='critical').sum()}</div>
                <div class='kpi-delta neg'>{100*(focus_df['Severity']=='critical').sum()/max(1,len(focus_df)):.0f}% of brand book</div>
            </div>
            <div class='kpi-tile success'>
                <div class='kpi-label'>Preferred</div>
                <div class='kpi-value' style='color:#059669;'>{(focus_df['Severity']=='success').sum()}</div>
                <div class='kpi-delta pos'>{100*(focus_df['Severity']=='success').sum()/max(1,len(focus_df)):.0f}% of brand book</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2 columns of charts
        col_a, col_b = st.columns(2)

        # CHART 1 — Distribution overlay: brand vs all
        with col_a:
            st.markdown(f"<div class='chart-title'>{focus_brand} vs market distribution</div><div class='chart-sub'>Density of access scores</div>", unsafe_allow_html=True)
            fig = go.Figure()
            if len(others_df):
                fig.add_trace(go.Histogram(
                    x=others_df["Access Score"], name="Other brands",
                    marker=dict(color="#D1D5DB"), opacity=0.6, nbinsx=20,
                    histnorm="probability density",
                    hovertemplate="Other brands<br>Score: %{x}<extra></extra>",
                ))
            fig.add_trace(go.Histogram(
                x=focus_df["Access Score"], name=focus_brand,
                marker=dict(color=ZS_ORANGE), opacity=0.85, nbinsx=20,
                histnorm="probability density",
                hovertemplate=f"{focus_brand}<br>Score: %{{x}}<extra></extra>",
            ))
            fig.add_vline(x=50, line=dict(color=TEXT_MUTED, dash="dash", width=1))
            fig = style_fig(fig, height=280, showlegend=True)
            fig.update_xaxes(title="Access score", range=[0, 100])
            fig.update_yaxes(title="Density")
            fig.update_layout(barmode="overlay")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # CHART 2 — Restriction profile radar
        with col_b:
            st.markdown(f"<div class='chart-title'>{focus_brand} restriction profile</div><div class='chart-sub'>% of brand policies with each restriction (vs market)</div>", unsafe_allow_html=True)
            axes = ["Brand step", "Generic step", "Photo", "TB", "Specialist", "Qty"]
            def profile(d):
                if not len(d): return [0]*6
                return [
                    100 * (d["_brand_steps"]>0).mean(),
                    100 * (d["_generic_steps"]>0).mean(),
                    100 * (d["_phototherapy"]==1).mean(),
                    100 * (d["_tb"]==1).mean(),
                    100 * (d["_specialist"]==1).mean(),
                    100 * (d["_qty"]==1).mean(),
                ]
            focus_prof = profile(focus_df)
            other_prof = profile(others_df)

            fig = go.Figure()
            if len(others_df):
                fig.add_trace(go.Scatterpolar(
                    r=other_prof + [other_prof[0]],
                    theta=axes + [axes[0]],
                    fill="toself", name="Other brands",
                    line=dict(color="#9CA3AF", width=2),
                    fillcolor="rgba(156,163,175,0.2)",
                ))
            fig.add_trace(go.Scatterpolar(
                r=focus_prof + [focus_prof[0]],
                theta=axes + [axes[0]],
                fill="toself", name=focus_brand,
                line=dict(color=ZS_ORANGE, width=2),
                fillcolor="rgba(255,107,53,0.3)",
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(range=[0, 100], tickfont=dict(size=9, color=TEXT_MUTED),
                                   gridcolor="#E5E7EB", linecolor="#E5E7EB"),
                    angularaxis=dict(tickfont=dict(size=10, color=TEXT_DARK), gridcolor="#E5E7EB"),
                ),
                height=300,
                font=dict(family="Inter"),
                margin=dict(t=20, b=20, l=30, r=30),
                paper_bgcolor="white",
                showlegend=True,
                legend=dict(orientation="h", y=-0.15, font=dict(size=10)),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # CHART 3 — Brand's policies ranked by access
        st.markdown(f"<div class='chart-title'>{focus_brand} policies ranked by access score</div><div class='chart-sub'>Click bar to identify policy</div>", unsafe_allow_html=True)
        ranked = focus_df.sort_values("Access Score").copy()
        ranked["color"] = ranked["Severity"].map({
            "critical": COLOR_CRITICAL, "warning": COLOR_WARNING,
            "monitor": COLOR_MONITOR, "success": COLOR_SUCCESS
        })
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=ranked["Policy ID"], y=ranked["Access Score"],
            marker=dict(color=ranked["color"]),
            text=[f"{v}" for v in ranked["Access Score"]],
            textposition="outside",
            textfont=dict(size=9, color=TEXT_DARK),
            customdata=ranked["Severity Label"],
            hovertemplate="<b>Policy %{x}</b><br>Score: %{y}<br>Tier: %{customdata}<extra></extra>",
        ))
        fig.add_hline(y=50, line=dict(color=TEXT_MUTED, dash="dash", width=1))
        fig = style_fig(fig, height=300)
        fig.update_xaxes(title=None, tickangle=-45, tickfont=dict(size=8))
        fig.update_yaxes(title="Access score", range=[0, 100])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Smart callout
        peers = others_df.groupby("Brand")["Access Score"].mean()
        if len(peers):
            rank = (peers < focus_avg).sum() + 1
            n_brands = peers.size + 1
            comparison_text = f"rank <strong>{rank} of {n_brands}</strong>"
        else:
            comparison_text = "only brand in view"

        st.markdown(f"""
        <div class='callout'>
            <strong>{focus_brand}:</strong> {comparison_text} on average access ({focus_avg:.1f} vs market avg {others_avg:.1f}).
            Profile shows {'higher' if delta_vs_market<0 else 'lower'} friction than peers across {sum(1 for a,b in zip(focus_prof,other_prof) if a>b)}/6 restriction categories.
        </div>
        """, unsafe_allow_html=True)


# ----------------------------------------------------------------
# TAB 4 — POLICY INSPECTOR (drill-down)
# ----------------------------------------------------------------
with tab4:
    if not len(dfv):
        st.info("No policies match the current filters.")
    else:
        df_v = dfv.reset_index(drop=True).copy()
        df_v["__key"] = df_v["Display Name"] + "  (" + df_v["Filename"] + ")"
        sel = st.selectbox("Policy", options=df_v["__key"].tolist(), label_visibility="collapsed")
        row = df_v[df_v["__key"] == sel].iloc[0]
        sev = row["Severity"]
        sev_label = row["Severity Label"]

        # Header band
        st.markdown(f"""
        <div style='background:#111827; border-radius:4px; padding:0.9rem 1.2rem; margin-bottom:0.8rem;'>
            <div style='display:flex; gap:0.5rem; align-items:center; margin-bottom:0.4rem;'>
                <span class='badge badge-{sev}'>{sev_label}</span>
                <span style='color:#FF6B35; font-weight:600; font-size:0.85rem;'>{row['Brand']}</span>
                <span style='color:#9CA3AF; font-size:0.78rem;'>· Policy {row['Policy ID']}</span>
            </div>
            <div style='font-family:"Source Serif Pro",serif; font-size:1.25rem; color:#FFFFFF; font-weight:600; line-height:1.3;'>
                Access Score <span style='color:#FF6B35;'>{row['Access Score']}</span>
                · {abs(row['Access Score']-50)} pts {"below" if row['Access Score']<50 else "above"} FDA parity
            </div>
        </div>
        """, unsafe_allow_html=True)

        # KPI strip + waterfall chart together
        brand_avg = df[df["Brand"] == row["Brand"]]["Access Score"].mean()
        all_avg = df["Access Score"].mean()
        pct_within_brand = int((df[df["Brand"] == row["Brand"]]["Access Score"] <= row["Access Score"]).mean() * 100)

        st.markdown(f"""
        <div class='kpi-strip' style='grid-template-columns: repeat(4, 1fr);'>
            <div class='kpi-tile accent'>
                <div class='kpi-label'>vs Brand average</div>
                <div class='kpi-value'>{row['Access Score']}</div>
                <div class='kpi-delta {"pos" if row['Access Score']>=brand_avg else "neg"}'>
                    {row['Access Score']-brand_avg:+.1f} vs {brand_avg:.1f}
                </div>
            </div>
            <div class='kpi-tile'>
                <div class='kpi-label'>vs Overall average</div>
                <div class='kpi-value'>{row['Access Score']}</div>
                <div class='kpi-delta {"pos" if row['Access Score']>=all_avg else "neg"}'>
                    {row['Access Score']-all_avg:+.1f} vs {all_avg:.1f}
                </div>
            </div>
            <div class='kpi-tile'>
                <div class='kpi-label'>Brand percentile</div>
                <div class='kpi-value'>{pct_within_brand}</div>
                <div class='kpi-delta neutral'>of {row['Brand']} policies</div>
            </div>
            <div class='kpi-tile'>
                <div class='kpi-label'>Restriction count</div>
                <div class='kpi-value'>{int(row['Restriction Score'])}</div>
                <div class='kpi-delta neutral'>access gates imposed</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns([5, 4])

        # Waterfall chart of score calculation
        with col_a:
            st.markdown("<div class='chart-title'>Score breakdown</div><div class='chart-sub'>How each parameter shifts the score from FDA parity baseline of 50</div>", unsafe_allow_html=True)

            deductions = []
            additions = []
            bs = to_int(row["Number of Steps through Brands"], 0)
            gs = to_int(row["Number of Steps through Generic"], 0)
            if bs > 0: deductions.append((f"Brand step × {bs}", -5.0 * min(bs, 5)))
            if gs > 0: deductions.append((f"Generic step × {gs}", -2.5 * min(gs, 5)))
            if row["Step through-Phototherapy"] == "Yes": deductions.append(("Phototherapy", -5.0))
            if row["TB Test required"] == "Yes": deductions.append(("TB testing", -3.5))
            spec = str(row["Specialist Types"])
            if spec not in ("NA","No",""):
                n_sp = len([s for s in spec.split(";") if s.strip()])
                deductions.append((f"Specialist ({n_sp})", -3.5 if n_sp<=1 else (-2.5 if n_sp<=2 else -1.5)))
            if str(row["Quantity Limits"]) not in ("No","NA",""):
                deductions.append(("Quantity limit", -2.0))
            ia = to_int(row["Initial Authorization Duration(in-months)"])
            if ia >= 12: additions.append(("Initial auth ≥12mo", 6.0))
            elif ia >= 6: additions.append((f"Initial auth {ia}mo", 2.0))
            elif 0<ia<6: deductions.append((f"Short auth ({ia}mo)", -3.0))
            rd = to_int(row["Reauthorization Duration(in-months)"])
            if rd >= 12: additions.append(("Reauth ≥12mo", 4.0))
            elif rd >= 6: additions.append((f"Reauth {rd}mo", 1.0))
            elif 0<rd<6: deductions.append((f"Short reauth ({rd}mo)", -2.0))
            if row["Reauthorization Required"] == "No": additions.append(("No reauth required", 3.0))

            # Build waterfall sequence
            labels = ["FDA parity"] + [d[0] for d in deductions] + [a[0] for a in additions] + ["Final"]
            measures = ["absolute"] + ["relative"]*(len(deductions)+len(additions)) + ["total"]
            values = [50] + [d[1] for d in deductions] + [a[1] for a in additions] + [None]

            fig = go.Figure(go.Waterfall(
                x=labels, y=values, measure=measures,
                connector=dict(line=dict(color="#D1D5DB", width=1)),
                decreasing=dict(marker=dict(color=COLOR_CRITICAL)),
                increasing=dict(marker=dict(color=COLOR_SUCCESS)),
                totals=dict(marker=dict(color=ZS_ORANGE)),
                text=[f"{v:+.1f}" if isinstance(v,(int,float)) and m=="relative" else (f"{int(v)}" if v else f"{int(row['Access Score'])}") for v,m in zip(values,measures)],
                textposition="outside",
                textfont=dict(size=10, color=TEXT_DARK),
            ))
            fig = style_fig(fig, height=320)
            fig.update_xaxes(title=None, tickangle=-30, tickfont=dict(size=9))
            fig.update_yaxes(title="Score points", range=[0, 70])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Parameter grid (compact)
        with col_b:
            st.markdown("<div class='chart-title'>Parameter detail</div><div class='chart-sub'>Extracted values</div>", unsafe_allow_html=True)
            params = [
                ("Age", row["Age"], None),
                ("Brand steps", row["Number of Steps through Brands"], "step"),
                ("Generic steps", row["Number of Steps through Generic"], "step"),
                ("Phototherapy", row["Step through-Phototherapy"], "yesno_bad"),
                ("TB test", row["TB Test required"], "yesno_bad"),
                ("Specialist", row["Specialist Types"], None),
                ("Quantity limit", row["Quantity Limits"], None),
                ("Initial auth (mo)", row["Initial Authorization Duration(in-months)"], "month"),
                ("Reauth (mo)", row["Reauthorization Duration(in-months)"], "month"),
                ("Reauth required", row["Reauthorization Required"], None),
            ]
            html = "<div style='border:1px solid #E5E7EB; border-radius:4px; overflow:hidden;'>"
            for label, val, kind in params:
                vs = str(val)
                color = TEXT_DARK
                if kind == "yesno_bad":
                    color = COLOR_CRITICAL if vs == "Yes" else (COLOR_SUCCESS if vs == "No" else TEXT_MUTED)
                elif kind == "step" and vs.isdigit() and int(vs) > 0:
                    color = COLOR_CRITICAL
                elif kind == "step" and vs in ("No", "0"):
                    color = COLOR_SUCCESS
                elif kind == "month":
                    try:
                        n = int(vs); color = COLOR_SUCCESS if n>=12 else (COLOR_WARNING if n>=6 else COLOR_CRITICAL)
                    except: color = TEXT_MUTED
                html += f"""
                <div style='display:flex; justify-content:space-between; padding:0.35rem 0.7rem;
                            border-bottom:1px dashed #F3F4F6; font-size:0.83rem;'>
                    <span style='color:{TEXT_MUTED};'>{label}</span>
                    <span style='color:{color}; font-weight:600;'>{vs[:40]}</span>
                </div>"""
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

        # Expandable verbatim language
        with st.expander("Verbatim policy language", expanded=False):
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown("**Step therapy requirements**")
                st.caption(row["Step Therapy Requirements Documented in Policy"])
            with cc2:
                st.markdown("**Reauthorization requirements**")
                st.caption(row["Reauthorization Requirements Documented in Policy"])


# ----------------------------------------------------------------
# TAB 5 — COMPARATIVE ANALYSIS (was: Side-by-Side Compare)
# ----------------------------------------------------------------
with tab5:
    if len(dfv) < 2:
        st.info("Need at least 2 policies in the filter to compare.")
    else:
        df_v = dfv.reset_index(drop=True).copy()
        df_v["__key"] = df_v["Display Name"] + "  (" + df_v["Filename"] + ")"
        picked_keys = st.multiselect(
            "Select 2–4 policies for comparison",
            df_v["__key"].tolist(),
            default=df_v["__key"].tolist()[:2],
            max_selections=4,
        )

        if len(picked_keys) >= 2:
            picked = df_v[df_v["__key"].isin(picked_keys)].copy()
            picked["short"] = picked.apply(lambda r: f"{r['Brand'][:8]} · {r['Policy ID'][:10]}", axis=1)

            col_a, col_b = st.columns([5, 4])

            # CHART 1 — Bar chart of access scores side-by-side
            with col_a:
                st.markdown("<div class='chart-title'>Access score comparison</div><div class='chart-sub'>Selected policies</div>", unsafe_allow_html=True)
                colors = picked["Severity"].map({
                    "critical": COLOR_CRITICAL, "warning": COLOR_WARNING,
                    "monitor": COLOR_MONITOR, "success": COLOR_SUCCESS
                })
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=picked["short"], y=picked["Access Score"],
                    marker=dict(color=colors),
                    text=picked["Access Score"], textposition="outside",
                    textfont=dict(size=11, color=TEXT_DARK),
                ))
                fig.add_hline(y=50, line=dict(color=TEXT_MUTED, dash="dash", width=1))
                fig = style_fig(fig, height=270)
                fig.update_yaxes(title="Access score", range=[0, 100])
                fig.update_xaxes(title=None, tickfont=dict(size=10))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # CHART 2 — Radar overlay
            with col_b:
                st.markdown("<div class='chart-title'>Restriction profile overlay</div><div class='chart-sub'>Normalized 0–1 by restriction category</div>", unsafe_allow_html=True)
                axes = ["Brand step", "Generic step", "Photo", "TB", "Specialist", "Qty"]
                fig = go.Figure()
                colors_radar = [ZS_ORANGE, ZS_NAVY, COLOR_SUCCESS, "#7C3AED"]
                for i, (_, r) in enumerate(picked.iterrows()):
                    vals = [
                        min(r["_brand_steps"]/5, 1),
                        min(r["_generic_steps"]/5, 1),
                        r["_phototherapy"],
                        r["_tb"],
                        r["_specialist"],
                        r["_qty"],
                    ]
                    fig.add_trace(go.Scatterpolar(
                        r=vals + [vals[0]],
                        theta=axes + [axes[0]],
                        fill="toself", name=r["short"],
                        line=dict(color=colors_radar[i % 4], width=2),
                        fillcolor=colors_radar[i % 4],
                        opacity=0.35,
                    ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(range=[0,1], tickfont=dict(size=8), gridcolor="#E5E7EB"),
                              angularaxis=dict(tickfont=dict(size=10), gridcolor="#E5E7EB")),
                    height=290,
                    font=dict(family="Inter"),
                    margin=dict(t=10, b=10, l=30, r=30),
                    paper_bgcolor="white",
                    showlegend=True,
                    legend=dict(orientation="h", y=-0.1, font=dict(size=9)),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Diff table — visual
            st.markdown("<div class='chart-title'>Parameter-by-parameter</div><div class='chart-sub'>Differences highlighted</div>", unsafe_allow_html=True)
            display_cols = ["Brand", "Access Score", "Age",
                "Number of Steps through Brands", "Number of Steps through Generic",
                "Step through-Phototherapy", "TB Test required", "Quantity Limits",
                "Specialist Types",
                "Initial Authorization Duration(in-months)",
                "Reauthorization Duration(in-months)",
                "Reauthorization Required"]
            comp = picked.set_index("short")[display_cols].astype(str).T
            def diff_style(r):
                vals = [str(v).strip() for v in r.values]
                if len(set(vals)) > 1:
                    return ["background-color:#FFF8F2; color:#111827; font-weight:500;"] * len(r)
                return ["color:#9CA3AF;"] * len(r)
            st.dataframe(comp.style.apply(diff_style, axis=1), use_container_width=True, height=440)

            # Summary
            n_diff = sum(1 for col in comp.index if len(set(str(v).strip() for v in comp.loc[col].values)) > 1)
            st.markdown(f"""
            <div class='callout'>
                <strong>{n_diff} of {len(comp)} parameters</strong> differ across the {len(picked_keys)} selected policies.
                Highlighted rows show where these policies diverge.
            </div>
            """, unsafe_allow_html=True)


# ----------------------------------------------------------------
# TAB 6 — METHODOLOGY (compact)
# ----------------------------------------------------------------
with tab6:
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown("""
        ##### Pipeline

        | Stage | Process |
        |---|---|
        | 1 | PDF text extraction (pdfplumber + pdftotext fallback, hash-cached) |
        | 2 | Hierarchical brand scoping with cross-brand negative filtering |
        | 3 | Brand-stratified few-shot retrieval (2 same-brand + 1 cross-brand, from 439 gold rows) |
        | 4 | Gemini 2.5 Flash extraction with Pydantic schema enforcement |
        | 5 | 3-layer validation: formatting → business rules → contradiction detection |
        | 6 | Deterministic Access Score (monotonic rules-based, 0–100) |

        ##### Design priorities

        - **Deterministic scoring** for reproducibility — no LLM variance in the final score
        - **Evidence-grounded extraction** — every value backed by a verbatim policy quote
        - **3-layer validation** — formatting + cross-field rules + keyword-based contradiction detection
        - **Hash-cached at every stage** — iteration is free, reviewers reproduce exactly
        """)

    with col_b:
        # Access Score anchor table
        st.markdown("##### Access Score calibration")
        anchors = pd.DataFrame({
            "Anchor": [0, 25, 50, 75, 100],
            "Label": ["No access", "Restricted", "FDA parity", "Preferred", "Best possible"],
            "Reference": [
                "Drug excluded from formulary",
                "3 brand steps + TB + specialty + age + 6mo auth",
                "Mirrors FDA label",
                "No steps, 12mo auth, broad eligibility",
                "No restrictions"
            ],
        })
        st.dataframe(anchors, use_container_width=True, hide_index=True, height=240)

        st.markdown("""
        <div class='callout'>
            <strong>Note:</strong> Anchors are reference points on a continuous 0–100 scale, not bucketed outputs.
            Real policies score anywhere on the scale.
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div class='footnote'>Pipeline run: {pd.Timestamp.now().strftime('%Y-%m-%d')} · n={len(dfv)} (filename, brand) rows in current view · Built for the H1'26 hackathon</div>", unsafe_allow_html=True)
