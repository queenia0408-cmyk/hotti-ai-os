#!/usr/bin/env python3
"""
Trading Backtest Engine — Momentum + Mean Reversion Strategy Tester
Cycle 3 Build-to-Understand: 실제 실행 가능한 백테스트

Usage:
    python backtest.py --symbol AAPL --start 2020-01-01 --end 2024-12-31
    python backtest.py --symbol ^GSPC --strategy momentum --capital 100000
"""

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import math

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Bar:
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class Trade:
    entry_date: datetime
    exit_date: datetime
    side: str          # 'long' | 'short'
    entry_price: float
    exit_price: float
    size: int
    pnl: float
    pnl_pct: float

@dataclass
class Result:
    symbol: str
    strategy: str
    start: datetime
    end: datetime
    initial_capital: float
    final_capital: float
    total_return_pct: float
    cagr_pct: float
    annual_volatility_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    profit_factor: float
    trades: List[Trade] = field(default_factory=list)

# ---------------------------------------------------------------------------
# Data Sources (Real + Mock)
# ---------------------------------------------------------------------------

def download_bars(symbol: str, start: datetime, end: datetime) -> Optional[List[Bar]]:
    """
    Download real price data via yfinance.
    Returns None if yfinance is not installed or download fails.
    """
    try:
        import yfinance as yf
        df = yf.download(symbol, start=start.strftime("%Y-%m-%d"),
                         end=end.strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
        if df.empty:
            return None

        bars = []
        for idx, row in df.iterrows():
            bars.append(Bar(
                date=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else datetime.fromtimestamp(idx.timestamp()),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
            ))
        return bars
    except ImportError:
        return None
    except Exception as e:
        print(f"   ⚠ yfinance download failed: {e}")
        return None


def generate_mock_bars(symbol: str, start: datetime, end: datetime) -> List[Bar]:
    """
    Generate synthetic price data for demonstration.
    Used as fallback when yfinance is unavailable.
    """
    import random
    random.seed(hash(symbol) % 2**31)

    days = (end - start).days
    bars = []
    price = 100.0 + random.uniform(-20, 50)
    current = start

    for _ in range(days):
        if current.weekday() >= 5:  # skip weekends
            current = current + timedelta(days=1)
            continue

        daily_return = random.gauss(0.0003, 0.015)  # mean 0.03%, std 1.5%
        open_price = price
        close_price = price * (1 + daily_return)
        intraday_range = close_price * random.uniform(0.005, 0.025)
        high_price = max(open_price, close_price) + intraday_range * random.random()
        low_price = min(open_price, close_price) - intraday_range * random.random()
        volume = int(random.uniform(500_000, 5_000_000))

        bars.append(Bar(
            date=current,
            open=round(open_price, 2),
            high=round(high_price, 2),
            low=round(low_price, 2),
            close=round(close_price, 2),
            volume=volume,
        ))
        price = close_price
        # advance day
        current = current + timedelta(days=1)

    return bars

# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------

def sma(prices: List[float], period: int) -> List[Optional[float]]:
    """Simple Moving Average — returns None for insufficient data."""
    result = [None] * len(prices)
    for i in range(period - 1, len(prices)):
        result[i] = sum(prices[i - period + 1 : i + 1]) / period
    return result

def ema(prices: List[float], period: int) -> List[float]:
    """Exponential Moving Average."""
    result = [None] * len(prices)
    multiplier = 2 / (period + 1)
    # Seed with SMA
    result[period - 1] = sum(prices[:period]) / period
    for i in range(period, len(prices)):
        result[i] = (prices[i] - result[i - 1]) * multiplier + result[i - 1]
    return result

def rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """Relative Strength Index."""
    if len(prices) < period + 1:
        return [None] * len(prices)

    result = [None] * len(prices)
    gains = []
    losses = []

    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        if avg_loss == 0:
            result[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i + 1] = 100.0 - (100.0 / (1.0 + rs))

        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    return result

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

def momentum_strategy(bars: List[Bar], capital: float,
                      lookback_short: int = 20,
                      lookback_long: int = 50) -> List[Trade]:
    """
    Golden Cross / Death Cross momentum strategy.
    - Buy when 20-day SMA crosses ABOVE 50-day SMA
    - Sell when 20-day SMA crosses BELOW 50-day SMA
    """
    closes = [b.close for b in bars]
    sma_short = sma(closes, lookback_short)
    sma_long = sma(closes, lookback_long)
    trades = []
    position = 0
    entry_price = 0.0
    cash = capital

    for i in range(lookback_long, len(bars)):
        if sma_short[i] is None or sma_long[i] is None:
            continue
        if sma_short[i - 1] is None or sma_long[i - 1] is None:
            continue

        # Golden Cross — BUY
        if sma_short[i - 1] <= sma_long[i - 1] and sma_short[i] > sma_long[i] and position == 0:
            size = int(cash / bars[i].close)
            if size > 0:
                position = size
                entry_price = bars[i].close
                cash -= size * entry_price

        # Death Cross — SELL
        elif sma_short[i - 1] >= sma_long[i - 1] and sma_short[i] < sma_long[i] and position > 0:
            pnl = position * (bars[i].close - entry_price)
            pnl_pct = (bars[i].close - entry_price) / entry_price * 100
            trades.append(Trade(
                entry_date=bars[i - (len(bars) - i)],  # approximate
                exit_date=bars[i].date,
                side='long',
                entry_price=entry_price,
                exit_price=bars[i].close,
                size=position,
                pnl=round(pnl, 2),
                pnl_pct=round(pnl_pct, 2),
            ))
            cash += position * bars[i].close
            position = 0

    # Close remaining position
    if position > 0:
        last = bars[-1]
        pnl = position * (last.close - entry_price)
        trades.append(Trade(
            entry_date=bars[0].date,
            exit_date=last.date,
            side='long',
            entry_price=entry_price,
            exit_price=last.close,
            size=position,
            pnl=round(pnl, 2),
            pnl_pct=round((last.close - entry_price) / entry_price * 100, 2),
        ))
        cash += position * last.close

    return trades


def mean_reversion_strategy(bars: List[Bar], capital: float,
                            rsi_period: int = 14,
                            oversold: float = 30,
                            overbought: float = 70) -> List[Trade]:
    """
    RSI Mean Reversion strategy.
    - Buy when RSI < oversold (30)
    - Sell when RSI > overbought (70)
    """
    closes = [b.close for b in bars]
    rsi_values = rsi(closes, rsi_period)
    trades = []
    position = 0
    entry_price = 0.0
    cash = capital

    for i in range(rsi_period + 1, len(bars)):
        if rsi_values[i] is None:
            continue

        # Oversold — BUY
        if rsi_values[i] < oversold and position == 0:
            size = int(cash / bars[i].close)
            if size > 0:
                position = size
                entry_price = bars[i].close
                cash -= size * entry_price

        # Overbought — SELL
        elif rsi_values[i] > overbought and position > 0:
            pnl = position * (bars[i].close - entry_price)
            pnl_pct = (bars[i].close - entry_price) / entry_price * 100
            trades.append(Trade(
                entry_date=bars[i - (len(bars) - i)].date,
                exit_date=bars[i].date,
                side='long',
                entry_price=entry_price,
                exit_price=bars[i].close,
                size=position,
                pnl=round(pnl, 2),
                pnl_pct=round(pnl_pct, 2),
            ))
            cash += position * bars[i].close
            position = 0

    # Close remaining
    if position > 0:
        last = bars[-1]
        pnl = position * (last.close - entry_price)
        trades.append(Trade(
            entry_date=bars[0].date,
            exit_date=last.date,
            side='long',
            entry_price=entry_price,
            exit_price=last.close,
            size=position,
            pnl=round(pnl, 2),
            pnl_pct=round((last.close - entry_price) / entry_price * 100, 2),
        ))
        cash += position * last.close

    return trades

# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def compute_metrics(bars: List[Bar], trades: List[Trade],
                    initial_capital: float, strategy: str, symbol: str) -> Result:
    """Compute comprehensive performance metrics."""

    if not trades:
        return Result(
            symbol=symbol, strategy=strategy,
            start=bars[0].date, end=bars[-1].date,
            initial_capital=initial_capital, final_capital=initial_capital,
            total_return_pct=0.0, cagr_pct=0.0, annual_volatility_pct=0.0,
            sharpe_ratio=0.0, sortino_ratio=0.0, max_drawdown_pct=0.0,
            win_rate_pct=0.0, total_trades=0, profit_factor=0.0,
        )

    # Total return
    final_capital = initial_capital + sum(t.pnl for t in trades)
    total_return_pct = (final_capital - initial_capital) / initial_capital * 100

    # CAGR
    years = (bars[-1].date - bars[0].date).days / 365.25
    cagr_pct = ((final_capital / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0.0

    # Daily returns for vol/sharpe (simplified: use trade-level)
    returns = [t.pnl_pct / 100 for t in trades]
    if len(returns) > 1:
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        std_ret = math.sqrt(variance)
        # Annualize
        annual_vol = std_ret * math.sqrt(252)
        sharpe = (mean_ret / std_ret * math.sqrt(252)) if std_ret > 0 else 0.0

        # Sortino (downside deviation only)
        downside_returns = [r for r in returns if r < 0]
        if downside_returns:
            downside_var = sum(r ** 2 for r in downside_returns) / len(downside_returns)
            downside_std = math.sqrt(downside_var)
            sortino = (mean_ret / downside_std * math.sqrt(252)) if downside_std > 0 else 0.0
        else:
            sortino = float('inf')
    else:
        annual_vol = 0.0
        sharpe = 0.0
        sortino = 0.0

    # Win rate
    winners = [t for t in trades if t.pnl > 0]
    win_rate_pct = len(winners) / len(trades) * 100

    # Profit factor
    gross_profit = sum(t.pnl for t in winners)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    # Max drawdown (from trade PnL equity curve)
    equity = initial_capital
    peak = equity
    max_dd = 0.0
    for t in trades:
        equity += t.pnl
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100
        if dd > max_dd:
            max_dd = dd

    return Result(
        symbol=symbol, strategy=strategy,
        start=bars[0].date, end=bars[-1].date,
        initial_capital=initial_capital,
        final_capital=round(final_capital, 2),
        total_return_pct=round(total_return_pct, 2),
        cagr_pct=round(cagr_pct, 2),
        annual_volatility_pct=round(annual_vol, 2),
        sharpe_ratio=round(sharpe, 2),
        sortino_ratio=round(sortino, 2) if sortino != float('inf') else 999.0,
        max_drawdown_pct=round(max_dd, 2),
        win_rate_pct=round(win_rate_pct, 2),
        total_trades=len(trades),
        profit_factor=round(profit_factor, 2) if profit_factor != float('inf') else 999.0,
        trades=trades,
    )

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def format_report(result: Result) -> str:
    """Pretty-print backtest result."""
    bar = "═" * 60
    return f"""
{bar}
📊 BACKTEST REPORT: {result.symbol} — {result.strategy}
{bar}
  Period:              {result.start.date()} → {result.end.date()}
  Initial Capital:     ${result.initial_capital:,.2f}
  Final Capital:       ${result.final_capital:,.2f}
  Total Return:        {result.total_return_pct:+.2f}%
  CAGR:                {result.cagr_pct:+.2f}%
  Annual Volatility:   {result.annual_volatility_pct:.2f}%
  ─────────────────────────────────────────
  Sharpe Ratio:        {result.sharpe_ratio:.2f}
  Sortino Ratio:       {result.sortino_ratio:.2f}
  Max Drawdown:        {result.max_drawdown_pct:.2f}%
  Win Rate:            {result.win_rate_pct:.1f}% ({sum(1 for t in result.trades if t.pnl > 0)}/{result.total_trades})
  Profit Factor:       {result.profit_factor:.2f}
  Total Trades:        {result.total_trades}
{bar}

Top 3 Trades:
"""
    sorted_trades = sorted(result.trades, key=lambda t: t.pnl, reverse=True)[:3]
    for i, t in enumerate(sorted_trades, 1):
        report += f"  #{i} {t.side.upper():5} | entry ${t.entry_price:.2f} → exit ${t.exit_price:.2f} | PnL ${t.pnl:+.2f} ({t.pnl_pct:+.2f}%)\n"

    report += f"\nWorst 3 Trades:\n"
    worst = sorted(result.trades, key=lambda t: t.pnl)[:3]
    for i, t in enumerate(worst, 1):
        report += f"  #{i} {t.side.upper():5} | entry ${t.entry_price:.2f} → exit ${t.exit_price:.2f} | PnL ${t.pnl:+.2f} ({t.pnl_pct:+.2f}%)\n"

    return report

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Trading Backtest Engine — Momentum & Mean Reversion",
        epilog="Cycle 3 Build-to-Understand | Claude Code Self-Evolution"
    )
    parser.add_argument("--symbol", default="AAPL", help="Ticker symbol (default: AAPL)")
    parser.add_argument("--start", default="2020-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default="2024-12-31", help="End date YYYY-MM-DD")
    parser.add_argument("--strategy", default="momentum",
                        choices=["momentum", "mean-reversion", "both"],
                        help="Strategy to backtest")
    parser.add_argument("--capital", type=float, default=100_000,
                        help="Initial capital (default: 100000)")
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")

    print(f"\n🔍 Loading data for {args.symbol} ({args.start} → {args.end})...")

    # Try real data first, fall back to synthetic
    bars = download_bars(args.symbol, start, end)
    if bars:
        print(f"   {len(bars)} bars loaded (yfinance — real market data)")
    else:
        bars = generate_mock_bars(args.symbol, start, end)
        print(f"   {len(bars)} bars loaded (synthetic — install yfinance for real data)")
    print()

    strategies = {
        "momentum": momentum_strategy,
        "mean-reversion": mean_reversion_strategy,
    }

    names = [args.strategy] if args.strategy != "both" else list(strategies.keys())

    for name in names:
        print(f"⚡ Running {name.upper()} strategy...")
        trades = strategies[name](bars, args.capital)
        result = compute_metrics(bars, trades, args.capital, name, args.symbol)
        print(format_report(result))

    print("✅ Backtest complete. Cycle 3 — Build to Understand.\n")


if __name__ == "__main__":
    main()
