"""Viral growth engine — simulates user growth with the K-factor model.

Model
-----
K-factor:        K = i × c                (invites per user × conversion rate)
Decay:           K(t) = K₀ · e^(−δ·t)     (saturation toward market limit)
Growth (waves):  each cycle adds a new wave of users equal to the previous
                 wave scaled by the current effective K. With a constant K
                 this reproduces the closed form

                     users_n = users₀ · (1 + K + K² + … + Kⁿ)

                 and when K = 1,  users_n = users₀ · (n + 1).
"""

from dataclasses import dataclass

from src.decay import DecayType, effective_k
from src.loops import LOOPS, LoopType


@dataclass
class CycleResult:
    """The state of the simulation after one cycle.

    Attributes:
        cycle: Zero-based cycle index (0 = seed users, before any growth).
        days: Elapsed days since the start of the simulation.
        k: Effective K-factor used during this cycle.
        new_users: Users added by this cycle's wave.
        total_users: Cumulative users after this cycle.
    """

    cycle: int
    days: float
    k: float
    new_users: float
    total_users: float


@dataclass
class Comparison:
    """Outcome of comparing a fast, low-K loop against a slow, high-K loop.

    Attributes:
        total_days: The fixed time horizon both scenarios run over.
        fast_label: Human-readable description of the fast scenario.
        slow_label: Human-readable description of the slow scenario.
        fast_users: Cumulative users for the fast scenario.
        slow_users: Cumulative users for the slow scenario.
        fast_cycles: Number of cycles the fast loop completed.
        slow_cycles: Number of cycles the slow loop completed.
    """

    total_days: int
    fast_label: str
    slow_label: str
    fast_users: float
    slow_users: float
    fast_cycles: int
    slow_cycles: int

    @property
    def winner(self) -> str:
        """Name of the winning scenario ('fast' or 'slow')."""
        return "fast" if self.fast_users >= self.slow_users else "slow"

    @property
    def multiple(self) -> float:
        """How many times the winner beats the loser."""
        if min(self.fast_users, self.slow_users) <= 0:
            return float("inf")
        return max(self.fast_users, self.slow_users) / min(self.fast_users, self.slow_users)


class ViralEngine:
    """Simulates viral user growth using the K-factor model with decay.

    Args:
        k: Initial K-factor K₀. If None, the loop type's default is used.
        cycles: Number of viral cycles to simulate.
        decay_rate: Saturation decay rate δ in K(t) = K₀·e^(−δt).
        cycle_time_days: Days per cycle. Controls how many cycles fit in a
            fixed time horizon.
        initial_users: Seed user count users₀.
        loop_type: One of the four defined viral loop types.
    """

    def __init__(
        self,
        k: float | None = None,
        cycles: int = 10,
        decay_rate: float = 0.05,
        cycle_time_days: float = 1.0,
        initial_users: int = 100,
        loop_type: LoopType = LoopType.ORGANIC,
    ):
        self.loop = LOOPS[loop_type]
        self.loop_type = loop_type
        self.initial_users = initial_users
        self.cycles = cycles
        self.decay_rate = decay_rate
        self.cycle_time_days = cycle_time_days
        self.k = self.loop.default_k if k is None else k

    # ── Decay ──────────────────────────────────────────────────────

    def effective_k_at(
        self, t: float, decay_type: DecayType = DecayType.EXPONENTIAL
    ) -> float:
        """Return the effective K-factor at elapsed time `t` days.

        Implements K(t) = K₀ · e^(−δ·t) under exponential decay.
        """
        return effective_k(self.k, self.decay_rate, t, decay_type)

    # ── Simulation ─────────────────────────────────────────────────

    def simulate(self, cycles: int | None = None) -> list[CycleResult]:
        """Run the simulation cycle by cycle.

        Args:
            cycles: Overrides the number of cycles if given.

        Returns:
            A list of CycleResult entries for cycles 0..n. Cycle 0 holds
            the seed users with no growth (new_users = 0).
        """
        n = self.cycles if cycles is None else cycles
        total = float(self.initial_users)
        wave = float(self.initial_users)
        results = [CycleResult(cycle=0, days=0.0, k=self.k, new_users=0.0, total_users=total)]

        for i in range(1, n + 1):
            t = i * self.cycle_time_days
            k_i = self.effective_k_at(t)
            new_users = wave * k_i
            wave = new_users
            total += new_users
            results.append(CycleResult(cycle=i, days=t, k=k_i, new_users=new_users, total_users=total))

        return results

    # ── Closed-form helpers ────────────────────────────────────────

    @staticmethod
    def users_after_n_cycles(k: float, cycles: int, initial_users: int = 100) -> float:
        """Closed-form cumulative users after `cycles` cycles.

        users_n = users₀ · (1 + K + K² + … + Kⁿ)  for K ≠ 1
        users_n = users₀ · (n + 1)                 for K = 1
        """
        if abs(k - 1.0) < 1e-9:
            return float(initial_users * (cycles + 1))
        return float(initial_users * (k ** (cycles + 1) - 1) / (k - 1))

    @staticmethod
    def comparative_table(
        k_values: list[float],
        cycles: int = 10,
        initial_users: int = 100,
    ) -> list[tuple[float, float]]:
        """Build a table of K-value vs cumulative users after `cycles` cycles."""
        return [
            (k, ViralEngine.users_after_n_cycles(k, cycles, initial_users))
            for k in k_values
        ]

    # ── Cycle-time comparison ──────────────────────────────────────

    @staticmethod
    def compare(
        total_days: int = 30,
        initial_users: int = 100,
        decay_rate: float = 0.05,
        fast_k: float = 0.8,
        fast_cycle: float = 3.0,
        slow_k: float = 1.2,
        slow_cycle: float = 30.0,
    ) -> Comparison:
        """Compare a fast small-K loop against a slow large-K loop.

        The point: over a fixed horizon, cycle velocity beats raw K-factor.
        K = 0.8 on a 3-day cycle completes floor(30/3) = 10 cycles while
        K = 1.2 on a 30-day cycle completes only floor(30/30) = 1 cycle.
        """
        fast_cycles = max(1, int(total_days // fast_cycle))
        slow_cycles = max(1, int(total_days // slow_cycle))

        fast_engine = ViralEngine(
            k=fast_k,
            cycles=fast_cycles,
            cycle_time_days=fast_cycle,
            decay_rate=decay_rate,
            initial_users=initial_users,
        )
        slow_engine = ViralEngine(
            k=slow_k,
            cycles=slow_cycles,
            cycle_time_days=slow_cycle,
            decay_rate=decay_rate,
            initial_users=initial_users,
        )

        fast_users = fast_engine.simulate()[-1].total_users
        slow_users = slow_engine.simulate()[-1].total_users

        return Comparison(
            total_days=total_days,
            fast_label=f"K={fast_k:.2f} @ {fast_cycle:.0f}-day cycle",
            slow_label=f"K={slow_k:.2f} @ {slow_cycle:.0f}-day cycle",
            fast_users=fast_users,
            slow_users=slow_users,
            fast_cycles=fast_cycles,
            slow_cycles=slow_cycles,
        )
