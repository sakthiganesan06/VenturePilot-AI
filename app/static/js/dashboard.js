/* ═══════════════════════════════════════════════════════════════════════
   VenturPilot AI — Dashboard JavaScript
   Renders all 23 interactive sections from Blueprint JSON
   ═══════════════════════════════════════════════════════════════════════ */

let BP = null; // Global blueprint

// ── Color Palettes ────────────────────────────────────────────────────────
const COLORS = {
  accent:  "#3b82d4",
  purple:  "#7c5cd8",
  success: "#22c55e",
  warning: "#f59e0b",
  danger:  "#ef4444",
  muted:   "#64748b",
  palette: ["#3b82d4","#7c5cd8","#22c55e","#f59e0b","#ef4444","#06b6d4","#ec4899","#84cc16"],
};

// ── Chart defaults ─────────────────────────────────────────────────────────
Chart.defaults.color = "#94a3b8";
Chart.defaults.borderColor = "rgba(255,255,255,0.06)";
Chart.defaults.font.family = "-apple-system,'Segoe UI',system-ui,sans-serif";

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const raw = sessionStorage.getItem("blueprint");
  if (!raw) {
    document.getElementById("noBlueprintNotice").style.display = "";
    return;
  }
  try {
    BP = JSON.parse(raw);
    initDashboard();
  } catch(e) {
    document.getElementById("noBlueprintNotice").style.display = "";
  }
});

