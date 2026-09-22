"""
CaseGuard — Confidence / Uncertainty Engine

Computes a weighted confidence score at every decision point.
All components and the final score are logged to the case.

confidence = w1 * graph_support       (links to confirmed fraud / pattern match)
           + w2 * historical_rate     (outcome distribution of similar prior cases)
           + w3 * signal_strength     (bank risk score + velocity + anomaly features)
           + w4 * evidence_coverage   (% of the typology checklist covered)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math


# ── Weights (must sum to 1.0) ────────────────────────────────────────────────
W_GRAPH_SUPPORT = 0.35
W_HISTORICAL_RATE = 0.25
W_SIGNAL_STRENGTH = 0.25
W_EVIDENCE_COVERAGE = 0.15

assert abs(W_GRAPH_SUPPORT + W_HISTORICAL_RATE + W_SIGNAL_STRENGTH + W_EVIDENCE_COVERAGE - 1.0) < 1e-9

# ── Decision thresholds ───────────────────────────────────────────────────────
THRESHOLD_ACT = 0.75       # ≥ this → recommend action
THRESHOLD_GATHER = 0.50    # 0.50–0.75 → gather more evidence
# < 0.50 → escalate to analyst


@dataclass
class ConfidenceComponents:
    graph_support: float = 0.0       # 0–1: fraud signals from graph traversal
    historical_rate: float = 0.0     # 0–1: fraction of similar prior cases that were fraud
    signal_strength: float = 0.0     # 0–1: normalized bank risk score + velocity z-score
    evidence_coverage: float = 0.0   # 0–1: % typology checklist items evidenced
    contradiction_penalty: float = 0.0  # subtracted if evidence resembles cleared cases

    def compute(self) -> float:
        raw = (
            W_GRAPH_SUPPORT * self.graph_support
            + W_HISTORICAL_RATE * self.historical_rate
            + W_SIGNAL_STRENGTH * self.signal_strength
            + W_EVIDENCE_COVERAGE * self.evidence_coverage
        )
        return max(0.0, min(1.0, raw - self.contradiction_penalty))

    def to_dict(self) -> dict:
        return {
            "graph_support": round(self.graph_support, 4),
            "historical_rate": round(self.historical_rate, 4),
            "signal_strength": round(self.signal_strength, 4),
            "evidence_coverage": round(self.evidence_coverage, 4),
            "contradiction_penalty": round(self.contradiction_penalty, 4),
            "final": round(self.compute(), 4),
        }


def compute_graph_support(
    pattern_matches: list[dict],
    confirmed_fraud_neighbor_count: int,
    total_neighbor_count: int,
) -> float:
    """
    Score based on:
    - How many fraud patterns were matched (each contributes proportional to severity)
    - Fraction of neighbors confirmed as fraud (guilt by association)
    """
    if not pattern_matches and confirmed_fraud_neighbor_count == 0:
        return 0.0

    # Pattern contribution: each match adds (severity / max_severity)
    # Severity mapping: critical=1.0, high=0.75, medium=0.5, low=0.25
    severity_map = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
    pattern_score = 0.0
    for pm in pattern_matches:
        sev = pm.get("severity", "medium")
        pattern_score = max(pattern_score, severity_map.get(sev, 0.5))

    # Neighborhood fraud fraction
    neighbor_score = 0.0
    if total_neighbor_count > 0:
        neighbor_score = min(1.0, confirmed_fraud_neighbor_count / max(1, total_neighbor_count))

    return min(1.0, 0.7 * pattern_score + 0.3 * neighbor_score)


def compute_historical_rate(prior_cases: list[dict]) -> float:
    """
    Fraction of similar prior cases that were confirmed fraud.
    Weighted by similarity score.
    """
    if not prior_cases:
        return 0.3  # Prior probability without information

    weighted_fraud = sum(
        pc["similarity"] for pc in prior_cases if pc["outcome"] == "fraud"
    )
    weighted_total = sum(pc["similarity"] for pc in prior_cases)

    if weighted_total == 0:
        return 0.3

    return weighted_fraud / weighted_total


def compute_signal_strength(
    bank_risk_score: float,
    velocity_z_score: Optional[float] = None,
    amount_percentile: Optional[float] = None,
) -> float:
    """
    Normalize bank risk score (0–1) and combine with velocity + amount signals.
    bank_risk_score: already 0–1 from the dataset
    velocity_z_score: how many std devs above normal transaction rate
    amount_percentile: percentile of transaction amount in customer history
    """
    # Bank risk score is the primary signal
    score = bank_risk_score

    # Velocity: cap at z=5 → 1.0
    if velocity_z_score is not None:
        vel_signal = min(1.0, velocity_z_score / 5.0)
        score = 0.7 * score + 0.3 * vel_signal

    # Amount percentile (high amounts on new accounts are risky)
    if amount_percentile is not None:
        amount_signal = amount_percentile  # already 0–1
        score = 0.85 * score + 0.15 * amount_signal

    return min(1.0, score)


def compute_evidence_coverage(
    pattern_id: Optional[str],
    evidence_types_collected: list[str],
    typology_checklists: dict[str, list[str]],
) -> float:
    """
    What fraction of the required evidence checklist for the detected typology
    has been collected.
    """
    if not pattern_id or pattern_id not in typology_checklists:
        # Generic coverage — reward having any evidence
        return min(1.0, len(evidence_types_collected) / 5.0)

    checklist = typology_checklists[pattern_id]
    if not checklist:
        return 1.0

    covered = sum(1 for item in checklist if item in evidence_types_collected)
    return covered / len(checklist)


def compute_contradiction_penalty(
    cleared_case_similarity: float,
    cleared_case_count: int,
) -> float:
    """
    Reduce confidence if evidence closely resembles cleared (not-fraud) cases.
    This makes the agent defensible, not just aggressive.
    """
    if cleared_case_count == 0:
        return 0.0
    # Penalty scales with how similar the cleared cases are
    return min(0.25, cleared_case_similarity * 0.3)


def decide_next_step(confidence: float) -> str:
    """
    Three-way decision based on confidence score.
    Returns: "act" | "gather_more" | "escalate"
    """
    if confidence >= THRESHOLD_ACT:
        return "act"
    elif confidence >= THRESHOLD_GATHER:
        return "gather_more"
    else:
        return "escalate"


def explain_uncertainty(components: ConfidenceComponents, confidence: float) -> list[str]:
    """
    Generate human-readable uncertainty reasons for the case record.
    """
    reasons = []

    if components.graph_support < 0.3:
        reasons.append("Limited graph evidence connecting this activity to known fraud patterns")
    if components.historical_rate < 0.4:
        reasons.append("Low historical fraud rate for similar cases")
    if components.signal_strength < 0.5:
        reasons.append("Moderate risk score — could be legitimate unusual transaction")
    if components.evidence_coverage < 0.6:
        reasons.append("Incomplete evidence checklist for the suspected fraud typology")
    if components.contradiction_penalty > 0.1:
        reasons.append("Activity resembles previously cleared cases — confidence reduced")
    if confidence < THRESHOLD_GATHER:
        reasons.append("Overall confidence too low to take action without analyst review")

    if not reasons:
        reasons.append("Sufficient evidence and confidence for recommended action")

    return reasons


# ── Typology evidence checklists ──────────────────────────────────────────────
# These are the evidence types needed to fully investigate each known pattern
TYPOLOGY_CHECKLISTS: dict[str, list[str]] = {
    "device_sharing": [
        "device_signal",
        "account_list",
        "transaction_history",
        "customer_profile",
        "velocity_check",
    ],
    "velocity_burst": [
        "transaction_history",
        "velocity_check",
        "card_history",
        "ip_signal",
        "device_signal",
    ],
    "ip_clustering": [
        "ip_signal",
        "customer_list",
        "transaction_history",
        "geo_analysis",
    ],
    "addr_mismatch_new_device": [
        "address_comparison",
        "device_signal",
        "transaction_history",
        "customer_profile",
        "card_history",
    ],
    "mule_chain": [
        "transaction_history",
        "money_flow_trace",
        "account_list",
        "velocity_check",
        "customer_profile",
    ],
}
