# TigerGraph Agentic Fraud Investigation — Master Playbook (HHGOA)

> A complete, actionable blueprint you can hand to your AI agent and your team. It tells you **what to build, how to build it, and how to win** — grounded in the real TigerGraph MCP (69 tools) and GraphRAG (hybrid vector + graph retrieval) capabilities.

---

## 0. Read This First — The One-Paragraph Strategy

The teams that win this hackathon will NOT be the ones with the fanciest LLM. They will be the ones who (a) model the HHGOA dataset as a **fraud knowledge graph** that makes fraud patterns queryable in GSQL, (b) wire those graph queries to the agent as **named tools via the TigerGraph MCP**, (c) run the agent in a **stateful LangGraph loop** that explicitly tracks evidence + confidence + uncertainty and *re-evaluates the next-best-action after every new piece of evidence*, and (d) use **case memory** (prior closed investigations written back into the graph) so the agent gets smarter case-over-case. Accuracy (25%) + Next-best-action (25%) = half the score. Both come from the **graph and the loop**, not from the model. Spend your time there.

---

## 1. What You're Actually Building

A working AI agent that, given a fraud trigger, does this loop autonomously:

```
TRIGGER → INVESTIGATE (graph) → GATHER EVIDENCE → ASSESS UNCERTAINTY
   ↑                                                        ↓
   └── MEMORY UPDATE ← EXPLAIN ← TAKE ACTION ← (more evidence?) 
```

**Deliverables (non-negotiable, from the rules):**
1. Working agent (GitHub repo)
2. Agent output on 20 benchmark cases — each case = one answer file containing: internal investigation record, evidence, findings, decisions, actions taken, **written back to the graph**, plus a **SAR (Suspicious Activity Report)** when policy requires, plus the **next-best-action + approval route** recorded *before* and *after* any extra evidence.
3. 3–5 min demo video (end-to-end)
4. Technical blog post
5. Social post on X/LinkedIn tagging @TigerGraphDB

---

## 2. Scoring Strategy — Where to Spend Your Hours

| Criterion | Weight | What wins it | Where to invest |
|---|---|---|---|
| **Investigation accuracy** | 25% | Correctly identifying fraud patterns + quality of evidence gathered | GSQL pattern queries + graph schema design |
| **Next best action** | 25% | Handling uncertain signals, knowing when to ask for more evidence, updating recommendations as evidence arrives | The uncertainty/confidence engine + NBA decision tree |
| **Case summary & explainability** | 10% | Clear case progression, evidence trail, reasoning | Structured case schema + LLM summarization grounded in evidence |
| **Agentic design & engineering** | 15% | Architecture, tool use, workflow orchestration, memory, controls, permissions | LangGraph state machine + MCP tool routing + permission gates |
| **Innovation** | 15% | Original use of graph + AI + GraphRAG + agentic capabilities | Case-memory-as-graph, GraphRAG over policies/typologies, confidence-driven loop |
| **Demo quality & completeness** | 10% | Clear, end-to-end, shows the loop | A polished UI that visualizes the investigation timeline |

> **Force multiplier:** Accuracy + Next-best-action = **50%**. Both are downstream of the graph schema and the agent loop. If you nail those two, the explainability and engineering scores ride along. Do **not** start with the UI.

---

## 3. Architecture Blueprint

