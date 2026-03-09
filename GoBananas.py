"""
🍌 GoBananas Dashboard
======================
Interactive dashboard to determine optimal selling strategy:
sell by the piece or by the kilo?

Run with:
    streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from models import (
    MarketConfig,
    profit_analysis,
    sweep_foot_traffic,
    sweep_price_sensitivity,
    sweep_piece_price,
    heatmap_data,
    monthly_projection,
)

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="🍌 GoBananas",
    page_icon="🍌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background: #0e0e0e;
    color: #f0ead6;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800;
    letter-spacing: -0.02em;
}

.metric-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
}

.verdict-piece {
    background: linear-gradient(135deg, #f5c842 0%, #e8a020 100%);
    color: #0e0e0e;
    border-radius: 16px;
    padding: 24px 32px;
    text-align: center;
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.02em;
}

.verdict-kilo {
    background: linear-gradient(135deg, #42c5f5 0%, #2080e8 100%);
    color: #0e0e0e;
    border-radius: 16px;
    padding: 24px 32px;
    text-align: center;
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.02em;
}

.mono {
    font-family: 'DM Mono', monospace;
}

section[data-testid="stSidebar"] {
    background: #141414;
    border-right: 1px solid #222;
}

.stSlider > div > div > div > div {
    background: #f5c842 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar: Parameters ───────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Parameters")
    st.markdown("---")

    st.markdown("### 💰 Pricing")
    price_per_piece = st.slider("Price per piece (€)", 0.10, 0.80, 0.30, 0.01,
                                 format="€%.2f")
    price_per_kilo = st.slider("Price per kilo (€)", 0.60, 3.00, 1.20, 0.05,
                                format="€%.2f")
    cost_per_kilo = st.slider("Wholesale cost /kg (€)", 0.20, 1.20, 0.55, 0.05,
                               format="€%.2f")
    bananas_per_kilo = st.slider("Bananas per kilo", 4.0, 9.0, 6.5, 0.5)

    st.markdown("### 📊 Demand")
    piece_demand = st.slider("Piece-preferring customers (%)", 0, 80, 40, 5,
                              format="%d%%") / 100
    kilo_demand = st.slider("Kilo-preferring customers (%)", 0, 80, 35, 5,
                             format="%d%%") / 100
    daily_customers = st.slider("Daily customers", 20, 1000, 200, 10)

    st.markdown("### 🏪 Operations")
    spoilage = st.slider("Spoilage rate (%)", 0, 30, 8, 1, format="%d%%") / 100
    display_space = st.slider("Display capacity (kg)", 5.0, 100.0, 20.0, 5.0)
    foot_traffic = st.slider("Foot traffic multiplier", 0.2, 3.0, 1.0, 0.1,
                              help="1.0 = normal, 3.0 = very high (market, station)")
    price_sensitivity = st.slider("Customer price sensitivity", 0.3, 3.0, 1.0, 0.1,
                                   help="1.0 = normal, 3.0 = very price-sensitive")

# ── Build config ──────────────────────────────────────────────────────────────

config = MarketConfig(
    price_per_piece=price_per_piece,
    price_per_kilo=price_per_kilo,
    cost_per_kilo=cost_per_kilo,
    bananas_per_kilo=bananas_per_kilo,
    piece_demand_pct=piece_demand,
    kilo_demand_pct=kilo_demand,
    daily_customers=daily_customers,
    spoilage_rate=spoilage,
    display_space_kg=display_space,
    foot_traffic_multiplier=foot_traffic,
    price_sensitivity=price_sensitivity,
)

result = profit_analysis(config)

# ── Plotly theme ──────────────────────────────────────────────────────────────

DARK_BG = "#0e0e0e"
CARD_BG = "#1a1a1a"
GRID_COLOR = "#2a2a2a"
YELLOW = "#f5c842"
BLUE = "#42c5f5"
GREEN = "#5af576"
RED = "#f55a5a"
TEXT = "#f0ead6"

plotly_layout = dict(
    paper_bgcolor=CARD_BG,
    plot_bgcolor=CARD_BG,
    font=dict(family="Syne, sans-serif", color=TEXT),
    xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    margin=dict(l=40, r=20, t=40, b=40),
)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("# 🍌 GoBananas")
st.markdown("*When should you sell by the piece — and when by the kilo?*")
st.markdown("---")

# ── Verdict ───────────────────────────────────────────────────────────────────

col_v1, col_v2, col_v3, col_v4 = st.columns([2, 1, 1, 1])

verdict_class = "verdict-piece" if result["optimal"] == "Piece" else "verdict-kilo"
verdict_emoji = "🍌" if result["optimal"] == "Piece" else "⚖️"

with col_v1:
    st.markdown(
        f'<div class="{verdict_class}">'
        f'{verdict_emoji} Sell by <strong>{result["optimal"]}</strong><br>'
        f'<span style="font-size:1rem; font-weight:400; opacity:0.8">'
        f'{result["advantage_pct"]:.1f}% more profitable</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

with col_v2:
    st.metric("Daily Profit — Piece",
              f"€{result['daily_profit_piece']:.2f}",
              delta=f"€{result['daily_profit_piece'] - result['daily_profit_kilo']:+.2f} vs kilo")

with col_v3:
    st.metric("Daily Profit — Kilo",
              f"€{result['daily_profit_kilo']:.2f}")

with col_v4:
    rev_piece = result["rev_per_kg_piece"]
    rev_kilo = result["rev_per_kg_kilo"]
    st.metric("Revenue /kg — Piece", f"€{rev_piece:.2f}",
              delta=f"€{rev_piece - rev_kilo:+.2f} vs kilo")

st.markdown("---")

# ── Row 1: Foot traffic sweep & Price sensitivity sweep ──────────────────────

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🚶 Foot Traffic vs. Profit")
    df_ft = sweep_foot_traffic(config)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_ft["foot_traffic"], y=df_ft["profit_piece"],
        name="Piece", line=dict(color=YELLOW, width=3),
        fill="tozeroy", fillcolor="rgba(245,200,66,0.08)"
    ))
    fig.add_trace(go.Scatter(
        x=df_ft["foot_traffic"], y=df_ft["profit_kilo"],
        name="Kilo", line=dict(color=BLUE, width=3),
        fill="tozeroy", fillcolor="rgba(66,197,245,0.08)"
    ))
    # Mark current position
    fig.add_vline(x=foot_traffic, line_dash="dash", line_color=GREEN,
                  annotation_text="current", annotation_font_color=GREEN)
    fig.update_layout(
        **plotly_layout,
        title="Daily Profit as Foot Traffic Increases",
        xaxis_title="Foot Traffic Multiplier",
        yaxis_title="Daily Profit (€)",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=340,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 💸 Price Sensitivity vs. Profit")
    df_ps = sweep_price_sensitivity(config)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_ps["price_sensitivity"], y=df_ps["profit_piece"],
        name="Piece", line=dict(color=YELLOW, width=3),
        fill="tozeroy", fillcolor="rgba(245,200,66,0.08)"
    ))
    fig2.add_trace(go.Scatter(
        x=df_ps["price_sensitivity"], y=df_ps["profit_kilo"],
        name="Kilo", line=dict(color=BLUE, width=3),
        fill="tozeroy", fillcolor="rgba(66,197,245,0.08)"
    ))
    fig2.add_vline(x=price_sensitivity, line_dash="dash", line_color=GREEN,
                   annotation_text="current", annotation_font_color=GREEN)
    fig2.update_layout(
        **plotly_layout,
        title="Daily Profit as Price Sensitivity Increases",
        xaxis_title="Price Sensitivity Multiplier",
        yaxis_title="Daily Profit (€)",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=340,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Heatmap & Piece-price break-even ──────────────────────────────────

col3, col4 = st.columns(2)

with col3:
    st.markdown("### 🗺️ Strategy Heatmap")
    st.caption("Foot traffic × Price sensitivity — which strategy wins?")

    df_heat = heatmap_data(config, n=35)
    pivot = df_heat.pivot(index="price_sensitivity", columns="foot_traffic", values="advantage")

    fig3 = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, "#1a4a6e"],
            [0.45, "#0a2a4e"],
            [0.5, "#1a1a1a"],
            [0.55, "#4a3a00"],
            [1.0, "#f5c842"],
        ],
        zmid=0,
        colorbar=dict(
            title=dict(text="Piece advantage (€)", font=dict(color=TEXT)),
            tickfont=dict(color=TEXT),
        ),
        hovertemplate=(
            "Foot Traffic: %{x:.1f}<br>"
            "Price Sensitivity: %{y:.1f}<br>"
            "Piece advantage: €%{z:.2f}<extra></extra>"
        ),
    ))
    # Mark current settings
    fig3.add_trace(go.Scatter(
        x=[foot_traffic], y=[price_sensitivity],
        mode="markers",
        marker=dict(color=GREEN, size=14, symbol="x", line=dict(width=3)),
        name="Current settings",
        showlegend=True,
    ))
    fig3.update_layout(
        **plotly_layout,
        xaxis_title="Foot Traffic Multiplier",
        yaxis_title="Price Sensitivity",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=360,
        annotations=[
            dict(x=0.15, y=2.6, text="🔵 Kilo wins", showarrow=False,
                 font=dict(color=BLUE, size=12)),
            dict(x=2.5, y=0.5, text="🟡 Piece wins", showarrow=False,
                 font=dict(color=YELLOW, size=12)),
        ]
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("### 📍 Break-even: Piece Price")
    st.caption("At what piece price does selling individually become optimal?")

    df_pp = sweep_piece_price(config)

    # Find crossover
    df_pp["diff"] = df_pp["profit_piece"] - df_pp["profit_kilo"]
    crossover = df_pp[df_pp["diff"] >= 0]["price_per_piece"].min()

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=df_pp["price_per_piece"], y=df_pp["profit_piece"],
        name="Piece profit", line=dict(color=YELLOW, width=3),
    ))
    fig4.add_trace(go.Scatter(
        x=df_pp["price_per_piece"], y=df_pp["profit_kilo"],
        name="Kilo profit", line=dict(color=BLUE, width=3),
    ))
    if not np.isnan(crossover):
        fig4.add_vline(x=crossover, line_dash="dot", line_color=GREEN,
                       annotation_text=f"break-even €{crossover:.2f}",
                       annotation_font_color=GREEN)
    fig4.add_vline(x=price_per_piece, line_dash="dash", line_color=RED,
                   annotation_text="current", annotation_font_color=RED)
    fig4.update_layout(
        **plotly_layout,
        title="Profit vs. Piece Price",
        xaxis_title="Price per Piece (€)",
        yaxis_title="Daily Profit (€)",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=360,
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: 30-day projection ──────────────────────────────────────────────────

st.markdown("### 📅 30-Day Cumulative Profit Projection")
st.caption("Includes day-to-day demand variation. Mixed = pieces Mon–Fri, kilo on weekends.")

df_month = monthly_projection(config, days=30)

fig5 = go.Figure()
fig5.add_trace(go.Scatter(
    x=df_month["day"], y=df_month["cumulative_piece"],
    name="Always Piece 🍌", line=dict(color=YELLOW, width=3),
    fill="tozeroy", fillcolor="rgba(245,200,66,0.05)"
))
fig5.add_trace(go.Scatter(
    x=df_month["day"], y=df_month["cumulative_kilo"],
    name="Always Kilo ⚖️", line=dict(color=BLUE, width=3),
    fill="tozeroy", fillcolor="rgba(66,197,245,0.05)"
))
fig5.add_trace(go.Scatter(
    x=df_month["day"], y=df_month["cumulative_mixed"],
    name="Mixed Strategy 🔀", line=dict(color=GREEN, width=2, dash="dot"),
))
fig5.update_layout(
    **plotly_layout,
    xaxis_title="Day",
    yaxis_title="Cumulative Profit (€)",
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    height=300,
)
st.plotly_chart(fig5, use_container_width=True)

# ── Row 4: Margin breakdown ───────────────────────────────────────────────────

st.markdown("### 🔬 Margin Breakdown")

col5, col6 = st.columns(2)

with col5:
    categories = ["Revenue /kg", "Spoilage Loss", "Cost", "Net Margin"]
    piece_vals = [
        result["rev_per_kg_piece"],
        -result["rev_per_kg_piece"] * 0.048,  # 60% of spoilage_rate
        -cost_per_kilo,
        result["margin_piece"],
    ]
    kilo_vals = [
        result["rev_per_kg_kilo"],
        -result["rev_per_kg_kilo"] * spoilage,
        -cost_per_kilo,
        result["margin_kilo"],
    ]

    fig6 = go.Figure()
    fig6.add_trace(go.Bar(name="Piece 🍌", x=categories, y=piece_vals,
                          marker_color=YELLOW, text=[f"€{v:.2f}" for v in piece_vals],
                          textposition="outside", textfont=dict(color=TEXT)))
    fig6.add_trace(go.Bar(name="Kilo ⚖️", x=categories, y=kilo_vals,
                          marker_color=BLUE, text=[f"€{v:.2f}" for v in kilo_vals],
                          textposition="outside", textfont=dict(color=TEXT)))
    fig6.update_layout(
        **plotly_layout,
        barmode="group",
        title="Per-kg Economics Comparison",
        yaxis_title="€ per kg",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=340,
    )
    st.plotly_chart(fig6, use_container_width=True)

with col6:
    st.markdown("#### 📋 Key Metrics")

    def metric_row(label, piece_val, kilo_val, fmt="€{:.2f}"):
        winner = "🟡 Piece" if piece_val > kilo_val else "🔵 Kilo"
        st.markdown(
            f"""<div class="metric-card">
            <div style="display:flex; justify-content:space-between; align-items:center">
                <span style="color:#888; font-size:0.85rem">{label}</span>
                <span style="font-size:0.8rem; color:#aaa">{winner}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:8px">
                <span style="color:{YELLOW}; font-family:'DM Mono',monospace; font-size:1.1rem">
                    🍌 {fmt.format(piece_val)}</span>
                <span style="color:{BLUE}; font-family:'DM Mono',monospace; font-size:1.1rem">
                    ⚖️ {fmt.format(kilo_val)}</span>
            </div></div>""",
            unsafe_allow_html=True,
        )

    metric_row("Revenue per kg", result["rev_per_kg_piece"], result["rev_per_kg_kilo"])
    metric_row("Gross margin per kg", result["margin_piece"], result["margin_kilo"])
    metric_row("Daily profit", result["daily_profit_piece"], result["daily_profit_kilo"])
    metric_row("Monthly profit (est.)",
               result["daily_profit_piece"] * 30,
               result["daily_profit_kilo"] * 30)

    implied_piece_per_kilo = price_per_piece * bananas_per_kilo
    premium_pct = (implied_piece_per_kilo - price_per_kilo) / price_per_kilo * 100
    st.markdown(
        f"""<div class="metric-card">
        <div style="color:#888; font-size:0.85rem">Piece-selling premium over kilo</div>
        <div style="color:{YELLOW if premium_pct > 0 else BLUE};
             font-family:'DM Mono',monospace; font-size:1.4rem; margin-top:8px">
            {premium_pct:+.1f}%</div>
        <div style="color:#666; font-size:0.8rem; margin-top:4px">
            Implied piece rate: €{implied_piece_per_kilo:.2f}/kg vs €{price_per_kilo:.2f}/kg
        </div></div>""",
        unsafe_allow_html=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#444; font-size:0.8rem;">'
    "🍌 GoBananas &nbsp;·&nbsp; "
    "Adjust parameters in the sidebar to explore your optimal strategy"
    "</div>",
    unsafe_allow_html=True,
)
