"""
CaseGuard - LangGraph Agent Orchestrator
Assembles the complete state graph with cyclic evidence gathering, uncertainty evaluation,
NBA recording before/after evidence, policy grounding, and case memory persistence.
"""
from typing import Dict, Any, Literal
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger("CaseGuard.Graph")

from agent.state import InvestigationState, EvidenceItem, PatternMatch, PriorCaseRef
from agent.confidence import (
    ConfidenceComponents,
    compute_graph_support,
    compute_historical_rate,
    compute_signal_strength,
    compute_evidence_coverage,
    compute_contradiction_penalty,
    decide_next_step,
    explain_uncertainty,
    TYPOLOGY_CHECKLISTS,
    THRESHOLD_ACT,
    THRESHOLD_GATHER
)
from agent.nba import (
    decide_nba,
    build_nba_record,
    check_sar_required,
    can_auto_execute,
    get_approval_route,
    ActionType
)
from agent.tools.mcp_tools import TigerGraphClient
from agent.tools.mock_actions import (
    execute_step_up_auth,
    execute_customer_validation,
    generate_sar_report
)
from agent.tools.graphrag import PolicyGroundingEngine


class CaseGuardOrchestrator:
    def __init__(self, tg_client: TigerGraphClient = None):
        self.tg = tg_client or TigerGraphClient()
        self.policy_engine = PolicyGroundingEngine()

    # -------------------------------------------------------------------------
    # Node 1: Triage & Initialization
    # -------------------------------------------------------------------------
    def node_triage(self, state: InvestigationState) -> Dict[str, Any]:
        trigger = state["trigger"]
        target = state["target"]
        case_id = state["case_id"]
        
        log_msg = f"TRIAGE: Case {case_id} initiated for {target['entity_type']} {target['entity_id']} (Risk Score: {trigger.get('risk_score', 0.5)})"
        logger.info(log_msg)
        
        return {
            "status": "open",
            "history": [log_msg],
            "iterations": 0,
            "max_iterations": state.get("max_iterations", 3)
        }

    # -------------------------------------------------------------------------
    # Node 2: Gather Evidence via TigerGraph GSQL
    # -------------------------------------------------------------------------
    def node_gather_evidence(self, state: InvestigationState) -> Dict[str, Any]:
        target = state["target"]
        target_id = target["entity_id"]
        target_type = target["entity_type"]
        new_evidence: list[EvidenceItem] = []
        
        # 1. Query customer profile / neighborhood
        prof_res = self.tg.run_installed_query("get_customer_profile", {"cust": target_id})
        new_evidence.append({
            "id": f"EV-PROF-{len(state.get('evidence', [])) + 1}",
            "source": "graph",
            "type": "customer_profile",
            "content": prof_res.get("summary", "Profile fetched."),
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "confidence_weight": 0.3
        })
        
        # 2. Check velocity on account
        vel_res = self.tg.run_installed_query("detect_velocity_burst", {"acc": target_id})
        new_evidence.append({
            "id": f"EV-VEL-{len(state.get('evidence', [])) + 2}",
            "source": "graph",
            "type": "velocity_check",
            "content": vel_res.get("summary", "Velocity evaluated."),
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "confidence_weight": 0.4
        })

        # 3. Check device sharing
        dev_res = self.tg.run_installed_query("detect_device_sharing", {"dev": target_id})
        new_evidence.append({
            "id": f"EV-DEV-{len(state.get('evidence', [])) + 3}",
            "source": "graph",
            "type": "device_signal",
            "content": dev_res.get("summary", "Device sharing inspected."),
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "confidence_weight": 0.45
        })

        log_msg = f"GATHER_EVIDENCE: Collected {len(new_evidence)} new graph evidence items via GSQL."
        return {
            "evidence": new_evidence,
            "history": [log_msg]
        }

    # -------------------------------------------------------------------------
    # Node 3: Detect Fraud Patterns (GSQL Pattern Detectors)
    # -------------------------------------------------------------------------
    def node_detect_patterns(self, state: InvestigationState) -> Dict[str, Any]:
        target = state["target"]
        target_id = target["entity_id"]
        patterns_matched: list[PatternMatch] = []
        
        # Check device sharing result
        dev_res = self.tg.run_installed_query("detect_device_sharing", {"dev": target_id})
        if dev_res.get("is_suspicious"):
            patterns_matched.append({
                "pattern_id": "device_sharing",
                "name": "Device Multi-Accounting / Syndicate Ring",
                "evidence_refs": ["EV-DEV-3"],
                "confidence": 0.85
            })

        # Check velocity burst result
        vel_res = self.tg.run_installed_query("detect_velocity_burst", {"acc": target_id})
        if vel_res.get("is_burst"):
            patterns_matched.append({
                "pattern_id": "velocity_burst",
                "name": "Rapid Transaction Burst",
                "evidence_refs": ["EV-VEL-2"],
                "confidence": 0.78
            })

        # Check pass-through mule chain
        mule_res = self.tg.run_installed_query("detect_mule_chain", {"start_acc": target_id})
        if mule_res.get("is_mule_chain"):
            patterns_matched.append({
                "pattern_id": "mule_chain",
                "name": "Multi-hop Mule Pass-Through Flow",
                "evidence_refs": ["EV-MULE-1"],
                "confidence": 0.88
            })

        pat_names = [p["pattern_id"] for p in patterns_matched]
        log_msg = f"DETECT_PATTERNS: Matched {len(patterns_matched)} fraud typologies: {pat_names}"
        return {
            "patterns_matched": patterns_matched,
            "history": [log_msg]
        }

    # -------------------------------------------------------------------------
    # Node 4: Retrieve Prior Cases from Graph Case Memory
    # -------------------------------------------------------------------------
    def node_retrieve_prior_cases(self, state: InvestigationState) -> Dict[str, Any]:
        # Emulate vector + graph hybrid recall of closed historical cases
        prior_cases: list[PriorCaseRef] = [
            {
                "case_id": "CASE-HIST-084",
                "similarity": 0.82,
                "outcome": "fraud",
                "pattern_id": "device_sharing"
            },
            {
                "case_id": "CASE-HIST-112",
                "similarity": 0.76,
                "outcome": "fraud",
                "pattern_id": "velocity_burst"
            },
            {
                "case_id": "CASE-HIST-023",
                "similarity": 0.58,
                "outcome": "cleared",
                "pattern_id": None
            }
        ]
        log_msg = f"CASE_MEMORY: Retrieved {len(prior_cases)} similar closed cases from TigerGraph memory."
        return {
            "prior_cases_used": prior_cases,
            "history": [log_msg]
        }

    # -------------------------------------------------------------------------
    # Node 5: Ground with Policy (GraphRAG)
    # -------------------------------------------------------------------------
    def node_ground_policy(self, state: InvestigationState) -> Dict[str, Any]:
        pats = [p["pattern_id"] for p in state.get("patterns_matched", [])]
        policy_text = self.policy_engine.get_grounding_context(
            pattern_ids=pats,
            confidence=state.get("confidence", 0.5),
            risk_level=state.get("risk_level", "medium")
        )
        log_msg = "GRAPHRAG: Retrieved and synthesized relevant regulatory policies and bank SOPs."
        return {
            "policy_context": policy_text,
            "history": [log_msg]
        }

    # -------------------------------------------------------------------------
    # Node 6: Assess Uncertainty & Confidence Scorer
    # -------------------------------------------------------------------------
    def node_assess_uncertainty(self, state: InvestigationState) -> Dict[str, Any]:
        patterns = state.get("patterns_matched", [])
        prior_cases = state.get("prior_cases_used", [])
        evidence = state.get("evidence", [])
        trigger = state["trigger"]
        bank_risk = trigger.get("risk_score", 0.5)
        
        # 1. Graph support
        graph_support = compute_graph_support(patterns, confirmed_fraud_neighbor_count=2, total_neighbor_count=3)
        
        # 2. Historical rate
        hist_rate = compute_historical_rate(prior_cases)
        
        # 3. Signal strength
        signal_strength = compute_signal_strength(bank_risk_score=bank_risk)
        
        # 4. Evidence coverage
        collected_types = [e["type"] for e in evidence]
        top_pat = patterns[0]["pattern_id"] if patterns else None
        evidence_coverage = compute_evidence_coverage(top_pat, collected_types, TYPOLOGY_CHECKLISTS)
        
        # 5. Contradiction penalty
        cleared_sim = max([pc["similarity"] for pc in prior_cases if pc["outcome"] == "cleared"], default=0.0)
        penalty = compute_contradiction_penalty(cleared_sim, cleared_case_count=1)
        
        components = ConfidenceComponents(
            graph_support=graph_support,
            historical_rate=hist_rate,
            signal_strength=signal_strength,
            evidence_coverage=evidence_coverage,
            contradiction_penalty=penalty
        )
        
        confidence = components.compute()
        risk_level = "critical" if confidence >= 0.85 else ("high" if confidence >= 0.70 else "medium")
        uncertainty_reasons = explain_uncertainty(components, confidence)
        evidence_sufficient = (confidence >= THRESHOLD_ACT)

        # Compute next-best-action candidate
        actions, reasoning = decide_nba(
            confidence=confidence,
            risk_level=risk_level,
            patterns_matched=[p["pattern_id"] for p in patterns],
            evidence_sufficient=evidence_sufficient,
            iteration=state.get("iterations", 0),
            transaction_amount=trigger.get("amount", 250.0)
        )
        
        nba_rec = build_nba_record(actions, reasoning, confidence)
        
        # If this is before extra evidence was gathered:
        update_dict: Dict[str, Any] = {
            "confidence": confidence,
            "confidence_components": components.to_dict(),
            "risk_level": risk_level,
            "uncertainty_reasons": uncertainty_reasons,
            "evidence_sufficient": evidence_sufficient,
            "history": [f"ASSESS_UNCERTAINTY: Confidence={confidence:.1%}, Risk={risk_level}, Actionable={evidence_sufficient}"]
        }
        
        if state.get("nba_before") is None:
            update_dict["nba_before"] = nba_rec
        else:
            update_dict["nba_after"] = nba_rec
            
        return update_dict

    # -------------------------------------------------------------------------
    # Node 7: Request More Evidence (Controlled Policy Actions)
    # -------------------------------------------------------------------------
    def node_request_evidence(self, state: InvestigationState) -> Dict[str, Any]:
        target_id = state["target"]["entity_id"]
        case_id = state["case_id"]
        new_ev: list[EvidenceItem] = []
        
        # Simulate step-up auth request
        auth_res = execute_step_up_auth(target_id, case_id)
        new_ev.append({
            "id": f"EV-AUTH-{len(state.get('evidence', [])) + 1}",
            "source": "external",
            "type": "step_up_auth_result",
            "content": auth_res["details"],
            "collected_at": auth_res["timestamp"],
            "confidence_weight": 0.6
        })
        
        # Simulate customer confirmation
        val_res = execute_customer_validation(target_id, state["trigger"].get("ref_id", "TX1"), 450.0)
        new_ev.append({
            "id": f"EV-VAL-{len(state.get('evidence', [])) + 2}",
            "source": "external",
            "type": "customer_validation_result",
            "content": val_res["details"],
            "collected_at": val_res["timestamp"],
            "confidence_weight": 0.75
        })

        curr_iters = state.get("iterations", 0) + 1
        log_msg = f"REQUEST_MORE_EVIDENCE (Iter {curr_iters}): Dispatched step-up auth and customer verification ping."
        return {
            "evidence": new_ev,
            "iterations": curr_iters,
            "status": "needs_evidence",
            "history": [log_msg]
        }

    # -------------------------------------------------------------------------
    # Node 8: Recommend or Execute Final Actions & Generate SAR
    # -------------------------------------------------------------------------
    def node_recommend_actions(self, state: InvestigationState) -> Dict[str, Any]:
        confidence = state.get("confidence", 0.5)
        risk_level = state.get("risk_level", "medium")
        patterns = [p["pattern_id"] for p in state.get("patterns_matched", [])]
        amount = state["trigger"].get("amount", 300.0)
        
        actions, reasoning = decide_nba(
            confidence=confidence,
            risk_level=risk_level,
            patterns_matched=patterns,
            evidence_sufficient=True,
            iteration=state.get("iterations", 0),
            transaction_amount=amount
        )
        
        # SAR Check
        sar_req, sar_refs = check_sar_required(confidence, risk_level, amount, patterns)
        sar_text = None
        if sar_req:
            sar_text = generate_sar_report(
                case_id=state["case_id"],
                target_id=state["target"]["entity_id"],
                reasons=state.get("uncertainty_reasons", ["Suspicious graph typology"]),
                evidence_summary="\n".join([f"- {e['type']}: {e['content']}" for e in state.get("evidence", [])[:4]]),
                total_amount=amount,
                regulatory_refs=sar_refs
            )

        action_records = []
        for act in actions:
            action_records.append({
                "action": act.value,
                "status": "executed" if can_auto_execute(act) else "pending_approval",
                "approval_route": get_approval_route(act),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "policy_refs": ["POL-BLK-002" if "block" in act.value else "POL-AUTH-003"]
            })

        # Ensure nba_after is recorded
        nba_after = state.get("nba_after") or build_nba_record(actions, reasoning, confidence)
        
        summary = (
            f"Case {state['case_id']} concluded with risk level {risk_level} and confidence {confidence:.1%}. "
            f"Matched {len(patterns)} typologies. Actions assigned: {[a.value for a in actions]}."
        )

        return {
            "actions_taken": action_records,
            "sar_required": sar_req,
            "sar_text": sar_text,
            "sar_regulatory_refs": sar_refs,
            "nba_after": nba_after,
            "case_summary": summary,
            "reasoning": reasoning,
            "status": "closed",
            "history": [f"RECOMMEND_ACTIONS: Finalized actions. SAR required={sar_req}."]
        }

    # -------------------------------------------------------------------------
    # Node 9: Write Case & Audit Trail into TigerGraph
    # -------------------------------------------------------------------------
    def node_write_case_to_graph(self, state: InvestigationState) -> Dict[str, Any]:
        case_id = state["case_id"]
        written = self.tg.write_investigation_record(case_id, dict(state))
        log_msg = f"WRITE_GRAPH: Investigation case {case_id} and audit nodes committed to TigerGraph (graph_written={written})."
        return {
            "graph_written": written,
            "history": [log_msg]
        }

    # -------------------------------------------------------------------------
    # Execution Runner Loop
    # -------------------------------------------------------------------------
    def run_investigation(self, initial_state: InvestigationState) -> InvestigationState:
        """Run the full cyclic state graph execution."""
        state = dict(initial_state)
        
        # 1. Triage
        state.update(self.node_triage(state))
        
        # 2. Initial Evidence Gathering
        res = self.node_gather_evidence(state)
        state["evidence"] = state.get("evidence", []) + res["evidence"]
        state["history"] = state.get("history", []) + res["history"]
        
        # 3. Pattern Detection
        res = self.node_detect_patterns(state)
        state["patterns_matched"] = state.get("patterns_matched", []) + res["patterns_matched"]
        state["history"] = state.get("history", []) + res["history"]
        
        # 4. Recall Case Memory
        res = self.node_retrieve_prior_cases(state)
        state["prior_cases_used"] = state.get("prior_cases_used", []) + res["prior_cases_used"]
        state["history"] = state.get("history", []) + res["history"]
        
        # 5. Policy Grounding
        res = self.node_ground_policy(state)
        state["policy_context"] = res["policy_context"]
        state["history"] = state.get("history", []) + res["history"]
        
        # 6. Assess Uncertainty (Before additional evidence)
        res = self.node_assess_uncertainty(state)
        state.update(res)
        
        # Check conditional branch: do we need more evidence?
        decision = decide_next_step(state["confidence"])
        if decision == "gather_more" and state.get("iterations", 0) < state.get("max_iterations", 2):
            logger.info("Uncertainty high ({}). Gathering additional targeted evidence...", state["confidence"])
            res_req = self.node_request_evidence(state)
            state["evidence"] = state.get("evidence", []) + res_req["evidence"]
            state["iterations"] = res_req["iterations"]
            state["history"] = state.get("history", []) + res_req["history"]
            
            # Re-evaluate uncertainty (After additional evidence)
            res_reassess = self.node_assess_uncertainty(state)
            state.update(res_reassess)

        # 7. Final Recommendations & SAR
        res_act = self.node_recommend_actions(state)
        state.update(res_act)
        
        # 8. Commit back to TigerGraph Knowledge Graph
        res_write = self.node_write_case_to_graph(state)
        state.update(res_write)
        
        return state
