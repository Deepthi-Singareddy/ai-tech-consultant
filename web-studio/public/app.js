const TASK1_URL = "http://127.0.0.1:8000/api/v1";
const TASK2_URL = "http://127.0.0.1:3000/api/v1";
const TASK3_URL = "http://127.0.0.1:8001/api/v1";

let currentActiveEmail = null;
let currentDraft = null;
let currentScopeData = null;
let activeEscalationId = null;

// Tab Switching
function switchTab(tabName) {
  document.querySelectorAll(".tab-btn").forEach((btn) => btn.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach((pane) => pane.classList.remove("active"));

  const targetPane = document.getElementById(`pane-${tabName}`);
  if (targetPane) targetPane.classList.add("active");

  const matchingBtn = Array.from(document.querySelectorAll(".tab-btn")).find((b) =>
    b.getAttribute("onclick").includes(tabName)
  );
  if (matchingBtn) matchingBtn.classList.add("active");

  if (tabName === "inbox") {
    loadEmails();
    loadAutonomyStatus();
  } else if (tabName === "knowledge") {
    loadEscalations();
  }
}

// Service Health Monitoring
async function checkServiceHealth() {
  const checkOne = async (url, dotId) => {
    const dot = document.getElementById(dotId);
    try {
      const res = await fetch(`${url}/health`, { signal: AbortSignal.timeout(1500) });
      if (res.ok) {
        dot.className = "dot";
      } else {
        dot.className = "dot offline";
      }
    } catch {
      dot.className = "dot offline";
    }
  };

  await Promise.all([
    checkOne(TASK1_URL, "dot-task1"),
    checkOne(TASK2_URL, "dot-task2"),
    checkOne(TASK3_URL, "dot-task3")
  ]);
}

// ---------------- TAB 1: KNOWLEDGE BRAIN ----------------
async function submitKBQuery() {
  const input = document.getElementById("kb-query-input");
  const query = input.value.trim();
  if (!query) return;

  const chatHistory = document.getElementById("kb-chat-history");

  // Append user message
  const userMsg = document.createElement("div");
  userMsg.className = "chat-msg user";
  userMsg.innerHTML = `<strong>You:</strong> ${escapeHtml(query)}`;
  chatHistory.appendChild(userMsg);
  input.value = "";
  chatHistory.scrollTop = chatHistory.scrollHeight;

  // Bot loading
  const botMsg = document.createElement("div");
  botMsg.className = "chat-msg bot";
  botMsg.innerHTML = `<em>Retrieving verified Brilliant Directories documentation & screenshots...</em>`;
  chatHistory.appendChild(botMsg);
  chatHistory.scrollTop = chatHistory.scrollHeight;

  try {
    const res = await fetch(`${TASK1_URL}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, include_images: true, top_k: 3 })
    });

    if (!res.ok) throw new Error("Task 1 API error");
    const data = await res.json();

    let html = `<div>${data.answer.replace(/\n/g, "<br>")}</div>`;

    if (data.status === "insufficient_evidence") {
      html += `<div style="margin-top: 0.5rem; color: var(--accent-amber); font-size: 0.8rem;">
        ⚠️ Insufficient verified evidence. Escalation ticket logged (ID: ${data.escalation_id}).
      </div>`;
      loadEscalations();
    }

    if (data.sources && data.sources.length > 0) {
      html += `<div style="margin-top: 0.75rem; font-size: 0.8rem; font-weight: 600; color: var(--text-muted);">Verified Sources & Citations:</div>`;
      data.sources.forEach((s) => {
        html += `<div class="citation-card">
          <a href="${s.url}" target="_blank" class="citation-link">${escapeHtml(s.title)}</a>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem;">Relevance: ${(s.relevance * 100).toFixed(1)}% | Section: ${escapeHtml(s.section_heading || "General")}</div>
        </div>`;
      });
    }

    if (data.images && data.images.length > 0) {
      html += `<div style="margin-top: 0.75rem; font-size: 0.8rem; font-weight: 600; color: var(--accent-cyan);">Associated Interface Screenshots:</div>`;
      data.images.forEach((img) => {
        html += `<div style="background: rgba(0,0,0,0.3); padding: 0.5rem; border-radius: 4px; margin-top: 0.3rem; font-size: 0.75rem;">
          📷 <strong>${escapeHtml(img.caption)}</strong>: ${escapeHtml(img.visual_description)}
        </div>`;
      });
    }

    botMsg.innerHTML = html;
  } catch (err) {
    botMsg.innerHTML = `<span style="color: var(--accent-rose);">Error connecting to Task 1 Knowledge Brain (:8000). Ensure the service is running.</span>`;
  }
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function loadEscalations() {
  try {
    const res = await fetch(`${TASK1_URL}/escalations`);
    if (!res.ok) return;
    const items = await res.json();
    const container = document.getElementById("escalation-list");
    const statPending = document.getElementById("stat-pending-esc");

    const pending = items.filter((i) => i.status === "pending");
    statPending.innerText = pending.length;

    if (items.length === 0) {
      container.innerHTML = `<p style="font-size: 0.85rem; color: var(--text-muted);">No escalations logged.</p>`;
      return;
    }

    container.innerHTML = items
      .map(
        (i) => `
      <div style="background: var(--bg-tertiary); padding: 0.6rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color); font-size: 0.8rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 600; color: ${i.status === "resolved" ? "var(--accent-emerald)" : "var(--accent-amber)"};">[${i.id}] ${i.status.toUpperCase()}</span>
          ${i.status === "pending" ? `<button class="btn-secondary" style="font-size: 0.75rem; padding: 0.2rem 0.5rem;" onclick="openEscalationModal('${i.id}', '${escapeHtml(i.query)}')">Resolve</button>` : `<span style="color: var(--text-dim); font-size: 0.7rem;">Resolved by ${i.resolved_by}</span>`}
        </div>
        <div style="margin-top: 0.3rem;">"${escapeHtml(i.query)}"</div>
        ${i.expert_answer ? `<div style="margin-top: 0.3rem; color: var(--accent-emerald); font-size: 0.75rem;">✔ Answer: ${escapeHtml(i.expert_answer)}</div>` : ""}
      </div>
    `
      )
      .join("");
  } catch {}
}

function openEscalationModal(id, query) {
  activeEscalationId = id;
  document.getElementById("modal-esc-query").innerText = `Question: "${query}"`;
  document.getElementById("modal-esc-answer").value = "";
  document.getElementById("modal-escalation").style.display = "flex";
}

function closeEscalationModal() {
  document.getElementById("modal-escalation").style.display = "none";
}

async function submitEscalationResolution() {
  const answer = document.getElementById("modal-esc-answer").value.trim();
  if (!answer || !activeEscalationId) return;

  try {
    await fetch(`${TASK1_URL}/escalations/${activeEscalationId}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expert_answer: answer, expert_name: "Senior Tech Consultant" })
    });
    closeEscalationModal();
    loadEscalations();
    alert("Expert resolution indexed into Knowledge Brain! Subsequent queries will retrieve this answer.");
  } catch (err) {
    alert("Failed to submit resolution.");
  }
}

