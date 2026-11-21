import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
from datetime import datetime
import json
import html
from pathlib import Path

st.set_page_config(
    page_title="Stock Valuation Framework",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS Styling ──────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Theme-aware: surfaces are translucent and text inherits Streamlit's light or dark colour */
    :root {
        --brand: #1a237e;
        --accent: #2962FF;
        --muted: color-mix(in srgb, currentColor 65%, transparent);
        --line: rgba(128, 128, 128, 0.25);
        --surface: rgba(128, 128, 128, 0.08);
        --radius: 14px;
        --shadow: 0 1px 2px rgba(0,0,0,0.10), 0 4px 14px rgba(0,0,0,0.10);
    }

    .block-container { padding-top: 1.25rem !important; max-width: 1400px; }
    h1 { margin-top: 0 !important; font-weight: 750; letter-spacing: -0.01em; }
    h2 { font-size: 1.45rem; letter-spacing: -0.01em; }
    h3 { font-size: 1.15rem; font-weight: 650; }
    hr { margin: 1.5rem 0; border: none; border-top: 1px solid var(--line); }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        padding: 0.95rem 1.05rem;
        box-shadow: var(--shadow);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-1px); }
    [data-testid="stMetricLabel"] p {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    [data-testid="stMetricValue"] > div {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        line-height: 1.2;
    }

    /* Tabs: pill style, theme-aware */
    .stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }
    .stTabs [data-baseweb="tab-list"] button {
        border-radius: 999px;
        padding: 0.4rem 1rem;
        font-weight: 600;
        border: 1px solid var(--line);
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background: var(--brand);
        border-color: var(--brand);
        color: #ffffff;
    }
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.1rem; }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: 1px solid var(--line);
        transition: all .15s ease;
    }
    .stButton > button:hover { border-color: var(--accent); color: var(--accent); }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--brand), var(--accent));
        border: none;
        color: #ffffff;
    }
    .stButton > button[kind="primary"]:hover { color: #ffffff; filter: brightness(1.06); }

    /* Expanders, inputs, containers */
    [data-testid="stExpander"] { border: 1px solid var(--line); border-radius: var(--radius); }
    .stTextInput input, .stNumberInput input { border-radius: 10px; }
    [data-testid="stVerticalBlockBorderWrapper"] { border-radius: var(--radius); }
    [data-testid="stDataFrame"] { border-radius: var(--radius); overflow: hidden; border: 1px solid var(--line); }
    [data-testid="stAlert"] { border-radius: 12px; }

    /* App banner (white text on brand gradient, so it reads in either theme) */
    .app-banner {
        background: linear-gradient(135deg, #1a237e 0%, #2962FF 100%);
        color: #ffffff;
        border-radius: 18px;
        padding: 1.5rem 1.75rem;
        box-shadow: 0 10px 30px rgba(26,35,126,0.25);
        margin-bottom: 1rem;
    }
    .app-kicker { font-size: 0.72rem; letter-spacing: 0.14em; font-weight: 700; opacity: 0.8; }
    .app-title { font-size: 1.9rem; font-weight: 750; margin: 0.25rem 0 0.3rem 0; letter-spacing: -0.01em; }
    .app-sub { font-size: 0.95rem; opacity: 0.92; }
    .app-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.9rem; }
    .app-chips span {
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.28);
        border-radius: 999px;
        padding: 0.2rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 600;
    }

    /* Empty state */
    .empty-state {
        background: var(--surface);
        border: 2px dashed var(--line);
        border-radius: 18px;
        padding: 2.5rem 1.5rem;
        text-align: center;
        color: var(--muted);
    }
    .empty-state .big { font-size: 2.4rem; }
    .empty-state .head { font-size: 1.2rem; font-weight: 700; margin: 0.5rem 0; color: inherit; }

    /* Stock hero card (white text on gradient) */
    .hero {
        background: linear-gradient(135deg, #1a237e 0%, #2962FF 100%);
        color: #ffffff;
        border-radius: 18px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px rgba(26,35,126,0.22);
    }
    .hero-ticker {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        border-radius: 6px;
        padding: 0.1rem 0.55rem;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.06em;
    }
    .hero-name { font-size: 1.6rem; font-weight: 750; margin: 0.4rem 0 0.2rem 0; }
    .hero-meta { font-size: 0.9rem; opacity: 0.9; }
    .hero-pill {
        display: inline-block;
        background: #ffffff;
        color: var(--brand);
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        font-weight: 700;
        margin-top: 0.6rem;
    }

    /* Summary report */
    .rpt-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 0.75rem; }
    .rpt-badge { display: inline-block; color: #ffffff; border-radius: 999px; padding: 0.3rem 0.9rem; font-weight: 700; font-size: 0.9rem; }
    .rpt-sub { color: var(--muted); font-size: 0.9rem; margin-top: 0.35rem; }
    .rpt-score { font-size: 2.2rem; font-weight: 800; line-height: 1; }
    .rpt-score span { font-size: 0.95rem; font-weight: 600; color: var(--muted); }

    /* Report key facts: wrapping cards */
    .fact-row { display: flex; flex-wrap: wrap; gap: 0.6rem; margin: 0.5rem 0 1rem 0; }
    .fact {
        flex: 1 1 170px;
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 0.7rem 0.9rem;
        box-shadow: var(--shadow);
        min-width: 0;
    }
    .fact-label { font-size: 0.72rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
    .fact-value { font-size: 1.25rem; font-weight: 700; line-height: 1.25; margin-top: 0.2rem; overflow-wrap: anywhere; }
    .fact-note { font-size: 0.8rem; color: var(--muted); margin-top: 0.15rem; }

    /* Market tabs: header (white text on gradient), summary cards, tile grid */
    .mk-head {
        background: linear-gradient(135deg, #1a237e 0%, #2962FF 100%);
        color: #ffffff;
        border-radius: 16px;
        padding: 1.1rem 1.4rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 8px 24px rgba(26,35,126,0.2);
    }
    .mk-kicker { font-size: 0.72rem; letter-spacing: 0.12em; font-weight: 700; opacity: 0.8; }
    .mk-title { font-size: 1.5rem; font-weight: 750; margin: 0.15rem 0; }
    .mk-sub { font-size: 0.9rem; opacity: 0.92; }
    .sum-row { display: flex; flex-wrap: wrap; gap: 0.7rem; margin-bottom: 0.9rem; }
    .sum-card {
        flex: 1 1 200px;
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 0.8rem 1rem;
        box-shadow: var(--shadow);
    }
    .sum-h { font-size: 0.72rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .sum-big { font-size: 1.6rem; font-weight: 750; margin-top: 0.2rem; }
    .sum-small { font-size: 0.8rem; color: var(--muted); }
    .sum-chips { margin-top: 0.45rem; display: flex; gap: 0.35rem; flex-wrap: wrap; }
    .tile-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0.7rem; margin-bottom: 1rem; }
    .tile {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 0.8rem 0.9rem;
        box-shadow: var(--shadow);
    }
    .tile-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; }
    .tile-name { font-weight: 700; font-size: 0.95rem; line-height: 1.25; }
    .tile-sym { font-size: 0.75rem; color: var(--muted); margin-top: 0.1rem; }
    .tile-price { font-weight: 700; font-size: 1rem; white-space: nowrap; }
    .tile-row { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-top: 0.5rem; }
    .tile-ret { font-size: 0.78rem; color: var(--muted); margin-top: 0.5rem; }

    /* Chips keep their own light colours so they read in either theme */
    .chip-bull, .chip-bear, .chip-ob, .chip-os, .chip-mid, .chip-na {
        display: inline-block;
        border-radius: 999px;
        padding: 0.12rem 0.5rem;
        font-size: 0.72rem;
        font-weight: 650;
        white-space: nowrap;
    }
    .chip-bull { background: #dcfce7; color: #14532d; }
    .chip-bear { background: #fee2e2; color: #7f1d1d; }
    .chip-ob { background: #ffedd5; color: #7c2d12; }
    .chip-os { background: #dbeafe; color: #1e3a8a; }
    .chip-mid { background: var(--surface); color: var(--muted); }
    .chip-na { background: transparent; color: var(--muted); border: 1px dashed var(--line); }
</style>
""", unsafe_allow_html=True)

# ── Persistent Watchlist Storage ────────────────────────────────────────────
WATCHLIST_FILE = Path(__file__).parent / "watchlist.json"

def load_saved_watchlist():
    if WATCHLIST_FILE.exists():
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    cleaned = [str(x).upper().strip() for x in data if str(x).strip()]
                    if cleaned:
                        return cleaned
        except Exception:
            pass
    # Default starter stock if no file or empty
    defaults = ["RKLB"]
    save_watchlist(defaults)
    return defaults

def save_watchlist(tickers):
    try:
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(list(dict.fromkeys(tickers)), f, indent=2)
    except Exception:
        pass

GLOSSARY = {
    "Framework score": "Sum of pillar points out of the maximum available. 70%+ is strong, 45–70% mixed, below 45% weak.",
    "ROIC": "Return on invested capital: after-tax operating profit ÷ (debt + equity). How well the business turns capital into profit.",
    "ROE": "Return on equity: net income ÷ shareholders' equity. Used for Capital Allocation only when ROIC can't be computed; distorted when equity is tiny or negative.",
    "Operating margin": "Operating income ÷ revenue. Above 15% earns a Quality point.",
    "Gross margin": "(Revenue − cost of sales) ÷ revenue. Above 40% signals pricing power.",
    "P/E": "Price ÷ earnings per share. Meaningless for loss-makers, so it is suppressed for them.",
    "PEG": "P/E ÷ earnings growth rate. Below 1.5 is attractive (Peter Lynch's rule of thumb).",
    "P/S": "Market cap ÷ revenue. Used when EV/Sales isn't available.",
    "P/B": "Price ÷ book value per share. Shown for reference; not scored.",
    "EV/Sales": "Enterprise value (market cap + debt − cash) ÷ revenue. The main multiple for pre-profit companies.",
    "EV/EBITDA": "Enterprise value ÷ EBITDA (earnings before interest, tax, depreciation and amortization). Below 12× earns a point.",
    "FCF yield": "Free cash flow ÷ market cap. Above 8% is strong.",
    "Cash runway": "Cash ÷ monthly cash burn: months the company can operate before needing new funding. 18+ months earns a point for loss-makers.",
    "Net cash % of market cap": "(Cash − debt) ÷ market cap. Above 30% gives a downside cushion.",
    "Rule of 40": "Revenue growth % + operating margin %. 40+ is the SaaS benchmark for an elite business.",
    "EV/Gross profit": "Enterprise value ÷ gross profit. Price relative to the margin the business earns on sales.",
    "Debt/Equity": "Total debt ÷ shareholders' equity, shown as a ratio. Below 0.5× earns 2 Risk points.",
    "Cash conversion": "Free cash flow ÷ net income. 80%+ means reported profit turns into cash.",
    "Dilution": "Change in shares outstanding over 3 years. A rising share count dilutes each holder's stake.",
    "Short interest": "Share of the float sold short. Above 20% costs one Risk point.",
    "Insider ownership": "Share of stock held by company insiders. Above 10% signals strong alignment.",
    "Smart money": "Insider open-market buys and sales over 12 months, plus whether top institutional holders added or trimmed shares in the latest quarter.",
    "Scenario model": "Projects revenue, EBITDA and exit value in N years, subtracts cash burn and shares issued to fund it, then discounts back at your required return.",
    "Reverse DCF": "Finds the revenue growth rate that makes the scenario model equal today's price.",
    "Peer regression": "Fits EV/Sales against revenue growth for peer companies, then reads off the multiple this company's growth would earn.",
    "R²": "Share of the variation in peer multiples that growth explains. Closer to 1 is a tighter fit; below 0.3 is weak.",
    "Discount rate": "Required annual return used to bring future value back to today. Higher means more conservative.",
    "Trend filter 50/200": "Bullish when the 50-day average is above the 200-day average. Backtest on 21 stocks: it cut the worst drawdown in 90% of them, but its risk-adjusted return was about the same as buy-and-hold. Use it to manage risk, not as a buy signal.",
}

SCORING_GUIDE = """
**Quality (3)**: operating margin above 15% (1); gross margin above 40% (1); gross margin expanding more than 2 points (1).

**Capital Allocation (3)**: ROIC above 15% (2) or above 8% (1); ROIC of 10%+ while revenue grows above 10% (1).

**Management (3)**: insider ownership above 20% (3), above 10% (2), above 3% (1).

**Growth (4)**: revenue growth above 20% (2) or above 10% (1); earnings growth above 15% (1), or revenue growth above 40% when earnings growth is missing; at least 75% of recent quarters up on the quarter before (1).

**Valuation (3)**. Profitable companies: PEG between 0 and 1.5 (2) or below 2.5 (1); EV/Sales below 3× (1); EV/EBITDA between 0 and 12× (1); FCF yield above 8% (1). Loss-makers: EV/Sales against a "fair" multiple of growth ÷ 10 (2 if below 0.7× fair, 1 if below 1.3×); cash runway of 18+ months (1); net cash above 30% of market cap (1).

**Risk (3)**: debt/equity below 0.5× (2) or below 1.5× (1); net cash positive (1); short interest above 20% of float (−1).

**Dilution (2)**: share count up 5% or less over 3 years (2); up 25% or less (1).

**Cash Quality (2)**: positive free cash flow (1); free cash flow at least 80% of net income (1, profitable companies only).

**Smart Money (2)**: net insider buying over 12 months (1); more top-10 institutional holders adding shares than trimming in the latest quarter (1).

Missing data removes that point from the total instead of counting as zero, so the denominator can be below the maximum.

**Verdict bands**: 70%+ strong alignment, 45–70% mixed signals, below 45% weak alignment. Pillar colours: 75%+ of its points ✅, 50–75% ⚠️, below 50% ❌.
"""

def close_ticker(symbol):
    if symbol in st.session_state.watchlist:
        st.session_state.watchlist.remove(symbol)
        save_watchlist(st.session_state.watchlist)


# ── Session state init ──────────────────────────────────────────────────────
if "watchlist" not in st.session_state:
    st.session_state.watchlist = load_saved_watchlist()

# ── Helpers ─────────────────────────────────────────────────────────────────

def safe_get(d, key, default=None):
    return d.get(key, default) if d else default


def format_number(n, is_pct=False, is_currency=False):
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "N/A"
    if is_pct:
        return f"{n*100:.1f}%" if abs(n) < 10 else f"{n:.1f}%"
    if is_currency:
        if abs(n) >= 1e9:
            return f"${n/1e9:.2f}B"
        if abs(n) >= 1e6:
            return f"${n/1e6:.1f}M"
        return f"${n:,.0f}"
    return f"{n:,.2f}" if isinstance(n, (int, float)) else str(n)


@st.cache_data(ttl=3600)
def get_stock_data(symbol):
    """Fetches and returns only pickle-serializable data (DataFrames as JSON strings)."""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        if not info or info.get("quoteType") is None:
            return None

        def df_to_json(df):
            try:
                return df.to_json() if df is not None and not df.empty else None
            except Exception:
                return None

        # Fetch annual & quarterly statements safely
        def safe_attr(attr):
            try:
                val = getattr(stock, attr, None)
                return df_to_json(val)
            except Exception:
                return None

        return {
            "info": dict(info),
            "financials": safe_attr("financials"),
            "balance": safe_attr("balance_sheet"),
            "cashflow": safe_attr("cashflow"),
            "quarterly_financials": safe_attr("quarterly_income_stmt"),
            "quarterly_balance": safe_attr("quarterly_balance_sheet"),
            "quarterly_cashflow": safe_attr("quarterly_cashflow"),
        }
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_shares_history(symbol):
    try:
        s = yf.Ticker(symbol).get_shares_full(start="2020-01-01")
        return s.dropna().sort_index() if s is not None and not s.empty else None
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_flow_data(symbol):
    """Insider open-market trades (trailing 12 months) and top-holder share changes, as plain data."""
    out = {"ins_ok": False, "inst_ok": False, "buy_n": 0, "sell_n": 0, "buy_val": 0.0, "sell_val": 0.0,
           "trades": [], "inst_up": 0, "inst_down": 0, "holders": []}
    try:
        t = yf.Ticker(symbol)
    except Exception:
        return out

    try:
        tx = t.insider_transactions
        if tx is not None:
            tx = tx.copy()
            out["ins_ok"] = True
            dates = pd.to_datetime(tx["Start Date"], errors="coerce")
            if getattr(dates.dt, "tz", None) is not None:
                dates = dates.dt.tz_localize(None)
            tx["Start Date"] = dates
            tx = tx[tx["Start Date"] >= pd.Timestamp.now().normalize() - pd.DateOffset(months=12)]
            txt = (tx.get("Transaction", pd.Series("", index=tx.index)).fillna("").astype(str) + " "
                   + tx.get("Text", pd.Series("", index=tx.index)).fillna("").astype(str)).str.lower()
            is_tax = txt.str.contains("to cover|withh", regex=True)
            is_buy = txt.str.contains("purchase|buy", regex=True) & ~is_tax
            is_sell = txt.str.contains("sale|sell", regex=True) & ~is_tax & ~is_buy
            value = pd.to_numeric(tx.get("Value"), errors="coerce").fillna(0).abs()
            out["buy_n"], out["sell_n"] = int(is_buy.sum()), int(is_sell.sum())
            out["buy_val"], out["sell_val"] = float(value[is_buy].sum()), float(value[is_sell].sum())
            shown = tx[is_buy | is_sell].sort_values("Start Date", ascending=False).head(50)
            out["trades"] = [
                {
                    "Date": r["Start Date"].strftime("%Y-%m-%d"),
                    "Insider": str(r.get("Insider", "")),
                    "Position": str(r.get("Position", "")),
                    "Type": "Buy" if is_buy.loc[i] else "Sale",
                    "Shares": float(pd.to_numeric(r.get("Shares"), errors="coerce")) if pd.notnull(r.get("Shares")) else 0.0,
                    "Value": float(pd.to_numeric(r.get("Value"), errors="coerce")) if pd.notnull(r.get("Value")) else 0.0,
                }
                for i, r in shown.iterrows()
            ]
    except Exception:
        out["ins_ok"] = False

    try:
        h = t.institutional_holders
        if h is not None and not h.empty:
            out["inst_ok"] = True
            pc = pd.to_numeric(h["pctChange"], errors="coerce").dropna()
            out["inst_up"], out["inst_down"] = int((pc > 0).sum()), int((pc < 0).sum())
            out["holders"] = [
                {
                    "Holder": str(r["Holder"]),
                    "Reported": pd.Timestamp(r["Date Reported"]).strftime("%Y-%m-%d") if pd.notnull(r["Date Reported"]) else "",
                    "% Held": float(r["pctHeld"]) * 100 if pd.notnull(r["pctHeld"]) else None,
                    "Change in shares": float(r["pctChange"]) * 100 if pd.notnull(r["pctChange"]) else None,
                }
                for _, r in h.iterrows()
            ]
    except Exception:
        out["inst_ok"] = False

    return out


def parse_stock_data(raw):
    """Reconstruct DataFrames from cached JSON strings."""
    if raw is None:
        return None, None, None, None, None, None, None

    def json_to_df(j):
        try:
            return pd.read_json(StringIO(j)) if j else None
        except Exception:
            return None

    return (
        raw.get("info"),
        json_to_df(raw.get("financials")),
        json_to_df(raw.get("balance")),
        json_to_df(raw.get("cashflow")),
        json_to_df(raw.get("quarterly_financials")),
        json_to_df(raw.get("quarterly_balance")),
        json_to_df(raw.get("quarterly_cashflow")),
    )


PILLARS = ["Quality", "Capital Allocation", "Management", "Growth", "Valuation", "Risk", "Dilution", "Cash Quality", "Smart Money"]
# Returns on capital, growth and ownership carry the most weight (Fisher/Cassel/Mayer); valuation is a discipline check
PILLAR_MAX = {
    "Quality": 3, "Capital Allocation": 3, "Management": 3, "Growth": 4, "Valuation": 3,
    "Risk": 3, "Dilution": 2, "Cash Quality": 2, "Smart Money": 2,
}


def compute_roic(financials, balance, tax_default=0.21):
    """Latest annual ROIC = NOPAT / (debt + equity). None if statements are unusable."""
    try:
        if financials is None or balance is None or financials.empty or balance.empty:
            return None
        f = financials[sorted(financials.columns)[-1]]
        b = balance[sorted(balance.columns)[-1]]

        def val(series, *names):
            for n in names:
                if n in series.index and pd.notnull(series[n]):
                    return float(series[n])
            return None

        ebit = val(f, "Operating Income", "EBIT")
        if ebit is None:
            return None
        tax_rate = tax_default
        pretax, tax = val(f, "Pretax Income"), val(f, "Tax Provision")
        if pretax and tax is not None and pretax > 0 and 0 <= tax / pretax <= 0.35:
            tax_rate = tax / pretax
        nopat = ebit * (1 - tax_rate) if ebit > 0 else ebit

        invested = val(b, "Invested Capital")
        if invested is None:
            equity = val(b, "Stockholders Equity", "Total Equity Gross Minority Interest")
            if equity is None:
                return None
            invested = equity + (val(b, "Total Debt") or 0)
        return nopat / invested if invested > 0 else None
    except Exception:
        return None


def compute_quarterly_metrics(q_financials):
    """Quarterly revenue consistency and gross-margin change, from the last quarters yfinance provides."""
    out = {"qoq_pos": 0, "qoq_n": 0, "gm_first": None, "gm_last": None}
    try:
        if q_financials is None or q_financials.empty:
            return out
        cols = sorted(q_financials.columns)
        rev_row = next((r for r in ["Total Revenue", "Operating Revenue"] if r in q_financials.index), None)
        if rev_row is None:
            return out
        rev = pd.to_numeric(q_financials.loc[rev_row, cols], errors="coerce")
        qoq = rev.pct_change(fill_method=None).dropna()
        out["qoq_pos"], out["qoq_n"] = int((qoq > 0).sum()), int(len(qoq))
        if "Gross Profit" in q_financials.index:
            gm = (pd.to_numeric(q_financials.loc["Gross Profit", cols], errors="coerce") / rev * 100).dropna()
            if len(gm) >= 2:
                out["gm_first"], out["gm_last"] = float(gm.iloc[0]), float(gm.iloc[-1])
    except Exception:
        pass
    return out


def compute_scores(info, runway_months=None, dilution_pct=None, roic=None, flow=None, qm=None):
    """Score a stock on every pillar. Returns (scores, explanations, maxes); maxes shrink when data is missing."""
    scores, explanations = {}, {}
    maxes = dict(PILLAR_MAX)
    qm = qm or {}

    def sg(key, default=None):
        return safe_get(info, key, default)

    roe        = sg("returnOnEquity")
    op_margin  = sg("operatingMargins")
    gross_margin = sg("grossMargins")
    insider_pct= sg("heldPercentInsiders")
    rev_growth = sg("revenueGrowth")
    earn_growth= sg("earningsGrowth")
    peg        = sg("pegRatio")
    ps         = sg("priceToSalesTrailing12Months")
    de_ratio   = sg("debtToEquity")
    total_cash = sg("totalCash")
    total_debt = sg("totalDebt")

    # 1. Quality — margins and whether gross margin is expanding
    q, qn = 0, []
    if op_margin and op_margin > 0.15: q += 1; qn.append("Strong op margin")
    elif op_margin and op_margin > 0:         qn.append("Positive op margin")
    if gross_margin and gross_margin > 0.40: q += 1; qn.append(f"Pricing power (gross margin {gross_margin*100:.0f}%)")
    if qm.get("gm_first") is not None:
        gm_diff = qm["gm_last"] - qm["gm_first"]
        if gm_diff > 2:    q += 1; qn.append(f"Gross margin expanding ({qm['gm_first']:.0f}% → {qm['gm_last']:.0f}%)")
        elif gm_diff < -2:         qn.append(f"Gross margin contracting ({qm['gm_first']:.0f}% → {qm['gm_last']:.0f}%)")
        else:                      qn.append("Gross margin stable")
    else:
        maxes["Quality"] -= 1
    scores["Quality"] = min(q, PILLAR_MAX["Quality"])
    explanations["Quality"] = "; ".join(qn) or "Limited data"

    # 1b. Capital Allocation — return on capital, and whether growth is being reinvested at high returns
    ca, can = 0, []
    # ROIC is preferred: ROE is distorted by tiny or negative equity, common in micro-caps
    ret, ret_name = (roic, "ROIC") if roic is not None else (roe, "ROE (ROIC n/a)")
    if ret is None:
        maxes["Capital Allocation"] = 0
        can.append("Return on capital unavailable — excluded from score")
    else:
        if ret > 0.15:   ca += 2; can.append(f"High {ret_name} ({ret*100:.0f}%)")
        elif ret > 0.08: ca += 1; can.append(f"Moderate {ret_name} ({ret*100:.0f}%)")
        else:                     can.append(f"Low/negative {ret_name} ({ret*100:.0f}%)")
        if ret >= 0.10 and rev_growth and rev_growth > 0.10:
            ca += 1; can.append("Reinvesting at high returns (return ≥10% while growing)")
    scores["Capital Allocation"] = min(ca, PILLAR_MAX["Capital Allocation"])
    explanations["Capital Allocation"] = "; ".join(can)

    # 2. Management — missing insider data is excluded from the score, not counted as zero
    m, mn = 0, []
    if insider_pct is None:
        maxes["Management"] = 0
        mn.append("Insider data unavailable — excluded from score")
    elif insider_pct > 0.20: m += 3; mn.append(f"Very high insider ownership ({insider_pct*100:.1f}%)")
    elif insider_pct > 0.10: m += 2; mn.append(f"Strong insider ownership ({insider_pct*100:.1f}%)")
    elif insider_pct > 0.03: m += 1; mn.append(f"Moderate insider ownership ({insider_pct*100:.1f}%)")
    else:                           mn.append(f"Low insider ownership ({insider_pct*100:.1f}%)")
    scores["Management"] = min(m, PILLAR_MAX["Management"])
    explanations["Management"] = "; ".join(mn)

    # 3. Growth
    g, gn = 0, []
    if rev_growth and rev_growth > 0.20:   g += 2; gn.append(f"Strong rev growth ({rev_growth*100:.0f}%)")
    elif rev_growth and rev_growth > 0.10: g += 1; gn.append(f"Moderate rev growth ({rev_growth*100:.0f}%)")
    else:                                         gn.append("Slow/negative rev growth")
    if earn_growth and earn_growth > 0.15: g += 1; gn.append("Positive earnings growth")
    elif earn_growth is None and rev_growth and rev_growth > 0.40:
        g += 1; gn.append("Hyper-growth (>40% revenue) stands in for earnings growth")
    if qm.get("qoq_n", 0) >= 4:
        if qm["qoq_pos"] / qm["qoq_n"] >= 0.75:
            g += 1; gn.append(f"Consistent growth ({qm['qoq_pos']}/{qm['qoq_n']} quarters up QoQ)")
        else:
            gn.append(f"Lumpy revenue ({qm['qoq_pos']}/{qm['qoq_n']} quarters up QoQ)")
    else:
        maxes["Growth"] -= 1
    scores["Growth"] = min(g, PILLAR_MAX["Growth"])
    explanations["Growth"] = "; ".join(gn)

    # 4. Valuation — max 4 pts, logic branches on profitable vs loss-making
    v, vn = 0, []
    _ev_rev    = sg("enterpriseToRevenue")
    _ev_ebitda = sg("enterpriseToEbitda")
    _fcf_v     = sg("freeCashflow")
    _mcap_v    = sg("marketCap")
    _op_cf     = sg("operatingCashflow")
    _total_cash= sg("totalCash")
    _total_debt= sg("totalDebt")
    _eps       = sg("trailingEps")
    _prof_mg   = sg("profitMargins")
    has_earnings_data = _eps is not None or _prof_mg is not None
    is_loss_making = has_earnings_data and (_eps is None or _eps <= 0) and (_prof_mg is None or _prof_mg <= 0)

    if is_loss_making:
        # ── Loss-maker path ──────────────────────────────────────────────
        vn.append("⚠️ Loss-making — earnings multiples not applicable")

        # Primary: EV/Sales vs revenue growth (up to 2 pts)
        # Rule of thumb: fair EV/Sales ≈ rev_growth% ÷ 10
        if _ev_rev and _ev_rev > 0 and rev_growth and rev_growth > 0:
            fair_evr = max(1.0, (rev_growth * 100) / 10)
            ratio = _ev_rev / fair_evr
            if ratio < 0.7:   v += 2; vn.append(f"Attractive EV/Rev vs growth ({_ev_rev:.1f}x, fair ~{fair_evr:.1f}x)")
            elif ratio < 1.3: v += 1; vn.append(f"Reasonable EV/Rev vs growth ({_ev_rev:.1f}x, fair ~{fair_evr:.1f}x)")
            else:                      vn.append(f"Rich EV/Rev vs growth ({_ev_rev:.1f}x, fair ~{fair_evr:.1f}x)")
        elif ps and rev_growth and rev_growth > 0:
            fair_ps = max(1.0, (rev_growth * 100) / 10)
            ratio = ps / fair_ps
            if ratio < 0.7:   v += 2; vn.append(f"Attractive P/S vs growth ({ps:.1f}x, fair ~{fair_ps:.1f}x)")
            elif ratio < 1.3: v += 1; vn.append(f"Reasonable P/S vs growth ({ps:.1f}x, fair ~{fair_ps:.1f}x)")
            else:                      vn.append(f"Rich P/S vs growth ({ps:.1f}x, fair ~{fair_ps:.1f}x)")
        else:
            vn.append("Sales multiple vs growth: insufficient data")

        # Cash runway: 1 pt if ≥18 months
        runway_mo = runway_months
        if runway_mo is None:
            burn_cf = _fcf_v if _fcf_v is not None and _fcf_v < 0 else _op_cf
            if burn_cf and burn_cf < 0 and _total_cash:
                runway_mo = _total_cash / (abs(burn_cf) / 12)
        if runway_mo is not None:
            if runway_mo >= 18: v += 1; vn.append(f"Adequate runway ({runway_mo:.0f}mo)")
            elif runway_mo >= 9:        vn.append(f"Tight runway ({runway_mo:.0f}mo) ⚠️")
            else:                       vn.append(f"Dangerously short runway ({runway_mo:.0f}mo) 🚨")
        elif _total_cash:
            vn.append("Cash flow positive or unavailable — runway not calculated")

        # Net cash % of market cap: 1 pt if >25%
        if _total_cash and _mcap_v:
            _nc = (_total_cash or 0) - (_total_debt or 0)
            nc_pct = _nc / _mcap_v
            if nc_pct > 0.30:   v += 1; vn.append(f"Net cash {nc_pct*100:.0f}% of mktcap (downside cushion)")
            elif nc_pct > 0.10:         vn.append(f"Some net cash ({nc_pct*100:.0f}% of mktcap)")
            elif nc_pct <= 0:           vn.append("Net debt position")

    else:
        # ── Profitable company path ──────────────────────────────────────
        # PEG: up to 2 pts (Lynch/Mayer style)
        if peg and 0 < peg < 1.5:   v += 2; vn.append(f"Attractive PEG ({peg:.2f})")
        elif peg and 0 < peg < 2.5: v += 1; vn.append(f"Reasonable PEG ({peg:.2f})")
        elif peg and peg < 0:               vn.append(f"Negative PEG ({peg:.2f}) — earnings shrinking")
        elif peg:                           vn.append(f"High PEG ({peg:.2f})")
        else:                               vn.append("PEG unavailable")

        # Sales multiple: prefer EV/Revenue, fall back to P/S — 1 pt
        if _ev_rev and _ev_rev > 0:
            if _ev_rev < 3:   v += 1; vn.append(f"Low EV/Rev ({_ev_rev:.1f}x)")
            elif _ev_rev < 6:         vn.append(f"Moderate EV/Rev ({_ev_rev:.1f}x)")
            else:                     vn.append(f"High EV/Rev ({_ev_rev:.1f}x)")
        elif ps:
            if ps < 5:        v += 1; vn.append(f"Reasonable P/S ({ps:.1f}x)")
            elif ps < 10:             vn.append(f"Elevated P/S ({ps:.1f}x)")

        # EV/EBITDA: 1 pt if <12x
        if _ev_ebitda and 0 < _ev_ebitda < 12:
            v += 1; vn.append(f"Reasonable EV/EBITDA ({_ev_ebitda:.1f}x)")
        elif _ev_ebitda and _ev_ebitda >= 12:
            vn.append(f"Elevated EV/EBITDA ({_ev_ebitda:.1f}x)")

        # FCF Yield: 1 pt if >8%, noted if positive
        if _fcf_v and _mcap_v:
            _fcfy = _fcf_v / _mcap_v
            if _fcfy > 0.08:    v += 1; vn.append(f"Strong FCF yield ({_fcfy*100:.1f}%)")
            elif _fcfy > 0:             vn.append(f"Positive FCF yield ({_fcfy*100:.1f}%)")
            else:                       vn.append(f"Negative FCF yield ({_fcfy*100:.1f}%)")

    scores["Valuation"] = min(v, PILLAR_MAX["Valuation"])
    explanations["Valuation"] = "; ".join(vn) or "Limited valuation data"

    # 5. Risk
    r, rn = 0, []
    # yfinance reports debtToEquity as a percentage (84.3 = 0.84x)
    if de_ratio is not None:
        de_x = de_ratio / 100
    elif total_debt == 0:
        de_x = 0.0
    else:
        de_x = None
    if de_x is not None:
        if de_x < 0.5:   r += 2; rn.append(f"Low debt ({de_x:.2f}x D/E)")
        elif de_x < 1.5: r += 1; rn.append(f"Moderate debt ({de_x:.2f}x D/E)")
        else:                    rn.append(f"High debt ({de_x:.2f}x D/E)")
    else:
        rn.append("Debt data unavailable")
    if total_cash and (total_cash - (total_debt or 0)) > 0:
        r += 1; rn.append("Net cash positive")
    short_pct = sg("shortPercentOfFloat")
    if short_pct is not None and short_pct > 0.20:
        r -= 1; rn.append(f"High short interest ({short_pct*100:.0f}% of float)")
    scores["Risk"] = max(0, min(r, PILLAR_MAX["Risk"]))
    explanations["Risk"] = "; ".join(rn)

    # Dilution — 3-year change in share count
    dl, dln = 0, []
    if dilution_pct is None:
        maxes["Dilution"] = 0
        dln.append("Share count history unavailable — excluded from score")
    elif dilution_pct <= 5:  dl += 2; dln.append(f"Disciplined share count ({dilution_pct:+.0f}% over 3y)")
    elif dilution_pct <= 25: dl += 1; dln.append(f"Moderate dilution ({dilution_pct:+.0f}% over 3y)")
    else:                             dln.append(f"Heavy dilution ({dilution_pct:+.0f}% over 3y)")
    scores["Dilution"] = min(dl, PILLAR_MAX["Dilution"])
    explanations["Dilution"] = "; ".join(dln)

    # Cash Quality — free cash flow sign, and how much net income it converts to
    cq, cqn = 0, []
    fcf_c = sg("freeCashflow")
    ni_c = sg("netIncomeToCommon")
    if fcf_c is None:
        maxes["Cash Quality"] -= 2
    else:
        if fcf_c > 0: cq += 1; cqn.append("Positive free cash flow")
        else:                  cqn.append("Negative free cash flow")
        if ni_c is None or ni_c <= 0:
            maxes["Cash Quality"] -= 1
            if ni_c is not None: cqn.append("Loss-making — cash conversion not meaningful")
        else:
            conv = fcf_c / ni_c
            if conv >= 0.8: cq += 1; cqn.append(f"Strong cash conversion (FCF {conv*100:.0f}% of net income)")
            else:                    cqn.append(f"Weak cash conversion (FCF {conv*100:.0f}% of net income)")
    scores["Cash Quality"] = min(cq, PILLAR_MAX["Cash Quality"])
    explanations["Cash Quality"] = "; ".join(cqn) if maxes["Cash Quality"] else "Cash flow data unavailable — excluded from score"

    # 6. Smart Money — 1 pt for net insider buying (12m), 1 pt for top holders adding shares (latest quarter)
    flow = flow or {}
    sm, smn = 0, []
    if flow.get("ins_ok"):
        bv, sv, bn, sn = flow["buy_val"], flow["sell_val"], flow["buy_n"], flow["sell_n"]
        net_buying = (bv > sv) if (bv + sv) > 0 else (bn > sn)
        if bn and net_buying:
            sm += 1; smn.append(f"Net insider buying ({bn} buys, {sn} sales, 12m)")
        elif bn or sn:
            smn.append(f"Net insider selling ({bn} buys, {sn} sales, 12m)")
        else:
            smn.append("No open-market insider trades (12m)")
    else:
        maxes["Smart Money"] -= 1
    if flow.get("inst_ok") and (flow["inst_up"] + flow["inst_down"]) > 0:
        if flow["inst_up"] > flow["inst_down"]:
            sm += 1; smn.append(f"Top holders adding ({flow['inst_up']} up / {flow['inst_down']} down)")
        else:
            smn.append(f"Top holders trimming ({flow['inst_up']} up / {flow['inst_down']} down)")
    elif not flow.get("inst_ok"):
        maxes["Smart Money"] -= 1
    if maxes["Smart Money"] == 0:
        smn = ["Insider and holder flow data unavailable — excluded from score"]
    scores["Smart Money"] = min(sm, PILLAR_MAX["Smart Money"])
    explanations["Smart Money"] = "; ".join(smn)

    return scores, explanations, maxes


@st.cache_data(ttl=3600)
def get_trend_filter(symbol):
    """50-day vs 200-day average: Bullish when the 50-day is above the 200-day, with the date of the last change."""
    try:
        close = yf.Ticker(symbol).history(period="5y", auto_adjust=True)["Close"].dropna()
        sma50, sma200 = close.rolling(50).mean(), close.rolling(200).mean()
        cond = (sma50 > sma200).where(sma200.notna()).dropna().astype(bool)
        if cond.empty:
            return None
        flips = cond.index[cond.ne(cond.shift(1)) & cond.shift(1).notna()]
        since = flips[-1] if len(flips) else cond.index[0]
        return {"state": "Bullish" if cond.iloc[-1] else "Bearish", "since": since.strftime("%Y-%m-%d")}
    except Exception:
        return None


def build_report_parts(ticker, name, sector, price, mcap, scores, maxes, explanations, score_pct, is_loss_making, runway_months, dilution_pct, flow, trend=None):
    """Structured summary of the scoring, built from the same numbers shown on screen."""
    total, possible = sum(scores.values()), sum(maxes.values())
    gaps = [c for c in PILLARS if not maxes[c]]
    facts = [("Pillars scored", f"{len(PILLARS) - len(gaps)}/{len(PILLARS)}", None)]
    if trend:
        facts.append(("Trend 50/200", trend["state"], f"Since {trend['since']}"))
    if runway_months is not None:
        facts.append(("Cash runway", f"~{runway_months:.0f} mo", None))
    if dilution_pct is not None:
        facts.append(("Share change, 3y", f"{dilution_pct:+.0f}%", None))
    if flow.get("ins_ok"):
        facts.append(("Insider buys / sales, 12m", f"{flow['buy_n']} / {flow['sell_n']}", None))
    return {
        "ticker": ticker,
        "name": str(name),
        "sector": str(sector),
        "price": price,
        "market_cap": format_number(mcap, is_currency=True),
        "is_loss_making": is_loss_making,
        "total": total,
        "possible": possible,
        "score_pct": score_pct,
        "verdict": "Strong alignment" if score_pct >= 70 else "Mixed signals" if score_pct >= 45 else "Weak alignment",
        "strengths": [(c, scores[c], maxes[c], explanations[c]) for c in PILLARS if maxes[c] and scores[c] / maxes[c] >= 0.75],
        "concerns": [(c, scores[c], maxes[c], explanations[c]) for c in PILLARS if maxes[c] and scores[c] / maxes[c] < 0.5],
        "gaps": gaps,
        "facts": facts,
    }


def report_markdown(p):
    lines = [
        f"# {p['name']} ({p['ticker']}) — Framework Report",
        f"*Quantitative screen as of {datetime.now():%Y-%m-%d}. Not investment advice.*",
        "",
        f"**{p['verdict']}:** {p['total']}/{p['possible']} points ({p['score_pct']:.0f}%).",
        f"{p['sector']} · Market cap {p['market_cap']}" + (f" · Price ${p['price']:.2f}" if p["price"] else ""),
    ]
    if p["is_loss_making"]:
        lines.append("Loss-making: valuation relies on EV/sales vs growth and cash runway, not earnings multiples.")
    lines.append("")
    if p["strengths"]:
        lines.append("**Strengths**")
        lines += [f"- **{c}** {s}/{m}: {e}" for c, s, m, e in p["strengths"]]
        lines.append("")
    if p["concerns"]:
        lines.append("**Concerns**")
        lines += [f"- **{c}** {s}/{m}: {e}" for c, s, m, e in p["concerns"]]
        lines.append("")
    lines.append("**Key facts:** " + "; ".join(f"{k}: {v}" for k, v, _ in p["facts"] if k != "Pillars scored") + ".")
    lines.append("")
    if p["gaps"]:
        lines.append(f"**Not scored (missing data):** {', '.join(p['gaps'])}.")
        lines.append("")
    lines.append("**Before acting:** read the latest 10-K and 10-Q, test the concerns above against the filings, and check why insiders are buying or selling.")
    return "\n".join(lines)


def md_safe(text):
    return str(text).replace("$", "\\$")


def render_report(p):
    color = {"Strong alignment": "#2e7d32", "Mixed signals": "#b26a00", "Weak alignment": "#c62828"}[p["verdict"]]
    st.markdown(
        f'<div class="rpt-head">'
        f'<div><span class="rpt-badge" style="background:{color}">{html.escape(p["verdict"])}</span>'
        f'<div class="rpt-sub">{html.escape(p["name"])} · {html.escape(p["sector"])}</div></div>'
        f'<div class="rpt-score">{p["total"]}<span> / {p["possible"]} pts · {p["score_pct"]:.0f}%</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.progress(min(p["score_pct"] / 100, 1.0))
    subtitle = f"Market cap {p['market_cap']}" + (f" · Price ${p['price']:.2f}" if p["price"] else "")
    st.caption(md_safe(subtitle) + (" · Loss-making: valuation uses EV/sales vs growth and cash runway" if p["is_loss_making"] else ""))

    cards = "".join(
        f'<div class="fact"><div class="fact-label">{html.escape(label)}</div>'
        f'<div class="fact-value">{html.escape(value)}</div>'
        + (f'<div class="fact-note">{html.escape(note)}</div>' if note else "")
        + '</div>'
        for label, value, note in p["facts"]
    )
    st.markdown(f'<div class="fact-row">{cards}</div>', unsafe_allow_html=True)
    st.caption(
        "**Trend 50/200:** Bullish when the 50-day average is above the 200-day average, Bearish when below. "
        "It is a risk filter, not a buy signal: in a 21-stock backtest it reduced the worst drawdown in 19 cases, "
        "but its risk-adjusted return matched buy-and-hold."
    )

    left, right = st.columns(2)
    with left:
        st.markdown("**Strengths**")
        if not p["strengths"]:
            st.caption("No pillar reached 75% of its points.")
        for c, s, m, e in p["strengths"]:
            st.markdown(f"✅ **{c}** · {s}/{m}")
            st.caption(md_safe(e))
    with right:
        st.markdown("**Concerns**")
        if not p["concerns"]:
            st.caption("No pillar fell below 50% of its points.")
        for c, s, m, e in p["concerns"]:
            icon = "⚠️" if s / m >= 0.25 else "❌"
            st.markdown(f"{icon} **{c}** · {s}/{m}")
            st.caption(md_safe(e))

    if p["gaps"]:
        st.caption(f"Not scored (missing data): {', '.join(p['gaps'])}.")
    st.caption("Before acting: read the latest 10-K and 10-Q, test the concerns above against the filings, and check why insiders are buying or selling.")


@st.cache_data(ttl=3600)
def get_peer_multiple(symbol):
    try:
        info = yf.Ticker(symbol).info
        ev_rev, growth = info.get("enterpriseToRevenue"), info.get("revenueGrowth")
        if not ev_rev or ev_rev <= 0 or growth is None:
            return None
        return {"Ticker": symbol, "Name": str(info.get("shortName") or symbol),
                "growth": float(growth), "ev_rev": float(ev_rev)}
    except Exception:
        return None


def scenario_fair_value(revenue, cash, debt, shares, price, burn_annual, growth_pct, years,
                        margin_pct, exit_mult, other_dil_pct, hurdle):
    """Per-share value in `years`: exit EV on EBITDA plus leftover cash less debt, discounted, diluted."""
    if not revenue or not shares:
        return None
    cash, debt = cash or 0, debt or 0
    ev = exit_mult * revenue * (1 + growth_pct / 100) ** years * (margin_pct / 100)
    cum_burn = burn_annual * years / 2
    gap = max(0.0, cum_burn - cash)
    new_shares = gap / price if price else 0.0
    equity = ev + (cash - cum_burn + gap) - debt
    pv = equity / (1 + hurdle) ** years * (1 - other_dil_pct / 100)
    return pv / (shares + new_shares) if pv > 0 else None


def implied_growth(price, revenue, cash, debt, shares, burn_annual, years, margin_pct, exit_mult, other_dil_pct, hurdle):
    """Annual revenue growth (%) at which the scenario model equals the current price, or None if out of range."""
    def fair(g):
        v = scenario_fair_value(revenue, cash, debt, shares, price, burn_annual, g, years,
                                margin_pct, exit_mult, other_dil_pct, hurdle)
        return v if v is not None else 0.0
    lo, hi = -50.0, 300.0
    if fair(lo) > price or fair(hi) < price:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if fair(mid) < price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ── Per-stock analysis renderer ─────────────────────────────────────────────

def show_stock_tab(ticker_sym):
    """Render the full analysis UI for a single ticker inside a tab."""
    with st.spinner(f"Loading {ticker_sym}…"):
        raw = get_stock_data(ticker_sym)

    if raw is None:
        st.error(f"Could not load data for **{ticker_sym}**. Check the symbol and try again.")
        return

    info, financials, balance, cashflow, q_financials, q_balance, q_cashflow = parse_stock_data(raw)
    stock = yf.Ticker(ticker_sym)   # keep outside cache (unpicklable)

    if q_financials is None:
        try:
            q_financials = stock.quarterly_income_stmt
        except Exception:
            q_financials = None
    if q_cashflow is None:
        try:
            q_cashflow = stock.quarterly_cashflow
        except Exception:
            q_cashflow = None
    if q_balance is None:
        try:
            q_balance = stock.quarterly_balance_sheet
        except Exception:
            q_balance = None

    sg = lambda key, default=None: safe_get(info, key, default)

    mcap         = sg("marketCap")
    price        = sg("currentPrice") or sg("regularMarketPrice")
    name         = sg("shortName") or sg("longName") or ticker_sym
    sector       = sg("sector", "N/A")
    industry     = sg("industry", "N/A")
    pe           = sg("trailingPE")
    forward_pe   = sg("forwardPE")
    peg          = sg("pegRatio")
    ps           = sg("priceToSalesTrailing12Months")
    pb           = sg("priceToBook")
    ev_ebitda    = sg("enterpriseToEbitda")
    ev_rev       = sg("enterpriseToRevenue")
    roe          = sg("returnOnEquity")
    roa          = sg("returnOnAssets")
    profit_margin= sg("profitMargins")
    op_margin    = sg("operatingMargins")
    gross_margin = sg("grossMargins")
    rev_growth   = sg("revenueGrowth")
    earn_growth  = sg("earningsGrowth")
    de_ratio     = sg("debtToEquity")
    current_ratio= sg("currentRatio")
    quick_ratio  = sg("quickRatio")
    insider_pct  = sg("heldPercentInsiders")
    inst_pct     = sg("heldPercentInstitutions")
    shares_out   = sg("sharesOutstanding")
    float_shares = sg("floatShares")
    fcf           = sg("freeCashflow")
    total_cash    = sg("totalCash")
    total_debt    = sg("totalDebt")
    op_cashflow   = sg("operatingCashflow")
    gross_profit  = sg("grossProfits")
    enterprise_val= sg("enterpriseValue")
    eps_trailing  = sg("trailingEps")
    eps_forward   = sg("forwardEps")
    revenue       = sg("totalRevenue")
    ebitda_val    = sg("ebitda")
    # Derived
    net_debt      = (total_debt or 0) - (total_cash or 0)
    is_loss_making= (eps_trailing is not None or profit_margin is not None) and (eps_trailing is None or eps_trailing <= 0) and (profit_margin is None or profit_margin <= 0)
    fcf_yield     = (fcf / mcap) if fcf and mcap else None
    # Cash runway: burn = trailing-quarter free cash flow (includes capex), else operating cash flow
    runway_months = None
    if q_cashflow is not None and not q_cashflow.empty:
        burn_row = next((r for r in ["Free Cash Flow", "Operating Cash Flow"] if r in q_cashflow.index), None)
        if burn_row:
            recent_cf = q_cashflow.loc[burn_row].dropna().iloc[:4]
            if not recent_cf.empty:
                ttm_cf_val = float(recent_cf.sum())
                if ttm_cf_val < 0 and total_cash:
                    runway_months = total_cash / (abs(ttm_cf_val) / (len(recent_cf) * 3))
    if runway_months is None:
        burn_cf = fcf if fcf is not None and fcf < 0 else op_cashflow
        if burn_cf and burn_cf < 0 and total_cash:
            runway_months = total_cash / (abs(burn_cf) / 12)

    # Share-count change over ~3 years (cached; also feeds the dilution chart)
    shares_hist = get_shares_history(ticker_sym)
    dilution_pct = None
    if shares_hist is not None and len(shares_hist) >= 2:
        s3 = shares_hist[shares_hist.index >= shares_hist.index[-1] - pd.DateOffset(years=3)]
        if len(s3) >= 2 and float(s3.iloc[0]) > 0:
            dilution_pct = (float(s3.iloc[-1]) / float(s3.iloc[0]) - 1) * 100
    # Net cash % of market cap
    net_cash_pct  = ((total_cash or 0) - (total_debt or 0)) / mcap if mcap else None
    # EV / Gross Profit
    ev_gross_profit = (enterprise_val / gross_profit) if enterprise_val and gross_profit and gross_profit > 0 else None
    # Rule of 40 (growth % + op margin %)
    rule_of_40    = ((rev_growth or 0) * 100) + ((op_margin or 0) * 100) if rev_growth is not None or op_margin is not None else None

    # Size label
    size_label = "Unknown"
    if mcap:
        if mcap < 300_000_000:      size_label = "Micro-cap (<$300M)"
        elif mcap < 2_000_000_000:  size_label = "Small-cap ($300M–$2B)"
        elif mcap < 10_000_000_000: size_label = "Mid-cap"
        else:                       size_label = "Large/Mega-cap"

    roic = compute_roic(financials, balance)
    flow = get_flow_data(ticker_sym)
    qm = compute_quarterly_metrics(q_financials)
    scores, explanations, maxes = compute_scores(info, runway_months, dilution_pct, roic, flow, qm)
    total_possible = sum(maxes.values())
    total_score = sum(scores.values())
    score_pct = (total_score / total_possible) * 100 if total_possible else 0
    pillar_pct = {c: (scores[c] / maxes[c] * 100 if maxes[c] else None) for c in PILLARS}

    top_l, top_r = st.columns([5, 1], vertical_alignment="center")
    top_l.caption(f"Analysis of {ticker_sym}. Closing a tab removes it from your watchlist (re-add it any time).")
    top_r.button("✕ Close", key=f"close_{ticker_sym}", help=f"Close {ticker_sym} and remove it from the watchlist",
                 on_click=close_ticker, args=(ticker_sym,), use_container_width=True)

    score_tone = "Strong alignment" if score_pct >= 70 else "Mixed signals" if score_pct >= 45 else "Weak alignment"
    st.markdown(
        f'<div class="hero">'
        f'<span class="hero-ticker">{html.escape(ticker_sym)}</span>'
        f'<div class="hero-name">{html.escape(str(name))}</div>'
        f'<div class="hero-meta">{html.escape(str(sector))} • {html.escape(str(industry))} • {html.escape(size_label)}</div>'
        f'<div class="hero-pill">{total_score}/{total_possible} · {score_pct:.0f}% · {score_tone}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    report = build_report_parts(ticker_sym, name, sector, price, mcap, scores, maxes, explanations,
                                score_pct, is_loss_making, runway_months, dilution_pct, flow,
                                trend=get_trend_filter(ticker_sym))
    with st.container(border=True):
        st.markdown("#### 📝 Summary report")
        render_report(report)
        st.download_button(
            "⬇️ Download report (.md)",
            data=report_markdown(report),
            file_name=f"{ticker_sym}_framework_report.md",
            mime="text/markdown",
            key=f"report_{ticker_sym}",
        )

    # ── Header section ──
    header_col1, header_col2 = st.columns([2, 1])

    with header_col1:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏢 Company", name)
            st.caption(f"{sector} • {industry}")
        with col2:
            st.metric("💰 Market Cap", format_number(mcap, is_currency=True))
            st.caption(size_label)
        with col3:
            st.metric("💵 Price", f"${price:.2f}" if price else "N/A")

    with header_col2:
        # Score badge with color coding
        if score_pct >= 70:
            score_color = "🟢"
            score_label = "Strong"
        elif score_pct >= 45:
            score_color = "🟡"
            score_label = "Moderate"
        else:
            score_color = "🔴"
            score_label = "Weak"

        st.metric(f"{score_color} Framework Score", f"{total_score}/{total_possible}",
                  help=GLOSSARY["Framework score"])
        st.progress(score_pct / 100)
        st.caption(f"{score_pct:.0f}% alignment ({score_label})")

    st.markdown("---")

    # ── Framework Score Radar Chart ──
    st.subheader("📊 Multi-Factor Framework Score")
    radar_col1, radar_col2 = st.columns([2, 1])

    with radar_col1:
        # Create radar chart
        categories = PILLARS
        values = [pillar_pct[cat] or 0 for cat in categories]

        fig_radar = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Score',
            line=dict(color='#2962FF'),
            fillcolor='rgba(41, 98, 255, 0.3)'
        ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%")),
            showlegend=False,
            height=380,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with radar_col2:
        st.write("**Category Breakdown:**")
        for cat in categories:
            # Create visual bars for each score
            score_val = scores[cat]
            max_val = maxes[cat]
            pct = pillar_pct[cat]

            if pct is None:
                st.write(f"⚪ **{cat}**: N/A (no data, excluded)")
                continue
            color = "🟢" if pct >= 75 else "🟡" if pct >= 50 else "🔴"
            st.write(f"{color} **{cat}**: {score_val}/{max_val} ({pct:.0f}%)")
            st.progress(min(score_val / max_val, 1.0))

    st.markdown("---")

    # ── Framework checklist details ──
    st.subheader("📋 Detailed Score Explanations")
    for row_start in range(0, len(PILLARS), 3):
        for col, cat in zip(st.columns(3), PILLARS[row_start:row_start + 3]):
            with col:
                pct = pillar_pct[cat]
                badge = "⚪" if pct is None else "✅" if pct >= 75 else "⚠️" if pct >= 50 else "❌"

                st.markdown(f"### {badge} {cat}")
                st.markdown(f"**Score:** {scores[cat]}/{maxes[cat]}" if pct is not None else "**Score:** N/A")
                st.caption(explanations[cat])

    st.markdown("---")

    # ── Detail tabs ──
    dtab1, dtab2, dtab3, dtab4, dtab5 = st.tabs([
        "📊 Valuation",
        "💰 Quality & Returns",
        "📈 Growth",
        "🛡️ Risk & Balance Sheet",
        "👥 Ownership",
    ])

    with dtab1:
        # ── Loss-maker banner ──
        if is_loss_making:
            st.warning(
                "⚠️ **Loss-making company detected.** Earnings-based multiples (P/E, PEG, EV/EBITDA) "
                "are not meaningful here. Focus on EV/Sales vs growth, cash runway, gross margin "
                "trajectory, and dilution risk."
            )

        st.subheader("💎 Relative Valuation Multiples")

        # Row 1
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            pe_val = format_number(pe) if not is_loss_making else "N/A"
            st.metric("📊 Trailing P/E", pe_val, help=GLOSSARY["P/E"])
            if pe and pe > 0 and not is_loss_making:
                st.caption("Low ✅" if pe < 20 else "Fair 🟡" if pe < 40 else "High ⚠️")
        with c2:
            fpe_val = format_number(forward_pe) if not is_loss_making else "N/A"
            st.metric("📊 Forward P/E", fpe_val)
        with c3:
            peg_val = format_number(peg) if not is_loss_making else "N/A"
            st.metric("📈 PEG Ratio", peg_val, help=GLOSSARY["PEG"])
            if peg and peg > 0 and not is_loss_making:
                st.caption("Cheap ✅" if peg < 1 else "Fair 🟡" if peg < 1.5 else "Rich ⚠️")
        with c4:
            ps_val = format_number(ps)
            st.metric("🏷️ P/S (TTM)", ps_val, help=GLOSSARY["P/S"])
            if ps and ps > 0:
                st.caption("Low ✅" if ps < 3 else "Fair 🟡" if ps < 6 else "High ⚠️")

        # Row 2
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            ev_ebitda_val = format_number(ev_ebitda) if not is_loss_making else "N/A"
            st.metric("🏢 EV/EBITDA", ev_ebitda_val, help=GLOSSARY["EV/EBITDA"])
            if ev_ebitda and ev_ebitda > 0 and not is_loss_making:
                st.caption("Cheap ✅" if ev_ebitda < 10 else "Fair 🟡" if ev_ebitda < 15 else "Rich ⚠️")
        with c6:
            ev_rev_val = format_number(ev_rev)
            st.metric("🏢 EV/Revenue", ev_rev_val, help=GLOSSARY["EV/Sales"])
            if ev_rev and ev_rev > 0:
                st.caption("Low ✅" if ev_rev < 2 else "Fair 🟡" if ev_rev < 4 else "High ⚠️")
        with c7:
            pb_val = format_number(pb)
            st.metric("📚 P/B", pb_val)
        with c8:
            fcf_yield_val = format_number(fcf_yield, is_pct=True)
            st.metric("💵 FCF Yield", fcf_yield_val, help=GLOSSARY["FCF yield"])
            if fcf_yield and fcf_yield > 0:
                st.caption("Strong ✅" if fcf_yield > 0.08 else "Good 🟢" if fcf_yield > 0.05 else "Low ⚠️")

        # ── Loss-maker specific metrics ──
        if is_loss_making:
            st.markdown("---")
            st.subheader("🔦 Loss-Maker Key Metrics")
            lm1, lm2, lm3, lm4 = st.columns(4)

            # Cash runway
            if runway_months is not None:
                runway_color = "normal"
                runway_str = f"{runway_months:.0f} months"
            else:
                runway_str = "N/A"
            lm1.metric("Cash Runway", runway_str)
            if runway_months is not None:
                if runway_months < 9:
                    lm1.caption("🚨 Dangerously short")
                elif runway_months < 18:
                    lm1.caption("⚠️ Watch closely")
                else:
                    lm1.caption("✅ Adequate")

            # Net cash % of market cap
            lm2.metric("Net Cash / Mkt Cap", format_number(net_cash_pct, is_pct=True))
            if net_cash_pct is not None:
                if net_cash_pct > 0.30:  lm2.caption("✅ Significant downside cushion")
                elif net_cash_pct > 0.10: lm2.caption("Some cushion")
                else:                     lm2.caption("⚠️ Limited or net debt")

            # EV / Gross Profit
            lm3.metric("EV / Gross Profit", format_number(ev_gross_profit))
            if ev_gross_profit is not None:
                if ev_gross_profit < 10:   lm3.caption("✅ Reasonable unit economics")
                elif ev_gross_profit < 20: lm3.caption("Elevated — needs growth")
                else:                      lm3.caption("⚠️ Rich on gross profit basis")

            # Rule of 40
            lm4.metric("Rule of 40", f"{rule_of_40:.0f}" if rule_of_40 is not None else "N/A")
            if rule_of_40 is not None:
                if rule_of_40 >= 40:    lm4.caption("✅ Healthy (SaaS benchmark)")
                elif rule_of_40 >= 20:  lm4.caption("Developing")
                else:                   lm4.caption("⚠️ Below benchmark")

            st.caption(
                "**Cash Runway** = Total Cash ÷ Monthly Op. Cash Burn  •  "
                "**EV/GP** = Enterprise Value ÷ Gross Profit  •  "
                "**Rule of 40** = Revenue Growth % + Operating Margin % (SaaS proxy)"
            )

        st.markdown("---")
        st.subheader("📐 Intrinsic Value Estimates")
        st.caption(
            "Rough, transparent approximations — a sanity-check range, not a price target. "
            "Methods that need positive earnings are automatically suppressed for loss-makers."
        )

        iv_rows = []

        # ── Method 1: Lynch PEG=1 (trailing EPS) — profitable only ──────
        if not is_loss_making:
            if eps_trailing and earn_growth and earn_growth > 0 and eps_trailing > 0:
                g_pct = min(earn_growth * 100, 30)  # cap: quarterly YoY spikes aren't sustainable growth
                fair1 = eps_trailing * g_pct
                upside1 = ((fair1 / price) - 1) * 100 if price else None
                iv_rows.append({
                    "Method": "Lynch PEG=1 (Trailing EPS)",
                    "Fair Value": f"${fair1:.2f}",
                    "Implied Upside": f"{upside1:+.0f}%" if upside1 is not None else "N/A",
                    "_upside": upside1,
                    "Best For": "Profitable cos with predictable earnings growth",
                    "Usable": "✅",
                })
            else:
                iv_rows.append({
                    "Method": "Lynch PEG=1 (Trailing EPS)",
                    "Fair Value": "N/A",
                    "Implied Upside": "N/A",
                    "_upside": None,
                    "Best For": "Profitable cos with predictable earnings growth",
                    "Usable": "❌ needs +EPS & +growth",
                })

            # ── Method 2: Lynch PEG=1 (forward EPS) ─────────────────────
            if eps_forward and earn_growth and earn_growth > 0 and eps_forward > 0:
                g_pct = min(earn_growth * 100, 30)  # cap: quarterly YoY spikes aren't sustainable growth
                fair2 = eps_forward * g_pct
                upside2 = ((fair2 / price) - 1) * 100 if price else None
                iv_rows.append({
                    "Method": "Lynch PEG=1 (Forward EPS)",
                    "Fair Value": f"${fair2:.2f}",
                    "Implied Upside": f"{upside2:+.0f}%" if upside2 is not None else "N/A",
                    "_upside": upside2,
                    "Best For": "Forward-looking; high-growth profitable names",
                    "Usable": "✅",
                })
            else:
                iv_rows.append({
                    "Method": "Lynch PEG=1 (Forward EPS)",
                    "Fair Value": "N/A",
                    "Implied Upside": "N/A",
                    "_upside": None,
                    "Best For": "Forward-looking; high-growth profitable names",
                    "Usable": "❌ needs +fwd EPS & +growth",
                })

            # ── Method 3: EV/EBITDA at 12× — profitable only ────────────
            if ebitda_val and ebitda_val > 0 and shares_out:
                fair_ev5 = 12 * ebitda_val
                fair5 = (fair_ev5 - net_debt) / shares_out
                upside5 = ((fair5 / price) - 1) * 100 if price and fair5 > 0 else None
                iv_rows.append({
                    "Method": "EV/EBITDA at 12× (fair multiple)",
                    "Fair Value": f"${fair5:.2f}" if fair5 > 0 else "N/A",
                    "Implied Upside": f"{upside5:+.0f}%" if upside5 is not None else "N/A",
                    "_upside": upside5,
                    "Best For": "Capital-intensive / asset-heavy small-caps",
                    "Usable": "✅",
                })
            else:
                iv_rows.append({
                    "Method": "EV/EBITDA at 12× (fair multiple)",
                    "Fair Value": "N/A",
                    "Implied Upside": "N/A",
                    "_upside": None,
                    "Best For": "Capital-intensive / asset-heavy small-caps",
                    "Usable": "❌ needs positive EBITDA",
                })
        else:
            iv_rows.append({
                "Method": "Lynch PEG=1 (Trailing) — SUPPRESSED",
                "Fair Value": "—",
                "Implied Upside": "—",
                "_upside": None,
                "Best For": "Not applicable for loss-makers (negative earnings)",
                "Usable": "⛔ loss-making",
            })
            iv_rows.append({
                "Method": "EV/EBITDA at 12× — SUPPRESSED",
                "Fair Value": "—",
                "Implied Upside": "—",
                "_upside": None,
                "Best For": "Not applicable for loss-makers (negative EBITDA)",
                "Usable": "⛔ loss-making",
            })

        # ── Method: Growth-adjusted EV/Sales (all companies) ─────────────
        # Rule of thumb: fair EV/Sales ≈ rev_growth% ÷ 10 (e.g. 30% growth -> 3.0x EV/Rev)
        if revenue and rev_growth and rev_growth > 0 and shares_out:
            fair_ev_rev3 = max(1.0, (rev_growth * 100) / 10)
            fair_ev3 = fair_ev_rev3 * revenue
            fair3 = (fair_ev3 - net_debt) / shares_out
            upside3 = ((fair3 / price) - 1) * 100 if price and fair3 > 0 else None
            iv_rows.append({
                "Method": "Growth-adj EV/Sales (rev_growth%÷10)",
                "Fair Value": f"${fair3:.2f}" if fair3 > 0 else "N/A",
                "Implied Upside": f"{upside3:+.0f}%" if upside3 is not None else "N/A",
                "_upside": upside3,
                "Best For": "Primary method for pre-profit micro/small-caps",
                "Usable": "✅",
            })
        else:
            iv_rows.append({
                "Method": "Growth-adj EV/Sales (rev_growth%÷10)",
                "Fair Value": "N/A",
                "Implied Upside": "N/A",
                "_upside": None,
                "Best For": "Primary method for pre-profit micro/small-caps",
                "Usable": "❌ needs revenue & +growth",
            })

        # ── Method: EV / Gross Profit (especially useful for loss-makers) ─
        if gross_profit and gross_profit > 0 and shares_out and enterprise_val:
            fair_ev_gp = 15 * gross_profit
            fair_gp = (fair_ev_gp - net_debt) / shares_out
            upside_gp = ((fair_gp / price) - 1) * 100 if price and fair_gp > 0 else None
            iv_rows.append({
                "Method": "EV/Gross Profit at 15× (fair multiple)",
                "Fair Value": f"${fair_gp:.2f}" if fair_gp > 0 else "N/A",
                "Implied Upside": f"{upside_gp:+.0f}%" if upside_gp is not None else "N/A",
                "_upside": upside_gp,
                "Best For": "High/expanding gross margin loss-makers (unit economics)",
                "Usable": "✅",
            })
        else:
            iv_rows.append({
                "Method": "EV/Gross Profit at 15×",
                "Fair Value": "N/A",
                "Implied Upside": "N/A",
                "_upside": None,
                "Best For": "High gross margin loss-makers",
                "Usable": "❌ needs gross profit data",
            })

        # ── Method: FCF Yield at 6% ───────────────────────────────────────
        if fcf and shares_out and fcf > 0:
            fcf_ps = fcf / shares_out
            fair4 = fcf_ps / 0.06
            upside4 = ((fair4 / price) - 1) * 100 if price else None
            iv_rows.append({
                "Method": "FCF Yield at 6% (FCF/share ÷ 0.06)",
                "Fair Value": f"${fair4:.2f}",
                "Implied Upside": f"{upside4:+.0f}%" if upside4 is not None else "N/A",
                "_upside": upside4,
                "Best For": "FCF-positive mature small-caps",
                "Usable": "✅",
            })
        else:
            iv_rows.append({
                "Method": "FCF Yield at 6% (FCF/share ÷ 0.06)",
                "Fair Value": "N/A",
                "Implied Upside": "N/A",
                "_upside": None,
                "Best For": "FCF-positive mature small-caps",
                "Usable": "❌ needs positive FCF" if not is_loss_making else "⛔ negative FCF (loss-maker)",
            })

        # ── Average upside across usable methods ──────────────────────────
        valid_upsides = sorted(r["_upside"] for r in iv_rows if r["_upside"] is not None)
        iv_spread_wide = False
        if valid_upsides:
            med_upside = float(np.median(valid_upsides))
            lo_up, hi_up = valid_upsides[0], valid_upsides[-1]
            iv_spread_wide = len(valid_upsides) >= 2 and (hi_up - lo_up) > 100
            iv_rows.append({
                "Method": "📊 Median (usable methods)",
                "Fair Value": f"${price * (1 + med_upside / 100):.2f}" if price else "—",
                "Implied Upside": f"{med_upside:+.0f}%",
                "_upside": med_upside,
                "Best For": f"Median of {len(valid_upsides)} method(s); range {lo_up:+.0f}% to {hi_up:+.0f}%",
                "Usable": "📊",
            })

        df_iv = pd.DataFrame(iv_rows).drop(columns=["_upside"])
        st.dataframe(df_iv, use_container_width=True, hide_index=True)
        if iv_spread_wide:
            st.caption("⚠️ Methods disagree by more than 100 percentage points — treat the median as low confidence and lean on the methods suited to this company type.")

        # ── Guidance notes ────────────────────────────────────────────────
        if is_loss_making:
            st.info(
                "**💡 Valuation Guidance for Loss-Making Micro/Small-Caps** \n"
                "- **EV/Sales (preferred)**: 1–4× is often reasonable for solid growth; >8–10× requires hyper-growth (>40%) or top-tier gross margins (>75%). \n"
                "- **EV/Gross Profit**: Far better than pure P/S when gross margins are improving (rewards high-margin business models). \n"
                "- **Cash Runway (prefer ≥18–24 mo)**: A 'cheap' EV/Sales is an illusion if a cash crunch forces massive dilutive secondary offerings. \n"
                "- **Net Cash % of Mkt Cap**: 30–50%+ provides a strong tangible floor while the company iterates toward profitability. \n"
                "- **De-emphasized**: Trailing P/E, PEG, and EV/EBITDA are omitted/suppressed because negative denominators yield misleading figures. \n"
                "- **Watch Dilution**: Frequent share count growth permanently impairs per-share upside."
            )
        else:
            st.info(
                "**💡 Valuation Guidance for Profitable Micro/Small-Caps** \n"
                "- **Lynch PEG=1**: Best for profitable, predictable growers. Breaks down when PEG > 3 or earnings are lumpy. \n"
                "- **Growth-adj EV/Sales**: Cross-check for asset-light businesses. \n"
                "- **FCF Yield (6%)**: Anchors valuation in real cash — most reliable for mature names. \n"
                "- **EV/EBITDA (12×)**: Useful for capital-intensive businesses; too conservative for hyper-growth. \n"
                "- **Always cross-check**: No single method is reliable in isolation. Treat as a range."
            )

        # ── Path-to-profitability scenario box ───────────────────────────
        st.markdown("---")
        st.subheader("🛤️ Path-to-Profitability Scenario (Operating Leverage Model)")
        st.caption(
            "User-adjustable scenario: model what this business could be worth once operating leverage "
            "takes hold and it reaches normalized margins. Includes cash burn on the way, new shares issued to fund any shortfall, "
            "and a discount rate you control."
        )
        with st.expander("⚙️ Configure Scenario Assumptions", expanded=is_loss_making):
            sc1, sc2, sc3 = st.columns(3)
            default_growth = int((rev_growth or 0.25) * 100) if rev_growth else 25
            sc_rev_growth = sc1.number_input(
                "Assumed annual revenue growth (%)",
                min_value=0, max_value=250, value=max(5, min(200, default_growth)),
                key=f"sc_rg_{ticker_sym}"
            )
            sc_target_margin = sc2.slider(
                "Target normalized EBITDA margin (%)",
                min_value=5, max_value=45, value=18,
                key=f"sc_mg_{ticker_sym}",
                help="EBITDA (not operating) margin, to match the EV/EBITDA exit multiple. Mature SaaS: 25-35%, Aerospace/Mfg: 12-20%, Retail: 6-12%"
            )
            sc_years = sc3.slider(
                "Years to reach normalized margin",
                min_value=2, max_value=7, value=4,
                key=f"sc_yr_{ticker_sym}"
            )
            sc4, sc5, sc6 = st.columns(3)
            sc_exit_ev_ebitda = sc4.number_input(
                "Exit EV/EBITDA multiple at maturity",
                min_value=6, max_value=40, value=15,
                key=f"sc_em_{ticker_sym}"
            )
            sc_dilution = sc5.slider(
                "Other dilution: stock comp, extra raises (%)",
                min_value=0, max_value=60, value=10,
                key=f"sc_di_{ticker_sym}",
                help="Haircut on top of the dilution from funding the modeled cash burn"
            )
            hurdle_rate = sc6.slider(
                "Discount rate / required return (%)",
                min_value=8, max_value=30, value=15,
                key=f"sc_hr_{ticker_sym}",
                help="Micro-cap risk hurdle used to discount the year-N value back to today"
            ) / 100

            if revenue and shares_out:
                future_rev = revenue * ((1 + sc_rev_growth / 100) ** sc_years)
                future_ebitda = future_rev * (sc_target_margin / 100)
                future_ev = sc_exit_ev_ebitda * future_ebitda

                # Burn fades linearly to breakeven by year N; any shortfall vs cash is raised at today's price
                annual_burn = (total_cash / runway_months * 12) if runway_months else 0.0
                cum_burn = annual_burn * sc_years / 2
                funding_gap = max(0.0, cum_burn - (total_cash or 0))
                new_shares = (funding_gap / price) if price else 0.0
                future_cash = (total_cash or 0) - cum_burn + funding_gap
                future_equity = future_ev + future_cash - (total_debt or 0)

                pv_equity = future_equity / ((1 + hurdle_rate) ** sc_years)
                pv_equity_diluted = pv_equity * (1 - sc_dilution / 100)
                fair_sc = pv_equity_diluted / (shares_out + new_shares) if pv_equity_diluted > 0 else None
                upside_sc = ((fair_sc / price) - 1) * 100 if fair_sc and price else None

                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Projected Revenue", format_number(future_rev, is_currency=True))
                r2.metric("Projected EBITDA", format_number(future_ebitda, is_currency=True))
                r3.metric("Discounted Fair Value", f"${fair_sc:.2f}" if fair_sc else "N/A")
                r4.metric("Implied Upside", f"{upside_sc:+.0f}%" if upside_sc is not None else "N/A")

                if annual_burn > 0:
                    gap_dil = (new_shares / shares_out) * 100
                    st.caption(
                        f"**Funding**: current burn ≈ {format_number(annual_burn, is_currency=True)}/yr, fading to breakeven by year {sc_years} "
                        f"= {format_number(cum_burn, is_currency=True)} cumulative vs {format_number(total_cash, is_currency=True)} cash → "
                        f"raise {format_number(funding_gap, is_currency=True)} at today's price (≈{gap_dil:.0f}% new shares)."
                    )
                st.caption(
                    f"**Scenario Logic**: In year {sc_years}, company generates {format_number(future_rev, is_currency=True)} rev "
                    f"at a {sc_target_margin}% EBITDA margin = {format_number(future_ebitda, is_currency=True)} EBITDA. "
                    f"Valued at {sc_exit_ev_ebitda}× EV/EBITDA, plus year-N cash less debt, discounted at {hurdle_rate*100:.0f}%/yr, "
                    f"with a {sc_dilution}% other-dilution haircut."
                )
            else:
                st.info("Revenue or share count data unavailable for scenario calculation.")

        burn_annual = (total_cash / runway_months * 12) if (runway_months and total_cash) else 0.0

        st.markdown("---")
        st.subheader("🎲 Probability-Weighted Scenarios")
        st.caption(
            "Bear, base and bull cases built from the assumptions above: bear halves growth and cuts margin, "
            "multiple and dilution relief; bull lifts them. Set the weights to your own odds."
        )
        cases = [
            ("Bear", sc_rev_growth * 0.5, max(3, sc_target_margin * 0.6), max(6, sc_exit_ev_ebitda * 0.7), min(80, sc_dilution + 15)),
            ("Base", sc_rev_growth, sc_target_margin, sc_exit_ev_ebitda, sc_dilution),
            ("Bull", sc_rev_growth * 1.5, min(45, sc_target_margin * 1.25), sc_exit_ev_ebitda * 1.2, max(0, sc_dilution - 5)),
        ]
        pw1, pw2, pw3 = st.columns(3)
        weights = [
            pw1.number_input("Bear weight (%)", 0, 100, 25, key=f"pw_bear_{ticker_sym}"),
            pw2.number_input("Base weight (%)", 0, 100, 50, key=f"pw_base_{ticker_sym}"),
            pw3.number_input("Bull weight (%)", 0, 100, 25, key=f"pw_bull_{ticker_sym}"),
        ]
        rows, vals, wts = [], [], []
        for (case, g_c, m_c, x_c, d_c), w in zip(cases, weights):
            fv = scenario_fair_value(revenue, total_cash, total_debt, shares_out, price, burn_annual,
                                     g_c, sc_years, m_c, x_c, d_c, hurdle_rate)
            rows.append({
                "Scenario": case,
                "Revenue growth": f"{g_c:.0f}%",
                "EBITDA margin": f"{m_c:.0f}%",
                "Exit EV/EBITDA": f"{x_c:.1f}×",
                "Extra dilution": f"{d_c:.0f}%",
                "Weight": f"{w}%",
                "Fair value": f"${fv:.2f}" if fv else "N/A",
                "Upside": f"{(fv / price - 1) * 100:+.0f}%" if fv and price else "N/A",
            })
            if fv and w > 0:
                vals.append(fv)
                wts.append(w)
        if vals and price:
            weighted_fv = sum(v * w for v, w in zip(vals, wts)) / sum(wts)
            wa, wb = st.columns(2)
            wa.metric("Probability-weighted fair value", f"${weighted_fv:.2f}")
            wb.metric("Weighted upside", f"{(weighted_fv / price - 1) * 100:+.0f}%")
        else:
            st.info("Scenario values unavailable: needs revenue, share count and a price.")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🔁 Reverse DCF: What Growth Is Priced In?")
        st.caption(
            "Solves for the annual revenue growth at which the scenario model equals today's price, "
            "holding the margin, exit multiple, dilution and discount rate above."
        )
        implied = implied_growth(price, revenue, total_cash, total_debt, shares_out, burn_annual,
                                 sc_years, sc_target_margin, sc_exit_ev_ebitda, sc_dilution, hurdle_rate) \
            if price and revenue and shares_out else None
        ra, rb = st.columns(2)
        ra.metric("Growth priced in", f"{implied:.0f}%/yr" if implied is not None else "Out of range")
        rb.metric("Your assumed growth", f"{sc_rev_growth:.0f}%/yr")
        if implied is None:
            st.info("The price is not reachable between −50% and +300% growth at these assumptions.")
        elif implied > sc_rev_growth:
            st.warning(f"The price already assumes about {implied:.0f}%/yr growth, more than your {sc_rev_growth}% assumption. Your view needs to beat the market.")
        else:
            st.success(f"The price assumes about {implied:.0f}%/yr growth, below your {sc_rev_growth}% assumption. The market is less optimistic than you.")

        st.markdown("---")
        st.subheader("📏 Peer Growth Regression (EV/Sales vs Revenue Growth)")
        st.caption(
            "Enter 3–8 peers in the same industry. Fits EV/Sales against revenue growth across the peers, "
            "then reads the multiple this company's growth would earn on that line."
        )
        peer_raw = st.text_input(
            "Peer tickers (comma-separated)", placeholder="e.g. PL, BKSY, SPIR, ASTS", key=f"peers_{ticker_sym}"
        )
        peer_syms = list(dict.fromkeys(
            p.strip().upper() for p in peer_raw.split(",") if p.strip() and p.strip().upper() != ticker_sym
        ))[:8]
        if peer_syms:
            with st.spinner("Loading peers…"):
                peer_rows = [r for r in (get_peer_multiple(p) for p in peer_syms) if r]
            if peer_rows:
                st.dataframe(
                    pd.DataFrame([{"Ticker": r["Ticker"], "Name": r["Name"],
                                   "Revenue growth": r["growth"] * 100, "EV/Sales": r["ev_rev"]} for r in peer_rows]),
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Revenue growth": st.column_config.NumberColumn(format="%.1f%%"),
                        "EV/Sales": st.column_config.NumberColumn(format="%.2f×"),
                    },
                )
            x = np.array([r["growth"] * 100 for r in peer_rows])
            y = np.array([r["ev_rev"] for r in peer_rows])
            if len(peer_rows) < 3:
                st.info(f"Need at least 3 peers with growth and EV/Sales data; got {len(peer_rows)}.")
            elif np.ptp(x) == 0 or rev_growth is None or not revenue or not shares_out:
                st.info("Cannot fit a line: peer growth rates are identical, or this company's growth or revenue is missing.")
            else:
                slope, intercept = np.polyfit(x, y, 1)
                r2 = float(np.corrcoef(x, y)[0, 1] ** 2)
                pred = intercept + slope * rev_growth * 100
                if pred <= 0:
                    st.info("The fitted line gives a non-positive multiple at this company's growth rate.")
                else:
                    fair_ps = (pred * revenue - net_debt) / shares_out
                    pa, pb, pc, pd_ = st.columns(4)
                    pa.metric("Peer-implied EV/Sales", f"{pred:.1f}×")
                    pb.metric("Current EV/Sales", f"{ev_rev:.1f}×" if ev_rev else "N/A")
                    pc.metric("Regression fair value", f"${fair_ps:.2f}" if fair_ps > 0 else "N/A")
                    pd_.metric("R² (fit quality)", f"{r2:.2f}")
                    if r2 < 0.3:
                        st.caption("Low R²: growth explains little of the peer multiples, so treat this fit as weak.")
                    xs = np.linspace(x.min(), x.max(), 20)
                    fig_peer = go.Figure()
                    fig_peer.add_trace(go.Scatter(x=x, y=y, mode="markers+text", text=[r["Ticker"] for r in peer_rows],
                                                  textposition="top center", name="Peers"))
                    fig_peer.add_trace(go.Scatter(x=xs, y=intercept + slope * xs, mode="lines", name="Fit",
                                                  line=dict(dash="dash")))
                    fig_peer.add_trace(go.Scatter(x=[rev_growth * 100], y=[ev_rev] if ev_rev else [pred],
                                                  mode="markers+text", text=[ticker_sym], textposition="top center",
                                                  marker=dict(size=14, color="#FF9100"), name=ticker_sym))
                    fig_peer.update_layout(
                        xaxis_title="Revenue growth (%)", yaxis_title="EV/Sales (×)",
                        height=340, margin=dict(l=20, r=20, t=20, b=20),
                    )
                    st.plotly_chart(fig_peer, use_container_width=True)

    with dtab2:
        st.subheader("Quality & Profitability")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ROE", format_number(roe, is_pct=True))
        c2.metric("ROA", format_number(roa, is_pct=True))
        c3.metric("Operating Margin", format_number(op_margin, is_pct=True))
        c4.metric("Gross Margin", format_number(gross_margin, is_pct=True))
        p1, p2 = st.columns(2)
        p1.metric("Profit Margin", format_number(profit_margin, is_pct=True))
        p2.metric("ROIC (NOPAT ÷ debt + equity)", f"{roic*100:.1f}%" if roic is not None else "N/A")
        st.info(
            "**Framework note**: High sustainable ROIC + positive margins = multi-bagger potential. "
            "ROIC drives the Capital Allocation score (ROE is the fallback when statements are unavailable)."
        )

    with dtab3:
        st.subheader("📈 Revenue & Growth Trajectory (TTM & Recent Quarters)")

        # ── 1. Process Quarterly Revenue Data (Up to 8 Quarters) ──
        q_records = []
        if q_financials is not None and not q_financials.empty:
            q_cols = sorted(list(q_financials.columns))
            # Take up to last 8 quarters
            recent_q_cols = q_cols[-8:]
            rev_row = next((r for r in ["Total Revenue", "Operating Revenue"] if r in q_financials.index), None)
            gp_row = next((r for r in ["Gross Profit"] if r in q_financials.index), None)
            sh_row = next((r for r in ["Diluted Average Shares", "Basic Average Shares"] if r in q_financials.index), None)

            for c in recent_q_cols:
                period_str = f"{c.year}-Q{(c.month-1)//3 + 1}"
                r_val = q_financials.loc[rev_row, c] if rev_row else np.nan
                gp_val = q_financials.loc[gp_row, c] if gp_row else np.nan
                sh_val = q_financials.loc[sh_row, c] if sh_row else np.nan
                q_records.append({
                    "date": c,
                    "quarter": period_str,
                    "revenue": float(r_val) if pd.notnull(r_val) else np.nan,
                    "gross_profit": float(gp_val) if pd.notnull(gp_val) else np.nan,
                    "shares": float(sh_val) if pd.notnull(sh_val) else np.nan,
                })

        df_q = pd.DataFrame(q_records).dropna(subset=["revenue"]).reset_index(drop=True) if q_records else pd.DataFrame()

        ttm_rev = None
        ttm_yoy = None
        latest_yoy = None
        growth_accel_str = "N/A"
        growth_accel_status = "N/A"
        qoq_consistency_str = "N/A"
        qoq_consistency_status = "N/A"
        cagr_2yr_str = "N/A"
        cagr_2yr_status = "N/A"
        rev_per_share_str = "N/A"
        rev_per_share_status = "N/A"
        gm_trend_str = "N/A"
        gm_trend_status = "N/A"

        if not df_q.empty:
            df_q["qoq_growth"] = df_q["revenue"].pct_change() * 100
            if len(df_q) >= 5:
                df_q["yoy_growth"] = df_q["revenue"].pct_change(4) * 100
            else:
                df_q["yoy_growth"] = np.nan
            df_q["gross_margin"] = (df_q["gross_profit"] / df_q["revenue"]) * 100
            if "shares" in df_q and df_q["shares"].notnull().any():
                df_q["rev_per_share"] = df_q["revenue"] / df_q["shares"]
                if len(df_q) >= 5:
                    df_q["rps_yoy_growth"] = df_q["rev_per_share"].pct_change(4) * 100
                else:
                    df_q["rps_yoy_growth"] = np.nan
                df_q["dilution_drag"] = df_q["yoy_growth"] - df_q["rps_yoy_growth"]
            else:
                df_q["rev_per_share"] = np.nan
                df_q["rps_yoy_growth"] = np.nan
                df_q["dilution_drag"] = np.nan

            # TTM calculations
            if len(df_q) >= 4:
                ttm_rev = df_q["revenue"].iloc[-4:].sum()
                if len(df_q) >= 8:
                    prior_ttm = df_q["revenue"].iloc[-8:-4].sum()
                    ttm_yoy = ((ttm_rev / prior_ttm) - 1) * 100 if prior_ttm > 0 else None
                elif not np.isnan(df_q["yoy_growth"].iloc[-1]):
                    ttm_yoy = df_q["yoy_growth"].iloc[-1]
            else:
                ttm_rev = df_q["revenue"].sum()

            latest_yoy = df_q["yoy_growth"].iloc[-1] if not np.isnan(df_q["yoy_growth"].iloc[-1]) else (rev_growth * 100 if rev_growth else None)

            # Growth Acceleration
            valid_yoys = df_q["yoy_growth"].dropna()
            if len(valid_yoys) >= 2:
                curr_y = valid_yoys.iloc[-1]
                prev_y = valid_yoys.iloc[-2]
                diff = curr_y - prev_y
                if diff > 4:
                    growth_accel_str = f"+{curr_y:.1f}% (vs +{prev_y:.1f}% prev)"
                    growth_accel_status = "🚀 Accelerating"
                elif diff < -4:
                    growth_accel_str = f"+{curr_y:.1f}% (vs +{prev_y:.1f}% prev)"
                    growth_accel_status = "🔻 Decelerating"
                else:
                    growth_accel_str = f"Steady at ~{curr_y:.1f}%"
                    growth_accel_status = "➡️ Stable"
            elif len(df_q) >= 2:
                curr_q = df_q["qoq_growth"].iloc[-1]
                prev_q = df_q["qoq_growth"].iloc[-2]
                growth_accel_str = f"QoQ: {curr_q:+.1f}% vs {prev_q:+.1f}%"
                growth_accel_status = "🟢 QoQ Momentum" if curr_q > prev_q else "🟡 Mixed"

            # QoQ Consistency
            valid_qoqs = df_q["qoq_growth"].dropna()
            if len(valid_qoqs) >= 2:
                pos_c = (valid_qoqs > 0).sum()
                tot_c = len(valid_qoqs)
                qoq_consistency_str = f"{pos_c}/{tot_c} positive quarters"
                if pos_c == tot_c:
                    qoq_consistency_status = "✅ Highly consistent"
                elif pos_c / tot_c >= 0.70:
                    qoq_consistency_status = "🟢 Moderate consistency"
                else:
                    qoq_consistency_status = "⚠️ Lumpy / Volatile"

            # Gross margin trend
            valid_gms = df_q["gross_margin"].dropna()
            if len(valid_gms) >= 2:
                first_gm = valid_gms.iloc[0]
                latest_gm = valid_gms.iloc[-1]
                diff_gm = latest_gm - first_gm
                gm_trend_str = f"{first_gm:.1f}% → {latest_gm:.1f}%"
                if diff_gm > 2:
                    gm_trend_status = "📈 Expanding unit economics"
                elif diff_gm < -2:
                    gm_trend_status = "📉 Contracting margins"
                else:
                    gm_trend_status = "➡️ Stable gross margin"

            # Revenue per share trend
            valid_rps = df_q["rps_yoy_growth"].dropna()
            if len(valid_rps) >= 1 and latest_yoy is not None:
                rps_val = valid_rps.iloc[-1]
                drag = latest_yoy - rps_val
                rev_per_share_str = f"{rps_val:+.1f}% YoY (Drag: -{drag:.1f}%)"
                if drag > 12:
                    rev_per_share_status = "🚨 Heavy dilution drag"
                elif drag > 4:
                    rev_per_share_status = "⚠️ Moderate dilution"
                else:
                    rev_per_share_status = "✅ Minimal dilution drag"

        # Multi-Year CAGR (annual financials)
        if financials is not None and not financials.empty and "Total Revenue" in financials.index:
            ann_rev = financials.loc["Total Revenue"].dropna()
            if len(ann_rev) >= 3 and ann_rev.values[2] > 0:
                cagr_2 = ((ann_rev.values[0] / ann_rev.values[2]) ** 0.5 - 1) * 100
                cagr_2yr_str = f"{cagr_2:.1f}%"
                cagr_2yr_status = "✅ Multi-year runway" if cagr_2 > 20 else ("🟢 Moderate CAGR" if cagr_2 > 10 else "⚠️ Slow growth")
            elif len(ann_rev) >= 2 and ann_rev.values[1] > 0:
                cagr_1 = ((ann_rev.values[0] / ann_rev.values[1]) - 1) * 100
                cagr_2yr_str = f"{cagr_1:.1f}% (1-yr)"
                cagr_2yr_status = "✅ High growth" if cagr_1 > 20 else "🟢 Moderate"

        # Cash Runway Status
        if runway_months is not None:
            runway_str_val = f"{runway_months:.0f} months"
            if runway_months >= 24:
                runway_status_val = "✅ Ample runway (≥24 mo)"
            elif runway_months >= 18:
                runway_status_val = "🟢 Adequate runway (18–24 mo)"
            elif runway_months >= 9:
                runway_status_val = "⚠️ Tight runway (<18 mo) — dilution risk"
            else:
                runway_status_val = "🚨 Dangerously short (<9 mo) — dilution imminent"
        else:
            runway_str_val = "Self-funding / N/A"
            runway_status_val = "✅ Positive OCF" if (op_cashflow and op_cashflow > 0) else "Data unavailable"

        # Rule of 40 Status
        if rule_of_40 is not None:
            rule_40_str = f"{rule_of_40:.0f}%"
            if rule_of_40 >= 40:
                rule_40_status = "✅ Elite (≥40%)"
            elif rule_of_40 >= 20:
                rule_40_status = "🟡 Developing (20–40%)"
            else:
                rule_40_status = "⚠️ Below benchmark (<20%)"
        else:
            rule_40_str = "N/A"
            rule_40_status = "Data unavailable"

        # ── KPI Cards Row 1 ──
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("💰 TTM Revenue", format_number(ttm_rev or revenue, is_currency=True))
        with k2:
            ttm_growth = f"{ttm_yoy:+.1f}%" if ttm_yoy is not None else format_number(rev_growth, is_pct=True)
            st.metric("📈 TTM YoY Growth", ttm_growth)
            if ttm_yoy and ttm_yoy > 20:
                st.caption("Strong 🚀")
            elif ttm_yoy and ttm_yoy > 10:
                st.caption("Solid 🟢")
            elif ttm_yoy and ttm_yoy > 0:
                st.caption("Modest 🟡")
        with k3:
            st.metric("📊 2-Yr Revenue CAGR", cagr_2yr_str)
            st.caption(cagr_2yr_status)
        with k4:
            st.metric("⚡ Rule of 40 Proxy", rule_40_str)
            st.caption(rule_40_status)

        # ── KPI Cards Row 2 ──
        k5, k6, k7, k8 = st.columns(4)
        with k5:
            st.metric("🚀 Growth Acceleration", "")
            st.write(f"**{growth_accel_status}**")
            st.caption(growth_accel_str)
        with k6:
            st.metric("📋 QoQ Consistency", "")
            st.write(qoq_consistency_str)
            st.caption(qoq_consistency_status)
        with k7:
            st.metric("👤 Rev Per Share", "")
            st.write(rev_per_share_status)
            st.caption(rev_per_share_str)
        with k8:
            st.metric("⏱️ Cash Runway", runway_str_val, help=GLOSSARY["Cash runway"])
            st.caption(runway_status_val)

        st.markdown("---")

        # ── Visual Chart: Quarterly Revenue & Margins ──
        if not df_q.empty:
            st.subheader("📊 Quarterly Revenue & Margin Progression")
            fig_q = go.Figure()
            # Bar for Revenue
            fig_q.add_trace(go.Bar(
                x=df_q["quarter"],
                y=df_q["revenue"] / 1e6,
                name="Revenue ($M)",
                marker_color="#2962FF",
                yaxis="y"
            ))
            # Line for YoY growth
            if df_q["yoy_growth"].notnull().any():
                fig_q.add_trace(go.Scatter(
                    x=df_q["quarter"],
                    y=df_q["yoy_growth"],
                    name="YoY Growth %",
                    mode="lines+markers",
                    line=dict(color="#00E676", width=2.5),
                    yaxis="y2"
                ))
            # Line for Gross margin
            if df_q["gross_margin"].notnull().any():
                fig_q.add_trace(go.Scatter(
                    x=df_q["quarter"],
                    y=df_q["gross_margin"],
                    name="Gross Margin %",
                    mode="lines+markers",
                    line=dict(color="#FF9100", width=2, dash="dot"),
                    yaxis="y2"
                ))
            fig_q.update_layout(
                title="Quarterly Revenue ($M) vs Growth & Gross Margin",
                xaxis_title="Quarter",
                yaxis=dict(title="Revenue ($M)", side="left"),
                yaxis2=dict(title="Percent (%)", side="right", overlaying="y", showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=380,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_q, use_container_width=True)

            # ── Detailed Table: Recent Quarters Breakdown ──
            st.subheader(f"📋 Last {len(df_q)} Quarters Financial Breakdown")
            if len(df_q) < 8:
                st.caption("Yahoo Finance supplies only the most recent quarters, so TTM YoY growth and multi-quarter acceleration may be unavailable.")
            df_display = df_q.copy()
            df_display = df_display.iloc[::-1].reset_index(drop=True)  # newest first
            table_rows = []
            for _, r in df_display.iterrows():
                table_rows.append({
                    "Quarter": r["quarter"],
                    "Revenue": format_number(r["revenue"], is_currency=True),
                    "QoQ Growth": f"{r['qoq_growth']:+.1f}%" if pd.notnull(r["qoq_growth"]) else "—",
                    "YoY Growth": f"{r['yoy_growth']:+.1f}%" if pd.notnull(r["yoy_growth"]) else "—",
                    "Gross Profit": format_number(r["gross_profit"], is_currency=True),
                    "Gross Margin": f"{r['gross_margin']:.1f}%" if pd.notnull(r["gross_margin"]) else "—",
                    "Shares (M)": f"{r['shares']/1e6:.1f}M" if pd.notnull(r["shares"]) else "—",
                    "Rev / Share": f"${r['rev_per_share']:.2f}" if pd.notnull(r["rev_per_share"]) else "—",
                    "Rev/Sh YoY": f"{r['rps_yoy_growth']:+.1f}%" if pd.notnull(r["rps_yoy_growth"]) else "—",
                    "Dilution Drag": f"-{r['dilution_drag']:.1f}%" if pd.notnull(r["dilution_drag"]) and r["dilution_drag"] > 0 else ("Minimal" if pd.notnull(r["dilution_drag"]) else "—"),
                })
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── Microcap Growth Quality Reference Guide ──
        st.subheader("🧭 Microcap Growth Quality Evaluation")
        ref_data = [
            {
                "Metric": "TTM YoY growth",
                "Stock Value": f"{ttm_yoy:+.1f}%" if ttm_yoy is not None else format_number(rev_growth, is_pct=True),
                "Why it matters for microcaps": "Cleaner than single-quarter YoY; filters out quarterly timing noise.",
                "Assessment": "✅ Strong (>20%)" if (ttm_yoy or (rev_growth and rev_growth*100) or 0) > 20 else ("🟢 Moderate" if (ttm_yoy or (rev_growth and rev_growth*100) or 0) > 10 else "⚠️ Subdued")
            },
            {
                "Metric": "Growth acceleration",
                "Stock Value": growth_accel_str,
                "Why it matters for microcaps": "Multi-baggers often show sustained or improving growth trajectories.",
                "Assessment": growth_accel_status
            },
            {
                "Metric": "QoQ consistency",
                "Stock Value": qoq_consistency_str,
                "Why it matters for microcaps": "Flags lumpy, contract-driven, or one-time revenue spikes.",
                "Assessment": qoq_consistency_status
            },
            {
                "Metric": "2-year / multi-year CAGR",
                "Stock Value": cagr_2yr_str,
                "Why it matters for microcaps": "Demonstrates runway quality and endurance beyond a temporary cycle.",
                "Assessment": cagr_2yr_status
            },
            {
                "Metric": "Revenue per share trend",
                "Stock Value": rev_per_share_str,
                "Why it matters for microcaps": "Adjusts for dilution — reveals if top-line growth is creating real per-share value.",
                "Assessment": rev_per_share_status
            },
            {
                "Metric": "Gross margin trend (quarterly)",
                "Stock Value": gm_trend_str,
                "Why it matters for microcaps": "Verifies unit economics are improving even while overall net income is negative.",
                "Assessment": gm_trend_status
            },
            {
                "Metric": "Cash runway (months)",
                "Stock Value": runway_str_val,
                "Why it matters for microcaps": "Months of cash left at current burn rate — determines impending dilution risk.",
                "Assessment": runway_status_val
            },
            {
                "Metric": "Rule of 40 proxy (growth% + margin%)",
                "Stock Value": rule_40_str,
                "Why it matters for microcaps": "Key operational efficiency screen for software, tech, and asset-light businesses.",
                "Assessment": rule_40_status
            },
        ]
        st.dataframe(pd.DataFrame(ref_data), use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── Historical Shares Outstanding & Dilution Watch ──
        st.subheader("🛡️ Shares Outstanding Trend (Dilution Watch)")
        try:
            if shares_hist is not None and not shares_hist.empty:
                shares_s = shares_hist
                if len(shares_s) >= 2:
                    first_val = float(shares_s.iloc[0])
                    latest_val = float(shares_s.iloc[-1])
                    total_dilution = ((latest_val / first_val) - 1) * 100 if first_val > 0 else None
                    if total_dilution is not None:
                        dilution_msg = f"Cumulative share count change: **{total_dilution:+.1f}%**"
                        if total_dilution > 25:
                            st.warning(f"🚨 **Heavy Dilution Alert**: {dilution_msg}. Frequent share issuance erodes per-share returns.")
                        elif total_dilution > 5:
                            st.info(f"⚠️ **Moderate Dilution**: {dilution_msg}")
                        else:
                            st.success(f"✅ **Disciplined Share Count**: {dilution_msg}")
                fig_shares = px.line(shares_hist, title="Shares Outstanding Trend (Dilution Watch)")
                fig_shares.update_layout(height=350)
                st.plotly_chart(fig_shares, use_container_width=True)
                st.caption("Rising shares = dilution (per-share destruction for loss-makers)")
        except Exception:
            st.caption("Shares outstanding history not available")
        st.info("**Framework note**: Multi-bagger compounders require multi-year double-digit growth paired with limited share dilution.")

    with dtab4:
        st.subheader("Risk & Balance Sheet")
        c1, c2, c3 = st.columns(3)
        c1.metric("Debt/Equity", f"{de_ratio/100:.2f}x" if de_ratio is not None else "N/A")
        c2.metric("Current Ratio", format_number(current_ratio))
        c3.metric("Quick Ratio", format_number(quick_ratio))
        c4, c5, c6 = st.columns(3)
        c4.metric("Total Cash", format_number(total_cash, is_currency=True))
        c5.metric("Total Debt", format_number(total_debt, is_currency=True))
        c6.metric("Free Cash Flow", format_number(fcf, is_currency=True))
        st.info("**Framework note**: Prefer low/no debt and positive free cash flow.")

    with dtab5:
        st.subheader("Ownership")
        c1, c2 = st.columns(2)
        c1.metric("Insider Ownership", format_number(insider_pct, is_pct=True))
        c2.metric("Institutional Ownership", format_number(inst_pct, is_pct=True))
        st.metric("Shares Outstanding", format_number(shares_out))
        st.metric("Float", format_number(float_shares))
        st.info("**Framework note**: High insider ownership is a top signal (Cassel, Fisher).")

        st.markdown("---")
        st.subheader("Smart Money: Insider Activity (last 12 months)")
        if flow["ins_ok"]:
            i1, i2, i3 = st.columns(3)
            i1.metric("Insider buys", f"{flow['buy_n']}  ·  {format_number(flow['buy_val'], is_currency=True)}")
            i2.metric("Insider sales", f"{flow['sell_n']}  ·  {format_number(flow['sell_val'], is_currency=True)}")
            i3.metric("Net insider $", format_number(flow["buy_val"] - flow["sell_val"], is_currency=True))
            if flow["trades"]:
                st.dataframe(pd.DataFrame(flow["trades"]), use_container_width=True, hide_index=True)
            else:
                st.caption("No open-market insider buys or sales in the last 12 months. Gifts, grants and tax withholding are not counted.")
        else:
            st.caption("Insider transaction data not available for this ticker.")

        st.subheader("Smart Money: Institutional Holders (top 10)")
        if flow["inst_ok"]:
            st.metric("Holders adding vs trimming", f"{flow['inst_up']} up  /  {flow['inst_down']} down")
            st.dataframe(
                pd.DataFrame(flow["holders"]),
                use_container_width=True, hide_index=True,
                column_config={
                    "% Held": st.column_config.NumberColumn(format="%.2f%%"),
                    "Change in shares": st.column_config.NumberColumn(format="%+.2f%%"),
                },
            )
            st.caption(
                "Yahoo Finance reports only each holder's most recent change, not four quarters of history, "
                "so this reflects the latest reporting quarter."
            )
        else:
            st.caption("Institutional holder data not available for this ticker.")

    # ── Summary ──
    st.markdown("---")
    st.subheader("Framework Summary")
    if score_pct >= 70:
        st.success(f"**Strong alignment** ({score_pct:.0f}%) — Worth deeper qualitative research.")
    elif score_pct >= 45:
        st.warning(f"**Mixed signals** ({score_pct:.0f}%) — Some attractive traits but clear gaps.")
    else:
        st.error(f"**Weak alignment** ({score_pct:.0f}%) — Does not fit the multi-bagger framework well.")

    if is_loss_making:
        st.info(
            "**📌 Multi-Bagger Reality Check for Loss-Makers**:\n"
            "Loss-making microcaps can still create enormous multi-bagger returns, but only when they possess:\n"
            "1. **High-quality, durable revenue growth** with improving unit economics / gross margins.\n"
            "2. **Sufficient runway (≥18–24 months)** or a large net cash cushion (>30% of market cap).\n"
            "3. **Disciplined share count**: limited dilution and no toxic death-spiral financing.\n"
            "4. **Reasonable sales multiple** relative to growth (avoid >8–10× without hyper-growth).\n"
            "5. **High insider alignment** (skin in the game).\n\n"
            "*Avoid names combining high burn, continuous dilution, decelerating revenue, and rich multiples.*"
        )

    st.markdown("""
**Next steps for any name that scores well:**
1. Read the latest 10-K / 10-Q yourself
2. Check insider buying/selling activity
3. Assess competitive position and runway (scuttlebutt)
4. Model simple scenarios (what growth is priced in?)
5. Size the position for liquidity and risk
""")
    st.caption(
        f"Data as of {datetime.now().strftime('%Y-%m-%d %H:%M')} "
        "• Not investment advice • Always verify primary sources"
    )


def add_ticker_from_form():
    t = st.session_state.get("add_ticker_input", "").upper().strip()
    if not t:
        st.session_state.add_msg = ("warning", "Enter a ticker symbol first.")
    elif t in st.session_state.watchlist:
        st.session_state.add_msg = ("warning", f"{t} is already in your watchlist.")
    else:
        st.session_state.watchlist.append(t)
        save_watchlist(st.session_state.watchlist)
        st.session_state.add_msg = ("success", f"Added {t}.")
    st.session_state.add_ticker_input = ""


def render_watchlist_panel():
    wl = st.session_state.watchlist
    with st.expander(f"📋 Watchlist · {len(wl)} stock{'s' if len(wl) != 1 else ''}", expanded=False):
        add_l, add_r = st.columns([4, 1], vertical_alignment="bottom")
        add_l.text_input("Add a ticker", placeholder="e.g. RKLB, NBIS, AAPL", key="add_ticker_input",
                         on_change=add_ticker_from_form)
        add_r.button("➕ Add", type="primary", use_container_width=True, on_click=add_ticker_from_form)
        msg = st.session_state.pop("add_msg", None)
        if msg:
            getattr(st, msg[0])(msg[1])

        if wl:
            for start in range(0, len(wl), 6):
                cols = st.columns(6)
                for col, t in zip(cols, wl[start:start + 6]):
                    col.button(f"{t}  ✕", key=f"chip_{t}", on_click=close_ticker, args=(t,),
                               use_container_width=True, help=f"Remove {t} from the watchlist")
            st.caption("Click a ticker's ✕ to remove it. Changes are saved automatically.")
        else:
            st.info("Your watchlist is empty.")
            if st.button("🔄 Reset to default (RKLB)", use_container_width=True):
                st.session_state.watchlist = ["RKLB"]
                save_watchlist(st.session_state.watchlist)
                st.rerun()


# ── Macro regime (independent of any stock) ─────────────────────────────────

MACRO_SYMBOLS = [
    ("^VIX", "CBOE Volatility Index (VIX)", "Yahoo", "Fear gauge; elevated = adverse"),
    ("^VIX3M", "CBOE 3-month volatility index", "Yahoo", "VIX term structure for fear gauge"),
    ("^GSPC", "S&P 500 index", "Yahoo", "Market trend vs 200-day average"),
    ("SPY", "S&P 500 ETF", "Yahoo", "Large-cap benchmark"),
    ("RSP", "S&P 500 equal-weight ETF", "Yahoo", "Breadth: broad participation vs mega caps"),
    ("^RUT", "Russell 2000 index", "Yahoo", "Small-cap benchmark"),
    ("IWM", "Russell 2000 ETF", "Yahoo", "Small-cap proxy"),
    ("HYG", "High-yield corporate bond ETF", "Yahoo", "Credit appetite (vs LQD)"),
    ("LQD", "Investment-grade corporate bond ETF", "Yahoo", "Credit appetite (vs HYG)"),
    ("TLT", "20+ year Treasury ETF", "Yahoo", "Long-duration rate moves (info)"),
    ("XLY", "Consumer discretionary ETF", "Yahoo", "Growth-sensitive spending (vs XLP)"),
    ("XLP", "Consumer staples ETF", "Yahoo", "Defensive rotation (vs XLY)"),
    ("DX-Y.NYB", "US Dollar index", "Yahoo", "Strong dollar tightens global liquidity"),
    ("HG=F", "Copper futures", "Yahoo", "Industrial demand and growth proxy"),
    ("CL=F", "WTI crude oil futures", "Yahoo", "Energy costs and inflation (info)"),
    ("GC=F", "Gold futures", "Yahoo", "Fear and real-rate hedge (info)"),
    ("BTC-USD", "Bitcoin", "Yahoo", "Speculative risk appetite (info)"),
    ("^TNX", "10-year Treasury yield index", "Yahoo", "Reference for DGS10"),
    ("^FVX", "5-year Treasury yield index", "Yahoo", "Reference curve point (info)"),
    ("^TYX", "30-year Treasury yield index", "Yahoo", "Reference curve point (info)"),
    ("^IRX", "13-week T-bill yield index", "Yahoo", "Short-rate reference (info)"),
    ("DGS10", "10-year Treasury constant maturity", "FRED", "Discount rate and mortgage cost"),
    ("DGS2", "2-year Treasury constant maturity", "FRED", "Policy-rate expectations (info)"),
    ("T10Y2Y", "10-year minus 2-year Treasury spread", "FRED", "Curve shape; inverted signals slowdown"),
    ("DFII10", "10-year real yield (TIPS)", "FRED", "Real cost of money"),
    ("T10YIE", "10-year breakeven inflation", "FRED", "Market inflation expectations"),
    ("FEDFUNDS", "Effective federal funds rate", "FRED", "Policy-rate direction"),
    ("BAMLH0A0HYM2", "ICE BofA high-yield option-adjusted spread", "FRED", "Credit stress"),
    ("NFCI", "Chicago Fed National Financial Conditions Index", "FRED", "Below 0 = looser than average"),
    ("DRTSCILM", "Bank lending standards, C&I loans", "FRED", "Net share of banks tightening credit"),
    ("UNRATE", "Unemployment rate", "FRED", "Labour market"),
    ("ICSA", "Initial jobless claims (weekly)", "FRED", "Layoffs"),
    ("CPIAUCSL", "Consumer price index (all urban)", "FRED", "Headline inflation"),
    ("PCEPILFE", "Core PCE price index", "FRED", "Fed's preferred inflation gauge"),
    ("INDPRO", "Industrial production index", "FRED", "Manufacturing and growth"),
    ("RSAFS", "Retail sales", "FRED", "Consumer demand"),
]
MACRO_YAHOO = [s for s, _, src, _ in MACRO_SYMBOLS if src == "Yahoo"]
MACRO_FRED = [s for s, _, src, _ in MACRO_SYMBOLS if src == "FRED"]


@st.cache_data(ttl=3600)
def fetch_macro_prices():
    try:
        data = yf.download(MACRO_YAHOO, period="3y", interval="1d", auto_adjust=True, progress=False)
        close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
        return close.dropna(how="all")
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=21600)
def fetch_fred(series_id):
    start = (pd.Timestamp.today() - pd.DateOffset(years=5)).strftime("%Y-%m-%d")
    try:
        df = pd.read_csv(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start}")
        df.columns = ["DATE", "VALUE"]
        s = pd.Series(pd.to_numeric(df["VALUE"], errors="coerce").values, index=pd.to_datetime(df["DATE"]))
        return s.dropna()
    except Exception:
        return None


def _ago(s, months):
    if s is None or s.empty:
        return None
    past = s[s.index <= s.index[-1] - pd.DateOffset(months=months)]
    return float(past.iloc[-1]) if len(past) else None


def _pct_change(s, months):
    then = _ago(s, months)
    return (float(s.iloc[-1]) / then - 1) * 100 if then else None


def compute_macro(px, fred):
    rows, series_map = [], {}

    def yh(sym):
        return px[sym].dropna() if (not px.empty and sym in px.columns) else None

    def add(name, group, latest, change, signal, rule, source):
        rows.append({"Indicator": name, "Group": group, "Latest": latest, "Change": change,
                     "signal": signal, "Rule": rule, "Source": source})

    def level(s, fmt):
        return fmt(float(s.iloc[-1])) if s is not None and len(s) else "n/a"

    # Rates
    d10 = fred.get("DGS10")
    if d10 is not None and len(d10):
        d = float(d10.iloc[-1]) - (_ago(d10, 3) or float(d10.iloc[-1]))
        sig = 1 if d < -0.25 else -1 if d > 0.25 else 0
        add("10-year Treasury yield", "Rates", level(d10, lambda v: f"{v:.2f}%"), f"{d:+.2f} pp (3m)",
            sig, "Falls >0.25 pp in 3m = supportive; rises >0.25 pp = adverse", "FRED DGS10")
        series_map["10-year Treasury yield"] = d10
    else:
        add("10-year Treasury yield", "Rates", "n/a", "n/a", None, "Data unavailable", "FRED DGS10")

    curve = fred.get("T10Y2Y")
    if curve is not None and len(curve):
        v = float(curve.iloc[-1])
        sig = 1 if v > 0.25 else -1 if v < 0 else 0
        add("10y minus 2y spread", "Rates", f"{v:+.2f} pp", "", sig,
            "Above 0.25 pp = normal curve (+1); below 0 = inverted (−1)", "FRED T10Y2Y")
        series_map["10y minus 2y spread"] = curve
    else:
        add("10y minus 2y spread", "Rates", "n/a", "n/a", None, "Data unavailable", "FRED T10Y2Y")

    ff = fred.get("FEDFUNDS")
    if ff is not None and len(ff):
        d = float(ff.iloc[-1]) - (_ago(ff, 6) or float(ff.iloc[-1]))
        sig = 1 if d <= -0.25 else -1 if d >= 0.25 else 0
        add("Fed funds rate", "Rates", level(ff, lambda v: f"{v:.2f}%"), f"{d:+.2f} pp (6m)", sig,
            "Cutting (≤−0.25 pp in 6m) = +1; hiking (≥+0.25 pp) = −1", "FRED FEDFUNDS")
    else:
        add("Fed funds rate", "Rates", "n/a", "n/a", None, "Data unavailable", "FRED FEDFUNDS")

    real = fred.get("DFII10")
    if real is not None and len(real):
        v = float(real.iloc[-1])
        sig = 1 if v < 1 else -1 if v > 2 else 0
        add("10-year real yield", "Rates", level(real, lambda x: f"{x:.2f}%"), "", sig,
            "Below 1% = +1; above 2% = −1", "FRED DFII10")
    else:
        add("10-year real yield", "Rates", "n/a", "n/a", None, "Data unavailable", "FRED DFII10")

    # Credit and liquidity
    hy = fred.get("BAMLH0A0HYM2")
    if hy is not None and len(hy):
        d = float(hy.iloc[-1]) - (_ago(hy, 3) or float(hy.iloc[-1]))
        sig = 1 if d < -0.2 else -1 if d > 0.3 else 0
        add("High-yield credit spread", "Credit", level(hy, lambda v: f"{v:.2f}%"), f"{d:+.2f} pp (3m)", sig,
            "Narrowing >0.2 pp = +1; widening >0.3 pp = −1", "FRED BAMLH0A0HYM2")
        series_map["High-yield credit spread"] = hy
    else:
        add("High-yield credit spread", "Credit", "n/a", "n/a", None, "Data unavailable", "FRED BAMLH0A0HYM2")

    nfci = fred.get("NFCI")
    if nfci is not None and len(nfci):
        v = float(nfci.iloc[-1])
        sig = 1 if v < 0 else -1 if v > 0 else 0
        add("Financial conditions (NFCI)", "Credit", f"{v:+.2f}", "", sig,
            "Below 0 = looser than average (+1); above 0 = tighter (−1)", "FRED NFCI")
        series_map["Financial conditions (NFCI)"] = nfci
    else:
        add("Financial conditions (NFCI)", "Credit", "n/a", "n/a", None, "Data unavailable", "FRED NFCI")

    hyg, lqd = yh("HYG"), yh("LQD")
    if hyg is not None and lqd is not None:
        ratio = (hyg / lqd).dropna()
        d = _pct_change(ratio, 3)
        sig = None if d is None else (1 if d > 0 else -1 if d < 0 else 0)
        add("High-yield vs investment-grade bonds", "Credit", f"{ratio.iloc[-1]:.3f}",
            f"{d:+.1f}% (3m)" if d is not None else "n/a", sig,
            "HYG outperforming LQD over 3m = +1; underperforming = −1", "Yahoo HYG / LQD")
    else:
        add("High-yield vs investment-grade bonds", "Credit", "n/a", "n/a", None, "Data unavailable", "Yahoo HYG / LQD")

    lend = fred.get("DRTSCILM")
    if lend is not None and len(lend):
        v = float(lend.iloc[-1])
        sig = 1 if v < 0 else -1 if v > 20 else 0
        add("Bank lending standards (C&I)", "Credit", f"{v:+.1f}%", "", sig,
            "Net easing (below 0) = +1; net tightening above 20% = −1", "FRED DRTSCILM")
    else:
        add("Bank lending standards (C&I)", "Credit", "n/a", "n/a", None, "Data unavailable", "FRED DRTSCILM")

    # Growth and labour
    ur = fred.get("UNRATE")
    if ur is not None and len(ur):
        d = float(ur.iloc[-1]) - (_ago(ur, 6) or float(ur.iloc[-1]))
        sig = 1 if d <= 0 else -1 if d >= 0.5 else 0
        add("Unemployment rate", "Growth", level(ur, lambda v: f"{v:.1f}%"), f"{d:+.1f} pp (6m)", sig,
            "Flat or falling = +1; rising ≥0.5 pp = −1", "FRED UNRATE")
    else:
        add("Unemployment rate", "Growth", "n/a", "n/a", None, "Data unavailable", "FRED UNRATE")

    claims = fred.get("ICSA")
    if claims is not None and len(claims) >= 52:
        ratio = float(claims.tail(4).mean()) / float(claims.tail(52).mean())
        sig = 1 if ratio <= 1.0 else -1 if ratio >= 1.10 else 0
        add("Jobless claims (4wk vs 52wk avg)", "Growth", f"{claims.tail(4).mean():,.0f}",
            f"{(ratio - 1) * 100:+.1f}%", sig, "At or below 52-week average = +1; ≥10% above = −1", "FRED ICSA")
    else:
        add("Jobless claims (4wk vs 52wk avg)", "Growth", "n/a", "n/a", None, "Data unavailable", "FRED ICSA")

    ip = fred.get("INDPRO")
    if ip is not None and len(ip) > 13:
        yoy = _pct_change(ip, 12)
        sig = 1 if yoy > 0 else -1 if yoy < -1 else 0
        add("Industrial production", "Growth", f"{yoy:+.1f}% YoY", "", sig,
            "Growing = +1; falling more than 1% = −1", "FRED INDPRO")
    else:
        add("Industrial production", "Growth", "n/a", "n/a", None, "Data unavailable", "FRED INDPRO")

    rs = fred.get("RSAFS")
    if rs is not None and len(rs) > 13:
        yoy = _pct_change(rs, 12)
        sig = 1 if yoy > 3 else -1 if yoy < 0 else 0
        add("Retail sales", "Growth", f"{yoy:+.1f}% YoY", "", sig,
            "Above 3% YoY = +1; negative = −1", "FRED RSAFS")
    else:
        add("Retail sales", "Growth", "n/a", "n/a", None, "Data unavailable", "FRED RSAFS")

    xly, xlp = yh("XLY"), yh("XLP")
    if xly is not None and xlp is not None:
        ratio = (xly / xlp).dropna()
        d = _pct_change(ratio, 3)
        sig = None if d is None else (1 if d > 0 else -1 if d < 0 else 0)
        add("Discretionary vs staples", "Growth", f"{ratio.iloc[-1]:.3f}",
            f"{d:+.1f}% (3m)" if d is not None else "n/a", sig,
            "Discretionary outperforming = +1 (growth appetite)", "Yahoo XLY / XLP")
    else:
        add("Discretionary vs staples", "Growth", "n/a", "n/a", None, "Data unavailable", "Yahoo XLY / XLP")

    # Inflation
    cpi = fred.get("CPIAUCSL")
    if cpi is not None and len(cpi) > 13:
        yoy = _pct_change(cpi, 12)
        sig = 1 if yoy < 3 else -1 if yoy > 4 else 0
        add("CPI inflation (YoY)", "Inflation", f"{yoy:.1f}%", "", sig,
            "Below 3% = +1; above 4% = −1", "FRED CPIAUCSL")
        series_map["CPI inflation (YoY)"] = cpi.pct_change(12).dropna() * 100
    else:
        add("CPI inflation (YoY)", "Inflation", "n/a", "n/a", None, "Data unavailable", "FRED CPIAUCSL")

    pce = fred.get("PCEPILFE")
    if pce is not None and len(pce) > 13:
        yoy = _pct_change(pce, 12)
        sig = 1 if yoy < 2.5 else -1 if yoy > 3.5 else 0
        add("Core PCE inflation (YoY)", "Inflation", f"{yoy:.1f}%", "", sig,
            "Below 2.5% = +1; above 3.5% = −1", "FRED PCEPILFE")
        series_map["Core PCE inflation (YoY)"] = pce.pct_change(12).dropna() * 100
    else:
        add("Core PCE inflation (YoY)", "Inflation", "n/a", "n/a", None, "Data unavailable", "FRED PCEPILFE")

    be = fred.get("T10YIE")
    if be is not None and len(be):
        v = float(be.iloc[-1])
        sig = 1 if v < 2.5 else -1 if v > 2.8 else 0
        add("10-year breakeven inflation", "Inflation", f"{v:.2f}%", "", sig,
            "Below 2.5% = +1; above 2.8% = −1", "FRED T10YIE")
    else:
        add("10-year breakeven inflation", "Inflation", "n/a", "n/a", None, "Data unavailable", "FRED T10YIE")

    # Market risk appetite
    vix = yh("^VIX")
    if vix is not None and len(vix) > 60:
        med = float(vix.tail(252).median())
        v = float(vix.iloc[-1])
        sig = 1 if v < med else -1 if v > 1.3 * med else 0
        add("VIX volatility", "Risk appetite", f"{v:.1f}", f"1y median {med:.1f}", sig,
            "Below 1-year median = +1; above 1.3× median = −1", "Yahoo ^VIX")
        series_map["VIX volatility"] = vix
    else:
        add("VIX volatility", "Risk appetite", "n/a", "n/a", None, "Data unavailable", "Yahoo ^VIX")

    spx = yh("^GSPC")
    if spx is not None and len(spx) > 200:
        ma = spx.rolling(200).mean()
        gap = (float(spx.iloc[-1]) / float(ma.iloc[-1]) - 1) * 100
        sig = 1 if gap > 0 else -1
        add("S&P 500 vs 200-day average", "Risk appetite", f"{gap:+.1f}%", "", sig,
            "Above the 200-day average = +1; below = −1", "Yahoo ^GSPC")
        series_map["S&P 500 vs 200-day average"] = (spx / ma - 1).dropna() * 100
    else:
        add("S&P 500 vs 200-day average", "Risk appetite", "n/a", "n/a", None, "Data unavailable", "Yahoo ^GSPC")

    rut = yh("^RUT")
    if rut is not None and spx is not None:
        ratio = (rut / spx).dropna()
        d = _pct_change(ratio, 3)
        sig = None if d is None else (1 if d > 0 else -1 if d < 0 else 0)
        add("Small caps vs large caps (Russell 2000 ÷ S&P 500)", "Risk appetite", f"{ratio.iloc[-1]:.3f}",
            f"{d:+.1f}% (3m)" if d is not None else "n/a", sig,
            "Small caps outperforming over 3m = +1 (key for this framework)", "Yahoo ^RUT / ^GSPC")
        series_map["Russell 2000 ÷ S&P 500"] = ratio
    else:
        add("Small caps vs large caps (Russell 2000 ÷ S&P 500)", "Risk appetite", "n/a", "n/a", None,
            "Data unavailable", "Yahoo ^RUT / ^GSPC")

    rsp, spy = yh("RSP"), yh("SPY")
    if rsp is not None and spy is not None:
        ratio = (rsp / spy).dropna()
        d = _pct_change(ratio, 3)
        sig = None if d is None else (1 if d > 0 else -1 if d < 0 else 0)
        add("Market breadth (equal-weight ÷ cap-weight)", "Risk appetite", f"{ratio.iloc[-1]:.3f}",
            f"{d:+.1f}% (3m)" if d is not None else "n/a", sig,
            "Equal-weight outperforming = +1 (broad participation)", "Yahoo RSP / SPY")
    else:
        add("Market breadth (equal-weight ÷ cap-weight)", "Risk appetite", "n/a", "n/a", None,
            "Data unavailable", "Yahoo RSP / SPY")

    dxy = yh("DX-Y.NYB")
    if dxy is not None and len(dxy) > 63:
        d = _pct_change(dxy, 3)
        sig = 1 if d < -1 else -1 if d > 2 else 0
        add("US dollar index", "Dollar and commodities", f"{float(dxy.iloc[-1]):.2f}", f"{d:+.1f}% (3m)", sig,
            "Weakening >1% over 3m = +1; strengthening >2% = −1", "Yahoo DX-Y.NYB")
        series_map["US dollar index"] = dxy
    else:
        add("US dollar index", "Dollar and commodities", "n/a", "n/a", None, "Data unavailable", "Yahoo DX-Y.NYB")

    cu = yh("HG=F")
    if cu is not None and len(cu) > 63:
        d = _pct_change(cu, 3)
        sig = 1 if d > 3 else -1 if d < -5 else 0
        add("Copper (3m trend)", "Dollar and commodities", f"{float(cu.iloc[-1]):.2f}", f"{d:+.1f}%", sig,
            "Up >3% over 3m = +1 (demand); down >5% = −1", "Yahoo HG=F")
        series_map["Copper"] = cu
    else:
        add("Copper (3m trend)", "Dollar and commodities", "n/a", "n/a", None, "Data unavailable", "Yahoo HG=F")

    for sym, label, rule in [
        ("CL=F", "Oil (3m trend)", "Information only: oil moves cut both ways"),
        ("GC=F", "Gold (3m trend)", "Information only: rises on fear or falling real rates"),
        ("BTC-USD", "Bitcoin (3m trend)", "Information only: speculative risk appetite"),
        ("TLT", "Long Treasuries (3m trend)", "Information only: duration moves"),
    ]:
        s = yh(sym)
        if s is not None and len(s) > 63:
            d = _pct_change(s, 3)
            add(label, "Dollar and commodities", f"{float(s.iloc[-1]):,.2f}", f"{d:+.1f}%", None, rule, f"Yahoo {sym}")
        else:
            add(label, "Dollar and commodities", "n/a", "n/a", None, "Data unavailable", f"Yahoo {sym}")

    scored = [r["signal"] for r in rows if r["signal"] is not None]
    score = sum(scored)
    ratio_score = score / len(scored) if scored else None
    if ratio_score is None:
        verdict = "Insufficient data"
    elif ratio_score >= 0.25:
        verdict = "Buy"
    elif ratio_score <= -0.25:
        verdict = "Sell"
    else:
        verdict = "Hold"
    info = {
        "verdict": verdict,
        "ratio": ratio_score,
        "risk_on": sum(1 for s in scored if s == 1),
        "risk_off": sum(1 for s in scored if s == -1),
        "neutral": sum(1 for s in scored if s == 0),
        "available": len(scored),
        "total": len(rows),
    }
    return rows, series_map, info


MACRO_SCORING_GUIDE = """
**How the regime is scored.** Each indicator gives +1 (Supportive), 0 (Neutral) or −1 (Adverse). The net score is the sum divided by the number of scored indicators. Information-only rows are not scored.

**Regime bands**: net score of +0.25 or higher = **Buy** (full target exposure to small caps); −0.25 or lower = **Sell** (reduce exposure); anything between = **Hold**.

**Rates**
- 10-year yield: falls more than 0.25 pp over 3 months = Supportive; rises more than 0.25 pp = Adverse.
- 10y minus 2y spread: above 0.25 pp = Supportive; below 0 (inverted) = Adverse.
- Fed funds, 6 months: cut of 0.25 pp or more = Supportive; hike of 0.25 pp or more = Adverse.
- 10-year real yield: below 1% = Supportive; above 2% = Adverse.

**Credit**
- High-yield spread, 3 months: narrows more than 0.2 pp = Supportive; widens more than 0.3 pp = Adverse.
- Financial conditions (NFCI): below 0 = Supportive; above 0 = Adverse.
- HYG versus LQD, 3 months: rising = Supportive; falling = Adverse.
- Bank lending standards: net easing (below 0) = Supportive; above 20% tightening = Adverse.

**Growth and labour**
- Unemployment, 6 months: flat or falling = Supportive; rises 0.5 pp or more = Adverse.
- Jobless claims, 4-week versus 52-week average: at or below 1.00 = Supportive; 10% or more above = Adverse.
- Industrial production, year on year: growing = Supportive; falling more than 1% = Adverse.
- Retail sales, year on year: above 3% = Supportive; negative = Adverse.
- Discretionary versus staples, 3 months: rising = Supportive (growth appetite); falling = Adverse.

**Inflation**
- CPI, year on year: below 3% = Supportive; above 4% = Adverse.
- Core PCE, year on year: below 2.5% = Supportive; above 3.5% = Adverse.
- 10-year breakeven inflation: below 2.5% = Supportive; above 2.8% = Adverse.

**Risk appetite**
- VIX versus its 1-year median: below = Supportive; above 1.3× = Adverse.
- S&P 500 versus its 200-day average: above = Supportive; below = Adverse.
- Russell 2000 versus S&P 500, 3 months: rising = Supportive; falling = Adverse.
- Equal-weight versus cap-weight S&P 500, 3 months: rising = Supportive; falling = Adverse.

**Dollar and commodities**
- Dollar index, 3 months: down more than 1% = Supportive; up more than 2% = Adverse.
- Copper, 3 months: up more than 3% = Supportive; down more than 5% = Adverse.
- Oil, gold, Bitcoin and long Treasuries are shown for information only.

**Market fear and greed** is a separate gauge: each of seven components is ranked within its last three years, and the gauge is the average. 0–25 extreme fear, 25–45 fear, 45–55 neutral, 55–75 greed, 75–100 extreme greed.

These thresholds are starting points, not back-tested rules.
"""

MACRO_GLOSSARY = {
    "Supportive": "An indicator that favours holding or adding small-cap exposure (formerly risk-on).",
    "Adverse": "An indicator that argues for reducing small-cap exposure (formerly risk-off).",
    "Net macro score": "Supportive signals minus Adverse signals, divided by the number of scored indicators. Ranges from −1 to +1; shown ×100 on the gauge.",
    "Regime": "The Buy, Hold or Sell verdict derived from the net macro score.",
    "Yield curve": "The gap between long and short Treasury yields. A normal curve slopes up; an inverted one has short yields above long yields, which has preceded slowdowns.",
    "Real yield": "A Treasury yield after inflation (TIPS). High real yields make borrowing and holding long-duration assets costlier.",
    "Breakeven inflation": "The inflation rate that bond markets imply, from the gap between nominal and inflation-protected Treasury yields.",
    "Fed funds rate": "The policy interest rate set by the Federal Reserve. Cuts ease financial conditions; hikes tighten them.",
    "High-yield spread": "Extra yield that risky corporate bonds pay over Treasuries. Widening spreads signal credit stress.",
    "NFCI": "Chicago Fed National Financial Conditions Index. Below 0 means looser conditions than average; above 0 means tighter.",
    "Lending standards": "Senior Loan Officer survey: the net share of banks tightening (positive) or easing (negative) business loans.",
    "Jobless claims": "Weekly initial unemployment insurance claims. A rising trend is an early sign of layoffs.",
    "PCE": "Personal Consumption Expenditures price index. The Fed's preferred inflation measure; the core version excludes food and energy.",
    "CPI": "Consumer Price Index: the headline measure of consumer inflation.",
    "VIX": "CBOE Volatility Index: the market's expected 30-day volatility of the S&P 500, implied by options. High readings mean fear.",
    "VIX term structure": "The VIX compared with the 3-month VIX. Normal (contango) means the 3-month is higher; inverted (backwardation) means near-term stress is priced above longer-term.",
    "Market breadth": "How many stocks take part in a rally. Equal-weight outperformance means gains are broad rather than led by a few mega caps.",
    "Small caps vs large caps": "The Russell 2000 divided by the S&P 500. Rising means small caps are leading, which tends to suit this framework.",
    "Risk appetite": "How willing investors are to hold riskier assets. Shown through volatility, credit, small caps, breadth and momentum.",
    "Momentum": "Where the S&P 500 sits relative to its moving average. Above the average suggests an uptrend.",
    "Dollar index": "Value of the US dollar against a basket of major currencies. A strong dollar tightens global financial conditions.",
    "Copper": "An industrial metal used as a proxy for global manufacturing demand.",
    "Fear & greed gauge": "A 0–100 score built from seven market measures, each ranked within its last three years. 0 is extreme fear, 100 is extreme greed.",
    "Percentile": "A component's rank within its own history. 80 means the current reading is higher than 80% of the last three years.",
    "FRED": "Federal Reserve Economic Data, the public database of US economic series used here.",
}


def _percentile_rank(series, invert=False):
    s = series.dropna().tail(756)
    if len(s) < 60:
        return None
    rank = float((s <= s.iloc[-1]).mean())
    return 1 - rank if invert else rank


def compute_fear_greed(px):
    """0 = extreme fear, 100 = extreme greed. Each component is ranked within its last 3 years."""
    def yh(sym):
        return px[sym].dropna() if (not px.empty and sym in px.columns) else None

    spx, spy, rsp = yh("^GSPC"), yh("SPY"), yh("RSP")
    vix, vix3m = yh("^VIX"), yh("^VIX3M")
    tlt, hyg, lqd, iwm = yh("TLT"), yh("HYG"), yh("LQD"), yh("IWM")

    def ratio(a, b):
        return (a / b).dropna() if a is not None and b is not None else None

    components = []

    def add(name, series, invert, reading):
        pct = _percentile_rank(series, invert) if series is not None else None
        components.append({
            "Component": name,
            "Latest": reading(series) if series is not None and len(series) else "n/a",
            "Greed percentile": round(pct * 100) if pct is not None else None,
        })

    add("VIX level (inverted)", vix, True, lambda s: f"{float(s.iloc[-1]):.1f}")
    add("VIX term structure, 1m ÷ 3m (inverted)", ratio(vix, vix3m), True,
        lambda s: f"{float(s.iloc[-1]):.2f}")
    add("Stocks vs Treasuries (SPY ÷ TLT)", ratio(spy, tlt), False, lambda s: f"{float(s.iloc[-1]):.2f}")
    add("Junk bond demand (HYG ÷ LQD)", ratio(hyg, lqd), False, lambda s: f"{float(s.iloc[-1]):.3f}")
    add("Market momentum (S&P vs 125-day avg)",
        (spx / spx.rolling(125).mean() - 1).dropna() * 100 if spx is not None else None, False,
        lambda s: f"{float(s.iloc[-1]):+.1f}%")
    add("Market breadth (RSP ÷ SPY)", ratio(rsp, spy), False, lambda s: f"{float(s.iloc[-1]):.3f}")
    add("Small-cap appetite (IWM ÷ SPY)", ratio(iwm, spy), False, lambda s: f"{float(s.iloc[-1]):.3f}")

    pcts = [c["Greed percentile"] for c in components if c["Greed percentile"] is not None]
    score = sum(pcts) / len(pcts) if pcts else None
    return score, components


def fear_greed_label(score):
    if score is None:
        return "Unavailable"
    if score < 25:
        return "Extreme fear"
    if score < 45:
        return "Fear"
    if score <= 55:
        return "Neutral"
    if score <= 75:
        return "Greed"
    return "Extreme greed"


def render_macro_tab():
    with st.spinner("Loading macro data…"):
        px = fetch_macro_prices()
        fred = {sid: fetch_fred(sid) for sid in MACRO_FRED}
    rows, series_map, info = compute_macro(px, fred)

    verdict = info["verdict"]
    color = {"Buy": "#2e7d32", "Hold": "#b26a00", "Sell": "#c62828"}.get(verdict, "#64748b")
    guidance = {
        "Buy": "Supportive. Macro supports full target exposure to small caps.",
        "Hold": "Neutral. Keep current exposure; add only on stock-level conviction.",
        "Sell": "Adverse. Macro argues for reducing small-cap exposure.",
        "Insufficient data": "Not enough indicators loaded to give a regime.",
    }[verdict]
    st.markdown(
        f'<div class="rpt-head">'
        f'<div><span class="rpt-badge" style="background:{color}">Macro regime: {html.escape(verdict)}</span>'
        f'<div class="rpt-sub">{html.escape(guidance)}</div></div>'
        f'<div class="rpt-score">{info["risk_on"]}<span> supportive · {info["risk_off"]} adverse · '
        f'{info["neutral"]} neutral of {info["available"]} scored</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.expander("📖 Macro scoring logic"):
        st.markdown(MACRO_SCORING_GUIDE)
    with st.expander("📚 Macro key terms"):
        st.markdown("\n\n".join(f"**{term}**: {meaning}" for term, meaning in MACRO_GLOSSARY.items()))

    fg_score, fg_components = compute_fear_greed(px)
    st.subheader("😨 Market Fear & Greed")
    fg_left, fg_right = st.columns([1, 2])
    with fg_left:
        fig_fg = go.Figure(go.Indicator(
            mode="gauge+number", value=fg_score if fg_score is not None else 0,
            number={"valueformat": ".0f"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#334155"},
                "steps": [
                    {"range": [0, 25], "color": "#fecaca"},
                    {"range": [25, 45], "color": "#fed7aa"},
                    {"range": [45, 55], "color": "#fef3c7"},
                    {"range": [55, 75], "color": "#d9f99d"},
                    {"range": [75, 100], "color": "#bbf7d0"},
                ],
            },
            title={"text": f"{fear_greed_label(fg_score)}"},
        ))
        fig_fg.update_layout(height=240, margin=dict(l=20, r=20, t=50, b=10))
        st.plotly_chart(fig_fg, use_container_width=True)
    with fg_right:
        st.dataframe(pd.DataFrame(fg_components), use_container_width=True, hide_index=True)
        st.caption(
            "Each component is ranked against its own last 3 years: 0 = most fearful, 100 = most greedy, "
            "and the gauge is the average. A self-built gauge, not CNN's index."
        )

    gauge_val = (info["ratio"] or 0) * 100
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=gauge_val,
        number={"suffix": "", "valueformat": ".0f"},
        gauge={
            "axis": {"range": [-100, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [-100, -25], "color": "#fecaca"},
                {"range": [-25, 25], "color": "#fef3c7"},
                {"range": [25, 100], "color": "#bbf7d0"},
            ],
        },
        title={"text": "Net macro score (−100 adverse … +100 supportive)"},
    ))
    fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=10))
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.subheader("Indicators")
    sig_text = {1: "🟢 Supportive", 0: "🟡 Neutral", -1: "🔴 Adverse", None: "ℹ️ Info / no data"}
    table = pd.DataFrame([{**{k: v for k, v in r.items() if k != "signal"}, "Signal": sig_text[r["signal"]]} for r in rows])
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.subheader("Trend charts")
    if series_map:
        choice = st.selectbox("Series", list(series_map.keys()), key="macro_series")
        s = series_map[choice]
        s = s[s.index >= s.index[-1] - pd.DateOffset(years=3)]
        fig_line = px_line(s, choice)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No series loaded for charting.")

    with st.expander("Symbols tracked (Yahoo Finance and FRED)"):
        st.dataframe(
            pd.DataFrame(MACRO_SYMBOLS, columns=["Symbol", "Name", "Source", "Used for"]),
            use_container_width=True, hide_index=True,
        )
    st.caption(
        "Macro overlay only, not investment advice. Thresholds are starting points, not tested rules: "
        "back-test them across past cycles before relying on them. Signals are updated when the data changes."
    )


def px_line(s, title):
    fig = go.Figure(go.Scatter(x=s.index, y=s.values, mode="lines", line=dict(color="#2962FF", width=2)))
    fig.update_layout(title=title, height=340, margin=dict(l=20, r=20, t=50, b=20), yaxis_title=title)
    return fig


# ── Indices and sector trends ───────────────────────────────────────────────

INDEX_UNIVERSE = (
    [(s, n, "Index / ETF") for s, n in [
        ("SPY", "S&P 500 ETF"), ("^GSPC", "S&P 500 index"), ("QQQ", "Nasdaq-100 ETF"), ("^NDX", "Nasdaq-100 index"),
        ("DIA", "Dow Jones ETF"), ("^DJI", "Dow Jones index"), ("IWM", "Russell 2000 ETF"), ("^RUT", "Russell 2000 index"),
        ("MDY", "S&P MidCap 400 ETF"), ("IJR", "S&P SmallCap 600 ETF"), ("RSP", "S&P 500 equal-weight ETF"),
        ("EFA", "Developed markets ex-US"), ("EEM", "Emerging markets"), ("^FTSE", "FTSE 100 (UK)"),
        ("^GDAXI", "DAX (Germany)"), ("^N225", "Nikkei 225 (Japan)"), ("^HSI", "Hang Seng (Hong Kong)"),
    ]]
    + [(s, n, "Sector") for s, n in [
        ("XLK", "Technology"), ("XLF", "Financials"), ("XLV", "Health care"), ("XLE", "Energy"),
        ("XLI", "Industrials"), ("XLY", "Consumer discretionary"), ("XLP", "Consumer staples"),
        ("XLU", "Utilities"), ("XLB", "Materials"), ("XLRE", "Real estate"), ("XLC", "Communication services"),
    ]]
    + [(s, n, "Theme") for s, n in [
        ("SMH", "Semiconductors"), ("XBI", "Biotech"), ("KRE", "Regional banks"), ("XHB", "Homebuilders"),
        ("ITA", "Aerospace & defence"), ("XME", "Metals & mining"), ("GDX", "Gold miners"), ("URA", "Uranium"),
        ("ICLN", "Clean energy"), ("IGV", "Software"),
    ]]
)

# (key, label, trading days, moving average used for the price check)
HORIZONS = [("Primary", "2 years", 504, 200), ("Secondary", "9 months", 189, 100), ("Tertiary", "3 months", 63, 50)]


COMMODITY_UNIVERSE = (
    [(s, n, "Precious metals") for s, n in [("GC=F", "Gold"), ("SI=F", "Silver"), ("PL=F", "Platinum"), ("PA=F", "Palladium")]]
    + [(s, n, "Industrial metals") for s, n in [("HG=F", "Copper"), ("ALI=F", "Aluminium")]]
    + [(s, n, "Energy") for s, n in [("CL=F", "WTI crude oil"), ("BZ=F", "Brent crude oil"), ("NG=F", "Natural gas"),
                                     ("HO=F", "Heating oil"), ("RB=F", "Gasoline")]]
    + [(s, n, "Agriculture") for s, n in [("ZC=F", "Corn"), ("ZW=F", "Wheat"), ("ZS=F", "Soybeans"), ("KC=F", "Coffee"),
                                          ("SB=F", "Sugar"), ("CT=F", "Cotton"), ("CC=F", "Cocoa")]]
    + [(s, n, "Commodity ETFs") for s, n in [("GLD", "Gold ETF"), ("SLV", "Silver ETF"), ("DBC", "Broad commodity ETF"),
                                             ("USO", "Oil ETF"), ("UNG", "Natural gas ETF"), ("CPER", "Copper ETF"),
                                             ("LIT", "Lithium ETF")]]
)

MARKETS = {
    "indices": dict(title="Indices, Sectors & Themes", subtitle="Major indices, sector ETFs and thematic ETFs",
                    universe=INDEX_UNIVERSE, bench="SPY", bar_group="Sector"),
    "commodities": dict(title="Commodities", subtitle="Metals, energy, agriculture and commodity ETFs",
                        universe=COMMODITY_UNIVERSE, bench="DBC", bar_group=None),
}
HORIZON_SHORT = {"Primary": "2Y", "Secondary": "9M", "Tertiary": "3M"}


@st.cache_data(ttl=3600)
def fetch_trend_prices(symbols):
    try:
        data = yf.download(list(symbols), period="5y", interval="1d", auto_adjust=True, progress=False)
        close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
        return close.dropna(how="all")
    except Exception:
        return pd.DataFrame()


def _rsi_macd(close):
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rsi = 100 - 100 / (1 + gain / loss)
    macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    hist = macd - macd.ewm(span=9, adjust=False).mean()
    return rsi, hist


def _confirmed_state(cond, confirm=3):
    """Bullish once the condition has held for `confirm` days in a row, Bearish once it has been false that long."""
    vals = cond.dropna().astype(bool)
    state, since = None, None
    for i in range(confirm - 1, len(vals)):
        window = vals.iloc[i - confirm + 1: i + 1]
        if window.all():
            new = "Bullish"
        elif not window.any():
            new = "Bearish"
        else:
            continue
        if new != state:
            state, since = new, vals.index[i]
    return state, since


def _breakout_state(close, up=55, down=20):
    """Bullish on a close above the prior 55-day high, Bearish on a close below the prior 20-day low."""
    hi = close.shift(1).rolling(up).max()
    lo = close.shift(1).rolling(down).min()
    state, since = None, None
    for date, c, h, l in zip(close.index, close.values, hi.values, lo.values):
        if np.isnan(h) or np.isnan(l):
            continue
        if c > h:
            new = "Bullish"
        elif c < l:
            new = "Bearish"
        else:
            continue
        if new != state:
            state, since = new, date
    return state, since


def analyse_index(close, bench=None):
    if len(close) < 260:
        return None
    rsi, hist = _rsi_macd(close)
    smas = {w: close.rolling(w).mean() for w in (50, 100, 200)}
    last = float(close.iloc[-1])
    out = {
        "price": last,
        "rsi": float(rsi.iloc[-1]),
        "macd": float(hist.iloc[-1]),
        "vs50": (last / smas[50].iloc[-1] - 1) * 100 if pd.notna(smas[50].iloc[-1]) else None,
        "vs200": (last / smas[200].iloc[-1] - 1) * 100 if pd.notna(smas[200].iloc[-1]) else None,
    }
    for key, _, n, w in HORIZONS:
        ma = smas[w]
        if len(close) <= n or pd.isna(ma.iloc[-1]) or pd.isna(ma.iloc[-1 - n]):
            out[key] = None
            continue
        ret = last / float(close.iloc[-1 - n]) - 1
        checks = [
            ret > 0,
            last > ma.iloc[-1],
            ma.iloc[-1] > ma.iloc[-1 - n],
            hist.iloc[-1] > 0,
        ]
        score = sum(checks)
        window = close.iloc[-(n + 1):]
        hi, lo = float(window.max()), float(window.min())
        pos = (last - lo) / (hi - lo) * 100 if hi > lo else 50.0
        status = "Overbought" if pos >= 80 else "Oversold" if pos <= 20 else "Neutral"
        out[key] = {"ret": ret * 100, "score": score, "trend": "Bullish" if score >= 3 else "Bearish",
                    "pos": pos, "status": status}
    ma_cond = (smas[50] > smas[200]).where(smas[50].notna() & smas[200].notna())
    out["sig_ma"] = _confirmed_state(ma_cond)
    out["sig_bo"] = _breakout_state(close)
    if bench is not None:
        ratio = (close / bench).dropna()
        out["sig_rs"] = _confirmed_state(ratio > ratio.rolling(50).mean())
    else:
        out["sig_rs"] = (None, None)
    return out


def _ret_text(h):
    return "n/a" if h is None else f"{h['ret']:+.1f}%"


def _trend_label(h):
    return "n/a" if h is None else f"{h['trend']} {h['score']}/4"


def _range_label(h):
    return "n/a" if h is None else f"{h['status']} · {h['pos']:.0f}%"


def _signal_label(sig):
    state, since = sig
    return "n/a" if state is None else f"{state} · since {since:%Y-%m-%d}"


def _style_labels(df, cols=None):
    def color(v):
        if not isinstance(v, str):
            return ""
        if v.startswith("Bullish"):
            return "background-color:#bbf7d0;color:#14532d;font-weight:600;border-radius:6px"
        if v.startswith("Bearish"):
            return "background-color:#fecaca;color:#7f1d1d;font-weight:600;border-radius:6px"
        if v.startswith("Overbought"):
            return "background-color:#fed7aa;color:#7c2d12;font-weight:600;border-radius:6px"
        if v.startswith("Oversold"):
            return "background-color:#bfdbfe;color:#1e3a8a;font-weight:600;border-radius:6px"
        return ""
    label_cols = cols or [c for c in df.columns if c.endswith(("trend", "range"))]
    return df.style.map(color, subset=label_cols).hide(axis="index")


def _short_status(h):
    return {"Overbought": "OB", "Oversold": "OS"}.get(h["status"], "Mid")


def _tile_html(r):
    chips, rng, rets = [], [], []
    for key, _, _, _ in HORIZONS:
        short, h = HORIZON_SHORT[key], r[key]
        if h is None:
            chips.append(f'<span class="chip-na">{short} n/a</span>')
            rng.append(f'<span class="chip-na">{short} n/a</span>')
            rets.append(f"{short} n/a")
            continue
        cls = "chip-bull" if h["trend"] == "Bullish" else "chip-bear"
        chips.append(f'<span class="{cls}">{short} {h["trend"]} {h["score"]}/4</span>')
        rcls = {"Overbought": "chip-ob", "Oversold": "chip-os"}.get(h["status"], "chip-mid")
        rng.append(f'<span class="{rcls}">{short} {_short_status(h)} {h["pos"]:.0f}%</span>')
        rets.append(f'{short} {h["ret"]:+.0f}%')
    return (
        f'<div class="tile"><div class="tile-top"><div>'
        f'<div class="tile-name">{html.escape(r["Name"])}</div>'
        f'<div class="tile-sym">{html.escape(r["Symbol"])} · {html.escape(r["Group"])}</div></div>'
        f'<div class="tile-price">{r["price"]:,.2f}</div></div>'
        f'<div class="tile-row">{"".join(chips)}</div>'
        f'<div class="tile-row">{"".join(rng)}</div>'
        f'<div class="tile-ret">{" · ".join(rets)}</div></div>'
    )


def render_trend_tab(market):
    cfg = MARKETS[market]
    bench_sym = cfg["bench"]
    symbols = tuple([s for s, _, _ in cfg["universe"]] + [bench_sym])
    with st.spinner(f"Loading {cfg['title'].lower()}…"):
        px = fetch_trend_prices(symbols)
    bench_close = px[bench_sym].dropna() if (not px.empty and bench_sym in px.columns) else None

    groups = ["All"] + list(dict.fromkeys(g for _, _, g in cfg["universe"]))
    group_filter = st.radio("Show", groups, horizontal=True, key=f"{market}_group")

    rows, closes, missing = [], {}, []
    for sym, name, group in cfg["universe"]:
        if px.empty or sym not in px.columns:
            missing.append(sym)
            continue
        close = px[sym].dropna()
        m = analyse_index(close, bench_close if sym != bench_sym else None)
        if m is None:
            missing.append(sym)
            continue
        rows.append({"Name": name, "Symbol": sym, "Group": group, **m})
        closes[sym] = close
    shown = [r for r in rows if group_filter == "All" or r["Group"] == group_filter]

    st.markdown(
        f'<div class="mk-head"><div class="mk-kicker">{len(shown)} instruments · benchmark {html.escape(bench_sym)}</div>'
        f'<div class="mk-title">{html.escape(cfg["title"])}</div>'
        f'<div class="mk-sub">{html.escape(cfg["subtitle"])}. Trend, range position and turn signals across three horizons.</div></div>',
        unsafe_allow_html=True,
    )

    cards = []
    for key, label, _, _ in HORIZONS:
        valid = [r for r in shown if r[key] is not None]
        bull = sum(1 for r in valid if r[key]["trend"] == "Bullish")
        ob = sum(1 for r in valid if r[key]["status"] == "Overbought")
        os_ = sum(1 for r in valid if r[key]["status"] == "Oversold")
        cards.append(
            f'<div class="sum-card"><div class="sum-h">{key} · {label}</div>'
            f'<div class="sum-big">{bull} / {len(valid)}</div><div class="sum-small">bullish trend</div>'
            f'<div class="sum-chips"><span class="chip-ob">{ob} overbought</span>'
            f'<span class="chip-os">{os_} oversold</span></div></div>'
        )
    st.markdown('<div class="sum-row">' + "".join(cards) + "</div>", unsafe_allow_html=True)

    if shown:
        st.subheader("Market map")
        st.markdown('<div class="tile-grid">' + "".join(_tile_html(r) for r in shown) + "</div>",
                    unsafe_allow_html=True)
        st.subheader("Turn signals")
        st.caption("Three rules that flag a trend changing direction, each with its current state and the date it last flipped.")
        sig_rows = []
        for r in shown:
            states = [r[k][0] for k in ("sig_ma", "sig_bo", "sig_rs") if r[k][0] is not None]
            bull = sum(1 for s in states if s == "Bullish")
            sig_rows.append({
                "Name": r["Name"],
                "Symbol": r["Symbol"],
                "MA cross 50/200": _signal_label(r["sig_ma"]),
                "Breakout 55/20": _signal_label(r["sig_bo"]),
                f"Rel. strength vs {bench_sym}": _signal_label(r["sig_rs"]),
                "Bullish rules": f"{bull} / {len(states)}" if states else "n/a",
            })
        sig_cols = ["MA cross 50/200", "Breakout 55/20", f"Rel. strength vs {bench_sym}"]
        st.dataframe(_style_labels(pd.DataFrame(sig_rows), cols=sig_cols), use_container_width=True)

        options = {f"{r['Name']} ({r['Symbol']})": r["Symbol"] for r in shown}
        st.subheader("Trend chart")
        pick = options[st.selectbox("Instrument", list(options.keys()), key=f"{market}_pick")]
        close = closes[pick]
        view = close[close.index >= close.index[-1] - pd.DateOffset(years=3)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=view.index, y=view.values, name="Price", line=dict(color="#0f172a", width=2)))
        for w, color in [(50, "#2962FF"), (100, "#FF9100"), (200, "#15803d")]:
            ma = close.rolling(w).mean()
            fig.add_trace(go.Scatter(x=view.index, y=ma.reindex(view.index).values, name=f"{w}-day average",
                                     line=dict(color=color, width=1.4, dash="dot")))
        for label, n, shade in [("Tertiary 3M", 63, "rgba(41,98,255,0.08)"),
                                ("Secondary 9M", 189, "rgba(255,145,0,0.06)"),
                                ("Primary 2Y", 504, "rgba(21,128,61,0.05)")]:
            if len(close) > n:
                fig.add_vrect(x0=close.index[-1 - n], x1=close.index[-1], fillcolor=shade, line_width=0,
                              annotation_text=label, annotation_position="top left")
        fig.update_layout(height=420, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.08))
        st.plotly_chart(fig, use_container_width=True)

        bar_rows = [r for r in shown
                    if (cfg["bar_group"] is None or r["Group"] == cfg["bar_group"])
                    and all(r[k] is not None for k, _, _, _ in HORIZONS)]
        if bar_rows:
            st.subheader("Returns by horizon")
            fig_b = go.Figure()
            for key, label, color in [("Tertiary", "3 months", "#2962FF"), ("Secondary", "9 months", "#FF9100"),
                                      ("Primary", "2 years", "#15803d")]:
                fig_b.add_trace(go.Bar(name=label, x=[r["Name"] for r in bar_rows],
                                       y=[r[key]["ret"] for r in bar_rows], marker_color=color))
            fig_b.update_layout(barmode="group", height=380, margin=dict(l=20, r=20, t=30, b=20), yaxis_title="Return (%)")
            st.plotly_chart(fig_b, use_container_width=True)

        with st.expander("Full detail table"):
            table = pd.DataFrame([{
                "Name": r["Name"], "Symbol": r["Symbol"], "Group": r["Group"],
                "Price": f"{r['price']:,.2f}",
                "RSI(14)": f"{r['rsi']:.0f}",
                "MACD": "▲ positive" if r["macd"] > 0 else "▼ negative",
                "vs 50D": f"{r['vs50']:+.1f}%" if r["vs50"] is not None else "n/a",
                "vs 200D": f"{r['vs200']:+.1f}%" if r["vs200"] is not None else "n/a",
                "2Y return": _ret_text(r["Primary"]), "2Y trend": _trend_label(r["Primary"]), "2Y range": _range_label(r["Primary"]),
                "9M return": _ret_text(r["Secondary"]), "9M trend": _trend_label(r["Secondary"]), "9M range": _range_label(r["Secondary"]),
                "3M return": _ret_text(r["Tertiary"]), "3M trend": _trend_label(r["Tertiary"]), "3M range": _range_label(r["Tertiary"]),
            } for r in shown])
            st.dataframe(_style_labels(table), use_container_width=True)

        with st.expander("How trends are assigned"):
            st.markdown(
                "**Horizons.** Primary = 2 years (504 trading days), secondary = 9 months (189), tertiary = 3 months (63).\n\n"
                "**Four checks per horizon:** (1) return over the horizon is positive; (2) price is above its moving average for that horizon "
                "(200-day, 100-day, 50-day); (3) that moving average is rising over the horizon; (4) MACD histogram is positive.\n\n"
                "**Bullish** = 3 or 4 checks passed. **Bearish** = 0–2 passed. The score shows how many passed.\n\n"
                "**Overbought / oversold (range position).** Where today's price sits between the horizon's high and low: "
                "0% = at the low, 100% = at the high. **80%+ = Overbought; 20%− = Oversold.**\n\n"
                "**Turn signals.** MA cross 50/200 (confirmed 3 days); breakout above the prior 55-day high or below the prior 20-day low; "
                f"relative strength vs {bench_sym} (ratio above its 50-day average, confirmed 3 days).\n\n"
                "**Other indicators.** RSI(14) is a 14-day momentum measure (above 70 overbought, below 30 oversold). "
                "'vs 50D' and 'vs 200D' show distance from those averages."
            )
    else:
        st.info("No price history loaded for this group.")
    if missing:
        st.caption(f"No data returned for: {', '.join(missing)}.")
    st.caption("Mechanical technical reads from Yahoo Finance data, not investment advice. "
               "Futures are continuous contracts, so prices can jump when the front month rolls.")


# ── Main area ───────────────────────────────────────────────────────────────

n_stocks = len(st.session_state.watchlist)
pillar_chips = "".join(f"<span>{html.escape(p)}</span>" for p in PILLARS)
st.markdown(
    f'<div class="app-banner">'
    f'<div class="app-kicker">QUANTITATIVE SCREEN · {n_stocks} STOCK{"S" if n_stocks != 1 else ""} IN WATCHLIST</div>'
    f'<div class="app-title">📈 Stock Valuation Framework</div>'
    f'<div class="app-sub">Score stocks on the principles from <i>100 Baggers</i>, Ian Cassel, Peter Lynch, '
    f'Phil Fisher and Greenblatt.</div>'
    f'<div class="app-chips">{pillar_chips}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

with st.expander("How to use this app"):
    st.markdown(
        "1. Add tickers in the sidebar.\n"
        "2. Pick a stock's tab and read its framework score (70%+ = worth researching).\n"
        "3. Review the valuation, growth and balance-sheet detail.\n"
        "4. Cross-check anything promising against the 10-K and 10-Q.\n\n"
        "Hover the ⓘ icons for metric definitions, or open the glossary in the sidebar."
    )

top_stocks, top_macro, top_indices, top_commodities = st.tabs(["📈 Stocks", "🌐 Macro", "📊 Indices", "🛢️ Commodities"])

with top_stocks:
    render_watchlist_panel()
    if not st.session_state.watchlist:
        st.markdown(
            '<div class="empty-state"><div class="big">📭</div>'
            '<div class="head">No stocks to analyse yet</div>'
            'Add a ticker above to see its framework score, valuation models and report.</div>',
            unsafe_allow_html=True,
        )
    else:
        # One tab per stock — clicking the tab loads that stock's full analysis
        tabs = st.tabs([f"{t}" for t in st.session_state.watchlist])
        for tab, ticker_sym in zip(tabs, st.session_state.watchlist):
            with tab:
                show_stock_tab(ticker_sym)

    st.markdown("---")
    with st.expander("📖 Scoring logic"):
        st.markdown(SCORING_GUIDE)
    with st.expander("📚 Key terms"):
        st.markdown("\n\n".join(f"**{term}**: {meaning}" for term, meaning in GLOSSARY.items()))

with top_macro:
    render_macro_tab()

with top_indices:
    render_trend_tab("indices")

with top_commodities:
    render_trend_tab("commodities")
