"""
CaseGuard — LangGraph Investigation State
The canonical state object passed between all agent nodes.
"""
from __future__ import annotations
from typing import TypedDict, Annotated, Optional
import operator


class EvidenceItem(TypedDict):
    id: str
    source: str          # "graph" | "policy" | "prior_case" | "external"
    type: str            # "transaction_history" | "device_signal" | "ip_cluster" | ...
    content: str
    collected_at: str
    confidence_weight: float


class PatternMatch(TypedDict):
    pattern_id: str
    name: str
    evidence_refs: list[str]
    confidence: float


class PriorCaseRef(TypedDict):
    case_id: str
    similarity: float
    outcome: str         # "fraud" | "cleared"
    pattern_id: Optional[str]


class NBARecord(TypedDict):
    action: str
    approval_route: str  # "auto" | "l1_analyst" | "l2_analyst" | "compliance"
    reasoning: str
    confidence_at_time: float


class ActionRecord(TypedDict):
    action: str
    status: str          # "recommended" | "executed" | "pending_approval"
    approval_route: str
    timestamp: str
    policy_refs: list[str]


class InvestigationState(TypedDict):
    # ── Case identity ────────────────────────────────────────────────────
    case_id: str
    trigger: dict               # {type, ref_id, risk_score, source}

    # ── Target entity ────────────────────────────────────────────────────
    target: dict                # {entity_type, entity_id}

    # ── Accumulated evidence ──────────────────────────────────────────────
    evidence: Annotated[list[EvidenceItem], operator.add]
    patterns_matched: Annotated[list[PatternMatch], operator.add]
    prior_cases_used: Annotated[list[PriorCaseRef], operator.add]
    policy_context: str         # GraphRAG-retrieved relevant policy text

    # ── Risk assessment ───────────────────────────────────────────────────
    risk_level: str             # "low" | "medium" | "high" | "critical"
    confidence: float           # 0.0 – 1.0
    confidence_components: dict # {graph_support, historical_rate, signal_strength, evidence_coverage}
    uncertainty_reasons: list[str]
    evidence_sufficient: bool

    # ── NBA (before AND after additional evidence) ────────────────────────
    nba_before: Optional[NBARecord]
    nba_after: Optional[NBARecord]

    # ── Actions ───────────────────────────────────────────────────────────
    actions_taken: Annotated[list[ActionRecord], operator.add]
    pending_approvals: list[dict]

    # ── SAR ───────────────────────────────────────────────────────────────
    sar_required: bool
    sar_text: Optional[str]
    sar_regulatory_refs: list[str]

    # ── Case summary ──────────────────────────────────────────────────────
    case_summary: str
    reasoning: str

    # ── Loop control ──────────────────────────────────────────────────────
    status: str                 # "open" | "needs_evidence" | "acted" | "closed"
    iterations: int
    max_iterations: int
    history: Annotated[list[str], operator.add]  # decision log (append-only)

    # ── Memory / graph write ──────────────────────────────────────────────
    graph_written: bool
    memory_updated: bool
