# 🏛️ Distributed Consensus Simulator

> **Raft + Paxos consensus algorithms visualized.** Built to understand distributed consensus through implementation — the Karpathy "Build to Understand" way.

## Why This Exists

Distributed consensus is the hardest problem in distributed systems — **FLP impossibility** proves no deterministic asynchronous consensus protocol can guarantee termination with even one faulty process. Yet Raft and Paxos work in practice because they make a crucial assumption: **partial synchrony** (messages eventually arrive within some unknown bound).

This simulator implements both algorithms and lets you watch consensus emerge from chaos.

## FLP Impossibility — First-Principles Derivation

### Theorem (Fischer, Lynch, Paterson 1985)

> In an asynchronous distributed system with no clocks and no failure detection, it is impossible to achieve deterministic consensus with even one crash failure.

### Proof Sketch

**Axiom 1 (Asynchrony):** Messages can be arbitrarily delayed. A process cannot distinguish between a crashed process and a slow one.

**Axiom 2 (Atomicity):** Each process executes steps atomically — a step is: receive message → change state → send messages.

**Axiom 3 (Fault Model):** At most one crash failure. Crashed process stops forever.

**Proof by contradiction:**

1. **Bivalent configuration exists.** Assume a protocol always reaches consensus. Start from an initial bivalent configuration C₀ (both 0 and 1 decisions possible). Show that for any round, there exists a bivalent configuration reachable from C₀.

2. **No deciding step from bivalent.** For any bivalent configuration C, there exists an arbitrarily long sequence of steps that remains bivalent. Proof: If from every bivalent C, some step leads to a univalent state, choose the "last" bivalent state — but because messages can be delayed, we can always delay the deciding message, creating another bivalent state. Contradiction.

3. **Non-termination.** Since we can stay bivalent forever, and the protocol must terminate to decide, we have a contradiction: no such deterministic protocol exists. ∎

### Why Raft/Paxos Escape FLP

They use **partial synchrony** — a weak timing assumption:
- ∃ unknown GST (Global Stabilization Time) after which all messages arrive within Δ
- Before GST, the system is asynchronous (can be slow)
- After GST, the system is synchronous
- The protocol is guaranteed to decide *eventually* after GST

This is the **liveness-via-randomization** trick: randomized election timeouts in Raft ensure that with probability → 1, a leader is elected and consensus terminates.

### Mathematical Model

**Safety (never wrong):**
$$\forall n \in \{0,1\}: \text{decided}(n) \Rightarrow \text{proposed}(n)$$
$$\neg(\text{decided}(0) \land \text{decided}(1))$$

**Liveness (eventually decides):**
$$P(\exists t: \text{decided} \mid \text{GST reached}) = 1$$

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Consensus Simulator                    │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Raft Engine  │  │ Paxos Engine │  │  Visualizer    │ │
│  │              │  │              │  │                │ │
│  │ • Leader     │  │ • Proposer   │  │ • State DAG    │ │
│  │   Election   │  │ • Acceptor   │  │ • Message Flow │ │
│  │ • Log        │  │ • Learner    │  │ • Timeline     │ │
│  │   Replication│  │              │  │ • Dashboard    │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│                          │                              │
│              ┌───────────▼───────────┐                  │
│              │   Network Simulator   │                  │
│              │  • Message delay      │                  │
│              │  • Partition/failure  │                  │
│              │  • Drop/duplicate     │                  │
│              └───────────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

## Usage

```bash
# Run Raft simulation with 5 nodes
python main.py raft --nodes 5 --scenario leader-election

# Run Paxos simulation
python main.py paxos --nodes 5 --proposals 10

# Run with visualization
python main.py raft --nodes 5 --viz dashboard

# Run chaos scenario (network partitions + failures)
python main.py raft --nodes 7 --scenario chaos --duration 60
```

## Raft Implementation

### Key Mechanisms

1. **Leader Election:**
   - Randomized election timeout: 150ms–300ms
   - Term-based: higher term always wins
   - Candidate requests votes, becomes leader with majority

2. **Log Replication:**
   - Leader appends to log, followers replicate
   - Committed when replicated to majority
   - Log Matching Property: same index+term ⇒ same all prior entries

3. **Safety:**
   - Leader Completeness: committed entries survive leader changes
   - Election Restriction: candidate must have up-to-date log
   - Leader Append-Only: leader never overwrites its own entries

## Paxos Implementation (Single-Decree)

### Roles
- **Proposer**: proposes values, must get majority
- **Acceptor**: accepts proposals, remembers highest
- **Learner**: learns the chosen value

### Two-Phase Protocol
1. **Prepare (phase 1):** Proposer → Acceptors: "I propose n." Acceptor responds with highest-numbered proposal < n it has accepted.
2. **Accept (phase 2):** Proposer → Acceptors: "Accept proposal n with value v (highest from phase 1 responses)."

## Test Scenarios

| Scenario | Description | Expected |
|----------|-------------|----------|
| Normal operation | 5 nodes, no failures | Leader elected, consensus < 500ms |
| Leader failure | Kill leader mid-replication | New leader elected, no data loss |
| Network partition | Split 5 nodes into 3+2 | Majority partition continues, minority stalls |
| Message delay | Random 0-500ms delays | Eventually consistent, longer convergence |
| Byzantine-free | Only crash-stop failures | Safety maintained |

## Technical Details

- **Language**: Python 3.11+
- **Concurrency**: `asyncio` for event-driven message passing
- **Visualization**: Rich terminal dashboard + optional PNG output
- **Testing**: pytest with property-based tests (hypothesis)

## References

- Ongaro, D., & Ousterhout, J. (2014). "In Search of an Understandable Consensus Algorithm" (Raft)
- Lamport, L. (1998). "The Part-Time Parliament" (Paxos)
- Fischer, M. J., Lynch, N. A., & Paterson, M. S. (1985). "Impossibility of Distributed Consensus with One Faulty Process"
- Lamport, L. (2001). "Paxos Made Simple"

## License

MIT — Built by Claude Code Operational Self for Karpathy Build-to-Understand dimension.
