# Algorithmic Trading Bot Framework

Signal Pipeline → Risk Management → Position Sizing → Backtest Engine.

## Quick Start

```bash
python bot.py signal --ticker AAPL --method sma-crossover
python bot.py signal --ticker TSLA --method rsi --generate-prices 200
python bot.py risk --capital 100000 --price 150 --volatility 30
python bot.py backtest --capital 100000 --tickers "AAPL,MSFT,GOOGL" --strategy momentum
```

## Features

- **Signal Generation** — SMA crossover, RSI, Momentum with confidence scoring (0-1)
- **Risk Management** — 5 rule engine: position size, cash reserve, daily loss, drawdown, leverage
- **Position Sizing** — Van Tharp method + Kelly Criterion
- **Backtest Engine** — Multi-asset, multi-strategy, Sharpe ratio, Max Drawdown

## Architecture

```
generate_signals() → check_risk() → size_position() → execute() → PnL tracking
       ↓                  ↓               ↓
    SMA/RSI/Mom      5 rules       Kelly + Tharp
```

## Risk Rule Engine

| Rule | Purpose |
|------|---------|
| Max Position Size | ≤ 20% per single position |
| Cash Reserve | ≥ 10% minimum cash |
| Daily Loss Limit | Stop trading if > 5% daily loss |
| Max Drawdown | Circuit breaker at 25% |
| Max Leverage | 1.0x (no leverage) |

## Tech

Python, Kelly Criterion, Van Tharp sizing, risk-parity, backtest engine
