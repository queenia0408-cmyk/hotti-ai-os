#!/usr/bin/env python3
"""
Strategy Framework Analyzer — SWOT, Porter's Five Forces, PESTLE, BCG Matrix, Decision Matrix
Cycle 9 Autonomous Evolution — Strategy Domain Deep-Dive

Multi-framework strategic analysis toolkit for business decision-making.

Usage:
    python strategy.py swot --company "Tesla" --strengths "Brand, Tech" --weaknesses "Production, Cash"
    python strategy.py porter --industry "EV Automotive" --rivalry high --suppliers medium
    python strategy.py pestle --market "EU" --political stable --economic growing
    python strategy.py bcg --stars "AI Division" --cash-cows "Cloud" --question-marks "Robotics" --dogs "Print"
    python strategy.py decision --options "Expand, Pivot, Hold" --criteria "Cost, ROI, Risk"
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ─── Data Models ─────────────────────────────────────────────────────────

@dataclass
class SWOTAnalysis:
    company: str
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    strategies: List[str] = field(default_factory=list)

@dataclass
class PortersFiveForces:
    industry: str
    competitive_rivalry: str      # high / medium / low
    threat_new_entrants: str
    bargaining_power_buyers: str
    bargaining_power_suppliers: str
    threat_substitutes: str
    overall_attractiveness: str = ""
    score: int = 0

@dataclass
class PESTLEAnalysis:
    market: str
    political: str
    economic: str
    social: str
    technological: str
    legal: str
    environmental: str
    opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)

@dataclass
class BCGMatrix:
    stars: List[str]        # High growth, High share → Invest
    cash_cows: List[str]    # Low growth, High share → Milk
    question_marks: List[str]  # High growth, Low share → Analyze
    dogs: List[str]         # Low growth, Low share → Divest
    recommendations: List[str] = field(default_factory=list)

@dataclass
class DecisionMatrix:
    options: List[str]
    criteria: List[str]
    weights: List[float]          # sum to 1.0
    scores: List[List[float]]     # options × criteria
    rankings: List[Tuple[str, float]] = field(default_factory=list)
    winner: str = ""


# ─── SWOT Analysis ──────────────────────────────────────────────────────

def swot_analyze(swot: SWOTAnalysis) -> SWOTAnalysis:
    """Generate cross-quadrant strategies from SWOT."""
    strategies = []

    # SO (Strengths + Opportunities): Attack — use strengths to seize opportunities
    if swot.strengths and swot.opportunities:
        so = f"🚀 SO-Attack: Leverage [{swot.strengths[0]}] to capture [{swot.opportunities[0]}]"
        strategies.append(so)

    # WO (Weaknesses + Opportunities): Improve — overcome weaknesses to pursue opportunities
    if swot.weaknesses and swot.opportunities:
        wo = f"📈 WO-Improve: Address [{swot.weaknesses[0]}] to exploit [{swot.opportunities[0]}]"
        strategies.append(wo)

    # ST (Strengths + Threats): Defend — use strengths to mitigate threats
    if swot.strengths and swot.threats:
        st = f"🛡️ ST-Defend: Use [{swot.strengths[0]}] to counter [{swot.threats[0]}]"
        strategies.append(st)

    # WT (Weaknesses + Threats): Avoid — minimize weaknesses against threats
    if swot.weaknesses and swot.threats:
        wt = f"⚠️ WT-Avoid: Mitigate [{swot.weaknesses[0]}] against [{swot.threats[0]}]"
        strategies.append(wt)

    swot.strategies = strategies
    return swot


# ─── Porter's Five Forces ────────────────────────────────────────────────

def porter_analyze(forces: PortersFiveForces) -> PortersFiveForces:
    """Score Porter's Five Forces and assess industry attractiveness."""
    val_map = {"high": 3, "medium": 2, "low": 1}
    factors = [
        forces.competitive_rivalry,
        forces.threat_new_entrants,
        forces.bargaining_power_buyers,
        forces.bargaining_power_suppliers,
        forces.threat_substitutes,
    ]

    total = sum(val_map.get(f.lower(), 2) for f in factors)

    # High score = unattractive industry (high competitive pressure)
    if total <= 7:
        forces.overall_attractiveness = "🟢 Highly Attractive — Low competitive pressure, good profit potential"
    elif total <= 10:
        forces.overall_attractiveness = "🟡 Moderately Attractive — Some competitive forces, manageable"
    elif total <= 13:
        forces.overall_attractiveness = "🟠 Challenging — Significant competitive pressure"
    else:
        forces.overall_attractiveness = "🔴 Unattractive — Intense competition, low profit potential"

    forces.score = total
    return forces


