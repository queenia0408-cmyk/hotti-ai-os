# Portfolio Optimizer

Monte Carlo Efficient Frontier + Risk Parity portfolio optimizer.

## Quick Start

```bash
pip install numpy yfinance
python optimizer.py --tickers AAPL MSFT GOOGL AMZN TSLA
python optimizer.py --tickers AAPL MSFT --sims 50000
python optimizer.py --tickers AAPL MSFT GOOGL --risk-parity --json report.json
```

## Features

- **Monte Carlo Efficient Frontier** — configurable N simulations (default 100k)
- **Risk Parity** — inverse-volatility weighting for equal risk contribution
- **Correlation Matrix** — asset correlation visualization
- **3 Optimal Portfolios** — Max Sharpe, Min Volatility, Max Return
- **Graceful Degradation** — yfinance real data with synthetic fallback

## Architecture

```
fetch_returns() → correlation_matrix() → monte_carlo_frontier() → find_optimal_portfolios()
                 → annualized_metrics()
                 → risk_parity_weights()
```

## Mathematical Foundation

- Markowitz Mean-Variance Optimization (1952)
- Geometric Brownian Motion for synthetic data
- Risk Parity: w_i ∝ 1/σ_i (inverse-volatility approximation)

## Tech

Python, numpy, yfinance, argparse, Monte Carlo simulation
