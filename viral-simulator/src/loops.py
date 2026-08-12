"""Viral loop type definitions.

A viral loop is the mechanism by which one user brings in the next. Four
archetypes are modelled, each with a different K-factor and cycle time:

┌──────────────┬─────────────────────────────┬─────────┬───────────┐
│ Loop type    │ Mechanism                   │ K₀      │ Cycle     │
├──────────────┼─────────────────────────────┼─────────┼───────────┤
│ Organic      │ Built into the product      │ 0.30    │  3 days   │
│ Incentivized │ Double-sided referral reward│ 0.60    │  7 days   │
│ Content      │ Users create shareable work │ 1.20    │ 30 days   │
│ Embedded     │ Product requires others     │ 1.50    │  1 day    │
└──────────────┴─────────────────────────────┴─────────┴───────────┘
"""

from dataclasses import dataclass
from enum import Enum


class LoopType(Enum):
    """The four viral loop archetypes."""

    ORGANIC = "organic"
    INCENTIVIZED = "incentivized"
    CONTENT = "content"
    EMBEDDED = "embedded"


@dataclass(frozen=True)
class ViralLoop:
    """A viral loop archetype.

    Attributes:
        name: Short display name.
        description: What makes this loop work.
        default_k: The K-factor this loop typically exhibits.
        cycle_time_days: How long one full loop iteration takes.
        mechanism: How users bring in other users.
    """

    name: str
    description: str
    default_k: float
    cycle_time_days: float
    mechanism: str


LOOPS: dict[LoopType, ViralLoop] = {
    LoopType.ORGANIC: ViralLoop(
        name="Organic",
        description="Built into the product; sharing happens naturally.",
        default_k=0.30,
        cycle_time_days=3.0,
        mechanism="Invite-on-use, word of mouth, built-in sharing.",
    ),
    LoopType.INCENTIVIZED: ViralLoop(
        name="Incentivized",
        description="Double-sided rewards for the inviter and the invitee.",
        default_k=0.60,
        cycle_time_days=7.0,
        mechanism="Referral codes, double-sided rewards, gamified invites.",
    ),
    LoopType.CONTENT: ViralLoop(
        name="Content",
        description="Users create shareable output that carries the brand.",
        default_k=1.20,
        cycle_time_days=30.0,
        mechanism="User-generated content, templates, memes, shared posts.",
    ),
    LoopType.EMBEDDED: ViralLoop(
        name="Embedded",
        description="The product inherently requires others to join.",
        default_k=1.50,
        cycle_time_days=1.0,
        mechanism="Network effects, collaboration, mutual usage.",
    ),
}
