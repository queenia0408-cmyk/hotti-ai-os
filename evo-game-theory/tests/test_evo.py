"""Tests for the evolutionary game theory simulator (P2-002)."""

import matplotlib

matplotlib.use("Agg")  # headless backend for tests

import numpy as np

from src.ess import find_pure_ess, is_ess
from src.games import (
    COORDINATION,
    HAWK_DOVE,
    PRISONERS_DILEMMA,
    STAG_HUNT,
    average_fitness,
    fitness,
    mixed_nash,
    pure_nash,
)
from src.population import Population
from src.replicator import replicator_dynamics, rk4, solve_replicator

ALL_GAMES = (PRISONERS_DILEMMA, HAWK_DOVE, STAG_HUNT, COORDINATION)


# 1 ------------------------------------------------------------------------
def test_replicator_dynamics_conserves_sum():
    """sum of frequencies stays exactly 1 under RK4 integration."""
    for A in ALL_GAMES:
        ts, ys = solve_replicator([0.7, 0.3], A, t_end=5.0, dt=0.01)
        assert np.allclose(ys.sum(axis=1), 1.0, atol=1e-8)


# 2 ------------------------------------------------------------------------
def test_prisoner_dilemma_defection_is_ess():
    """Defection is the unique ESS in the Prisoner's Dilemma."""
    assert is_ess(PRISONERS_DILEMMA, [0.0, 1.0])
    assert not is_ess(PRISONERS_DILEMMA, [1.0, 0.0])


# 3 ------------------------------------------------------------------------
def test_hawk_dove_mixed_nash():
    """The interior mixed strategy is the Nash equilibrium of Hawk-Dove."""
    p = mixed_nash(HAWK_DOVE)
    assert p is not None
    assert np.isclose(p[0], 0.5, atol=1e-9)
    f = HAWK_DOVE @ p
    assert np.isclose(f[0], f[1], atol=1e-12)  # opponent is indifferent
    assert is_ess(HAWK_DOVE, p)                # and it is the ESS


# 4 ------------------------------------------------------------------------
def test_stag_hunt_two_pure_nash():
    """Both (Stag, Stag) and (Hare, Hare) are Nash equilibria."""
    ne = pure_nash(STAG_HUNT)
    assert set(ne) == {0, 1}


# 5 ------------------------------------------------------------------------
def test_coordination_multiple_equilibria():
    """The coordination game has multiple pure equilibria."""
    ne = pure_nash(COORDINATION)
    assert len(ne) >= 2
    assert 0 in ne and 1 in ne


# 6 ------------------------------------------------------------------------
def test_rk4_convergence():
    """A smaller step size gives a more accurate RK4 solution."""
    def rhs(t, y):
        return -y  # exact solution y = e^{-t}

    t_end = 2.0
    exact = np.exp(-t_end)
    _, coarse = rk4(rhs, np.array([1.0]), 0.0, t_end, dt=0.1)
    _, fine = rk4(rhs, np.array([1.0]), 0.0, t_end, dt=0.01)
    err_coarse = abs(coarse[-1, 0] - exact)
    err_fine = abs(fine[-1, 0] - exact)
    assert err_fine < err_coarse
    assert err_fine < 1e-6


# 7 ------------------------------------------------------------------------
def test_ess_detection_correct():
    """is_ess correctly classifies known cases."""
    # Prisoner's Dilemma: only defection is ESS
    assert is_ess(PRISONERS_DILEMMA, [0.0, 1.0])
    assert not is_ess(PRISONERS_DILEMMA, [1.0, 0.0])
    assert not is_ess(PRISONERS_DILEMMA, [0.5, 0.5])
    # Hawk-Dove: the interior mixed strategy is the unique ESS
    assert is_ess(HAWK_DOVE, [0.5, 0.5])
    assert not is_ess(HAWK_DOVE, [1.0, 0.0])
    assert not is_ess(HAWK_DOVE, [0.0, 1.0])
    # Stag Hunt: both pure strategies are ESS
    assert is_ess(STAG_HUNT, [1.0, 0.0])
    assert is_ess(STAG_HUNT, [0.0, 1.0])
    # Coordination: both pure strategies are ESS, the mixed strategy is not
    assert is_ess(COORDINATION, [1.0, 0.0])
    assert is_ess(COORDINATION, [0.0, 1.0])
    assert not is_ess(COORDINATION, [0.5, 0.5])