# ─── PESTLE Analysis ────────────────────────────────────────────────────

def pestle_analyze(pestle: PESTLEAnalysis) -> PESTLEAnalysis:
    """Categorize PESTLE factors into opportunities and threats."""
    # Simple heuristic: stable/positive → opportunity, unstable/negative → threat
    pos_keywords = ["stable", "growing", "strong", "advanced", "favourable", "supportive", "positive"]
    neg_keywords = ["unstable", "declining", "weak", "restrictive", "hostile", "negative", "tightening", "volatile"]

    factors = {
        "Political": pestle.political,
        "Economic": pestle.economic,
        "Social": pestle.social,
        "Technological": pestle.technological,
        "Legal": pestle.legal,
        "Environmental": pestle.environmental,
    }

    for category, status in factors.items():
        status_lower = status.lower()
        if any(kw in status_lower for kw in pos_keywords):
            pestle.opportunities.append(f"{category}: {status}")
        elif any(kw in status_lower for kw in neg_keywords):
            pestle.threats.append(f"{category}: {status}")

    return pestle


# ─── BCG Matrix ─────────────────────────────────────────────────────────

def bcg_analyze(bcg: BCGMatrix) -> BCGMatrix:
    """Generate strategic recommendations from BCG portfolio."""
    recs = []

    if bcg.stars:
        recs.append(f"⭐ STARS: Invest heavily in {', '.join(bcg.stars)} — high growth, high share. Future cash cows.")
    if bcg.cash_cows:
        recs.append(f"💵 CASH COWS: Milk {', '.join(bcg.cash_cows)} — fund stars and question marks from their profits.")
    if bcg.question_marks:
        recs.append(f"❓ QUESTION MARKS: Analyze {', '.join(bcg.question_marks)} — either invest to build share or divest.")
    if bcg.dogs:
        recs.append(f"🐕 DOGS: Consider divesting {', '.join(bcg.dogs)} — low growth, low share. Cash traps.")

    if bcg.stars and not bcg.question_marks:
        recs.append("⚠️ No question marks — pipeline risk. Future stars may be missing.")
    if not bcg.cash_cows:
        recs.append("⚠️ No cash cows — funding source missing. Stars need external capital.")
    if bcg.dogs and len(bcg.dogs) > len(bcg.stars) + len(bcg.cash_cows):
        recs.append("🔴 Portfolio dominated by dogs — major restructuring needed.")

    bcg.recommendations = recs
    return bcg


# ─── Decision Matrix ────────────────────────────────────────────────────

def decision_analyze(dm: DecisionMatrix) -> DecisionMatrix:
    """Weighted decision matrix with rankings."""
    n_options = len(dm.options)
    n_criteria = len(dm.criteria)

    # Apply weights and compute weighted scores
    weighted = []
    for i in range(n_options):
        total = sum(dm.scores[i][j] * dm.weights[j] for j in range(n_criteria))
        weighted.append((dm.options[i], round(total, 2)))

    # Sort by score descending
    weighted.sort(key=lambda x: -x[1])
    dm.rankings = weighted
    dm.winner = weighted[0][0] if weighted else ""

    return dm


# ─── Reports ─────────────────────────────────────────────────────────────

def format_swot(swot: SWOTAnalysis) -> str:
    bar = "═" * 64
    lines = [
        f"\n{bar}",
        f"📊 SWOT ANALYSIS — {swot.company}",
        f"{bar}",
        f"",
        f"💪 STRENGTHS:       {', '.join(swot.strengths) if swot.strengths else 'N/A'}",
        f"🔻 WEAKNESSES:      {', '.join(swot.weaknesses) if swot.weaknesses else 'N/A'}",
        f"🌟 OPPORTUNITIES:   {', '.join(swot.opportunities) if swot.opportunities else 'N/A'}",
        f"⚠️ THREATS:         {', '.join(swot.threats) if swot.threats else 'N/A'}",
    ]
    if swot.strategies:
        lines.append(f"")
        lines.append(f"🎯 CROSS-QUADRANT STRATEGIES:")
        for s in swot.strategies:
            lines.append(f"   {s}")
    lines.extend([f"", f"{bar}", f"✅ SWOT analysis complete.\n"])
    return "\n".join(lines)


