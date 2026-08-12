#!/usr/bin/env python3
"""K-factor Viral Coefficient Simulator — Main entry point.

Usage:
    python main.py --k 0.8 --cycles 10
    python main.py --compare
    python main.py --k 1.2 --cycles 15 --type incentivized
    python main.py --type all
"""

import argparse
import sys
from pathlib import Path

# Add project root to path so `src` is importable.
sys.path.insert(0, str(Path(__file__).parent))

from src.engine import Comparison, CycleResult, ViralEngine
from src.loops import LOOPS, LoopType


TYPE_ALIASES: dict[str, LoopType] = {
    "organic": LoopType.ORGANIC,
    "incentivized": LoopType.INCENTIVIZED,
    "content": LoopType.CONTENT,
    "embedded": LoopType.EMBEDDED,
}

# K-values used for the comparative table (K vs users after N cycles).
COMPARISON_K_VALUES = [0.3, 0.5, 0.7, 0.9, 1.0, 1.1, 1.3, 1.5, 2.0]


def banner(title: str, width: int = 70) -> str:
    """Render a centered banner header."""
    return f"{'=' * width}\n  {title}\n{'=' * width}"


def render_cycle_table(results: list[CycleResult]) -> str:
    """Render the per-cycle growth table."""
    header = (
        f"{'Cycle':>6} {'Days':>7} {'Effective K':>12} "
        f"{'New Users':>12} {'Total Users':>12}"
    )
    lines = [header, "-" * len(header)]
    for r in results:
        lines.append(
            f"{r.cycle:>6} {r.days:>7.1f} {r.k:>12.3f} "
            f"{r.new_users:>12.1f} {r.total_users:>12.1f}"
        )
    return "\n".join(lines)


def render_comparative_table(cycles: int, initial_users: int) -> str:
    """Render the K-value vs users table for `cycles` cycles."""
    rows = ViralEngine.comparative_table(COMPARISON_K_VALUES, cycles, initial_users)
    col = f"Users after {cycles} cycles"
    header = f"{'K-factor':>8}  {col:>22}"
    lines = [header, "-" * len(header)]
    for k, users in rows:
        marker = "   ← K > 1 → super-viral" if k > 1.0 else ""
        lines.append(f"{k:>8.2f}  {users:>22,.1f}{marker}")
    return "\n".join(lines)


def render_single(engine: ViralEngine) -> str:
    """Render a full report for a single loop simulation."""
    results = engine.simulate()
    loop = engine.loop
    final_users = results[-1].total_users

    lines = [banner("K-factor Viral Coefficient Simulator")]
    lines.append(f"  Loop type : {loop.name}")
    lines.append(f"  Description: {loop.description}")
    lines.append(f"  K₀        : {engine.k:.3f}")
    lines.append(f"  Decay δ   : {engine.decay_rate:.3f}")
    lines.append(f"  Cycle time: {engine.cycle_time_days:.1f} days")
    lines.append(f"  Initial   : {engine.initial_users} users")
    lines.append(f"  Cycles    : {engine.cycles}")
    lines.append("")
    lines.append(render_cycle_table(results))
    lines.append("")
    lines.append(f"  Final users after {engine.cycles} cycles: {final_users:,.1f}")
    lines.append(f"  New users from viral growth: {final_users - engine.initial_users:,.1f}")
    lines.append("")
    lines.append(banner(f"Comparative table — users after {engine.cycles} cycles"))
    lines.append(render_comparative_table(engine.cycles, engine.initial_users))
    return "\n".join(lines)


def render_all(cycles: int, decay_rate: float, k_override: float | None, initial_users: int) -> str:
    """Render a side-by-side comparison of all four loop types."""
    lines = [banner("K-factor Viral Coefficient Simulator — All Loop Types")]
    header = f"{'Loop':<14} {'K₀':>6} {'Cycle (d)':>9} {'Final Users':>14} {'New Users':>14}"
    lines.append(header)
    lines.append("-" * len(header))

    for loop_type in LoopType:
        loop = LOOPS[loop_type]
        k = k_override if k_override is not None else loop.default_k
        engine = ViralEngine(
            k=k,
            cycles=cycles,
            decay_rate=decay_rate,
            cycle_time_days=loop.cycle_time_days,
            initial_users=initial_users,
            loop_type=loop_type,
        )
        results = engine.simulate()
        final = results[-1].total_users
        new = final - initial_users
        lines.append(
            f"{loop.name:<14} {k:>6.2f} {loop.cycle_time_days:>9.1f} "
            f"{final:>14,.1f} {new:>14,.1f}"
        )

    lines.append("")
    lines.append("  K₀ = loop default (use --k to override for all loops).")
    lines.append("  Decay and cycle count are shared across loops.")
    return "\n".join(lines)


