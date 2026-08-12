"""Discrete-time population simulation with fitness-based reproduction."""

from __future__ import annotations

import numpy as np


class Population:
    """A population of strategies evolving by selection and mutation.

    Every generation each strategy reproduces in proportion to its fitness
    (discrete-time replicator update):

        x_i' = x_i * f_i(x) / phi(x)

    When ``mutation_rate > 0`` a fraction ``m`` of each strategy's offspring
    mutates to a uniformly random *other* strategy, which prevents any
    strategy from going extinct:

        x_i'' = (1 - m) * x_i' + m / (n - 1) * sum_{j != i} x_j'
    """

    def __init__(
        self,
        payoff_matrix,
        initial_counts,
        total=1000,
        mutation_rate=0.0,
    ):
        self.A = np.asarray(payoff_matrix, dtype=float)
        self.n = self.A.shape[0]
        if self.n < 2:
            raise ValueError("need at least two strategies")
        self.total = int(total)
        if self.total <= 0:
            raise ValueError("total population size must be positive")
        self.mutation_rate = float(mutation_rate)
        if not 0.0 <= self.mutation_rate < 1.0:
            raise ValueError("mutation_rate must be in [0, 1)")

        counts = np.asarray(initial_counts, dtype=float)
        if counts.shape != (self.n,):
            raise ValueError(f"initial_counts must have length {self.n}")
        if counts.sum() <= 0:
            raise ValueError("initial_counts must sum to a positive value")
        if (counts < 0).any():
            raise ValueError("initial_counts must be non-negative")

        self.counts = counts
        self.frequencies = counts / counts.sum()
        self.generation = 0
        self.history = [self.frequencies.copy()]

    def step(self) -> np.ndarray:
        """Advance the population by one generation and return frequencies."""
        x = self.frequencies
        f = self.A @ x
        phi = float(x @ f)
        if phi <= 0:
            raise RuntimeError("non-positive average fitness")

        # Discrete-time replicator update.
        new_freqs = x * f / phi
        new_freqs = new_freqs / new_freqs.sum()

        # Uniform mutation.
        if self.mutation_rate > 0.0:
            m = self.mutation_rate
            new_freqs = new_freqs * (1.0 - m) + (m / (self.n - 1.0)) * (
                1.0 - new_freqs
            )

        new_freqs = np.clip(new_freqs, 0.0, 1.0)
        new_freqs = new_freqs / new_freqs.sum()

        self.frequencies = new_freqs
        self.counts = new_freqs * self.total
        self.generation += 1
        self.history.append(new_freqs.copy())
        return new_freqs

    def run(self, generations: int) -> np.ndarray:
        """Run ``generations`` generations and return final frequencies."""
        for _ in range(int(generations)):
            self.step()
        return self.frequencies

    @property
    def surviving_strategies(self) -> list:
        """Indices of strategies with frequency above a small threshold."""
        return [i for i in range(self.n) if self.frequencies[i] > 1e-6]
