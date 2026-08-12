"""Simple neural-network building blocks implemented with NumPy only.

The :class:`MLP` is a small multi-layer perceptron with ReLU hidden units and a
linear output layer, plus manual forward/backward passes and a
gradient-descent update step. :class:`Actor` and :class:`Critic` wrap MLPs for
the policy and the value function used by the PPO agent.
"""

from __future__ import annotations

import numpy as np


def softmax(x, axis=-1):
    """Numerically stable softmax along ``axis``."""
    x = np.asarray(x, dtype=np.float64)
    m = np.max(x, axis=axis, keepdims=True)
    e = np.exp(x - m)
    return e / np.sum(e, axis=axis, keepdims=True)


def logsumexp(x, axis=-1):
    """Numerically stable log-sum-exp; keeps the reduced dimension (size 1)."""
    x = np.asarray(x, dtype=np.float64)
    m = np.max(x, axis=axis, keepdims=True)
    return np.log(np.sum(np.exp(x - m), axis=axis, keepdims=True)) + m


class MLP:
    """Multi-layer perceptron (ReLU hidden, linear output) with manual backprop.

    Parameters
    ----------
    sizes : list[int]
        Layer sizes, e.g. ``[input, hidden, output]``.
    seed : int or None
        Seed for reproducible weight initialisation.
    init_scale : float
        Scales the Xavier-style uniform weight initialisation.
    """

    def __init__(self, sizes, seed=None, init_scale=1.0):
        self.sizes = list(sizes)
        self.init_scale = init_scale
        rng = np.random.default_rng(seed)
        self.params = {}
        self.grads = {}
        for i in range(len(sizes) - 1):
            fan_in, fan_out = sizes[i], sizes[i + 1]
            limit = init_scale * np.sqrt(6.0 / (fan_in + fan_out))
            self.params[f"W{i}"] = rng.uniform(-limit, limit, size=(fan_in, fan_out))
            self.params[f"b{i}"] = np.zeros((fan_out,))
        self.cache = {}

    def forward(self, x):
        """Forward pass. Returns output of shape ``(batch, sizes[-1])``."""
        x = np.asarray(x, dtype=np.float64)
        if x.ndim == 1:
            x = x.reshape(1, -1)
        self.cache = {"a0": x}
        n = len(self.sizes) - 1
        a = x
        for i in range(n):
            z = a @ self.params[f"W{i}"] + self.params[f"b{i}"]
            self.cache[f"z{i}"] = z
            a = np.maximum(0.0, z) if i < n - 1 else z
            self.cache[f"a{i + 1}"] = a
        return a

    def backward(self, dout):
        """Backward pass; ``dout`` is the gradient of the loss wrt the output.

        Fills and returns ``self.grads``.
        """
        n = len(self.sizes) - 1
        d = np.asarray(dout, dtype=np.float64)
        self.grads = {}
        for i in range(n - 1, -1, -1):
            a_prev = self.cache[f"a{i}"]
            dz = d if i == n - 1 else d * (self.cache[f"z{i}"] > 0.0)
            self.grads[f"W{i}"] = a_prev.T @ dz
            self.grads[f"b{i}"] = np.sum(dz, axis=0)
            if i > 0:
                d = dz @ self.params[f"W{i}"].T
        return self.grads

    def step(self, lr, grad_clip=5.0):
        """Gradient-descent update with optional per-parameter gradient clipping."""
        for k in self.params:
            g = np.clip(self.grads[k], -grad_clip, grad_clip)
            self.params[k] -= lr * g


class Actor:
    """Policy network: maps a state to portfolio weights via softmax.

    The softmax output is used both as the portfolio allocation (applied to
    the environment) and as a categorical distribution over asset indices,
    which supplies the log-probability used by the PPO importance ratio.
    """

    def __init__(self, state_dim, action_dim, hidden=64, seed=None):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.net = MLP([state_dim, hidden, action_dim], seed=seed)
        self.rng = np.random.default_rng(seed)

    def forward(self, state):
        """Return softmax weights of shape ``(batch, action_dim)``."""
        state = np.asarray(state, dtype=np.float64)
        if state.ndim == 1:
            state = state.reshape(1, -1)
        return softmax(self.net.forward(state), axis=-1)

    def log_prob(self, state, action):
        """Log-probabilities of categorical ``action`` indices under the policy."""
        logits = self.net.forward(state)
        logp = logits - logsumexp(logits, axis=-1)
        action = np.asarray(action)
        if action.ndim == 1:
            idx = action.astype(np.int64).reshape(-1, 1)
            return np.take_along_axis(logp, idx, axis=1).reshape(-1)
        return np.sum(action * logp, axis=-1)

    def grad_log_prob(self, state, action):
        """Gradient of ``log_prob`` wrt the actor output logits: ``onehot - softmax``."""
        probs = self.forward(state)
        action = np.asarray(action)
        onehot = np.zeros_like(probs)
        if action.ndim == 1:
            onehot[np.arange(len(action)), action.astype(np.int64)] = 1.0
        else:
            onehot = action
        return onehot - probs


class Critic:
    """Value network: maps a state to a scalar value estimate."""

    def __init__(self, state_dim, hidden=64, seed=None):
        self.state_dim = state_dim
        self.net = MLP([state_dim, hidden, 1], seed=seed)

    def forward(self, state):
        """Return value estimates of shape ``(batch, 1)``."""
        state = np.asarray(state, dtype=np.float64)
        if state.ndim == 1:
            state = state.reshape(1, -1)
        return self.net.forward(state)
