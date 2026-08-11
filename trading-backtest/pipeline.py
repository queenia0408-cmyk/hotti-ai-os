#!/usr/bin/env python3
"""
Data Pipeline — Automated Market Analysis
Cycle 5 Quality Engineering — yfinance → pandas → report

Usage:
    python pipeline.py                  # Run with default tickers
    python pipeline.py --tickers AAPL MSFT GOOGL  # Custom tickers
    python pipeline.py --output report.json       # JSON output
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Pipeline Steps
# ---------------------------------------------------------------------------

def fetch_data(tickers: list[str], days: int = 252) -> Optional[dict]:
    """Step 1: Download real market data via yfinance."""
    try:
        import yfinance as yf
        import pandas as pd
    except ImportError:
        print("⚠ yfinance/pandas not installed. Run: pip install yfinance pandas")
        return None

    end = datetime.now()
    start = end - timedelta(days=days * 2)  # extra buffer for non-trading days

    data = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                             end=end.strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
            if not df.empty:
                data[ticker] = df
                print(f"   ✅ {ticker}: {len(df)} rows")
            else:
                print(f"   ⚠ {ticker}: no data")
        except Exception as e:
            print(f"   ❌ {ticker}: {e}")

    return data if data else None


def compute_metrics(data: dict) -> dict:
    """Step 2: Compute analytics for each ticker."""
    import pandas as pd
    import numpy as np

    results = {}

    for ticker, df in data.items():
        if 'Close' not in df.columns:
            continue

        closes = df['Close'].values
        if len(closes) < 2:
            continue

        # Daily returns
        returns = np.diff(closes) / closes[:-1]

        # Metrics
        mean_daily = np.mean(returns)
        std_daily = np.std(returns, ddof=1)
        annual_return = mean_daily * 252
        annual_vol = std_daily * np.sqrt(252)
        sharpe = annual_return / annual_vol if annual_vol > 0 else 0

        # Sortino
        downside = returns[returns < 0]
        downside_std = np.std(downside, ddof=1) if len(downside) > 1 else 0
        sortino = annual_return / (downside_std * np.sqrt(252)) if downside_std > 0 else 0

        # Max drawdown
        cumulative = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - peak) / peak
        max_dd = float(np.min(drawdown))

        # Current stats
        current_price = float(closes[-1])
        price_change_20d = float((closes[-1] / closes[-min(20, len(closes))] - 1) * 100)

        # RSI(14)
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else np.mean(gains)
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else np.mean(losses)
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi_14 = 100 - (100 / (1 + rs)) if avg_loss > 0 else 100

        # SMA cross
        sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else None
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else None
        sma_signal = "bullish" if sma_20 and sma_50 and sma_20 > sma_50 else \
                     "bearish" if sma_20 and sma_50 else "insufficient data"

        results[ticker] = {
            "current_price": round(current_price, 2),
            "price_change_20d_pct": round(price_change_20d, 2),
            "annual_return_pct": round(annual_return * 100, 2),
            "annual_volatility_pct": round(annual_vol * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "rsi_14": round(rsi_14, 1),
            "sma_20": round(sma_20, 2) if sma_20 else None,
            "sma_50": round(sma_50, 2) if sma_50 else None,
            "sma_signal": sma_signal,
            "data_points": len(closes),
        }

    return results


def generate_report(results: dict) -> str:
    """Step 3: Format analysis report."""
    bar = "═" * 64
    lines = [f"\n{bar}",
             f"📊 DAILY MARKET ANALYSIS — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             f"{bar}"]

    for ticker, m in results.items():
        signal_emoji = "🟢" if m["sma_signal"] == "bullish" else "🔴" if m["sma_signal"] == "bearish" else "⚪"
        lines.append(f"\n{signal_emoji} {ticker} — ${m['current_price']} ({m['price_change_20d_pct']:+.1f}% 20d)")
        lines.append(f"   Sharpe: {m['sharpe_ratio']} | Sortino: {m['sortino_ratio']} | MaxDD: {m['max_drawdown_pct']:.1f}%")
        lines.append(f"   RSI(14): {m['rsi_14']} | SMA20: {m['sma_20']} | SMA50: {m['sma_50']} | {m['sma_signal']}")
        lines.append(f"   Ann.Ret: {m['annual_return_pct']:+.1f}% | Ann.Vol: {m['annual_volatility_pct']:.1f}% | {m['data_points']} bars")

    lines.append(f"\n{bar}")
    lines.append("✅ Pipeline complete. Cycle 5 — Quality Engineering.\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Data Pipeline — Automated Market Analysis",
        epilog="Cycle 5 Quality Engineering | Claude Code Self-Evolution"
    )
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
                        help="Ticker symbols (default: AAPL MSFT GOOGL AMZN TSLA)")
    parser.add_argument("--output", default=None,
                        help="Save JSON report to file")
    parser.add_argument("--days", type=int, default=252,
                        help="Trading days of data (default: 252 = 1 year)")
    args = parser.parse_args()

    print(f"\n🔍 Fetching data for {len(args.tickers)} tickers...")

    data = fetch_data(args.tickers, args.days)
    if not data:
        print("❌ No data fetched. Install yfinance: pip install yfinance pandas")
        sys.exit(1)

    print(f"\n📊 Computing metrics...")
    results = compute_metrics(data)

    report = generate_report(results)
    print(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "tickers": args.tickers,
                "results": results,
            }, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON saved to: {args.output}")


if __name__ == "__main__":
    main()
