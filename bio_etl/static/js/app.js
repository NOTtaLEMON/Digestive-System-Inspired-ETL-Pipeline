/**
 * Bio-mimetic Digestive System ETL Pipeline
 * Enterprise Light-Theme Animation Engine & Multi-Bolus Controller
 */

// Global State
let currentSessionId = null;
let eventQueue = [];
let eventIndex = 0;
let isPaused = false;
let playbackSpeed = 1.0;
let totalPipelineChunks = 0;
let activeQuarantinedList = [];
let currentModalQuarantineIdx = 0;

let pipelineConfig = {
  file_source: "server_file",
  server_filename: "short_messy_health_data.csv",
  bp_format: "slash",
  date_format: "YYYY-MM-DD",
  chunk_size_mode: "auto",
  manual_chunk_size: 25,
  column_priorities: {},
  enable_ai_agent: true,
  auto_approve_quarantine: false
};

// 20 Distinct Enterprise Colors for Boluses
const BOLUS_COLORS = [
  "#0284c7", "#059669", "#d97706", "#7c3aed", "#e11d48", 
  "#0891b2", "#16a34a", "#ea580c", "#9333ea", "#db2777",
  "#2563eb", "#10b981", "#f59e0b", "#6366f1", "#f43f5e",
  "#0d9488", "#4f46e5", "#047857", "#c026d3", "#b45309"
];

// Organ coordinates on SVG canvas for the moving food boluses
const ORGAN_COORDS = {
  mouth: { cx: 270, cy: 60, name: "Mouth (Mastication)", badgeColor: "#e11d48" },
  esophagus: { cx: 265, cy: 130, name: "Esophagus (Peristalsis)", badgeColor: "#f43f5e" },
  stomach: { cx: 240, cy: 245, name: "Stomach (Acid Dissolution)", badgeColor: "#059669" },
  liver: { cx: 355, cy: 215, name: "Liver (Detoxification & Bile)", badgeColor: "#d97706" },
  immune: { cx: 270, cy: 330, name: "Immune System (WBC Threat Scan)", badgeColor: "#dc2626" },
  duodenum: { cx: 270, cy: 365, name: "Duodenum (Absorption Queue)", badgeColor: "#0284c7" },
  small_intestine: { cx: 270, cy: 440, name: "Small Intestine (Villi Absorption)", badgeColor: "#0284c7" },
  bloodstream: { cx: 70, cy: 640, name: "Bloodstream (Metabolism Vault)", badgeColor: "#0284c7" },
  large_intestine: { cx: 270, cy: 635, name: "Large Intestine (Colon Ejection)", badgeColor: "#7c3aed" }
};

// DOM Elements
const stageBadge = document.getElementById("current-organ-badge");
const bolusesContainer = document.getElementById("boluses-container");
const logStream = document.getElementById("activity-log-stream");
const configModal = document.getElementById("config-modal");
const quarantineModal = document.getElementById("quarantine-confirm-modal");
const quickFileSelector = document.getElementById("quick-file-selector");
const ctrlAiToggle = document.getElementById("ctrl-ai-toggle");

// KPI elements
const kpiMouth = document.getElementById("kpi-mouth");
const kpiStomach = document.getElementById("kpi-stomach");
const kpiLiver = document.getElementById("kpi-liver");
const kpiThreats = document.getElementById("kpi-threats");
const kpiQuarantine = document.getElementById("kpi-quarantine");
const kpiAbsorbed = document.getElementById("kpi-absorbed");
const kpiExcreted = document.getElementById("kpi-excreted");

// Counters
let counts = {
  mouthBoluses: 0,
  stomachChars: 0,
  liverFields: 0,
  threats: 0,
  quarantine: 0,
  absorbed: 0,
  excreted: 0
};

// Bolus DOM tracking
const renderedBoluses = new Map(); // chunkIdx -> SVGElement