```
┌────────────────────────────────────────────────────────────────────┐
│                        AGENT (LangGraph state machine)              │
│  Trigger → Investigate → Gather → Assess → [more?] → NBA → Explain │
│                  ↑ uses case memory ↓ writes case back              │
└────────────┬───────────────────────────────┬────────────────────────┘
             │ MCP tools (69 available)       │ GraphRAG (policy/typology grounding)
             ▼                                ▼
┌──────────────────────────┐     ┌───────────────────────────────────┐
│   TigerGraph MCP Server  │     │  TigerGraph GraphRAG              │
│  • run_installed_query    │     │  • hybrid vector+graph retrieval  │
│  • get_neighbors          │     │  • ingest fraud policy docs        │
│  • get_node/edges         │     │  • community search over typologies│
│  • search_top_k_similarity│     │  • grounds LLM with relevant text  │
│  • add_node/edge (cases)  │     └───────────────────────────────────┘
│  • gsql (raw)             │
└─────────────┬─────────────┘
              ▼
┌──────────────────────────────────────────────────────────────────────┐
│            TigerGraph (Savanna or Community 4.2+)                     │
│   Fraud Knowledge Graph: Transactions, Accounts, Customers,         │
│   Devices, IPs, Emails, PriorCases, Patterns, PolicyRules            │
│   + TigerVector embeddings for case-memory similarity                 │
└──────────────────────────────────────────────────────────────────────┘
             ▲
             │ LLM (GPT-4.1 / Claude / Gemini) — reasoning + tool selection
┌────────────┴───────────┐
│  Custom Tools / Mocks   │  (step-up auth, customer validation, block account…)
└────────────────────────┘
```

**Why these choices:**
- **LangGraph** (not vanilla LangChain/CrewAI) because the investigation is a *stateful cyclic loop* — you revisit "gather more evidence" multiple times. LangGraph's `StateGraph` with conditional edges models this exactly. The TigerGraph MCP repo itself recommends LangGraph.
- **TigerGraph MCP** exposes 69 tools — you don't write graph plumbing; you expose your installed GSQL queries as agent tools and let the LLM call them.
- **GraphRAG** for the *unstructured* side: fraud policy PDFs, typology documents, regulatory references. It does hybrid vector+graph retrieval so the agent gets "relevant policy clause" not "raw text dump."
- **TigerVector** (built into TG 4.2+) for case-memory similarity — embed closed-case summaries, retrieve similar past cases by embedding + graph structure.

---

## 4. Graph Schema Design — The Foundation

Get this right first. Everything downstream depends on it. The HHGOA dataset has ~590K transactions, ~13.5K customers, device/connection records, closed investigations, 5 known fraud patterns, and a fraud policy.

### 4.1 Vertex Types

| Vertex | Primary ID | Key Attributes |
|---|---|---|
| `Transaction` | TransactionID | amount, timestamp, risk_score, card_type, product, addr_match, ...Vesta C1-C9/Vxxx features |
| `Account` (card) | card_id / account_id | card_type, issuer, first_seen, status |
| `Customer` | customer_id | name, email, phone, billing_country, created_at, risk_tier |
| `Device` | device_id (devicetype+deviceinfo hash) | device_type, first_seen, device_count |
| `IPAddress` | ip_id | ip_str, isp, country, first_seen |
| `Email` | email_addr | domain, first_seen |
| `Address` | addr_hash (billing/shipping) | street_hash, city, state, country, zip |
| `PriorCase` | case_id | opened_at, closed_at, outcome (fraud/cleared), pattern_id, summary, **embedding** |
| `FraudPattern` | pattern_id | name, description, severity, typology_ref |
| `PolicyRule` | rule_id | rule_text, category (block/monitor/escalate/SAR), threshold |
| `InvestigationCase` | case_id | trigger, status (open/closed), risk_level, confidence, opened_at, updated_at |
| `Evidence` | evidence_id | source, type, content, collected_at, confidence_weight |
| `Action` | action_id | type, status (recommended/executed), approval_route, timestamp |

### 4.2 Edge Types (directed, weighted where useful)

| Edge | From → To | Meaning |
|---|---|---|
| `used_card` | Transaction → Account | this txn used this card |
| `purchased_by` | Transaction → Customer | txn belongs to customer |
| `originated_from_device` | Transaction → Device | device that made the online txn |
| `originated_from_ip` | Transaction → IPAddress | IP source |
| `uses_email` | Customer → Email | customer's email |
| `billed_to` / `shipped_to` | Transaction → Address | billing/shipping addr |
| `owns_card` | Customer → Account | card ownership |
| `has_device` | Customer → Device | device used by customer |
| **`similar_to`** | PriorCase → Transaction | case involved this txn (weighted by role) |
| **`case_involved_customer`** | PriorCase → Customer | case touched this customer |
| **`exhibited_pattern`** | PriorCase → FraudPattern | case matched this pattern |
| **`triggered_by`** | InvestigationCase → Transaction/Customer | what started this case |
| **`case_has_evidence`** | InvestigationCase → Evidence | evidence collected |
| **`case_recommends`** | InvestigationCase → Action | recommended/executed action |
| **`case_matched_pattern`** | InvestigationCase → FraudPattern | pattern detected |
| **`references_rule`** | Action → PolicyRule | policy justification |
| **`case_outcome_like`** | InvestigationCase → PriorCase | "this case resembles prior case X" (memory link) |

