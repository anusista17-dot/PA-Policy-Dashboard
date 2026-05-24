"""
Payer Policy Intelligence Dashboard
====================================
Interactive Streamlit dashboard for the H1'26 hackathon.

Usage:
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
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal custom CSS for polish
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    [data-testid="stMetricValue"] { font-size: 2rem; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem; color: #666; }
    .badge {
        display: inline-block; padding: 0.2rem 0.6rem; border-radius: 0.4rem;
        font-size: 0.85rem; font-weight: 600;
    }
    .badge-yes { background: #fde0e0; color: #c62828; }
    .badge-no  { background: #e3f2fd; color: #1565c0; }
    .badge-na  { background: #f0f0f0; color: #666; }
    .param-row {
        padding: 0.5rem 0; border-bottom: 1px solid #f0f0f0;
    }
    .param-label { font-weight: 600; color: #444; font-size: 0.9rem; }
    .param-value { color: #222; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA LOADING
# ============================================================
NUMERIC_COLS = [
    "Number of Steps through Brands",
    "Number of Steps through Generic",
    "Initial Authorization Duration(in-months)",
    "Reauthorization Duration(in-months)",
    "Access Score",
]


@st.cache_data
def load_data_from_bytes(content: bytes) -> pd.DataFrame:
    """Load CSV from uploaded bytes; preserve 'NA' as a literal string."""
    df = pd.read_csv(io.BytesIO(content), keep_default_na=False, na_values=[""])
    if "Access Score" in df.columns:
        df["Access Score"] = pd.to_numeric(df["Access Score"], errors="coerce").fillna(50).astype(int)
    return df


@st.cache_data
def load_data_from_path(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, keep_default_na=False, na_values=[""])
    if "Access Score" in df.columns:
        df["Access Score"] = pd.to_numeric(df["Access Score"], errors="coerce").fillna(50).astype(int)
    return df


def to_int(v, default: int = 0) -> int:
    try:
        return int(str(v).strip())
    except Exception:
        return default


def restrictiveness_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Derive numeric 0-1 restrictiveness scores per parameter."""
    out = df.copy()
    out["Brand Steps (n)"] = out["Number of Steps through Brands"].map(lambda v: to_int(v, 0))
    out["Generic Steps (n)"] = out["Number of Steps through Generic"].map(lambda v: to_int(v, 0))
    out["Phototherapy required"] = (out["Step through-Phototherapy"] == "Yes").astype(int)
    out["TB Test required"] = (out["TB Test required"] == "Yes").astype(int)
    out["Specialist required"] = (~out["Specialist Types"].isin(["NA", "No", ""])).astype(int)
    out["Short initial auth"] = out["Initial Authorization Duration(in-months)"].map(
        lambda v: 1 if (to_int(v, 12) < 12 and to_int(v, 12) > 0) else 0
    )
    return out


def score_color(score: float) -> str:
    """Map access score to a traffic-light colour."""
    if score < 25:   return "#d32f2f"
    if score < 50:   return "#f57c00"
    if score < 75:   return "#fbc02d"
    return "#388e3c"


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 📁 Data Source")
    uploaded = st.file_uploader("Upload `result.csv`", type=["csv"])
    df: Optional[pd.DataFrame] = None

    if uploaded is not None:
        df = load_data_from_bytes(uploaded.getvalue())
        st.success(f"Loaded {len(df)} rows from upload")
    else:
        # Try defaults in order
        for default_path in ["result.csv", "outputs/result.csv", "data/result.csv"]:
            if pathlib.Path(default_path).exists():
                df = load_data_from_path(default_path)
                st.info(f"Using `{default_path}` ({len(df)} rows)")
                break

    if df is None:
        st.warning("⬆️ Upload a `result.csv` to begin")
        st.caption("Expected columns: Filename, Brand, Age, ... Access Score (15 total)")
        st.stop()

    st.markdown("---")
    st.markdown("### 🔍 Filters")
    all_brands = sorted(df["Brand"].dropna().unique())
    brands_sel = st.multiselect("Brand", all_brands, default=all_brands)
    score_min, score_max = int(df["Access Score"].min()), int(df["Access Score"].max())
    score_range = st.slider(
        "Access Score range",
        min_value=0, max_value=100,
        value=(score_min, score_max),
    )

    df_view = df[
        df["Brand"].isin(brands_sel)
        & df["Access Score"].between(*score_range)
    ].copy()
    st.caption(f"**{len(df_view)}** of {len(df)} rows match filters")

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption(
        "Built for the H1'26 hackathon — extracts 12 structured parameters "
        "from US payer Prior Authorization policies and scores access quality "
        "on a continuous 0–100 scale."
    )