// Strict HTML escape to prevent XSS payloads from executing in DOM
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
  setupTabs();
  setupPlaybackButtons();
  setupModalHandlers();
  setupQuickControls();
  setupQuarantineModalHandlers();
  await loadServerConfig();
  await loadAvailableFiles();
});

// Setup Tabs
function setupTabs() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const target = document.getElementById(btn.getAttribute("data-tab"));
      if (target) target.classList.add("active");
    });
  });
}

// Setup Quick Controls
function setupQuickControls() {
  quickFileSelector.addEventListener("change", (e) => {
    pipelineConfig.server_filename = e.target.value;
    document.getElementById("cfg-server-filename").value = e.target.value;
  });

  ctrlAiToggle.addEventListener("change", (e) => {
    pipelineConfig.enable_ai_agent = e.target.checked;
  });
}

// Setup Playback Buttons
function setupPlaybackButtons() {
  const btnPausePlay = document.getElementById("btn-pause-play");
  btnPausePlay.addEventListener("click", () => {
    isPaused = !isPaused;
    btnPausePlay.textContent = isPaused ? "Resume" : "Pause";
    if (!isPaused) processNextEvent();
  });

  const btnStep = document.getElementById("btn-step-forward");
  btnStep.addEventListener("click", () => {
    isPaused = true;
    btnPausePlay.textContent = "Resume";
    processNextEvent(true);
  });

  document.querySelectorAll(".speed-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".speed-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      playbackSpeed = parseFloat(btn.getAttribute("data-speed"));
    });
  });

  document.getElementById("btn-start-run").addEventListener("click", startDigestionPipeline);
}

// Setup Config Modal Handlers
function setupModalHandlers() {
  const btnOpen = document.getElementById("btn-open-config");
  const btnClose = document.getElementById("btn-close-config");
  const btnCancel = document.getElementById("btn-cancel-config");
  const btnSave = document.getElementById("btn-save-config");

  btnOpen.addEventListener("click", () => configModal.classList.add("active"));
  btnClose.addEventListener("click", () => configModal.classList.remove("active"));
  btnCancel.addEventListener("click", () => configModal.classList.remove("active"));

  const selFileSource = document.getElementById("cfg-file-source");
  selFileSource.addEventListener("change", (e) => {
    if (e.target.value === "upload") {
      document.getElementById("group-server-file").style.display = "none";
      document.getElementById("group-upload-file").style.display = "block";
    } else {
      document.getElementById("group-server-file").style.display = "block";
      document.getElementById("group-upload-file").style.display = "none";
    }
  });

  const selChunkMode = document.getElementById("cfg-chunk-mode");
  selChunkMode.addEventListener("change", (e) => {
    document.getElementById("cfg-manual-chunk-wrapper").style.display = 
      e.target.value === "manual" ? "block" : "none";
  });

  btnSave.addEventListener("click", () => {
    saveConfigFromModal();
    configModal.classList.remove("active");
  });
}

// Setup Dedicated Quarantine Pop-up Modal Handlers
function setupQuarantineModalHandlers() {
  document.getElementById("btn-modal-q-later").addEventListener("click", () => {
    quarantineModal.classList.remove("active");
  });

  document.getElementById("btn-modal-q-squash").addEventListener("click", async () => {
    if (activeQuarantinedList.length > 0 && currentModalQuarantineIdx < activeQuarantinedList.length) {
      const qrec = activeQuarantinedList[currentModalQuarantineIdx];
      await resolveSingleQuarantine(qrec.quarantine_id, "squash");
      currentModalQuarantineIdx++;
      showNextQuarantineInModal();
    }
  });

  document.getElementById("btn-modal-q-approve").addEventListener("click", async () => {
    if (activeQuarantinedList.length > 0 && currentModalQuarantineIdx < activeQuarantinedList.length) {
      const qrec = activeQuarantinedList[currentModalQuarantineIdx];
      await resolveSingleQuarantine(qrec.quarantine_id, "approve");
      currentModalQuarantineIdx++;
      showNextQuarantineInModal();
    }
  });
}

