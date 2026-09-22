"""
CaseGuard — Next-Best-Action (NBA) Engine + Permission Matrix

The permission matrix is HARDCODED. The agent cannot bypass it.
Actions are selected via a deterministic decision tree driven by confidence,
risk level, and detected fraud patterns — not by the LLM directly.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime, timezone


class ActionType(str, Enum):
    ALLOW_TRANSACTION = "allow_transaction"
    BLOCK_TRANSACTION = "block_transaction"
    BLOCK_ACCOUNT = "block_account"
    MONITOR_ACCOUNT = "monitor_account"
    WARN_CUSTOMER = "warn_customer"
    CREATE_FRAUD_CASE = "create_fraud_case"
    FILE_SAR = "file_SAR"
    REQUEST_MORE_EVIDENCE = "request_more_evidence"
    REQUEST_STEP_UP_AUTH = "request_step_up_auth"
    REQUEST_CUSTOMER_VALIDATION = "request_customer_validation"
    ESCALATE_TO_ANALYST = "escalate_to_analyst"


class ApprovalRoute(str, Enum):
    AUTO = "auto"
    L1_ANALYST = "l1_analyst"
    L2_ANALYST = "l2_analyst"
    COMPLIANCE_OFFICER = "compliance_officer"
    HUMAN_QUEUE = "human_queue"


@dataclass(frozen=True)
class PermissionEntry:
    action: ActionType
    auto_execute: bool
    requires_approval: bool
    approval_route: ApprovalRoute
    description: str


# ── PERMISSION MATRIX (HARDCODED — CANNOT BE BYPASSED) ───────────────────────
PERMISSION_MATRIX: dict[ActionType, PermissionEntry] = {
    ActionType.ALLOW_TRANSACTION: PermissionEntry(
        action=ActionType.ALLOW_TRANSACTION,
        auto_execute=True,
        requires_approval=False,
        approval_route=ApprovalRoute.AUTO,
        description="Allow transaction to proceed — auto-executable",
    ),
    ActionType.MONITOR_ACCOUNT: PermissionEntry(
        action=ActionType.MONITOR_ACCOUNT,
        auto_execute=True,
        requires_approval=False,
        approval_route=ApprovalRoute.AUTO,
        description="Flag account for enhanced monitoring — auto-executable",
    ),
    ActionType.WARN_CUSTOMER: PermissionEntry(
        action=ActionType.WARN_CUSTOMER,
        auto_execute=True,
        requires_approval=False,
        approval_route=ApprovalRoute.AUTO,
        description="Send warning notification to customer — auto-executable",
    ),
    ActionType.REQUEST_STEP_UP_AUTH: PermissionEntry(
        action=ActionType.REQUEST_STEP_UP_AUTH,
        auto_execute=True,
        requires_approval=False,
        approval_route=ApprovalRoute.AUTO,
        description="Request step-up authentication — auto-executable",
    ),
    ActionType.REQUEST_CUSTOMER_VALIDATION: PermissionEntry(
        action=ActionType.REQUEST_CUSTOMER_VALIDATION,
        auto_execute=True,
        requires_approval=False,
        approval_route=ApprovalRoute.AUTO,
        description="Ask customer to validate a transaction — auto-executable",
    ),
    ActionType.REQUEST_MORE_EVIDENCE: PermissionEntry(
        action=ActionType.REQUEST_MORE_EVIDENCE,
        auto_execute=True,
        requires_approval=False,
        approval_route=ApprovalRoute.AUTO,
        description="Request additional evidence from approved sources — auto-executable",
    ),
    ActionType.CREATE_FRAUD_CASE: PermissionEntry(
        action=ActionType.CREATE_FRAUD_CASE,
        auto_execute=True,
        requires_approval=False,
        approval_route=ApprovalRoute.AUTO,
        description="Open a fraud investigation case — auto-executable",
    ),
    ActionType.ESCALATE_TO_ANALYST: PermissionEntry(
        action=ActionType.ESCALATE_TO_ANALYST,
        auto_execute=True,
        requires_approval=False,
        approval_route=ApprovalRoute.HUMAN_QUEUE,
        description="Route case to human analyst queue — auto-routes",
    ),
    ActionType.BLOCK_TRANSACTION: PermissionEntry(
        action=ActionType.BLOCK_TRANSACTION,
        auto_execute=False,
        requires_approval=True,
        approval_route=ApprovalRoute.L1_ANALYST,
        description="Block transaction — requires L1 analyst approval",
    ),
    ActionType.BLOCK_ACCOUNT: PermissionEntry(
        action=ActionType.BLOCK_ACCOUNT,
        auto_execute=False,
        requires_approval=True,
        approval_route=ApprovalRoute.L2_ANALYST,
        description="Block/freeze account — requires L2 analyst approval",
    ),
    ActionType.FILE_SAR: PermissionEntry(
        action=ActionType.FILE_SAR,
        auto_execute=False,
        requires_approval=True,
        approval_route=ApprovalRoute.COMPLIANCE_OFFICER,
        description="File Suspicious Activity Report — requires compliance officer",
    ),
}


def get_approval_route(action: ActionType) -> str:
    return PERMISSION_MATRIX[action].approval_route.value


def can_auto_execute(action: ActionType) -> bool:
    return PERMISSION_MATRIX[action].auto_execute


def check_sar_required(
    confidence: float,
    risk_level: str,
    transaction_amount: Optional[float],
    patterns_matched: list[str],
) -> tuple[bool, list[str]]:
    """
    Determine if a SAR must be filed per policy.
    Returns (required, regulatory_refs)
    """
    refs = []
    required = False

    # Policy threshold: high/critical confidence + high risk
    if confidence >= 0.75 and risk_level in ("high", "critical"):
        required = True
        refs.append("BSA/AML Policy §4.2: SAR required for high-confidence fraud")

    # Amount threshold (>= $5,000 for suspicious activity per BSA)
    if transaction_amount and transaction_amount >= 5000:
        required = True
        refs.append("31 CFR 1020.320: SAR required for transactions ≥ $5,000 with suspicious activity")

    # Pattern-specific triggers
    sar_patterns = {"mule_chain", "structuring", "money_laundering"}
    if any(p in sar_patterns for p in patterns_matched):
        required = True
        refs.append("BSA/AML Policy §5.1: SAR required for money movement patterns")

    return required, refs


def decide_nba(
    confidence: float,
    risk_level: str,
    patterns_matched: list[str],
    evidence_sufficient: bool,
    iteration: int,
    transaction_amount: Optional[float] = None,
) -> tuple[list[ActionType], str]:
    """
    Deterministic NBA decision tree.
    Returns (recommended_actions, reasoning)
    
    This is called TWICE:
    1. Before additional evidence is requested → nba_before
    2. After additional evidence is received  → nba_after
    """
    actions: list[ActionType] = []
    reasoning_parts: list[str] = []

    is_high_risk = risk_level in ("high", "critical")
    has_pattern = bool(patterns_matched)
    large_amount = transaction_amount and transaction_amount >= 1000

    # ── Branch 1: High confidence + high risk + confirmed pattern ────────────
    if confidence >= 0.85 and is_high_risk and has_pattern:
        actions = [
            ActionType.BLOCK_TRANSACTION,
            ActionType.BLOCK_ACCOUNT,
            ActionType.CREATE_FRAUD_CASE,
            ActionType.ESCALATE_TO_ANALYST,
        ]
        if check_sar_required(confidence, risk_level, transaction_amount, patterns_matched)[0]:
            actions.append(ActionType.FILE_SAR)
        reasoning_parts.append(
            f"High confidence ({confidence:.0%}) with confirmed pattern(s) {patterns_matched} "
            f"and {risk_level} risk level. Blocking transaction and account pending analyst review."
        )

    # ── Branch 2: Medium-high confidence + medium risk + pattern detected ────
    elif confidence >= 0.70 and has_pattern:
        actions = [
            ActionType.BLOCK_TRANSACTION,
            ActionType.MONITOR_ACCOUNT,
            ActionType.WARN_CUSTOMER,
            ActionType.CREATE_FRAUD_CASE,
        ]
        reasoning_parts.append(
            f"Pattern detected ({patterns_matched}) with confidence {confidence:.0%}. "
            "Blocking transaction, monitoring account, notifying customer."
        )

    # ── Branch 3: Insufficient evidence — request more ───────────────────────
    elif confidence < 0.60 or not evidence_sufficient:
        if iteration == 0:
            # First pass: start with least invasive evidence request
            actions = [
                ActionType.REQUEST_STEP_UP_AUTH,
                ActionType.MONITOR_ACCOUNT,
            ]
            reasoning_parts.append(
                f"Confidence {confidence:.0%} is below action threshold. "
                "Requesting step-up authentication as least-invasive first step."
            )
        else:
            # Subsequent passes: escalate evidence request
            actions = [
                ActionType.REQUEST_CUSTOMER_VALIDATION,
                ActionType.MONITOR_ACCOUNT,
                ActionType.ESCALATE_TO_ANALYST,
            ]
            reasoning_parts.append(
                f"After {iteration} iteration(s), confidence {confidence:.0%} still insufficient. "
                "Escalating with customer validation request and analyst review."
            )

    # ── Branch 4: High confidence, low risk, no pattern → allow ─────────────
    elif confidence >= 0.85 and not is_high_risk and not has_pattern:
        actions = [ActionType.ALLOW_TRANSACTION]
        reasoning_parts.append(
            f"High confidence ({confidence:.0%}) that this is legitimate. "
            "No fraud patterns detected, low risk level. Allowing transaction."
        )

    # ── Branch 5: Ambiguous — escalate ───────────────────────────────────────
    else:
        actions = [
            ActionType.ESCALATE_TO_ANALYST,
            ActionType.MONITOR_ACCOUNT,
        ]
        reasoning_parts.append(
            f"Ambiguous signals (confidence {confidence:.0%}, risk {risk_level}). "
            "Escalating to analyst for human judgment."
        )

    # Always create a case if we haven't yet and there's any suspicion
    if confidence >= 0.50 and ActionType.CREATE_FRAUD_CASE not in actions:
        actions.insert(0, ActionType.CREATE_FRAUD_CASE)

    return actions, " ".join(reasoning_parts)


def build_nba_record(
    actions: list[ActionType],
    reasoning: str,
    confidence: float,
) -> dict:
    """Build the NBA record dict for the answer file."""
    # Primary action for the record (highest severity)
    severity_order = [
        ActionType.FILE_SAR,
        ActionType.BLOCK_ACCOUNT,
        ActionType.BLOCK_TRANSACTION,
        ActionType.ESCALATE_TO_ANALYST,
        ActionType.BLOCK_TRANSACTION,
        ActionType.MONITOR_ACCOUNT,
        ActionType.WARN_CUSTOMER,
        ActionType.REQUEST_MORE_EVIDENCE,
        ActionType.REQUEST_CUSTOMER_VALIDATION,
        ActionType.REQUEST_STEP_UP_AUTH,
        ActionType.ALLOW_TRANSACTION,
    ]

    primary = next((a for a in severity_order if a in actions), actions[0] if actions else ActionType.ESCALATE_TO_ANALYST)
    route = get_approval_route(primary)

    return {
        "primary_action": primary.value,
        "all_actions": [a.value for a in actions],
        "approval_route": route,
        "reasoning": reasoning,
        "confidence_at_time": round(confidence, 4),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "auto_executable": [a.value for a in actions if can_auto_execute(a)],
        "requires_approval": [a.value for a in actions if not can_auto_execute(a)],
    }