// ---------------- TAB 2: INBOX AGENT ----------------
let allEmailsCache = [];

async function loadEmails() {
  try {
    const res = await fetch(`${TASK2_URL}/emails`);
    if (!res.ok) return;
    allEmailsCache = await res.json();
    renderEmailsList(allEmailsCache);
    if (allEmailsCache.length > 0 && !currentActiveEmail) {
      selectEmail(allEmailsCache[0].id);
    }
  } catch {
    document.getElementById("email-list-container").innerHTML = `<p style="color: var(--accent-rose); padding: 1rem;">Failed to load emails from Task 2 (:3000).</p>`;
  }
}

function filterEmails() {
  const sel = document.getElementById("email-category-filter").value;
  if (!sel) {
    renderEmailsList(allEmailsCache);
  } else {
    renderEmailsList(allEmailsCache.filter((e) => e.expectedCategory === sel));
  }
}

function renderEmailsList(emails) {
  const container = document.getElementById("email-list-container");
  container.innerHTML = emails
    .map((e) => {
      const riskClass = `badge-${e.expectedRisk ? e.expectedRisk.toLowerCase() : "low"}`;
      return `
      <div class="email-item ${currentActiveEmail === e.id ? "selected" : ""}" onclick="selectEmail('${e.id}')">
        <div class="email-meta">
          <span>${escapeHtml(e.senderName)}</span>
          <span class="badge ${riskClass}">${e.expectedRisk || "LOW"}</span>
        </div>
        <div class="email-subject">${escapeHtml(e.subject)}</div>
        <div style="font-size: 0.75rem; color: var(--text-dim); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
          ${escapeHtml(e.body)}
        </div>
      </div>
    `;
    })
    .join("");
}