def render_compare(cmp: Comparison) -> str:
    """Render the fast-vs-slow cycle-time comparison."""
    lines = [banner(f"Cycle Time Comparison — {cmp.total_days} days")]
    lines.append(
        f"  Fast : {cmp.fast_label:<30} → {cmp.fast_cycles:>3} cycles → {cmp.fast_users:>12,.1f} users"
    )
    lines.append(
        f"  Slow : {cmp.slow_label:<30} → {cmp.slow_cycles:>3} cycles → {cmp.slow_users:>12,.1f} users"
    )
    lines.append("")
    if cmp.winner == "fast":
        lines.append(
            f"  ✅ Fast & small wins: {cmp.fast_label} reaches {cmp.multiple:.2f}× more users "
            "over the same horizon."
        )
        lines.append("     Cycle velocity beats raw K-factor.")
    else:
        lines.append(
            f"  ⚠️  Slow & big wins: {cmp.slow_label} reaches {cmp.multiple:.2f}× more users "
            "over the same horizon."
        )
    lines.append("")
    lines.append("  users after T days = simulate K over ⌊T / cycle_time⌋ cycles")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "K-factor Viral Coefficient Simulator — models user growth with the "
            "K-factor and saturation decay."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python main.py --k 0.8 --cycles 10            # single loop, growth table
  python main.py --compare                      # K=0.8@3d vs K=1.2@30d
  python main.py --k 1.2 --cycles 15 --type incentivized
  python main.py --type all                     # all four loop types
        """,
    )
    parser.add_argument(
        "--k", type=float, default=None,
        help="Initial K-factor K₀ (default: the loop type's default)",
    )
    parser.add_argument(
        "--cycles", type=int, default=10,
        help="Number of viral cycles (default: 10)",
    )
    parser.add_argument(
        "--decay", type=float, default=0.05,
        help="Saturation decay rate δ for K(t)=K₀·e^(−δt) (default: 0.05)",
    )
    parser.add_argument(
        "--type", choices=list(TYPE_ALIASES) + ["all"], default="organic",
        help="Viral loop type, or 'all' to show every loop (default: organic)",
    )
    parser.add_argument(
        "--cycle-time", type=float, default=None,
        help="Override the loop cycle time in days (default: loop default)",
    )
    parser.add_argument(
        "--initial-users", type=int, default=100,
        help="Seed user count (default: 100)",
    )
    parser.add_argument(
        "--compare", action="store_true",
        help="Compare K=0.8@3d vs K=1.2@30d over a fixed horizon",
    )
    parser.add_argument(
        "--days", type=int, default=30,
        help="Total-day horizon for --compare (default: 30)",
    )
    return parser


def main():
    args = build_parser().parse_args()

    if args.compare:
        cmp = ViralEngine.compare(
            total_days=args.days,
            initial_users=args.initial_users,
            decay_rate=args.decay,
        )
        print(render_compare(cmp))
        return

    if args.type == "all":
        print(render_all(
            cycles=args.cycles,
            decay_rate=args.decay,
            k_override=args.k,
            initial_users=args.initial_users,
        ))
        return

    loop_type = TYPE_ALIASES[args.type]
    loop = LOOPS[loop_type]
    k = args.k if args.k is not None else loop.default_k
    cycle_time = args.cycle_time if args.cycle_time is not None else loop.cycle_time_days

    engine = ViralEngine(
        k=k,
        cycles=args.cycles,
        decay_rate=args.decay,
        cycle_time_days=cycle_time,
        initial_users=args.initial_users,
        loop_type=loop_type,
    )
    print(render_single(engine))


if __name__ == "__main__":
    main()
