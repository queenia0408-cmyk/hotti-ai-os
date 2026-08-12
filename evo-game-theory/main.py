"""P2-002: Evolutionary Game Theory Simulator — CLI entry point."""

from __future__ import annotations

import argparse
import sys

import numpy as np

from src.games import (
    GAMES,
    GAME_NAMES,
    GAME_STRATEGIES,
    average_fitness,
    fitness,
    mixed_nash,
    pure_nash,
)
from src.ess import find_pure_ess
from src.population import Population
from src.replicator import solve_replicator


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="evo-game-theory",
        description=(
            "Simulate evolutionary game dynamics: replicator dynamics, "
            "ESS detection, population games and phase portraits."
        ),
    )
    parser.add_argument(
        "--game",
        required=True,
        choices=list(GAMES.keys()),
        help="which game to simulate",
    )
    parser.add_argument(
        "--population",
        type=int,
        default=1000,
        help="total population size for the population simulation",
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=100,
        help="number of generations for the population simulation",
    )
    parser.add_argument(
        "--mutation-rate",
        type=float,
        default=0.0,
        help="per-generation mutation probability (0 disables mutation)",
    )
    parser.add_argument(
        "--x0",
        type=float,
        default=0.5,
        help="initial frequency of strategy 0",
    )
    parser.add_argument(
        "--t-end",
        type=float,
        default=20.0,
        help="integration horizon for replicator dynamics",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=0.01,
        help="RK4 step size",
    )
    parser.add_argument(
        "--show-portrait",
        action="store_true",
        help="display the phase portrait in a matplotlib window",
    )
    parser.add_argument(
        "--save-portrait",
        type=str,
        default=None,
        metavar="PATH",
        help="save the phase portrait to a file (e.g. portrait.png)",
    )
    parser.add_argument(
        "--portrait-x0",
        type=str,
        default="0.1,0.3,0.5,0.7,0.9",
        help="comma-separated starting points for the trajectory panel",
    )
    parser.add_argument(
        "--no-simulate",
        action="store_true",
        help="only report game facts (no replicator/population simulation)",
    )
    return parser.parse_args(argv)


def report_game(name: str) -> np.ndarray:
    """Print game facts and return the payoff matrix."""
    A = GAMES[name]
    strategies = GAME_STRATEGIES[name]
    print(f"\n=== {GAME_NAMES[name]} ===")
    print("Payoff matrix A (rows = own strategy, columns = opponent's):")
    print(A)
    print(f"Strategies: {strategies}")

    ne = pure_nash(A)
    if ne:
        print("Pure symmetric Nash equilibria: "
              + ", ".join(strategies[i] for i in ne))
    else:
        print("Pure symmetric Nash equilibria: none")

    m = mixed_nash(A)
    if m is not None:
        print(f"Interior mixed Nash equilibrium: x = {np.round(m, 6).tolist()}")

    pure_ess = find_pure_ess(A)
    if pure_ess:
        print("Pure ESS: " + ", ".join(strategies[i] for i in pure_ess))
    else:
        print("Pure ESS: none")
    return A


def main(argv=None) -> int:
    args = parse_args(argv)
    A = report_game(args.game)

    if args.show_portrait or args.save_portrait:
        try:
            from src.plotting import phase_portrait

            x0s = [float(v) for v in args.portrait_x0.split(",") if v != ""]
            fig = phase_portrait(
                A,
                strategy_names=GAME_STRATEGIES[args.game],
                trajectories=x0s,
                save_path=args.save_portrait,
            )
            if args.show_portrait:
                import matplotlib.pyplot as plt

                plt.show()
            elif args.save_portrait:
                print(f"Portrait saved to {args.save_portrait}")
        except ImportError as exc:  # matplotlib missing
            print(f"matplotlib is required for portraits: {exc}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"Could not create portrait: {exc}", file=sys.stderr)

    if args.no_simulate:
        return 0

    strategies = GAME_STRATEGIES[args.game]

    # --- Replicator dynamics -------------------------------------------
    x0 = np.array([args.x0, 1.0 - args.x0])
    ts, ys = solve_replicator(x0, A, t_end=args.t_end, dt=args.dt)
    final = ys[-1]
    print("\n--- Replicator dynamics ---")
    print(f"x(0)     = {np.round(x0, 4).tolist()}")
    print(f"x({args.t_end:g}) = {np.round(final, 6).tolist()}  (sum={final.sum():.6f})")
    print(f"fitness  = {np.round(fitness(A, final), 6).tolist()}")
    print(f"avg fit  = {average_fitness(A, final):.6f}")
    dominant = int(np.argmax(final))
    print(f"Dominant strategy: {strategies[dominant]} "
          f"(x = {final[dominant]:.4f})")

    # --- Population simulation ------------------------------------------
    if args.population and args.population > 0:
        initial_counts = np.array(
            [args.population * args.x0, args.population * (1.0 - args.x0)]
        )
        pop = Population(
            A,
            initial_counts=initial_counts,
            total=args.population,
            mutation_rate=args.mutation_rate,
        )
        pop.run(args.generations)
        print("\n--- Population simulation "
              f"(N={args.population}, generations={args.generations}, "
              f"mutation_rate={args.mutation_rate}) ---")
        print(f"Final frequencies: {np.round(pop.frequencies, 6).tolist()}")
        surviving = [strategies[i] for i in pop.surviving_strategies]
        print("Surviving strategies (>1e-6): "
              + (", ".join(surviving) if surviving else "none"))

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
