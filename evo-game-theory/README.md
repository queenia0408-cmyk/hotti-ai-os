# P2-002: Evolutionary Game Theory Simulator

A pure-Python simulation of evolutionary game dynamics: **replicator dynamics**,
**evolutionarily stable strategy (ESS) detection**, **population games** with
fitness-based reproduction and mutation, and **phase portraits**.

## Math

For a symmetric 2-player game given by a payoff matrix `A` (`A[i, j]` = payoff
to a player using strategy `i` against a player using strategy `j`), the
population profile `x` is a probability vector over strategies.

- Expected fitness of strategy `i`:
  `f_i(x) = Σ_j A[i, j] * x[j]`
- Population average fitness:
  `φ(x) = Σ_j x_j * f_j(x)`
- **Replicator dynamics**:
  `dx_i/dt = x_i * (f_i(x) − φ(x))`
- **ESS**: a strategy `p` is an ESS if for every alternative strategy `q ≠ p`
  either `u(p,p) > u(q,p)`, or `u(p,p) = u(q,p)` and `u(p,q) > u(q,q)`.

The replicator ODE is integrated with a classical 4th-order Runge-Kutta (RK4)
solver.

## Supported games

| `--game`      | Name                    | Payoff matrix | Key facts |
|---------------|-------------------------|---------------|-----------|
| `prisoner`    | Prisoner's Dilemma      | `[[3,0],[5,1]]` | Defect is the unique ESS |
| `hawk-dove`   | Hawk-Dove               | `[[0,3],[1,2]]` | Mixed strategy `[0.5, 0.5]` is the unique ESS |
| `stag-hunt`   | Stag Hunt               | `[[4,0],[2,2]]` | Both pure strategies are ESS/Nash |
| `coordination`| Coordination            | `[[2,0],[0,2]]` | Multiple pure equilibria (risk dominance basin) |

## Project structure

```
evo-game-theory/
  main.py          # CLI entry point
  src/
    __init__.py
    replicator.py  # Replicator dynamics ODE + RK4 integrator
    games.py       # Game definitions (payoff matrices, Nash finders)
    ess.py         # ESS detection algorithm
    population.py  # Population simulation: N strategies, fitness-based reproduction
    plotting.py    # Phase portraits, trajectory plots (matplotlib)
  tests/
    __init__.py
    test_evo.py    # 14 tests
  pytest.ini
  README.md
```

## Installation

Requires Python 3.9+ with `numpy`, `matplotlib`, and `pytest`.

```bash
cd evo-game-theory
python -m pip install numpy matplotlib pytest
```

## Usage

```bash
python main.py --game prisoner                       # Simulate Prisoner's Dilemma
python main.py --game hawk-dove --population 1000 --generations 50
python main.py --game stag-hunt --show-portrait      # Open the phase portrait window
python main.py --game coordination --mutation-rate 0.01
python main.py --game hawk-dove --save-portrait portrait.png   # Save the portrait
```

### CLI flags

| Flag               | Default | Description |
|--------------------|---------|-------------|
| `--game`           | —       | `prisoner` \| `hawk-dove` \| `stag-hunt` \| `coordination` (required) |
| `--population`     | `1000`  | Total population size for the population simulation |
| `--generations`    | `100`   | Generations for the population simulation |
| `--mutation-rate`  | `0.0`   | Per-generation mutation probability |
| `--x0`             | `0.5`   | Initial frequency of strategy 0 |
| `--t-end` / `--dt` | `20.0` / `0.01` | Replicator integration horizon / RK4 step |
| `--show-portrait`  | off     | Display the phase portrait window |
| `--save-portrait`  | —       | Save the phase portrait to a file |
| `--no-simulate`    | off     | Only report game facts (no integration) |

## Phase portrait

For the 2-strategy games the portrait shows:

- the simplex line `x ∈ [0, 1]` (frequency of strategy 0) with arrows
  indicating the direction of `dx/dt`;
- stable (green), unstable (red) and degenerate (grey) equilibria;
- time trajectories `x(t)` integrated from several starting points.

## Tests

```bash
python -m pytest tests/ -v        # from inside the project
pytest evo-game-theory/tests/ -v  # from the parent directory
```

14 tests cover: sum conservation under RK4, ESS detection for all four games,
mixed/pure Nash finding, RK4 convergence, population convergence to the ESS,
payoff consistency, mutation preventing fixation, and phase-portrait
equilibria.