# ============================================================
# HEADER
# ============================================================
st.title("💊 Payer Policy Intelligence")
st.markdown(
    "<div style='color:#666; margin-top:-0.5rem; margin-bottom:1.5rem;'>"
    "Access quality analysis across Prior Authorization policies for plaque-psoriasis biologics"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# TABS
# ============================================================
tab_overview, tab_drill, tab_compare, tab_data = st.tabs(
    ["📊 Overview", "🔍 Policy Detail", "⚖️ Compare", "📋 Raw Data"]
)


# ----------------------------------------------------------------
# TAB 1: OVERVIEW
# ----------------------------------------------------------------
with tab_overview:
    # ---- KPI ROW ----
    c1, c2, c3, c4 = st.columns(4)
    avg_score = df_view["Access Score"].mean() if len(df_view) else 0
    delta_from_parity = avg_score - 50
    c1.metric("Total Policies", f"{len(df_view):,}")
    c2.metric(
        "Avg Access Score",
        f"{avg_score:.1f}",
        delta=f"{delta_from_parity:+.1f} vs FDA parity",
        delta_color="normal",
    )
    c3.metric("Brands Covered", df_view["Brand"].nunique())
    c4.metric(
        "Multi-brand Documents",
        int((df_view.groupby("Filename")["Brand"].count() > 1).sum())
        if len(df_view) else 0,
    )

    st.markdown("---")

    # ---- ACCESS SCORE DISTRIBUTION ----
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown("##### Access Score Distribution")
        fig_hist = px.histogram(
            df_view, x="Access Score", color="Brand",
            nbins=20, opacity=0.85,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_hist.add_vline(x=50, line_dash="dash", line_color="#666",
                          annotation_text="FDA parity", annotation_position="top right")
        fig_hist.add_vline(x=25, line_dash="dot", line_color="#999")
        fig_hist.add_vline(x=75, line_dash="dot", line_color="#999")
        fig_hist.update_layout(
            height=380, margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="Access Score (0 = no access → 100 = best possible)",
            yaxis_title="Number of policies",
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_b:
        st.markdown("##### Access Score Anchor Reference")
        anchors = pd.DataFrame({
            "Anchor": [
                "0 — No access",
                "25 — Restricted",
                "50 — FDA parity",
                "75 — Preferred",
                "100 — Best possible",
            ],
            "Count in view": [
                ((df_view["Access Score"] >= 0) & (df_view["Access Score"] < 13)).sum(),
                ((df_view["Access Score"] >= 13) & (df_view["Access Score"] < 38)).sum(),
                ((df_view["Access Score"] >= 38) & (df_view["Access Score"] < 63)).sum(),
                ((df_view["Access Score"] >= 63) & (df_view["Access Score"] < 88)).sum(),
                (df_view["Access Score"] >= 88).sum(),
            ],
        })
        st.dataframe(anchors, hide_index=True, use_container_width=True)
        st.caption(
            "Anchors are reference points on a continuous 0–100 scale. "
            "Bucketing every policy to one of these 5 values would collapse real variance."
        )

    # ---- BOX PLOT BY BRAND ----
    st.markdown("##### Access Score by Brand")
    fig_box = px.box(
        df_view.sort_values("Brand"),
        x="Brand", y="Access Score",
        color="Brand", points="all",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_box.add_hline(y=50, line_dash="dash", line_color="#666",
                     annotation_text="FDA parity", annotation_position="right")
    fig_box.update_layout(
        height=400, showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        yaxis=dict(range=[0, 100]),
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # ---- RESTRICTIVENESS HEATMAP ----
    st.markdown("##### Restrictiveness Profile by Brand")
    st.caption(
        "Each cell shows the mean restrictiveness signal for that parameter across policies for the brand. "
        "Brand-step counts are normalised to 0-1 by dividing by 5."
    )
    sig_df = restrictiveness_signals(df_view)
    sig_cols = [
        "Brand Steps (n)", "Generic Steps (n)",
        "Phototherapy required", "TB Test required",
        "Specialist required", "Short initial auth",
    ]
    # Normalise step counts to 0-1 for heatmap consistency
    sig_df["Brand Steps (n)"] = (sig_df["Brand Steps (n)"] / 5).clip(0, 1)
    sig_df["Generic Steps (n)"] = (sig_df["Generic Steps (n)"] / 5).clip(0, 1)
    heat = sig_df.groupby("Brand")[sig_cols].mean().round(2)
    if len(heat):
        fig_heat = px.imshow(
            heat.values,
            x=sig_cols, y=heat.index,
            color_continuous_scale="RdYlGn_r",
            aspect="auto", text_auto=".2f",
            zmin=0, zmax=1,
        )
        fig_heat.update_layout(
            height=max(280, 40 * len(heat)),
            margin=dict(t=10, b=10, l=10, r=10),
            coloraxis_colorbar=dict(title="Restr."),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # ---- RANKINGS ----
    st.markdown("##### Most & Least Restrictive Policies")
    col_l, col_r = st.columns(2)
    rank_cols = ["Filename", "Brand", "Access Score",
                "Number of Steps through Brands", "TB Test required"]
    with col_l:
        st.markdown("**🔴 Most restrictive** (lowest Access Score)")
        st.dataframe(
            df_view.nsmallest(5, "Access Score")[rank_cols],
            hide_index=True, use_container_width=True,
        )
    with col_r:
        st.markdown("**🟢 Least restrictive** (highest Access Score)")
        st.dataframe(
            df_view.nlargest(5, "Access Score")[rank_cols],
            hide_index=True, use_container_width=True,
        )


# ----------------------------------------------------------------
# TAB 2: POLICY DETAIL (DRILL-DOWN)
# ----------------------------------------------------------------
with tab_drill:
    if not len(df_view):
        st.info("No rows match the current filters.")
    else:
        df_view = df_view.reset_index(drop=True)
        df_view["__key"] = df_view["Filename"] + "  —  " + df_view["Brand"]
        sel = st.selectbox(
            "Select a (Filename, Brand) combination",
            options=df_view["__key"].tolist(),
        )
        row = df_view[df_view["__key"] == sel].iloc[0]

        st.markdown("---")

        # ---- TOP ROW: GAUGE + KEY FACTS ----
        gcol, fcol = st.columns([2, 3])

        with gcol:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=int(row["Access Score"]),
                number={"font": {"size": 56}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1,
                             "tickvals": [0, 25, 50, 75, 100]},
                    "bar": {"color": score_color(row["Access Score"]), "thickness": 0.3},
                    "steps": [
                        {"range": [0, 25],  "color": "#fde0e0"},
                        {"range": [25, 50], "color": "#fdf0d8"},
                        {"range": [50, 75], "color": "#e8f4d8"},
                        {"range": [75, 100],"color": "#d8f0d8"},
                    ],
                    "threshold": {
                        "line": {"color": "#222", "width": 3},
                        "thickness": 0.85,
                        "value": int(row["Access Score"]),
                    },
                },
                title={"text": "Access Score", "font": {"size": 18}},
            ))
            fig_gauge.update_layout(height=320, margin=dict(t=40, b=10, l=20, r=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with fcol:
            st.markdown(f"#### {row['Brand']}")
            st.caption(f"📄 `{row['Filename']}`")

            # Brand-context comparison
            brand_rows = df[df["Brand"] == row["Brand"]]
            brand_mean = brand_rows["Access Score"].mean()
            delta = row["Access Score"] - brand_mean
            overall_mean = df["Access Score"].mean()
            delta_all = row["Access Score"] - overall_mean

            cc1, cc2, cc3 = st.columns(3)
            cc1.metric(
                f"vs {row['Brand']} average",
                f"{row['Access Score']}",
                delta=f"{delta:+.1f} vs avg of {brand_mean:.1f}",
            )
            cc2.metric(
                "vs all policies avg",
                f"{row['Access Score']}",
                delta=f"{delta_all:+.1f} vs avg of {overall_mean:.1f}",
            )
            pct_value = int(round((brand_rows['Access Score'] <= row['Access Score']).mean() * 100))
            # Ordinal suffix: 1st, 2nd, 3rd, 4th... 11th, 12th, 13th... 21st, 22nd, 23rd
            if 11 <= (pct_value % 100) <= 13:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(pct_value % 10, "th")
            cc3.metric(
                "Brand percentile",
                f"{pct_value}{suffix}",
            )

            # Quick badges row
            st.markdown("")
            def badge(label: str, value: str) -> str:
                v = str(value).strip()
                if v == "Yes":
                    cls = "badge-yes"
                elif v in ("No", "NA"):
                    cls = "badge-no" if v == "No" else "badge-na"
                else:
                    cls = "badge-no"
                return f"<span class='badge {cls}'>{label}: {v}</span>"

            badges_html = " ".join([
                badge("TB test", row["TB Test required"]),
                badge("Phototherapy", row["Step through-Phototherapy"]),
                badge("Reauth", row["Reauthorization Required"]),
            ])
            st.markdown(badges_html, unsafe_allow_html=True)

        st.markdown("---")

        # ---- DETAILED PARAMETERS ----
        st.markdown("#### Extracted Parameters")
        param_cols_left = [
            "Age", "Number of Steps through Brands",
            "Number of Steps through Generic", "Step through-Phototherapy",
            "TB Test required", "Specialist Types",
        ]
        param_cols_right = [
            "Initial Authorization Duration(in-months)",
            "Reauthorization Duration(in-months)",
            "Reauthorization Required", "Quantity Limits",
        ]

        pcol_l, pcol_r = st.columns(2)
        with pcol_l:
            for c in param_cols_left:
                st.markdown(
                    f"<div class='param-row'>"
                    f"<div class='param-label'>{c}</div>"
                    f"<div class='param-value'>{row[c]}</div></div>",
                    unsafe_allow_html=True,
                )
        with pcol_r:
            for c in param_cols_right:
                st.markdown(
                    f"<div class='param-row'>"
                    f"<div class='param-label'>{c}</div>"
                    f"<div class='param-value'>{row[c]}</div></div>",
                    unsafe_allow_html=True,
                )

        # Long-text fields full width
        st.markdown("#### Verbatim policy language")
        with st.expander("Step Therapy Requirements Documented in Policy", expanded=False):
            st.write(row["Step Therapy Requirements Documented in Policy"])
        with st.expander("Reauthorization Requirements Documented in Policy", expanded=False):
            st.write(row["Reauthorization Requirements Documented in Policy"])


# ----------------------------------------------------------------
# TAB 3: COMPARE
# ----------------------------------------------------------------
with tab_compare:
    if len(df_view) < 2:
        st.info("Need at least 2 rows in the filter to compare.")
    else:
        df_view = df_view.reset_index(drop=True)
        df_view["__key"] = df_view["Filename"] + "  —  " + df_view["Brand"]
        choices = df_view["__key"].tolist()

        selected = st.multiselect(
            "Pick 2–3 policies to compare",
            choices,
            default=choices[:min(2, len(choices))],
            max_selections=3,
        )

        if len(selected) >= 2:
            picked = df_view[df_view["__key"].isin(selected)].copy()

            # Comparison table — transpose so parameters are rows, policies are columns
            display_cols = [
                "Brand", "Access Score", "Age",
                "Number of Steps through Brands", "Number of Steps through Generic",
                "Step through-Phototherapy", "TB Test required", "Quantity Limits",
                "Specialist Types",
                "Initial Authorization Duration(in-months)",
                "Reauthorization Duration(in-months)",
                "Reauthorization Required",
            ]
            comp = picked.set_index("__key")[display_cols].astype(str).T

            def highlight_diffs(row):
                vals = [str(v).strip() for v in row.values]
                if len(set(vals)) > 1:
                    return ["background-color: #fff4cc"] * len(row)
                return [""] * len(row)

            styled = comp.style.apply(highlight_diffs, axis=1)
            st.dataframe(styled, use_container_width=True, height=460)
            st.caption("🟡 Highlighted rows = the policies disagree on that parameter.")

            # Radar chart of restrictiveness signals
            st.markdown("##### Restrictiveness Profile (radar)")
            radar_signals = restrictiveness_signals(picked).set_index("__key")
            radar_axes = ["Brand Steps (n)", "Generic Steps (n)", "Phototherapy required",
                         "TB Test required", "Specialist required", "Short initial auth"]
            # Normalise step counts to 0-1
            radar_data = radar_signals[radar_axes].copy()
            radar_data["Brand Steps (n)"] = (radar_data["Brand Steps (n)"] / 5).clip(0, 1)
            radar_data["Generic Steps (n)"] = (radar_data["Generic Steps (n)"] / 5).clip(0, 1)

            fig_radar = go.Figure()
            colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
            for i, (key, vals) in enumerate(radar_data.iterrows()):
                fig_radar.add_trace(go.Scatterpolar(
                    r=list(vals.values) + [vals.values[0]],
                    theta=radar_axes + [radar_axes[0]],
                    fill="toself",
                    name=key, opacity=0.55,
                    line_color=colors[i % len(colors)],
                ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(range=[0, 1], visible=True)),
                showlegend=True, height=460,
                margin=dict(t=20, b=20, l=40, r=40),
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("Select at least 2 policies above.")


# ----------------------------------------------------------------
# TAB 4: RAW DATA
# ----------------------------------------------------------------
with tab_data:
    st.markdown(f"#### Filtered data ({len(df_view)} rows)")

    search = st.text_input("🔍 Search (filename or brand)", "")
    df_show = df_view.drop(columns=["__key"], errors="ignore")
    if search:
        mask = (
            df_show["Filename"].str.contains(search, case=False, na=False)
            | df_show["Brand"].str.contains(search, case=False, na=False)
        )
        df_show = df_show[mask]

    st.dataframe(df_show, use_container_width=True, height=520)

    # Download
    csv_bytes = df_show.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download filtered CSV",
        data=csv_bytes,
        file_name="result_filtered.csv",
        mime="text/csv",
    )


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption(
    "Built with Streamlit + Plotly. "
    "Source: extracted from 70 US payer Prior Authorization policy documents "
    "using Gemini 2.5 Flash via the pipeline in `solution.ipynb`."
)
