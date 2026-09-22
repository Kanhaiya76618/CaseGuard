"""
CaseGuard - Mock External Actions & Controlled Evidence Gathering
Simulates step-up authentication, customer transaction validation, account blocks, and SAR generation.
"""
from datetime import datetime, timezone
import random
from typing import Dict, Any


def execute_step_up_auth(target_id: str, case_id: str) -> Dict[str, Any]:
    """Simulate requesting 2FA/step-up authentication from account holder."""
    # Deterministic simulation based on ID
    seed = sum(ord(c) for c in target_id)
    rng = random.Random(seed)
    
    # Outcomes: SUCCESS, FAILED, TIMED_OUT
    status = rng.choices(["SUCCESS", "FAILED", "TIMED_OUT"], weights=[0.45, 0.35, 0.20])[0]
    
    return {
        "action": "request_step_up_auth",
        "target_id": target_id,
        "case_id": case_id,
        "auth_status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": f"Step-up 2FA prompt delivered to registered authenticator. Result: {status}"
    }


def execute_customer_validation(target_id: str, transaction_id: str, amount: float) -> Dict[str, Any]:
    """Simulate asking customer to confirm transaction via SMS/push."""
    seed = sum(ord(c) for c in target_id) + int(amount)
    rng = random.Random(seed)
    
    response = rng.choices(["CONFIRMED_LEGITIMATE", "DENIED_FRAUD", "NO_RESPONSE"], weights=[0.40, 0.45, 0.15])[0]
    
    return {
        "action": "request_customer_validation",
        "target_id": target_id,
        "transaction_id": transaction_id,
        "customer_response": response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": f"Customer validation ping for ${amount}: Customer reported '{response}'"
    }


def execute_block_transaction(transaction_id: str, approval_by: str = "L1_Analyst") -> Dict[str, Any]:
    """Execute transaction block upon analyst sign-off."""
    return {
        "action": "block_transaction",
        "transaction_id": transaction_id,
        "status": "executed",
        "approved_by": approval_by,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": f"Transaction {transaction_id} successfully declined and placed on hold."
    }


def execute_block_account(card_or_customer_id: str, approval_by: str = "L2_Analyst") -> Dict[str, Any]:
    """Execute account freeze upon senior analyst approval."""
    return {
        "action": "block_account",
        "entity_id": card_or_customer_id,
        "status": "executed",
        "approved_by": approval_by,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": f"Account/Card {card_or_customer_id} frozen to prevent further fund dissipation."
    }


def generate_sar_report(
    case_id: str,
    target_id: str,
    reasons: list[str],
    evidence_summary: str,
    total_amount: float,
    regulatory_refs: list[str]
) -> str:
    """Draft a FinCEN-compliant Suspicious Activity Report (SAR) narrative."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    refs_str = "\n".join(f" - {ref}" for ref in regulatory_refs)
    reasons_str = "\n".join(f" - {r}" for r in reasons)
    
    return f"""
SUSPICIOUS ACTIVITY REPORT (SAR) - NARRATIVE
Case ID: {case_id}
Filing Date: {date_str}
Subject ID / Primary Target: {target_id}
Total Suspicious Volume: ${total_amount:,.2f}

1. REGULATORY BASIS:
{refs_str}

2. NATURE OF SUSPICIOUS ACTIVITY:
{reasons_str}

3. CHRONOLOGICAL EVIDENCE TRAIL:
{evidence_summary}

4. NEXT BEST ACTIONS & DISPOSITION:
The automated CaseGuard agent, in accordance with institution risk thresholds and human compliance review, 
has placed a preventative lock on associated accounts and escalated this dossier for FinCEN transmission.
"""
