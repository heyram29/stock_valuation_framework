# Trend logic: Bullish, Bearish, Neutral and turn signals

This describes how the Indices and Commodities tabs and the stock trend filter classify each instrument. The thresholds below match the code. Prices are daily closes from Yahoo Finance, adjusted for splits and dividends (`auto_adjust=True`).

## 1. Horizons

| Horizon | Lookback | Trading days | Moving average used in the trend check |
|---|---|---|---|
| Primary | 2 years | 504 | 200-day |
| Secondary | 9 months | 189 | 100-day |
| Tertiary | 3 months | 63 | 50-day |

## 2. Trend label (per horizon)

Four checks are run every day. Each check that passes scores 1 point, giving a daily score from 0 to 4.

1. **Return:** the close is above the close `n` days earlier, where `n` is the horizon length.
2. **Price above its average:** the close is above the moving average for that horizon.
3. **Average rising:** that moving average is higher than it was `n` days earlier.
4. **Momentum:** the MACD histogram is above zero (12-day and 26-day EMAs with a 9-day signal line).

The label is sticky, so it does not flip on every day the score moves by one:

- **Score of 3 or 4:** Bullish.
- **Score of 0 or 1:** Bearish.
- **Score of 2:** keeps the previous label. If there is no previous label yet, it shows Neutral.

The table shows the current label, the score for today, for example `Bullish 3/4`, and the date the label started.

Your review found that the earlier rule flipped the primary label 6.6 to 8.5 times a year on SPY, QQQ, GLD and SLV. The sticky rule flipped it 0.6 to 3.1 times a year on the same instruments. Fewer flips do not by themselves prove a better signal. The sticky rule has not yet been backtested on risk-adjusted return.

## 3. Range position and RSI (per horizon)

Two status labels are shown side by side. They are calculated independently and can disagree.

**Range position** (per horizon): take the highest and lowest close over the horizon window (horizon length plus one day).

- Range position = (today's close − low) ÷ (high − low) × 100
- **80% or more:** Overbought
- **20% or less:** Oversold
- **Between 20% and 80%:** Neutral
- If the high and low are equal, the position is set to 50%.

**RSI(14)** (one value, not per horizon): a 14-day momentum measure.

- **80 or more:** Overbought
- **20 or less:** Oversold
- **Between 20 and 80:** Neutral

Range position compares price with its own recent range, so a steady uptrend tends to read as Overbought. RSI measures recent momentum, so the two can disagree.

## 4. Turn signals

Three rules flag a trend changing direction. Each shows its current state and the date that state began.

### a) MA cross 50/200
- **Bullish** when the 50-day average is above the 200-day average, confirmed for 3 days in a row.
- **Bearish** when it is below, confirmed for 3 days in a row.
- The date shown is the day the 3-day confirmation was reached.

### b) Breakout 55/20 (Donchian)
- **Bullish** on a close above the highest close of the previous 55 days.
- **Bearish** on a close below the lowest close of the previous 20 days.
- Breakouts count on the day they happen, with no confirmation wait.
- The state holds until the opposite breakout occurs.

### c) Relative strength
- The instrument's price is divided by its benchmark: SPY for indices, sectors and themes, and DBC for commodities.
- **Bullish** when that ratio is above its own 50-day average, confirmed for 3 days in a row.
- **Bearish** when it is below, confirmed for 3 days in a row.
- The ratio is only calculated once the 50-day average exists, so the first 49 days are not counted as Bearish.
- **Price-only index tickers** (symbols starting with `^`, such as `^GSPC` and `^RUT`) are excluded. They do not pay dividends, so their price ratio to SPY drifts downward against a dividend-adjusted series. Their relative-strength signal shows as n/a.
- SPY is not compared with itself, so it also shows n/a.

Relative strength means an instrument is beating its benchmark. It does not mean the instrument is rising. It is shown separately and is not included in the trend count below.

### Trend count
The table shows how many of the two trend rules (MA cross and breakout) are bullish, for example `1 / 2`. Relative strength is shown in its own column.

## 5. Stock trend filter (50/200)

For individual stocks, the report shows the 50-day against the 200-day average, using the same 3-day confirmation as the MA cross above. It is a risk filter, not a buy signal.

## 6. Backtest results

Results are from the backtests run during development, not a live track record.

- **ETFs (25):** none of the three turn signals beat buy-and-hold on risk-adjusted return. Each reduced the worst drawdown.
- **Individual stocks (21):** the 50/200 filter reduced the worst drawdown in 19 cases. Its median risk-adjusted return was about the same as buy-and-hold.
- **Sticky trend label:** not yet backtested on risk-adjusted return or drawdown.

## 7. Data and limits

- **Dividend-adjusted prices:** all series use `auto_adjust=True`. Index tickers (`^`) are the exception, since Yahoo does not adjust them, which is why relative strength is excluded for them.
- **Commodity futures are stitched:** each futures symbol (for example `GC=F`) is a continuous series that joins successive contracts. Prices can jump at each roll, and those jumps can trigger false breakouts or moving-average crosses.
- **DBC overlaps with metals:** the benchmark for commodity relative strength, DBC, holds gold and silver, so commodity relative strength partly compares gold and silver with themselves.
- **Parameters are standard, not optimised:** the 3-day confirmation, the 55/20 breakout windows, the 80/20 range and RSI cut-offs, and the 4-check score are conventional choices. They were not fitted to this data.
- **Lag:** moving-average and relative-strength signals confirm after about 3 days, so they lag turning points.
- **Whipsaw:** in sideways markets, all trend rules give repeated false signals.
- **Not investment advice.**
