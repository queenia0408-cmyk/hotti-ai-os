# P2-001: Mini PPO Portfolio Optimizer

A minimal but correct implementation of **Proximal Policy Optimization (PPO)**
for portfolio allocation, using **NumPy only** (no PyTorch / TensorFlow).

The agent learns an asset-allocation policy that maximises a Sharpe-like
objective. All market data is **synthetic** — the project is an educational
demonstration of the PPO algorithm, not a trading system.

---

## What PPO does

PPO is an on-policy reinforcement-learning algorithm that improves a policy
`π_θ(a|s)` by taking *conservative* gradient steps. It uses an
Actor-Critic architecture:

| Network  | Input | Output |
|----------|-------|--------|
| **Actor**  | state `s` | portfolio weights `π_θ(·|s)` (softmax over assets) |
| **Critic** | state `s` | scalar state-value estimate `V_θ(s)` |

### Clipped surrogate objective

PPO maximises (we minimise its negative) the clipped objective:

```
L^CLIP(θ) = E[ min( r_t(θ)·A_t,  clip(r_t(θ), 1-ε, 1+ε)·A_t ) ]
```

where the importance-sampling ratio is

```
r_t(θ) = π_θ(a_t|s_t) / π_θ_old(a_t|s_t)
```

Clipping prevents a single bad batch from pushing the policy too far away from
the behaviour policy `π_θ_old`. The default clipping parameter is **ε = 0.2**.

### Generalized Advantage Estimation (GAE)

Advantages are computed with GAE (λ = 0.95, γ = 0.99):

```
δ_t     = r_t + γ·V(s_{t+1}) − V(s_t)        (no bootstrap on terminal steps)
A_t     = δ_t + (γ·λ)·A_{t+1}
```

### Training loop

1. Roll out episodes with the current policy, storing `(s, a, logπ, r, s', done)`.
2. Estimate `V(s)` / `V(s')` with the Critic and compute GAE advantages.
3. Run **multiple PPO epochs** (default 4–10) over the batch with gradient
   descent on the clipped surrogate (Actor) and MSE on the return targets
   (Critic).
4. Discard the batch and repeat.

---

## Policy / weights mapping

The Actor outputs portfolio weights `w = softmax(logits)`. This vector is
applied directly to the environment as the new allocation. To obtain the
scalar `log π_θ(a|s)` needed by the importance ratio, we sample an asset index
`a ~ Categorical(w)` and use `log π_θ(a|s) = log w_a` — a common "softmax
policy" simplification for toy portfolio RL. The gradient of the clipped loss
is chained back through the network analytically.

---

## Portfolio environment

```
state  = [ past `lookback` returns per asset (flattened),
           current portfolio weights,
           current portfolio volatility ]
action = new portfolio weight vector (Actor's softmax output)
reward = portfolio_return − risk_penalty × portfolio_volatility
```

Returns are drawn from a correlated multivariate normal with per-asset
`mu`/`sigma` (randomised per environment, seeded), clipped to `[-0.3, 0.3]` so
portfolio value stays strictly positive.

---

## Project structure

```
ppo-portfolio/
  main.py          # CLI entry point (--train / --evaluate / --benchmark)
  src/
    __init__.py
    ppo.py         # PPO algorithm: clip loss, GAE, update step
    networks.py    # Actor and Critic networks (simple MLPs)
    env.py         # Portfolio environment (returns, volatility, weights)
    replay.py      # Trajectory buffer for (s, a, r, s', done)
  tests/
    __init__.py
    test_ppo.py    # 10 tests
  README.md
```

---

## Usage

Requires Python 3.8+ and NumPy (no other dependencies).

```bash
# Train a PPO agent (default: 300 episodes, AAPL,MSFT,GOOGL)
python main.py --train --episodes 500

# Evaluate a trained agent
python main.py --evaluate

# Train on a custom ticker list (labels only; data is synthetic)
python main.py --tickers AAPL,MSFT,GOOGL --train --episodes 300

# Benchmark PPO vs Equal Weight vs Max Sharpe on synthetic returns
python main.py --benchmark
```

### Hyperparameters (CLI flags)

| Flag | Default | Meaning |
|------|---------|---------|
| `--episodes` | 300 | Training episodes |
| `--episode-length` | 100 | Steps per episode |
| `--lookback` | 10 | Past returns in the state |
| `--risk-penalty` | 0.5 | Risk penalty in the reward |
| `--hidden` | 64 | Hidden-layer size |
| `--epochs` | 4 | PPO epochs per update |
| `--clip-eps` | 0.2 | Clipping parameter ε |
| `--gamma` | 0.99 | Discount factor |
| `--lam` | 0.95 | GAE λ |
| `--actor-lr` / `--critic-lr` | 3e-3 | Learning rates |
| `--update-interval` | 4 | Episodes collected per PPO update |
| `--seed` | 0 | Random seed |

---

## Tests

```bash
cd ppo-portfolio
python -m pytest tests/ -v
```

From the parent directory:

```bash
pytest ppo-portfolio/tests/ -v
```

Covers: clip-loss formula, GAE, actor weight validity, critic output shape,
environment step contract, non-negative portfolio value, training reduces
loss, benchmark runs all three strategies, replay-buffer storage/sampling, and
ratio clipping bounds.

---

## Benchmark

`--benchmark` compares three strategies on the **same** synthetic return series:

- **PPO** — the trained policy (deterministic softmax weights)
- **Equal Weight** — `1/N` in every asset
- **Max Sharpe** — long-only tangency portfolio estimated in-sample

Metrics: total return, mean daily return, annualised volatility, and
annualised Sharpe (assuming 252 periods/year).

---

## Limitations / disclaimer

- Educational toy: returns are synthetic, the action model uses the softmax
  simplification described above, and no fees/slippage/transaction costs are
  modelled.
- Not financial advice. Do not use for real trading decisions.
