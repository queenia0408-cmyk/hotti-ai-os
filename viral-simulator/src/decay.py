"""K-factor decay models.

The K-factor (viral coefficient) is not constant. As a product saturates its
addressable market, each new invite converts a smaller share of new users.
This is modelled as a time-dependent decay of the initial K-factor:

    K(t) = K₀ · e^(−δ·t)

where:
    K₀  — initial K-factor (invites per user × conversion rate)
    δ   — saturation decay rate (higher δ → faster saturation)
    t   — elapsed time, in days or cycles
"""

from collections.abc import Callable
from enum import Enum
from math import exp


class DecayType(Enum):
    """Supported decay models."""

    CONSTANT = "constant"        # No decay: K(t) = K₀ forever
    EXPONENTIAL = "exponential"  # Saturation: K(t) = K₀·e^(−δt)


def constant_k(k0: float, decay_rate: float, t: float) -> float:
    """No-decay model: the K-factor stays at K₀ forever."""
    return float(k0)


def exponential_decay(k0: float, decay_rate: float, t: float) -> float:
    """Exponential saturation decay: K(t) = K₀ · e^(−δ·t)."""
    return float(k0 * exp(-decay_rate * t))


DECAY_FUNCTIONS: dict[DecayType, Callable[[float, float, float], float]] = {
    DecayType.CONSTANT: constant_k,
    DecayType.EXPONENTIAL: exponential_decay,
}


def effective_k(
    k0: float,
    decay_rate: float,
    t: float,
    decay_type: DecayType = DecayType.EXPONENTIAL,
) -> float:
    """Compute the effective K-factor at time `t` under the given decay model."""
    return DECAY_FUNCTIONS[decay_type](k0, decay_rate, t)