function showNextQuarantineInModal() {
  if (currentModalQuarantineIdx >= activeQuarantinedList.length) {
    quarantineModal.classList.remove("active");
    return;
  }
  const qrec = activeQuarantinedList[currentModalQuarantineIdx];
  document.getElementById("modal-q-pid").textContent = qrec.patient_id || "Unknown Record";
  document.getElementById("modal-q-priority").textContent = `RECORD ${currentModalQuarantineIdx + 1} OF ${activeQuarantinedList.length}`;
  document.getElementById("modal-q-reason").textContent = (qrec.flagged_reasons || ["Priority violation"]).join(", ");
  document.getElementById("modal-q-raw").textContent = JSON.stringify(qrec.raw_data || {});
  quarantineModal.classList.add("active");
}

async function loadServerConfig() {
  try {
    const res = await fetch("/api/default-config");
    const data = await res.json();
    pipelineConfig.column_priorities = data.default_priorities;
    renderPriorityTable(data.default_priorities, data.priority_levels);
  } catch (err) {
    console.error("Failed to load default config:", err);
  }
}

async function loadAvailableFiles() {
  try {
    const res = await fetch("/api/available-files");
    const data = await res.json();
    const selModal = document.getElementById("cfg-server-filename");
    selModal.innerHTML = "";
    quickFileSelector.innerHTML = "";

    data.files.forEach(f => {
      const optModal = document.createElement("option");
      optModal.value = f.filename;
      optModal.textContent = `${f.filename} (${(f.size_bytes/1024).toFixed(1)} KB)`;
      if (f.is_default) optModal.selected = true;
      selModal.appendChild(optModal);

      const optQuick = document.createElement("option");
      optQuick.value = f.filename;
      optQuick.textContent = `Dataset: ${f.filename} (${(f.size_bytes/1024).toFixed(1)} KB)`;
      if (f.is_default) {
        optQuick.selected = true;
        pipelineConfig.server_filename = f.filename;
      }
      quickFileSelector.appendChild(optQuick);
    });
  } catch (err) {
    console.error("Failed to load workspace files:", err);
  }
}

