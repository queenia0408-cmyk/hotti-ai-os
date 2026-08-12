"""Mini PPO Portfolio Optimizer - CLI entry point.

A minimal but correct PPO (Proximal Policy Optimization) agent for portfolio
allocation, implemented with NumPy only.

Examples
--------
    python main.py --train --episodes 500
    python main.py --evaluate
    python main.py --tickers AAPL,MSFT,GOOGL --train --episodes 300
    python main.py --benchmark
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from src.env import PortfolioEnv
from src.ppo import PPO, compute_gae
from src.replay import ReplayBuffer

AGENT_PATH = "ppo_agent.npz"
TRADING_DAYS = 252


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Mini PPO Portfolio Optimizer")
    parser.add_argument("--train", action="store_true", help="Train the PPO agent")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate a trained agent")
    parser.add_argument(
        "--benchmark", action="store_true", help="Compare PPO vs Equal Weight vs Max Sharpe"
    )
    parser.add_argument(
        "--tickers",
        type=str,
        default="AAPL,MSFT,GOOGL",
        help="Comma-separated asset tickers (labels only; data is synthetic)",
    )
    parser.add_argument("--episodes", type=int, default=300, help="Training episodes")
    parser.add_argument("--episode-length", type=int, default=100, help="Steps per episode")
    parser.add_argument("--lookback", type=int, default=10, help="Past returns in the state")
    parser.add_argument("--risk-penalty", type=float, default=0.5, help="Risk penalty in the reward")
    parser.add_argument("--hidden", type=int, default=64, help="Hidden layer size")
    parser.add_argument("--epochs", type=int, default=4, help="PPO epochs per update")
    parser.add_argument("--clip-eps", type=float, default=0.2, help="PPO clipping parameter")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor")
    parser.add_argument("--lam", type=float, default=0.95, help="GAE lambda")
    parser.add_argument("--actor-lr", type=float, default=3e-3, help="Actor learning rate")
    parser.add_argument("--critic-lr", type=float, default=3e-3, help="Critic learning rate")
    parser.add_argument("--update-interval", type=int, default=4, help="Episodes per PPO update")
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    parser.add_argument("--eval-episodes", type=int, default=20, help="Episodes for evaluation")
    parser.add_argument("--benchmark-periods", type=int, default=500, help="Periods in benchmark series")
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Training / evaluation
# ---------------------------------------------------------------------------
def train_agent(ppo, env, episodes, update_interval, gamma, lam, epochs, clip_eps, log_interval=50):
    """Collect trajectories, compute GAE advantages, and run PPO updates."""
    buffer = ReplayBuffer()
    ep_returns = []
    total_returns = []
    for ep in range(episodes):
        state = env.reset()
        done = False
        ep_ret = 0.0
        while not done:
            weights, action_idx, logp = ppo.select_action(state)
            next_state, reward, done = env.step(weights)
            buffer.store(state, action_idx, logp, reward, next_state, done)
            state = next_state
            ep_ret += reward
        ep_returns.append(ep_ret)
        total_returns.append(env.portfolio_value - 1.0)

        if (ep + 1) % update_interval == 0:
            states, actions, old_logps, rewards, next_states, dones = buffer.get_all()
            values = ppo.critic.forward(states).reshape(-1)
            next_values = ppo.critic.forward(next_states).reshape(-1)
            advantages = compute_gae(rewards, values, next_values, dones, gamma, lam)
            returns = advantages + values
            ppo.update(states, actions, old_logps, advantages, returns, epochs=epochs, clip_eps=clip_eps)
            buffer.clear()

        if log_interval and (ep + 1) % log_interval == 0:
            recent = float(np.mean(ep_returns[-log_interval:]))
            tr = float(np.mean(total_returns[-log_interval:]))
            print(f"  episode {ep + 1:4d}/{episodes}  mean_reward={recent:+.5f}  mean_total_return={tr:+.4f}")
    return ep_returns, total_returns


def evaluate_agent(ppo, env, episodes=20):
    """Run the (deterministic) policy and record return / Sharpe per episode."""
    records = []
    for _ in range(episodes):
        state = env.reset()
        done = False
        rets = []
        while not done:
            weights, _, _ = ppo.select_action(state, deterministic=True)
            next_state, _, done = env.step(weights)
            rets.append(env.last_portfolio_return)
            state = next_state
        rets = np.asarray(rets, dtype=np.float64)
        total_return = env.portfolio_value - 1.0
        sharpe = (rets.mean() / (rets.std() + 1e-12)) * np.sqrt(TRADING_DAYS)
        records.append(
            {
                "total_return": float(total_return),
                "mean_daily_return": float(rets.mean()),
                "volatility": float(rets.std() * np.sqrt(TRADING_DAYS)),
                "sharpe": float(sharpe),
            }
        )
    return records


# ---------------------------------------------------------------------------
# Benchmark: PPO vs Equal Weight vs Max Sharpe
# ---------------------------------------------------------------------------
def make_state(window, weights, cov):
    vol = float(np.sqrt(max(float(np.asarray(weights) @ cov @ np.asarray(weights)), 0.0)))
    return np.concatenate([np.asarray(window).reshape(-1), np.asarray(weights).reshape(-1), [vol]])


def evaluate_strategy_on_series(series, weight_fn, lookback, cov):
    """Apply a weight function to a fixed return series and score it."""
    series = np.asarray(series, dtype=np.float64)
    T, A = series.shape
    weights = np.ones(A) / A
    rets = []
    value = 1.0
    for t in range(T):
        if t >= lookback:
            window = series[t - lookback : t]
        else:
            window = np.zeros((lookback, A))
            if t > 0:
                window[lookback - t :] = series[:t]
        state = make_state(window, weights, cov)
        w = np.asarray(weight_fn(state), dtype=np.float64).reshape(-1)
        w = np.clip(w, 0.0, None)
        if w.sum() <= 0.0:
            w = np.ones(A) / A
        else:
            w = w / w.sum()
        port_ret = float(w @ series[t])
        weights = w
        value *= 1.0 + port_ret
        rets.append(port_ret)
    rets = np.asarray(rets, dtype=np.float64)
    mean = rets.mean()
    std = rets.std()
    return {
        "total_return": float(value - 1.0),
        "mean_daily_return": float(mean),
        "volatility": float(std * np.sqrt(TRADING_DAYS)),
        "sharpe": float((mean / (std + 1e-12)) * np.sqrt(TRADING_DAYS)),
    }


def max_sharpe_weights(series):
    """Long-only max-Sharpe (tangency) weights estimated in-sample."""
    series = np.asarray(series, dtype=np.float64)
    A = series.shape[1]
    mu = series.mean(axis=0)
    cov = np.cov(series.T) + 1e-6 * np.eye(A)
    w = np.linalg.solve(cov, mu)
    w = np.clip(w, 0.0, None)
    s = w.sum()
    if s <= 0.0:
        return np.ones(A) / A
    return w / s


def run_benchmark(ppo, env, n_periods=500, lookback=10, seed=0):
    """Compare PPO, Equal Weight and Max Sharpe on one synthetic series."""
    series = env.generate_return_series(n_periods, seed=seed)
    A = env.n_assets

    def ppo_weight_fn(state):
        return ppo.actor.forward(state.reshape(1, -1)).reshape(-1)

    eq_w = np.ones(A) / A
    ms_w = max_sharpe_weights(series)

    return {
        "PPO": evaluate_strategy_on_series(series, ppo_weight_fn, lookback, env.cov),
        "EqualWeight": evaluate_strategy_on_series(series, lambda s: eq_w, lookback, env.cov),
        "MaxSharpe": evaluate_strategy_on_series(series, lambda s: ms_w, lookback, env.cov),
    }


def print_table(results, tickers):
    print(f"\nBenchmark on {len(tickers)} synthetic assets ({', '.join(tickers)})")
    header = f"{'Strategy':<12}{'Total Return':>14}{'Mean Daily':>12}{'Volatility':>12}{'Sharpe':>10}"
    print(header)
    print("-" * len(header))
    for name, r in results.items():
        print(
            f"{name:<12}{r['total_return']:>14.4f}{r['mean_daily_return']:>12.5f}"
            f"{r['volatility']:>12.4f}{r['sharpe']:>10.3f}"
        )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None):
    args = parse_args(argv)
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if not tickers:
        tickers = ["AAPL", "MSFT", "GOOGL"]
    n_assets = len(tickers)
    state_dim = args.lookback * n_assets + n_assets + 1

    if not (args.train or args.evaluate or args.benchmark):
        print("Nothing to do. Pass --train, --evaluate, or --benchmark.")
        return 1

    ppo = None
    if args.train:
        ppo = PPO(state_dim, n_assets, hidden=args.hidden, actor_lr=args.actor_lr,
                  critic_lr=args.critic_lr, seed=args.seed)
        env = PortfolioEnv(n_assets=n_assets, lookback=args.lookback,
                           risk_penalty=args.risk_penalty, seed=args.seed,
                           max_steps=args.episode_length)
        print(f"Training PPO on {n_assets} assets ({', '.join(tickers)}) for {args.episodes} episodes")
        train_agent(ppo, env, args.episodes, args.update_interval, args.gamma,
                    args.lam, args.epochs, args.clip_eps)
        ppo.save(AGENT_PATH)
        print(f"Saved agent to {AGENT_PATH}")

    if args.evaluate:
        if ppo is None:
            ppo = PPO(state_dim, n_assets, hidden=args.hidden, actor_lr=args.actor_lr,
                      critic_lr=args.critic_lr, seed=args.seed)
            if not ppo.load(AGENT_PATH):
                print(f"No trained agent found at {AGENT_PATH}. Run --train first.")
                return 1
        env = PortfolioEnv(n_assets=n_assets, lookback=args.lookback,
                           risk_penalty=args.risk_penalty, seed=args.seed + 1,
                           max_steps=args.episode_length)
        print(f"Evaluating agent over {args.eval_episodes} episodes")
        records = evaluate_agent(ppo, env, episodes=args.eval_episodes)
        mean_tr = float(np.mean([r["total_return"] for r in records]))
        mean_sharpe = float(np.mean([r["sharpe"] for r in records]))
        mean_vol = float(np.mean([r["volatility"] for r in records]))
        print(f"  mean total return      : {mean_tr:+.4f}")
        print(f"  mean annualized Sharpe : {mean_sharpe:+.3f}")
        print(f"  mean annualized vol    : {mean_vol:.4f}")

    if args.benchmark:
        if ppo is None:
            ppo = PPO(state_dim, n_assets, hidden=args.hidden, actor_lr=args.actor_lr,
                      critic_lr=args.critic_lr, seed=args.seed)
            env = PortfolioEnv(n_assets=n_assets, lookback=args.lookback,
                               risk_penalty=args.risk_penalty, seed=args.seed,
                               max_steps=args.episode_length)
            quick = min(args.episodes, 150)
            print(f"Quick-training a fresh agent for the benchmark ({quick} episodes)")
            train_agent(ppo, env, quick, args.update_interval, args.gamma,
                        args.lam, args.epochs, args.clip_eps)
        else:
            env = PortfolioEnv(n_assets=n_assets, lookback=args.lookback,
                               risk_penalty=args.risk_penalty, seed=args.seed,
                               max_steps=args.episode_length)
        print("Running benchmark: PPO vs Equal Weight vs Max Sharpe")
        results = run_benchmark(ppo, env, n_periods=args.benchmark_periods,
                                lookback=args.lookback, seed=args.seed)
        print_table(results, tickers)

    return 0


if __name__ == "__main__":
    sys.exit(main())
