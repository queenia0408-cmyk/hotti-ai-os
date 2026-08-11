#!/usr/bin/env python3
"""
Options Pricing Engine — Black-Scholes, Binomial Tree, Greeks, Implied Volatility
Cycle 8 Autonomous Evolution — Trading Domain Deep-Dive

Mathematical foundations:
- Black-Scholes-Merton (1973) — analytical European option pricing
- Cox-Ross-Rubinstein (1979) — binomial tree for American options
- Newton-Raphson — implied volatility solver
- Greeks: Delta, Gamma, Theta, Vega, Rho (analytical + finite difference)

Usage:
    python pricing.py --spot 100 --strike 105 --days 30 --vol 0.25 --rate 0.05
    python pricing.py --spot 100 --strike 100 --days 90 --vol 0.20 --greeks
    python pricing.py --spot 150 --strike 140 --days 7 --vol 0.35 --implied --price 12.50
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from scipy.stats import norm


# ─── Data Models ─────────────────────────────────────────────────────────

@dataclass
class OptionResult:
    option_type: str       # "call" or "put"
    style: str             # "european" or "american"
    spot: float
    strike: float
    time_to_expiry: float  # years
    volatility: float      # annualized σ
    risk_free_rate: float  # continuous r
    price: float
    method: str            # "black-scholes" or "binomial-tree"


@dataclass
class Greeks:
    delta: float
    gamma: float
    theta: float           # per day
    vega: float            # per 1% vol change
    rho: float             # per 1% rate change


# ─── Core Math ───────────────────────────────────────────────────────────

def norm_cdf(x: float) -> float:
    """Standard normal CDF."""
    return float(norm.cdf(x))


def norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return float(norm.pdf(x))


# ─── Black-Scholes (European) ────────────────────────────────────────────

def black_scholes(
    spot: float,
    strike: float,
    time_to_expiry: float,
    volatility: float,
    risk_free_rate: float,
    option_type: str = "call",
) -> float:
    """
    Black-Scholes-Merton analytical pricing for European options.

    C = S·N(d1) - K·e^(-rT)·N(d2)
    P = K·e^(-rT)·N(-d2) - S·N(-d1)

    where:
        d1 = [ln(S/K) + (r + σ²/2)·T] / (σ·√T)
        d2 = d1 - σ·√T
    """
    if time_to_expiry <= 0:
        # At expiry: intrinsic value
        if option_type == "call":
            return max(0.0, spot - strike)
        return max(0.0, strike - spot)

    if volatility <= 0:
        # Zero vol: discounted intrinsic
        pv_strike = strike * math.exp(-risk_free_rate * time_to_expiry)
        if option_type == "call":
            return max(0.0, spot - pv_strike)
        return max(0.0, pv_strike - spot)

    d1 = (math.log(spot / strike) + (risk_free_rate + volatility**2 / 2) * time_to_expiry) \
         / (volatility * math.sqrt(time_to_expiry))
    d2 = d1 - volatility * math.sqrt(time_to_expiry)

    if option_type == "call":
        return spot * norm_cdf(d1) - strike * math.exp(-risk_free_rate * time_to_expiry) * norm_cdf(d2)
    else:
        return strike * math.exp(-risk_free_rate * time_to_expiry) * norm_cdf(-d2) - spot * norm_cdf(-d1)


# ─── Binomial Tree (Cox-Ross-Rubinstein, American) ───────────────────────

def binomial_tree(
    spot: float,
    strike: float,
    time_to_expiry: float,
    volatility: float,
    risk_free_rate: float,
    option_type: str = "call",
    steps: int = 200,
    american: bool = True,
) -> float:
    """
    CRR binomial tree for European or American options.

    u = exp(σ·√Δt), d = 1/u
    p = (exp(r·Δt) - d) / (u - d)  — risk-neutral probability

    American: V = max(intrinsic, discounted expected)
    European: V = discounted expected only
    """
    if time_to_expiry <= 0:
        if option_type == "call":
            return max(0.0, spot - strike)
        return max(0.0, strike - spot)

    dt = time_to_expiry / steps
    u = math.exp(volatility * math.sqrt(dt))
    d = 1.0 / u
    p = (math.exp(risk_free_rate * dt) - d) / (u - d)
    discount = math.exp(-risk_free_rate * dt)

    # Terminal payoffs
    values = []
    for i in range(steps + 1):
        s_t = spot * (u ** (steps - i)) * (d ** i)
        if option_type == "call":
            values.append(max(0.0, s_t - strike))
        else:
            values.append(max(0.0, strike - s_t))

    # Backward induction
    for step in range(steps - 1, -1, -1):
        for i in range(step + 1):
            s_t = spot * (u ** (step - i)) * (d ** i)
            continuation = discount * (p * values[i] + (1 - p) * values[i + 1])

            if american:
                if option_type == "call":
                    exercise = max(0.0, s_t - strike)
                else:
                    exercise = max(0.0, strike - s_t)
                values[i] = max(continuation, exercise)
            else:
                values[i] = continuation

    return values[0]


# ─── Greeks ──────────────────────────────────────────────────────────────

def compute_greeks(
    spot: float,
    strike: float,
    time_to_expiry: float,
    volatility: float,
    risk_free_rate: float,
    option_type: str = "call",
    method: str = "analytical",
) -> Greeks:
    """
    Compute option Greeks.

    Analytical (Black-Scholes):
      Delta = N(d1) for calls, N(d1) - 1 for puts
      Gamma = N'(d1) / (S·σ·√T)
      Theta = -(S·σ·N'(d1))/(2√T) - r·K·e^(-rT)·N(d2)  (call, per year)
      Vega  = S·√T·N'(d1)  (per 100% vol, divide by 100 for 1%)
      Rho   = K·T·e^(-rT)·N(d2)  (call, per 100% rate)
    """
    if time_to_expiry <= 0 or volatility <= 0:
        # At expiry or zero vol: degenerate Greeks
        intrinsic = max(0.0, spot - strike) if option_type == "call" else max(0.0, strike - spot)
        delta = 1.0 if (option_type == "call" and spot > strike) or \
                        (option_type == "put" and spot < strike) else 0.0
        return Greeks(delta=delta, gamma=0.0, theta=0.0, vega=0.0, rho=0.0)

    if method == "analytical":
        d1 = (math.log(spot / strike) + (risk_free_rate + volatility**2 / 2) * time_to_expiry) \
             / (volatility * math.sqrt(time_to_expiry))
        d2 = d1 - volatility * math.sqrt(time_to_expiry)

        pdf_d1 = norm_pdf(d1)

        if option_type == "call":
            delta = norm_cdf(d1)
            theta = (-spot * volatility * pdf_d1 / (2 * math.sqrt(time_to_expiry))
                     - risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry) * norm_cdf(d2))
            rho = strike * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * norm_cdf(d2)
        else:
            delta = norm_cdf(d1) - 1
            theta = (-spot * volatility * pdf_d1 / (2 * math.sqrt(time_to_expiry))
                     + risk_free_rate * strike * math.exp(-risk_free_rate * time_to_expiry) * norm_cdf(-d2))
            rho = -strike * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * norm_cdf(-d2)

        gamma = pdf_d1 / (spot * volatility * math.sqrt(time_to_expiry))
        vega = spot * math.sqrt(time_to_expiry) * pdf_d1 / 100  # per 1% vol

        # Theta per day
        theta_per_day = theta / 365

        return Greeks(
            delta=round(delta, 4),
            gamma=round(gamma, 4),
            theta=round(theta_per_day, 6),
            vega=round(vega, 4),
            rho=round(rho / 100, 4),  # per 1% rate
        )

    else:
        # Finite difference Greeks
        h_spot = spot * 0.001
        h_vol = 0.0001  # 0.01% vol bump
        h_rate = 0.0001
        h_time = 1 / 365  # 1 day

        price = black_scholes(spot, strike, time_to_expiry, volatility, risk_free_rate, option_type)
        price_up = black_scholes(spot + h_spot, strike, time_to_expiry, volatility, risk_free_rate, option_type)
        price_down = black_scholes(spot - h_spot, strike, time_to_expiry, volatility, risk_free_rate, option_type)
        price_vol_up = black_scholes(spot, strike, time_to_expiry, volatility + h_vol, risk_free_rate, option_type)
        price_rate_up = black_scholes(spot, strike, time_to_expiry, volatility, risk_free_rate + h_rate, option_type)
        price_t_down = black_scholes(spot, strike, time_to_expiry - h_time, volatility, risk_free_rate, option_type)

        delta = (price_up - price_down) / (2 * h_spot)
        gamma = (price_up - 2 * price + price_down) / (h_spot ** 2)
        theta = (price_t_down - price) / h_time  # per day
        vega = (price_vol_up - price) / (h_vol * 100)  # per 1% vol
        rho = (price_rate_up - price) / (h_rate * 100)  # per 1% rate

        return Greeks(
            delta=round(delta, 4),
            gamma=round(gamma, 4),
            theta=round(theta, 6),
            vega=round(vega, 4),
            rho=round(rho, 4),
        )


# ─── Implied Volatility ──────────────────────────────────────────────────

def implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    option_type: str = "call",
    max_iter: int = 100,
    tolerance: float = 1e-8,
) -> Optional[float]:
    """
    Newton-Raphson solver for implied volatility.

    σ_{n+1} = σ_n - (BS(σ_n) - market_price) / vega(σ_n)

    Finds the volatility that makes the Black-Scholes price match the market price.
    """
    # Initial guess: use approximation from Brenner-Subrahmanyam (1988)
    # For ATM options: σ ≈ C · √(2π/T) / S
    if abs(spot - strike * math.exp(-risk_free_rate * time_to_expiry)) < spot * 0.01:
        sigma = market_price * math.sqrt(2 * math.pi / time_to_expiry) / spot
    else:
        sigma = 0.3  # Fallback initial guess

    sigma = max(0.01, min(sigma, 5.0))  # Clamp to sane range

    for i in range(max_iter):
        price = black_scholes(spot, strike, time_to_expiry, sigma, risk_free_rate, option_type)
        diff = price - market_price

        if abs(diff) < tolerance:
            return sigma

        # Vega = S·√T·N'(d1)  (raw vega, per unit vol)
        d1 = (math.log(spot / strike) + (risk_free_rate + sigma**2 / 2) * time_to_expiry) \
             / (sigma * math.sqrt(time_to_expiry))
        vega_raw = spot * math.sqrt(time_to_expiry) * norm_pdf(d1)

        if abs(vega_raw) < 1e-12:
            return None  # Vega too small, can't converge

        sigma = sigma - diff / vega_raw

        if sigma <= 0:
            return None  # Negative vol, invalid

    return None  # Failed to converge


# ─── Parity Check ────────────────────────────────────────────────────────

def check_put_call_parity(
    spot: float,
    strike: float,
    time_to_expiry: float,
    volatility: float,
    risk_free_rate: float,
) -> dict:
    """
    Verify Put-Call Parity: C - P = S - K·e^(-rT)

    Returns the parity discrepancy — should be near zero for valid pricing.
    """
    call = black_scholes(spot, strike, time_to_expiry, volatility, risk_free_rate, "call")
    put = black_scholes(spot, strike, time_to_expiry, volatility, risk_free_rate, "put")
    pv_strike = strike * math.exp(-risk_free_rate * time_to_expiry)

    lhs = call - put
    rhs = spot - pv_strike

    return {
        "call": round(call, 4),
        "put": round(put, 4),
        "call_minus_put": round(lhs, 4),
        "spot_minus_pv_strike": round(rhs, 4),
        "discrepancy": round(abs(lhs - rhs), 8),
        "parity_holds": abs(lhs - rhs) < 0.01,
    }


# ─── Reports ─────────────────────────────────────────────────────────────

def format_report(
    spot: float, strike: float, days: int, volatility: float, rate: float,
    call_price: float, put_price: float, greeks: Optional[Greeks],
    iv: Optional[float], parity: dict, method: str,
) -> str:
    bar = "═" * 64
    t = days / 365
    moneyness = spot / strike
    label = "ATM" if abs(moneyness - 1) < 0.02 else ("ITM" if moneyness > 1 else "OTM")

    lines = [
        f"\n{bar}",
        f"🎯 OPTIONS PRICING ENGINE — {method.upper()}",
        f"{bar}",
        f"",
        f"📊 MARKET PARAMETERS",
        f"   Spot: ${spot:,.2f}  |  Strike: ${strike:,.2f}  ({label})",
        f"   Days to Expiry: {days}d ({t:.3f}y)  |  σ: {volatility:.1%}  |  r: {rate:.1%}",
        f"",
        f"💰 OPTION PRICES",
        f"   CALL: ${call_price:,.4f}  |  PUT: ${put_price:,.4f}",
    ]

    if greeks:
        lines.extend([
            f"",
            f"📐 GREEKS",
            f"   Δ (delta): {greeks.delta:+.4f}  — sensitivity to underlying price",
            f"   Γ (gamma): {greeks.gamma:.4f}  — rate of change of delta",
            f"   Θ (theta): {greeks.theta:+.4f}/day  — time decay",
            f"   ν (vega):  {greeks.vega:+.4f}/1% vol  — sensitivity to volatility",
            f"   ρ (rho):   {greeks.rho:+.4f}/1% rate  — sensitivity to interest rate",
        ])

    if iv is not None:
        lines.extend([
            f"",
            f"🔮 IMPLIED VOLATILITY: {iv:.2%}",
        ])

    lines.extend([
        f"",
        f"✅ PUT-CALL PARITY",
        f"   C - P = {parity['call_minus_put']:.4f}",
        f"   S - Ke^(-rT) = {parity['spot_minus_pv_strike']:.4f}",
        f"   Discrepancy: {parity['discrepancy']:.8f} {'✅' if parity['parity_holds'] else '⚠️'}",
        f"",
        f"{bar}",
        f"✅ Options pricing complete. Cycle 8 — Autonomous Evolution.",
        f"{bar}\n",
    ])

    return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Options Pricing Engine — Black-Scholes + Binomial Tree + Greeks",
        epilog="Cycle 8 Autonomous Evolution | Claude Code Self-Evolution"
    )
    parser.add_argument("--spot", type=float, required=True, help="Current underlying price")
    parser.add_argument("--strike", type=float, required=True, help="Option strike price")
    parser.add_argument("--days", type=int, default=30, help="Days to expiry")
    parser.add_argument("--vol", "--volatility", type=float, default=0.25, dest="volatility",
                        help="Annualized volatility (e.g. 0.25 = 25%%)")
    parser.add_argument("--rate", type=float, default=0.05, help="Risk-free rate (e.g. 0.05 = 5%%)")
    parser.add_argument("--greeks", action="store_true", help="Compute Greeks")
    parser.add_argument("--american", action="store_true", help="Use binomial tree for American option")
    parser.add_argument("--steps", type=int, default=200, help="Binomial tree steps")
    parser.add_argument("--implied", action="store_true", help="Compute implied volatility")
    parser.add_argument("--price", type=float, default=None, help="Market price for implied vol calculation")
    parser.add_argument("--json", default=None, help="Save JSON output")
    args = parser.parse_args()

    spot = args.spot
    strike = args.strike
    t = args.days / 365
    vol = args.volatility
    rate = args.rate

    if vol <= 0:
        print("❌ Volatility must be positive.", file=sys.stderr)
        sys.exit(1)

    # Pricing
    if args.american:
        method = "binomial-tree (american)"
        call_price = binomial_tree(spot, strike, t, vol, rate, "call", args.steps, american=True)
        put_price = binomial_tree(spot, strike, t, vol, rate, "put", args.steps, american=True)
    else:
        method = "black-scholes (european)"
        call_price = black_scholes(spot, strike, t, vol, rate, "call")
        put_price = black_scholes(spot, strike, t, vol, rate, "put")

    # Greeks
    greeks = None
    if args.greeks:
        greeks = compute_greeks(spot, strike, t, vol, rate, "call")

    # Implied volatility
    iv = None
    if args.implied and args.price is not None:
        iv = implied_volatility(args.price, spot, strike, t, rate, "call")
        if iv is None:
            print("⚠️ Implied volatility failed to converge.")

    # Parity
    parity = check_put_call_parity(spot, strike, t, vol, rate)

    print(format_report(spot, strike, args.days, vol, rate,
                        call_price, put_price, greeks, iv, parity, method))

    if args.json:
        output = {
            "spot": spot,
            "strike": strike,
            "days_to_expiry": args.days,
            "time_to_expiry_years": round(t, 6),
            "volatility": vol,
            "risk_free_rate": rate,
            "call_price": round(call_price, 4),
            "put_price": round(put_price, 4),
            "method": method,
            "put_call_parity": parity,
        }
        if greeks:
            output["greeks"] = {
                "delta": greeks.delta,
                "gamma": greeks.gamma,
                "theta_per_day": greeks.theta,
                "vega_per_1pct_vol": greeks.vega,
                "rho_per_1pct_rate": greeks.rho,
            }
        if iv is not None:
            output["implied_volatility"] = round(iv, 6)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON saved to: {args.json}")


if __name__ == "__main__":
    main()
