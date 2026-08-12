"""Tests for the K-factor viral coefficient simulator.

Covers:
- Exponential decay model K(t) = K₀·e^(−δt)
- Four viral loop type definitions and their ordering
- Closed-form geometric growth (users_n = users₀·(1 + K + … + Kⁿ))
- K = 1 linear-growth special case (users_n = users₀·(n + 1))
- Cycle-time comparison (K=0.8@3d beats K=1.2@30d over 30 days)
- Comparative table (K-value vs users after N cycles)
"""

import sys
from math import exp
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.decay import DecayType, constant_k, effective_k, exponential_decay
from src.engine import CycleResult, Comparison, ViralEngine
from src.loops import LOOPS, LoopType, ViralLoop


# ── Decay Model Tests ──────────────────────────────────────────────

class TestDecayModel:
    """Test the K-factor decay models."""

    def test_exponential_decay_formula(self):
        """K_t = K_0 · e^(−δt) is computed exactly."""
        k0, delta, t = 0.8, 0.05, 3.0
        expected = k0 * exp(-delta * t)
        assert exponential_decay(k0, delta, t) == pytest.approx(expected)

    def test_exponential_decay_at_zero(self):
        """K(0) = K₀ — no decay has elapsed at t=0."""
        assert exponential_decay(0.8, 0.05, 0.0) == pytest.approx(0.8)

    def test_decay_is_monotonically_decreasing(self):
        """Effective K decreases as time passes for a positive δ."""
        ks = [exponential_decay(0.8, 0.05, t) for t in range(0, 20)]
        assert all(ks[i] > ks[i + 1] for i in range(len(ks) - 1))

    def test_constant_model_no_decay(self):
        """The constant model keeps K unchanged regardless of time."""
        assert constant_k(1.2, 0.5, 100) == 1.2

    def test_effective_k_dispatch(self):
        """effective_k dispatches on the decay type."""
        assert effective_k(0.8, 0.05, 3.0, DecayType.CONSTANT) == 0.8
        assert effective_k(0.8, 0.05, 3.0, DecayType.EXPONENTIAL) == pytest.approx(
            0.8 * exp(-0.05 * 3.0)
        )

    def test_effective_k_engine_default_is_exponential(self):
        """ViralEngine uses exponential decay by default."""
        engine = ViralEngine(k=0.8, decay_rate=0.05)
        assert engine.effective_k_at(3.0) == pytest.approx(0.8 * exp(-0.05 * 3.0))


# ── Loop Type Tests ────────────────────────────────────────────────

class TestLoopTypes:
    """Test the four viral loop archetypes."""

    def test_four_loop_types_defined(self):
        """Exactly four viral loop types exist."""
        assert len(LOOPS) == 4
        assert set(LOOPS) == {
            LoopType.ORGANIC,
            LoopType.INCENTIVIZED,
            LoopType.CONTENT,
            LoopType.EMBEDDED,
        }

    def test_k_ordering_embedded_highest(self):
        """K ordering: Embedded > Content > Incentivized > Organic."""
        ks = {
            LoopType.ORGANIC: LOOPS[LoopType.ORGANIC].default_k,
            LoopType.INCENTIVIZED: LOOPS[LoopType.INCENTIVIZED].default_k,
            LoopType.CONTENT: LOOPS[LoopType.CONTENT].default_k,
            LoopType.EMBEDDED: LOOPS[LoopType.EMBEDDED].default_k,
        }
        assert ks[LoopType.EMBEDDED] > ks[LoopType.CONTENT]
        assert ks[LoopType.CONTENT] > ks[LoopType.INCENTIVIZED]
        assert ks[LoopType.INCENTIVIZED] > ks[LoopType.ORGANIC]

    def test_cycle_time_ordering_embedded_fastest(self):
        """Embedded has the fastest cycle; content the slowest."""
        cts = {lt: loop.cycle_time_days for lt, loop in LOOPS.items()}
        assert cts[LoopType.EMBEDDED] < cts[LoopType.ORGANIC]
        assert cts[LoopType.ORGANIC] < cts[LoopType.INCENTIVIZED]
        assert cts[LoopType.INCENTIVIZED] < cts[LoopType.CONTENT]

    def test_distinct_default_k_and_cycle_times(self):
        """Every loop type has a unique K and unique cycle time."""
        ks = {loop.default_k for loop in LOOPS.values()}
        cts = {loop.cycle_time_days for loop in LOOPS.values()}
        assert len(ks) == 4
        assert len(cts) == 4

    def test_loop_metadata_present(self):
        """Every loop has a name, description, and mechanism."""
        for loop in LOOPS.values():
            assert isinstance(loop, ViralLoop)
            assert loop.name
            assert loop.description
            assert loop.mechanism


# ── Viral Engine Tests ─────────────────────────────────────────────

