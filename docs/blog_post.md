# CaseGuard: Winning with Uncertainty-Gated Agentic Fraud Investigation on TigerGraph

*A technical breakdown of our submission for the TigerGraph HHGOA Hackathon.*

---

## 1. Executive Summary

Traditional automated fraud prevention systems suffer from a binary fallacy: attempting to label complex transactions as either "fraud" or "not fraud." In modern financial crime, sophisticated syndicates exploit these rigid thresholds through synthetic identities, distributed device emulators, and rapid multi-hop pass-through accounts.

We built **CaseGuard**: an autonomous fraud investigation agent powered by **TigerGraph**, **GSQL analytics**, and a cyclic **LangGraph state machine**. 

CaseGuard's defining philosophy is **"An investigator that knows what it doesn't know."** Rather than guessing aggressively, CaseGuard:
1. Formulates hypotheses by executing **GSQL graph algorithms** (detecting device sharing, velocity bursts, IP clusters, and mule chains).
2. Computes an explicit, multi-factor **Uncertainty & Confidence score**.
3. Initiates **controlled, policy-approved evidence gathering** (step-up 2FA, customer transaction pings) when confidence is insufficient.
4. Generates defensible **Next-Best-Action (NBA)** recommendations with strict Human-in-the-Loop policy guardrails.
5. Persists closed cases back into the graph to empower **continuous case-memory learning**.

---

## 2. Architecture Blueprint

```
┌────────────────────────────────────────────────────────┐
│                   STREAMLIT DASHBOARD                  │
│   Case Timeline · Evidence Lineage · Approval Queue   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│              CASEGUARD AGENT ORCHESTRATOR               │
│                   (LangGraph Loop)                     │
│                                                        │
│  TRIAGE ─▶ GATHER ─▶ DETECT_PATTERNS ─▶ CASE_MEMORY    │
│    ▲                                          │        │
│    │      ┌─────────────────────────────┐     │        │
│    │      │  Uncertainty Engine         │     │        │
│    └──────┤  (Score < Threshold?)       │◀────┘        │
│  Request  └──────────────┬──────────────┘              │
│  Evidence                │ Score >= Threshold          │
│                          ▼                             │
│                  RECOMMEND_ACTIONS ─▶ PERSIST_GRAPH    │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    TIGERGRAPH DB                       │
│  • Transaction Graph Topology                          │
│  • Installed GSQL Pattern Detectors                   │
│  • Case Memory & Prior Investigations                  │
│  • GraphRAG Policy Knowledge Store                     │
└────────────────────────────────────────────────────────┘
```

---

## 3. How TigerGraph & GSQL Win the Investigation

The dataset contains ~590,000 transactions, ~13,500 customers, and multi-dimensional identity signals. A generic LLM cannot compute connected graph paths or aggregate velocity over graph edges.

In CaseGuard, **GSQL does 100% of the graph traversal and pattern detection; the LLM reasons over the structured graph output:**

- **Device Multi-Accounting (`detect_device_sharing.gsql`)**: Evaluates the subgraphs connecting `Device -> Transaction -> Account` and `Customer`. Instantly flags device fingerprints linked to 3+ distinct cards or identities within sliding windows.
- **Velocity Burst Analysis (`detect_velocity_burst.gsql`)**: Performs real-time accumulator-driven aggregations over `Transaction` vertices outgoing from a card to catch automated testing bursts.
- **Mule Chain Tracing (`detect_mule_chain.gsql`)**: Multi-hop BFS traversal through pass-through intermediary accounts.
- **Address & Device Discrepancies (`detect_addr_mismatch.gsql`)**: Discovers mismatches between billing address, shipping address, and newly seen device IDs.

---

## 4. The Uncertainty Engine (The Winning Lever)

The primary differentiator in judging criteria (representing 50% of the score between Accuracy and Next-Best-Action) is the agent's ability to navigate ambiguity.

CaseGuard computes confidence as a weighted, calibrated formula:

$$\text{Confidence} = w_1 \cdot \text{GraphSupport} + w_2 \cdot \text{HistoricalRate} + w_3 \cdot \text{SignalStrength} + w_4 \cdot \text{EvidenceCoverage} - \text{Penalty}_{\text{contradiction}}$$

- **Graph Support ($w=0.35$)**: Grounded in GSQL query matches and neighbor fraud density.
- **Historical Rate ($w=0.25$)**: Outcome distribution of structurally similar prior closed cases.
- **Signal Strength ($w=0.25$)**: Bank model risk score and anomaly features.
- **Evidence Coverage ($w=0.15$)**: Percentage of the required checklist for the suspected typology.
- **Contradiction Penalty**: Subtracted if behavioral signals resemble previously cleared legitimate cases, preventing aggressive false-positive blocks.

### The NBA Decision Progression (Before vs. After Evidence)
Hackathon guidelines require logging the next best action both **before** requesting additional evidence and **after** receiving it. CaseGuard enforces this natively in state:
- If $\text{Confidence} < 0.60$, CaseGuard logs the initial NBA (e.g., `monitor_account` + `request_step_up_auth`), dispatches the mock verification, and recalculates the updated NBA upon receiving user validation.

---

## 5. Hardcoded Governance & Permission Matrix

Autonomous agents in banking must operate within strict regulatory guardrails:
- Non-invasive actions (`request_step_up_auth`, `warn_customer`, `monitor_account`) **auto-execute**.
- High-impact protective actions (`block_transaction`, `block_account`, `file_SAR`) are classified as `pending_approval` and routed to **L1/L2 Analysts** or **Compliance Officers** via the UI approval queue.
- Mandatory SAR narratives are drafted in FinCEN standard formatting when transaction volume exceeds \$5,000 or mule laundering patterns are detected.

---

## 6. Key Learnings & Future Horizon

1. **Separation of Graph Execution & LLM Reasoning**: Offloading graph traversals to pre-compiled GSQL queries gives sub-millisecond execution times and deterministic evidence.
2. **Graph-Backed Memory Over Raw Vector Stores**: Embedding case summaries while maintaining graph linkages (`SIMILAR_TO_PRIOR_CASE`) creates a rich historical audit trail.
3. **With More Time**: We plan to implement automated community detection (Louvain) in GSQL to proactively identify emerging, undocumented syndicate clusters before a trigger even fires.
