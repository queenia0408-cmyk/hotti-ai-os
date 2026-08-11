#!/usr/bin/env python3
"""
Algorithmic Trading Bot Framework — Order Management, Position Sizing, Risk Control, Signal Pipeline
Cycle 11-12 Autonomous Evolution — Trading + Systems Deep-Dive

Architecture: Signal → RiskCheck → PositionSizer → OrderManager → Execution → PnL

Usage:
    python bot.py backtest --capital 100000 --strategy momentum --tickers AAPL MSFT
    python bot.py signal --ticker AAPL --method sma-crossover
    python bot.py risk --capital 100000 --positions 5 --max-drawdown 0.15
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Tuple


# ─── Enums & Data Models ─────────────────────────────────────────────────

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    ticker: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: float
    status: OrderStatus = OrderStatus.PENDING
    id: str = ""
    timestamp: str = ""
    fill_price: Optional[float] = None


@dataclass
class Position:
    ticker: str
    quantity: int
    avg_price: float
    current_price: float
    pnl: float = 0.0
    pnl_pct: float = 0.0
    allocation_pct: float = 0.0


@dataclass
class Portfolio:
    cash: float
    positions: List[Position]
    total_value: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    peak_value: float = 0.0
    sharpe_ratio: float = 0.0


@dataclass
class RiskLimits:
    max_position_size_pct: float  # e.g., 0.20 = 20% per position
    max_portfolio_risk_pct: float  # max drawdown allowed
    max_correlation: float         # max correlation between positions
    min_cash_reserve_pct: float    # always keep X% cash
    max_daily_loss_pct: float      # stop trading if daily loss > X%
    trailing_stop_pct: float       # trailing stop distance
    max_leverage: float            # 1.0 = no leverage


@dataclass
class SignalResult:
    ticker: str
    signal: str                    # "BUY", "SELL", "HOLD"
    confidence: float              # 0.0-1.0
    indicators: dict
    reason: str


# ─── Signal Generation ───────────────────────────────────────────────────

def generate_signals(ticker: str, prices: List[float], method: str = "sma-crossover") -> SignalResult:
    """Generate trading signals from price data."""
    if len(prices) < 50:
        return SignalResult(ticker=ticker, signal="HOLD", confidence=0.0,
                           indicators={}, reason="Insufficient data (< 50 bars)")

    indicators = {}

    # SMA Crossover (short=10, long=30)
    sma_short = sum(prices[-10:]) / 10
    sma_long = sum(prices[-30:]) / 30
    sma_trend = "bullish" if sma_short > sma_long else "bearish"
    indicators["sma_10"] = round(sma_short, 2)
    indicators["sma_30"] = round(sma_long, 2)
    indicators["sma_trend"] = sma_trend

    # RSI (14-period)
    gains = [max(0, prices[i] - prices[i-1]) for i in range(-14, 0)]
    losses = [max(0, prices[i-1] - prices[i]) for i in range(-14, 0)]
    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    indicators["rsi_14"] = round(rsi, 1)

    # Momentum (20-day)
    mom = (prices[-1] / prices[-20] - 1) * 100
    indicators["momentum_20"] = round(mom, 1)

    # Volatility (20-day annualized)
    rets = [(prices[i] / prices[i-1] - 1) for i in range(-20, 0)]
    mean_ret = sum(rets) / len(rets)
    var = sum((r - mean_ret)**2 for r in rets) / (len(rets) - 1)
    vol = math.sqrt(var) * math.sqrt(252) * 100
    indicators["volatility_20"] = round(vol, 1)

    # Signal logic
    reasons = []
    confidence = 0.5

    if method == "sma-crossover":
        if sma_short > sma_long:
            signal = "BUY"
            confidence += 0.15
            reasons.append("SMA 10 > SMA 30 (bullish crossover)")
        else:
            signal = "SELL"
            confidence -= 0.15
            reasons.append("SMA 10 < SMA 30 (bearish crossover)")
    elif method == "rsi":
        if rsi < 30:
            signal = "BUY"
            confidence += 0.3
            reasons.append(f"RSI={rsi} — oversold")
        elif rsi > 70:
            signal = "SELL"
            confidence -= 0.3
            reasons.append(f"RSI={rsi} — overbought")
        else:
            signal = "HOLD"
            reasons.append(f"RSI={rsi} — neutral zone")
    elif method == "momentum":
        if mom > 5:
            signal = "BUY"
            confidence += 0.2
            reasons.append(f"Momentum={mom}% — strong positive")
        elif mom < -5:
            signal = "SELL"
            confidence -= 0.2
            reasons.append(f"Momentum={mom}% — strong negative")
        else:
            signal = "HOLD"
            reasons.append(f"Momentum={mom}% — neutral")
    else:
        signal = "HOLD"
        reasons.append("No clear signal")

    # Adjust for volatility
    if vol > 40:
        confidence -= 0.15
        reasons.append(f"High volatility ({vol}%) — reduce conviction")

    confidence = max(0.0, min(1.0, confidence))

    return SignalResult(
        ticker=ticker,
        signal=signal,
        confidence=round(confidence, 2),
        indicators=indicators,
        reason="; ".join(reasons),
    )


# ─── Risk Management ────────────────────────────────────────────────────

def check_risk(order: Order, portfolio: Portfolio, limits: RiskLimits,
               positions: List[Position]) -> Tuple[bool, str]:
    """Validate order against risk limits. Returns (approved, reason)."""
    # Calculate current position value
    pos_value = order.quantity * order.price
    total_equity = portfolio.total_value if portfolio.total_value > 0 else portfolio.cash

    # Check 1: Position size limit
    if pos_value / total_equity > limits.max_position_size_pct:
        return False, f"Position size {pos_value/total_equity:.1%} exceeds limit {limits.max_position_size_pct:.1%}"

    # Check 2: Cash reserve
    cash_after = portfolio.cash - pos_value
    if cash_after / total_equity < limits.min_cash_reserve_pct:
        return False, f"Cash reserve {cash_after/total_equity:.1%} below minimum {limits.min_cash_reserve_pct:.1%}"

    # Check 3: Daily loss limit
    if portfolio.total_pnl_pct < -limits.max_daily_loss_pct:
        return False, f"Daily loss {portfolio.total_pnl_pct:.1%} exceeds limit {limits.max_daily_loss_pct:.1%}"

    # Check 4: Max drawdown
    if portfolio.max_drawdown_pct > limits.max_portfolio_risk_pct * 100:
        return False, f"Drawdown {portfolio.max_drawdown_pct:.1f}% exceeds limit {limits.max_portfolio_risk_pct*100:.1f}%"

    # Check 5: Leverage
    total_exposure = sum(p.quantity * p.current_price for p in positions) + pos_value
    if total_exposure / total_equity > limits.max_leverage:
        return False, f"Leverage {total_exposure/total_equity:.1f}x exceeds limit {limits.max_leverage:.1f}x"

    return True, "Risk check passed"


# ─── Position Sizing ─────────────────────────────────────────────────────

def kelly_criterion(win_rate: float, avg_win_pct: float, avg_loss_pct: float) -> float:
    """
    Kelly Criterion: f* = (p·b - q) / b
    where p=win probability, q=loss probability, b=win/loss ratio
    Returns optimal bet size as fraction of capital.
    """
    if avg_loss_pct <= 0:
        return 0
    b = avg_win_pct / avg_loss_pct
    q = 1 - win_rate
    kelly = (win_rate * b - q) / b
    return max(0.0, min(kelly, 0.25))  # Cap at 25% (half-Kelly conservative)


def size_position(capital: float, price: float, volatility_pct: float,
                  risk_per_trade_pct: float = 0.02,
                  atr_stop_pct: float = 2.0) -> Tuple[int, float]:
    """
    Van Tharp position sizing: shares = (capital × risk%) / (price × stop%)
    """
    risk_amount = capital * risk_per_trade_pct
    stop_distance = price * (atr_stop_pct / 100)
    if stop_distance <= 0:
        return 0, 0
    shares = int(risk_amount / stop_distance)
    allocation = (shares * price) / capital if capital > 0 else 0
    return max(1, shares), round(allocation, 3)


# ─── Backtest Engine ─────────────────────────────────────────────────────

def run_backtest(capital: float, tickers: List[str], strategy: str = "momentum",
                 days: int = 252) -> Portfolio:
    """Simple backtest with synthetic data."""
    import random
    random.seed(42)

    prices = {}
    for t in tickers:
        base = 100 + random.random() * 100
        prices[t] = []
        px = base
        for _ in range(days):
            px *= 1 + random.gauss(0.0005, 0.015)
            prices[t].append(px)

    # Default risk limits
    limits = RiskLimits(
        max_position_size_pct=0.20,
        max_portfolio_risk_pct=0.25,
        max_correlation=0.7,
        min_cash_reserve_pct=0.10,
        max_daily_loss_pct=0.05,
        trailing_stop_pct=0.05,
        max_leverage=1.0,
    )

    cash = capital
    positions: List[Position] = []
    trade_log = []
    peak = capital
    max_dd = 0.0
    daily_values = []

    for day in range(50, days):
        # Generate signals
        for t in tickers[:]:
            hist = prices[t][:day+1]
            signal = generate_signals(t, hist, strategy)

            current_price = hist[-1]
            portfolio_value = cash + sum(p.quantity * prices[p.ticker][day] for p in positions)

            # Track drawdown
            if portfolio_value > peak:
                peak = portfolio_value
            dd = (peak - portfolio_value) / peak * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)

            daily_values.append(portfolio_value)

            if signal.signal == "BUY" and signal.confidence > 0.65 and cash > capital * 0.05:
                vol = signal.indicators.get("volatility_20", 20)
                qty, alloc = size_position(cash, current_price, vol)

                # Risk check
                test_order = Order(ticker=t, side=OrderSide.BUY, order_type=OrderType.MARKET,
                                   quantity=qty, price=current_price)
                test_portfolio = Portfolio(cash=cash, positions=positions,
                                           total_value=portfolio_value, peak_value=peak,
                                           max_drawdown_pct=max_dd)

                if check_risk(test_order, test_portfolio, limits, positions)[0]:
                    cost = qty * current_price
                    if cost <= cash * 0.9:
                        cash -= cost
                        positions.append(Position(ticker=t, quantity=qty, avg_price=current_price,
                                                  current_price=current_price))
                        trade_log.append(f"Day {day}: BUY {qty} {t} @ ${current_price:.2f}")

            elif signal.signal == "SELL" and signal.confidence > 0.6:
                for p in list(positions):
                    if p.ticker == t:
                        sale = p.quantity * current_price
                        cash += sale
                        pnl = sale - p.quantity * p.avg_price
                        trade_log.append(f"Day {day}: SELL {p.quantity} {t} @ ${current_price:.2f} | PnL: ${pnl:+.2f}")
                        positions.remove(p)
                        break

    # Final portfolio
    final_value = cash
    for p in positions:
        px = prices[p.ticker][-1]
        p.current_price = px
        p.pnl = p.quantity * (px - p.avg_price)
        p.pnl_pct = (px / p.avg_price - 1) * 100
        final_value += p.quantity * px

    total_pnl = final_value - capital
    total_pnl_pct = (final_value / capital - 1) * 100

    # Sharpe ratio
    if len(daily_values) > 1:
        d_returns = [(daily_values[i]/daily_values[i-1] - 1) for i in range(1, len(daily_values))]
        if d_returns:
            mean_ret = sum(d_returns) / len(d_returns)
            std_ret = math.sqrt(sum((r - mean_ret)**2 for r in d_returns) / (len(d_returns) - 1))
            sharpe = (mean_ret / std_ret * math.sqrt(252)) if std_ret > 0 else 0
        else:
            sharpe = 0
    else:
        sharpe = 0

    return Portfolio(
        cash=round(cash, 2),
        positions=positions,
        total_value=round(final_value, 2),
        total_pnl=round(total_pnl, 2),
        total_pnl_pct=round(total_pnl_pct, 2),
        max_drawdown_pct=round(max_dd, 2),
        peak_value=round(peak, 2),
        sharpe_ratio=round(sharpe, 2),
    )


# ─── Reports ─────────────────────────────────────────────────────────────

def format_signal(signal: SignalResult) -> str:
    bar = "═" * 64
    emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}.get(signal.signal, "⚪")
    return f"""
{bar}
{emoji} SIGNAL — {signal.ticker} — {signal.signal} (confidence: {signal.confidence:.0%})
{bar}

   Indicators:
