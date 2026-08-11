# Trading Backtest Engine

> Cycle 3 Build-to-Understand | Claude Code Self-Evolution v3.0

Production-grade momentum & mean reversion strategy backtester.

## Quick Start

```bash
pip install -r requirements.txt
python backtest.py --symbol AAPL --strategy both --start 2020-01-01 --end 2024-12-31
```

## Features

- **Momentum Strategy**: Golden Cross / Death Cross (20/50 SMA)
- **Mean Reversion Strategy**: RSI oversold/overbought signals
- **Analytics**: Sharpe Ratio, Sortino Ratio, Max Drawdown, Win Rate, Profit Factor
- **Real Data**: yfinance integration for live market data
- **Synthetic Data**: Built-in mock generator for testing without API

## Architecture

```
backtest.py
├── Data Models: Bar, Trade, Result
├── Data Sources: yfinance (real) / generate_mock_bars() (synthetic)
├── Indicators: SMA, EMA, RSI (from-scratch)
├── Strategies: momentum_strategy(), mean_reversion_strategy()
└── Analytics: CAGR, Sharpe, Sortino, Max Drawdown, Profit Factor
```

## Requirements

- Python 3.10+
- yfinance, pandas (optional — for real data)

## Roadmap

- [ ] Multi-asset portfolio backtesting
- [ ] Walk-forward optimization
- [ ] Interactive Streamlit UI
- [ ] Alpaca/IBKR live trading integration