### 4.3 Why this schema wins

- **Fraud patterns become graph traversals.** "Device shared across N accounts" = hop Device→Customer→Account. "Velocity" = count txns from one card in a 1-hour window. "Mule chain" = path of money through accounts. GSQL handles these natively — no ML needed for pattern detection.
- **Case memory is first-class.** Prior cases are vertices with embeddings; `case_outcome_like` edges let the agent *traverse* from a new case to similar old ones, not just vector-search them.
- **Full audit trail.** Evidence and Action vertices linked to InvestigationCase give you the explainability score for free — every recommendation has a `references_rule` edge to policy.

---

## 5. Fraud Pattern Detection — GSQL Queries as Agent Tools

The dataset says "5 known fraud patterns" + "not every fraud pattern is documented." So build detectors for the known ones **and** let the agent discover undocumented ones via graph anomaly queries.

### 5.1 Five likely fraud patterns & their GSQL detection logic

| # | Pattern | GSQL detection sketch | Evidence signal |
|---|---|---|---|
| 1 | **Device/Account sharing** | From a Device vertex, count distinct Customer→Account edges within 24h. Threshold: ≥3 | One device, many identities |
| 2 | **Velocity / transaction burst** | From a card (Account), count outgoing `used_card` edges in a sliding 1h window. Threshold: >N normal | Card hit rapidly |
| 3 | **IP clustering** | From IPAddress, count distinct Customer edges; flag if high count + cross-border | Many accounts, one IP |
| 4 | **Address mismatch (ship≠bill) + new device** | Transaction where `shipped_to ≠ billed_to` AND device `first_seen < 7d` AND amount > threshold | Identity theft / account takeover |
| 5 | **Mule / money-movement chain** | Multi-hop path: Account →(txn)→ Account →(txn)→ Account within short window, decreasing amounts | Funds funneled through chain |

> These are starting points — read the dataset README first; it documents the exact 5 patterns and their characteristics. Tune thresholds against the closed-investigation cases (you have labeled fraud/cleared outcomes for the first 4 months). **Use those labels to calibrate.**

### 5.2 Undocumented pattern discovery (the innovation lever)

Install a few **anomaly** queries the agent can run when known patterns don't fit:
- **PageRank / centrality spike** — a node with anomalous betweenness in the transaction graph.
- **Community detection** (Louvain via TigerGraph algorithms) — find clusters of accounts tightly connected that shouldn't be.
- **Triangle count** — three entities mutually linked (device↔ip↔account triangle) is a strong synthetic-identity signal.

The agent calling a graph algorithm query as a "tool" — and reasoning about the result — is exactly the kind of graph+AI innovation the judges want.

### 5.3 Expose these as installed queries via MCP

Each detector becomes an **installed GSQL query**. The agent calls it through `tigergraph__run_installed_query`. Name them clearly so the LLM picks the right one:

```
detect_device_sharing(vertex_id, time_window)
detect_velocity_burst(account_id, window_hours)
detect_ip_clustering(ip_id)
detect_addr_mismatch_new_device(transaction_id)
detect_mule_chain(account_id, depth)
find_anomalous_centrality(graph_name)
find_suspicious_communities()
```

Use `tigergraph__update_query_description` (TG 4.0+) to give each query an LLM-readable description — this is the hint that makes tool selection accurate.

---

## 6. The Agent Loop — LangGraph State Machine

### 6.1 State schema

