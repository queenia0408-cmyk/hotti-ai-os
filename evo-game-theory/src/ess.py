"""Evolutionarily Stable Strategy (ESS) detection."""

from __future__ import annotations

import numpy as np

from src.games import mixed_nash


def is_ess(payoff_matrix, strategy, tol=1e-9) -> bool:
    """Return ``True`` when ``strategy`` is an evolutionarily stable strategy.

    A (possibly mixed) strategy ``p`` is an ESS if for every alternative
    (pure) strategy ``q != p``:

    * ``u(p, p) > u(q, p)``, or
    * ``u(p, p) == u(q, p)`` and ``u(p, q) > u(q, q)``.

    Because payoffs are bilinear in the strategies, checking every pure
    strategy ``q`` is sufficient.
    """
    A = np.asarray(payoff_matrix, dtype=float)
    n = A.shape[0]
    p = np.asarray(strategy, dtype=float)
    if p.ndim != 1 or p.shape[0] != n:
        raise ValueError("strategy must be a length-n vector")
    if p.sum() <= 0 or (p < -tol).any():
        raise ValueError("strategy must be a non-negative, non-zero vector")
    p = p / p.sum()

    u_pp = p @ A @ p
    for i in range(n):
        q = _pure(n, i)
        if np.allclose(q, p, atol=tol):
            continue
        u_qp = q @ A @ p
        if u_qp > u_pp + tol:
            return False
        if abs(u_qp - u_pp) <= tol:
            u_pq = p @ A @ q
            u_qq = q @ A @ q
            if u_pq <= u_qq + tol:
                return False
    return True


def find_pure_ess(payoff_matrix) -> list:
    """Indices of the pure-strategy ESS of a symmetric game."""
    A = np.asarray(payoff_matrix, dtype=float)
    n = A.shape[0]
    return [i for i in range(n) if is_ess(A, _pure(n, i))]


def find_ess(payoff_matrix) -> list:
    """All ESS of a symmetric game.

    Returns a list of ``("pure", index)`` entries plus, for 2x2 games, a
    ``("mixed", vector)`` entry when the interior mixed strategy is an ESS.
    """
    A = np.asarray(payoff_matrix, dtype=float)
    n = A.shape[0]
    results = [("pure", i) for i in find_pure_ess(A)]
    if n == 2:
        mixed = mixed_nash(A)
        if mixed is not None and is_ess(A, mixed):
            results.append(("mixed", mixed))
    return results


def _pure(n: int, i: int) -> np.ndarray:
    q = np.zeros(n)
    q[i] = 1.0
    return q
