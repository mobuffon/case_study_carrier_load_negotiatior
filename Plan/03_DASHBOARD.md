# 03 — Dashboard Spec

## Goal

A single-page HTML dashboard served by the FastAPI backend at `/`. Shows use-case metrics from the calls DB. Built with vanilla JS + Chart.js (via CDN). No build step.

---

## File: `app/static/index.html`

Single file. No frameworks. Chart.js from cdnjs.

### Layout (top to bottom)

```
┌──────────────────────────────────────────────────────┐
│  Header: "Acme Logistics · Carrier Sales"            │
│  Subhead: "Live metrics from inbound carrier calls"  │
│  Refresh button (top-right)                          │
├──────────────────────────────────────────────────────┤
│  KPI tiles row (6 across on desktop, 2 across mobile)│
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌────┐│
│  │Total │ │Book- │ │Avg   │ │Avg   │ │Avg   │ │Elig││
│  │Calls │ │ing % │ │Rounds│ │Δ $   │ │Δ %   │ │%   ││
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └────┘│
├──────────────────────────────────────────────────────┤
│  Charts row                                          │
│  ┌──────────────────┐ ┌──────────────────┐          │
│  │ Outcome (bar)    │ │ Sentiment (donut)│          │
│  └──────────────────┘ └──────────────────┘          │
├──────────────────────────────────────────────────────┤
│  Recent calls table                                  │
│  Time | MC | Carrier | Load | Outcome | Sent | Rate │
│  …last 20 calls, most recent on top                  │
└──────────────────────────────────────────────────────┘
```

### KPI definitions

| Tile | Source | Format |
|---|---|---|
| Total Calls | `total_calls` | integer |
| Booking Rate | `conversion_rate` | percentage, 1 decimal (e.g. "37.5%") |
| Avg Rounds | `avg_negotiation_rounds` | 1 decimal (e.g. "1.8") |
| Avg Δ $ | `avg_rate_delta_dollars` | signed dollar amount ("+$45.20" / "-$12.50") |
| Avg Δ % | `avg_rate_delta_pct` | signed pct ("+2.4%" / "-0.7%") |
| Eligibility | `eligibility_rate` | percentage |

### Styling

- System font stack — no web fonts
- Light background (`#fafaf7`), card surfaces (`#ffffff`) with thin border (`#e6e4dd`)
- Accent color: a single brand-ish color, e.g. `#2563eb` (blue) for primary actions
- Outcome colors (deterministic mapping for chart):
  - `booked` → green `#16a34a`
  - `no_agreement` → amber `#d97706`
  - `not_eligible` → red `#dc2626`
  - `no_match` → gray `#6b7280`
  - `declined` → orange `#ea580c`
  - `abandoned` → light gray `#9ca3af`
  - `error` → dark red `#991b1b`
- Sentiment colors:
  - `positive` → `#16a34a`
  - `neutral` → `#6b7280`
  - `negative` → `#dc2626`

