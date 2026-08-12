# 🦠 K-factor Viral Coefficient Simulator

> **Simulate viral user growth with the K-factor model and saturation decay.** Built to understand growth mechanics through implementation — the Karpathy "Build to Understand" way.

## Why This Exists

Growth teams obsess over the **K-factor** (viral coefficient) — the average number of new users each existing user brings in. The conventional wisdom is "K > 1 means viral." But that framing misses the two numbers that actually decide whether a product grows fast: **cycle time** and **decay**.

This simulator makes the counter-intuitive result tangible: **a product with K = 0.8 on a 3-day cycle beats a product with K = 1.2 on a 30-day cycle over a 30-day horizon.** Cycle velocity beats raw K-factor.

## The Model

### K-factor

$$K = i \times c$$

where `i` = invites sent per user and `c` = conversion rate of those invites.

### Decay

Real K-factors do not stay constant. As a product saturates its addressable market, each new invite converts a smaller share of new users:

$$K(t) = K_0 \cdot e^{-\delta \cdot t}$$

where `K₀` is the initial K-factor, `δ` is the saturation decay rate, and `t` is elapsed time.

### Growth (wave model)

Each cycle produces a new wave of users equal to the previous wave scaled by the current effective K. With a constant K this reproduces the closed form:

$$\text{users}_n = \text{users}_0 \cdot (1 + K + K^2 + \dots + K^n) \quad (K \neq 1)$$

$$\text{users}_n = \text{users}_0 \cdot (n + 1) \quad (K = 1)$$

### Cycle time comparison

$$\text{users after } T \text{ days} = \text{simulate } K \text{ over } \left\lfloor \frac{T}{\text{cycle\_time}} \right\rfloor \text{ cycles}$$

Over 30 days, K = 0.8 at 3-day cycles completes ⌊30/3⌋ = **10 cycles**, while K = 1.2 at 30-day cycles completes ⌊30/30⌋ = **1 cycle**. Ten compounding waves beat one big wave.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Viral Coefficient Simulator              │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  loops.py    │  │  decay.py    │  │  engine.py     │  │
│  │              │  │              │  │                │  │
│  │ • Organic    │  │ • Constant   │  │ • simulate()   │  │
│  │ • Incentiv.  │  │ • Exponential│  │ • users_after_ │  │
│  │ • Content    │  │   K₀·e^(−δt) │  │   n_cycles()  │  │
│  │ • Embedded   │  │              │  │ • comparative_ │  │
│  │              │  │              │  │   table()      │  │
│  └─────────────┘  └──────────────┘  │ • compare()     │  │
│                    [K-factor decay] └────────┬─────────┘  │
│                          ▲                   │            │
│              ┌───────────┴───────────────────▼─────────┐  │
│              │              main.py (CLI)              │  │
│              │  --k --cycles --decay --type --compare  │  │
│              └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Usage

```bash
# Single loop: growth table + comparative table
python main.py --k 0.8 --cycles 10

# The headline comparison: K=0.8@3d vs K=1.2@30d over 30 days
python main.py --compare

# Run a specific loop type with an explicit K-factor
python main.py --k 1.2 --cycles 15 --type incentivized

# Show all four loop types side by side
python main.py --type all
```

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--k` | loop default | Initial K-factor K₀ |
| `--cycles` | `10` | Number of viral cycles |
| `--decay` | `0.05` | Saturation decay rate δ in K(t) = K₀·e^(−δt) |
| `--type` | `organic` | Loop type: `organic` / `incentivized` / `content` / `embedded` / `all` |
| `--cycle-time` | loop default | Override the loop cycle time in days |
| `--initial-users` | `100` | Seed user count users₀ |
| `--compare` | — | Show K=0.8@3d vs K=1.2@30d over a horizon |
| `--days` | `30` | Total-day horizon for `--compare` |

## Viral Loop Types

| Loop type | Mechanism | Default K₀ | Cycle time | Trade-off |
|-----------|-----------|------------|------------|-----------|
| **Organic** | Built into the product; sharing happens naturally | 0.30 | 3 days | Low K, fast cycle |
| **Incentivized** | Double-sided rewards for inviter and invitee | 0.60 | 7 days | Medium K, medium cycle |
| **Content** | Users create shareable output that carries the brand | 1.20 | 30 days | High K, slow cycle |
| **Embedded** | Product inherently requires others to join | 1.50 | 1 day | Highest K, fastest cycle |

The trade-off is the point: **content loops have the highest K but take a month per cycle**, while **embedded loops compound daily**.

## Project Structure

```
viral-simulator/
├── main.py              # CLI entry point with argparse
├── src/
│   ├── __init__.py
│   ├── engine.py        # ViralEngine: simulation logic, closed forms, compare
│   ├── loops.py         # Loop type definitions (organic, incentivized, content, embedded)
│   └── decay.py         # Decay models (constant, exponential)
├── tests/
│   ├── __init__.py
│   └── test_simulator.py
└── README.md
```

## Testing

```bash
python -m pytest tests/ -v
```

The suite covers the decay formula, loop-type definitions and ordering, the closed-form geometric growth series, the K = 1 linear-growth special case, the cycle-time comparison, and the comparative table.

## Technical Details

- **Language**: Python 3.11+
- **Dependencies**: stdlib only (`dataclasses`, `argparse`, `math`) — no numpy/pandas
- **Testing**: pytest

## License

MIT — Built by Claude Code Operational Self for Karpathy Build-to-Understand dimension.
