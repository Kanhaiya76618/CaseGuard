# CaseGuard — Agentic Fraud Investigation System

> TigerGraph-powered AI agent for fraud investigation, uncertainty-gated evidence gathering, and next-best-action recommendations.
> Built for the HHGOA Hackathon (TigerGraph Agentic Fraud Investigation).

[![Dev.to Blog Post](https://img.shields.io/badge/Dev.to-Technical%20Blog%20Post-0A0A0A?style=for-the-badge&logo=devdotto)](https://dev.to/kanha_9650/-caseguard-winning-with-uncertainty-gated-agentic-fraud-investigation-on-tigergraph-407p)
[![X Announcement](https://img.shields.io/badge/X-Social%20Post-1DA1F2?style=for-the-badge&logo=x)](https://x.com/Kanhaiy41867349/status/2102605055862153410?s=20)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

- 📖 **Technical Blog Post**: [Read on Dev.to](https://dev.to/kanha_9650/-caseguard-winning-with-uncertainty-gated-agentic-fraud-investigation-on-tigergraph-407p)
- 🐦 **X (Twitter) Announcement**: [View Tweet](https://x.com/Kanhaiy41867349/status/2102605055862153410?s=20)


## Architecture

```
Streamlit UI (analyst dashboard)
     │
LangGraph Agent (stateful cyclic loop)
     ├── TigerGraph MCP (69 graph tools)
     │        └── TigerGraph Savanna (graph + TigerVector)
     ├── GSQL Pattern Queries (7 detectors)
     ├── Uncertainty Engine (confidence scorer)
     ├── NBA Decision Tree + Permission Matrix (hardcoded guardrail)
     └── GraphRAG (policy/typology grounding)
```

## Setup & Quickstart

```bash
# 1. Clone repository
git clone https://github.com/Kanhaiya76618/CaseGuard.git
cd CaseGuard

# 2. Run the dynamic Hacker House Goa UI & Live API Server
python3 scripts/serve_live.py
# Open http://localhost:8000 in your browser!

# 3. Or run the official benchmark generator over all 20 cases
python3 scripts/run_real_benchmarks.py
```

## Project Structure

```
caseguard/
├── agent/
│   ├── state.py          # LangGraph InvestigationState
│   ├── graph.py          # LangGraph StateGraph definition
│   ├── nodes/            # Individual agent node implementations
│   │   ├── triage.py
│   │   ├── gather_evidence.py
│   │   ├── detect_patterns.py
│   │   ├── retrieve_prior_cases.py
│   │   ├── ground_policy.py
│   │   ├── assess_uncertainty.py
│   │   ├── request_evidence.py
│   │   ├── recommend_actions.py
│   │   ├── explain.py
│   │   ├── write_case.py
│   │   └── update_memory.py
│   ├── confidence.py     # Uncertainty / confidence scoring engine
│   ├── nba.py            # Next-best-action decision tree + permission matrix
│   └── tools/
│       ├── mcp_tools.py  # TigerGraph MCP wrappers
│       ├── mock_actions.py  # Mock step-up auth, block, SAR APIs
│       └── graphrag.py   # Policy/typology GraphRAG retrieval
├── gsql/
│   ├── schema.gsql
│   ├── loading_jobs.gsql
│   ├── detect_device_sharing.gsql
│   ├── detect_velocity_burst.gsql
│   ├── detect_ip_clustering.gsql
│   ├── detect_addr_mismatch.gsql
│   ├── detect_mule_chain.gsql
│   ├── find_similar_cases.gsql
│   ├── get_customer_profile.gsql
│   └── trace_transaction.gsql
├── ui/
│   └── app.py            # Streamlit analyst dashboard
├── scripts/
│   ├── setup_schema.py
│   ├── load_data.py
│   ├── install_queries.py
│   └── run_benchmark.py
├── output/
│   ├── cases/            # 20 answer JSON files
│   └── sars/             # SAR documents
├── data/                 # Dataset (not committed — gitignore)
├── docs/
│   └── blog_post.md
├── tests/
│   └── test_confidence.py
├── .env.example
├── requirements.txt
└── README.md
```

## Key Design Decisions

- **GSQL does all fraud analysis** — LLM reasons over graph results, never replaces graph traversal
- **Confidence = weighted blend** of graph support, historical rate, signal strength, evidence coverage
- **NBA permission matrix is hardcoded** — agent cannot bypass it
- **NBA recorded before AND after** additional evidence requests (judging requirement)
- **Case memory = graph-first** — prior cases as vertices + TigerVector embeddings for hybrid retrieval
- **GraphRAG for policy** — relevant policy clauses retrieved, not raw doc dumps

## Autonomous Monitoring & Innovation Cases (Innovation 15%)

Per Line 19 of the official dataset specification:
> *"Optional. If your agent also monitors the exam period on its own, picks up alerts from the risk scores, and investigates beyond the 20 cases, put those in a separate folder. They count toward Innovation, not accuracy."*

CaseGuard continuously scans real-time streams beyond the initial 20 exam cases. We provide **5 additional autonomous monitoring cases** (`HHG-021` to `HHG-025`) in `cases_autonomous/` (and `cases/extra/`), also discoverable in the live Web UI:
- **`HHG-021`**: Automated Headless Card Testing probe burst & rapid escalation (Policy R5).
- **`HHG-022`**: High-Exposure Cross-Border Syndicate & TOR Device Sharing Ring with FinCEN SAR filing over $5,000 (Policies R2, R6).
- **`HHG-023`**: Out-of-region legitimate business travel false positive resolution (Policies R1, R3).
- **`HHG-024`**: Account Takeover (ATO) brute-force credential stuffing with full customer card quarantine (Policies R2, R10).
- **`HHG-025`**: Undocumented Velocity Stacking & multi-merchant structured draining attack (Policy R9).

## Judging Alignment

| Criterion | How We Win It |
|-----------|---------------|
| Investigation accuracy (25%) | 7 GSQL pattern queries + calibrated thresholds on official 20 benchmark cases (`cases/`) |
| Next best action (25%) | Explicit NBA decision tree + before/after recording conforming to Bank Fraud Policy v1.0 |
| Case summary/explainability (10%) | Structured 3-part case schema + grounded LLM summary and FinCEN SAR narratives |
| Agentic design (15%) | LangGraph cyclic investigation loop + TigerGraph MCP + permission guardrails |
| Innovation (15%) | Autonomous monitoring folder (`cases_autonomous/`), case memory as graph, hybrid GraphRAG |
| Demo (10%) | Hacker House Goa editorial UI + dynamic live investigation engine at `http://localhost:8000` |