class TestViralEngine:
    """Test the simulation engine."""

    def test_geometric_series_no_decay(self):
        """users_n = users₀·(1 + K + … + Kⁿ) reproduces the closed form."""
        engine = ViralEngine(k=0.8, cycles=10, decay_rate=0.0, cycle_time_days=3.0)
        results = engine.simulate()
        expected = 100 * (1 - 0.8**11) / (1 - 0.8)
        assert results[-1].total_users == pytest.approx(expected)

    def test_k_equals_one_gives_linear_growth(self):
        """K = 1 → users_n = users₀·(n + 1)."""
        engine = ViralEngine(k=1.0, cycles=5, decay_rate=0.0)
        results = engine.simulate()
        assert results[-1].total_users == pytest.approx(100 * 6)

    def test_decay_reduces_final_users(self):
        """With decay, final users are lower than without decay."""
        no_decay = ViralEngine(k=1.2, cycles=10, decay_rate=0.0).simulate()[-1].total_users
        with_decay = ViralEngine(k=1.2, cycles=10, decay_rate=0.05).simulate()[-1].total_users
        assert with_decay < no_decay

    def test_loop_default_k_used_when_none(self):
        """Engine uses the loop's default K when none is given."""
        engine = ViralEngine(loop_type=LoopType.CONTENT)
        assert engine.k == LOOPS[LoopType.CONTENT].default_k

    def test_explicit_k_overrides_loop_default(self):
        """Explicit k overrides the loop default."""
        engine = ViralEngine(k=0.9, loop_type=LoopType.CONTENT)
        assert engine.k == 0.9

    def test_simulation_is_monotonic(self):
        """Total users never decrease across cycles."""
        engine = ViralEngine(k=0.6, cycles=20, decay_rate=0.05)
        totals = [r.total_users for r in engine.simulate()]
        assert totals == sorted(totals)
        assert len(totals) == 21  # cycles 0..20

    def test_cycle_time_comparison_formula(self):
        """Users after T days = simulate K over ⌊T / cycle_time⌋ cycles."""
        engine = ViralEngine(k=0.8, cycles=10, decay_rate=0.0, cycle_time_days=3.0)
        total_30d = engine.simulate()[-1].total_users
        expected = ViralEngine.users_after_n_cycles(k=0.8, cycles=10)
        assert total_30d == pytest.approx(expected)

    def test_cycle_result_structure(self):
        """CycleResult rows carry cycle, days, k, new_users, total_users."""
        results = ViralEngine(k=0.5, cycles=2, decay_rate=0.0).simulate()
        assert isinstance(results[0], CycleResult)
        assert results[0].cycle == 0
        assert results[0].new_users == 0.0
        assert results[0].total_users == 100
        assert results[1].new_users == pytest.approx(50.0)


# ── Comparison Tests ───────────────────────────────────────────────

class TestComparison:
    """Test the cycle-time comparison feature."""

    def test_fast_small_beats_slow_big(self):
        """K=0.8@3d beats K=1.2@30d over 30 days (10 vs 1 cycles)."""
        fast = ViralEngine(k=0.8, cycles=10, cycle_time_days=3.0, decay_rate=0.0)
        slow = ViralEngine(k=1.2, cycles=1, cycle_time_days=30.0, decay_rate=0.0)
        assert fast.simulate()[-1].total_users > slow.simulate()[-1].total_users

    def test_compare_helper_fast_wins(self):
        """ViralEngine.compare returns both scenarios with fast winning."""
        cmp = ViralEngine.compare(total_days=30)
        assert isinstance(cmp, Comparison)
        assert cmp.fast_cycles == 10
        assert cmp.slow_cycles == 1
        assert cmp.fast_users > cmp.slow_users
        assert cmp.winner == "fast"

    def test_compare_helper_with_decay_fast_still_wins(self):
        """The comparison holds even under the default saturation decay."""
        cmp = ViralEngine.compare(total_days=30, decay_rate=0.05)
        assert cmp.fast_users > cmp.slow_users

    def test_compare_multiple_positive(self):
        """The win-multiple is greater than 1 and finite."""
        cmp = ViralEngine.compare(total_days=30)
        assert cmp.multiple > 1.0
        assert cmp.multiple != float("inf")

    def test_comparative_table_matches_closed_form(self):
        """Table of K vs users after 10 cycles matches the closed form."""
        rows = ViralEngine.comparative_table(k_values=[0.5, 1.0, 1.5])
        assert rows[0][0] == 0.5
        assert rows[0][1] == pytest.approx(100 * (1 - 0.5**11) / (1 - 0.5))
        assert rows[1] == pytest.approx((1.0, 100 * 11))
        assert rows[2][1] == pytest.approx(100 * (1.5**11 - 1) / (1.5 - 1))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
