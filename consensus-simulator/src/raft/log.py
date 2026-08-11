"""Raft replicated log — the heart of the consensus mechanism.

Log Matching Property: if two entries in different logs have the same index
and term, then they store the same command, and the logs are identical up to
that index.

Leader Append-Only: a leader never overwrites or deletes entries in its own
log — it only appends new entries.

Log entries flow: leader → followers via AppendEntries RPC.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogEntry:
    """A single entry in the Raft log.

    Attributes:
        term: The term when this entry was received by the leader.
        command: The state machine command to execute.
        index: 1-indexed position in the log.
    """
    term: int
    command: Any
    index: int = 0  # Set when appended

    def __repr__(self) -> str:
        return f"LogEntry(idx={self.index}, term={self.term}, cmd={self.command!r})"


@dataclass
class RaftLog:
    """The replicated log for a Raft node.

    Invariants:
    - committed ≤ applied ≤ len(entries)
    - For any i where entries[i].term == entries[j].term with i < j,
      all entries between i and j have the same term (term continuity
      within leader's append batches).

    Attributes:
        entries: The ordered list of log entries (index 0 is a sentinel).
        committed: Index of highest entry known to be committed.
        applied: Index of highest entry applied to state machine.
        last_included_index: For snapshot/compaction support.
        last_included_term: Term of last included entry.
    """
    entries: list[LogEntry] = field(default_factory=list)
    committed: int = 0
    applied: int = 0
    last_included_index: int = 0
    last_included_term: int = 0

    def __post_init__(self):
        if not self.entries:
            # Sentinel entry at index 0 (term 0, no command)
            self.entries.append(LogEntry(term=0, command=None, index=0))

    @property
    def last_index(self) -> int:
        """Index of the last entry in the log."""
        return len(self.entries) - 1

    @property
    def last_term(self) -> int:
        """Term of the last entry in the log."""
        return self.entries[-1].term

    def term_at(self, index: int) -> int:
        """Get the term of the entry at the given index.

        Returns last_included_term if index == last_included_index
        (for snapshot support). Raises IndexError if out of bounds.
        """
        if index < 0 or index > self.last_index:
            raise IndexError(f"Log index {index} out of range [0, {self.last_index}]")
        if index == self.last_included_index and self.last_included_index > 0:
            return self.last_included_term
        return self.entries[index].term

    def append(self, term: int, command: Any) -> LogEntry:
        """Append a new entry to the log.

        Returns the created LogEntry.
        """
        entry = LogEntry(term=term, command=command, index=len(self.entries))
        self.entries.append(entry)
        return entry

    def append_entries(self, prev_log_index: int, prev_log_term: int,
                       entries: list[LogEntry]) -> bool:
        """Handle AppendEntries RPC from leader.

        Args:
            prev_log_index: Index of log entry immediately preceding new ones.
            prev_log_term: Term of prev_log_index entry.
            entries: New entries to append (empty for heartbeat).

        Returns:
            True if the append succeeded (log consistency check passed).
        """
        # Reply false if log doesn't contain entry at prev_log_index
        # whose term matches prev_log_term.
        if prev_log_index > self.last_index:
            return False
        if prev_log_index >= 0 and self.term_at(prev_log_index) != prev_log_term:
            return False

        # If existing entries conflict with new ones, delete all existing
        # entries starting with the first conflicting entry.
        for i, new_entry in enumerate(entries):
            idx = prev_log_index + 1 + i
            if idx <= self.last_index:
                if self.term_at(idx) != new_entry.term:
                    # Conflict found — truncate from this point
                    self.entries = self.entries[:idx]
            else:
                break

        # Append any new entries not already in the log.
        for i, new_entry in enumerate(entries):
            idx = prev_log_index + 1 + i
            if idx > self.last_index:
                new_entry.index = idx
                self.entries.append(new_entry)

        return True

    def commit_to(self, leader_commit: int):
        """Update commit index based on leader's commit index.

        If leaderCommit > commitIndex, set commitIndex =
        min(leaderCommit, index of last new entry).
        """
        if leader_commit > self.committed:
            self.committed = min(leader_commit, self.last_index)

    def get_entries_from(self, start_index: int) -> list[LogEntry]:
        """Get all entries starting from start_index (inclusive)."""
        if start_index < 0 or start_index > self.last_index:
            return []
        return self.entries[start_index:]

    def is_up_to_date(self, last_index: int, last_term: int) -> bool:
        """Check if this log is at least as up-to-date as the given index/term.

        Used during leader election: a voter only votes for a candidate
        whose log is at least as up-to-date as its own.
        """
        if last_term != self.last_term:
            return last_term > self.last_term
        return last_index >= self.last_index

    def __len__(self) -> int:
        return len(self.entries)
