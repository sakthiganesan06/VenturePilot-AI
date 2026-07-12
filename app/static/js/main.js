/* ═══════════════════════════════════════════════════════════════════════
   VenturPilot AI — Main JavaScript (shared across all pages)
   ═══════════════════════════════════════════════════════════════════════ */

// ── Navbar scroll effect ─────────────────────────────────────────────────
window.addEventListener("scroll", () => {
  document.getElementById("mainNav")?.classList.toggle("scrolled", window.scrollY > 40);
});

// ── Show Chat Floating Button when blueprint exists ──────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const bp = sessionStorage.getItem("blueprint");
  if (bp) {
    const el = document.getElementById("chatFloating");
    if (el) el.style.display = "flex";
    
    // Show hint bubble if it was not closed before
    const hintClosed = sessionStorage.getItem("chat_hint_closed");
    const bubble = document.getElementById("chatHintBubble");
    if (hintClosed === "true" && bubble) {
      bubble.style.display = "none";
    }
  }
});

// ── Chat ─────────────────────────────────────────────────────────────────
let chatHistory = [];
let chatOpen = false;

function toggleChat() {
  const win = document.getElementById("chatWindow");
  const bubble = document.getElementById("chatHintBubble");
  chatOpen = !chatOpen;
  win.style.display = chatOpen ? "flex" : "none";
  if (chatOpen) {
    document.getElementById("chatBadge").style.display = "none";
    if (bubble) {
      bubble.style.display = "none";
      sessionStorage.setItem("chat_hint_closed", "true");
    }
    if (chatHistory.length === 0) addBotMessage("👋 Hi! I'm your AI Startup Mentor powered by IBM Granite. I know your startup blueprint. Ask me anything about strategy, funding, competitors, or roadmap!");
    document.getElementById("chatInput")?.focus();
  }
}

function closeChatHint(e) {
  if (e) {
    e.stopPropagation(); // Avoid triggering toggleChat
  }
  const bubble = document.getElementById("chatHintBubble");
  if (bubble) {
    bubble.style.display = "none";
    sessionStorage.setItem("chat_hint_closed", "true");
  }
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && document.activeElement === document.getElementById("chatInput")) {
    sendChatMessage();
  }
});

async function sendChatMessage() {
  const input = document.getElementById("chatInput");
  const msg = input?.value?.trim();
  if (!msg) return;
  input.value = "";

  addUserMessage(msg);
  const typingEl = addTypingIndicator();

  const blueprint = JSON.parse(sessionStorage.getItem("blueprint") || "{}");

  try {
    const resp = await fetch("/api/chat/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, blueprint, history: chatHistory })
    });
    const data = await resp.json();
    typingEl.remove();
    if (data.success) {
      addBotMessage(data.response);
      chatHistory = data.history || chatHistory;
    } else {
      addBotMessage("⚠️ Sorry, I couldn't process that. Please try again.");
    }
  } catch (e) {
    typingEl.remove();
    addBotMessage("⚠️ Network error. Please check your connection.");
  }
}

function addUserMessage(text) {
  const msgs = document.getElementById("chatMessages");
  const el = document.createElement("div");
  el.className = "chat-msg chat-msg-user";
  el.textContent = text;
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
}

function addBotMessage(text) {
  const msgs = document.getElementById("chatMessages");
  const el = document.createElement("div");
  el.className = "chat-msg chat-msg-bot";
  el.innerHTML = text.replace(/\n/g, "<br/>");
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
}

function addTypingIndicator() {
  const msgs = document.getElementById("chatMessages");
  const el = document.createElement("div");
  el.className = "chat-msg chat-typing";
  el.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
  return el;
}

// ── Copy to clipboard ─────────────────────────────────────────────────────
function copyText(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  navigator.clipboard.writeText(el.textContent).then(() => showToast("✅ Copied to clipboard!"));
}

// ── Toast notification ────────────────────────────────────────────────────
function showToast(msg, type = "success") {
  const toast = document.createElement("div");
  toast.style.cssText = `
    position:fixed; bottom:1.5rem; left:50%; transform:translateX(-50%);
    background:#1a1f35; border:1px solid rgba(59,130,212,0.3);
    color:#e2e8f0; padding:0.6rem 1.5rem; border-radius:30px;
    font-size:13px; font-weight:600; z-index:9999;
    animation:fadeInUp 0.25s ease;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  `;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2800);
}

// ── Export helpers (shared) ────────────────────────────────────────────────
async function exportPDF() {
  const bp = JSON.parse(sessionStorage.getItem("blueprint") || "null");
  if (!bp) { showToast("⚠️ No blueprint found. Generate one first."); return; }
  showToast("⏳ Generating PDF...");
  try {
    const resp = await fetch("/api/export/blueprint-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ blueprint: bp })
    });
    if (!resp.ok) throw new Error("PDF generation failed");
    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url; a.download = "startup_blueprint.pdf"; a.click();
    showToast("✅ Blueprint PDF downloaded!");
  } catch(e) {
    showToast("❌ PDF export failed: " + e.message);
  }
}

async function exportPitchPDF() {
  const bp = JSON.parse(sessionStorage.getItem("blueprint") || "null");
  if (!bp) { showToast("⚠️ No blueprint found."); return; }
  showToast("⏳ Generating Pitch Deck PDF...");
  try {
    const resp = await fetch("/api/export/pitch-deck-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ blueprint: bp })
    });
    if (!resp.ok) throw new Error("Pitch deck generation failed");
    const blob = await resp.blob();
    const a    = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "pitch_deck.pdf"; a.click();
    showToast("✅ Pitch Deck PDF downloaded!");
  } catch(e) { showToast("❌ Export failed: " + e.message); }
}

async function exportJSON() {
  const bp = JSON.parse(sessionStorage.getItem("blueprint") || "null");
  if (!bp) { showToast("⚠️ No blueprint found."); return; }
  try {
    const resp = await fetch("/api/export/json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ blueprint: bp })
    });
    const blob = await resp.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "startup_blueprint.json"; a.click();
    showToast("✅ JSON exported!");
  } catch(e) { showToast("❌ JSON export failed."); }
}

// ── Smooth section scrolling ──────────────────────────────────────────────
function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  document.querySelectorAll(".dash-nav-btn").forEach(b => b.classList.remove("active"));
  document.querySelector(`[onclick="scrollToSection('${id}')"]`)?.classList.add("active");
}

// Intersection Observer for nav active state
const sectionObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = entry.target.id;
      document.querySelectorAll(".dash-nav-btn").forEach(b => b.classList.remove("active"));
      document.querySelector(`[onclick="scrollToSection('${id}')"]`)?.classList.add("active");
    }
  });
}, { threshold: 0.3, rootMargin: "-130px 0px 0px 0px" });

document.querySelectorAll(".section-anchor").forEach(el => sectionObserver.observe(el));
