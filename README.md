# CaseGuard — Agentic Fraud Investigation System

> TigerGraph-powered AI agent for fraud investigation, uncertainty-gated evidence gathering, and next-best-action recommendations.
> Built for the HHGOA Hackathon (TigerGraph Agentic Fraud Investigation).

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

## Judging Alignment

| Criterion | How We Win It |
|-----------|---------------|
| Investigation accuracy (25%) | 7 GSQL pattern queries + calibrated thresholds |
| Next best action (25%) | Explicit NBA decision tree + before/after recording |
| Case summary/explainability (10%) | Structured case schema + grounded LLM summary |
| Agentic design (15%) | LangGraph + MCP + permission guardrails |
| Innovation (15%) | Case-memory-as-graph + hybrid GraphRAG + TigerVector |
| Demo (10%) | Streamlit dashboard with graph viz + confidence meter |
