# Market Data Dashboard

Real-time multi-asset market monitor with technical indicators and portfolio analytics.

## Quick Start

```bash
python dashboard.py --tickers "AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA"
python dashboard.py --tickers "AAPL,MSFT" --live --json report.json
```

## Features

- **Multi-Asset Monitoring** — Price, daily/weekly/monthly changes, volume
- **Technical Indicators** — RSI (14), SMA (20/50), 20-day volatility (annualized)
- **Signal Generation** — BUY/BULLISH/BEARISH/SELL based on RSI + SMA crossover
- **Portfolio Summary** — Aggregate returns, volatility, RSI, market bias, diversification score
- **Correlation Matrix** — Sector-based correlation estimates
- **Insights** — Top/worst performers, volatility ranking, overbought/oversold alerts

## Usage

| Flag | Description |
|------|-------------|
| `--tickers` | Comma-separated ticker list (default: AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA) |
| `--live` | Use live yfinance data (requires yfinance installed) |
| `--json` | Save output as JSON report |

## Architecture

```
fetch_market_data() → compute_correlation() → portfolio_summary() → format_dashboard()
         ↓                      ↓                       ↓                    ↓
   yfinance → metrics    sector grouping        aggregate stats      formatted CLI
   synthetic fallback    correlation matrix     market bias          JSON export
```

## Tech

Python, NumPy, yfinance (optional), sector correlation modeling, RSI, SMA, volatility