# 8 ------------------------------------------------------------------------
def test_population_converges_to_ess():
    """The population simulation converges to the mixed ESS of Hawk-Dove."""
    pop = Population(HAWK_DOVE, [900, 100], total=1000, mutation_rate=0.0)
    pop.run(500)
    assert abs(pop.frequencies[0] - 0.5) < 1e-2


# 9 ------------------------------------------------------------------------
def test_payoff_matrix_consistent():
    """Fitness / average fitness match a manual computation."""
    x = np.array([0.3, 0.7])
    f = fitness(PRISONERS_DILEMMA, x)
    assert np.allclose(f, [0.9, 2.2])          # f0=3*.3, f1=5*.3+1*.7
    phi = average_fitness(PRISONERS_DILEMMA, x)
    assert np.isclose(phi, 0.3 * 0.9 + 0.7 * 2.2)
    dx = replicator_dynamics(x, PRISONERS_DILEMMA)
    assert np.allclose(dx, x * (f - phi), atol=1e-12)


# 10 -----------------------------------------------------------------------
def test_mutation_prevents_fixation():
    """Mutation rate > 0 prevents single-strategy dominance in the PD."""
    # Without mutation cooperation is driven to extinction.
    pop0 = Population(PRISONERS_DILEMMA, [500, 500], total=1000, mutation_rate=0.0)
    pop0.run(300)
    assert pop0.frequencies[0] < 1e-6

    # With mutation both strategies survive.
    popm = Population(PRISONERS_DILEMMA, [500, 500], total=1000, mutation_rate=0.01)
    popm.run(300)
    assert popm.frequencies[0] > 1e-4
    assert popm.frequencies[1] > 1e-4


# 11 -----------------------------------------------------------------------
def test_phase_portrait_creates_figure():
    """The phase portrait renders and its Hawk-Dove equilibria are correct."""
    import matplotlib.pyplot as plt

    from src.plotting import find_equilibria_1d, phase_portrait

    fig = phase_portrait(HAWK_DOVE, trajectories=[0.2, 0.6], save_path=None)
    assert fig is not None
    eqs = find_equilibria_1d(HAWK_DOVE)
    stable = [e for e in eqs if e["stable"]]
    assert len(stable) == 1
    assert abs(stable[0]["x"] - 0.5) < 1e-9
    plt.close(fig)


# 12 -----------------------------------------------------------------------
def test_phase_portrait_stag_hunt_two_stable():
    """Stag Hunt has two stable (pure) and one unstable (mixed) equilibrium."""
    from src.plotting import find_equilibria_1d

    eqs = find_equilibria_1d(STAG_HUNT)
    stable = [e for e in eqs if e["stable"]]
    unstable = [e for e in eqs if e["unstable"]]
    assert len(stable) == 2
    assert len(unstable) == 1


# 13 -----------------------------------------------------------------------
def test_replicator_dynamics_zero_at_pure_states():
    """dx/dt = 0 at every pure-strategy state."""
    for A in ALL_GAMES:
        for x0 in ([1.0, 0.0], [0.0, 1.0]):
            dx = replicator_dynamics(x0, A)
            assert np.allclose(dx, 0.0, atol=1e-12)


# 14 -----------------------------------------------------------------------
def test_pure_ess_stag_hunt_and_pd():
    """find_pure_ess returns the expected pure ESS indices."""
    assert find_pure_ess(STAG_HUNT) == [0, 1]
    assert find_pure_ess(PRISONERS_DILEMMA) == [1]
