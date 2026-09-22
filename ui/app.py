"""
CaseGuard - Streamlit Fraud Investigation Dashboard
Interactive Analyst UI demonstrating:
- Live Case Pipeline & Progression
- Multi-Hop Subgraph Topology Visualization
- Dynamic Uncertainty & Confidence Meter
- Next-Best-Action (NBA) Panel (Before vs. After Additional Evidence)
- Human-in-the-Loop Approval Queue (L1/L2 Analyst & Compliance)
- Full FinCEN SAR Generator & Review
"""
import os
import json
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="CaseGuard | TigerGraph Agentic Fraud Investigation",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1E88E5;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85em;
    }
    .badge-critical { background: #ffebee; color: #c62828; }
    .badge-high { background: #fff3e0; color: #ef6c00; }
    .badge-medium { background: #e8f5e9; color: #2e7d32; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ CaseGuard: TigerGraph Agentic Fraud Investigator")
st.caption("TigerGraph HHGOA Hackathon · Uncertainty-Gated Investigation & Next-Best-Action Engine")

# Load Cases
CASES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "cases"))

@st.cache_data
def load_all_cases():
    cases = []
    if not os.path.exists(CASES_DIR):
        return []
    for f in sorted(os.listdir(CASES_DIR)):
        if f.endswith(".json"):
            with open(os.path.join(CASES_DIR, f), "r") as fp:
                cases.append(json.load(fp))
    return cases

cases = load_all_cases()

if not cases:
    st.error("No case files found. Please run `python3 scripts/run_benchmark.py` first.")
    st.stop()

# Sidebar: Case Navigation & Controls
st.sidebar.header("Investigation Cases")
case_ids = [c["case_id"] for c in cases]
selected_case_id = st.sidebar.selectbox("Select Case to Inspect:", case_ids, index=0)

selected_case = next(c for c in cases if c["case_id"] == selected_case_id)
trigger = selected_case["trigger"]
record = selected_case["investigation_record"]
risk = record["risk_assessment"]
nba = selected_case["next_best_action"]

# Top Metrics Row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Trigger Type", trigger.get("type", "N/A"))
with col2:
    st.metric("Bank Risk Score", f"{trigger.get('risk_score', 0.0):.2f}")
with col3:
    conf = risk.get("confidence", 0.0)
    st.metric("Agent Confidence", f"{conf:.1%}")
with col4:
    r_level = risk.get("risk_level", "medium").upper()
    st.metric("Assessed Risk", r_level)
with col5:
    st.metric("Graph Persisted", "✅ True" if selected_case.get("graph_written") else "❌ False")

st.divider()

# Main Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Next Best Action (NBA)",
    "🔎 Evidence & Lineage",
    "📊 Uncertainty Engine Breakdown",
    "⚖️ Human Approval Queue",
    "📜 SAR Regulatory Dossier"
])

# -----------------------------------------------------------------------------
# TAB 1: Next-Best-Action (Before & After Evidence)
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Next-Best-Action Decision Progression")
    st.info("💡 Crucial Evaluation Requirement: The agent evaluates and logs NBA **before** requesting additional evidence and re-evaluates **after** acquiring targeted signals.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### 1️⃣ NBA: Before Additional Evidence")
        before = nba.get("before_additional_evidence") or {}
        if before:
            st.success(f"**Primary Recommendation:** `{before.get('primary_action')}`")
            st.write(f"**Approval Route:** `{before.get('approval_route')}`")
            st.write(f"**Confidence at Time:** `{before.get('confidence_at_time', 0.0):.1%}`")
            st.write(f"**Rationale:** {before.get('reasoning')}")
            st.json(before.get("all_actions", []))
        else:
            st.write("No before-state recorded.")

    with col_b:
        st.markdown("### 2️⃣ NBA: After Additional Evidence")
        after = nba.get("after_additional_evidence") or {}
        if after:
            st.success(f"**Final Recommendation:** `{after.get('primary_action')}`")
            st.write(f"**Approval Route:** `{after.get('approval_route')}`")
            st.write(f"**Confidence at Time:** `{after.get('confidence_at_time', 0.0):.1%}`")
            st.write(f"**Rationale:** {after.get('reasoning')}")
            st.json(after.get("all_actions", []))
        else:
            st.write("No subsequent evidence required.")

    st.markdown("### Executed & Assigned Actions")
    st.dataframe(pd.DataFrame(selected_case.get("actions_taken", [])))