function renderPriorityTable(priorities, levels) {
  const tbody = document.getElementById("priority-matrix-rows");
  tbody.innerHTML = "";
  for (const [col, prio] of Object.entries(priorities)) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight: 600;">${escapeHtml(col)}</td>
      <td>
        <select class="priority-select" data-col="${escapeHtml(col)}">
          ${levels.map(l => `<option value="${l.value}" ${l.value === prio ? 'selected' : ''}>${l.label.split(' ')[0]}</option>`).join("")}
        </select>
      </td>
    `;
    tbody.appendChild(tr);
  }
}

function saveConfigFromModal() {
  pipelineConfig.file_source = document.getElementById("cfg-file-source").value;
  pipelineConfig.server_filename = document.getElementById("cfg-server-filename").value;
  quickFileSelector.value = pipelineConfig.server_filename;
  pipelineConfig.bp_format = document.getElementById("cfg-bp-format").value;
  pipelineConfig.date_format = document.getElementById("cfg-date-format").value;
  pipelineConfig.chunk_size_mode = document.getElementById("cfg-chunk-mode").value;
  pipelineConfig.manual_chunk_size = parseInt(document.getElementById("cfg-manual-chunk-val").value) || 25;

  document.querySelectorAll(".priority-select").forEach(sel => {
    const col = sel.getAttribute("data-col");
    pipelineConfig.column_priorities[col] = sel.value;
  });
}

// Start Digestion Pipeline
async function startDigestionPipeline() {
  pipelineConfig.enable_ai_agent = ctrlAiToggle.checked;

  counts = { mouthBoluses: 0, stomachChars: 0, liverFields: 0, threats: 0, quarantine: 0, absorbed: 0, excreted: 0 };
  updateKpiDisplay();
  logStream.innerHTML = "";
  eventQueue = [];
  eventIndex = 0;
  isPaused = false;
  activeQuarantinedList = [];
  currentModalQuarantineIdx = 0;
  totalPipelineChunks = 0;

  // Clear boluses container
  bolusesContainer.innerHTML = "";
  renderedBoluses.clear();

  document.getElementById("btn-pause-play").textContent = "Pause";
  const btnStart = document.getElementById("btn-start-run");
  btnStart.disabled = true;
  btnStart.textContent = "Processing Pipeline...";

  try {
    let res;
    if (pipelineConfig.file_source === "upload") {
      const fileInput = document.getElementById("cfg-file-upload");
      if (!fileInput.files.length) {
        alert("Please select a CSV file to upload or choose a workspace dataset.");
        btnStart.disabled = false;
        btnStart.textContent = "Execute Pipeline";
        return;
      }
      const formData = new FormData();
      formData.append("file", fileInput.files[0]);
      formData.append("config_json", JSON.stringify({
        chunk_size_mode: pipelineConfig.chunk_size_mode,
        manual_chunk_size: pipelineConfig.manual_chunk_size,
        standard_bp_format: pipelineConfig.bp_format,
        standard_date_format: pipelineConfig.date_format,
        column_priorities: pipelineConfig.column_priorities,
        enable_ai_agent: pipelineConfig.enable_ai_agent,
        auto_approve_quarantine: false
      }));
      res = await fetch("/api/pipeline/upload", { method: "POST", body: formData });
    } else {
      res = await fetch("/api/pipeline/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_source: "server_file",
          server_filename: pipelineConfig.server_filename,
          bp_format: pipelineConfig.bp_format,
          date_format: pipelineConfig.date_format,
          chunk_size_mode: pipelineConfig.chunk_size_mode,
          manual_chunk_size: pipelineConfig.manual_chunk_size,
          column_priorities: pipelineConfig.column_priorities,
          enable_ai_agent: pipelineConfig.enable_ai_agent,
          auto_approve_quarantine: false
        })
      });
    }

    const data = await res.json();
    currentSessionId = data.session_id;
    totalPipelineChunks = data.total_chunks || 1;

    kpiMouth.textContent = `0 / ${totalPipelineChunks} Boluses`;

    const evRes = await fetch(`/api/pipeline/${currentSessionId}/events?after_idx=0`);
    const evData = await evRes.json();
    eventQueue = evData.events;

    processNextEvent();

  } catch (err) {
    console.error("Pipeline initiation error:", err);
    alert("Error executing pipeline: " + err.message);
    btnStart.disabled = false;
    btnStart.textContent = "Execute Pipeline";
  }
}

// Sequential Event Processing
function processNextEvent(singleStep = false) {
  if (eventIndex >= eventQueue.length) {
    checkPipelineCompletion();
    return;
  }

  const ev = eventQueue[eventIndex];
  eventIndex++;

  renderEvent(ev);

  if (!isPaused && !singleStep) {
    const baseDelay = Math.max(10, 110 / playbackSpeed);
    setTimeout(() => processNextEvent(), baseDelay);
  }
}

// Get or dynamically create a distinct SVG Bolus with a unique color
function getOrCreateBolus(chunkIdx) {
  if (chunkIdx === null || chunkIdx === undefined) return null;
  if (renderedBoluses.has(chunkIdx)) {
    return renderedBoluses.get(chunkIdx);
  }

  const color = BOLUS_COLORS[chunkIdx % BOLUS_COLORS.length];
  const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  circle.setAttribute("id", `bolus-${chunkIdx}`);
  circle.setAttribute("cx", "270");
  circle.setAttribute("cy", "55");
  circle.setAttribute("r", "10");
  circle.setAttribute("fill", color);
  circle.setAttribute("stroke", "#ffffff");
  circle.setAttribute("stroke-width", "2");
  circle.setAttribute("class", "food-bolus");
  circle.style.transition = "cx 0.6s cubic-bezier(0.4, 0, 0.2, 1), cy 0.6s cubic-bezier(0.4, 0, 0.2, 1), r 0.5s ease";

  bolusesContainer.appendChild(circle);
  renderedBoluses.set(chunkIdx, circle);
  return circle;
}

function renderEvent(ev) {
  const stage = ev.stage;
  const chunkIdx = ev.chunk_idx !== null && ev.chunk_idx !== undefined ? ev.chunk_idx : 0;
  const organ = ORGAN_COORDS[stage] || ORGAN_COORDS.mouth;

  stageBadge.textContent = `Status: ${organ.name}`;
  stageBadge.style.color = organ.badgeColor;

  const bolusEl = getOrCreateBolus(chunkIdx);

  // Position update based on stage
  if (bolusEl) {
    if (stage === "mouth") {
      bolusEl.setAttribute("cx", "270");
      bolusEl.setAttribute("cy", "55");
      counts.mouthBoluses = Math.max(counts.mouthBoluses, chunkIdx + 1);
      kpiMouth.textContent = `Bolus ${chunkIdx + 1} of ${totalPipelineChunks} (${totalPipelineChunks} total)`;
    } else if (stage === "stomach") {
      // Subtle spread in stomach vat
      const offset = (chunkIdx % 4) * 8 - 12;
      bolusEl.setAttribute("cx", String(240 + offset));
      bolusEl.setAttribute("cy", String(245 + offset));
    } else if (stage === "liver") {
      bolusEl.setAttribute("cx", "355");
      bolusEl.setAttribute("cy", "215");
    } else if (stage === "immune") {
      if (ev.action && ev.action.includes("Reached Duodenum") || ev.action.includes("Cleared")) {
        // Queue at duodenum waiting area at entrance of Small Intestine
        const queueX = 220 + ((chunkIdx * 14) % 100);
        const queueY = 365 + Math.floor(chunkIdx / 7) * 8;
        bolusEl.setAttribute("cx", String(queueX));
        bolusEl.setAttribute("cy", String(queueY));
      } else {
        bolusEl.setAttribute("cx", "270");
        bolusEl.setAttribute("cy", "330");
      }
    }
  }

  // Collective absorption across Small Intestine villi
  if (stage === "small_intestine" && (ev.action.includes("Collective") || ev.is_absorbed)) {
    // All accumulated boluses simultaneously traverse the villi and absorb into bloodstream
    renderedBoluses.forEach((bCircle, cIdx) => {
      // Staggered villi cascade into capillary
      setTimeout(() => {
        bCircle.setAttribute("cx", "270");
        bCircle.setAttribute("cy", "440");
        setTimeout(() => {
          bCircle.setAttribute("cx", "70");
          bCircle.setAttribute("cy", "640");
          bCircle.setAttribute("r", "5"); // shrink into absorbed cellular nutrient
          bCircle.style.opacity = "0.75";
        }, 300);
      }, (cIdx % 10) * 40);
    });
  }

  // Update counters
  if (stage === "stomach" && ev.details && ev.details.dissolved_characters) {
    counts.stomachChars += ev.details.dissolved_characters;
    kpiStomach.textContent = counts.stomachChars;
  } else if (stage === "liver" && ev.details && ev.details.changes) {
    counts.liverFields += ev.details.changes;
    kpiLiver.textContent = counts.liverFields;
  } else if (stage === "immune") {
    if (ev.is_threat) {
      counts.threats++;
      kpiThreats.textContent = counts.threats;
      recordThreatInTab(ev);
    }
    if (ev.is_quarantined) {
      counts.quarantine++;
      kpiQuarantine.textContent = counts.quarantine;
      recordQuarantineInTab(ev);
    }
  } else if (stage === "small_intestine" && ev.is_absorbed) {
    counts.absorbed++;
    kpiAbsorbed.textContent = counts.absorbed;
  } else if (stage === "large_intestine" && ev.is_excreted) {
    counts.excreted++;
    kpiExcreted.textContent = counts.excreted;
    recordWasteInTab(ev);
  }

  appendLogEntry(ev);
}

function appendLogEntry(ev) {
  const div = document.createElement("div");
  div.className = `log-entry stage-${ev.stage} ${ev.is_threat ? 'threat-neutralized' : ''}`;

  const timeStr = new Date(ev.timestamp * 1000).toLocaleTimeString();
  const pid = ev.patient_id ? `[${escapeHtml(ev.patient_id)}] ` : "";

  div.innerHTML = `
    <div class="log-meta">
      <span class="log-organ-badge" style="color: ${ORGAN_COORDS[ev.stage]?.badgeColor || '#0284c7'};">
        ${escapeHtml(ev.stage.toUpperCase().replace('_', ' '))}
      </span>
      <span>${timeStr}</span>
    </div>
    <div class="log-action">${pid}${escapeHtml(ev.action)}</div>
    <div class="log-reason">${escapeHtml(ev.reason)}</div>
  `;

  logStream.prepend(div);
  if (logStream.children.length > 250) {
    logStream.removeChild(logStream.lastChild);
  }
}

function recordThreatInTab(ev) {
  const threatList = document.getElementById("threat-list");
  const threatsLabel = document.getElementById("threats-counter-label");
  if (counts.threats === 1) threatList.innerHTML = "";

  threatsLabel.textContent = `${counts.threats} detected`;

  const div = document.createElement("div");
  div.className = "threat-card";
  div.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
      <span class="threat-badge">${escapeHtml(ev.details?.threat_type || 'SECURITY PAYLOAD')}</span>
      <span style="font-size: 0.72rem; color: var(--color-danger); font-family: var(--font-mono);">Row #${ev.row_idx}</span>
    </div>
    <div style="font-size: 0.8rem; font-weight: 600; color: #991b1b;">Field: '${escapeHtml(ev.details?.field_name)}'</div>
    <div style="font-size: 0.75rem; font-family: var(--font-mono); background: #ffffff; border: 1px solid #fee2e2; padding: 0.25rem 0.4rem; border-radius: 4px; color: #991b1b; margin-top: 0.2rem; word-break: break-all;">
      ${escapeHtml(ev.details?.detected_payload || 'Threat payload')}
    </div>
    <div style="font-size: 0.72rem; color: var(--color-success); margin-top: 0.25rem; font-weight: 600;">
      Neutralized and rerouted to colon waste
    </div>
  `;
  threatList.appendChild(div);
}