### Full code (drop-in)

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Acme Logistics · Carrier Sales Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #fafaf7;
    --surface: #ffffff;
    --border: #e6e4dd;
    --text: #1c1c1a;
    --text-muted: #5f5e5a;
    --accent: #2563eb;
    --pos: #16a34a;
    --neg: #dc2626;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg); color: var(--text);
  }
  header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px; }
  h1 { font-size: 22px; font-weight: 500; margin: 0; }
  .subhead { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
  button.refresh {
    background: var(--accent); color: white; border: none; padding: 8px 16px;
    border-radius: 6px; cursor: pointer; font-size: 14px;
  }
  button.refresh:hover { opacity: 0.9; }
  .kpi-row {
    display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 24px;
  }
  @media (max-width: 900px) {
    .kpi-row { grid-template-columns: repeat(2, 1fr); }
  }
  .kpi {
    background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
    padding: 16px;
  }
  .kpi-label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.4px; }
  .kpi-value { font-size: 24px; font-weight: 500; margin-top: 6px; }
  .kpi-value.pos { color: var(--pos); }
  .kpi-value.neg { color: var(--neg); }
  .chart-row {
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px;
  }
  @media (max-width: 900px) {
    .chart-row { grid-template-columns: 1fr; }
  }
  .card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
    padding: 16px;
  }
  .card h2 { font-size: 14px; font-weight: 500; margin: 0 0 12px; color: var(--text-muted); }
  .chart-wrap { height: 240px; position: relative; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--border); }
  th { font-weight: 500; color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.4px; }
  td.outcome { font-weight: 500; }
  .pill {
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 11px; font-weight: 500;
  }
  .pill.positive { background: #dcfce7; color: #166534; }
  .pill.neutral  { background: #f3f4f6; color: #374151; }
  .pill.negative { background: #fee2e2; color: #991b1b; }
  .empty { color: var(--text-muted); text-align: center; padding: 40px; }
  #api-key-prompt {
    background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
    padding: 24px; max-width: 400px; margin: 60px auto;
  }
  #api-key-prompt input {
    width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 4px;
    margin: 12px 0; font-size: 14px;
  }
</style>
</head>
<body>

<div id="auth-gate" style="display:none">
  <div id="api-key-prompt">
    <h2 style="margin:0 0 8px;font-size:16px">Dashboard access</h2>
    <p style="color:var(--text-muted);font-size:13px;margin:0">Enter the API key to view metrics.</p>
    <input id="api-key-input" type="password" placeholder="API key" />
    <button class="refresh" onclick="saveKey()">Continue</button>
  </div>
</div>

<div id="app" style="display:none">
  <header>
    <div>
      <h1>Acme Logistics · Carrier Sales</h1>
      <div class="subhead">Live metrics from inbound carrier calls</div>
    </div>
    <button class="refresh" onclick="refresh()">Refresh</button>
  </header>

  <div class="kpi-row">
    <div class="kpi"><div class="kpi-label">Total calls</div><div class="kpi-value" id="kpi-total">—</div></div>
    <div class="kpi"><div class="kpi-label">Booking rate</div><div class="kpi-value" id="kpi-conv">—</div></div>
    <div class="kpi"><div class="kpi-label">Avg rounds</div><div class="kpi-value" id="kpi-rounds">—</div></div>
    <div class="kpi"><div class="kpi-label">Avg Δ $</div><div class="kpi-value" id="kpi-delta-d">—</div></div>
    <div class="kpi"><div class="kpi-label">Avg Δ %</div><div class="kpi-value" id="kpi-delta-p">—</div></div>
    <div class="kpi"><div class="kpi-label">Eligibility</div><div class="kpi-value" id="kpi-elig">—</div></div>
  </div>

  <div class="chart-row">
    <div class="card">
      <h2>Outcome breakdown</h2>
      <div class="chart-wrap"><canvas id="chart-outcome"></canvas></div>
    </div>
    <div class="card">
      <h2>Carrier sentiment</h2>
      <div class="chart-wrap"><canvas id="chart-sentiment"></canvas></div>
    </div>
  </div>

  <div class="card">
    <h2>Recent calls</h2>
    <div id="calls-table-wrap">
      <table>
        <thead>
          <tr>
            <th>Time</th><th>MC</th><th>Carrier</th><th>Load</th>
            <th>Outcome</th><th>Sent.</th><th>Rounds</th><th>Loadboard</th><th>Agreed</th>
          </tr>
        </thead>
        <tbody id="calls-tbody"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
const OUTCOME_COLORS = {
  booked: "#16a34a", no_agreement: "#d97706", not_eligible: "#dc2626",
  no_match: "#6b7280", declined: "#ea580c", abandoned: "#9ca3af", error: "#991b1b"
};
const SENTIMENT_COLORS = { positive: "#16a34a", neutral: "#6b7280", negative: "#dc2626" };

let outcomeChart = null;
let sentimentChart = null;

function getKey() { return sessionStorage.getItem("api_key"); }
function setKey(k) { sessionStorage.setItem("api_key", k); }

function saveKey() {
  const k = document.getElementById("api-key-input").value.trim();
  if (!k) return;
  setKey(k);
  init();
}

async function fetchJSON(path) {
  const r = await fetch(path, { headers: { "X-API-Key": getKey() } });
  if (r.status === 401) {
    sessionStorage.removeItem("api_key");
    showAuthGate();
    throw new Error("auth failed");
  }
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

function fmtPct(x) { return (x * 100).toFixed(1) + "%"; }
function fmtSignedDollar(x) {
  const sign = x >= 0 ? "+" : "−";
  return sign + "$" + Math.abs(x).toFixed(2);
}
function fmtSignedPct(x) {
  const sign = x >= 0 ? "+" : "−";
  return sign + Math.abs(x).toFixed(2) + "%";
}
function fmtTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function applyDeltaColor(el, value) {
  el.classList.remove("pos", "neg");
  if (value > 0) el.classList.add("pos");
  else if (value < 0) el.classList.add("neg");
}

async function loadMetrics() {
  const m = await fetchJSON("/metrics/summary");

  document.getElementById("kpi-total").textContent = m.total_calls;
  document.getElementById("kpi-conv").textContent = fmtPct(m.conversion_rate);
  document.getElementById("kpi-rounds").textContent = m.avg_negotiation_rounds.toFixed(1);

  const deltaD = document.getElementById("kpi-delta-d");
  deltaD.textContent = fmtSignedDollar(m.avg_rate_delta_dollars);
  applyDeltaColor(deltaD, m.avg_rate_delta_dollars);

  const deltaP = document.getElementById("kpi-delta-p");
  deltaP.textContent = fmtSignedPct(m.avg_rate_delta_pct);
  applyDeltaColor(deltaP, m.avg_rate_delta_pct);

  document.getElementById("kpi-elig").textContent = fmtPct(m.eligibility_rate);

  renderOutcomeChart(m.outcome_breakdown);
  renderSentimentChart(m.sentiment_breakdown);
}

function renderOutcomeChart(breakdown) {
  const ctx = document.getElementById("chart-outcome");
  const entries = Object.entries(breakdown).sort((a, b) => b[1] - a[1]);
  const labels = entries.map(([k]) => k.replace(/_/g, " "));
  const data = entries.map(([_, v]) => v);
  const colors = entries.map(([k]) => OUTCOME_COLORS[k] || "#9ca3af");

  if (outcomeChart) outcomeChart.destroy();
  outcomeChart = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ data, backgroundColor: colors, borderRadius: 4 }] },
    options: {
      maintainAspectRatio: false,
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, ticks: { precision: 0 } },
        y: { grid: { display: false } }
      }
    }
  });
}

