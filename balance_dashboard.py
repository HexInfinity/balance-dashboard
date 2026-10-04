"""
Personal Finance Dashboard
--------------------------
Reads the "Main" tab of your balance tracker workbook and renders a
fintech-style dashboard: net worth trend, liquidity ratio, investment
platform performance (HL / Trading 212 / Crypto), account breakdowns,
credit card exposure, and mortgage/debt payoff progress.

Run with:
    pip install streamlit pandas openpyxl plotly
    streamlit run balance_dashboard.py
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --------------------------------------------------------------------------
# Page config + fintech dark theme
# --------------------------------------------------------------------------
st.set_page_config(page_title="Balance Dashboard", page_icon="\U0001F4CA", layout="wide")

ACCENT = "#3DD68C"      # green — growth / positive
ACCENT_2 = "#5B8DEF"    # blue — cash / liquidity
WARN = "#F5A623"        # amber — caution
DANGER = "#E5484D"      # red — debt / negative
BG = "#0E1117"
CARD = "#161B22"
TEXT_MUTED = "#8B949E"

st.markdown(f"""
<style>
    .stApp {{ background-color: {BG}; }}
    div[data-testid="stMetric"] {{
        background-color: {CARD};
        border: 1px solid #21262D;
        border-radius: 10px;
        padding: 14px 18px;
    }}
    div[data-testid="stMetricLabel"] {{ color: {TEXT_MUTED}; }}
    h1, h2, h3 {{ color: #E6EDF3; }}
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color="#E6EDF3"),
        xaxis=dict(gridcolor="#21262D", zerolinecolor="#21262D"),
        yaxis=dict(gridcolor="#21262D", zerolinecolor="#21262D"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=10, t=40, b=10),
    )
)

st.title("Personal Finance Dashboard")

# --------------------------------------------------------------------------
# Load + parse the "Main" sheet
# --------------------------------------------------------------------------
COL_MAP = {
    0: "date",
    1: "santander_current", 2: "barclays_current", 3: "bos_current", 4: "nationwide_current",
    5: "regular_saver", 6: "esavings_barclays", 7: "tandem", 8: "hl_cash_isa", 9: "total_accounts",
    11: "cc_santander", 12: "cc_bos", 13: "cc_mbna", 14: "cc_total",
    16: "banking_balance", 17: "gearing", 18: "change", 19: "movement_pct",
    21: "wage", 22: "needed",
    24: "hl_cash", 25: "hl_assets", 26: "hl_paid_in", 27: "hl_discrete_growth",
    28: "hl_invested", 29: "hl_cum_growth", 30: "hl_pct_growth", 31: "hl_yearly_growth",
    33: "t212_cash", 34: "t212_assets", 35: "t212_paid_in", 36: "t212_discrete_growth",
    37: "t212_invested", 38: "t212_cum_growth", 39: "t212_pct_growth", 40: "t212_yearly_growth",
    42: "crypto_cash", 43: "crypto_basket", 44: "crypto_wallet", 45: "crypto_assets",
    46: "crypto_paid_in", 47: "crypto_discrete_growth", 48: "crypto_invested",
    49: "crypto_cum_growth", 50: "crypto_pct_growth", 51: "crypto_yearly_growth",
    53: "cash_balance", 54: "investment_balance", 55: "liquidity", 57: "total_net",
    59: "sofa_debt", 60: "mortgage", 62: "fun_balance", 63: "fun_change", 64: "fun_change_pct",
}


@st.cache_data
def load_data(file) -> pd.DataFrame:
    raw = pd.read_excel(file, sheet_name="Main", header=None, skiprows=2, engine="openpyxl")
    keep_idx = [i for i in COL_MAP if i < raw.shape[1]]
    df = raw[keep_idx].rename(columns={i: COL_MAP[i] for i in keep_idx})

    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    numeric_cols = [c for c in df.columns if c != "date"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.drop_duplicates(subset="date", keep="last")
    return df


uploaded = st.sidebar.file_uploader("Balance tracker (.xlsx)", type=["xlsx"])
if uploaded is None:
    st.info("Upload your balance tracker workbook in the sidebar to get started.")
    st.stop()

df = load_data(uploaded)

min_d, max_d = df["date"].min(), df["date"].max()
date_range = st.sidebar.slider(
    "Date range", min_value=min_d.to_pydatetime(), max_value=max_d.to_pydatetime(),
    value=(min_d.to_pydatetime(), max_d.to_pydatetime()), format="MMM YYYY",
)
df = df[(df["date"] >= date_range[0]) & (df["date"] <= date_range[1])]
latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) > 1 else latest

def delta(col):
    return latest[col] - prev[col]

# --------------------------------------------------------------------------
# KPI row
# --------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Net Worth (liquid)", f"£{latest['total_net']:,.0f}", f"{delta('total_net'):+,.0f}")
k2.metric("Liquidity Ratio", f"{latest['liquidity']*100:,.1f}%",
          f"{(latest['liquidity']-prev['liquidity'])*100:+.1f} pp")