function recordQuarantineInTab(ev) {
  const qList = document.getElementById("quarantine-records-list");
  const countText = document.getElementById("quarantine-count-text");
  const badgeTab = document.getElementById("badge-tab-quarantine");
  const btnApproveAll = document.getElementById("btn-approve-all-quarantine");

  if (counts.quarantine === 1) qList.innerHTML = "";

  countText.textContent = counts.quarantine;
  badgeTab.style.display = "inline";
  badgeTab.textContent = counts.quarantine;
  btnApproveAll.style.display = "inline-flex";

  const qid = ev.details?.quarantine_id || `Q-${counts.quarantine}`;
  const pid = ev.patient_id || "Unknown";
  const reasons = ev.details?.flagged_reasons || ["Priority Violation"];

  activeQuarantinedList.push({
    quarantine_id: qid,
    patient_id: pid,
    flagged_reasons: reasons,
    raw_data: ev.details?.raw_data || {}
  });

  const div = document.createElement("div");
  div.className = "quarantine-card";
  div.id = `qcard-${qid}`;
  div.innerHTML = `
    <div class="quarantine-header">
      <span class="quarantine-pid">${escapeHtml(pid)}</span>
      <span style="font-size: 0.72rem; font-weight: 700; color: var(--color-warning);">HELD IN QUARANTINE</span>
    </div>
    <div class="quarantine-reasons">
      Violation: ${escapeHtml(reasons.join(", "))}
    </div>
    <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono); margin-bottom: 0.5rem; word-break: break-all;">
      ${escapeHtml(JSON.stringify(ev.details?.raw_data || {}).slice(0, 110))}...
    </div>
    <div style="font-size: 0.8rem; font-weight: 700; color: var(--color-danger); margin-bottom: 0.4rem;">
      Action Required: Squash this record??
    </div>
    <div class="quarantine-actions">
      <button class="btn btn-sm btn-danger" onclick="resolveSingleQuarantine('${escapeHtml(qid)}', 'squash')">
        Squash Record
      </button>
      <button class="btn btn-sm btn-success" onclick="resolveSingleQuarantine('${escapeHtml(qid)}', 'approve')">
        Approve with Imputation
      </button>
    </div>
  `;
  qList.appendChild(div);
}

