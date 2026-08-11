"""Paxos (Single-Decree) — the original consensus algorithm.

Lamport's Paxos is the intellectual ancestor of all consensus algorithms.
This implements the single-decree Synod protocol from "Paxos Made Simple."

Key insight: Paxos separates the consensus problem into three roles —
Proposer (proposes values), Acceptor (accepts proposals), Learner (learns result).

The algorithm guarantees:
- Safety: Only a single value is chosen, and only if proposed.
- Liveness under partial synchrony: With a distinguished proposer
  (eventual leader), a value is eventually chosen.

┌──────────┐      ┌──────────┐      ┌──────────┐
│ Proposer │ ───→ │ Acceptor │ ───→ │ Learner  │
│ (client) │ ←─── │ (quorum) │ ←─── │ (output) │
└──────────┘      └──────────┘      └──────────┘

Phase 1 (Prepare):
  Proposer → Acceptors: Prepare(n)  "I propose round n"
  Acceptor → Proposer: Promise(n, v_highest_below_n)

Phase 2 (Accept):
  Proposer → Acceptors: Accept(n, v)  "Accept value v in round n"
  Acceptor → Proposer: Accepted(n, v)
  Proposer → Learners: Chosen(v)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


@dataclass
class PrepareRequest:
    """Phase 1a: Proposer → Acceptor"""
    proposal_number: int  # Unique, monotonically increasing
    proposer_id: int


@dataclass
class PrepareResponse:
    """Phase 1b: Acceptor → Proposer"""
    proposal_number: int
    accepted: bool = False
    highest_accepted_number: int = -1   # Highest-numbered proposal accepted
    highest_accepted_value: Any = None   # Value of that proposal
    acceptor_id: int = -1


@dataclass
class AcceptRequest:
    """Phase 2a: Proposer → Acceptor"""
    proposal_number: int
    value: Any
    proposer_id: int


@dataclass
class AcceptResponse:
    """Phase 2b: Acceptor → Proposer (and Proposer → Learner)"""
    proposal_number: int
    accepted: bool
    acceptor_id: int = -1


class AcceptorState(Enum):
    IDLE = auto()
    PROMISED = auto()  # Has promised not to accept proposals < n
    ACCEPTED = auto()  # Has accepted a proposal


@dataclass
class Acceptor:
    """Paxos Acceptor — the fault-tolerant memory of the protocol.

    Invariants:
    1. An acceptor only accepts the first proposal it receives (for a given
       proposal number it hasn't already promised to ignore).
    2. Once an acceptor promises to ignore proposals below n, it must not
       accept any proposal with number < n.
    3. promised_number and accepted_number are monotonically increasing.
    """

    acceptor_id: int
    promised_number: int = -1          # Highest proposal number promised
    accepted_number: int = -1          # Highest proposal number accepted
    accepted_value: Any = None         # Value of the accepted proposal

    def receive_prepare(self, req: PrepareRequest) -> PrepareResponse:
        """Handle a Prepare request (Phase 1a).

        If this is the highest-numbered prepare seen, promise not to accept
        any proposal with a lower number, and return any previously accepted
        proposal.
        """
        if req.proposal_number > self.promised_number:
            self.promised_number = req.proposal_number
            return PrepareResponse(
                proposal_number=req.proposal_number,
                accepted=(self.accepted_number >= 0),
                highest_accepted_number=self.accepted_number,
                highest_accepted_value=self.accepted_value,
                acceptor_id=self.acceptor_id,
            )
        else:
            # Already promised a higher number — reject
            return PrepareResponse(
                proposal_number=req.proposal_number,
                accepted=False,
                acceptor_id=self.acceptor_id,
            )

    def receive_accept(self, req: AcceptRequest) -> AcceptResponse:
        """Handle an Accept request (Phase 2a).

        Accept the proposal only if we haven't promised to ignore it
        (i.e., req.proposal_number >= promised_number).
        """
        if req.proposal_number >= self.promised_number:
            self.promised_number = req.proposal_number
            self.accepted_number = req.proposal_number
            self.accepted_value = req.value
            return AcceptResponse(
                proposal_number=req.proposal_number,
                accepted=True,
                acceptor_id=self.acceptor_id,
            )
        else:
            return AcceptResponse(
                proposal_number=req.proposal_number,
                accepted=False,
                acceptor_id=self.acceptor_id,
            )


@dataclass
class Proposer:
    """Paxos Proposer — drives the consensus protocol.

    Picks a unique proposal number (typically <round, server_id> to ensure
    uniqueness across proposers) and executes the two-phase protocol.

    Value selection rule: In Phase 2, if any acceptor returned a previously
    accepted value in Phase 1, the proposer MUST use the value with the
    highest accepted proposal number. Otherwise, it can propose its own value.
    """

    proposer_id: int
    base_proposal_number: int = 0
    current_value: Any = None
    quorum_size: int = 0

    # Per-proposal state
    round_number: int = 0
    prepare_responses: dict[int, PrepareResponse] = field(default_factory=dict)
    accept_responses: dict[int, AcceptResponse] = field(default_factory=dict)

    def next_proposal_number(self) -> int:
        """Generate the next unique proposal number."""
        self.round_number += 1
        return self.round_number * 1000 + self.proposer_id

    def propose(self, value: Any, proposal_number: int | None = None):
        """Start a new proposal round with the given value.

        If proposal_number is not provided, a new unique number is generated.
        """
        if proposal_number is None:
            proposal_number = self.next_proposal_number()

        self.current_value = value
        self.prepare_responses.clear()
        self.accept_responses.clear()
        return PrepareRequest(
            proposal_number=proposal_number,
            proposer_id=self.proposer_id,
        )

    def collect_prepare_response(self, resp: PrepareResponse) -> tuple[bool, Any | None]:
        """Collect a Phase 1 response.

        Returns (quorum_reached, value_to_propose).
        - quorum_reached: True if majority of acceptors have responded.
        - value_to_propose: The value that MUST be used in Phase 2 (None if
          no acceptor has accepted a previous value — use own).
        """
        self.prepare_responses[resp.acceptor_id] = resp

        if len(self.prepare_responses) >= self.quorum_size:
            # Value selection rule
            best_number = -1
            best_value = None
            for r in self.prepare_responses.values():
                if r.accepted and r.highest_accepted_number > best_number:
                    best_number = r.highest_accepted_number
                    best_value = r.highest_accepted_value

            # If any acceptor had a value, must use the highest one
            if best_value is not None:
                return True, best_value
            return True, self.current_value

        return False, None

    def collect_accept_response(self, resp: AcceptResponse) -> bool:
        """Collect a Phase 2 response.

        Returns True if a quorum of acceptors has accepted the proposal.
        """
        self.accept_responses[resp.acceptor_id] = resp
        accepted_count = sum(1 for r in self.accept_responses.values() if r.accepted)
        return accepted_count >= self.quorum_size


@dataclass
class Learner:
    """Paxos Learner — observes the protocol and learns the chosen value.

    A value is chosen when a quorum of acceptors has accepted it.
    """

    chosen_value: Any = None
    chosen_number: int = -1
    accept_count: dict[int, int] = field(default_factory=dict)  # value hash → count

    def receive_accepted(self, proposal_number: int, value: Any) -> tuple[bool, Any]:
        """Receive notification that a proposal was accepted.

        Returns (chosen, value) — (True, value) when a value is chosen.
        """
        value_hash = hash(value) if value is not None else 0
        self.accept_count[value_hash] = self.accept_count.get(value_hash, 0) + 1
        return False, None  # Quorum check done externally (needs total acceptor count)

    def is_chosen(self, quorum_size: int) -> bool:
        """Check if any value has been chosen by a quorum."""
        for count in self.accept_count.values():
            if count >= quorum_size:
                return True
        return False
