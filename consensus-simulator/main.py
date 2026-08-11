#!/usr/bin/env python3
"""Distributed Consensus Simulator — Main entry point.

Usage:
    python main.py raft --nodes 5 --scenario normal
    python main.py paxos --nodes 5 --proposals 3
    python main.py raft --nodes 7 --scenario chaos --duration 30
"""

import argparse
import asyncio
import random
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.raft.node import RaftNode, NodeState, AppendEntriesRequest, AppendEntriesResponse
from src.raft.election import VoteRequest, VoteResponse, ElectionTimer
from src.raft.log import RaftLog, LogEntry
from src.viz import SimulationVizState, ConsensusEvent, EventType, render_text_dashboard


class NetworkSimulator:
    """Simulates an asynchronous network between Raft nodes.

    Supports:
    - Message delays (uniform or Gaussian distribution)
    - Message drops
    - Network partitions (split nodes into groups)
    - Node failures (crash-stop)
    """

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        self.min_delay: float = 0.01   # seconds
        self.max_delay: float = 0.2    # seconds
        self.drop_rate: float = 0.0
        self.partitions: list[set[int]] = []  # List of partition groups
        self.viz_state = SimulationVizState()

    def can_deliver(self, from_id: int, to_id: int) -> bool:
        """Check if a message can be delivered given current partitions."""
        if not self.partitions:
            return True
        # Nodes in different partitions cannot communicate
        for partition in self.partitions:
            if from_id in partition:
                return to_id in partition
        return False

    def should_drop(self) -> bool:
        """Random drop based on drop_rate."""
        return self.rng.random() < self.drop_rate

    def delay(self) -> float:
        """Sample a random message delay."""
        return self.rng.uniform(self.min_delay, self.max_delay)

    def create_partition(self, group_a: set[int], group_b: set[int]):
        """Split the network into two partitions."""
        self.partitions = [group_a, group_b]

    def heal_partitions(self):
        """Remove all network partitions."""
        self.partitions.clear()

    def kill_node(self, node: RaftNode):
        """Simulate a crash-stop failure."""
        node.stop()

    def add_event(self, event_type: EventType, node_id: int,
                  detail: dict | None = None, description: str = ""):
        """Record a consensus event for visualization."""
        self.viz_state.add_event(ConsensusEvent(
            time=self.viz_state.time,
            event_type=event_type,
            node_id=node_id,
            detail=detail or {},
            description=description,
        ))


