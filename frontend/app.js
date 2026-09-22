// ==========================================================================
// CaseGuard - Frontend Interactive Controller
// Manages Case Selection, Glassmorphism Tabs, and Dynamic Data Binding
// ==========================================================================

let casesData = [];
let selectedCase = null;

// DOM Elements
const casesListContainer = document.getElementById("casesListContainer");
const caseCountBadge = document.getElementById("caseCountBadge");

// Hero Stats
const statTargetId = document.getElementById("statTargetId");
const statTargetType = document.getElementById("statTargetType");
const statRiskScore = document.getElementById("statRiskScore");
const statTriggerReason = document.getElementById("statTriggerReason");
const statConfidence = document.getElementById("statConfidence");
const statRiskLevel = document.getElementById("statRiskLevel");

// NBA Elements
const nbaBeforeAction = document.getElementById("nbaBeforeAction");
const nbaBeforeRoute = document.getElementById("nbaBeforeRoute");
const nbaBeforeConfidence = document.getElementById("nbaBeforeConfidence");
const nbaBeforeReasoning = document.getElementById("nbaBeforeReasoning");

const nbaAfterAction = document.getElementById("nbaAfterAction");
const nbaAfterRoute = document.getElementById("nbaAfterRoute");
const nbaAfterConfidence = document.getElementById("nbaAfterConfidence");
const nbaAfterReasoning = document.getElementById("nbaAfterReasoning");

const actionsTableBody = document.getElementById("actionsTableBody");

// Uncertainty Elements
const uncertaintyScoreText = document.getElementById("uncertaintyScoreText");
const confidenceBarFill = document.getElementById("confidenceBarFill");
const compGraphSupport = document.getElementById("compGraphSupport");
const compHistRate = document.getElementById("compHistRate");
const compSignalStrength = document.getElementById("compSignalStrength");
const compEvidenceCoverage = document.getElementById("compEvidenceCoverage");
const uncertaintyReasonsList = document.getElementById("uncertaintyReasonsList");

// Evidence Elements
const evidenceTableBody = document.getElementById("evidenceTableBody");
const matchedPatternsContainer = document.getElementById("matchedPatternsContainer");
const caseMemoryContainer = document.getElementById("caseMemoryContainer");

// Approval & SAR
const approvalQueueContainer = document.getElementById("approvalQueueContainer");
const sarDossierContent = document.getElementById("sarDossierContent");
const sarStatusBadge = document.getElementById("sarStatusBadge");

// Initialize application
async function initApp() {
  setupTabs();
  try {
    const res = await fetch("data/cases.json");
    casesData = await res.json();
    caseCountBadge.textContent = `${casesData.length} Cases`;
    renderCasesList();
    if (casesData.length > 0) {
      selectCase(casesData[0].case_id);
    }
  } catch (err) {
    console.error("Failed loading cases data:", err);
    casesListContainer.innerHTML = `<div style="padding: 12px; color: var(--accent-rose)">Failed loading cases. Run export first.</div>`;
  }
}

// Setup Glassmorphic Tabs
function setupTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  const panels = document.querySelectorAll(".tab-panel");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      panels.forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add("active");
      }
    });
  });
}

// Render Sidebar Cases
function renderCasesList() {
  casesListContainer.innerHTML = "";
  casesData.forEach((c) => {
    const risk = c.investigation_record.risk_assessment;
    const btn = document.createElement("button");
    btn.className = `case-card-btn ${selectedCase && selectedCase.case_id === c.case_id ? "active" : ""}`;
    btn.setAttribute("data-id", c.case_id);

    const rLevel = (risk.risk_level || "medium").toLowerCase();
    const tagClass = rLevel === "critical" ? "risk-critical" : rLevel === "high" ? "risk-high" : "risk-medium";

    btn.innerHTML = `
      <div class="case-card-header">
        <span class="case-card-title">${c.case_id}</span>
        <span class="risk-tag ${tagClass}">${risk.risk_level || "MEDIUM"}</span>
      </div>
      <div class="case-card-meta">
        <span>${c.investigation_record.target.entity_type}: ${c.investigation_record.target.entity_id}</span>
        <span>Score: ${(c.trigger.risk_score || 0).toFixed(2)}</span>
      </div>
    `;

    btn.addEventListener("click", () => selectCase(c.case_id));
    casesListContainer.appendChild(btn);
  });
}

