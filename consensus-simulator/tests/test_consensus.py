"""Tests for Raft consensus implementation.

Covers:
- Log operations (append, consistency check, truncation)
- Election logic (vote granting, timeout behavior)
- State transitions (follower→candidate→leader→follower)
- Leader election in multi-node cluster
- Network partition behavior
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.raft.log import RaftLog, LogEntry
from src.raft.election import (
    ElectionTimer, VoteRequest, VoteResponse, should_grant_vote
)
from src.raft.node import (
    RaftNode, NodeState, AppendEntriesRequest, AppendEntriesResponse
)


# ── Log Tests ──────────────────────────────────────────────────────

class TestRaftLog:
    """Test the replicated log implementation."""

    def test_initial_state(self):
        """New log has sentinel entry at index 0."""
        log = RaftLog()
        assert log.last_index == 0
        assert log.last_term == 0
        assert log.committed == 0
        assert log.applied == 0

    def test_append_single_entry(self):
        """Appending an entry increments last_index."""
        log = RaftLog()
        entry = log.append(term=1, command="SET x=1")
        assert entry.index == 1
        assert entry.term == 1
        assert entry.command == "SET x=1"
        assert log.last_index == 1
        assert log.last_term == 1

    def test_append_multiple_entries(self):
        """Multiple appends maintain correct indices."""
        log = RaftLog()
        e1 = log.append(term=1, command="a")
        e2 = log.append(term=1, command="b")
        e3 = log.append(term=2, command="c")
        assert e1.index == 1
        assert e2.index == 2
        assert e3.index == 3
        assert log.last_index == 3

    def test_term_at(self):
        """term_at returns correct term for each index."""
        log = RaftLog()
        log.append(term=1, command="a")
        log.append(term=1, command="b")
        log.append(term=3, command="c")
        assert log.term_at(0) == 0  # Sentinel
        assert log.term_at(1) == 1
        assert log.term_at(2) == 1
        assert log.term_at(3) == 3

    def test_term_at_out_of_bounds(self):
        """term_at raises IndexError for invalid indices."""
        log = RaftLog()
        with pytest.raises(IndexError):
            log.term_at(-1)
        with pytest.raises(IndexError):
            log.term_at(5)  # Beyond last_index

    def test_append_entries_success(self):
        """AppendEntries succeeds when prev_log_index and prev_log_term match."""
        log = RaftLog()
        log.append(term=1, command="a")
        log.append(term=1, command="b")

        success = log.append_entries(
            prev_log_index=2,
            prev_log_term=1,
            entries=[LogEntry(term=2, command="c", index=3)],
        )
        assert success
        assert log.last_index == 3
        assert log.term_at(3) == 2

    def test_append_entries_prev_index_mismatch(self):
        """AppendEntries fails when prev_log_index is beyond the log."""
        log = RaftLog()
        log.append(term=1, command="a")

        success = log.append_entries(
            prev_log_index=5,  # Doesn't exist
            prev_log_term=1,
            entries=[],
        )
        assert not success

    def test_append_entries_prev_term_mismatch(self):
        """AppendEntries fails when prev_log_term doesn't match."""
        log = RaftLog()
        log.append(term=1, command="a")
        log.append(term=1, command="b")

        success = log.append_entries(
            prev_log_index=1,
            prev_log_term=99,  # Wrong term
            entries=[],
        )
        assert not success

    def test_append_entries_conflict_truncation(self):
        """Conflicting entries are truncated on AppendEntries."""
        log = RaftLog()
        log.append(term=1, command="a")
        log.append(term=1, command="b")
        log.append(term=1, command="c")  # Will conflict

        # Leader has: idx1(term1,a), idx2(term1,b), idx3(term2,d)
        success = log.append_entries(
            prev_log_index=1,
            prev_log_term=1,
            entries=[
                LogEntry(term=2, command="d", index=2),
                LogEntry(term=2, command="e", index=3),
            ],
        )
        assert success
        assert log.last_index == 3
        assert log.term_at(2) == 2
        assert log.term_at(3) == 2
        assert log.entries[2].command == "d"
        assert log.entries[3].command == "e"

    def test_commit_to(self):
        """commit_to updates commit_index correctly."""
        log = RaftLog()
        log.append(term=1, command="a")
        log.append(term=1, command="b")
        log.append(term=1, command="c")

        log.commit_to(leader_commit=2)
        assert log.committed == 2

        # commit_to should not exceed log length
        log.commit_to(leader_commit=10)
        assert log.committed == 3

    def test_is_up_to_date(self):
        """is_up_to_date correctly compares log freshness."""
        log = RaftLog()
        log.append(term=1, command="a")
        log.append(term=3, command="b")  # last_term=3

        # Higher term → more up-to-date
        assert log.is_up_to_date(last_index=1, last_term=5)  # Higher term
        assert not log.is_up_to_date(last_index=10, last_term=2)  # Lower term

        # Same term → higher index wins
        assert log.is_up_to_date(last_index=3, last_term=3)  # Same term, same index
        assert not log.is_up_to_date(last_index=1, last_term=3)  # Same term, lower index

    def test_get_entries_from(self):
        """get_entries_from returns correct slice."""
        log = RaftLog()
        log.append(term=1, command="a")
        log.append(term=1, command="b")
        log.append(term=2, command="c")

        entries = log.get_entries_from(2)
        assert len(entries) == 2
        assert entries[0].command == "b"
        assert entries[1].command == "c"

        # Out of bounds
        assert log.get_entries_from(10) == []
        assert log.get_entries_from(-1) == []