class RaftCluster:
    """A cluster of Raft nodes connected by a simulated network."""

    def __init__(self, num_nodes: int = 5, network: NetworkSimulator | None = None):
        self.network = network or NetworkSimulator()
        self.nodes: dict[int, RaftNode] = {}
        self.message_queue: list[tuple[float, int, int, object]] = []  # (deliver_at, from, to, msg)

        peer_ids = list(range(num_nodes))
        for i in range(num_nodes):
            node = RaftNode(
                node_id=i,
                peer_ids=[p for p in peer_ids if p != i],
            )
            node.send_rpc = self._make_send_rpc(i)
            node.state_change_callback = self._on_state_change
            self.nodes[i] = node

    def _make_send_rpc(self, sender_id: int):
        """Create an async RPC sender bound to a specific node."""
        async def send_rpc(node: RaftNode, rpc_type: str, msg: object) -> None:
            # Enqueue messages to all peers (broadcast)
            for peer_id in node.peer_ids:
                if self.network.can_deliver(sender_id, peer_id) and \
                   not self.network.should_drop():
                    delay = self.network.delay()
                    deliver_at = self.network.viz_state.time + delay
                    self.message_queue.append((deliver_at, sender_id, peer_id, msg))
                    self.network.viz_state.message_count += 1
        return send_rpc

    def _on_state_change(self, node: RaftNode, old_state: NodeState, new_state: NodeState):
        """Callback when a node changes state."""
        self.network.viz_state.add_event(ConsensusEvent(
            time=self.network.viz_state.time,
            event_type=EventType.STATE_CHANGE,
            node_id=node.node_id,
            detail={"from": old_state.name, "to": new_state.name},
            description=f"{old_state.name} → {new_state.name} (term {node.current_term})",
        ))

    def deliver_messages(self, current_time: float) -> list[tuple[int, int, object]]:
        """Deliver all messages whose delivery time has arrived.

        Returns list of (from_id, to_id, message) tuples that were delivered.
        """
        delivered = []
        remaining = []
        for deliver_at, from_id, to_id, msg in self.message_queue:
            if deliver_at <= current_time:
                delivered.append((from_id, to_id, msg))
            else:
                remaining.append((deliver_at, from_id, to_id, msg))
        self.message_queue = remaining
        return delivered

    def process_message(self, from_id: int, to_id: int, msg: object):
        """Process a delivered message at the receiving node."""
        to_node = self.nodes[to_id]
        if not to_node.running:
            return

        if isinstance(msg, VoteRequest):
            resp = to_node.handle_request_vote(msg)
            # Send response back (no delay for responses per Raft simplicity)
            from_node = self.nodes[from_id]
            if from_node.running and msg.term >= from_node.current_term:
                if resp.vote_granted:
                    # Count votes for candidate
                    pass  # Handled in run_election_round

        elif isinstance(msg, AppendEntriesRequest):
            resp = to_node.handle_append_entries(msg)
            # Response handling
            from_node = self.nodes[from_id]
            if from_node.running and msg.term >= from_node.current_term:
                from_node.process_append_response(to_id, resp)

    def run_election(self, candidate: RaftNode) -> bool:
        """Run an election round for a candidate.

        Sends RequestVote to all peers and counts responses.
        Returns True if candidate won (majority votes).

        In a real Raft implementation, this is async/event-driven.
        For the simulator, we process votes synchronously since the
        network is simulated.
        """
        req = VoteRequest(
            term=candidate.current_term,
            candidate_id=candidate.node_id,
            last_log_index=candidate.log.last_index,
            last_log_term=candidate.log.last_term,
        )

        votes = 1  # Vote for self
        votes_needed = (len(self.nodes) // 2) + 1

        for peer_id in candidate.peer_ids:
            peer = self.nodes[peer_id]
            if not peer.running:
                continue
            resp = peer.handle_request_vote(req)
            if resp.vote_granted:
                votes += 1
            elif resp.term > candidate.current_term:
                candidate.become_follower(resp.term)
                return False

        if votes >= votes_needed:
            candidate.become_leader()
            self.network.viz_state.add_event(ConsensusEvent(
                time=self.network.viz_state.time,
                event_type=EventType.ELECTION_WIN,
                node_id=candidate.node_id,
                detail={"votes": votes, "needed": votes_needed, "term": candidate.current_term},
                description=f"Won election with {votes}/{votes_needed} votes (term {candidate.current_term})",
            ))
            self.network.viz_state.leader_id = candidate.node_id
            return True

        return False

    def tick(self, dt: float):
        """Advance the simulation by dt seconds."""
        current_time = self.network.viz_state.time + dt
        self.network.viz_state.time = current_time

        # 1. Deliver pending messages
        delivered = self.deliver_messages(current_time)
        for from_id, to_id, msg in delivered:
            self.process_message(from_id, to_id, msg)

        # 2. Tick each node
        for node in self.nodes.values():
            if not node.running:
                continue
            node.tick(dt)

            # Check election timeout
            if node.state in (NodeState.FOLLOWER, NodeState.CANDIDATE) and \
               node.timer.fired:
                node.become_candidate()
                self.network.viz_state.add_event(ConsensusEvent(
                    time=current_time,
                    event_type=EventType.ELECTION_START,
                    node_id=node.node_id,
                    detail={"term": node.current_term},
                    description=f"Election started (term {node.current_term})",
                ))

                # Run election
                won = self.run_election(node)
                if won:
                    # Send initial heartbeats
                    for peer_id in node.peer_ids:
                        peer = self.nodes[peer_id]
                        if peer.running:
                            hb = node.prepare_append_entries(peer_id)
                            if hb:
                                self.process_message(node.node_id, peer_id, hb)

            # Leaders send periodic heartbeats (every ~1/3 of min election timeout)
            if node.state == NodeState.LEADER:
                # Heartbeat interval ≈ 1/2 of min election timeout
                pass  # Heartbeats managed in main loop for simplicity

        # 3. Update viz state
        for node in self.nodes.values():
            self.network.viz_state.add_node_snapshot(
                node.node_id,
                node.state.name,
                node.current_term,
                len(node.log),
                node.commit_index,
            )

    def get_leader(self) -> RaftNode | None:
        """Get the current leader node, if any."""
        for node in self.nodes.values():
            if node.is_leader and node.running:
                return node
        return None


async def run_raft_simulation(
    num_nodes: int = 5,
    duration: float = 30.0,
    scenario: str = "normal",
    viz: bool = False,
    tick_rate: float = 0.01,  # 10ms tick
):
    """Run a Raft consensus simulation.

    Scenarios:
    - normal: 5 nodes, no failures, observe leader election + log replication
    - leader_failure: Kill leader after 5s, observe new election
    - partition: Split network into 3+2, observe minority stall
    - chaos: Random failures, delays, partitions
    """
    network = NetworkSimulator(seed=42)
    cluster = RaftCluster(num_nodes=num_nodes, network=network)

    print(f"\n{'='*70}")
    print(f"  Raft Consensus Simulation")
    print(f"  Nodes: {num_nodes} | Scenario: {scenario} | Duration: {duration}s")
    print(f"{'='*70}\n")

    start_time = time.time()
    tick_count = 0
    leader_killed = False
    partition_active = False

    while time.time() - start_time < duration:
        cluster.tick(tick_rate)
        tick_count += 1

        sim_time = network.viz_state.time

        # Scenario triggers
        if scenario in ("leader_failure", "chaos") and not leader_killed and sim_time > 5.0:
            leader = cluster.get_leader()
            if leader:
                print(f"\n  💀 Killing leader N{leader.node_id} at t={sim_time:.1f}s\n")
                network.kill_node(leader)
                network.viz_state.leader_id = None
                leader_killed = True

        if scenario in ("partition", "chaos") and not partition_active and sim_time > 8.0:
            mid = num_nodes // 2
            group_a = set(range(mid + 1))  # Majority (3 of 5)
            group_b = set(range(mid + 1, num_nodes))  # Minority (2 of 5)
            print(f"\n  🔀 Network partition: {group_a} | {group_b} at t={sim_time:.1f}s\n")
            network.create_partition(group_a, group_b)
            partition_active = True

        if partition_active and sim_time > 15.0:
            print(f"\n  🔗 Healing partition at t={sim_time:.1f}s\n")
            network.heal_partitions()
            partition_active = False

        # Periodic leader heartbeats (every ~500ms sim time)
        if tick_count % 50 == 0:
            leader = cluster.get_leader()
            if leader:
                for peer_id in leader.peer_ids:
                    peer = cluster.nodes[peer_id]
                    if peer.running:
                        hb = leader.prepare_append_entries(peer_id)
                        if hb:
                            cluster.process_message(leader.node_id, peer_id, hb)

        # Periodic logging
        if tick_count % 200 == 0 and viz:
            print(render_text_dashboard(network.viz_state))
            print()

        await asyncio.sleep(0)  # Yield to event loop

    # Final state
    print("\n  Final State:")
    print(render_text_dashboard(network.viz_state))

    # Summary
    leader = cluster.get_leader()
    if leader:
        print(f"\n  ✅ Consensus achieved: N{leader.node_id} is leader (term {leader.current_term})")
    else:
        print(f"\n  ⚠️  No leader elected")

    print(f"  Total ticks: {tick_count} | Messages: {network.viz_state.message_count}")
    print(f"  Events logged: {len(network.viz_state.events)}")


def main():
    parser = argparse.ArgumentParser(
        description="Distributed Consensus Simulator — Raft + Paxos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py raft --nodes 5 --scenario normal
  python main.py raft --nodes 7 --scenario chaos --duration 30
  python main.py paxos --nodes 5 --proposals 3
        """,
    )
    subparsers = parser.add_subparsers(dest="algorithm", required=True)

    # Raft subcommand
    raft_parser = subparsers.add_parser("raft", help="Run Raft consensus simulation")
    raft_parser.add_argument("--nodes", type=int, default=5, help="Number of nodes (default: 5)")
    raft_parser.add_argument("--scenario", choices=["normal", "leader_failure", "partition", "chaos"],
                             default="normal", help="Simulation scenario")
    raft_parser.add_argument("--duration", type=float, default=30.0,
                             help="Simulation duration in seconds (default: 30)")
    raft_parser.add_argument("--viz", action="store_true", default=True,
                             help="Enable visualization (default: True)")
    raft_parser.add_argument("--no-viz", action="store_true",
                             help="Disable visualization")

    # Paxos subcommand
    paxos_parser = subparsers.add_parser("paxos", help="Run Paxos consensus simulation")
    paxos_parser.add_argument("--nodes", type=int, default=5, help="Number of nodes (default: 5)")
    paxos_parser.add_argument("--proposals", type=int, default=3,
                              help="Number of proposals to run")

    args = parser.parse_args()

    if args.algorithm == "raft":
        show_viz = not args.no_viz
        asyncio.run(run_raft_simulation(
            num_nodes=args.nodes,
            duration=args.duration,
            scenario=args.scenario,
            viz=show_viz,
        ))
    elif args.algorithm == "paxos":
        print("Paxos simulation — coming soon. Use 'raft' for now.")
        sys.exit(0)


if __name__ == "__main__":
    main()