""" + "\n".join(f"      {k}: {v}" for k, v in signal.indicators.items()) + f"""

   Reason: {signal.reason}

{bar}
✅ Signal analysis complete.
"""


def format_backtest(pf: Portfolio, strategy: str) -> str:
    bar = "═" * 64
    lines = [
        f"\n{bar}",
        f"📊 BACKTEST RESULTS — {strategy.upper()} Strategy",
        f"{bar}",
        f"",
        f"   Final Value:    ${pf.total_value:,.2f}",
        f"   Total PnL:      ${pf.total_pnl:+,.2f} ({pf.total_pnl_pct:+.2f}%)",
        f"   Cash:           ${pf.cash:,.2f}",
        f"   Max Drawdown:   {pf.max_drawdown_pct:.2f}%",
        f"   Sharpe Ratio:   {pf.sharpe_ratio:.2f}",
        f"   Positions:      {len(pf.positions)} open",
        f"",
    ]

    if pf.positions:
        lines.append(f"   Open Positions:")
        for p in pf.positions:
            lines.append(f"      {p.ticker}: {p.quantity} shares @ ${p.avg_price:.2f} | PnL: ${p.pnl:+,.2f} ({p.pnl_pct:+.1f}%)")

    lines.extend([f"", f"{bar}", f"✅ Backtest complete.\n"])
    return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Algorithmic Trading Bot — Signals + Risk + Position Sizing + Backtest",
        epilog="Cycle 11-12 Autonomous Evolution | Claude Code Self-Evolution"
    )
    subparsers = parser.add_subparsers(dest="command", help="Mode")

    # Signal
    sig_parser = subparsers.add_parser("signal", help="Generate trading signals")
    sig_parser.add_argument("--ticker", required=True)
    sig_parser.add_argument("--method", default="sma-crossover",
                            choices=["sma-crossover", "rsi", "momentum"])
    sig_parser.add_argument("--generate-prices", type=int, default=100,
                            help="Generate N synthetic price bars")
    sig_parser.add_argument("--json", default=None)

    # Risk
    risk_parser = subparsers.add_parser("risk", help="Position sizing + risk check")
    risk_parser.add_argument("--capital", type=float, default=100_000)
    risk_parser.add_argument("--price", type=float, default=100.0)
    risk_parser.add_argument("--volatility", type=float, default=25.0, help="Annualized volatility %")
    risk_parser.add_argument("--risk-per-trade", type=float, default=0.02)
    risk_parser.add_argument("--json", default=None)

    # Backtest
    back_parser = subparsers.add_parser("backtest", help="Run backtest")
    back_parser.add_argument("--capital", type=float, default=100_000)
    back_parser.add_argument("--strategy", default="momentum",
                             choices=["sma-crossover", "rsi", "momentum"])
    back_parser.add_argument("--tickers", type=lambda s: [t.strip() for t in s.split(",")],
                             default=["AAPL", "MSFT", "GOOGL"])
    back_parser.add_argument("--json", default=None)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "signal":
        import random
        random.seed(42)
        prices = [100.0]
        for _ in range(args.generate_prices - 1):
            prices.append(prices[-1] * (1 + random.gauss(0.0005, 0.015)))
        signal = generate_signals(args.ticker, prices, args.method)
        print(format_signal(signal))
        if args.json:
            with open(args.json, "w") as f:
                json.dump({"ticker": signal.ticker, "signal": signal.signal,
                           "confidence": signal.confidence, "indicators": signal.indicators,
                           "reason": signal.reason}, f, indent=2)

    elif args.command == "risk":
        shares, alloc = size_position(args.capital, args.price, args.volatility, args.risk_per_trade)
        kelly = kelly_criterion(win_rate=0.55, avg_win_pct=10.0, avg_loss_pct=5.0)
        print(f"""