async function selectEmail(id) {
  currentActiveEmail = id;
  renderEmailsList(allEmailsCache);

  const email = allEmailsCache.find((e) => e.id === id);
  if (!email) return;

  document.getElementById("draft-sender-info").innerText = `From: ${email.senderName} <${email.sender}>`;
  document.getElementById("draft-subject-info").innerText = email.subject;

  // Process email via Task 2 API
  document.getElementById("draft-loading").style.display = "block";
  document.getElementById("draft-details").style.opacity = "0.3";

  try {
    const res = await fetch(`${TASK2_URL}/emails/${id}/process`, { method: "POST" });
    const data = await res.json();
    currentDraft = data.draft;

    document.getElementById("draft-textarea").value = currentDraft.draftReply;

    // Badges
    const badgeContainer = document.getElementById("email-badge-container");
    const riskBadge = `<span class="badge badge-${currentDraft.riskLevel.toLowerCase()}">${currentDraft.riskLevel} RISK</span>`;
    const catBadge = `<span class="badge" style="background: rgba(99,102,241,0.2); color:#818cf8;">${currentDraft.category}</span>`;
    const autoBadge = currentDraft.requiresHumanApproval
      ? `<span class="badge badge-medium">HITL APPROVAL REQUIRED</span>`
      : `<span class="badge badge-low">AUTONOMOUS ELIGIBLE</span>`;

    badgeContainer.innerHTML = `${catBadge} ${riskBadge} ${autoBadge}`;

    // Sources box
    const sourcesBox = document.getElementById("draft-sources-box");
    if (currentDraft.sourcesUsed && currentDraft.sourcesUsed.length > 0) {
      sourcesBox.innerHTML = `<strong>Grounded Knowledge Sources Used:</strong> ` +
        currentDraft.sourcesUsed.map((s) => `<a href="${s.url}" target="_blank" style="color: var(--accent-cyan); margin-left: 0.3rem;">[${escapeHtml(s.title)}]</a>`).join(" ");
    } else {
      sourcesBox.innerHTML = `<span style="color: var(--text-dim);">No specific product doc chunk required.</span>`;
    }
  } catch (err) {
    document.getElementById("draft-textarea").value = "Failed to fetch draft from Task 2 API.";
  } finally {
    document.getElementById("draft-loading").style.display = "none";
    document.getElementById("draft-details").style.opacity = "1";
  }
}

