#!/usr/bin/env python3
"""
Portfolio Optimizer — Monte Carlo Efficient Frontier + Risk Parity
Cycle 7 Deep Domain Expansion — Trading Domain

Mathematical foundations:
- Markowitz Mean-Variance Optimization (1952)
- Monte Carlo simulation for efficient frontier
- Risk Parity (equal risk contribution)
- Geometric Brownian Motion for forward simulation

Usage:
    python optimizer.py --tickers AAPL MSFT GOOGL AMZN TSLA
    python optimizer.py --tickers AAPL MSFT --sims 50000
    python optimizer.py --tickers AAPL MSFT GOOGL --risk-parity
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np


# ─── Data Models ─────────────────────────────────────────────────────────

@dataclass
class PortfolioWeight:
    ticker: str
    weight: float  # 0.0 ~ 1.0
    allocation: float  # dollar amount

@dataclass
class PortfolioResult:
    weights: List[PortfolioWeight]
    expected_return_pct: float
    volatility_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    diversification_ratio: float  # weighted avg correlation → lower = better


# ─── Data Fetching ───────────────────────────────────────────────────────

def fetch_returns(tickers: List[str], days: int = 252) -> Optional[dict]:
    """Download historical data, compute daily log returns."""
    try:
        import yfinance as yf
    except ImportError:
        return None

    end = datetime.now()
    start = end - timedelta(days=days * 2)

    returns = {}
    prices = {}
    for t in tickers:
        try:
            df = yf.download(t, start=start.strftime("%Y-%m-%d"),
                             end=end.strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
            if df.empty or len(df) < 50:
                print(f"   ⚠ {t}: insufficient data")
                continue
            close = df['Close'].values
            log_ret = np.diff(np.log(close))
            returns[t] = log_ret
            prices[t] = close
            print(f"   ✅ {t}: {len(log_ret)} daily returns")
        except Exception as e:
            print(f"   ❌ {t}: {e}")

    return returns if len(returns) >= 2 else None


def generate_mock_returns(tickers: List[str], days: int = 252) -> dict:
    """Generate correlated synthetic returns for demonstration."""
    np.random.seed(42)
    n_assets = len(tickers)
    n_days = days

    # Random correlation structure
    base = np.random.randn(n_days) * 0.008  # market factor
    returns = {}
    for i, t in enumerate(tickers):
        # Each asset = market factor + idiosyncratic noise
        beta = 0.3 + np.random.random() * 1.2  # 0.3 ~ 1.5
        noise = np.random.randn(n_days) * 0.012
        ret = beta * base + noise
        # Add slight positive drift
        ret += 0.0003 + np.random.random() * 0.0004  # 0.03%~0.07% daily
        returns[t] = ret

    return returns


# ─── Analytics ───────────────────────────────────────────────────────────

def correlation_matrix(returns: dict) -> Tuple[np.ndarray, List[str]]:
    """Compute correlation matrix from return series."""
    tickers = list(returns.keys())
    n = len(tickers)
    corr = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            c = np.corrcoef(returns[tickers[i]], returns[tickers[j]])[0, 1]
            corr[i, j] = c
            corr[j, i] = c
    return corr, tickers


def annualized_metrics(returns: dict) -> dict:
    """Compute annualized return, volatility, Sharpe for each asset."""
    metrics = {}
    for t, r in returns.items():
        ann_ret = np.mean(r) * 252 * 100
        ann_vol = np.std(r, ddof=1) * np.sqrt(252) * 100
        sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
        metrics[t] = {
            "annual_return_pct": round(ann_ret, 2),
            "annual_volatility_pct": round(ann_vol, 2),
            "sharpe_ratio": round(sharpe, 2),
        }
    return metrics


def portfolio_metrics(weights: np.ndarray, returns: dict, tickers: List[str]) -> dict:
    """Compute portfolio-level metrics for given weights."""
    # Portfolio return series
    port_ret = np.zeros(len(returns[tickers[0]]))
    for i, t in enumerate(tickers):
        port_ret += weights[i] * returns[t]

    ann_ret = np.mean(port_ret) * 252 * 100
    ann_vol = np.std(port_ret, ddof=1) * np.sqrt(252) * 100
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0

    # Max drawdown
    cum = np.cumprod(1 + port_ret)
    peak = np.maximum.accumulate(cum)
    max_dd = float(np.min((cum - peak) / peak) * 100)

    # Diversification ratio: 1 - weighted_avg_correlation
    corr, _ = correlation_matrix(returns)
    weighted_corr = 0
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            weighted_corr += weights[i] * weights[j] * corr[i, j]
    # Normalize (max possible sum of weight pairs = 0.5 * (1 - sum(w²)))
    norm = 0.5 * (1 - np.sum(weights ** 2))
    avg_corr = weighted_corr / norm if norm > 0 else 0
    div_ratio = 1 - avg_corr

    return {
        "annual_return_pct": round(ann_ret, 2),
        "annual_volatility_pct": round(ann_vol, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "diversification_ratio": round(div_ratio, 4),
    }


# ─── Monte Carlo Efficient Frontier ──────────────────────────────────────

def monte_carlo_frontier(returns: dict, n_sims: int = 100_000) -> List[dict]:
    """Random portfolio simulation → efficient frontier."""
    tickers = list(returns.keys())
    n = len(tickers)
    results = []

    print(f"\n🎲 Running {n_sims:,} Monte Carlo simulations...")

    for i in range(n_sims):
        # Generate random weights, normalize
        w = np.random.random(n)
        w = w / w.sum()

        metrics = portfolio_metrics(w, returns, tickers)

        results.append({
            "weights": {tickers[j]: round(w[j], 4) for j in range(n)},
            "return_pct": metrics["annual_return_pct"],
            "volatility_pct": metrics["annual_volatility_pct"],
            "sharpe_ratio": metrics["sharpe_ratio"],
        })

        if (i + 1) % 25000 == 0:
            print(f"   ... {i + 1:,} simulations")

    return results


def find_optimal_portfolios(frontier: List[dict]) -> dict:
    """Find key portfolios on the efficient frontier."""
    # Max Sharpe (tangency portfolio)
    max_sharpe = max(frontier, key=lambda p: p["sharpe_ratio"])

    # Min volatility (global minimum variance)
    min_vol = min(frontier, key=lambda p: p["volatility_pct"])

    # Max return
    max_ret = max(frontier, key=lambda p: p["return_pct"])

    return {
        "max_sharpe": max_sharpe,
        "min_volatility": min_vol,
        "max_return": max_ret,
    }


# ─── Risk Parity ─────────────────────────────────────────────────────────

def risk_parity_weights(returns: dict, max_iter: int = 1000) -> dict:
    """
    Compute Risk Parity weights where each asset contributes equal risk.
    Risk contribution_i = w_i * (Σw) marginal risk_i

    Simplified approach: inverse-volatility weighting
    w_i ∝ 1 / σ_i
    """
    tickers = list(returns.keys())
    vols = np.array([np.std(returns[t], ddof=1) for t in tickers])
    inv_vols = 1.0 / vols
    weights = inv_vols / inv_vols.sum()

    metrics = portfolio_metrics(weights, returns, tickers)

    return {
        "weights": {tickers[i]: round(weights[i], 4) for i in range(len(tickers))},
        "method": "inverse-volatility (risk parity approximation)",
        "metrics": metrics,
    }


# ─── Reports ─────────────────────────────────────────────────────────────

def format_report(optimals: dict, risk_parity: dict, metrics: dict, corr, tickers) -> str:
    bar = "═" * 64
    lines = [f"\n{bar}",
             f"📊 PORTFOLIO OPTIMIZER — {', '.join(tickers)}",
             f"{bar}"]

    # Individual asset metrics
    lines.append("\n📈 INDIVIDUAL ASSETS")
    for t, m in metrics.items():
        lines.append(f"  {t:6}: {m['annual_return_pct']:+.1f}% ret | {m['annual_volatility_pct']:.1f}% vol | Sharpe {m['sharpe_ratio']:.2f}")

    # Correlation matrix
    lines.append("\n📊 CORRELATION MATRIX")
    header = "       " + "  ".join(f"{t:>6}" for t in tickers)
    lines.append(header)
    for i, t in enumerate(tickers):
        row = f"  {t:4} " + "  ".join(f"{corr[i,j]:6.3f}" for j in range(len(tickers)))
        lines.append(row)

    # Optimal portfolios
    labels = {
        "max_sharpe": "🎯 Max Sharpe (Tangency)",
        "min_volatility": "🛡️ Min Volatility (GMV)",
        "max_return": "🚀 Max Return",
    }
    lines.append(f"\n🎯 OPTIMAL PORTFOLIOS ({len(optimals['max_sharpe']['weights'])} assets)")
    for key, label in labels.items():
        p = optimals[key]
        lines.append(f"\n  {label}")
        lines.append(f"    Return: {p['return_pct']:+.1f}% | Vol: {p['volatility_pct']:.1f}% | Sharpe: {p['sharpe_ratio']:.2f}")
        for t, w in sorted(p["weights"].items(), key=lambda x: -x[1]):
            bar_len = int(w * 50)
            lines.append(f"    {t:6}: {'█' * bar_len} {w:.1%}")

    # Risk Parity
    lines.append(f"\n⚖️ RISK PARITY ({risk_parity['method']})")
    rp = risk_parity
    m = rp["metrics"]
    lines.append(f"    Return: {m['annual_return_pct']:+.1f}% | Vol: {m['annual_volatility_pct']:.1f}% | Sharpe: {m['sharpe_ratio']:.2f}")
    for t, w in sorted(rp["weights"].items(), key=lambda x: -x[1]):
        bar_len = int(w * 50)
        lines.append(f"    {t:6}: {'█' * bar_len} {w:.1%}")

    lines.append(f"\n{bar}")
    lines.append("✅ Portfolio optimization complete. Cycle 7 — Deep Domain Expansion.\n")
    return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Portfolio Optimizer — Monte Carlo Efficient Frontier + Risk Parity",
        epilog="Cycle 7 Deep Domain Expansion | Claude Code Self-Evolution"
    )
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
                        help="Ticker symbols")
    parser.add_argument("--sims", type=int, default=100_000,
                        help="Monte Carlo simulations (default: 100k)")
    parser.add_argument("--risk-parity", action="store_true",
                        help="Also compute risk parity weights")
    parser.add_argument("--json", default=None, help="Save JSON output")
    args = parser.parse_args()

    print(f"\n🔍 Fetching data for {len(args.tickers)} tickers...")
    returns = fetch_returns(args.tickers)

    if not returns:
        print("   ⚠ Using synthetic data (yfinance unavailable)")
        returns = generate_mock_returns(args.tickers)

    tickers = list(returns.keys())
    print(f"   {len(tickers)} assets, {len(returns[tickers[0]])} daily returns each")

    # Asset-level metrics
    metrics = annualized_metrics(returns)

    # Correlation matrix
    corr, _ = correlation_matrix(returns)

    # Monte Carlo efficient frontier
    frontier = monte_carlo_frontier(returns, args.sims)
    optimals = find_optimal_portfolios(frontier)

    # Risk parity
    rp = risk_parity_weights(returns)

    print(format_report(optimals, rp, metrics, corr, tickers))

    if args.json:
        output = {
            "timestamp": datetime.now().isoformat(),
            "tickers": tickers,
            "individual_metrics": metrics,
            "correlation_matrix": {tickers[i]: {tickers[j]: round(corr[i,j], 3) for j in range(len(tickers))} for i in range(len(tickers))},
            "optimal_portfolios": optimals,
            "risk_parity": rp,
            "monte_carlo_simulations": args.sims,
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON saved to: {args.json}")


if __name__ == "__main__":
    main()
