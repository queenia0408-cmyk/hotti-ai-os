"""Raft leader election with randomized timeouts.

Key property: Randomized election timeouts ensure split votes are rare
and that a leader is elected with probability → 1.

The election safety property: at most one leader can be elected in a
given term. This is guaranteed by the voting rule — each server votes
for at most one candidate per term, and a candidate needs majority.
"""

import asyncio
import random
from enum import Enum, auto
from dataclasses import dataclass


class ElectionState(Enum):
    """States of the election timer."""
    FOLLOWER = auto()    # Waiting for heartbeat from leader
    CANDIDATE = auto()   # Election timeout fired — requesting votes
    LEADER = auto()      # Won election — sending heartbeats


@dataclass
class ElectionTimer:
    """Randomized election timeout à la Raft §5.2.

    The timeout is randomized in [min_ms, max_ms] to prevent split votes.
    Raft paper recommends 150ms–300ms for practical systems; we scale up
    for simulation visibility.

    Attributes:
        min_ms: Minimum election timeout in milliseconds.
        max_ms: Maximum election timeout in milliseconds.
        current_timeout: The randomly chosen timeout for this election round.
        elapsed: Milliseconds elapsed since last heartbeat received.
    """
    min_ms: int = 2000   # Simulation-scaled for visibility
    max_ms: int = 4000
    current_timeout: float = 0.0
    elapsed: float = 0.0

    def __post_init__(self):
        self.reset()

    def reset(self):
        """Reset the timer with a new random timeout.

        Must be called when:
        - A valid heartbeat is received from the current leader
        - The node grants a vote to a candidate
        - The node becomes a candidate itself
        """
        self.elapsed = 0.0
        self.current_timeout = random.uniform(self.min_ms, self.max_ms) / 1000.0

    def tick(self, dt: float) -> bool:
        """Advance the timer by dt seconds.

        Returns True if the timeout has fired (node should become candidate).
        """
        self.elapsed += dt
        return self.elapsed >= self.current_timeout

    @property
    def remaining(self) -> float:
        """Seconds remaining until timeout fires."""
        return max(0.0, self.current_timeout - self.elapsed)

    @property
    def fired(self) -> bool:
        """Has the election timeout fired?"""
        return self.elapsed >= self.current_timeout


@dataclass
class VoteRequest:
    """RequestVote RPC arguments."""
    term: int             # Candidate's current term
    candidate_id: int     # Candidate requesting the vote
    last_log_index: int   # Index of candidate's last log entry
    last_log_term: int    # Term of candidate's last log entry


@dataclass
class VoteResponse:
    """RequestVote RPC results."""
    term: int              # Current term, for candidate to update itself
    vote_granted: bool     # True means candidate received vote


def should_grant_vote(
    candidate_last_index: int,
    candidate_last_term: int,
    voter_last_index: int,
    voter_last_term: int,
    voted_for: int | None,
    candidate_id: int,
    candidate_term: int,
    voter_term: int,
) -> tuple[bool, str]:
    """Determine whether to grant a vote to a candidate.

    Rules (Raft §5.2):
    1. Reply false if candidate_term < voter_term (stale candidate).
    2. If voted_for is None or candidate_id, grant vote IF the candidate's
       log is at least as up-to-date as the voter's log.
    3. Otherwise, deny.

    "Up-to-date" means: the candidate's last log entry has a higher term,
    or same term with equal or greater index.
    """
    if candidate_term < voter_term:
        return False, f"candidate term {candidate_term} < voter term {voter_term}"

    if voted_for is not None and voted_for != candidate_id:
        return False, f"already voted for node {voted_for} in term {voter_term}"

    # Log up-to-date check
    log_ok = (
        candidate_last_term > voter_last_term or
        (candidate_last_term == voter_last_term and
         candidate_last_index >= voter_last_index)
    )

    if not log_ok:
        return False, (
            f"candidate log (idx={candidate_last_index}, term={candidate_last_term}) "
            f"behind voter log (idx={voter_last_index}, term={voter_last_term})"
        )

    return True, "vote granted"
