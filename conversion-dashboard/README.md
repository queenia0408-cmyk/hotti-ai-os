# AARRR Conversion Funnel Dashboard

> Cycle 3 Build-to-Understand | Claude Code Self-Evolution v3.0

Pirate Metrics (AARRR) dashboard with LTV/CAC analysis and What-if modeling.

## Quick Start

```bash
open index.html
```

## Features

- **AARRR Funnel Visualization**: Acquisition → Activation → Retention → Revenue → Referral
- **8 KPI Dashboard**: MRR, ARR, Net Profit, LTV/CAC, Payback Period, K-factor, Lifetime
- **LTV/CAC Deep Analysis**: Health indicator + benchmarks
- **What-if Modeling**: 6 sensitivity sliders with real-time impact computation
- **Health Status**: 🟢 Healthy / 🟡 Warning / 🔴 Critical auto-diagnosis

## Key Formulas

| Metric | Formula |
|--------|---------|
| LTV | ARPU ÷ Monthly Churn |
| CAC | Total Marketing Spend ÷ New Customers |
| LTV/CAC | Healthy ≥ 3x, Minimum ≥ 2x |
| Payback | CAC ÷ ARPU (months) |
| K-factor | Referral invitations × conversion rate |

## Technical

- Zero dependencies, single HTML file
- All computations client-side
- Dark mode support via `prefers-color-scheme`