function recordWasteInTab(ev) {
  const wasteList = document.getElementById("waste-list");
  if (counts.excreted === 1) wasteList.innerHTML = "";

  const div = document.createElement("div");
  div.className = "waste-item";

  div.innerHTML = `
    <div style="display: flex; justify-content: space-between; color: var(--color-purple); font-weight: 600; font-size: 0.78rem;">
      <span>${escapeHtml(ev.patient_id || 'Biological Waste')}</span>
      <span>${new Date(ev.timestamp * 1000).toLocaleTimeString()}</span>
    </div>
    <div style="color: var(--text-secondary); margin-top: 0.15rem;">${escapeHtml(ev.reason)}</div>
  `;
  wasteList.prepend(div);
}

function updateKpiDisplay() {
  kpiMouth.textContent = "0 / 0";
  kpiStomach.textContent = "0";
  kpiLiver.textContent = "0";
  kpiThreats.textContent = "0";
  kpiQuarantine.textContent = "0";
  kpiAbsorbed.textContent = "0";
  kpiExcreted.textContent = "0";
}

// Check if pipeline reached quarantine checkpoint or completed
async function checkPipelineCompletion() {
  try {
    const res = await fetch(`/api/pipeline/${currentSessionId}/report`);
    const data = await res.json();

    if (data.is_waiting_quarantine) {
      stageBadge.textContent = "Status: Immune Quarantine Tribunal (Action Required)";
      stageBadge.style.color = "#d97706";
      document.querySelector('[data-tab="tab-immune"]').click();

      // Trigger the dedicated pop-up modal asking "Squash this record??"
      currentModalQuarantineIdx = 0;
      if (activeQuarantinedList.length > 0) {
        showNextQuarantineInModal();
      }
      return;
    }

    if (data.is_completed) {
      onPipelineFullyCompleted(data);
    }
  } catch (err) {
    console.error("Error checking report:", err);
  }
}

