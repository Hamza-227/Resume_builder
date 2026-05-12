"use strict";

let uploadedFile = null;

// ─── DRAG & DROP ───────────────────────────────────────────────
const dz = document.getElementById("dropZone");
dz.addEventListener("dragover", e => { e.preventDefault(); dz.classList.add("dragover"); });
dz.addEventListener("dragleave", () => dz.classList.remove("dragover"));
dz.addEventListener("drop", e => {
  e.preventDefault(); dz.classList.remove("dragover");
  const f = e.dataTransfer.files[0];
  if (f) setFile(f);
});

function handleFile(f) { if (f) setFile(f); }

function setFile(f) {
  if (!f.name.endsWith(".pdf")) { showCheckErr("Please upload a PDF file."); return; }
  if (f.size > 5 * 1024 * 1024) { showCheckErr("File too large. Max 5MB."); return; }
  uploadedFile = f;
  document.getElementById("fileName").textContent = f.name;
  document.getElementById("fileSelected").classList.remove("hidden");
  document.getElementById("checkErr").classList.add("hidden");
  document.getElementById("checkBtn").disabled = false;
}

// ─── SUBMIT TO BACKEND ─────────────────────────────────────────
async function checkResume() {
  if (!uploadedFile) { showCheckErr("Please select a PDF file first."); return; }

  const btn = document.getElementById("checkBtn");
  const txt = document.getElementById("checkText");
  btn.disabled = true;
  btn.classList.add("loading");
  txt.innerHTML = '<span class="spinner"></span> Analyzing your resume...';

  try {
    const fd = new FormData();
    fd.append("file", uploadedFile);

    const res = await fetch("/check-ats", { method: "POST", body: fd });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      throw new Error(j.error || `Server error (${res.status})`);
    }
    const data = await res.json();
    renderResults(data);
  } catch (e) {
    showCheckErr(e.message || "Analysis failed. Please try again.");
  } finally {
    btn.disabled = false;
    btn.classList.remove("loading");
    txt.innerHTML = '📊 Check ATS Score';
  }
}

// ─── RENDER RESULTS ────────────────────────────────────────────
function renderResults(d) {
  const card = document.getElementById("results-card");
  card.classList.remove("hidden");
  card.scrollIntoView({ behavior: "smooth", block: "start" });

  // Animate score number
  animateNumber("scoreNum", 0, d.total_score, 1400);

  // Ring color + animation
  const ring = document.getElementById("ringFill");
  const circumference = 326.7;
  const offset = circumference - (d.total_score / 100) * circumference;
  ring.style.stroke = d.total_score >= 75 ? "#16a34a" : d.total_score >= 50 ? "#d97706" : "#dc2626";
  setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);

  // Verdict
  const vEl = document.getElementById("scoreVerdict");
  if (d.total_score >= 75) {
    vEl.textContent = "✓ Good ATS Compatibility";
    vEl.className = "score-verdict verdict-great";
  } else if (d.total_score >= 50) {
    vEl.textContent = "⚠ Needs Improvement";
    vEl.className = "score-verdict verdict-ok";
  } else {
    vEl.textContent = "✗ Likely to Be Rejected by ATS";
    vEl.className = "score-verdict verdict-poor";
  }

  // Score breakdown summary
  document.getElementById("scoreBreakdown").innerHTML = `
    <span style="font-size:13px;color:var(--ink-3)">
      Text: <b>${d.categories.text_extraction.score}/${d.categories.text_extraction.max}</b> &nbsp;·&nbsp;
      Sections: <b>${d.categories.sections.score}/${d.categories.sections.max}</b> &nbsp;·&nbsp;
      Format: <b>${d.categories.format.score}/${d.categories.format.max}</b> &nbsp;·&nbsp;
      Keywords: <b>${d.categories.keywords.score}/${d.categories.keywords.max}</b>
    </span>`;

  // Category bars
  const bars = document.getElementById("catBars");
  bars.innerHTML = "";
  const cats = [
    { label: "Text Extraction",   key: "text_extraction" },
    { label: "Section Headers",   key: "sections" },
    { label: "Length & Format",   key: "format" },
    { label: "Metrics & Keywords",key: "keywords" },
    { label: "Contact & Links",   key: "contact" },
    { label: "Red Flag Check",    key: "red_flags" },
  ];
  cats.forEach(c => {
    const cat = d.categories[c.key];
    const pct = Math.round((cat.score / cat.max) * 100);
    const color = pct >= 75 ? "#16a34a" : pct >= 50 ? "#d97706" : "#dc2626";
    const div = document.createElement("div");
    div.className = "cat-bar-item";
    div.innerHTML = `
      <span class="cat-label">${c.label}</span>
      <div class="cat-track"><div class="cat-fill" style="width:0%;background:${color}" data-w="${pct}%"></div></div>
      <span class="cat-score-label">${cat.score}/${cat.max}</span>`;
    bars.appendChild(div);
  });
  // Animate bars after render
  setTimeout(() => {
    bars.querySelectorAll(".cat-fill").forEach(el => el.style.width = el.dataset.w);
  }, 200);

  // Recommendations
  const recsList = document.getElementById("recsList");
  recsList.innerHTML = "";
  d.recommendations.forEach((rec, i) => {
    const priorityClass = rec.priority === "high" ? "priority-high" : rec.priority === "medium" ? "priority-med" : "priority-low";
    const badgeClass    = rec.priority === "high" ? "badge-high"    : rec.priority === "medium" ? "badge-med"    : "badge-low";
    const div = document.createElement("div");
    div.className = `rec-item ${priorityClass}`;
    div.innerHTML = `
      <div class="rec-num">${i + 1}</div>
      <div class="rec-body">
        <strong>${rec.title} <span class="rec-badge ${badgeClass}">${rec.priority.toUpperCase()}</span></strong>
        <p>${rec.description}</p>
      </div>`;
    recsList.appendChild(div);
  });
}

function animateNumber(id, from, to, duration) {
  const el = document.getElementById(id);
  const start = performance.now();
  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(from + (to - from) * ease);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function showCheckErr(msg) {
  const b = document.getElementById("checkErr");
  b.textContent = "⚠️ " + msg;
  b.classList.remove("hidden");
}