```python
class InvestigationState(TypedDict):
    case_id: str
    trigger: dict               # {type: signal|report|analyst, ref: ..., risk_score: ...}
    target: dict                # {entity_type, entity_id} — txn/card/customer
    evidence: list[dict]        # accumulated evidence items
    patterns_matched: list[str] # fraud pattern IDs detected
    risk_level: str            # low|medium|high|critical
    confidence: float          # 0.0–1.0
    uncertainty_reasons: list[str]
    nba_before: dict           # next-best-action before extra evidence
    nba_after: dict | None     # updated after extra evidence (if any requested)
    actions_taken: list[dict]
    prior_cases_used: list[str]
    status: str                # open|needs_evidence|acted|closed
    history: list[str]         # decision log
    iterations: int
```

### 6.2 Nodes (each is a function or LLM call)

| Node | Responsibility | TigerGraph MCP tools it uses |
|---|---|---|
| `ingest_trigger` | Normalize trigger, identify target entity | `get_node`, `get_node_edges` |
| `create_case` | Open InvestigationCase vertex in graph | `add_node` (InvestigationCase) |
| `gather_initial_evidence` | Pull txn history, device, IP, account behavior, neighborhood | `run_installed_query` (custom), `get_neighbors`, `get_node_edges` |
| `detect_patterns` | Run the 5 pattern detectors + anomaly queries | `run_installed_query` (detect_*) |
| `retrieve_prior_cases` | Vector+graph search for similar closed cases | `search_top_k_similarity`, `run_installed_query` |
| `ground_with_policy` | GraphRAG over fraud policy + typologies + regulatory refs | (GraphRAG API / MCP) |
| `assess_uncertainty` | Compute confidence; decide: enough to act, or need more? | (pure LLM reasoning over state) |
| `request_more_evidence` | Issue controlled action: step-up auth, customer validation, analyst input | mock APIs |
| `update_nba` | Re-compute next-best-action after new evidence | (LLM + decision tree) |
| `execute_or_recommend_action` | Recommend/execute within permissions | mock APIs + `add_edge` (Action) |
| `explain` | Generate case summary + reasoning + SAR if required | (LLM, grounded in evidence) |
| `write_case_to_graph` | Persist case, evidence, actions, decisions, memory links | `add_node`/`add_edge` |
| `update_memory` | Embed case summary; link to patterns/customers for future retrieval | `upsert_vectors`, `add_edge` |

### 6.3 Conditional edges (the loop)

```
assess_uncertainty ──(confidence ≥ threshold AND evidence sufficient)──→ execute_or_recommend_action
                ──(confidence < threshold OR evidence insufficient)──→ request_more_evidence
request_more_evidence ──(evidence received)──→ gather_initial_evidence  [re-gather, loop back]
                    ──(no response / timeout)──→ execute_or_recommend_action [act on best available]
execute_or_recommend_action ──(action requires human approval)──→ park for approval
                          ──(action auto-authorized)──→ execute
```

Cap iterations (`max_iterations`) to avoid infinite loops. Every pass through the loop **appends to `history`** and **updates the InvestigationCase vertex in the graph** — this gives you the case-progression score.

---

## 7. Next-Best-Action Engine — The 25% Differentiator

This is the most-judged capability. Build it as an explicit decision layer, not "let the LLM decide."

### 7.1 Action catalog (from the rules)

`allow_transaction` · `block_transaction` · `block_account` · `monitor_account` · `warn_customer` · `create_fraud_case` · `file_SAR` · `request_more_evidence` · `escalate_to_analyst` · `request_step_up_auth` · `request_customer_validation`

### 7.2 Permission matrix (controls — judges check for this)

| Action | Auto-execute? | Needs approval? | Approval route |
|---|---|---|---|
| allow_transaction | yes (agent) | no | — |
| monitor_account | yes (agent) | no | — |
| warn_customer | yes (agent) | no | — |
| request_step_up_auth | yes (agent) | no | — |
| request_customer_validation | yes (agent) | no | — |
| request_more_evidence | yes (agent) | no | — |
| block_transaction | no | yes | L1 analyst |
| block_account | no | yes | L2 analyst |
| escalate_to_analyst | yes (agent routes) | — | escalates to human queue |
| file_SAR | no | yes | compliance officer |
| create_fraud_case | yes (agent) | no | — |

