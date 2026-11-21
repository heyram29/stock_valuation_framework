# Stock Valuation Framework

Interactive Streamlit app that scores a stock against the common principles from *100 Baggers*, Ian Cassel, Peter Lynch, Phil Fisher, Greenblatt, Wanger and related works.

## Framework pillars scored (16 points)
- Quality, 4 pts (ROIC with ROE fallback, operating margin, gross margin / pricing power)
- Management alignment, 3 pts (insider ownership; excluded from the total if the data is missing)
- Growth runway, 3 pts (revenue/earnings growth)
- Valuation discipline, 3 pts (PEG, EV/sales, EV/EBITDA, FCF yield; loss-makers use EV/sales vs growth, runway, net cash)
- Risk / balance sheet, 3 pts (debt/equity, net cash, share dilution penalty)

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
