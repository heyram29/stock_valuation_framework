# Stock Valuation Framework

Interactive Streamlit app that scores a stock against the common principles from *100 Baggers*, Ian Cassel, Peter Lynch, Phil Fisher, Greenblatt, Wanger and related works.

## Framework pillars scored (24 points)
- Quality, 3 pts (operating margin, gross margin level, gross margin trend)
- Capital allocation, 3 pts (ROIC with ROE fallback; 1 pt for returns of 10%+ while growing)
- Management alignment, 3 pts (insider ownership; excluded from the total if the data is missing)
- Growth runway, 4 pts (revenue growth, earnings growth or hyper-growth stand-in, consistency of quarterly growth)
- Valuation discipline, 3 pts (PEG, EV/sales, EV/EBITDA, FCF yield; loss-makers use EV/sales vs growth, runway, net cash)
- Risk / balance sheet, 3 pts (debt/equity, net cash; -1 pt when short interest is above 20% of float)
- Dilution, 2 pts (change in share count over 3 years)
- Cash quality, 2 pts (positive free cash flow; free cash flow at least 80% of net income)
- Smart money, 2 pts (1 pt for net insider buying over the last 12 months; 1 pt for more top-10 institutional holders adding shares than trimming in the latest quarter)

Each stock tab starts with a short summary report, which can be downloaded as Markdown.

## Macro tab
A separate tab that scores the macro regime (Buy / Hold / Sell) from rates, credit, growth, inflation, risk appetite, the dollar and commodities. It uses Yahoo Finance tickers and FRED series, and needs no API key. The full symbol list is in the tab. Signal thresholds are starting points and should be back-tested before use.

## Valuation models for loss-making growers
- Probability-weighted scenarios: bear, base and bull cases, weighted by your odds.
- Reverse DCF: the revenue growth the current price already assumes.
- Peer growth regression: EV/Sales fitted against revenue growth across peers you enter.

## Installation

Requires Python 3.10 or newer.

1. Clone the repository and go to the folder:
   ```bash
   git clone https://github.com/heyram29/stock_valuation_framework.git
   cd stock_valuation_framework
   ```
2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   source .venv/bin/activate       # macOS / Linux
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to run

```bash
streamlit run microcap_framework_dashboard.py
```

Streamlit prints a local address, normally http://localhost:8501. If that port is busy it uses the next free one. Open the address, enter a ticker on the Stocks tab, and click **Analyze Stock**.

On Windows with Anaconda, run `C:\Users\<you>\anaconda3\Scripts\streamlit.exe run microcap_framework_dashboard.py` so the app uses the Python that has the dependencies installed.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'yfinance'`**: the dependencies are installed in a different Python. Install them with the same `pip` (or use the Anaconda `streamlit.exe` above).
- **Stocks tab shows "Could not load data"**: Yahoo Finance is rate-limiting or refusing the connection. Wait a minute and reload. Hosted servers are often blocked by Yahoo, so this usually works only on a home computer.
- **Yahoo `401 Invalid Crumb` lines in the log**: yfinance prints these when Yahoo refuses a request. They are harmless if the data still loads.

## Notes
- Best for US-listed stocks. Micro/small-caps often have incomplete data.
- Insider ownership and some ratios can be missing for the smallest names.
- This is a quantitative screen only — always do qualitative work (filings, management, competitive position) on anything that scores well.
- Not investment advice.
