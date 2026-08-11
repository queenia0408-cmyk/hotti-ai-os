# Monte Carlo Decision Simulator

> Cycle 3 Build-to-Understand | Claude Code Self-Evolution v3.0

Interactive decision science toolkit in a single HTML file.

## Quick Start

```bash
open index.html
```

## Modules

| Module | Science | Interaction |
|--------|---------|-------------|
| **EV Calculator** | Expected Value Theory | Add/remove scenarios, real-time computation |
| **Bayesian Updater** | Bayes' Theorem | Prior → Evidence → Posterior |
| **Monte Carlo** | Geometric Brownian Motion | 1K-100K simulations, VaR, distribution |
| **Pre-Mortem** | Cognitive Debiasing | Random failure mode generation |

## Technical Highlights

- **Box-Muller Transform**: Uniform → Normal distribution conversion
- **GBM Model**: `S_T = S_0 × exp(μT + σ√T × Z)`
- **VaR (95%)**: Value at Risk computation
- **Zero Dependencies**: Single HTML file, no build step
