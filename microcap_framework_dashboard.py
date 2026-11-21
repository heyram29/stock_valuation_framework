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
    initial_sidebar_state="expanded"
)

# ── Custom CSS Styling ──────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Pull the page and sidebar content up toward the top edge */
    .block-container {
        padding-top: 1rem !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0.75rem;
    }
    h1 {
        margin-top: 0 !important;
    }

    /* Compact sidebar watchlist rows */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.4rem;
    }
    [data-testid="stSidebar"] .stButton > button {
        padding: 0.2rem 0.5rem;
        font-size: 0.85rem;
        border-radius: 6px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: none;
        box-shadow: none;
    }

    /* Metric cards enhancement */
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #2962FF;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }

    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Title styling */
    h1 {
        color: #1a237e;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    h2, h3 {
        color: #1a237e;
        font-weight: 600;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] button {
        font-weight: 600;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        margin-right: 0.5rem;
    }

    /* Alert boxes */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 8px;
        padding: 1rem;
        font-weight: 500;
    }

    /* Dataframe styling */
    [data-testid="dataframe"] {
        font-size: 0.95rem;
    }

    /* Divider */
    hr {
        margin: 2rem 0;
        border: 1px solid #e0e0e0;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* Tabs: underline the active tab instead of boxing it */
    .stTabs [data-baseweb="tab-list"] button {
        border-radius: 8px 8px 0 0;
        padding: 0.6rem 1.1rem;
        margin-right: 0.25rem;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        height: 3px;
        border-radius: 3px;
    }

    /* Summary report header */
    .rpt-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }
    .rpt-badge {
        display: inline-block;
        color: #ffffff;
        border-radius: 999px;
        padding: 0.3rem 0.9rem;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .rpt-sub {
        color: #5f6368;
        font-size: 0.9rem;
        margin-top: 0.35rem;
    }
    .rpt-score {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1a237e;
        line-height: 1;
    }
    .rpt-score span {
        font-size: 0.95rem;
        font-weight: 600;
        color: #5f6368;
    }

    /* Hero card at the top of each stock tab */
    .hero {
        background: linear-gradient(135deg, #1a237e 0%, #2962FF 100%);
        color: #ffffff;
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 14px rgba(26,35,126,0.25);
    }
    .hero-ticker {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        border-radius: 6px;
        padding: 0.1rem 0.55rem;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    .hero-name {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0.4rem 0 0.2rem 0;
    }
    .hero-meta {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .hero-pill {
        display: inline-block;
        background: #ffffff;
        color: #1a237e;
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        font-weight: 700;
        margin-top: 0.6rem;
    }
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

# ── Session state init ──────────────────────────────────────────────────────
if "watchlist" not in st.session_state:
    st.session_state.watchlist = load_saved_watchlist()

# ── Sidebar: watchlist manager ──────────────────────────────────────────────
with st.sidebar:
    with st.form("add_ticker", clear_on_submit=True, border=False):
        new_ticker_input = st.text_input(
            "Add a ticker",
            placeholder="e.g. RKLB, NBIS, AAPL",
        )
        submitted = st.form_submit_button("➕ Add to watchlist", type="primary", use_container_width=True)
    if submitted:
        t = new_ticker_input.upper().strip()
        if not t:
            st.warning("Enter a ticker symbol first.")
        elif t in st.session_state.watchlist:
            st.warning(f"{t} is already in your watchlist.")
        else:
            st.session_state.watchlist.append(t)
            save_watchlist(st.session_state.watchlist)
            st.rerun()

    if st.session_state.watchlist:
        for t in list(st.session_state.watchlist):
            col_name, col_btn = st.columns([4, 1], vertical_alignment="center")
            col_name.markdown(f"**{html.escape(t)}**")
            if col_btn.button("✕", key=f"remove_{t}", help=f"Remove {t}"):
                st.session_state.watchlist.remove(t)
                save_watchlist(st.session_state.watchlist)
                st.rerun()
    else:
        st.info("Your watchlist is empty.")
        if st.button("🔄 Reset to default (RKLB)", use_container_width=True):
            st.session_state.watchlist = ["RKLB"]
            save_watchlist(st.session_state.watchlist)
            st.rerun()

    st.markdown("---")
    st.caption("💾 Saved automatically • Data from Yahoo Finance")

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


def build_report_parts(ticker, name, sector, price, mcap, scores, maxes, explanations, score_pct, is_loss_making, runway_months, dilution_pct, flow):
    """Structured summary of the scoring, built from the same numbers shown on screen."""
    total, possible = sum(scores.values()), sum(maxes.values())
    gaps = [c for c in PILLARS if not maxes[c]]
    facts = [("Pillars scored", f"{len(PILLARS) - len(gaps)}/{len(PILLARS)}")]
    if runway_months is not None:
        facts.append(("Cash runway", f"~{runway_months:.0f} mo"))
    if dilution_pct is not None:
        facts.append(("Share change, 3y", f"{dilution_pct:+.0f}%"))
    if flow.get("ins_ok"):
        facts.append(("Insider trades, 12m", f"{flow['buy_n']} buys · {flow['sell_n']} sales"))
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
    lines.append("**Key facts:** " + "; ".join(f"{k}: {v}" for k, v in p["facts"] if k != "Pillars scored") + ".")
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

    for col, (label, value) in zip(st.columns(len(p["facts"])), p["facts"]):
        col.metric(label, md_safe(value))

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
                                score_pct, is_loss_making, runway_months, dilution_pct, flow)
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

        st.metric(f"{score_color} Framework Score", f"{total_score}/{total_possible}")
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
            st.metric("📊 Trailing P/E", pe_val)
            if pe and pe > 0 and not is_loss_making:
                st.caption("Low ✅" if pe < 20 else "Fair 🟡" if pe < 40 else "High ⚠️")
        with c2:
            fpe_val = format_number(forward_pe) if not is_loss_making else "N/A"
            st.metric("📊 Forward P/E", fpe_val)
        with c3:
            peg_val = format_number(peg) if not is_loss_making else "N/A"
            st.metric("📈 PEG Ratio", peg_val)
            if peg and peg > 0 and not is_loss_making:
                st.caption("Cheap ✅" if peg < 1 else "Fair 🟡" if peg < 1.5 else "Rich ⚠️")
        with c4:
            ps_val = format_number(ps)
            st.metric("🏷️ P/S (TTM)", ps_val)
            if ps and ps > 0:
                st.caption("Low ✅" if ps < 3 else "Fair 🟡" if ps < 6 else "High ⚠️")

        # Row 2
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            ev_ebitda_val = format_number(ev_ebitda) if not is_loss_making else "N/A"
            st.metric("🏢 EV/EBITDA", ev_ebitda_val)
            if ev_ebitda and ev_ebitda > 0 and not is_loss_making:
                st.caption("Cheap ✅" if ev_ebitda < 10 else "Fair 🟡" if ev_ebitda < 15 else "Rich ⚠️")
        with c6:
            ev_rev_val = format_number(ev_rev)
            st.metric("🏢 EV/Revenue", ev_rev_val)
            if ev_rev and ev_rev > 0:
                st.caption("Low ✅" if ev_rev < 2 else "Fair 🟡" if ev_rev < 4 else "High ⚠️")
        with c7:
            pb_val = format_number(pb)
            st.metric("📚 P/B", pb_val)
        with c8:
            fcf_yield_val = format_number(fcf_yield, is_pct=True)
            st.metric("💵 FCF Yield", fcf_yield_val)
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
            st.metric("⏱️ Cash Runway", runway_str_val)
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


# ── Main area ───────────────────────────────────────────────────────────────

st.title("📈 Stock Valuation Framework")
st.markdown(
    "Score stocks on the principles from *100 Baggers*, Ian Cassel, Peter Lynch, Phil Fisher and Greenblatt: "
    "**Quality · Management · Growth · Valuation · Risk**"
)

with st.expander("How to use this app"):
    st.markdown(
        "1. Add tickers in the sidebar.\n"
        "2. Pick a stock's tab and read its framework score (70%+ = worth researching).\n"
        "3. Review the valuation, growth and balance-sheet detail.\n"
        "4. Cross-check anything promising against the 10-K and 10-Q."
    )

st.markdown("---")

if not st.session_state.watchlist:
    st.info("👈 Add a ticker in the sidebar to get started.")
else:
    # One tab per stock — clicking the tab loads that stock's full analysis
    tab_labels = [f"{t}" for t in st.session_state.watchlist]
    tabs = st.tabs(tab_labels)
    for tab, ticker_sym in zip(tabs, st.session_state.watchlist):
        with tab:
            show_stock_tab(ticker_sym)
