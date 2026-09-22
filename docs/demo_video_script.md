# CaseGuard Demo Video Script (3-5 Minutes)

**Target Duration:** ~3 minutes 45 seconds  
**Objective:** Clean, convincing demonstration directly addressing every judging rubric category (Accuracy 25%, NBA 25%, Explainability 10%, Engineering 15%, Innovation 15%, Demo 10%).

---

### [00:00 - 00:30] Introduction & The Big Idea
- **Visual:** Split screen: Slide showing "An investigator that knows what it doesn't know" and the Streamlit UI dashboard.
- **Voiceover:** 
  > "Hi everyone! This is CaseGuard, built for the TigerGraph Agentic Fraud Investigation Hackathon. Most teams build an agent that answers a simple binary question: 'is this fraud?'. We built an agent that answers: 'how confident am I, what is the cheapest piece of evidence that reduces my uncertainty, and what next-best action is defensible right now?'"

---

### [00:30 - 01:15] GSQL Graph Analytics in TigerGraph
- **Visual:** Switch to TigerGraph schema diagram / GSQL code (`detect_device_sharing.gsql`, `detect_velocity_burst.gsql`).
- **Voiceover:**
  > "CaseGuard does not use the LLM to do graph traversal. All topology queries and pattern detectors are compiled directly into native GSQL inside TigerGraph. We detect multi-accounting device syndicates, card velocity spikes, and multi-hop mule layering in single-digit milliseconds. The agent accesses these capabilities via TigerGraph MCP tools."

---

### [01:15 - 02:05] The Uncertainty Engine & The NBA Loop (Crucial 50%)
- **Visual:** Select `CASE-BENCHMARK-001` in the Streamlit UI. Open Tab 1 ("Next Best Action") and Tab 3 ("Uncertainty Engine Breakdown").
- **Voiceover:**
  > "Notice here in Case 1: the trigger bank risk score was 0.88, but our Uncertainty Engine computed an overall confidence of only 48.1%. Why? Because our GSQL query found our evidence checklist was incomplete, and the behavior partially resembled cleared historical cases.
  > Instead of abruptly blocking the account, our Next-Best-Action engine recorded the **NBA Before Evidence**: auto-execute step-up authentication and monitor the account. 
  > The agent then dispatched a simulated 2FA challenge and customer verification ping, received the new signal, and re-evaluated the **NBA After Evidence**."

---

### [02:05 - 02:50] Human-in-the-Loop Governance & SAR Filing
- **Visual:** Open Tab 4 ("Human Approval Queue") and Tab 5 ("SAR Regulatory Dossier").
- **Voiceover:**
  > "CaseGuard enforces a hardcoded permission matrix. High-impact operations like freezing accounts or canceling payments cannot be auto-executed by AI alone. They are parked here in our Analyst Queue for L1 and L2 review. 
  > Furthermore, under Bank Secrecy Act rules and 31 CFR 1020.320, our GraphRAG compliance engine detected that this high-volume pattern warrants a mandatory Suspicious Activity Report, which the agent formatted automatically into a FinCEN-compliant dossier."

---

### [02:50 - 03:30] Case Memory & Benchmark Delivery
- **Visual:** Show the `output/cases/` folder with 20 JSON answer files and Tab 2 showing retrieved prior cases (`CASE-HIST-084`).
- **Voiceover:**
  > "Every investigation is written back into the TigerGraph database with `graph_written: true`. When new cases arrive, CaseGuard queries this case memory to calibrate future confidence scores. 
  > We have verified and generated all 20 benchmark answer files strictly complying with the hackathon specification."

---

### [03:30 - 03:45] Conclusion & Call to Action
- **Visual:** GitHub repository and architecture diagram.
- **Voiceover:**
  > "CaseGuard turns uncertain fraud signals into defensible, auditable action. Check out our open-source repo and technical blog post. Thank you!"