function initDashboard() {
  document.getElementById("noBlueprintNotice").style.display = "none";
  document.getElementById("dashNav").style.display = "";
  document.getElementById("dashboardContent").style.display = "";
  document.getElementById("chatFloating").style.display = "flex";

  // Title
  const name = BP?.executive_summary?.startup_names?.[0] || "Your Startup";
  document.getElementById("dashTitle").textContent = `${name} — Blueprint Dashboard`;

  renderScores();
  renderExecutiveSummary();
  renderBMC();
  renderMarketAnalysis();
  renderCompetitors();
  renderSWOT();
  renderBudget();
  renderRevenueModel();
  renderFunding();
  renderGovernmentSchemes();
  renderLegalChecklist();
  renderRoadmap();
  renderRisks();
  renderInvestorReadiness();
  renderImprovements();
  renderStartupNames();
  renderElevatorPitch();
  renderPitchDeck();
  renderRecommendations();
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 1: SCORES
// ══════════════════════════════════════════════════════════════════════════
function renderScores() {
  const sc = BP.scores || {};
  // Overall gauge
  drawGaugeCanvas("gaugeOverall", sc.overall || 0);
  document.getElementById("scoreOverallLabel").textContent = scoreLabel(sc.overall || 0);

  // Dimension bars
  const dims = [
    ["Innovation",         "innovation"],
    ["Market Demand",      "market_demand"],
    ["Investment Potential","investment_potential"],
    ["Feasibility",        "feasibility"],
    ["Scalability",        "scalability"],
  ];
  const container = document.getElementById("scoresBars");
  container.innerHTML = "";
  dims.forEach(([label, key]) => {
    const val = sc[key] || 0;
    const color = val >= 75 ? COLORS.success : val >= 50 ? COLORS.warning : COLORS.danger;
    container.innerHTML += `
      <div class="score-bar-wrap">
        <div class="score-bar-label"><span>${label}</span><strong>${val}/100</strong></div>
        <div class="score-bar-track"><div class="score-bar-fill" data-width="${val}" style="background:${color};"></div></div>
      </div>`;
  });
  // Animate bars after render
  requestAnimationFrame(() => {
    document.querySelectorAll(".score-bar-fill").forEach(el => {
      el.style.width = (el.dataset.width || 0) + "%";
    });
  });

  setWhyPanel("why-scores", sc.why);
}

function scoreLabel(val) {
  if (val >= 80) return "🚀 Strong Potential";
  if (val >= 65) return "✅ Good Potential";
  if (val >= 50) return "⚠️ Moderate";
  return "🔴 Needs Work";
}

function drawGaugeCanvas(canvasId, val) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const cx = canvas.width / 2, cy = canvas.height / 2, r = 70;
  const start = -Math.PI * 0.8;
  const end = start + (Math.PI * 1.6) * (val / 100);
  const color = val >= 75 ? COLORS.success : val >= 50 ? COLORS.warning : COLORS.danger;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // Track
  ctx.beginPath(); ctx.arc(cx, cy, r, -Math.PI*0.8, Math.PI*0.8);
  ctx.strokeStyle = "rgba(255,255,255,0.06)"; ctx.lineWidth = 14; ctx.lineCap = "round"; ctx.stroke();
  // Fill
  ctx.beginPath(); ctx.arc(cx, cy, r, start, end);
  ctx.strokeStyle = color; ctx.lineWidth = 14; ctx.lineCap = "round"; ctx.stroke();
  // Text
  ctx.fillStyle = "#e2e8f0"; ctx.font = "bold 28px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText(val, cx, cy);
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 2: EXECUTIVE SUMMARY
// ══════════════════════════════════════════════════════════════════════════
function renderExecutiveSummary() {
  const es = BP.executive_summary || {};
  const cards = [
    { icon: "bi-building", label: "Industry",       val: es.industry || "—" },
    { icon: "bi-bullseye", label: "Target Customers", val: es.target_customers || "—" },
    { icon: "bi-cash-stack",label:"Estimated Budget", val: es.estimated_budget || "—" },
    { icon: "bi-tag-fill", label: "Tagline",         val: es.tagline || "—" },
    { icon: "bi-exclamation-circle", label: "Problem", val: es.problem || "—" },
    { icon: "bi-lightbulb-fill",     label: "Solution", val: es.solution || "—" },
  ];
  const container = document.getElementById("execCards");
  container.innerHTML = cards.map((c, i) => `
    <div class="col-md-6 col-lg-4" data-aos="fade-up" data-aos-delay="${i*60}">
      <div class="glass-card p-4 h-100">
        <div class="d-flex align-items-center gap-2 mb-2">
          <i class="bi ${c.icon} text-accent"></i>
          <span class="small text-muted fw-semibold text-uppercase" style="font-size:11px;letter-spacing:.08em;">${c.label}</span>
        </div>
        <p class="mb-0 fw-semibold">${c.val}</p>
      </div>
    </div>`).join("");

  if (es.startup_names?.length) {
    container.insertAdjacentHTML("beforeend", `
      <div class="col-12" data-aos="fade-up">
        <div class="glass-card p-4">
          <div class="d-flex align-items-center gap-2 mb-3"><i class="bi bi-stars text-accent"></i><span class="fw-semibold">AI-Suggested Startup Names</span></div>
          <div class="chips-wrap">${es.startup_names.map(n => `<span class="chip">${n}</span>`).join("")}</div>
        </div>
      </div>`);
  }
  setWhyPanel("why-exec", es.why);
  AOS.refresh();
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 3: BUSINESS MODEL CANVAS
// ══════════════════════════════════════════════════════════════════════════
function renderBMC() {
  const bmc = BP.business_model_canvas || {};
  const sections = [
    { key: "key_partners",        label: "Key Partners",         cls: "bmc-kp" },
    { key: "key_activities",      label: "Key Activities",        cls: "bmc-ka" },
    { key: "key_resources",       label: "Key Resources",         cls: "bmc-kr" },
    { key: "value_propositions",  label: "Value Propositions",    cls: "bmc-vp" },
    { key: "customer_relationships", label: "Customer Relationships", cls: "bmc-cr" },
    { key: "channels",            label: "Channels",              cls: "bmc-ch" },
    { key: "customer_segments",   label: "Customer Segments",     cls: "bmc-cs" },
    { key: "cost_structure",      label: "Cost Structure",        cls: "bmc-cost" },
    { key: "revenue_streams",     label: "Revenue Streams",       cls: "bmc-rev" },
  ];
  const grid = document.getElementById("bmcGrid");
  grid.innerHTML = sections.map(s => {
    const items = bmc[s.key] || [];
    return `
      <div class="bmc-cell ${s.cls}" onclick="openBMCModal('${s.key}','${s.label}')">
        <div class="bmc-cell-title">${s.label}</div>
        <ul class="bmc-cell-content ps-3 mb-0">
          ${items.slice(0, 3).map(i => `<li>${i}</li>`).join("")}
          ${items.length > 3 ? `<li class="text-muted">+${items.length - 3} more…</li>` : ""}
        </ul>
      </div>`;
  }).join("");
  setWhyPanel("why-bmc", bmc.why);
}

function openBMCModal(key, label) {
  const bmc = BP.business_model_canvas || {};
  const items = bmc[key] || [];
  document.getElementById("bmcModalTitle").textContent = label;
  document.getElementById("bmcModalBody").innerHTML = `
    <ul class="list-unstyled mb-0">
      ${items.map(i => `<li class="py-1 border-bottom border-secondary d-flex gap-2"><i class="bi bi-check2 text-accent mt-1"></i><span>${i}</span></li>`).join("")}
    </ul>
    ${bmc.why ? `<div class="why-panel mt-3">${bmc.why}</div>` : ""}`;
  new bootstrap.Modal(document.getElementById("bmcModal")).show();
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 4: MARKET ANALYSIS
// ══════════════════════════════════════════════════════════════════════════
function renderMarketAnalysis() {
  const ma = BP.market_analysis || {};

  function parseMarketSize(val) {
    if (!val) return 0;
    let clean = val.replace(/[₹$,\s]/g, "");
    let num = parseFloat(clean);
    if (isNaN(num)) return 0;
    let lower = val.toLowerCase();
    if (lower.includes("cr") || lower.includes("crore")) {
      return num * 10000000;
    }
    if (lower.includes("billion") || lower.includes("b")) {
      return num * 1000000000;
    }
    if (lower.includes("million") || lower.includes("m")) {
      return num * 1000000;
    }
    if (lower.includes("lakh") || lower.includes("l")) {
      return num * 100000;
    }
    return num;
  }

  const tamVal = parseMarketSize(ma.tam) || 100;
  const samVal = parseMarketSize(ma.sam) || 20;
  const somVal = parseMarketSize(ma.som) || 2;

  // TAM SAM SOM chart
  const ctx = document.getElementById("chartTAMSAMSOM")?.getContext("2d");
  if (ctx) {
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: ["TAM", "SAM", "SOM"],
        datasets: [{
          label: "Market Size",
          data: [tamVal, samVal, somVal],
          backgroundColor: [COLORS.accent, COLORS.purple, COLORS.success],
          borderRadius: 8,
        }]
      },
      options: {
        responsive: true,
        plugins: {
          title: { display: true, text: "TAM / SAM / SOM Breakdown", font: { size: 14 } },
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const vals = [ma.tam, ma.sam, ma.som];
                return " " + (vals[ctx.dataIndex] || ctx.raw);
              }
            }
          }
        },
        scales: { y: { display: false }, x: { grid: { display: false } } }
      }
    });
  }

  // Metric cards
  const metrics = [
    { label: "Market Size",   val: ma.market_size || "—",   icon: "bi-graph-up",       color: "accent" },
    { label: "Growth Rate",   val: ma.growth_rate || "—",   icon: "bi-arrow-up-right", color: "success" },
    { label: "TAM",           val: ma.tam || "—",            icon: "bi-globe",          color: "purple" },
    { label: "SAM",           val: ma.sam || "—",            icon: "bi-crosshair",      color: "warning" },
    { label: "SOM",           val: ma.som || "—",            icon: "bi-bullseye",       color: "accent" },
  ];
  document.getElementById("marketMetricCards").innerHTML = metrics.map(m => `
    <div class="col-6 col-lg-4">
      <div class="glass-card p-3 text-center">
        <i class="bi ${m.icon} text-${m.color} mb-1 d-block" style="font-size:1.4rem;"></i>
        <div class="fw-bold small">${m.val}</div>
        <div class="text-muted" style="font-size:11px;">${m.label}</div>
      </div>
    </div>`).join("");

  // Trends
  const trends = ma.trends || [];
  document.getElementById("marketTrends").innerHTML = trends.map((t, i) => `
    <div class="d-flex gap-2 mb-2"><span class="badge" style="background:rgba(59,130,212,0.15);color:${COLORS.accent};min-width:22px;">${i+1}</span><span class="small">${t}</span></div>`).join("");

  // Customer Personas
  const personas = ma.customer_personas || [];
  document.getElementById("personaCards").innerHTML = personas.map(p => `
    <div class="col-md-4">
      <div class="glass-card p-4 h-100">
        <div class="d-flex align-items-center gap-2 mb-3">
          <div style="width:40px;height:40px;background:rgba(59,130,212,0.15);border-radius:50%;display:flex;align-items:center;justify-content:center;"><i class="bi bi-person-fill text-accent"></i></div>
          <div><div class="fw-bold small">${p.name || "Persona"}</div><div class="text-muted" style="font-size:11px;">Age: ${p.age || "—"}</div></div>
        </div>
        <p class="text-muted small mb-2">😣 <strong>Pain:</strong> ${p.pain || "—"}</p>
        <p class="text-muted small mb-0">💰 <strong>WTP:</strong> ${p.willingness_to_pay || "—"}</p>
      </div>
    </div>`).join("");

  setWhyPanel("why-market", ma.why);
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 5: COMPETITORS
// ══════════════════════════════════════════════════════════════════════════
function renderCompetitors() {
  const competitors = BP.competitors || [];
  const container = document.getElementById("competitorCards");
  container.innerHTML = competitors.map(c => {
    const isUs = c.name === "Our Product";
    return `
      <div class="col-md-6 col-lg-3">
        <div class="glass-card p-4 h-100 ${isUs ? "comp-our border border-2" : ""}">
          ${isUs ? '<div class="mb-2"><span class="badge bg-accent text-white">⭐ Our Product</span></div>' : ""}
          <h6 class="fw-bold">${c.name}</h6>
          <div class="text-accent fw-semibold mb-3">${c.pricing}</div>
          <div class="mb-2">
            <div class="text-muted mb-1" style="font-size:11px;text-transform:uppercase;font-weight:600;">Strengths</div>
            ${(c.strengths||[]).map(s => `<div class="d-flex gap-1 mb-1 small"><i class="bi bi-check-circle-fill text-success mt-1" style="font-size:10px;"></i><span>${s}</span></div>`).join("")}
          </div>
          <div>
            <div class="text-muted mb-1" style="font-size:11px;text-transform:uppercase;font-weight:600;">Weaknesses</div>
            ${(c.weaknesses||[]).map(w => `<div class="d-flex gap-1 mb-1 small"><i class="bi bi-x-circle-fill text-danger mt-1" style="font-size:10px;"></i><span>${w}</span></div>`).join("")}
          </div>
        </div>
      </div>`;
  }).join("");

  // Comparison bar chart
  const ctx = document.getElementById("chartCompetitors")?.getContext("2d");
  if (ctx && competitors.length) {
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: competitors.map(c => c.name),
        datasets: [{
          label: "Market Share %",
          data: competitors.map(c => c.market_share || 0),
          backgroundColor: competitors.map((c, i) => c.name === "Our Product" ? COLORS.accent : COLORS.palette[i % COLORS.palette.length]),
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        plugins: { title: { display: true, text: "Competitor Market Share Comparison", font: { size: 13 } }, legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { callback: v => v + "%" } }, x: { grid: { display: false } } }
      }
    });
  }

  document.getElementById("compAdvantage").textContent = BP.competitive_advantage || "—";
  document.getElementById("marketGap").textContent = BP.market_gap || "—";
  setWhyPanel("why-comp", "Competitor analysis reveals your key differentiators and market positioning opportunities.");
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 6: SWOT
// ══════════════════════════════════════════════════════════════════════════
function renderSWOT() {
  const swot = BP.swot || {};
  const items = [
    { key: "strengths",    label: "💪 Strengths",    cls: "swot-card-strength",    color: "#22c55e" },
    { key: "weaknesses",   label: "⚠️ Weaknesses",   cls: "swot-card-weakness",   color: "#f59e0b" },
    { key: "opportunities",label: "🚀 Opportunities", cls: "swot-card-opportunity", color: "#3b82d4" },
    { key: "threats",      label: "🛡️ Threats",      cls: "swot-card-threat",      color: "#ef4444" },
  ];
  document.getElementById("swotCards").innerHTML = items.map(s => `
    <div class="col-md-6">
      <div class="glass-card p-4 h-100 ${s.cls}">
        <h6 class="fw-bold mb-3" style="color:${s.color}">${s.label}</h6>
        <ul class="list-unstyled mb-0">
          ${(swot[s.key] || []).map(i => `<li class="mb-2 small d-flex gap-2"><span style="color:${s.color};">•</span><span>${i}</span></li>`).join("")}
        </ul>
      </div>
    </div>`).join("");
  setWhyPanel("why-swot", swot.why);
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 7: BUDGET
// ══════════════════════════════════════════════════════════════════════════
function renderBudget() {
  const budget = BP.budget || {};
  const keys   = ["development","infrastructure","marketing","operations","hiring","legal","miscellaneous"];
  const vals   = keys.map(k => {
    const v = budget[k];
    if (typeof v === "string") return parseInt(v.replace(/[^0-9]/g, "")) || 0;
    return parseInt(v) || 0;
  });
  const labels = keys.map(k => k.charAt(0).toUpperCase() + k.slice(1));
  
  let total = budget.total;
  if (typeof total === "string") {
    total = parseInt(total.replace(/[^0-9]/g, "")) || 0;
  } else {
    total = parseInt(total) || 0;
  }
  if (!total) total = vals.reduce((a,b) => a+b, 0);

  // Pie chart
  const pieCx = document.getElementById("chartBudgetPie")?.getContext("2d");
  if (pieCx) {
    new Chart(pieCx, {
      type: "doughnut",
      data: { labels, datasets: [{ data: vals, backgroundColor: COLORS.palette, borderWidth: 2, borderColor: "rgba(0,0,0,0.3)" }] },
      options: {
        responsive: true,
        plugins: { title: { display: true, text: "Budget Distribution", font: { size: 13 } },
          legend: { position: "bottom", labels: { boxWidth: 10, padding: 12 } } }
      }
    });
  }

  // Bar chart
  const barCx = document.getElementById("chartBudgetBar")?.getContext("2d");
  if (barCx) {
    new Chart(barCx, {
      type: "bar",
      data: {
        labels,
        datasets: [{ label: "Amount (₹)", data: vals, backgroundColor: COLORS.palette, borderRadius: 6 }]
      },
      options: {
        responsive: true,
        plugins: { title: { display: true, text: "Budget by Category", font: { size: 13 } }, legend: { display: false } },
        scales: {
          y: { ticks: { callback: v => "₹" + (v/100000).toFixed(1) + "L" } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // Budget detail cards
  document.getElementById("budgetCards").innerHTML = keys.map((k, i) => `
    <div class="col-md-6 col-lg-3">
      <div class="glass-card p-3 text-center">
        <div class="fw-bold" style="color:${COLORS.palette[i]};">₹${fmtNum(vals[i])}</div>
        <div class="text-muted small">${labels[i]}</div>
        <div class="text-muted" style="font-size:11px;">${vals[i] ? ((vals[i]/total)*100).toFixed(1) : 0}%</div>
      </div>
    </div>`).join("") + `
    <div class="col-12">
      <div class="glass-card p-3 border-accent text-center">
        <div class="fw-bold fs-5 text-accent">₹${fmtNum(total)}</div>
        <div class="text-muted small">Total Budget</div>
      </div>
    </div>`;

  setWhyPanel("why-budget", budget.why);
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 8: REVENUE MODEL
// ══════════════════════════════════════════════════════════════════════════
function renderRevenueModel() {
  const rm = BP.revenue_model || {};
  const options = rm.options || [];
  document.getElementById("revenueCards").innerHTML = options.map(o => `
    <div class="col-md-6 col-lg-4">
      <div class="glass-card p-4 h-100 ${o.recommended ? "revenue-card-recommended border border-2" : ""}">
        ${o.recommended ? '<div class="mb-2"><span class="revenue-recommended-badge">⭐ Recommended</span></div>' : ""}
        <h6 class="fw-bold">${o.model}</h6>
        <div class="mb-2"><div class="text-muted" style="font-size:11px;">FIT SCORE</div>
          <div class="d-flex align-items-center gap-2 mt-1">
            <div class="score-bar-track flex-grow-1"><div class="score-bar-fill" data-width="${o.score}" style="background:${o.recommended?COLORS.accent:COLORS.muted};width:0;"></div></div>
            <span class="small fw-bold">${o.score}/100</span>
          </div>
        </div>
        <div class="text-muted small">📈 MRR Potential: <strong class="text-white">${o.mrr_potential || "—"}</strong></div>
      </div>
    </div>`).join("");
  requestAnimationFrame(() => document.querySelectorAll(".score-bar-fill").forEach(el => { el.style.width = (el.dataset.width || 0) + "%"; }));
  setWhyPanel("why-revenue", rm.why);
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 9: FUNDING
// ══════════════════════════════════════════════════════════════════════════
function renderFunding() {
  const funding = BP.funding || [];
  const FUND_ICONS = { Bootstrap: "bi-piggy-bank", "Angel Investors": "bi-person-badge-fill", "Venture Capital": "bi-building-fill", "Startup India Seed Fund": "bi-flag-fill", SIDBI: "bi-bank", "SIDBI SCALE": "bi-bank" };
  document.getElementById("fundingCards").innerHTML = funding.map((f, i) => `
    <div class="col-md-6 col-lg-4">
      <div class="glass-card p-4 h-100 funding-card" onclick="toggleFundingDetails(this)">
        <div class="d-flex align-items-start gap-3 mb-3">
          <div class="tech-icon" style="font-size:1.6rem;color:${COLORS.palette[i%COLORS.palette.length]};"><i class="bi ${FUND_ICONS[f.type] || 'bi-currency-rupee'}"></i></div>
          <div>
            <h6 class="fw-bold mb-0">${f.type}</h6>
            <div class="text-muted small">${f.stage}</div>
          </div>
        </div>
        <div class="fw-semibold text-accent mb-2">${f.amount}</div>
        <div class="small text-muted mb-3">${f.eligibility}</div>
        <div class="funding-details">
          <div class="mb-2 small"><i class="bi bi-check-circle text-success me-2"></i><strong>Advantage:</strong> ${f.advantage}</div>
          <div class="small"><i class="bi bi-exclamation-circle text-warning me-2"></i><strong>Challenge:</strong> ${f.challenge}</div>
        </div>
        <div class="text-muted small mt-2" style="font-size:11px;">👆 Click to expand</div>
      </div>
    </div>`).join("");
  setWhyPanel("why-funding", "Funding path tailored to your startup stage, team, and Indian ecosystem opportunity.");
}

function toggleFundingDetails(card) {
  const det = card.querySelector(".funding-details");
  det.classList.toggle("show");
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 10: GOVERNMENT SCHEMES
// ══════════════════════════════════════════════════════════════════════════
function renderGovernmentSchemes() {
  const schemes = BP.government_schemes || [];
  const SCHEME_COLORS = [COLORS.accent, COLORS.purple, COLORS.success, COLORS.warning];
  document.getElementById("schemeCards").innerHTML = schemes.map((s, i) => `
    <div class="col-md-6">
      <div class="glass-card p-4 h-100 scheme-card" onclick="openSchemeModal(${i})">
        <div class="d-flex align-items-center justify-content-between mb-3">
          <div class="d-flex align-items-center gap-2">
            <div style="width:36px;height:36px;background:rgba(59,130,212,0.15);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;">🏛️</div>
            <h6 class="fw-bold mb-0">${s.name}</h6>
          </div>
          <span class="scheme-ministry-badge">${s.ministry}</span>
        </div>
        <p class="text-muted small mb-3">${s.benefit}</p>
        <div class="d-flex gap-2">
          <button class="btn btn-outline-accent btn-sm">View Details <i class="bi bi-arrow-right ms-1"></i></button>
        </div>
      </div>
    </div>`).join("");
  setWhyPanel("why-schemes", "Schemes recommended using RAG retrieval from Indian government startup policy knowledge base.");
}

function openSchemeModal(idx) {
  const s = (BP.government_schemes || [])[idx];
  if (!s) return;
  document.getElementById("schemeModalTitle").textContent = `🏛️ ${s.name}`;
  document.getElementById("schemeModalBody").innerHTML = `
    <div class="row g-3">
      <div class="col-md-6">
        <div class="why-panel"><strong>Ministry:</strong> ${s.ministry}</div>
      </div>
      <div class="col-12"><h6 class="fw-bold">Benefits</h6><p class="text-muted">${s.benefit}</p></div>
      <div class="col-12"><h6 class="fw-bold">Eligibility</h6><p class="text-muted">${s.eligibility}</p></div>
      <div class="col-12">
        <h6 class="fw-bold">Required Documents</h6>
        <ul class="text-muted">${(s.docs||[]).map(d=>`<li>${d}</li>`).join("")}</ul>
      </div>
      <div class="col-12">
        <div class="alert alert-info border-0" style="background:rgba(59,130,212,0.1);">
          <i class="bi bi-info-circle me-2"></i>Apply via <strong>${s.name.includes("Startup India")?"startupindia.gov.in":s.name.includes("MSME")?"udyamregistration.gov.in":"respective government portal"}</strong>
        </div>
      </div>
    </div>`;
  new bootstrap.Modal(document.getElementById("schemeModal")).show();
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 11: LEGAL CHECKLIST
// ══════════════════════════════════════════════════════════════════════════
function renderLegalChecklist() {
  const items = BP.legal_checklist || [];
  document.getElementById("legalChecklist").innerHTML = items.map((item, i) => `
    <div class="legal-item" onclick="toggleLegalDetail(${i})">
      <div class="legal-check" id="lc-${i}" onclick="event.stopPropagation(); toggleLegalCheck(${i})"></div>
      <div class="flex-grow-1">
        <div class="d-flex flex-wrap align-items-center gap-2 mb-1">
          <span class="fw-semibold small">${item.item}</span>
          <span class="priority-${item.priority} small">${item.priority}</span>
        </div>
        <div class="d-flex gap-3 text-muted" style="font-size:12px;">
          <span>💰 ${item.estimated_cost}</span>
          <span>⏱️ ${item.timeline}</span>
        </div>
        <div class="legal-item-detail" id="ld-${i}">
          Click items in the checklist to mark as completed. Cost estimate: <strong>${item.estimated_cost}</strong>. 
          Timeline: <strong>${item.timeline}</strong>. Priority: <strong>${item.priority}</strong>.
          Consult a certified CA or legal advisor for actual compliance.
        </div>
      </div>
    </div>`).join("");
}

function toggleLegalCheck(i) {
  const el = document.getElementById(`lc-${i}`);
  el.classList.toggle("checked");
  el.innerHTML = el.classList.contains("checked") ? '<i class="bi bi-check-lg text-white" style="font-size:12px;"></i>' : "";
}
function toggleLegalDetail(i) { document.getElementById(`ld-${i}`)?.classList.toggle("show"); }

// ══════════════════════════════════════════════════════════════════════════
// SECTION 12: ROADMAP
// ══════════════════════════════════════════════════════════════════════════
function renderRoadmap() {
  const roadmap = BP.roadmap || [];
  document.getElementById("roadmapTimeline").innerHTML = roadmap.map((step, i) => `
    <div class="roadmap-item" onclick="toggleRoadmapTasks(${i})">
      <div class="roadmap-item-body">
        <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-1">
          <div>
            <span class="fw-bold">${step.phase}</span>
            <span class="text-muted small ms-2">${step.duration}</span>
          </div>
          <span class="badge bg-accent-subtle text-accent border border-accent" style="font-size:11px;">🏆 ${step.milestone}</span>
        </div>
        <div class="roadmap-tasks" id="rt-${i}">
          ${(step.tasks||[]).map(t => `<div class="d-flex gap-2 mb-1 small"><i class="bi bi-check2 text-success"></i><span>${t}</span></div>`).join("")}
        </div>
      </div>
    </div>`).join("");
}

function toggleRoadmapTasks(i) { document.getElementById(`rt-${i}`)?.classList.toggle("show"); }

// ══════════════════════════════════════════════════════════════════════════
// SECTION 13: SIMULATION
// ══════════════════════════════════════════════════════════════════════════
function runSimulation() {
  const sim = BP.simulation || {};
  document.getElementById("simulationDash").style.display = "";
  document.getElementById("simulateBtn").innerHTML = '<i class="bi bi-check-circle me-1"></i>Running ✓';
  document.getElementById("simulateBtn").disabled = true;

  const months = Array.from({length:12}, (_,i) => `M${i+1}`);
  const rev = (sim.monthly_revenue || []).map(x => {
    if (typeof x === "string") return parseInt(x.replace(/[^0-9]/g, "")) || 0;
    return parseInt(x) || 0;
  });
  const exp = (sim.monthly_expenses || []).map(x => {
    if (typeof x === "string") return parseInt(x.replace(/[^0-9]/g, "")) || 0;
    return parseInt(x) || 0;
  });
  const cust = (sim.customers || []).map(x => {
    if (typeof x === "string") return parseInt(x.replace(/[^0-9]/g, "")) || 0;
    return parseInt(x) || 0;
  });

  // KPI cards
  const breakEven = sim.break_even_month;
  const runway = sim.cash_runway_months;
  
  let burnRate = sim.burn_rate;
  if (typeof burnRate === "string") {
    burnRate = parseInt(burnRate.replace(/[^0-9]/g, "")) || 0;
  } else {
    burnRate = parseInt(burnRate) || 0;
  }

  document.getElementById("simKPIs").innerHTML = [
    { label: "Burn Rate/Month", val: "₹" + fmtNum(burnRate), icon: "bi-fire" },
    { label: "Cash Runway", val: (runway || "—") + " months", icon: "bi-calendar3" },
    { label: "Break-even Month", val: "Month " + (breakEven || "—"), icon: "bi-check-circle" },
    { label: "Month 12 Revenue", val: "₹" + fmtNum(rev[11] || 0), icon: "bi-graph-up-arrow" },
    { label: "Month 12 Customers", val: (cust[11] || 0).toLocaleString(), icon: "bi-people-fill" },
    { label: "Month 12 Profit", val: "₹" + fmtNum((rev[11]||0) - (exp[11]||0)), icon: "bi-cash-stack" },
  ].map(k => `<div class="col-6 col-md-4 col-lg-2"><div class="kpi-card"><i class="bi ${k.icon} text-accent d-block mb-1" style="font-size:1.4rem;"></i><div class="kpi-value">${k.val}</div><div class="kpi-label">${k.label}</div></div></div>`).join("");

  // Revenue vs Expense
  const ctx1 = document.getElementById("chartRevenueExpense")?.getContext("2d");
  if (ctx1) {
    new Chart(ctx1, {
      type: "line",
      data: {
        labels: months,
        datasets: [
          { label: "Revenue (₹)", data: rev, borderColor: COLORS.success, backgroundColor: "rgba(34,197,94,0.08)", fill: true, tension: 0.4, pointRadius: 3 },
          { label: "Expenses (₹)", data: exp, borderColor: COLORS.danger, backgroundColor: "rgba(239,68,68,0.08)", fill: true, tension: 0.4, pointRadius: 3 }
        ]
      },
      options: {
        responsive: true,
        plugins: { title: { display: true, text: "Monthly Revenue vs Expenses", font: { size: 13 } } },
        scales: {
          y: { ticks: { callback: v => "₹" + (v/1000).toFixed(0) + "K" } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // Customer growth
  const ctx2 = document.getElementById("chartCustomers")?.getContext("2d");
  if (ctx2) {
    new Chart(ctx2, {
      type: "line",
      data: {
        labels: months,
        datasets: [{ label: "Customers", data: cust, borderColor: COLORS.accent, backgroundColor: "rgba(59,130,212,0.08)", fill: true, tension: 0.4, pointRadius: 3 }]
      },
      options: {
        responsive: true,
        plugins: { title: { display: true, text: "Customer Growth Projection", font: { size: 13 } } },
        scales: { x: { grid: { display: false } } }
      }
    });
  }

  document.getElementById("simAssumptions").textContent = sim.assumptions || "Based on industry-standard SaaS growth metrics with Indian market context.";
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 14: RISKS
// ══════════════════════════════════════════════════════════════════════════
function renderRisks() {
  const risks = BP.risks || [];
  const RISK_ICONS = { Technical: "bi-gear", Financial: "bi-cash-stack", Market: "bi-graph-down", Legal: "bi-shield", Operational: "bi-people" };

  document.getElementById("riskCards").innerHTML = risks.map(r => `
    <div class="col-md-6">
      <div class="glass-card p-4 h-100 risk-level-${r.level?.toLowerCase() || 'medium'}">
        <div class="d-flex align-items-center gap-2 mb-2">
          <i class="bi ${RISK_ICONS[r.category] || 'bi-exclamation-triangle'} text-accent"></i>
          <span class="fw-bold">${r.category} Risk</span>
          <span class="ms-auto small fw-semibold" style="color:${r.level==='High'?COLORS.danger:r.level==='Medium'?COLORS.warning:COLORS.success};">${r.level}</span>
        </div>
        <p class="text-muted small mb-2">${r.risk}</p>
        <div class="score-bar-track mb-2"><div class="score-bar-fill" data-width="${r.probability||0}" style="background:${r.level==='High'?COLORS.danger:r.level==='Medium'?COLORS.warning:COLORS.success};width:0;"></div></div>
        <div class="text-muted" style="font-size:11px;">Probability: ${r.probability||0}%</div>
        <div class="mt-2 small"><i class="bi bi-shield-check text-success me-1"></i><strong>Mitigation:</strong> ${r.mitigation}</div>
      </div>
    </div>`).join("");

  requestAnimationFrame(() => document.querySelectorAll(".score-bar-fill").forEach(el => { el.style.width = (el.dataset.width || 0) + "%"; }));

  // Risk radar chart
  const ctx = document.getElementById("chartRisks")?.getContext("2d");
  if (ctx && risks.length) {
    new Chart(ctx, {
      type: "radar",
      data: {
        labels: risks.map(r => r.category),
        datasets: [{
          label: "Risk Probability %",
          data: risks.map(r => r.probability || 0),
          backgroundColor: "rgba(239,68,68,0.12)",
          borderColor: COLORS.danger,
          pointBackgroundColor: COLORS.danger,
        }]
      },
      options: {
        responsive: true,
        plugins: { title: { display: true, text: "Risk Probability Radar", font: { size: 13 } } },
        scales: { r: { min: 0, max: 100, ticks: { display: false }, grid: { color: "rgba(255,255,255,0.06)" } } }
      }
    });
  }
  setWhyPanel("why-risks", "Risk matrix generated based on your industry, stage, and market context.");
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 15: INVESTOR READINESS
// ══════════════════════════════════════════════════════════════════════════
function renderInvestorReadiness() {
  const ir = BP.investor_readiness || {};
  drawGaugeCanvas("gaugeInvestor", ir.score || 0);
  document.getElementById("investorScoreLabel").textContent = scoreLabel(ir.score || 0);

  document.getElementById("investorDetails").innerHTML = `
    <h6 class="fw-semibold mb-4">Investor Readiness Details</h6>
    ${[
      ["Funding Readiness", ir.funding_readiness || 0, "%"],
      ["Investor Pitch Score", ir.pitch_score || 0, "/100"],
    ].map(([label, val, unit]) => `
      <div class="score-bar-wrap">
        <div class="score-bar-label"><span>${label}</span><strong>${val}${unit}</strong></div>
        <div class="score-bar-track"><div class="score-bar-fill" data-width="${val}" style="background:${COLORS.accent};"></div></div>
      </div>`).join("")}
    <div class="row g-3 mt-2">
      <div class="col-6"><div class="kpi-card"><div class="kpi-label">Investment Risk Level</div><div class="kpi-value text-warning" style="font-size:1rem;">${ir.investment_risks || "—"}</div></div></div>
      <div class="col-6"><div class="kpi-card"><div class="kpi-label">Funding Timeline</div><div class="kpi-value text-accent" style="font-size:1rem;">${ir.funding_timeline || "—"}</div></div></div>
    </div>
    ${ir.gaps?.length ? `
    <div class="mt-3">
      <h6 class="text-warning fw-semibold mb-2"><i class="bi bi-exclamation-triangle me-2"></i>Gaps to Close</h6>
      ${ir.gaps.map(g => `<div class="d-flex gap-2 mb-1 small text-muted"><i class="bi bi-arrow-right-circle text-accent mt-1"></i><span>${g}</span></div>`).join("")}
    </div>` : ""}`;

  requestAnimationFrame(() => document.querySelectorAll(".score-bar-fill").forEach(el => { el.style.width = (el.dataset.width || 0) + "%"; }));
  setWhyPanel("why-investor", ir.why);
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 16: STARTUP IMPROVER
// ══════════════════════════════════════════════════════════════════════════
function renderImprovements() {
  const improvements = BP.improvements || [];
  const container = document.getElementById("improvementCards");
  container.innerHTML = improvements.map((imp, i) => `
    <div class="col-md-6" data-aos="fade-up" data-aos-delay="${i*60}">
      <div class="glass-card p-4 h-100 improvement-card">
        <div class="d-flex align-items-center gap-2 mb-3">
          <span class="badge" style="background:rgba(34,197,94,0.15);color:#4ade80;border:1px solid rgba(34,197,94,0.25);">${imp.impact} Impact</span>
          <span class="fw-semibold">${imp.area}</span>
        </div>
        <div class="mb-2 before">${imp.current}</div>
        <div class="after d-flex gap-2"><i class="bi bi-arrow-right-circle-fill text-success mt-1"></i><span>${imp.improved}</span></div>
      </div>
    </div>`).join("");
  AOS.refresh();
}

async function loadImprovements() {
  const btn = document.querySelector('[onclick="loadImprovements()"]');
  btn.disabled = true;
  btn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Improving...';
  try {
    const resp = await fetch("/api/improve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ blueprint: BP })
    });
    const data = await resp.json();
    if (data.success && data.improvements?.length) {
      BP.improvements = data.improvements;
      sessionStorage.setItem("blueprint", JSON.stringify(BP));
      renderImprovements();
      showToast("✅ Startup improvements updated!");
    }
  } catch(e) { showToast("❌ Could not load improvements."); }
  btn.disabled = false;
  btn.innerHTML = '<i class="bi bi-stars me-1"></i>✨ Improve My Startup';
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 17: STARTUP NAMES
// ══════════════════════════════════════════════════════════════════════════
function renderStartupNames() {
  const names = BP.startup_names || {};
  document.getElementById("nameCards").innerHTML = (names.names || []).map(n => `
    <div class="col-6 col-md-4 col-lg-3">
      <div class="name-card" onclick="copyText2('${n}')">
        <span class="fw-semibold">${n}</span>
        <i class="bi bi-clipboard text-muted" style="font-size:12px;"></i>
      </div>
    </div>`).join("");

  document.getElementById("taglineList").innerHTML = (names.taglines || []).map(t => `
    <div class="d-flex align-items-center justify-content-between mb-2 pb-2 border-bottom border-secondary">
      <span class="small italic">"${t}"</span>
      <button class="btn btn-ghost btn-sm" onclick="copyText2('${t}')"><i class="bi bi-clipboard" style="font-size:11px;"></i></button>
    </div>`).join("");

  document.getElementById("domainList").innerHTML = (names.domains || []).map(d => `
    <div class="d-flex align-items-center justify-content-between mb-2 pb-2 border-bottom border-secondary">
      <span class="small font-monospace text-accent">${d}</span>
      <button class="btn btn-ghost btn-sm" onclick="copyText2('${d}')"><i class="bi bi-clipboard" style="font-size:11px;"></i></button>
    </div>`).join("");
}

function copyText2(text) {
  navigator.clipboard.writeText(text).then(() => showToast(`"${text}" copied!`));
}

async function regenerateNames() {
  const es = BP.executive_summary || {};
  showToast("⏳ Generating new names...");
  try {
    const resp = await fetch("/api/names", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea: es.solution || "", industry: es.industry || "" })
    });
    const data = await resp.json();
    if (data.success && data.data) {
      BP.startup_names = data.data;
      sessionStorage.setItem("blueprint", JSON.stringify(BP));
      renderStartupNames();
      showToast("✅ New names generated!");
    }
  } catch(e) { showToast("❌ Name generation failed."); }
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 18: ELEVATOR PITCH
// ══════════════════════════════════════════════════════════════════════════
function renderElevatorPitch() {
  const ep = BP.elevator_pitch || {};
  document.getElementById("pitch30sec").textContent = ep["30_sec"] || "—";
  document.getElementById("pitch2min").textContent  = ep["2_min"]  || "—";
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 19: PITCH DECK
// ══════════════════════════════════════════════════════════════════════════
function renderPitchDeck() {
  const es = BP.executive_summary || {};
  const ma = BP.market_analysis  || {};
  const rm = BP.revenue_model    || {};
  const sim = BP.simulation      || {};
  const ir  = BP.investor_readiness || {};

  const slides = [
    { num: "01", title: "Cover", body: `${es.startup_names?.[0] || "Your Startup"} — ${es.tagline || ""}` },
    { num: "02", title: "The Problem", body: es.problem || "—" },
    { num: "03", title: "Our Solution", body: es.solution || "—" },
    { num: "04", title: "Market Size", body: `TAM: ${ma.tam || "—"} | SAM: ${ma.sam || "—"} | SOM: ${ma.som || "—"} | CAGR: ${ma.growth_rate || "—"}` },
    { num: "05", title: "Product", body: es.solution || "—" },
    { num: "06", title: "Business Model", body: `Recommended: ${rm.recommended || "—"}` },
    { num: "07", title: "Go-to-Market", body: `Target: ${es.target_customers || "—"}` },
    { num: "08", title: "Traction & Roadmap", body: (BP.roadmap || []).slice(0,2).map(r => r.phase + ": " + r.milestone).join(" → ") },
    { num: "09", title: "Financials", body: `Budget: ${es.estimated_budget || "—"} | Break-even: Month ${sim.break_even_month || "—"} | Runway: ${sim.cash_runway_months || "—"}mo` },
    { num: "10", title: "The Ask", body: `Seeking: ${es.estimated_budget || "—"} | ${ir.funding_timeline || "—"}` },
  ];

  document.getElementById("pitchDeckPreview").innerHTML = slides.map(s => `
    <div class="pitch-slide">
      <div class="pitch-slide-num">Slide ${s.num}</div>
      <div class="pitch-slide-title">${s.title}</div>
      <div class="pitch-slide-body">${s.body}</div>
    </div>`).join("");
}

// ══════════════════════════════════════════════════════════════════════════
// SECTION 21: RECOMMENDATIONS
// ══════════════════════════════════════════════════════════════════════════
function renderRecommendations() {
  const recs = BP.recommendations || [];
  const IMPACT_COLORS = { "Very High": "#22c55e", "High": "#3b82d4", "Medium": "#f59e0b" };
  document.getElementById("recCards").innerHTML = recs.map((r, i) => `
    <div class="col-md-6" data-aos="fade-up" data-aos-delay="${i*50}">
      <div class="glass-card p-4 h-100 rec-card" onclick="toggleRec(${i})">
        <div class="d-flex align-items-center gap-2 mb-2">
          <i class="bi bi-lightbulb-fill text-accent"></i>
          <span class="fw-semibold">${r.title}</span>
          <span class="ms-auto small fw-bold" style="color:${IMPACT_COLORS[r.impact] || '#3b82d4'};">${r.impact}</span>
        </div>
        <div class="d-flex gap-2 mb-2">
          <span class="chip">⚡ Effort: ${r.effort || "Medium"}</span>
        </div>
        <div class="rec-expand" id="rec-${i}">${r.detail}</div>
        <div class="text-muted small" style="font-size:11px;">👆 Click to expand</div>
      </div>
    </div>`).join("");
  AOS.refresh();
}

function toggleRec(i) { document.getElementById(`rec-${i}`)?.classList.toggle("show"); }

// ══════════════════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════════════════
function toggleWhy(panelId) {
  const el = document.getElementById(panelId);
  if (el) el.style.display = el.style.display === "none" ? "" : "none";
}

function setWhyPanel(panelId, text) {
  const el = document.getElementById(panelId);
  if (el && text) el.textContent = "💡 " + text;
}

function fmtNum(n) {
  if (!n && n !== 0) return "—";
  if (n >= 10000000) return (n / 10000000).toFixed(1) + " Cr";
  if (n >= 100000)   return (n / 100000).toFixed(1)   + "L";
  if (n >= 1000)     return (n / 1000).toFixed(1)     + "K";
  return n.toLocaleString();
}
