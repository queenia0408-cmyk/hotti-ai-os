"""Raft consensus node — the core state machine.

Each Raft node is always in one of three states:
- FOLLOWER: Passive, responds to RPCs from leader/candidates
- CANDIDATE: Active, requesting votes to become leader
- LEADER: Active, handling client requests and replicating log

State transitions:
    Follower ──(timeout)──→ Candidate ──(majority votes)──→ Leader
         ↑                      │                              │
         └──(discover higher term)─────────────────────────────┘
"""

import asyncio
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable

from .log import RaftLog, LogEntry
from .election import (
    ElectionTimer, VoteRequest, VoteResponse, should_grant_vote
)


class NodeState(Enum):
    FOLLOWER = auto()
    CANDIDATE = auto()
    LEADER = auto()


@dataclass
class AppendEntriesRequest:
    """Arguments for AppendEntries RPC."""
    term: int              # Leader's term
    leader_id: int         # So follower can redirect clients
    prev_log_index: int    # Index of log entry immediately preceding
    prev_log_term: int     # Term of prev_log_index entry
    entries: list[LogEntry] = field(default_factory=list)
    leader_commit: int = 0  # Leader's commit index


@dataclass
class AppendEntriesResponse:
    """Results from AppendEntries RPC."""
    term: int       # Current term, for leader to update itself
    success: bool   # True if follower contained entry matching prev


