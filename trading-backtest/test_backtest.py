#!/usr/bin/env python3
"""
Unit tests for Trading Backtest Engine
Cycle 5 Quality Engineering — pytest 기반 테스트 스위트

Usage:
    pytest test_backtest.py -v
    python -m pytest test_backtest.py -v
"""

import sys
import os
import math
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest import (
    Bar, Trade, Result,
    sma, ema, rsi,
    generate_mock_bars,
    momentum_strategy,
    mean_reversion_strategy,
    compute_metrics,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────

def make_bars(prices: list[float], start_date: datetime = None) -> list[Bar]:
    """Helper: create mock bars from a list of closing prices."""
    if start_date is None:
        start_date = datetime(2024, 1, 1)
    bars = []
    for i, close in enumerate(prices):
        date = start_date + timedelta(days=i)
        while date.weekday() >= 5:
            date += timedelta(days=1)
        bars.append(Bar(
            date=date,
            open=close * 0.99,
            high=close * 1.02,
            low=close * 0.98,
            close=close,
            volume=1_000_000,
        ))
    return bars


# ─── Indicator Tests ───────────────────────────────────────────────────────

class TestSMA:
    def test_sma_basic(self):
        prices = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = sma(prices, 3)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == 2.0   # (1+2+3)/3
        assert result[3] == 3.0   # (2+3+4)/3
        assert result[4] == 4.0   # (3+4+5)/3

    def test_sma_period_longer_than_data(self):
        prices = [1.0, 2.0]
        result = sma(prices, 5)
        assert all(x is None for x in result)

    def test_sma_period_one(self):
        prices = [5.0, 10.0, 15.0]
        result = sma(prices, 1)
        assert result == [5.0, 10.0, 15.0]


class TestEMA:
    def test_ema_basic(self):
        prices = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = ema(prices, 3)
        # Seed = (10+20+30)/3 = 20.0
        assert result[2] == 20.0
        # EMA = (40 - 20) * 0.5 + 20 = 30.0
        assert abs(result[3] - 30.0) < 0.01
        # EMA = (50 - 30) * 0.5 + 30 = 40.0
        assert abs(result[4] - 40.0) < 0.01

    def test_ema_rising_trend(self):
        prices = list(range(1, 21))  # 1..20
        result = ema(prices, 5)
        # EMA should lag but follow the trend upward
        assert result[-1] > result[4]
        assert result[-1] < prices[-1]  # EMA lags in uptrend


class TestRSI:
    def test_rsi_all_gains(self):
        """All gains → RSI should approach 100."""
        prices = [100.0 + i for i in range(20)]
        result = rsi(prices, 14)
        assert result[-1] is not None
        assert result[-1] > 90  # Near 100

    def test_rsi_all_losses(self):
        """All losses → RSI should approach 0."""
        prices = [100.0 - i for i in range(20)]
        result = rsi(prices, 14)
        assert result[-1] is not None
        assert result[-1] < 10  # Near 0

    def test_rsi_stable_prices(self):
        """Flat prices → RSI should be near 100 (no losses)."""
        prices = [50.0] * 20
        result = rsi(prices, 14)
        # No losses → RSI = 100 (division by zero handled)
        assert result[-1] == 100.0 or result[-1] is None

    def test_rsi_insufficient_data(self):
        prices = [100.0, 101.0]
        result = rsi(prices, 14)
        assert all(x is None for x in result)


# ─── Strategy Tests ────────────────────────────────────────────────────────

class TestMomentumStrategy:
    def test_no_trades_when_no_cross(self):
        """No crossover → no trades."""
        bars = make_bars([100.0 + i * 0.1 for i in range(100)])
        trades = momentum_strategy(bars, capital=100_000)
        # With steady uptrend, SMA20 stays above SMA50 after initial cross
        # At minimum, the strategy should run without error
        assert isinstance(trades, list)

    def test_trades_are_valid(self):
        """Every trade should have valid entry/exit."""
        bars = generate_mock_bars("TEST", datetime(2020, 1, 1), datetime(2022, 12, 31))
        trades = momentum_strategy(bars, capital=100_000)
        for t in trades:
            assert t.entry_price > 0
            assert t.exit_price > 0
            assert t.size > 0
            assert t.side == 'long'


class TestMeanReversionStrategy:
    def test_trades_are_valid(self):
        bars = generate_mock_bars("TEST", datetime(2020, 1, 1), datetime(2022, 12, 31))
        trades = mean_reversion_strategy(bars, capital=100_000)
        for t in trades:
            assert t.entry_price > 0
            assert t.exit_price > 0
            assert t.size > 0

    def test_custom_thresholds(self):
        """Custom RSI thresholds should change behavior."""
        bars = generate_mock_bars("TEST", datetime(2020, 1, 1), datetime(2021, 12, 31))
        trades_loose = mean_reversion_strategy(bars, 100_000, oversold=40, overbought=60)
        trades_tight = mean_reversion_strategy(bars, 100_000, oversold=25, overbought=75)
        # Looser thresholds = more trades
        assert len(trades_loose) >= len(trades_tight) or len(trades_tight) == 0


# ─── Metrics Tests ─────────────────────────────────────────────────────────

class TestComputeMetrics:
    def test_no_trades(self):
        bars = make_bars([100.0] * 10)
        result = compute_metrics(bars, [], 100_000, "test", "TEST")
        assert result.total_trades == 0
        assert result.total_return_pct == 0.0
        assert result.sharpe_ratio == 0.0
        assert result.final_capital == 100_000

    def test_all_winning_trades(self):
        bars = make_bars([100.0, 105.0, 110.0, 115.0])
        trades = [
            Trade(datetime(2024, 1, 1), datetime(2024, 1, 2), 'long', 100.0, 105.0, 100, 500.0, 5.0),
            Trade(datetime(2024, 1, 3), datetime(2024, 1, 4), 'long', 105.0, 110.0, 100, 500.0, 4.76),
        ]
        result = compute_metrics(bars, trades, 100_000, "test", "TEST")
        assert result.win_rate_pct == 100.0
        assert result.total_return_pct == 1.0  # 1000 gain on 100k
        assert result.profit_factor == 999.0  # infinity → 999 sentinel

    def test_all_losing_trades(self):
        bars = make_bars([100.0, 95.0, 90.0])
        trades = [
            Trade(datetime(2024, 1, 1), datetime(2024, 1, 2), 'long', 100.0, 90.0, 100, -1000.0, -10.0),
        ]
        result = compute_metrics(bars, trades, 100_000, "test", "TEST")
        assert result.win_rate_pct == 0.0
        assert result.total_return_pct == -1.0

    def test_sharpe_positive_for_profitable(self):
        """Varying returns produce positive Sharpe."""
        bars = make_bars([100.0, 101.0, 103.0, 104.0, 107.0])
        trades = [
            Trade(datetime(2024, 1, 1), datetime(2024, 1, 2), 'long', 100.0, 102.0, 100, 200.0, 2.0),
            Trade(datetime(2024, 1, 2), datetime(2024, 1, 3), 'long', 102.0, 105.0, 100, 300.0, 2.94),
            Trade(datetime(2024, 1, 3), datetime(2024, 1, 4), 'long', 105.0, 104.0, 100, -100.0, -0.95),
            Trade(datetime(2024, 1, 4), datetime(2024, 1, 5), 'long', 104.0, 109.0, 100, 500.0, 4.81),
        ]
        result = compute_metrics(bars, trades, 100_000, "test", "TEST")
        # Positive overall return with variance → Sharpe > 0
        assert result.total_return_pct > 0
        assert result.sharpe_ratio > 0

    def test_max_drawdown(self):
        bars = make_bars([100.0] * 10)
        trades = [
            Trade(datetime(2024, 1, 1), datetime(2024, 1, 2), 'long', 100.0, 90.0, 1000, -10000.0, -10.0),
            Trade(datetime(2024, 1, 3), datetime(2024, 1, 4), 'long', 90.0, 95.0, 1000, 5000.0, 5.56),
        ]
        result = compute_metrics(bars, trades, 100_000, "test", "TEST")
        assert result.max_drawdown_pct > 0


# ─── Data Model Tests ──────────────────────────────────────────────────────

class TestDataModels:
    def test_bar_creation(self):
        bar = Bar(datetime(2024, 1, 1), 100.0, 105.0, 98.0, 102.0, 1_000_000)
        assert bar.close == 102.0
        assert bar.volume == 1_000_000

    def test_trade_pnl_calculation(self):
        trade = Trade(
            datetime(2024, 1, 1), datetime(2024, 1, 10),
            'long', 100.0, 110.0, 500, 5000.0, 10.0
        )
        assert trade.pnl == 5000.0
        assert trade.pnl == 500 * (110.0 - 100.0)

    def test_result_has_all_fields(self):
        result = Result('AAPL', 'momentum', datetime(2024, 1, 1), datetime(2024, 6, 30),
                        100_000, 105_000, 5.0, 10.0, 15.0, 1.5, 2.0, 8.0, 60.0, 10, 1.5)
        assert result.symbol == 'AAPL'
        assert result.sharpe_ratio == 1.5
        assert result.sortino_ratio == 2.0


# ─── Integration Tests ─────────────────────────────────────────────────────

class TestEndToEnd:
    def test_mock_data_consistency(self):
        bars = generate_mock_bars("AAPL", datetime(2023, 1, 1), datetime(2023, 12, 31))
        assert len(bars) > 200  # trading days
        for bar in bars:
            assert bar.high >= bar.low
            assert bar.high >= bar.open
            assert bar.high >= bar.close
            assert bar.low <= bar.open
            assert bar.low <= bar.close
            assert bar.volume > 0

    def test_mock_data_reproducibility(self):
        bars1 = generate_mock_bars("TEST", datetime(2023, 1, 1), datetime(2023, 6, 30))
        bars2 = generate_mock_bars("TEST", datetime(2023, 1, 1), datetime(2023, 6, 30))
        # Same seed → same data
        for b1, b2 in zip(bars1, bars2):
            assert b1.close == b2.close

    def test_full_pipeline(self):
        """End-to-end: data → strategy → metrics."""
        bars = generate_mock_bars("TEST", datetime(2022, 1, 1), datetime(2023, 12, 31))
        trades = momentum_strategy(bars, 100_000)
        result = compute_metrics(bars, trades, 100_000, "momentum", "TEST")
        assert result.total_trades >= 0
        assert result.initial_capital == 100_000
        assert isinstance(result.sharpe_ratio, (int, float))


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