// Resolve Quarantine Actions
async function resolveSingleQuarantine(qid, action) {
  const card = document.getElementById(`qcard-${qid}`);
  if (card) {
    card.style.opacity = "0.5";
    card.innerHTML = `<div style="text-align: center; color: var(--color-primary); font-size: 0.8rem; padding: 0.5rem;">Processing ${action}...</div>`;
  }

  const resolutions = [{ quarantine_id: qid, action: action }];
  await submitQuarantineResolutions(resolutions);
}

document.getElementById("btn-approve-all-quarantine").addEventListener("click", async () => {
  const cards = document.querySelectorAll(".quarantine-card");
  const resolutions = [];
  cards.forEach(c => {
    const qid = c.id.replace("qcard-", "");
    resolutions.push({ quarantine_id: qid, action: "approve" });
  });
  quarantineModal.classList.remove("active");
  await submitQuarantineResolutions(resolutions);
});

async function submitQuarantineResolutions(resolutions) {
  try {
    const res = await fetch(`/api/pipeline/${currentSessionId}/resolve-quarantine`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resolutions })
    });
    const data = await res.json();

    const evRes = await fetch(`/api/pipeline/${currentSessionId}/events?after_idx=${eventQueue.length}`);
    const evData = await evRes.json();
    eventQueue.push(...evData.events);

    processNextEvent();
  } catch (err) {
    console.error("Failed to resolve quarantine:", err);
  }
}