# -----------------------------------------------------------------------------
# TAB 2: Evidence & Graph Lineage
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Gathered Graph Evidence & Pattern Lineage")
    
    ev_list = record.get("evidence_gathered", [])
    if ev_list:
        ev_df = pd.DataFrame(ev_list)
        st.dataframe(ev_df[["id", "source", "type", "confidence_weight", "content"]], use_container_width=True)
    
    st.markdown("#### Matched Fraud Typologies (GSQL Detectors)")
    pats = record.get("patterns_matched", [])
    if pats:
        for p in pats:
            st.warning(f"🚨 **{p.get('name')}** (`{p.get('pattern_id')}`) — Confidence: {p.get('confidence', 0.0):.1%}")
    else:
        st.success("No documented high-confidence fraud typologies matched.")

    st.markdown("#### Case Memory: Retrieved Closed Investigations")
    priors = record.get("prior_cases_used", [])
    if priors:
        st.dataframe(pd.DataFrame(priors), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 3: Uncertainty Engine Breakdown
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Quantitative Uncertainty & Confidence Decomposition")
    comp = risk.get("confidence_components", {})
    
    if comp:
        cols = st.columns(4)
        cols[0].metric("Graph Support (w=0.35)", f"{comp.get('graph_support', 0.0):.2f}")
        cols[1].metric("Historical Rate (w=0.25)", f"{comp.get('historical_rate', 0.0):.2f}")
        cols[2].metric("Signal Strength (w=0.25)", f"{comp.get('signal_strength', 0.0):.2f}")
        cols[3].metric("Evidence Coverage (w=0.15)", f"{comp.get('evidence_coverage', 0.0):.2f}")

        st.caption(f"Contradiction Penalty (Cleared Case Resemblance): -{comp.get('contradiction_penalty', 0.0):.2f}")
        st.progress(float(comp.get("final", 0.5)))
    
    st.markdown("#### Uncertainty Attribution Reasons")
    for r in risk.get("uncertainty_reasons", []):
        st.markdown(f"- ⚠️ {r}")

# -----------------------------------------------------------------------------
# TAB 4: Human-in-the-Loop Approval Queue
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("Policy-Gated Human Approval Queue")
    st.markdown("Enforces institution guardrails: High-impact actions (account locks, SAR filing) require explicit human sign-off.")
    
    acts_requiring_approval = [a for a in selected_case.get("actions_taken", []) if a.get("status") == "pending_approval"]
    
    if acts_requiring_approval:
        for a in acts_requiring_approval:
            with st.expander(f"Pending Action: {a.get('action').upper()} ({a.get('approval_route')})", expanded=True):
                st.write(f"Policy Reference: {a.get('policy_refs')}")
                col_x, col_y = st.columns(2)
                if col_x.button(f"Approve {a.get('action')}", key=f"app_{a.get('action')}"):
                    st.success(f"Action {a.get('action')} Approved and Executed into Core Banking.")
                if col_y.button(f"Reject & Dismiss", key=f"rej_{a.get('action')}"):
                    st.error(f"Action {a.get('action')} Dismissed by Analyst.")
    else:
        st.success("No actions pending human sign-off for this case. All approved actions are auto-executable.")

# -----------------------------------------------------------------------------
# TAB 5: SAR Regulatory Dossier
# -----------------------------------------------------------------------------
with tab5:
    st.subheader("Suspicious Activity Report (FinCEN Compliance)")
    sar_data = selected_case.get("sar", {})
    if sar_data.get("required"):
        st.warning("⚠️ Mandatory SAR Filing Triggered under BSA/AML Policy & 31 CFR 1020.320")
        st.code(sar_data.get("text", "No draft generated."), language="markdown")
    else:
        st.info("SAR filing not mandated for this case under current risk and transaction volume thresholds.")