// Select and Display a Specific Case
function selectCase(caseId) {
  selectedCase = casesData.find((c) => c.case_id === caseId);
  if (!selectedCase) return;

  // Update active state in sidebar
  document.querySelectorAll(".case-card-btn").forEach((btn) => {
    if (btn.getAttribute("data-id") === caseId) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  const record = selectedCase.investigation_record;
  const target = record.target;
  const trigger = selectedCase.trigger;
  const risk = record.risk_assessment;
  const nba = selectedCase.next_best_action;
  const comp = risk.confidence_components || {};

  // 1. Top Hero Stats
  statTargetId.textContent = target.entity_id;
  statTargetType.textContent = `Type: ${target.entity_type}`;
  statRiskScore.textContent = (trigger.risk_score || 0).toFixed(2);
  statTriggerReason.textContent = trigger.reason || "Alert Flag";

  const confPct = Math.round((risk.confidence || 0) * 100);
  statConfidence.textContent = `${confPct}%`;
  statRiskLevel.textContent = `Risk: ${(risk.risk_level || "MEDIUM").toUpperCase()}`;

  // 2. Next Best Action (Before & After)
  const before = nba.before_additional_evidence || {};
  nbaBeforeAction.textContent = before.primary_action || "allow_transaction";
  nbaBeforeRoute.textContent = before.approval_route || "auto";
  nbaBeforeConfidence.textContent = `${Math.round((before.confidence_at_time || 0) * 100)}%`;
  nbaBeforeReasoning.textContent = before.reasoning || "No initial reasoning available.";

  const after = nba.after_additional_evidence || {};
  nbaAfterAction.textContent = after.primary_action || before.primary_action || "allow_transaction";
  nbaAfterRoute.textContent = after.approval_route || before.approval_route || "auto";
  nbaAfterConfidence.textContent = `${Math.round((after.confidence_at_time || before.confidence_at_time || 0) * 100)}%`;
  nbaAfterReasoning.textContent = after.reasoning || before.reasoning || "Sufficient evidence collected.";

  // Actions Table
  actionsTableBody.innerHTML = "";
  (selectedCase.actions_taken || []).forEach((act) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td style="font-family: var(--font-mono); font-weight: 600;">${act.action}</td>
      <td><span class="pill-badge ${act.status === 'executed' ? 'active' : ''}">${act.status}</span></td>
      <td><code>${act.approval_route}</code></td>
      <td style="color: var(--text-muted); font-size: 0.75rem;">${new Date(act.timestamp).toLocaleTimeString()}</td>
      <td>${act.policy_refs ? act.policy_refs.join(", ") : "POL-AUTH-003"}</td>
    `;
    actionsTableBody.appendChild(row);
  });

  // 3. Uncertainty Breakdown
  uncertaintyScoreText.textContent = `${confPct}%`;
  confidenceBarFill.style.width = `${confPct}%`;

  compGraphSupport.textContent = (comp.graph_support || 0).toFixed(2);
  compHistRate.textContent = (comp.historical_rate || 0).toFixed(2);
  compSignalStrength.textContent = (comp.signal_strength || 0).toFixed(2);
  compEvidenceCoverage.textContent = (comp.evidence_coverage || 0).toFixed(2);

  uncertaintyReasonsList.innerHTML = "";
  (risk.uncertainty_reasons || []).forEach((reason) => {
    const item = document.createElement("div");
    item.style.cssText = "background: rgba(255,255,255,0.03); padding: 10px 14px; border-radius: 8px; border-left: 3px solid #f59e0b; font-size: 0.85rem;";
    item.textContent = `⚠️ ${reason}`;
    uncertaintyReasonsList.appendChild(item);
  });

  // 4. Evidence Trail Table
  evidenceTableBody.innerHTML = "";
  (record.evidence_gathered || []).forEach((ev) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td style="font-family: var(--font-mono); font-weight: 700; color: #818cf8;">${ev.id}</td>
      <td><span class="pill-badge">${ev.source}</span></td>
      <td><code>${ev.type}</code></td>
      <td><strong>${ev.confidence_weight || 0.4}</strong></td>
      <td>${ev.content}</td>
    `;
    evidenceTableBody.appendChild(row);
  });

  // Patterns
  matchedPatternsContainer.innerHTML = "";
  (record.patterns_matched || []).forEach((p) => {
    const card = document.createElement("div");
    card.className = "clay-stat-card";
    card.style.padding = "14px";
    card.innerHTML = `
      <div class="clay-stat-label">Typology Match</div>
      <div style="font-weight: 700; color: #f43f5e; margin: 4px 0;">${p.name}</div>
      <div style="font-size: 0.75rem; color: var(--text-secondary);">Pattern: ${p.pattern_id} | Confidence: ${Math.round((p.confidence || 0) * 100)}%</div>
    `;
    matchedPatternsContainer.appendChild(card);
  });

  // Case Memory
  caseMemoryContainer.innerHTML = "";
  (record.prior_cases_used || []).forEach((pc) => {
    const card = document.createElement("div");
    card.className = "clay-stat-card";
    card.style.padding = "14px";
    card.innerHTML = `
      <div class="clay-stat-label">Historical Case Recall</div>
      <div style="font-weight: 700; color: #38bdf8; margin: 4px 0;">${pc.case_id}</div>
      <div style="font-size: 0.75rem; color: var(--text-secondary);">Outcome: <strong>${pc.outcome.toUpperCase()}</strong> | Similarity: ${Math.round((pc.similarity || 0) * 100)}%</div>
    `;
    caseMemoryContainer.appendChild(card);
  });

  // 5. Human Approval Queue
  approvalQueueContainer.innerHTML = "";
  const pendingActions = (selectedCase.actions_taken || []).filter((a) => a.status === "pending_approval");
  if (pendingActions.length === 0) {
    approvalQueueContainer.innerHTML = `
      <div style="padding: 24px; text-align: center; color: #34d399; background: rgba(16,185,129,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: var(--radius-lg);">
        ✅ All recommended actions for this case are auto-executable. No human analyst approval is pending.
      </div>
    `;
  } else {
    pendingActions.forEach((act) => {
      const card = document.createElement("div");
      card.className = "approval-card";
      card.innerHTML = `
        <div>
          <div style="font-weight: 800; font-size: 1.05rem; font-family: var(--font-mono); color: #fbbf24;">${act.action.toUpperCase()}</div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">Approval Route: <strong>${act.approval_route}</strong> | Policy: ${act.policy_refs ? act.policy_refs.join(", ") : 'POL-BLK-002'}</div>
        </div>
        <div style="display: flex; gap: 10px;">
          <button class="clay-btn clay-btn-primary" onclick="alert('Action approved by Analyst and executed in core banking.')">Approve</button>
          <button class="clay-btn clay-btn-danger" onclick="alert('Action declined.')">Reject</button>
        </div>
      `;
      approvalQueueContainer.appendChild(card);
    });
  }

  // 6. SAR
  const sar = selectedCase.sar || {};
  if (sar.required) {
    sarStatusBadge.textContent = "Mandatory Filing Triggered";
    sarStatusBadge.style.color = "#fb7185";
    sarStatusBadge.style.borderColor = "rgba(244,63,94,0.4)";
    sarDossierContent.textContent = sar.text || "Generating regulatory dossier...";
  } else {
    sarStatusBadge.textContent = "Not Required";
    sarStatusBadge.style.color = "#34d399";
    sarStatusBadge.style.borderColor = "rgba(16,185,129,0.4)";
    sarDossierContent.textContent = "SAR filing not required for this case under current transaction thresholds.";
  }
}

// Run on page load
window.addEventListener("DOMContentLoaded", initApp);
