"""Phase portraits and trajectory plots for 2-strategy games (matplotlib)."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from src.replicator import replicator_dynamics, solve_replicator


def flow_1d(x, payoff_matrix) -> float:
    """dx/dt of the frequency of strategy 0 when strategy 1 has frequency 1-x."""
    A = np.asarray(payoff_matrix, dtype=float)
    dx = replicator_dynamics(np.array([x, 1.0 - x]), A)
    return float(dx[0])


def find_equilibria_1d(payoff_matrix) -> list:
    """Equilibria of a 2-strategy game on the simplex line ``x`` in [0, 1].

    Returns a list of dicts ``{"x": float, "stable": bool, "unstable": bool}``
    sorted by ``x``.  Uses the identity ``g(x) = x*(1-x)*(f0(x)-f1(x))`` and
    the sign of ``g'(x)`` at each equilibrium.
    """
    A = np.asarray(payoff_matrix, dtype=float)
    a, b = A[0, 0], A[0, 1]
    c, d = A[1, 0], A[1, 1]
    alpha = b - d
    beta = a - b - c + d

    eqs = []

    def add(x, gp):
        eqs.append({"x": float(x), "stable": gp < -1e-9, "unstable": gp > 1e-9})

    # Endpoints are always equilibria of the replicator equation.
    add(0.0, alpha)     # g'(0) = b - d
    add(1.0, c - a)     # g'(1) = c - a

    # Interior equilibrium where f0 == f1, i.e. alpha + beta*x = 0.
    if abs(beta) > 1e-12:
        xstar = -alpha / beta
        if 0.0 < xstar < 1.0:
            add(xstar, xstar * (1.0 - xstar) * beta)  # g'(x*) = x*(1-x)*beta
    eqs.sort(key=lambda e: e["x"])
    return eqs


def phase_portrait(payoff_matrix, strategy_names=None, trajectories=None,
                   save_path=None):
    """Draw the 1-D phase line plus example trajectories.

    The top panel is the simplex line ``x`` in [0, 1] (frequency of strategy
    0) with arrows showing the direction of ``dx/dt`` and coloured markers for
    stable (green) / unstable (red) / degenerate (grey) equilibria.  The
    bottom panel shows ``x(t)`` obtained by integrating the replicator
    equation from several starting points.

    Returns the matplotlib ``Figure``.
    """
    A = np.asarray(payoff_matrix, dtype=float)
    if trajectories is None:
        trajectories = [0.1, 0.3, 0.5, 0.7, 0.9]

    fig, (ax_line, ax_ts) = plt.subplots(
        2, 1, figsize=(9, 5.5), gridspec_kw={"height_ratios": [1, 1.4]}
    )

    # --- Phase line ----------------------------------------------------
    xs = np.linspace(0.0, 1.0, 401)
    dxs = np.array([flow_1d(xi, A) for xi in xs])
    scale = float(np.max(np.abs(dxs))) + 1e-12

    ax_line.axhline(0.0, color="0.75", lw=2, zorder=1)
    for xi, dxi in zip(xs[::20], dxs[::20]):
        ax_line.arrow(
            xi, 0.0, dxi / scale * 0.06, 0.0,
            head_width=0.03, head_length=0.012,
            fc="0.3", ec="0.3", length_includes_head=True, zorder=2,
        )

    for eq in find_equilibria_1d(A):
        if eq["stable"]:
            color, marker, label = "green", "o", "stable"
        elif eq["unstable"]:
            color, marker, label = "red", "o", "unstable"
        else:
            color, marker, label = "0.4", "s", "degenerate"
        ax_line.plot(eq["x"], 0.0, marker=marker, ms=11, color=color, zorder=3)
        ax_line.annotate(
            f"x={eq['x']:.2f}\n{label}",
            (eq["x"], 0.0), textcoords="offset points",
            xytext=(0, 14), ha="center", fontsize=8, color=color,
        )

    ax_line.set_xlim(-0.05, 1.05)
    ax_line.set_ylim(-0.12, 0.12)
    ax_line.set_yticks([])
    ax_line.set_xlabel("frequency of strategy 0, x")
    ax_line.set_title("Phase line: direction of dx/dt on the simplex")

    # --- Trajectories --------------------------------------------------
    for x0 in trajectories:
        if not 0.0 <= x0 <= 1.0:
            continue
        ts, ys = solve_replicator([x0, 1.0 - x0], A, t_end=20.0, dt=0.01)
        ax_ts.plot(ts, ys[:, 0], label=f"x(0)={x0:g}")
    ax_ts.set_xlabel("time t")
    ax_ts.set_ylabel("frequency of strategy 0")
    ax_ts.set_ylim(-0.02, 1.02)
    ax_ts.set_title("Replicator-dynamics trajectories")
    ax_ts.legend(fontsize=8, ncol=2, loc="best")

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_trajectories(payoff_matrix, start_points=None, t_end=20.0, dt=0.01,
                      save_path=None):
    """Plot ``x(t)`` (frequency of strategy 0) from several starting points."""
    A = np.asarray(payoff_matrix, dtype=float)
    if start_points is None:
        start_points = [0.1, 0.3, 0.5, 0.7, 0.9]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for x0 in start_points:
        if not 0.0 <= x0 <= 1.0:
            continue
        ts, ys = solve_replicator([x0, 1.0 - x0], A, t_end=t_end, dt=dt)
        ax.plot(ts, ys[:, 0], label=f"x(0)={x0:g}")
    ax.set_xlabel("time t")
    ax.set_ylabel("frequency of strategy 0")
    ax.set_title("Replicator-dynamics trajectories")
    ax.legend(fontsize=8)
    ax.set_ylim(-0.02, 1.02)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig
