// Auto-Categorization Webhook - Frontend App
// Team 15 | SD-02

// API base (same origin). Keep trailing slash handling out of Chart.js etc.
const API = "";
let categoryChart = null;
let priorityChart = null;

const SAMPLES = [
  { id: "TKT-001", title: "Unable to login after password reset", desc: "User cannot access the portal after performing a password reset. Getting invalid credentials error." },
  { id: "TKT-002", title: "Payment not going through at checkout", desc: "My credit card keeps declining even though the card is valid and has sufficient balance." },
  { id: "TKT-003", title: "Application crashes on startup", desc: "The desktop app crashes immediately after the splash screen with NullPointerException in main thread." },
  { id: "TKT-004", title: "VPN dropping connection every few minutes", desc: "Company VPN disconnects every 10-15 minutes while working from home. Very disruptive." },
  { id: "TKT-005", title: "Need access to finance reporting module", desc: "I have been assigned as Finance Analyst and need access to the financial reporting dashboard." },
];
let sampleIdx = 0;
let recentTicketsCache = [];
let activeCategoryFilter = "";
let activePriorityFilter = "";

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  loadStats();
  setInterval(checkHealth, 30000);
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".filter-group")) {
      closeAllDropdowns();
    }
  });
});

function toggleFilterMenu(menuId) {
  const menu = document.getElementById(menuId);
  closeAllDropdowns();
  menu.classList.toggle("hidden");
}

function closeAllDropdowns() {
  const menus = ["categoryFilter", "priorityFilter"];
  menus.forEach((id) => document.getElementById(id)?.classList.add("hidden"));
}

function applyTableFilter(type, value) {
  if (type === "category") activeCategoryFilter = value || "";
  if (type === "priority") activePriorityFilter = value || "";
  updateFilterToggleLabels();
  renderRecentTable(recentTicketsCache);
  closeAllDropdowns();
}

function clearTableFilters() {
  activeCategoryFilter = "";
  activePriorityFilter = "";
  updateFilterToggleLabels();
  renderRecentTable(recentTicketsCache);
}

function updateFilterToggleLabels() {
  document.getElementById("categoryToggleBtn").textContent = activeCategoryFilter
    ? `Category ▾: ${activeCategoryFilter}`
    : `Category ▾`;
  document.getElementById("priorityToggleBtn").textContent = activePriorityFilter
    ? `Priority ▾: ${activePriorityFilter}`
    : `Priority ▾`;
}

// Health check
async function checkHealth() {
  const badge = document.getElementById("statusBadge");
  try {
    const res = await fetch(`${API}/api/health`);
    const data = await res.json();
    if (data.ollama_available) {
      badge.innerHTML = `<span class="dot"></span> Online · ${data.model}`;
      badge.className = "status-badge online";
    } else {
      badge.innerHTML = `<span class="dot"></span> Degraded (no Ollama)`;
      badge.className = "status-badge offline";
    }
  } catch {
    badge.innerHTML = `<span class="dot"></span> Offline`;
    badge.className = "status-badge offline";
  }
}

// Load sample ticket
function loadSample() {
  const s = SAMPLES[sampleIdx % SAMPLES.length];
  sampleIdx++;
  document.getElementById("ticketId").value = s.id;
  document.getElementById("ticketTitle").value = s.title;
  document.getElementById("ticketDesc").value = s.desc;
}

function clearForm() {
  document.getElementById("ticketId").value = "TKT-001";
  document.getElementById("ticketTitle").value = "";
  document.getElementById("ticketDesc").value = "";
  document.getElementById("resultSection").classList.add("hidden");
}

// Classify ticket
async function classifyTicket() {
  const ticketId = document.getElementById("ticketId").value.trim();
  const title = document.getElementById("ticketTitle").value.trim();
  const description = document.getElementById("ticketDesc").value.trim();

  if (!title) {
    alert("Please enter a ticket title.");
    return;
  }

  showLoader(true);
  document.getElementById("resultSection").classList.add("hidden");

  try {
    const res = await fetch(`${API}/api/classify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticket_id: ticketId || "TKT-AUTO", title, description: description || undefined }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    renderResult(data);
    loadStats();
  } catch (err) {
    alert(`Classification failed: ${err.message}\n\nMake sure Ollama is running: ollama serve`);
  } finally {
    showLoader(false);
  }
}

function renderResult(data) {
  const section = document.getElementById("resultSection");
  const grid = document.getElementById("resultGrid");
  const confidence = data.confidence || 0;
  const confPct = Math.round(confidence * 100);

  grid.innerHTML = `
    <div class="result-item highlight">
      <div class="r-label">Category</div>
      <div class="r-value">${data.category}</div>
    </div>
    <div class="result-item">
      <div class="r-label">Subcategory</div>
      <div class="r-value">${data.subcategory}</div>
    </div>
    <div class="result-item">
      <div class="r-label">Priority</div>
      <div class="r-value"><span class="priority-badge priority-${data.priority}">${data.priority}</span></div>
    </div>
    <div class="result-item">
      <div class="r-label">Confidence</div>
      <div class="r-value">${confPct}%</div>
      <div class="confidence-bar"><div class="confidence-fill" style="width:${confPct}%"></div></div>
    </div>
    <div class="result-item">
      <div class="r-label">Model Used</div>
      <div class="r-value" style="font-size:0.9rem">${data.model_used}</div>
    </div>
    <div class="result-item">
      <div class="r-label">Processing</div>
      <div class="r-value" style="font-size:0.9rem">${data.processing_time_ms?.toFixed(0)}ms</div>
    </div>
    <div class="result-item">
      <div class="r-label">Attempts</div>
      <div class="r-value">${data.attempts}</div>
    </div>
    <div class="result-item">
      <div class="r-label">Ticket ID</div>
      <div class="r-value" style="font-size:0.9rem">${data.ticket_id}</div>
    </div>
  `;

  if (data.agent_reasoning) {
    document.getElementById("reasoningText").textContent = data.agent_reasoning;
    document.getElementById("reasoningBox").classList.remove("hidden");
  }

  section.classList.remove("hidden");
  section.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Load stats and charts
async function loadStats() {
  try {
    const res = await fetch(`${API}/api/logs`);
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("totalTickets").textContent = data.total_tickets;
    document.getElementById("avgConf").textContent = `${Math.round((data.average_confidence || 0) * 100)}%`;

    const cats = data.category_distribution || {};
    const topCat = Object.entries(cats).sort((a, b) => b[1] - a[1])[0];
    document.getElementById("topCategory").textContent = topCat ? topCat[0] : "—";

    const prios = data.priority_distribution || {};
    document.getElementById("criticalCount").textContent = prios["Critical"] || 0;

    renderCategoryChart(cats);
    renderPriorityChart(prios);
    recentTicketsCache = data.recent_tickets || [];
    renderRecentTable(recentTicketsCache);
    updateFilterToggleLabels();
  } catch (err) {
    console.warn("Stats load error:", err);
  }
}

const CHART_COLORS = ["#6c63ff", "#a78bfa", "#10b981", "#f59e0b", "#3b82f6", "#ef4444", "#ec4899"];

function renderCategoryChart(data) {
  const ctx = document.getElementById("categoryChart").getContext("2d");
  const labels = Object.keys(data);
  const values = Object.values(data);
  if (categoryChart) categoryChart.destroy();
  if (!labels.length) return;
  categoryChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: CHART_COLORS, borderWidth: 2, borderColor: "#1a1d2e" }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom", labels: { color: "#94a3b8", font: { size: 11 } } },
      },
    },
  });
}

function renderPriorityChart(data) {
  const ctx = document.getElementById("priorityChart").getContext("2d");
  const order = ["Critical", "High", "Medium", "Low"];
  const colors = { Critical: "#ef4444", High: "#f59e0b", Medium: "#3b82f6", Low: "#10b981" };
  const labels = order.filter((k) => k in data);
  const values = labels.map((k) => data[k]);
  if (priorityChart) priorityChart.destroy();
  if (!labels.length) return;
  priorityChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: labels.map((k) => colors[k] + "99"),
        borderColor: labels.map((k) => colors[k]),
        borderWidth: 2,
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { ticks: { color: "#94a3b8", stepSize: 1 }, grid: { color: "rgba(255,255,255,0.05)" } },
      },
    },
  });
}

function renderRecentTable(tickets) {
  const tbody = document.getElementById("recentBody");
  const filteredTickets = tickets.filter((t) => {
    if (activeCategoryFilter && (!t.category || t.category.toLowerCase() !== activeCategoryFilter.toLowerCase())) {
      return false;
    }
    if (activePriorityFilter && (!t.priority || t.priority.toLowerCase() !== activePriorityFilter.toLowerCase())) {
      return false;
    }
    return true;
  });

  if (!filteredTickets.length) {
    const message = activeCategoryFilter || activePriorityFilter
      ? "No tickets match the selected filters"
      : "No tickets classified yet";
    tbody.innerHTML = `<tr><td colspan="7" class="empty">${message}</td></tr>`;
    return;
  }

  tbody.innerHTML = filteredTickets.map((t) => {
    const conf = Math.round((t.confidence || 0) * 100);
    const date = t.created_at ? new Date(t.created_at).toLocaleString() : "—";
    return `
      <tr>
        <td><code>${t.ticket_id}</code></td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${t.title}</td>
        <td>${t.category || "—"}</td>
        <td><span class="priority-badge priority-${t.priority}">${t.priority || "—"}</span></td>
        <td>
          <div style="display:flex;align-items:center;gap:8px">
            ${conf}%
            <div class="confidence-bar" style="width:60px;display:inline-block"><div class="confidence-fill" style="width:${conf}%"></div></div>
          </div>
        </td>
        <td style="font-size:0.78rem;color:#94a3b8">${t.model_used || "—"}</td>
        <td style="font-size:0.78rem;color:#94a3b8">${date}</td>
      </tr>
    `;
  }).join("");
}

function showLoader(show) {
  const loader = document.getElementById("loader");
  const btn = document.querySelector(".btn.primary");
  loader.classList.toggle("hidden", !show);
  btn.disabled = show;
}