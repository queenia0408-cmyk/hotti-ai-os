"""Game definitions for evolutionary game theory.

A symmetric 2-player game is specified by a payoff matrix ``A`` where
``A[i, j]`` is the payoff to a player using pure strategy ``i`` against an
opponent using pure strategy ``j``.  For a population profile ``x`` (a
probability vector over strategies) the expected payoff to strategy ``i`` is

    f_i(x) = sum_j A[i, j] * x[j]
"""

from __future__ import annotations

import numpy as np

# --- Canonical 2x2 games ------------------------------------------------

# Prisoner's Dilemma: T=5 > R=3 > P=1 > S=0
#   strategy 0 = Cooperate, strategy 1 = Defect
PRISONERS_DILEMMA = np.array(
    [
        [3.0, 0.0],  # cooperate
        [5.0, 1.0],  # defect
    ]
)

# Hawk-Dove (a.k.a. Snowdrift / Chicken): strategy 0 = Hawk, 1 = Dove
HAWK_DOVE = np.array(
    [
        [0.0, 3.0],
        [1.0, 2.0],
    ]
)

# Stag Hunt: strategy 0 = Stag, 1 = Hare
STAG_HUNT = np.array(
    [
        [4.0, 0.0],
        [2.0, 2.0],
    ]
)

# Pure Coordination: strategy 0 = A, 1 = B
COORDINATION = np.array(
    [
        [2.0, 0.0],
        [0.0, 2.0],
    ]
)

GAMES = {
    "prisoner": PRISONERS_DILEMMA,
    "hawk-dove": HAWK_DOVE,
    "stag-hunt": STAG_HUNT,
    "coordination": COORDINATION,
}

GAME_NAMES = {
    "prisoner": "Prisoner's Dilemma",
    "hawk-dove": "Hawk-Dove",
    "stag-hunt": "Stag Hunt",
    "coordination": "Coordination",
}

GAME_STRATEGIES = {
    "prisoner": ["Cooperate", "Defect"],
    "hawk-dove": ["Hawk", "Dove"],
    "stag-hunt": ["Stag", "Hare"],
    "coordination": ["A", "B"],
}


def fitness(payoff_matrix, x) -> np.ndarray:
    """Expected payoff vector: ``f_i(x) = sum_j A[i, j] * x[j]``."""
    A = np.asarray(payoff_matrix, dtype=float)
    x = np.asarray(x, dtype=float)
    return A @ x


def average_fitness(payoff_matrix, x) -> float:
    """Population average payoff ``phi(x) = sum_j x_j * f_j(x)``."""
    f = fitness(payoff_matrix, x)
    x = np.asarray(x, dtype=float)
    return float(x @ f)


def pure_nash(payoff_matrix) -> list:
    """Pure symmetric Nash equilibria of a symmetric game.

    A pure strategy ``i`` is a (symmetric) Nash equilibrium when it is a
    best response to itself: ``A[i, i] >= A[j, i]`` for every pure ``j``.
    """
    A = np.asarray(payoff_matrix, dtype=float)
    n = A.shape[0]
    return [i for i in range(n) if all(A[i, i] >= A[j, i] for j in range(n))]


def mixed_nash(payoff_matrix):
    """Interior mixed-strategy Nash equilibrium for a 2x2 symmetric game.

    Returns the probability vector ``[p, 1-p]`` for the equilibrium in which
    both players mix, or ``None`` when no interior mixed equilibrium exists.
    """
    A = np.asarray(payoff_matrix, dtype=float)
    if A.shape != (2, 2):
        return None
    a, b = A[0, 0], A[0, 1]
    c, d = A[1, 0], A[1, 1]
    denom = a - b - c + d
    if abs(denom) < 1e-12:
        return None  # degenerate / continuum of equilibria
    p = (d - b) / denom
    if not (0.0 < p < 1.0):
        return None
    return np.array([p, 1.0 - p])


def is_best_response(payoff_matrix, strategy_index, x) -> bool:
    """Whether pure strategy ``strategy_index`` is a best response to ``x``."""
    A = np.asarray(payoff_matrix, dtype=float)
    x = np.asarray(x, dtype=float)
    f = A @ x
    return bool(f[strategy_index] >= f.max() - 1e-12)