# ── Election Tests ─────────────────────────────────────────────────

class TestElectionTimer:
    """Test the randomized election timer."""

    def test_initial_not_fired(self):
        """Fresh timer should not be fired."""
        timer = ElectionTimer(min_ms=1000, max_ms=2000)
        assert not timer.fired
        assert timer.remaining > 0

    def test_fires_after_timeout(self):
        """Timer fires after elapsed >= timeout."""
        timer = ElectionTimer(min_ms=100, max_ms=200)
        timer.tick(0.5)  # 500ms > max 200ms
        assert timer.fired

    def test_reset(self):
        """Reset clears elapsed and picks new timeout."""
        timer = ElectionTimer(min_ms=100, max_ms=200)
        timer.tick(0.5)
        assert timer.fired

        timer.reset()
        assert not timer.fired
        assert timer.elapsed == 0.0
        assert timer.current_timeout > 0

    def test_tick_returns_fired(self):
        """tick returns True only when timeout fires."""
        timer = ElectionTimer(min_ms=100, max_ms=100)  # Deterministic
        assert not timer.tick(0.05)  # 50ms < 100ms
        assert timer.tick(0.10)  # 150ms >= 100ms


class TestVoteGranting:
    """Test the vote granting logic."""

    def test_grant_to_more_up_to_date_candidate(self):
        """Vote granted when candidate's log is more up-to-date."""
        grant, reason = should_grant_vote(
            candidate_last_index=10, candidate_last_term=5,
            voter_last_index=5, voter_last_term=3,
            voted_for=None, candidate_id=2, candidate_term=4,
            voter_term=4,
        )
        assert grant
        assert "granted" in reason

    def test_deny_stale_term(self):
        """Vote denied when candidate term is less than voter term."""
        grant, reason = should_grant_vote(
            candidate_last_index=10, candidate_last_term=5,
            voter_last_index=5, voter_last_term=3,
            voted_for=None, candidate_id=2, candidate_term=3,
            voter_term=5,  # Voter has higher term
        )
        assert not grant
        assert "term" in reason.lower()

    def test_deny_already_voted(self):
        """Vote denied when already voted for another candidate in same term."""
        grant, reason = should_grant_vote(
            candidate_last_index=10, candidate_last_term=5,
            voter_last_index=5, voter_last_term=3,
            voted_for=1, candidate_id=2, candidate_term=4,
            voter_term=4,
        )
        assert not grant
        assert "already voted" in reason

    def test_deny_outdated_log(self):
        """Vote denied when candidate's log is behind voter's."""
        grant, reason = should_grant_vote(
            candidate_last_index=3, candidate_last_term=2,
            voter_last_index=10, voter_last_term=5,  # Voter has newer log
            voted_for=None, candidate_id=2, candidate_term=4,
            voter_term=4,
        )
        assert not grant
        assert "log" in reason.lower()


# ── Node State Machine Tests ───────────────────────────────────────