async function submitReview(action) {
  if (!currentActiveEmail || !currentDraft) return;

  const finalReply = document.getElementById("draft-textarea").value;
  try {
    const res = await fetch(`${TASK2_URL}/emails/${currentActiveEmail}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category: currentDraft.category,
        originalDraft: currentDraft.draftReply,
        finalSentReply: finalReply,
        action,
        reviewerName: "Lead Tech Consultant"
      })
    });
    const result = await res.json();
    alert(`Review recorded (${action})! Edit Distance: ${(result.reviewRecord.editDistanceRatio * 100).toFixed(1)}%. Autonomy Streak: ${result.updatedCategoryState.consecutiveUneditedApprovals}/20.`);
    loadAutonomyStatus();
  } catch (err) {
    alert("Error recording review.");
  }
}

async function loadAutonomyStatus() {
  try {
    const res = await fetch(`${TASK2_URL}/autonomy/status`);
    if (!res.ok) return;
    const data = await res.json();
    const container = document.getElementById("autonomy-table-container");

    let rows = data.categories
      .map((c) => {
        let statusBadge = "";
        if (c.isSafetyBlacklisted) {
          statusBadge = `<span class="badge badge-critical">SAFETY BLACKLISTED</span>`;
        } else if (c.isAutonomousActive) {
          statusBadge = `<span class="badge badge-low">AUTONOMOUS SEND ACTIVE</span>`;
        } else {
          statusBadge = `<span class="badge badge-medium">HUMAN REVIEW REQUIRED</span>`;
        }

        const pct = Math.min(100, Math.round((c.consecutiveUneditedApprovals / 20) * 100));

        return `
        <tr>
          <td><strong>${c.category}</strong></td>
          <td>${statusBadge}</td>
          <td>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <div style="flex: 1; background: var(--bg-tertiary); height: 6px; border-radius: 3px; overflow: hidden;">
                <div style="width: ${pct}%; background: var(--accent-emerald); height: 100%;"></div>
              </div>
              <span style="font-size: 0.8rem; font-weight: 600;">${c.consecutiveUneditedApprovals}/20</span>
            </div>
          </td>
          <td>${c.totalApproved} / ${c.totalEdited} / ${c.totalRejected}</td>
        </tr>
      `;
      })
      .join("");

    container.innerHTML = `
      <table class="wbs-table">
        <thead>
          <tr>
            <th>Category</th>
            <th>Mode</th>
            <th>Consecutive Streak</th>
            <th>Appr / Edit / Rej</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  } catch {}
}

// ---------------- TAB 3: MEETING TO SCOPE ----------------
async function processSelectedMeeting() {
  const meetingId = document.getElementById("meeting-selector").value;
  const container = document.getElementById("scope-results-container");
  container.style.display = "block";

  try {
    if (meetingId === "MEETING-C") {
      // Run Scope Diff Engine
      const res = await fetch(`${TASK3_URL}/scope/diff`, { method: "POST" });
      const data = await res.json();
      renderDiffReport(data.diff_report);
      renderScopeData(data.revised_sow, data.revised_proposal);
    } else {
      document.getElementById("delta-banner").style.display = "none";
      const res = await fetch(`${TASK3_URL}/transcripts/${meetingId}/process`, { method: "POST" });
      const data = await res.json();
      renderScopeData(data.scope_of_work, data.proposal);
    }
  } catch (err) {
    alert("Error processing transcript from Task 3 (:8001).");
  }
}

function renderDiffReport(diff) {
  const banner = document.getElementById("delta-banner");
  banner.style.display = "block";

  let changesHtml = diff.changes
    .map((c) => {
      let badgeClass = "badge-modified";
      if (c.type === "ADDED") badgeClass = "badge-added";
      if (c.type === "REMOVED") badgeClass = "badge-removed";
      if (c.type === "SCOPE_CREEP_WARNING") badgeClass = "badge-creep";

      return `
      <div style="display: flex; gap: 0.75rem; align-items: flex-start; margin-bottom: 0.5rem; font-size: 0.85rem;">
        <span class="badge ${badgeClass}">${c.type}</span>
        <div>
          <strong>${escapeHtml(c.description)}</strong>
          <div style="color: var(--text-muted); font-size: 0.8rem;">${escapeHtml(c.notes)}</div>
        </div>
      </div>
    `;
    })
    .join("");

  document.getElementById("delta-details-content").innerHTML = `
    <div style="margin-bottom: 0.75rem; font-size: 0.9rem;">${escapeHtml(diff.summary_for_client)}</div>
    <div style="background: rgba(0,0,0,0.3); padding: 0.75rem; border-radius: var(--radius-sm);">${changesHtml}</div>
  `;
}

function renderScopeData(sow, proposal) {
  currentScopeData = { sow, proposal };

  document.getElementById("sow-hours-badge").innerText = `${sow.total_hours_pert} PERT Hours`;
  document.getElementById("proposal-cost-display").innerText = `$${sow.cost_usd.toLocaleString()} (₹${sow.cost_inr.toLocaleString()})`;

  const statusBadge = document.getElementById("proposal-status-badge");
  statusBadge.innerText = proposal.status;
  statusBadge.className = `badge ${proposal.status === "APPROVED" ? "badge-low" : "badge-medium"}`;

  // Render WBS Table
  let wbsRows = sow.wbs_tasks
    .map(
      (t) => `
    <tr>
      <td><strong>${t.task_id}</strong></td>
      <td>${escapeHtml(t.name)}</td>
      <td><span class="badge" style="background: rgba(255,255,255,0.08);">${t.category}</span></td>
      <td>${t.optimistic_hours}h / ${t.likely_hours}h / ${t.pessimistic_hours}h</td>
      <td><strong>${t.expected_hours_pert}h</strong></td>
    </tr>
  `
    )
    .join("");

  document.getElementById("wbs-table-container").innerHTML = `
    <table class="wbs-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Task Name</th>
          <th>Category</th>
          <th>O / M / P</th>
          <th>PERT</th>
        </tr>
      </thead>
      <tbody>${wbsRows}</tbody>
    </table>
  `;

  // Render Proposal
  let proposalHtml = `
    <h3 style="color: var(--accent-cyan); margin-bottom: 0.5rem;">${escapeHtml(proposal.title)}</h3>
    <p><strong>Client:</strong> ${escapeHtml(proposal.client_name)} | <strong>Version:</strong> ${proposal.version}</p>
    <p style="margin: 0.5rem 0;">${escapeHtml(proposal.executive_summary)}</p>
    
    <h4 style="margin-top: 0.75rem; color: var(--accent-indigo);">Agreed Deliverables:</h4>
    <ul style="padding-left: 1.25rem;">
      ${proposal.deliverables_summary.map((d) => `<li>${escapeHtml(d)}</li>`).join("")}
    </ul>

    <h4 style="margin-top: 0.75rem; color: var(--accent-rose);">Explicit Out-of-Scope Exclusions:</h4>
    <ul style="padding-left: 1.25rem;">
      ${proposal.exclusions.map((e) => `<li>${escapeHtml(e)}</li>`).join("")}
    </ul>

    <div style="margin-top: 0.75rem; padding: 0.5rem; background: rgba(0,0,0,0.25); border-radius: var(--radius-sm);">
      <strong>Timeline:</strong> ${proposal.timeline_weeks} weeks delivery commitment.
    </div>
  `;

  document.getElementById("proposal-preview-box").innerHTML = proposalHtml;
}

async function approveCurrentProposal() {
  if (!currentScopeData || !currentScopeData.proposal) return;
  const propId = currentScopeData.proposal.proposal_id;

  try {
    const res = await fetch(`${TASK3_URL}/proposals/${propId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reviewer_name: "Senior Forward Deployed Engineer", approved: true })
    });
    const updated = await res.json();
    alert(`Proposal ${propId} officially APPROVED and signed off! Ready for client presentation.`);
    currentScopeData.proposal = updated;
    renderScopeData(currentScopeData.sow, updated);
  } catch (err) {
    alert("Approval submission failed.");
  }
}

// Utility
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Init
window.addEventListener("DOMContentLoaded", () => {
  checkServiceHealth();
  setInterval(checkServiceHealth, 4000);
  loadEmails();
  loadAutonomyStatus();
  loadEscalations();
});
