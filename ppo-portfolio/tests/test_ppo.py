"""Tests for the Mini PPO Portfolio Optimizer (10 tests)."""

import numpy as np

import main as main_mod
from src.env import PortfolioEnv
from src.networks import Actor, Critic
from src.ppo import PPO, clip_loss, clip_ratio, compute_gae
from src.replay import ReplayBuffer


def test_clip_loss_computes_correctly():
    ratio = np.array([1.0, 1.5, 0.5, 1.1])
    adv = np.array([1.0, 1.0, -1.0, 2.0])
    loss = clip_loss(ratio, adv, clip_eps=0.2)
    # surrogates: min(1.0,1.0)=1.0, min(1.5,1.2)=1.2, min(-0.5,-0.8)=-0.8,
    #             min(2.2,2.2)=2.2  ->  mean = 3.6/4 = 0.9  ->  loss = -0.9
    assert np.isclose(loss, -0.9)


def test_gae_computes_correctly():
    rewards = [1.0, 1.0, 1.0, 1.0]
    values = [0.5, 0.6, 0.7, 0.8]
    next_values = [0.6, 0.7, 0.8, 0.0]
    dones = [False, False, False, True]
    adv = compute_gae(rewards, values, next_values, dones, gamma=0.99, lam=0.95)
    expected = np.array([3.254266474, 2.29693405, 1.2801, 0.2])
    assert np.allclose(adv, expected, atol=1e-6)


def test_actor_outputs_valid_weights():
    actor = Actor(state_dim=5, action_dim=3, seed=0)
    x = np.random.default_rng(0).normal(size=(4, 5))
    probs = actor.forward(x)
    assert probs.shape == (4, 3)
    assert np.allclose(probs.sum(axis=1), 1.0)
    assert np.all(probs >= 0.0)


def test_critic_outputs_scalar():
    critic = Critic(state_dim=5, seed=0)
    x = np.random.default_rng(1).normal(size=(4, 5))
    out = critic.forward(x)
    assert out.shape == (4, 1)


def test_environment_step_returns_tuple():
    env = PortfolioEnv(n_assets=3, lookback=5, seed=0, max_steps=10)
    state = env.reset()
    assert state.shape == (5 * 3 + 3 + 1,)
    result = env.step(np.array([0.5, 0.3, 0.2]))
    assert isinstance(result, tuple) and len(result) == 3
    next_state, reward, done = result
    assert next_state.shape == state.shape
    assert isinstance(done, bool)


def test_portfolio_value_nonnegative():
    env = PortfolioEnv(n_assets=3, lookback=5, seed=0, max_steps=200)
    rng = np.random.default_rng(0)
    state = env.reset()
    for _ in range(100):
        w = rng.dirichlet(np.ones(3))
        state, reward, done = env.step(w)
        assert env.portfolio_value >= 0.0
        if done:
            state = env.reset()


def test_training_reduces_loss():
    n_assets, lookback = 3, 5
    state_dim = lookback * n_assets + n_assets + 1
    ppo = PPO(state_dim, n_assets, hidden=32, actor_lr=1e-3, critic_lr=1e-2, seed=0)
    env = PortfolioEnv(n_assets=n_assets, lookback=lookback, seed=0, max_steps=30)

    # Collect a trajectory for a representative batch of states/actions.
    states, actions, old_logps = [], [], []
    state = env.reset()
    done = False
    while not done:
        weights, idx, logp = ppo.select_action(state)
        next_state, reward, done = env.step(weights)
        states.append(state)
        actions.append(idx)
        old_logps.append(logp)
        state = next_state
    states = np.asarray(states)
    actions = np.asarray(actions)
    old_logps = np.asarray(old_logps)

    # Use a synthetic return target with a clear signal so the loss reduction
    # is numerically unambiguous.
    rng = np.random.default_rng(1)
    returns = rng.uniform(0.0, 1.0, size=len(states))
    advantages = returns - ppo.critic.forward(states).reshape(-1)

    loss_before = np.mean((ppo.critic.forward(states).reshape(-1) - returns) ** 2)
    ppo.update(states, actions, old_logps, advantages, returns, epochs=200, clip_eps=0.2)
    loss_after = np.mean((ppo.critic.forward(states).reshape(-1) - returns) ** 2)

    assert loss_after < loss_before * 0.5


def test_benchmark_compares_all_methods():
    n_assets, lookback = 3, 5
    state_dim = lookback * n_assets + n_assets + 1
    ppo = PPO(state_dim, n_assets, hidden=16, seed=0)
    env = PortfolioEnv(n_assets=n_assets, lookback=lookback, seed=0, max_steps=20)
    results = main_mod.run_benchmark(ppo, env, n_periods=100, lookback=lookback, seed=1)
    assert set(results.keys()) == {"PPO", "EqualWeight", "MaxSharpe"}
    for name, r in results.items():
        assert "total_return" in r and "sharpe" in r
        assert np.isfinite(r["total_return"]) and np.isfinite(r["sharpe"])


def test_replay_buffer_stores_correctly():
    buffer = ReplayBuffer()
    for i in range(5):
        buffer.store(np.array([i, i + 1]), i, -0.5 - i, i * 0.1,
                     np.array([i + 1, i + 2]), i % 2 == 0)
    assert len(buffer) == 5
    states, actions, log_probs, rewards, next_states, dones = buffer.get_all()
    assert states.shape == (5, 2)
    assert actions.tolist() == [0, 1, 2, 3, 4]
    assert log_probs.tolist() == [-0.5, -1.5, -2.5, -3.5, -4.5]
    assert np.allclose(rewards, [0.0, 0.1, 0.2, 0.3, 0.4])
    assert next_states.shape == (5, 2)
    assert dones.tolist() == [True, False, True, False, True]
    sampled_states, sampled_actions, *_ = buffer.sample(batch_size=3)
    assert sampled_states.shape == (3, 2)
    buffer.clear()
    assert len(buffer) == 0


def test_clip_ratio_bounded():
    ratio = np.array([0.1, 0.8, 1.0, 1.2, 2.5, 5.0])
    clipped = clip_ratio(ratio, clip_eps=0.2)
    assert np.all(clipped >= 0.8)
    assert np.all(clipped <= 1.2)
    assert np.allclose(clipped, np.clip(ratio, 0.8, 1.2))