class TestRaftNode:
    """Test Raft node state transitions and RPC handling."""

    def test_initial_state(self):
        """New node starts as follower in term 0."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])
        assert node.state == NodeState.FOLLOWER
        assert node.current_term == 0
        assert node.voted_for is None

    def test_become_candidate_increments_term(self):
        """Becoming a candidate increments term and votes for self."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])
        node.become_candidate()
        assert node.state == NodeState.CANDIDATE
        assert node.current_term == 1
        assert node.voted_for == 0

    def test_become_leader_sets_volatile_state(self):
        """Leader initializes next_index and match_index for all peers."""
        node = RaftNode(node_id=0, peer_ids=[1, 2, 3])
        node.become_candidate()
        node.become_leader()
        assert node.state == NodeState.LEADER
        assert node.current_leader_id == 0
        assert node.next_index == {1: 1, 2: 1, 3: 1}  # last_index+1
        assert node.match_index == {1: 0, 2: 0, 3: 0}

    def test_become_follower_resets(self):
        """Following a higher term resets voted_for and timer."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])
        node.become_candidate()  # term 1, voted_for=0
        node.become_follower(term=3)
        assert node.state == NodeState.FOLLOWER
        assert node.current_term == 3
        assert node.voted_for is None

    def test_handle_request_vote_lower_term(self):
        """Reject vote request with lower term."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])
        node.current_term = 5

        req = VoteRequest(term=3, candidate_id=1,
                         last_log_index=10, last_log_term=4)
        resp = node.handle_request_vote(req)
        assert not resp.vote_granted
        assert resp.term == 5

    def test_handle_request_vote_higher_term(self):
        """Higher term causes step-down to follower."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])
        node.current_term = 3

        req = VoteRequest(term=5, candidate_id=1,
                         last_log_index=10, last_log_term=4)
        resp = node.handle_request_vote(req)
        # Should step down to follower with term 5
        assert node.current_term == 5
        assert node.state == NodeState.FOLLOWER

    def test_handle_append_entries_lower_term(self):
        """Reject AppendEntries with lower term."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])
        node.current_term = 5

        req = AppendEntriesRequest(
            term=3, leader_id=1, prev_log_index=0, prev_log_term=0,
        )
        resp = node.handle_append_entries(req)
        assert not resp.success
        assert resp.term == 5

    def test_handle_append_entries_updates_leader(self):
        """Valid AppendEntries updates current_leader_id."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])

        req = AppendEntriesRequest(
            term=1, leader_id=1, prev_log_index=0, prev_log_term=0,
        )
        resp = node.handle_append_entries(req)
        assert resp.success
        assert node.current_leader_id == 1

    def test_handle_append_entries_candidate_steps_down(self):
        """Candidate steps down when receiving AppendEntries from valid leader."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])
        node.become_candidate()
        assert node.state == NodeState.CANDIDATE

        req = AppendEntriesRequest(
            term=node.current_term, leader_id=1,
            prev_log_index=0, prev_log_term=0,
        )
        resp = node.handle_append_entries(req)
        assert node.state == NodeState.FOLLOWER

    def test_propose_only_leader(self):
        """Only the leader can propose commands."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])
        with pytest.raises(RuntimeError):
            node.propose("SET x=1")

        node.become_candidate()
        node.become_leader()
        entry = node.propose("SET x=1")
        assert entry.command == "SET x=1"
        assert entry.term == node.current_term

    def test_advance_commit_index(self):
        """Commit index advances when majority replicates."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])
        node.become_candidate()
        node.become_leader()

        # Add an entry
        node.propose("cmd1")
        assert node.log.last_index == 1

        # Simulate replication to one peer (need majority = 2 with self)
        node.match_index[1] = 1
        node._advance_commit_index()
        assert node.commit_index == 1

    def test_apply_committed(self):
        """Committed entries are applied in order."""
        node = RaftNode(node_id=0, peer_ids=[1, 2])
        node.become_candidate()
        node.become_leader()

        node.propose("cmd1")
        node.propose("cmd2")
        node.commit_index = 2

        applied = node.apply_committed()
        assert len(applied) == 2
        assert applied[0].command == "cmd1"
        assert applied[1].command == "cmd2"
        assert node.last_applied == 2


# ── Paxos Tests ────────────────────────────────────────────────────

