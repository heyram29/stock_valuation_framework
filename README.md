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

## How to run

```bash
pip install -r requirements.txt
streamlit run microcap_framework_dashboard.py
```

Then open the local URL (usually http://localhost:8501), enter a ticker, and click **Analyze Stock**.

## Notes
- Best for US-listed stocks. Micro/small-caps often have incomplete data.
- Insider ownership and some ratios can be missing for the smallest names.
- This is a quantitative screen only — always do qualitative work (filings, management, competitive position) on anything that scores well.
- Not investment advice.