def format_porter(forces: PortersFiveForces) -> str:
    bar = "═" * 64
    lines = [
        f"\n{bar}",
        f"🏭 PORTER'S FIVE FORCES — {forces.industry}",
        f"{bar}",
        f"",
        f"   1. Competitive Rivalry:        {forces.competitive_rivalry.upper()}",
        f"   2. Threat of New Entrants:     {forces.threat_new_entrants.upper()}",
        f"   3. Bargaining Power of Buyers: {forces.bargaining_power_buyers.upper()}",
        f"   4. Bargaining Power of Suppliers: {forces.bargaining_power_suppliers.upper()}",
        f"   5. Threat of Substitutes:      {forces.threat_substitutes.upper()}",
        f"",
        f"   Total Pressure Score: {forces.score}/15",
        f"   {forces.overall_attractiveness}",
        f"",
        f"{bar}",
        f"✅ Porter's Five Forces analysis complete.\n",
    ]
    return "\n".join(lines)


def format_pestle(pestle: PESTLEAnalysis) -> str:
    bar = "═" * 64
    lines = [
        f"\n{bar}",
        f"🌍 PESTLE ANALYSIS — {pestle.market}",
        f"{bar}",
        f"",
        f"   Political:       {pestle.political}",
        f"   Economic:        {pestle.economic}",
        f"   Social:          {pestle.social}",
        f"   Technological:   {pestle.technological}",
        f"   Legal:           {pestle.legal}",
        f"   Environmental:   {pestle.environmental}",
    ]
    if pestle.opportunities:
        lines.append(f"")
        lines.append(f"🌟 OPPORTUNITIES:")
        for o in pestle.opportunities:
            lines.append(f"   {o}")
    if pestle.threats:
        lines.append(f"")
        lines.append(f"⚠️ THREATS:")
        for t in pestle.threats:
            lines.append(f"   {t}")
    lines.extend([f"", f"{bar}", f"✅ PESTLE analysis complete.\n"])
    return "\n".join(lines)


def format_bcg(bcg: BCGMatrix) -> str:
    bar = "═" * 64
    lines = [
        f"\n{bar}",
        f"📈 BCG GROWTH-SHARE MATRIX",
        f"{bar}",
        f"",
        f"   ⭐ Stars (High Growth, High Share):",
        f"      {', '.join(bcg.stars) if bcg.stars else 'None'}",
        f"",
        f"   💵 Cash Cows (Low Growth, High Share):",
        f"      {', '.join(bcg.cash_cows) if bcg.cash_cows else 'None'}",
        f"",
        f"   ❓ Question Marks (High Growth, Low Share):",
        f"      {', '.join(bcg.question_marks) if bcg.question_marks else 'None'}",
        f"",
        f"   🐕 Dogs (Low Growth, Low Share):",
        f"      {', '.join(bcg.dogs) if bcg.dogs else 'None'}",
        f"",
    ]
    if bcg.recommendations:
        lines.append(f"💡 STRATEGIC RECOMMENDATIONS:")
        for r in bcg.recommendations:
            lines.append(f"   {r}")
    lines.extend([f"", f"{bar}", f"✅ BCG Matrix analysis complete.\n"])
    return "\n".join(lines)


def format_decision(dm: DecisionMatrix) -> str:
    bar = "═" * 64
    lines = [
        f"\n{bar}",
        f"🎲 WEIGHTED DECISION MATRIX",
        f"{bar}",
        f"",
        f"   Criteria (weights):",
    ]
    for i, (c, w) in enumerate(zip(dm.criteria, dm.weights)):
        lines.append(f"      {c}: {w:.1%}")

    lines.append(f"")
    lines.append(f"   Options × Criteria Matrix:")
    header = "   " + " " * 20 + "".join(f"{c:>10}" for c in dm.criteria) + f"  {'TOTAL':>8}"
    lines.append(header)
    lines.append("   " + "-" * (22 + 10 * len(dm.criteria) + 8))

    for i, opt in enumerate(dm.options):
        score_str = "".join(f"{dm.scores[i][j]:>10.2f}" for j in range(len(dm.criteria)))
        total = sum(dm.scores[i][j] * dm.weights[j] for j in range(len(dm.criteria)))
        lines.append(f"   {opt:>20} {score_str}  {total:>8.3f}")

    lines.append(f"")
    lines.append(f"🏆 RANKINGS:")
    for rank, (opt, score) in enumerate(dm.rankings, 1):
        icon = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"  {rank}."))
        lines.append(f"   {icon} {opt}: {score:.3f}")

    if dm.winner:
        lines.append(f"")
        lines.append(f"   ✅ RECOMMENDED: {dm.winner}")

    lines.extend([f"", f"{bar}", f"✅ Decision Matrix analysis complete.\n"])
    return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────