> Hardcode this matrix as a guardrail the agent **cannot bypass**. The "controls & permissions" part of the engineering score is literally this table enforced in code.

### 7.3 Decision logic (confidence × risk × pattern)

```
IF confidence ≥ 0.85 AND risk = high AND pattern = confirmed_fraud:
    → block_account + create_case + file_SAR (if policy threshold met) + escalate
ELIF confidence ≥ 0.7 AND risk = medium AND pattern detected:
    → block_transaction + monitor_account + warn_customer
ELIF confidence < 0.6 OR evidence insufficient:
    → request_more_evidence (specific evidence: step-up auth / customer validation / analyst input)
    → record nba_before, then re-run loop, then record nba_after
ELIF confidence ≥ 0.85 AND no pattern AND risk = low:
    → allow_transaction + close_case
ELSE:
    → escalate_to_analyst
```

**Critical for scoring:** the rules explicitly want the next-best-action + approval route recorded **before** any extra evidence is requested **and** **after** it's received. So `nba_before` goes into state *before* `request_more_evidence`, and `nba_after` is recomputed after the loop returns. Both get written to the answer file and to the graph.

### 7.4 SAR (Suspicious Activity Report) trigger

Use GraphRAG to retrieve the bank's fraud policy + regulatory references, then a policy-matching step:
- If pattern severity ≥ threshold OR transaction amount ≥ threshold OR pattern is on a watchlist → SAR required.
- The SAR text is generated by the LLM, grounded in: evidence items, matched pattern, prior similar cases, and the relevant policy clauses retrieved via GraphRAG.

---

## 8. Case Memory — The Innovation Lever (15%)

This is where you differentiate. "Memory" isn't a vector DB bolted on — it's **the graph itself**.

### 8.1 Write phase (after each case closes)
1. Embed the case summary (TigerVector via `tigergraph__upsert_vectors` on the PriorCase/InvestigationCase vertex).
2. Add `exhibited_pattern` / `case_matched_pattern` edges.
3. Add `case_involved_customer` / `similar_to` edges to the entities involved.
4. Tag the case vertex with `outcome` (fraud/cleared) and the analyst decision.

### 8.2 Read phase (when investigating a new case)
1. **Vector recall:** `search_top_k_similarity` on case-summary embeddings → top-K similar past cases.
2. **Graph recall:** traverse from the *target entity* to any PriorCase via shared device/IP/email/address — "this customer's device was involved in a prior confirmed-fraud case."
3. **Combine:** the agent reasons over both: "3 similar past cases were confirmed fraud with the same device-sharing pattern → raises my confidence."

### 8.3 Pattern emergence across cases
After the benchmark, run a query: which patterns/entities/relationships recur across multiple confirmed-fraud cases? Store these as `FraudPattern` vertices the agent can cite. This is "the agent learning" — strong innovation signal.

---

## 9. GraphRAG — Grounding in Policy & Typologies

GraphRAG (the TigerGraph product) ingests the unstructured policy/typology/regulatory documents into a knowledge graph and does **hy vector + graph retrieval**. Use it for:

| Need | How |
|---|---|
| "Does policy require a SAR here?" | GraphRAG retrieves the relevant policy clause + threshold → LLM evaluates against case facts |
| "What typology does this match?" | GraphRAG retrieves typology descriptions → LLM matches against detected graph pattern |
| "What regulatory reference applies?" | GraphRAG retrieves regulatory text → cited in the case explanation/SAR |
| "What's the standard investigation procedure for this pattern?" | GraphRAG retrieves procedure doc → agent follows it as a workflow hint |

**Key principle from the rules:** *"Pass the relevant context to the LLM rather than simply passing raw data."* GraphRAG's job is to turn raw policy PDFs into retrieved, relevant, structured context — not to dump the whole document.

