"""Trajectory replay buffer for the PPO training loop."""

from __future__ import annotations

import numpy as np


class ReplayBuffer:
    """Stores transitions ``(s, a, logp, r, s', done)`` and samples from them.

    The buffer holds a batch of recent trajectories between PPO updates.
    ``actions`` are sampled asset indices and ``log_probs`` the corresponding
    policy log-probabilities under the behaviour policy.
    """

    def __init__(self, capacity=None, seed=None):
        self.capacity = capacity
        self.rng = np.random.default_rng(seed)
        self.states = []
        self.actions = []
        self.log_probs = []
        self.rewards = []
        self.next_states = []
        self.dones = []

    def store(self, state, action, log_prob, reward, next_state, done):
        self.states.append(state)
        self.actions.append(action)
        self.log_probs.append(log_prob)
        self.rewards.append(reward)
        self.next_states.append(next_state)
        self.dones.append(bool(done))
        if self.capacity is not None and len(self.states) > self.capacity:
            del self.states[0]
            del self.actions[0]
            del self.log_probs[0]
            del self.rewards[0]
            del self.next_states[0]
            del self.dones[0]

    def get_all(self):
        """Return all stored transitions as NumPy arrays."""
        return (
            np.asarray(self.states, dtype=np.float64),
            np.asarray(self.actions, dtype=np.int64),
            np.asarray(self.log_probs, dtype=np.float64),
            np.asarray(self.rewards, dtype=np.float64),
            np.asarray(self.next_states, dtype=np.float64),
            np.asarray(self.dones, dtype=bool),
        )

    def sample(self, batch_size=None):
        """Return ``batch_size`` transitions (or all of them) as arrays."""
        states, actions, log_probs, rewards, next_states, dones = self.get_all()
        n = len(states)
        if batch_size is None or batch_size >= n:
            idx = np.arange(n)
        else:
            idx = self.rng.choice(n, size=batch_size, replace=False)
        return (
            states[idx],
            actions[idx],
            log_probs[idx],
            rewards[idx],
            next_states[idx],
            dones[idx],
        )

    def clear(self):
        self.states.clear()
        self.actions.clear()
        self.log_probs.clear()
        self.rewards.clear()
        self.next_states.clear()
        self.dones.clear()

    def __len__(self):
        return len(self.states)