def parse_list(s: str) -> List[str]:
    """Parse comma-separated list."""
    return [item.strip() for item in s.split(",") if item.strip()]


def parse_floats(s: str) -> List[float]:
    """Parse comma-separated floats."""
    return [float(x.strip()) for x in s.split(",") if x.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="Strategy Framework Analyzer — SWOT, Porter, PESTLE, BCG, Decision Matrix",
        epilog="Cycle 9 Autonomous Evolution | Claude Code Self-Evolution"
    )
    subparsers = parser.add_subparsers(dest="command", help="Framework to use")

    # SWOT
    swot_parser = subparsers.add_parser("swot", help="SWOT Analysis")
    swot_parser.add_argument("--company", default="My Company")
    swot_parser.add_argument("--strengths", type=parse_list, default=[])
    swot_parser.add_argument("--weaknesses", type=parse_list, default=[])
    swot_parser.add_argument("--opportunities", type=parse_list, default=[])
    swot_parser.add_argument("--threats", type=parse_list, default=[])
    swot_parser.add_argument("--json", default=None)

    # Porter's Five Forces
    porter_parser = subparsers.add_parser("porter", help="Porter's Five Forces")
    porter_parser.add_argument("--industry", default="My Industry")
    porter_parser.add_argument("--rivalry", default="medium", choices=["high", "medium", "low"])
    porter_parser.add_argument("--entrants", default="medium", choices=["high", "medium", "low"])
    porter_parser.add_argument("--buyers", default="medium", choices=["high", "medium", "low"])
    porter_parser.add_argument("--suppliers", default="medium", choices=["high", "medium", "low"])
    porter_parser.add_argument("--substitutes", default="medium", choices=["high", "medium", "low"])
    porter_parser.add_argument("--json", default=None)

    # PESTLE
    pestle_parser = subparsers.add_parser("pestle", help="PESTLE Analysis")
    pestle_parser.add_argument("--market", default="Global")
    pestle_parser.add_argument("--political", default="stable")
    pestle_parser.add_argument("--economic", default="moderate")
    pestle_parser.add_argument("--social", default="neutral")
    pestle_parser.add_argument("--technological", default="evolving")
    pestle_parser.add_argument("--legal", default="standard")
    pestle_parser.add_argument("--environmental", default="neutral")
    pestle_parser.add_argument("--json", default=None)

    # BCG Matrix
    bcg_parser = subparsers.add_parser("bcg", help="BCG Growth-Share Matrix")
    bcg_parser.add_argument("--stars", type=parse_list, default=[])
    bcg_parser.add_argument("--cash-cows", dest="cash_cows", type=parse_list, default=[])
    bcg_parser.add_argument("--question-marks", dest="question_marks", type=parse_list, default=[])
    bcg_parser.add_argument("--dogs", type=parse_list, default=[])
    bcg_parser.add_argument("--json", default=None)

    # Decision Matrix
    dm_parser = subparsers.add_parser("decision", help="Weighted Decision Matrix")
    dm_parser.add_argument("--options", type=parse_list, required=True)
    dm_parser.add_argument("--criteria", type=parse_list, required=True)
    dm_parser.add_argument("--weights", type=parse_floats, default=None,
                           help="Comma-separated weights (auto-equal if omitted)")
    dm_parser.add_argument("--scores", type=parse_floats, default=None,
                           help="Comma-separated scores row-major (options×criteria)")
    dm_parser.add_argument("--json", default=None)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ── SWOT ──────────────────────────────────────────────────
    if args.command == "swot":
        swot = SWOTAnalysis(
            company=args.company,
            strengths=args.strengths,
            weaknesses=args.weaknesses,
            opportunities=args.opportunities,
            threats=args.threats,
        )
        swot = swot_analyze(swot)
        print(format_swot(swot))

        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump({
                    "framework": "SWOT",
                    "company": swot.company,
                    "strengths": swot.strengths,
                    "weaknesses": swot.weaknesses,
                    "opportunities": swot.opportunities,
                    "threats": swot.threats,
                    "strategies": swot.strategies,
                }, f, indent=2, ensure_ascii=False)

    # ── Porter ────────────────────────────────────────────────
    elif args.command == "porter":
        forces = PortersFiveForces(
            industry=args.industry,
            competitive_rivalry=args.rivalry,
            threat_new_entrants=args.entrants,
            bargaining_power_buyers=args.buyers,
            bargaining_power_suppliers=args.suppliers,
            threat_substitutes=args.substitutes,
        )
        forces = porter_analyze(forces)
        print(format_porter(forces))

        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump({
                    "framework": "PortersFiveForces",
                    "industry": forces.industry,
                    "forces": {
                        "competitive_rivalry": forces.competitive_rivalry,
                        "threat_new_entrants": forces.threat_new_entrants,
                        "bargaining_power_buyers": forces.bargaining_power_buyers,
                        "bargaining_power_suppliers": forces.bargaining_power_suppliers,
                        "threat_substitutes": forces.threat_substitutes,
                    },
                    "score": forces.score,
                    "attractiveness": forces.overall_attractiveness,
                }, f, indent=2, ensure_ascii=False)

    # ── PESTLE ────────────────────────────────────────────────
    elif args.command == "pestle":
        pestle = PESTLEAnalysis(
            market=args.market,
            political=args.political,
            economic=args.economic,
            social=args.social,
            technological=args.technological,
            legal=args.legal,
            environmental=args.environmental,
        )
        pestle = pestle_analyze(pestle)
        print(format_pestle(pestle))

        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump({
                    "framework": "PESTLE",
                    "market": pestle.market,
                    "factors": {
                        "political": pestle.political,
                        "economic": pestle.economic,
                        "social": pestle.social,
                        "technological": pestle.technological,
                        "legal": pestle.legal,
                        "environmental": pestle.environmental,
                    },
                    "opportunities": pestle.opportunities,
                    "threats": pestle.threats,
                }, f, indent=2, ensure_ascii=False)

    # ── BCG ───────────────────────────────────────────────────
    elif args.command == "bcg":
        bcg = BCGMatrix(
            stars=args.stars,
            cash_cows=args.cash_cows,
            question_marks=args.question_marks,
            dogs=args.dogs,
        )
        bcg = bcg_analyze(bcg)
        print(format_bcg(bcg))

        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump({
                    "framework": "BCG",
                    "stars": bcg.stars,
                    "cash_cows": bcg.cash_cows,
                    "question_marks": bcg.question_marks,
                    "dogs": bcg.dogs,
                    "recommendations": bcg.recommendations,
                }, f, indent=2, ensure_ascii=False)

    # ── Decision Matrix ───────────────────────────────────────
    elif args.command == "decision":
        n_opts = len(args.options)
        n_crit = len(args.criteria)

        # Auto-equal weights if not provided
        if args.weights is None:
            weights = [1.0 / n_crit] * n_crit
        else:
            if len(args.weights) != n_crit:
                print(f"❌ Expected {n_crit} weights, got {len(args.weights)}", file=sys.stderr)
                sys.exit(1)
            total = sum(args.weights)
            weights = [w / total for w in args.weights]

        # Generate or parse scores
        if args.scores is None:
            # Interactive-ish: random for demo
            import random
            random.seed(42)
            scores = []
            for _ in range(n_opts):
                scores.append([round(random.uniform(1, 10), 1) for _ in range(n_crit)])
        else:
            expected = n_opts * n_crit
            if len(args.scores) != expected:
                print(f"❌ Expected {expected} scores ({n_opts}×{n_crit}), got {len(args.scores)}", file=sys.stderr)
                sys.exit(1)
            scores = []
            for i in range(n_opts):
                scores.append(args.scores[i * n_crit:(i + 1) * n_crit])

        dm = DecisionMatrix(
            options=args.options,
            criteria=args.criteria,
            weights=weights,
            scores=scores,
        )
        dm = decision_analyze(dm)
        print(format_decision(dm))

        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump({
                    "framework": "DecisionMatrix",
                    "options": dm.options,
                    "criteria": dm.criteria,
                    "weights": dm.weights,
                    "scores": dm.scores,
                    "rankings": [{"option": o, "score": s} for o, s in dm.rankings],
                    "winner": dm.winner,
                }, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
