"""Consensus visualization — Rich terminal dashboard.

The visualization shows:
1. Node state transitions (Follower/Candidate/Leader timeline)
2. Log replication progress (commit index per node)
3. Message flow between nodes
4. Election events and term changes

Uses the Rich library for terminal rendering.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(Enum):
    """Types of consensus events to visualize."""
    STATE_CHANGE = "state_change"
    ELECTION_START = "election_start"
    ELECTION_WIN = "election_win"
    LOG_APPEND = "log_append"
    LOG_COMMIT = "log_commit"
    MESSAGE_SEND = "message_send"
    HEARTBEAT = "heartbeat"
    TERM_CHANGE = "term_change"


@dataclass
class ConsensusEvent:
    """A single consensus event for visualization."""
    time: float
    event_type: EventType
    node_id: int
    detail: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __repr__(self) -> str:
        return f"[t={self.time:.3f}] {self.event_type.value}: n{self.node_id} {self.description}"


@dataclass
class NodeTimeline:
    """Timeline of states for a single node."""
    node_id: int
    segments: list[dict] = field(default_factory=list)  # [{start, end, state}]


@dataclass
class SimulationVizState:
    """Snapshot of the entire simulation for visualization.

    Captured at each visualization tick to render the dashboard.
    """
    time: float = 0.0
    nodes: list[dict] = field(default_factory=list)  # [{id, state, term, log_len, commit}]
    events: list[ConsensusEvent] = field(default_factory=list)
    message_count: int = 0
    leader_id: int | None = None

    def add_event(self, event: ConsensusEvent):
        self.events.append(event)
        # Keep only last 100 events for performance
        if len(self.events) > 100:
            self.events = self.events[-100:]

    def add_node_snapshot(self, node_id: int, state: str, term: int,
                          log_len: int, commit: int):
        """Add or update a node's snapshot."""
        for n in self.nodes:
            if n["id"] == node_id:
                n.update(state=state, term=term, log_len=log_len, commit=commit)
                return
        self.nodes.append({
            "id": node_id,
            "state": state,
            "term": term,
            "log_len": log_len,
            "commit": commit,
        })


def render_text_dashboard(state: SimulationVizState) -> str:
    """Render a text-based dashboard of the simulation state.

    Returns a string suitable for terminal output.
    """
    lines = []
    lines.append("=" * 70)
    lines.append(f"  Consensus Simulator  |  Time: {state.time:6.2f}s  |  Messages: {state.message_count}")
    lines.append("=" * 70)

    # Node status table
    lines.append(f"{'Node':>6}  {'State':>10}  {'Term':>6}  {'Log':>6}  {'Commit':>8}")
    lines.append("-" * 70)
    for n in sorted(state.nodes, key=lambda x: x["id"]):
        state_str = n["state"]
        marker = " ★" if n["id"] == state.leader_id else ""
        lines.append(
            f"  N{n['id']:02d}{marker:<2}  {state_str:>10}  {n['term']:>6}  "
            f"{n['log_len']:>6}  {n['commit']:>8}"
        )

    lines.append("-" * 70)
    lines.append(f"  Leader: N{state.leader_id}" if state.leader_id is not None
                 else "  Leader: (none)")

    # Recent events
    if state.events:
        lines.append("")
        lines.append(f"  Recent Events ({min(10, len(state.events))} of {len(state.events)}):")
        for ev in state.events[-10:]:
            lines.append(f"    {ev}")

    lines.append("=" * 70)
    return "\n".join(lines)


def render_state_diagram(state: SimulationVizState, width: int = 70) -> str:
    """Render a simple ASCII state diagram showing node states over time.

    This is a horizontal timeline where each node is a row and
    state is shown as characters: F=Follower, C=Candidate, L=Leader.
    """
    lines = ["Node states:", "-" * width]

    for n in sorted(state.nodes, key=lambda x: x["id"]):
        state_char = {"FOLLOWER": "F", "CANDIDATE": "C", "LEADER": "L"}.get(
            n["state"], "?"
        )
        leader_mark = " ← LEADER" if n["id"] == state.leader_id else ""
        bar_len = min(40, width - 20)
        bar = "█" * bar_len if n["state"] == "LEADER" else \
              "▓" * bar_len if n["state"] == "CANDIDATE" else \
              "░" * bar_len
        lines.append(f"  N{n['id']:02d} [{state_char}] {bar}{leader_mark}")

    return "\n".join(lines)
