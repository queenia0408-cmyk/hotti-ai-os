"""Proximal Policy Optimization (PPO) with a clipped surrogate objective.

Implements the clipped PPO objective

    L^CLIP(theta) = E_t[ min( r_t(theta) * A_t,
                              clip(r_t(theta), 1-eps, 1+eps) * A_t ) ]

with the importance-sampling ratio ``r_t(theta) = pi_theta(a|s) / pi_old(a|s)``,
Generalized Advantage Estimation (GAE) for the advantages, and an
Actor-Critic architecture. Everything is implemented with NumPy only.
"""

from __future__ import annotations

import numpy as np

from .networks import Actor, Critic

# Defaults from the project spec / the PPO paper.
CLIP_EPS = 0.2
GAMMA = 0.99
LAMBDA = 0.95
PPO_EPOCHS = 4


def clip_ratio(ratio, clip_eps=CLIP_EPS):
    """Clip the importance-sampling ratio to ``[1 - eps, 1 + eps]``."""
    ratio = np.asarray(ratio, dtype=np.float64)
    return np.clip(ratio, 1.0 - clip_eps, 1.0 + clip_eps)


def clip_loss(ratio, advantage, clip_eps=CLIP_EPS):
    """The clipped PPO surrogate objective, averaged over the batch.

    Returns ``-mean( min(r*A, clip(r, 1-eps, 1+eps)*A) )`` so that it can be
    minimised by gradient descent.
    """
    ratio = np.asarray(ratio, dtype=np.float64)
    adv = np.asarray(advantage, dtype=np.float64)
    surr1 = ratio * adv
    surr2 = np.clip(ratio, 1.0 - clip_eps, 1.0 + clip_eps) * adv
    return float(-np.mean(np.minimum(surr1, surr2)))


def compute_gae(rewards, values, next_values, dones, gamma=GAMMA, lam=LAMBDA):
    """Generalized Advantage Estimation (Schulman et al., 2015).

    ``delta_t   = r_t + gamma * V(s_{t+1}) - V(s_t)``  (no bootstrap on done)
    ``A_t       = delta_t + (gamma * lambda) * A_{t+1}``
    """
    rewards = np.asarray(rewards, dtype=np.float64).reshape(-1)
    values = np.asarray(values, dtype=np.float64).reshape(-1)
    next_values = np.asarray(next_values, dtype=np.float64).reshape(-1)
    dones = np.asarray(dones, dtype=bool).reshape(-1)

    T = len(rewards)
    advantages = np.zeros(T, dtype=np.float64)
    gae = 0.0
    for t in reversed(range(T)):
        if dones[t]:
            delta = rewards[t] - values[t]
            gae = delta
        else:
            delta = rewards[t] + gamma * next_values[t] - values[t]
            gae = delta + gamma * lam * gae
        advantages[t] = gae
    return advantages


class PPO:
    """Actor-Critic PPO agent for portfolio allocation."""

    def __init__(self, state_dim, action_dim, hidden=64, actor_lr=3e-3, critic_lr=3e-3, seed=None):
        self.state_dim = state_dim
        self.action_dim = action_dim
        rng = np.random.default_rng(seed)
        self.actor = Actor(state_dim, action_dim, hidden, seed=int(rng.integers(0, 2**31)))
        self.critic = Critic(state_dim, hidden, seed=int(rng.integers(0, 2**31)))
        self.actor_lr = actor_lr
        self.critic_lr = critic_lr

    # -- acting -----------------------------------------------------------
    def select_action(self, state, deterministic=False):
        """Return ``(weights, action_idx, log_prob)``.

        ``weights`` is the Actor's softmax output and is what gets applied to
        the environment. ``action_idx`` is a sample from the same categorical
        distribution; it, together with ``log_prob``, drives the PPO ratio.
        """
        state = np.asarray(state, dtype=np.float64).reshape(1, -1)
        probs = self.actor.forward(state).reshape(-1)
        if deterministic:
            idx = int(np.argmax(probs))
        else:
            idx = int(self.actor.rng.choice(self.action_dim, p=probs))
        logp = float(np.log(max(probs[idx], 1e-12)))
        return probs, idx, logp

    # -- training ---------------------------------------------------------
    def compute_gae(self, rewards, values, next_values, dones, gamma=GAMMA, lam=LAMBDA):
        return compute_gae(rewards, values, next_values, dones, gamma, lam)

    def update(self, states, actions, old_logps, advantages, returns, epochs=PPO_EPOCHS, clip_eps=CLIP_EPS):
        """Run multiple PPO epochs over a batch; returns the final losses."""
        states = np.asarray(states, dtype=np.float64)
        actions = np.asarray(actions, dtype=np.int64).reshape(-1)
        old_logps = np.asarray(old_logps, dtype=np.float64).reshape(-1)
        adv = np.asarray(advantages, dtype=np.float64).reshape(-1)
        returns = np.asarray(returns, dtype=np.float64).reshape(-1)
        N = len(states)

        # Standard PPO trick: normalise advantages for stable updates.
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)

        info = {}
        for _ in range(epochs):
            logp = self.actor.log_prob(states, actions)
            ratio = np.exp(np.clip(logp - old_logps, -20.0, 20.0))
            ratio = np.clip(ratio, 1e-6, 1e6)  # numerical safety

            # Clipped surrogate objective.
            clipped = np.clip(ratio, 1.0 - clip_eps, 1.0 + clip_eps)
            surr1 = ratio * adv
            surr2 = clipped * adv
            actor_loss = -np.mean(np.minimum(surr1, surr2))

            # Value (critic) loss: MSE against the GAE return targets.
            values = self.critic.forward(states).reshape(-1)
            critic_loss = np.mean((values - returns) ** 2)

            # --- Actor gradient ------------------------------------------
            # Gradient only flows where ``min`` selects the unclipped term.
            mask = ((adv >= 0.0) & (ratio < 1.0 + clip_eps)) | (
                (adv < 0.0) & (ratio > 1.0 - clip_eps)
            )
            g = -(mask * adv * ratio) / N
            d_logp = self.actor.grad_log_prob(states, actions)  # wrt logits
            self.actor.net.backward(g[:, None] * d_logp)
            self.actor.net.step(self.actor_lr)

            # --- Critic gradient -----------------------------------------
            d_critic = (2.0 / N) * (values - returns).reshape(-1, 1)
            self.critic.net.backward(d_critic)
            self.critic.net.step(self.critic_lr)

            info = {
                "actor_loss": float(actor_loss),
                "critic_loss": float(critic_loss),
                "total_loss": float(actor_loss + critic_loss),
            }
        return info

    # -- persistence ------------------------------------------------------
    def save(self, path):
        data = {}
        for k, v in self.actor.net.params.items():
            data[f"actor_{k}"] = v
        for k, v in self.critic.net.params.items():
            data[f"critic_{k}"] = v
        np.savez(path, **data)

    def load(self, path):
        try:
            data = np.load(path)
        except (IOError, OSError, FileNotFoundError):
            return False
        for k in self.actor.net.params:
            self.actor.net.params[k] = data[f"actor_{k}"]
        for k in self.critic.net.params:
            self.critic.net.params[k] = data[f"critic_{k}"]
        return True