@dataclass
class RaftNode:
    """A single Raft consensus node.

    Persistent state (must survive crashes):
        current_term: Latest term server has seen (initialized to 0).
        voted_for: CandidateId that received vote in current term (or None).
        log: The replicated log.

    Volatile state:
        state: FOLLOWER | CANDIDATE | LEADER.
        commit_index: Index of highest log entry known to be committed.
        last_applied: Index of highest log entry applied to state machine.

    Leader-only volatile state (reinitialized after election):
        next_index: For each server, index of the next log entry to send.
        match_index: For each server, index of highest log entry known to be
                     replicated on that server.
    """

    node_id: int
    peer_ids: list[int] = field(default_factory=list)
    current_term: int = 0
    voted_for: int | None = None
    log: RaftLog = field(default_factory=RaftLog)

    # Volatile
    state: NodeState = NodeState.FOLLOWER
    commit_index: int = 0
    last_applied: int = 0

    # Leader state (reinitialized after election)
    next_index: dict[int, int] = field(default_factory=dict)
    match_index: dict[int, int] = field(default_factory=dict)

    # Leadership identification
    current_leader_id: int | None = None

    # Timing
    timer: ElectionTimer = field(default_factory=ElectionTimer)

    # Communication — callbacks set by the network layer
    send_rpc: Callable[["RaftNode", str, Any], asyncio.Future] | None = None
    state_change_callback: Callable[["RaftNode", NodeState, NodeState], None] | None = None

    # Event for simulation control
    running: bool = True

    def __post_init__(self):
        if not self.next_index:
            self.next_index = {p: 1 for p in self.peer_ids}
        if not self.match_index:
            self.match_index = {p: 0 for p in self.peer_ids}

    # ── State Transitions ──────────────────────────────────────────

    def become_follower(self, term: int):
        """Transition to follower state.

        Triggered by:
        - Discovering a higher term from any RPC
        - Granting a vote to a candidate
        - Election timeout in candidate without majority
        """
        old_state = self.state
        self.state = NodeState.FOLLOWER
        if term > self.current_term:
            self.current_term = term
            self.voted_for = None
        self.timer.reset()
        if old_state != NodeState.FOLLOWER and self.state_change_callback:
            self.state_change_callback(self, old_state, NodeState.FOLLOWER)

    def become_candidate(self):
        """Transition to candidate state and start an election.

        Triggered by election timeout in follower/candidate state.
        """
        old_state = self.state
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id  # Vote for self
        self.timer.reset()
        if self.state_change_callback:
            self.state_change_callback(self, old_state, NodeState.CANDIDATE)

    def become_leader(self):
        """Transition to leader state after winning an election.

        Triggered by receiving majority of votes as candidate.
        Immediately sends heartbeat (empty AppendEntries) to all peers
        to assert leadership and prevent new elections.
        """
        old_state = self.state
        self.state = NodeState.LEADER
        self.current_leader_id = self.node_id

        # Initialize leader volatile state
        last_index = self.log.last_index
        self.next_index = {p: last_index + 1 for p in self.peer_ids}
        self.match_index = {p: 0 for p in self.peer_ids}

        if self.state_change_callback:
            self.state_change_callback(self, old_state, NodeState.LEADER)

    # ── RPC Handlers ───────────────────────────────────────────────

    def handle_request_vote(self, req: VoteRequest) -> VoteResponse:
        """Handle a RequestVote RPC from a candidate.

        Rules (Raft §5.2):
        1. Reply false if term < currentTerm
        2. If votedFor is null or candidateId, AND candidate's log is at
           least as up-to-date as receiver's log, grant vote.
        """
        if req.term < self.current_term:
            return VoteResponse(term=self.current_term, vote_granted=False)

        # Discovered higher term — step down
        if req.term > self.current_term:
            self.become_follower(req.term)

        grant, reason = should_grant_vote(
            candidate_last_index=req.last_log_index,
            candidate_last_term=req.last_log_term,
            voter_last_index=self.log.last_index,
            voter_last_term=self.log.last_term,
            voted_for=self.voted_for,
            candidate_id=req.candidate_id,
            candidate_term=req.term,
            voter_term=self.current_term,
        )

        if grant:
            self.voted_for = req.candidate_id
            self.timer.reset()  # Reset election timer on granting vote

        return VoteResponse(term=self.current_term, vote_granted=grant)

    def handle_append_entries(self, req: AppendEntriesRequest) -> AppendEntriesResponse:
        """Handle an AppendEntries RPC from the leader.

        Rules (Raft §5.3):
        1. Reply false if term < currentTerm.
        2. Reply false if log doesn't contain entry at prevLogIndex
           whose term matches prevLogTerm.
        3. If existing entry conflicts with new one, delete it and
           all that follow.
        4. Append any new entries not already in the log.
        5. If leaderCommit > commitIndex, set commitIndex = min(leaderCommit,
           index of last new entry).
        """
        if req.term < self.current_term:
            return AppendEntriesResponse(term=self.current_term, success=False)

        # Valid leader heartbeat/append — reset election timer
        self.timer.reset()

        if req.term > self.current_term:
            self.become_follower(req.term)

        # Update leader tracking
        self.current_leader_id = req.leader_id
        if self.state == NodeState.CANDIDATE:
            self.become_follower(req.term)

        # Log consistency check and append
        success = self.log.append_entries(
            prev_log_index=req.prev_log_index,
            prev_log_term=req.prev_log_term,
            entries=req.entries,
        )

        if success:
            self.log.commit_to(req.leader_commit)

        return AppendEntriesResponse(term=self.current_term, success=success)

    # ── Leader Operations ──────────────────────────────────────────

    def propose(self, command: Any) -> LogEntry:
        """Propose a new command to the state machine.

        Only valid when this node is the leader. The leader appends the
        command to its own log and will replicate to followers.
        """
        if self.state != NodeState.LEADER:
            raise RuntimeError(f"Node {self.node_id} is not the leader")
        return self.log.append(term=self.current_term, command=command)

    def prepare_append_entries(self, peer_id: int) -> AppendEntriesRequest | None:
        """Prepare an AppendEntries RPC for a specific peer.

        Returns None if no entries need to be sent (heartbeat only).
        """
        prev_log_index = self.next_index[peer_id] - 1
        prev_log_term = self.log.term_at(prev_log_index) if prev_log_index >= 0 else 0

        entries_to_send = self.log.get_entries_from(self.next_index[peer_id])

        return AppendEntriesRequest(
            term=self.current_term,
            leader_id=self.node_id,
            prev_log_index=prev_log_index,
            prev_log_term=prev_log_term,
            entries=entries_to_send,
            leader_commit=self.commit_index,
        )

    def process_append_response(self, peer_id: int, resp: AppendEntriesResponse):
        """Process a response to AppendEntries RPC.

        On success: Update next_index and match_index for the peer.
        On failure: Decrement next_index and retry (eventually consistent).

        Check if we can advance commit_index.
        """
        if resp.term > self.current_term:
            self.become_follower(resp.term)
            return

        if self.state != NodeState.LEADER:
            return

        if resp.success:
            # Update tracking
            new_match = max(
                self.match_index.get(peer_id, 0),
                self.next_index[peer_id] + len(
                    self.log.get_entries_from(self.next_index[peer_id])
                ) - 1
            )
            self.match_index[peer_id] = new_match
            self.next_index[peer_id] = new_match + 1

            # Try to advance commit_index
            self._advance_commit_index()
        else:
            # Log inconsistency — decrement and retry
            self.next_index[peer_id] = max(1, self.next_index[peer_id] - 1)

    def _advance_commit_index(self):
        """Advance commit_index if there exists an N > commit_index such that
        a majority of match_index[i] ≥ N and log[N].term == current_term.

        This is the leader's commit rule (Raft §5.4).
        """
        N = self.log.last_index
        while N > self.commit_index:
            # Count nodes that have replicated up to N
            count = 1  # Leader itself
            for peer_id in self.peer_ids:
                if self.match_index.get(peer_id, 0) >= N:
                    count += 1

            majority = (len(self.peer_ids) + 1 + 1) // 2  # peers + self
            if count >= majority and self.log.term_at(N) == self.current_term:
                self.commit_index = N
                break
            N -= 1

    # ── State Machine Application ──────────────────────────────────

    def apply_committed(self) -> list[LogEntry]:
        """Apply committed entries to the state machine.

        Returns the list of newly applied entries.
        """
        applied = []
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log.entries[self.last_applied]
            applied.append(entry)
        return applied

    # ── Simulation Control ─────────────────────────────────────────

    def tick(self, dt: float):
        """Advance the node's internal clock by dt seconds."""
        self.timer.tick(dt)

    def stop(self):
        """Simulate a crash-stop failure."""
        self.running = False

    @property
    def is_leader(self) -> bool:
        return self.state == NodeState.LEADER

    def __repr__(self) -> str:
        return (
            f"RaftNode(id={self.node_id}, state={self.state.name}, "
            f"term={self.current_term}, log_len={len(self.log)}, "
            f"committed={self.commit_index}, applied={self.last_applied})"
        )
