"""Replicator dynamics and Runge-Kutta 4 integration."""

from __future__ import annotations

import numpy as np


def replicator_dynamics(x, payoff_matrix, t=0.0) -> np.ndarray:
    """Replicator dynamics vector field.

    ``dx_i/dt = x_i * (f_i(x) - phi(x))`` where
    ``f_i(x) = sum_j A[i, j] * x[j]`` is the fitness of strategy ``i`` and
    ``phi(x) = sum_j x_j * f_j(x)`` is the population average fitness.
    """
    x = np.asarray(x, dtype=float)
    A = np.asarray(payoff_matrix, dtype=float)
    f = A @ x      # fitness of every strategy
    phi = x @ f    # average fitness
    return x * (f - phi)


def rk4(func, y0, t0, t1, dt):
    """Integrate ``y' = func(t, y)`` with classical 4th-order Runge-Kutta.

    Returns ``(ts, ys)`` with a sample at ``t0`` and after every step up to
    ``t1``.  The final step is shortened so the last returned time is exactly
    ``t1``.
    """
    y0 = np.asarray(y0, dtype=float)
    t = t0
    y = y0.copy()
    ts = [t0]
    ys = [y.copy()]
    while t < t1 - 1e-12:
        h = min(dt, t1 - t)
        k1 = func(t, y)
        k2 = func(t + 0.5 * h, y + 0.5 * h * k1)
        k3 = func(t + 0.5 * h, y + 0.5 * h * k2)
        k4 = func(t + h, y + h * k3)
        y = y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        t += h
        ts.append(t)
        ys.append(y.copy())
    return np.array(ts), np.array(ys)


def solve_replicator(x0, payoff_matrix, t_end=10.0, dt=0.01):
    """Integrate the replicator dynamics from initial profile ``x0``.

    Returns ``(ts, ys)`` where each ``ys[k]`` is the population profile at
    time ``ts[k]``.
    """
    A = np.asarray(payoff_matrix, dtype=float)

    def rhs(t, y):
        return replicator_dynamics(y, A, t)

    return rk4(rhs, x0, 0.0, t_end, dt)
