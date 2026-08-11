# Strategy Framework Analyzer

Multi-framework strategic analysis toolkit: SWOT, Porter's Five Forces, PESTLE, BCG Matrix, Weighted Decision Matrix.

## Quick Start

```bash
# SWOT Analysis with cross-quadrant strategies
python strategy.py swot --company "Tesla" --strengths "Brand, Tech" --weaknesses "Cash, QA" --opportunities "EV Growth, FSD" --threats "Competition, Supply Chain"

# Porter's Five Forces
python strategy.py porter --industry "SaaS" --rivalry high --entrants medium --buyers high --suppliers low --substitutes medium

# PESTLE Analysis
python strategy.py pestle --market "EU" --political stable --economic growing

# BCG Growth-Share Matrix
python strategy.py bcg --stars "AI" --cash-cows "Cloud" --question-marks "Robotics" --dogs "Print"

# Weighted Decision Matrix
python strategy.py decision --options "Expand,Pivot,Hold" --criteria "Cost,ROI,Risk" --weights 0.3,0.4,0.3 --scores 5,8,6,7,6,4,9,4,3
```

## Features

- **SWOT** — Cross-quadrant strategy generation (SO/ST/WO/WT)
- **Porter's Five Forces** — Industry attractiveness scoring (3-15 scale)
- **PESTLE** — 6-factor macro-environment analysis with opp/threat categorization
- **BCG Matrix** — Portfolio analysis with strategic recommendations
- **Decision Matrix** — Weighted multi-criteria decision analysis with rankings
- **JSON output** — All frameworks support `--json report.json`

## Tech

Python, argparse, dataclasses, weighted decision analysis
