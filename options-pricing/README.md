# Options Pricing Engine

Black-Scholes + Binomial Tree + Greeks + Implied Volatility calculator.

## Quick Start

```bash
pip install numpy scipy
python pricing.py --spot 100 --strike 105 --days 30 --vol 0.25 --rate 0.05
python pricing.py --spot 100 --strike 100 --days 90 --vol 0.20 --greeks
python pricing.py --spot 150 --strike 140 --days 7 --vol 0.35 --implied --price 12.50
python pricing.py --spot 100 --strike 100 --days 30 --vol 0.25 --american --steps 500
```

## Features

- **Black-Scholes-Merton** — analytical European option pricing
- **CRR Binomial Tree** — American option pricing with configurable steps
- **Greeks** — Delta, Gamma, Theta, Vega, Rho (analytical + finite difference)
- **Implied Volatility** — Newton-Raphson solver
- **Put-Call Parity** — automatic verification

## Mathematical Foundation

- Black-Scholes-Merton (1973): C = S·N(d1) - K·e^(-rT)·N(d2)
- Cox-Ross-Rubinstein (1979): binomial lattice
- Newton-Raphson: σ_{n+1} = σ_n - f(σ_n)/f'(σ_n)

## Architecture

```
black_scholes() → option price (European)
binomial_tree() → option price (American, CRR)
compute_greeks() → Delta, Gamma, Theta, Vega, Rho
implied_volatility() → Newton-Raphson solver
check_put_call_parity() → C - P = S - Ke^(-rT)
```

## Tech

Python, numpy, scipy, Black-Scholes, Binomial Tree, Newton-Raphson