function renderSentimentChart(breakdown) {
  const ctx = document.getElementById("chart-sentiment");
  const entries = Object.entries(breakdown);
  const labels = entries.map(([k]) => k);
  const data = entries.map(([_, v]) => v);
  const colors = entries.map(([k]) => SENTIMENT_COLORS[k] || "#9ca3af");

  if (sentimentChart) sentimentChart.destroy();
  sentimentChart = new Chart(ctx, {
    type: "doughnut",
    data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 0 }] },
    options: {
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: { legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 12 } } } }
    }
  });
}

async function loadCalls() {
  const calls = await fetchJSON("/calls?limit=20");
  const tbody = document.getElementById("calls-tbody");
  if (calls.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty">No calls yet</td></tr>`;
    return;
  }
  tbody.innerHTML = calls.map(c => `
    <tr>
      <td>${fmtTime(c.created_at)}</td>
      <td>${c.mc_number ?? "—"}</td>
      <td>${c.carrier_name ?? "—"}</td>
      <td>${c.load_id ?? "—"}</td>
      <td class="outcome" style="color:${OUTCOME_COLORS[c.outcome] || '#111'}">${c.outcome.replace(/_/g, " ")}</td>
      <td><span class="pill ${c.sentiment}">${c.sentiment}</span></td>
      <td>${c.negotiation_rounds}</td>
      <td>${c.loadboard_rate != null ? "$" + c.loadboard_rate.toFixed(2) : "—"}</td>
      <td>${c.agreed_rate != null ? "$" + c.agreed_rate.toFixed(2) : "—"}</td>
    </tr>
  `).join("");
}

async function refresh() {
  try {
    await Promise.all([loadMetrics(), loadCalls()]);
  } catch (e) {
    console.error(e);
  }
}

function showAuthGate() {
  document.getElementById("auth-gate").style.display = "block";
  document.getElementById("app").style.display = "none";
}

function init() {
  if (!getKey()) {
    showAuthGate();
    return;
  }
  document.getElementById("auth-gate").style.display = "none";
  document.getElementById("app").style.display = "block";
  refresh();
  setInterval(refresh, 30_000); // auto-refresh every 30s
}

init();
</script>
</body>
</html>
```

---

## Acceptance Criteria

- [ ] Dashboard loads at `https://<your-app>.fly.dev/` with no console errors
- [ ] If no API key in sessionStorage, the gate appears
- [ ] After entering the correct API key, the dashboard renders
- [ ] Wrong key shows the gate again, doesn't crash
- [ ] Empty-state (zero calls) renders without breaking — KPIs show 0 / "—", charts gracefully handle empty data, table shows "No calls yet"
- [ ] After at least 1 call, all 6 KPIs show real numbers
- [ ] Outcome and sentiment charts render with correct colors
- [ ] Recent calls table shows last 20 calls, most recent on top
- [ ] Auto-refreshes every 30s without flicker
- [ ] Manual refresh button works
- [ ] Mobile-responsive: KPIs stack 2-wide, charts stack vertically

---

## Notes

- **API key in sessionStorage**: documented tradeoff. For a real product, replace with proper auth (Cognito, Clerk, or a session cookie from server-side login). For the demo, mention this in the README and Acme doc.
- **Chart.js version**: 4.4.4 is current. If you upgrade, verify `type: "doughnut"` and the option shapes.
- **No build step**: this is intentional — keeps the deployment simple and reviewer-friendly.