Setup: use the GraphRAG quick-start (`setup_graphrag.sh`) with an OpenAI/Gemini key, then ingest the policy/typology/regulatory docs through its UI or API. Wire it as a tool the agent calls during `ground_with_policy`.

---

## 10. Implementation Plan — Step-by-Step Build Order

A realistic order that front-loads the scoring-heavy work.

### Phase 0 — Setup (Day 0, half day)
1. Read the **dataset README** end to end — it defines files, columns, answer format, how the 20 cases work.
2. Spin up **TigerGraph Savanna** (enable auto-stop/start) **or** Community Edition 4.2+ locally via Docker.
3. `pip install tigergraph-mcp` (+ `[llm]` extras for query generation). Configure `.env` with `TG_HOST`, `TG_GRAPHNAME`, `TG_USERNAME`, `TG_PASSWORD`.
4. `pip install langgraph langchain-mcp-adapters langchain-openai`.
5. Create the GitHub repo (this is a deliverable).

### Phase 1 — Graph & Data (Day 1) — feeds Accuracy (25%)
1. Write the GSQL schema (Section 4).
2. Write loading jobs for the HHGOA CSV/JSON (transactions, customers, devices, IPs, closed cases, patterns, policy).
3. Load the 4 months of closed investigations as `PriorCase` vertices with embeddings.
4. Load the 20 benchmark-case triggers separately (don't leak answers).
5. Verify counts: ~590K txns, ~13.5K customers.

### Phase 2 — Pattern Queries (Day 1–2) — feeds Accuracy (25%)
1. Write & install the 5 pattern-detection GSQL queries (Section 5).
2. Calibrate thresholds against the labeled closed cases (precision/recall on months 1–4).
3. Write 2–3 anomaly queries (centrality, community, triangle).
4. Use `tigergraph__update_query_description` to give each query an LLM-friendly description.

### Phase 3 — Agent Loop (Day 2–3) — feeds Engineering (15%) + NBA (25%)
1. Define the LangGraph `StateGraph` (Section 6).
2. Implement nodes, wiring each to the right MCP tool.
3. Implement the uncertainty/confidence function + NBA decision tree (Section 7).
4. Implement the permission guardrails (Section 7.2).
5. Test on 2–3 closed cases (where you know the answer) before touching the 20 benchmarks.

### Phase 4 — Memory & GraphRAG (Day 3) — feeds Innovation (15%)
1. Add TigerVector embeddings to PriorCase/InvestigationCase.
2. Implement case-memory write & read (Section 8).
3. Stand up GraphRAG; ingest policy/typology/regulatory docs.
4. Wire `ground_with_policy` node to GraphRAG.

### Phase 5 — Answer Files (Day 4) — the actual submission
1. Run the agent on all 20 benchmark cases.
2. For each, emit the answer file: investigation record, evidence, findings, decisions, actions, NBA before/after, SAR (if required).
3. Write each case back to the graph (`add_node`/`add_edge`).
4. Verify the answer format matches the README exactly.

### Phase 6 — UI & Demo (Day 4–5) — feeds Demo (10%)
1. Build an analyst dashboard (Streamlit or React). Show: case timeline, evidence panel, confidence gauge, NBA with approval route, prior-case matches, graph visualization of the investigated subgraph.
2. Record the 3–5 min demo: trigger → investigate → evidence → uncertainty → more evidence → updated NBA → action → explanation. Show the graph.

### Phase 7 — Write-up (Day 5)
1. Blog post (what you built, architecture, TigerGraph usage, agentic capabilities, learnings, future improvements).
2. Social post on X/LinkedIn tagging @TigerGraphDB, linking blog + demo.
3. Finalize GitHub repo: README, run instructions, env template, the 20 answer files.

---

## 11. The 20 Answer Files — Exact Structure

For each benchmark case, produce a file containing:

```json
{
  "case_id": "...",
  "trigger": { "type": "...", "ref": "...", "risk_score": ... },
  "investigation_record": {
    "target": { "entity_type": "...", "entity_id": "..." },
    "evidence_gathered": [
      { "id": "...", "source": "graph|policy|prior_case|external",
        "type": "transaction_history|device_signal|ip_cluster|policy_clause|...",
        "content": "...", "collected_at": "...", "confidence_weight": ... }
    ],
    "patterns_matched": [ { "pattern_id": "...", "name": "...", "evidence_refs": [...] } ],
    "prior_cases_used": [ { "case_id": "...", "similarity": ..., "outcome": "..." } ],
    "risk_assessment": { "risk_level": "...", "confidence": ..., "uncertainty_reasons": [...] }
  },
  "next_best_action": {
    "before_additional_evidence": {
      "action": "...", "approval_route": "...", "reasoning": "..." },
    "after_additional_evidence": {
      "action": "...", "approval_route": "...", "reasoning": "..." }
  },
  "actions_taken": [
    { "action": "...", "status": "recommended|executed", "approval_route": "...",
      "timestamp": "...", "policy_refs": [...] }
  ],
  "sar": { "required": true, "text": "...", "regulatory_refs": [...] },
  "case_summary": "...",
  "reasoning": "...",
  "graph_written": true
}
```

> Match the **exact** format the dataset README specifies. Re-read it before generating files.

---

## 12. AI Prompt Template — Hand This to Your Coding Agent

Copy this to your AI assistant (Cursor, Copilot, etc.) to drive the build:

```
You are building an Agentic Fraud Investigation system for the TigerGraph HHGOA hackathon.

STACK: TigerGraph (Savanna or Community 4.2+), tigergraph-mcp (pip install),
LangGraph, an OpenAI/Anthropic/Gemini LLM, TigerGraph GraphRAG, Streamlit UI.

GOAL: An agent that, given a fraud trigger, investigates via the graph,
assesses uncertainty, gathers more evidence if needed, recommends a
next-best-action within a permission matrix, writes the case to the graph,
and produces a structured answer file per the README format.

DO THIS IN ORDER:
1. Read /path/to/dataset/README — follow its file/column/answer-format spec exactly.
2. Create GSQL schema with these vertex types: Transaction, Account, Customer,
   Device, IPAddress, Email, Address, PriorCase, FraudPattern, PolicyRule,
   InvestigationCase, Evidence, Action. (See playbook §4.)
3. Write loading jobs; load HHGOA data. Verify counts.
4. Write & install 5 fraud-pattern GSQL queries (device-sharing, velocity,
   IP-clustering, addr-mismatch-new-device, mule-chain) + 2 anomaly queries
   (centrality, community). Calibrate thresholds on the 4 months of labeled
   closed cases. Give each query an LLM-readable description.
5. Build a LangGraph StateGraph with nodes: ingest_trigger, create_case,
   gather_initial_evidence, detect_patterns, retrieve_prior_cases,
   ground_with_policy, assess_uncertainty, request_more_evidence, update_nba,
   execute_or_recommend_action, explain, write_case_to_graph, update_memory.
   Conditional edges implement the evidence loop with a max_iterations cap.
6. Wire each node to tigergraph-mcp tools (run_installed_query, get_neighbors,
   search_top_k_similarity, add_node/edge, upsert_vectors, gsql).
7. Implement the NBA decision tree (§7.3) + permission matrix (§7.2) as code
   guardrails the agent cannot bypass.
8. Stand up GraphRAG; ingest the fraud policy + typologies + regulatory refs;
   wire ground_with_policy to retrieve relevant clauses.
9. Implement case memory: embed closed-case summaries in TigerVector; on new
   case, vector-retrieve + graph-traverse similar prior cases.
10. Run on the 20 benchmark cases; emit answer files in the README format;
    write each case to the graph.
11. Build a Streamlit analyst dashboard: case timeline, evidence, confidence
    gauge, NBA + approval route, prior-case matches, subgraph visualization.
12. Record a 3–5 min demo end-to-end.

CONSTRAINTS:
- The LLM reasons and selects tools; GSQL does the graph analysis. Don't make
  the LLM re-implement graph traversal in Python.
- Every recommendation must cite policy (references_rule edge).
- Record NBA before AND after any extra-evidence request.
- Enforce the permission matrix in code.
- Do not look at the 20 benchmark answers during development. Use the
  4-month labeled closed cases for calibration only.

Deliver: GitHub repo, 20 answer files, demo video, blog post, social post.
```

---

## 13. Pitfalls & How to Avoid Them

| Pitfall | Fix |
|---|---|
| Treating the LLM as the graph engine | GSQL does traversal/pattern detection; LLM reasons over results & picks tools |
| One-shotting the 20 cases without the loop | Build the loop, test on closed cases first, then run benchmarks |
| Not writing cases back to the graph | It's an explicit deliverable — `graph_written: true` in every answer file |
| Forgetting NBA-before-and-after | It's explicitly judged; both go in the answer file |
| No permission guardrails | Hardcode the matrix; judges look for "operate within policies & permissions" |
| Vector-only memory (no graph) | Combine vector similarity *with* graph traversal from the target entity — that's the innovation |
| Dumping raw policy text to the LLM | Use GraphRAG to retrieve *relevant* clauses, not the whole doc |
| Over-engineering the UI first | UI is 10%; build it last after accuracy + NBA work |
| Leaking benchmark answers | Only calibrate on the 4-month labeled closed cases; never touch the 20-case labels |

---

## 14. TigerGraph MCP Tools You'll Actually Use (cheat sheet)

| Tool | When |
|---|---|
| `tigergraph__list_graphs`, `get_graph_schema` | Setup & sanity checks |
| `tigergraph__create_loading_job`, `run_loading_job_with_file` | Load HHGOA data |
| `tigergraph__install_query`, `run_installed_query` | Install & run your pattern detectors |
| `tigergraph__gsql` | Raw schema + ad-hoc analysis |
| `tigergraph__get_node`, `get_node_edges`, `get_neighbors` | Gather neighborhood evidence |
| `tigergraph__get_node_degree`, `get_vertex_count` | Quick stats |
| `tigergraph__add_vector_attribute`, `upsert_vectors`, `search_top_k_similarity` | Case-memory embeddings |
| `tigergraph__add_node`, `add_edge` | Write InvestigationCase, Evidence, Action, memory links |
| `tigergraph__update_query_description` | Make queries LLM-discoverable |
| `tigergraph__discover_tools`, `get_workflow` | Let the agent find the right tool at runtime |

> Run the MCP server with `--allowed-tools schema,query,vector,loading,discovery,utility` to keep the agent's tool context lean (~9–12K tokens instead of 29K).

---

## 15. Final Checklist Before You Submit

- [ ] Dataset README read; answer format matches exactly
- [ ] TigerGraph (Savanna with auto-stop/start, or Community 4.2+) running
- [ ] Schema + data loaded; counts verified (~590K txns, ~13.5K customers)
- [ ] 5 pattern detectors + 2 anomaly queries installed & calibrated on labeled cases
- [ ] LangGraph loop with evidence-gather cycle, max_iterations cap
- [ ] NBA decision tree + permission matrix enforced in code
- [ ] Case memory: embeddings written, vector+graph retrieval working
- [ ] GraphRAG standing; policy/typology/regulatory docs ingested; `ground_with_policy` wired
- [ ] 20 benchmark answer files generated in README format
- [ ] Each case written to the graph (`graph_written: true`)
- [ ] SAR generated where policy requires
- [ ] NBA before-and-after recorded in every answer file
- [ ] Streamlit/React analyst dashboard
- [ ] 3–5 min demo video (end-to-end, shows the loop + graph)
- [ ] GitHub repo with README, run instructions, env template, answer files
- [ ] Blog post (what/architecture/TigerGraph usage/agentic capabilities/learnings/future)
- [ ] Social post on X or LinkedIn tagging @TigerGraphDB, linking blog + demo

---

**Bottom line:** Win the graph + the loop, and you win the hackathon. Accuracy and next-best-action are 50% of the score and both are downstream of your schema and your LangGraph state machine — not your LLM. Build those first, wrap them in MCP tools and a permission matrix, use case memory and GraphRAG for the innovation score, and ship a clean demo last.