════════════════════════════════════════════════════════════════
⚖️ POSITION SIZING & RISK
════════════════════════════════════════════════════════════════

   Capital:          ${args.capital:,.2f}
   Price:            ${args.price:.2f}
   Risk per Trade:   {args.risk_per_trade:.1%}

   Position Size:    {shares} shares (${shares * args.price:,.2f} = {alloc:.1%} allocation)
   Kelly Criterion:  {kelly:.1%} (half-Kelly: {kelly/2:.1%})

════════════════════════════════════════════════════════════════
✅ Risk analysis complete.
""")
        if args.json:
            with open(args.json, "w") as f:
                json.dump({"shares": shares, "allocation_pct": alloc, "kelly": kelly}, f, indent=2)

    elif args.command == "backtest":
        pf = run_backtest(args.capital, args.tickers, args.strategy)
        print(format_backtest(pf, args.strategy))
        if args.json:
            with open(args.json, "w") as f:
                pos_data = [{"ticker": p.ticker, "quantity": p.quantity,
                             "avg_price": p.avg_price, "pnl": p.pnl,
                             "pnl_pct": p.pnl_pct} for p in pf.positions]
                json.dump({"total_value": pf.total_value, "total_pnl": pf.total_pnl,
                           "total_pnl_pct": pf.total_pnl_pct, "max_drawdown_pct": pf.max_drawdown_pct,
                           "sharpe_ratio": pf.sharpe_ratio, "positions": pos_data,
                           "cash": pf.cash}, f, indent=2)


if __name__ == "__main__":
    main()