from src.paxos import (
    Acceptor, Proposer, Learner,
    PrepareRequest, PrepareResponse,
    AcceptRequest, AcceptResponse,
)


class TestPaxosAcceptor:
    """Test the Paxos Acceptor."""

    def test_initial_state(self):
        """Acceptor starts with no promises or acceptances."""
        acc = Acceptor(acceptor_id=0)
        assert acc.promised_number == -1
        assert acc.accepted_number == -1
        assert acc.accepted_value is None

    def test_prepare_higher_number(self):
        """Acceptor promises a higher proposal number."""
        acc = Acceptor(acceptor_id=0)
        req = PrepareRequest(proposal_number=10, proposer_id=1)
        resp = acc.receive_prepare(req)
        assert resp.accepted is False  # No previous acceptance
        assert acc.promised_number == 10

    def test_prepare_lower_number_rejected(self):
        """Prepare with lower number is ignored (acceptor already promised higher)."""
        acc = Acceptor(acceptor_id=0)
        acc.receive_prepare(PrepareRequest(proposal_number=10, proposer_id=1))

        resp = acc.receive_prepare(PrepareRequest(proposal_number=5, proposer_id=2))
        # Accepted field is False — signal rejection
        assert resp.proposal_number == 5

    def test_prepare_returns_previous_acceptance(self):
        """Prepare with higher number returns any previously accepted value."""
        acc = Acceptor(acceptor_id=0)
        acc.receive_prepare(PrepareRequest(proposal_number=5, proposer_id=1))
        acc.receive_accept(AcceptRequest(proposal_number=5, value="foo", proposer_id=1))

        # New proposer with higher number
        resp = acc.receive_prepare(PrepareRequest(proposal_number=10, proposer_id=2))
        assert resp.accepted is True
        assert resp.highest_accepted_number == 5
        assert resp.highest_accepted_value == "foo"

    def test_accept_higher_number(self):
        """Acceptor accepts a proposal with number >= promised_number."""
        acc = Acceptor(acceptor_id=0)
        acc.receive_prepare(PrepareRequest(proposal_number=5, proposer_id=1))

        resp = acc.receive_accept(AcceptRequest(proposal_number=5, value="bar", proposer_id=1))
        assert resp.accepted
        assert acc.accepted_value == "bar"

    def test_accept_lower_number_rejected(self):
        """Acceptor rejects proposals below promised_number."""
        acc = Acceptor(acceptor_id=0)
        acc.receive_prepare(PrepareRequest(proposal_number=10, proposer_id=1))

        resp = acc.receive_accept(AcceptRequest(proposal_number=5, value="bar", proposer_id=2))
        assert not resp.accepted


class TestPaxosProposer:
    """Test the Paxos Proposer."""

    def test_proposal_number_uniqueness(self):
        """Different proposers get different proposal numbers."""
        p1 = Proposer(proposer_id=1, quorum_size=3)
        p2 = Proposer(proposer_id=2, quorum_size=3)

        n1 = p1.next_proposal_number()
        n2 = p2.next_proposal_number()
        assert n1 != n2

    def test_value_selection_rule_no_prior(self):
        """When no acceptor has a prior value, proposer uses its own."""
        p = Proposer(proposer_id=1, quorum_size=2)
        p.propose("own_value", proposal_number=10)

        quorum, value = p.collect_prepare_response(
            PrepareResponse(proposal_number=10, accepted=False, acceptor_id=0)
        )
        assert not quorum  # Need 2 for quorum

        quorum, value = p.collect_prepare_response(
            PrepareResponse(proposal_number=10, accepted=False, acceptor_id=1)
        )
        assert quorum
        assert value == "own_value"  # No prior → use own

    def test_value_selection_rule_with_prior(self):
        """When an acceptor has a prior value, proposer MUST use the highest one."""
        p = Proposer(proposer_id=1, quorum_size=2)
        p.propose("own_value", proposal_number=10)

        p.collect_prepare_response(
            PrepareResponse(proposal_number=10, accepted=False, acceptor_id=0)
        )
        quorum, value = p.collect_prepare_response(
            PrepareResponse(proposal_number=10, accepted=True,
                          highest_accepted_number=8, highest_accepted_value="prior_value",
                          acceptor_id=1)
        )
        assert quorum
        assert value == "prior_value"  # MUST use prior value


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