// Pipeline Fully Completed
function onPipelineFullyCompleted(data) {
  stageBadge.textContent = "Status: Metabolism Complete";
  stageBadge.style.color = "#059669";
  kpiMouth.textContent = `${totalPipelineChunks} / ${totalPipelineChunks} Boluses`;

  const btnStart = document.getElementById("btn-start-run");
  btnStart.disabled = false;
  btnStart.textContent = "Execute Pipeline";

  const rep = data.final_report;
  if (!rep) return;

  const m = rep.health_metrics;
  document.getElementById("res-avg-age").textContent = m.average_age;
  document.getElementById("res-avg-bmi").textContent = m.average_bmi;
  document.getElementById("res-chronic-pct").textContent = `${m.chronic_illness_pct}%`;
  document.getElementById("res-smoker-pct").textContent = `${m.smoker_percentage}%`;

  // BMI Distribution bars
  const bmiContainer = document.getElementById("bmi-distribution-bars");
  bmiContainer.innerHTML = "";
  for (const [cat, count] of Object.entries(m.bmi_categories)) {
    const pct = m.total_absorbed > 0 ? (count / m.total_absorbed * 100).toFixed(1) : 0;
    const bar = document.createElement("div");
    bar.className = "breakdown-bar";
    bar.innerHTML = `
      <div class="bar-label-group">
        <span>${escapeHtml(cat)}</span>
        <span>${count} patients (${pct}%)</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${pct}%;"></div>
      </div>
    `;
    bmiContainer.appendChild(bar);
  }

  // AI Agent Insights
  if (rep.ai_insights) {
    const aiBox = document.getElementById("ai-insights-container");
    aiBox.style.display = "block";
    document.getElementById("ai-summary-text").textContent = rep.ai_insights.population_summary;

    const recsContainer = document.getElementById("ai-recommendations-list");
    recsContainer.innerHTML = "<div style='font-weight: 700; font-size: 0.78rem; color: var(--text-primary); margin-bottom: 0.25rem;'>Recommended Preventive Protocols:</div>";
    const ul = document.createElement("ul");
    ul.style.paddingLeft = "1.2rem";
    ul.style.fontSize = "0.78rem";
    ul.style.color = "var(--text-secondary)";
    rep.ai_insights.clinical_recommendations.forEach(r => {
      const li = document.createElement("li");
      li.textContent = r;
      ul.appendChild(li);
    });
    recsContainer.appendChild(ul);
  } else {
    document.getElementById("ai-insights-container").style.display = "none";
  }

  // Enable download buttons
  const btnCsv = document.getElementById("btn-download-csv");
  const btnJson = document.getElementById("btn-download-json");
  const btnWaste = document.getElementById("btn-download-waste");

  btnCsv.disabled = false;
  btnJson.disabled = false;
  btnWaste.disabled = false;

  btnCsv.onclick = () => window.open(`/api/pipeline/${currentSessionId}/download/csv`, "_blank");
  btnJson.onclick = () => window.open(`/api/pipeline/${currentSessionId}/download/json`, "_blank");
  btnWaste.onclick = () => window.open(`/api/pipeline/${currentSessionId}/download/waste`, "_blank");

  document.querySelector('[data-tab="tab-analytics"]').click();
}
