"""Portfolio environment for the PPO portfolio optimizer.

The state is a concatenation of

* the past ``lookback`` per-asset returns (flattened),
* the current portfolio weights, and
* the current portfolio volatility.

The action is a new portfolio weight vector (the Actor's softmax output).
The reward is a Sharpe-like objective::

    reward = portfolio_return - risk_penalty * portfolio_volatility

Asset returns are synthetic: multivariate normal draws (with correlation)
clipped to keep portfolio values strictly positive.
"""

from __future__ import annotations

import numpy as np


class PortfolioEnv:
    """A toy portfolio-allocation environment driven by synthetic returns."""

    def __init__(
        self,
        n_assets=3,
        lookback=10,
        risk_penalty=0.5,
        mu=None,
        sigma=None,
        corr=None,
        seed=None,
        max_steps=100,
    ):
        self.n_assets = n_assets
        self.lookback = lookback
        self.risk_penalty = risk_penalty
        self.max_steps = max_steps
        self.rng = np.random.default_rng(seed)

        if mu is None:
            mu = self.rng.uniform(0.0005, 0.002, size=n_assets)
        if sigma is None:
            sigma = self.rng.uniform(0.008, 0.02, size=n_assets)
        if corr is None:
            corr = np.full((n_assets, n_assets), 0.3)
            np.fill_diagonal(corr, 1.0)

        self.mu = np.asarray(mu, dtype=np.float64).reshape(-1)
        self.sigma = np.asarray(sigma, dtype=np.float64).reshape(-1)
        self.corr = np.asarray(corr, dtype=np.float64)
        self.cov = np.outer(self.sigma, self.sigma) * self.corr
        # Regularise so the Cholesky factor always exists.
        self._chol = np.linalg.cholesky(self.cov + 1e-12 * np.eye(n_assets))

        self.last_portfolio_return = 0.0
        self.reset()

    # -- synthetic return generation -------------------------------------
    def _sample_returns(self):
        z = self.rng.standard_normal(self.n_assets)
        r = self.mu + self._chol @ z
        return np.clip(r, -0.3, 0.3)

    def generate_return_series(self, n_periods, seed=None):
        """Draw an independent return series from the same market parameters."""
        rng = np.random.default_rng(seed)
        z = rng.standard_normal((n_periods, self.n_assets))
        returns = self.mu[None, :] + z @ self._chol.T
        return np.clip(returns, -0.3, 0.3)

    # -- helpers ----------------------------------------------------------
    def _portfolio_vol(self, weights):
        v = float(np.asarray(weights) @ self.cov @ np.asarray(weights))
        return float(np.sqrt(max(v, 0.0)))

    def _state(self):
        return np.concatenate(
            [
                self.returns_window.reshape(-1),
                self.weights,
                [self._portfolio_vol(self.weights)],
            ]
        )

    # -- OpenAI-gym-like interface ----------------------------------------
    def reset(self):
        self.step_count = 0
        self.weights = np.ones(self.n_assets) / self.n_assets
        self.returns_window = np.array(
            [self._sample_returns() for _ in range(self.lookback)]
        )
        self.portfolio_value = 1.0
        self.last_portfolio_return = 0.0
        return self._state()

    def step(self, action):
        action = np.asarray(action, dtype=np.float64).reshape(-1)
        if action.size != self.n_assets:
            raise ValueError(f"expected {self.n_assets} weights, got {action.size}")
        total = action.sum()
        if total <= 0:
            action = np.ones(self.n_assets) / self.n_assets
        else:
            action = action / total

        r = self._sample_returns()
        port_ret = float(action @ r)
        self.last_portfolio_return = port_ret
        self.portfolio_value *= 1.0 + port_ret

        vol = self._portfolio_vol(action)
        reward = port_ret - self.risk_penalty * vol

        self.weights = action
        self.returns_window = np.roll(self.returns_window, -1, axis=0)
        self.returns_window[-1] = r
        self.step_count += 1
        done = self.step_count >= self.max_steps
        return self._state(), reward, done
