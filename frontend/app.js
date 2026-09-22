// ==========================================================================
// CaseGuard — Hacker House Goa UI Controller
// Lightweight, clean, zero external dependencies
// ==========================================================================

let casesData = [];
let selectedCaseIndex = 0;
let currentStep = 1;

// Elements
const casePillsContainer = document.getElementById("casePillsContainer");
const activeCaseTitleDisplay = document.getElementById("activeCaseTitleDisplay");
const activeCaseSubDisplay = document.getElementById("activeCaseSubDisplay");

// Init
async function init() {
  setupStepper();
  try {
    const res = await fetch("data/cases.json");
    casesData = await res.json();
    renderPills();
    selectCase(0);
  } catch (err) {
    console.error("Failed to load cases data:", err);
    activeCaseTitleDisplay.textContent = "Error loading cases";
  }
}

// Stepper setup
function setupStepper() {
  const stepButtons = document.querySelectorAll(".step-item");
  stepButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const step = parseInt(btn.getAttribute("data-step"), 10);
      goToStep(step);
    });
  });
}

function goToStep(stepNum) {
  currentStep = stepNum;

  // Update Stepper Navigation buttons
  document.querySelectorAll(".step-item").forEach((btn) => {
    const s = parseInt(btn.getAttribute("data-step"), 10);
    if (s === stepNum) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // Switch Active Step View
  document.querySelectorAll(".step-view").forEach((view, idx) => {
    if (idx + 1 === stepNum) {
      view.classList.add("active-view");
    } else {
      view.classList.remove("active-view");
    }
  });
}

// Render 20 benchmark case pills
function renderPills() {
  casePillsContainer.innerHTML = "";
  casesData.forEach((c, index) => {
    const pill = document.createElement("button");
    pill.className = `case-select-pill ${index === selectedCaseIndex ? "selected" : ""}`;
    pill.textContent = c.case_id.replace("CASE-BENCHMARK-", "CASE ");
    pill.addEventListener("click", () => selectCase(index));
    casePillsContainer.appendChild(pill);
  });
}

// Select Case & Populate details
function selectCase(index) {
  selectedCaseIndex = index;
  const current = casesData[index];
  if (!current) return;

  // Update selected pill style
  document.querySelectorAll(".case-select-pill").forEach((p, idx) => {
    if (idx === index) {
      p.classList.add("selected");
    } else {
      p.classList.remove("selected");
    }
  });

  const record = current.investigation_record;
  const target = record.target;
  const trigger = current.trigger;
  const risk = record.risk_assessment;
  const comp = risk.confidence_components || {};
  const nba = current.next_best_action;
  const sar = current.sar || {};

  // Step 1: Dropzone Box
  activeCaseTitleDisplay.textContent = `${current.case_id} Loaded`;
  activeCaseSubDisplay.textContent = `Target: ${target.entity_type} ${target.entity_id} — Risk Score: ${(trigger.risk_score || 0).toFixed(2)}`;

  // Step 2: Evidence Trail
  document.getElementById("step2TargetBadge").textContent = `${target.entity_type} ${target.entity_id}`;
  document.getElementById("step2TriggerType").textContent = trigger.type || "Alert";
  document.getElementById("step2RiskScore").textContent = (trigger.risk_score || 0).toFixed(2);

  const matchedPats = (record.patterns_matched || []).map((p) => p.name).join(", ");
  document.getElementById("step2MatchedTypologies").textContent = matchedPats || "No High-Confidence Pattern";

  const evContainer = document.getElementById("step2EvidenceList");
  evContainer.innerHTML = "";
  (record.evidence_gathered || []).slice(0, 4).forEach((ev) => {
    const div = document.createElement("div");
    div.style.cssText = "font-size:0.8rem; color: var(--text-headline); background: rgba(0,0,0,0.03); padding:8px 12px; border-radius: 6px; border-left: 3px solid var(--forest-green);";
    div.textContent = `• [${ev.type}] ${ev.content}`;
    evContainer.appendChild(div);
  });

  // Step 3: Uncertainty
  const confPct = Math.round((risk.confidence || 0) * 100);
  document.getElementById("step3ConfBadge").textContent = `CONFIDENCE: ${confPct}%`;
  document.getElementById("step3GraphSupport").textContent = (comp.graph_support || 0).toFixed(2);
  document.getElementById("step3HistRate").textContent = (comp.historical_rate || 0).toFixed(2);
  document.getElementById("step3SignalStrength").textContent = (comp.signal_strength || 0).toFixed(2);
  document.getElementById("step3Coverage").textContent = (comp.evidence_coverage || 0).toFixed(2);

  const reasonsList = document.getElementById("step3ReasonsList");
  reasonsList.innerHTML = "";
  (risk.uncertainty_reasons || []).forEach((r) => {
    const p = document.createElement("div");
    p.style.margin = "4px 0";
    p.textContent = `• ${r}`;
    reasonsList.appendChild(p);
  });

  // Step 4: Next Best Action & SAR
  const before = nba.before_additional_evidence || {};
  document.getElementById("step4NbaBeforeAction").textContent = before.primary_action || "allow_transaction";
  document.getElementById("step4NbaBeforeReason").textContent = before.reasoning || "Initial step evaluated.";

  const after = nba.after_additional_evidence || {};
  document.getElementById("step4NbaAfterAction").textContent = after.primary_action || before.primary_action || "allow_transaction";
  document.getElementById("step4NbaAfterReason").textContent = after.reasoning || before.reasoning || "Evidence received.";

  document.getElementById("step4SarStatusBadge").textContent = sar.required ? "SAR REQUIRED" : "SAR NOT REQUIRED";
  document.getElementById("step4SarTextDisplay").textContent = sar.required ? (sar.text || "Generating SAR...") : "Transaction risk falls below mandatory regulatory filing thresholds.";
}

window.addEventListener("DOMContentLoaded", init);