k3.metric("Cash Balance", f"£{latest['cash_balance']:,.0f}", f"{delta('cash_balance'):+,.0f}")
k4.metric("Investment Balance", f"£{latest['investment_balance']:,.0f}",
          f"{delta('investment_balance'):+,.0f}")
k5.metric("Mortgage Remaining", f"£{latest['mortgage']:,.0f}", f"{delta('mortgage'):+,.0f}",
          delta_color="inverse")

st.caption(f"Snapshot as of {latest['date'].strftime('%d %b %Y')}")
st.divider()

# --------------------------------------------------------------------------
# Net worth composition + liquidity ratio
# --------------------------------------------------------------------------
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Net Worth Composition")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["cash_balance"], name="Cash",
                              stackgroup="one", line=dict(color=ACCENT_2, width=0.5),
                              fillcolor="rgba(91,141,239,0.5)"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["investment_balance"], name="Investments",
                              stackgroup="one", line=dict(color=ACCENT, width=0.5),
                              fillcolor="rgba(61,214,140,0.5)"))
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=360, yaxis_title="£")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Liquidity Ratio")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["liquidity"]*100, mode="lines",
                              line=dict(color=ACCENT_2, width=2), fill="tozeroy",
                              fillcolor="rgba(91,141,239,0.15)"))
    fig.add_hrect(y0=0, y1=30, fillcolor=DANGER, opacity=0.08, line_width=0)
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=360, yaxis_title="% cash of liquid assets",
                       yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------------------------------------------------
# Investment platform performance
# --------------------------------------------------------------------------
st.subheader("Investment Platform Performance")
p1, p2 = st.columns(2)

platforms = {
    "Hargreaves Lansdown": ("hl_assets", "hl_pct_growth", "hl_yearly_growth"),
    "Trading 212": ("t212_assets", "t212_pct_growth", "t212_yearly_growth"),
    "Crypto": ("crypto_assets", "crypto_pct_growth", "crypto_yearly_growth"),
}

with p1:
    fig = go.Figure()
    colors = [ACCENT, ACCENT_2, WARN]
    for (name, (asset_col, _, _)), color in zip(platforms.items(), colors):
        fig.add_trace(go.Scatter(x=df["date"], y=df[asset_col], name=name,
                                  line=dict(color=color, width=2)))
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=340, title="Assets by platform", yaxis_title="£")
    st.plotly_chart(fig, use_container_width=True)

with p2:
    names, cum_growth, yearly_growth = [], [], []
    for name, (_, pct_col, yr_col) in platforms.items():
        names.append(name)
        cum_growth.append((latest[pct_col] or 0) * 100)
        yearly_growth.append((latest[yr_col] or 0) * 100)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=cum_growth, name="Cumulative %", marker_color=ACCENT_2))
    fig.add_trace(go.Bar(x=names, y=yearly_growth, name="Yearly %", marker_color=ACCENT))
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=340, barmode="group",
                       title="Rate of return by platform (latest)", yaxis_title="%")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------------------------------------------------
# Account breakdown + credit cards + income headroom
# --------------------------------------------------------------------------
b1, b2, b3 = st.columns(3)

with b1:
    st.subheader("Current Accounts (latest)")
    acc_cols = {
        "Santander": "santander_current", "Barclays": "barclays_current",
        "Bank of Scotland": "bos_current", "Nationwide": "nationwide_current",
    }
    vals = {k: latest[v] for k, v in acc_cols.items() if pd.notna(latest[v])}
    fig = go.Figure(go.Bar(x=list(vals.values()), y=list(vals.keys()), orientation="h",
                            marker_color=ACCENT_2))
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=280, xaxis_title="£")
    st.plotly_chart(fig, use_container_width=True)

with b2:
    st.subheader("Credit Card Exposure")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["cc_total"], line=dict(color=DANGER, width=2),
                              fill="tozeroy", fillcolor="rgba(229,72,77,0.15)"))
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=280, yaxis_title="£ owed")
    st.plotly_chart(fig, use_container_width=True)

with b3:
    st.subheader("Wage vs Needed")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["date"], y=df["wage"], name="Wage", marker_color=ACCENT))
    fig.add_trace(go.Bar(x=df["date"], y=df["needed"], name="Needed", marker_color=WARN))
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=280, barmode="overlay", yaxis_title="£")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------------------------------------------------
# Mortgage payoff + fun balance
# --------------------------------------------------------------------------
m1, m2 = st.columns(2)

with m1:
    st.subheader("Mortgage & Debt Payoff")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["mortgage"], name="Mortgage",
                              line=dict(color=DANGER, width=2)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["sofa_debt"], name="Other debt",
                              line=dict(color=WARN, width=2)))
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=320, yaxis_title="£ remaining")
    st.plotly_chart(fig, use_container_width=True)

with m2:
    st.subheader("Fun Balance (net worth ex. debt)")
    fig = go.Figure()
    colors = np.where(df["fun_balance"] >= 0, ACCENT, DANGER)
    fig.add_trace(go.Bar(x=df["date"], y=df["fun_balance"], marker_color=list(colors)))
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=320, yaxis_title="£")
    st.plotly_chart(fig, use_container_width=True)
