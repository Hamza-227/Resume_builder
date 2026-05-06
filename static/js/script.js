/* ═══════════════════════════════════════════════════════════════════════════
   script.js — Free ATS Resume Builder
   Handles: dynamic form, validation, progress tracking, PDF download
════════════════════════════════════════════════════════════════════════════ */

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
// COUNTERS (track how many of each block exist)
// ─────────────────────────────────────────────────────────────────────────────
let expCount  = 0;
let eduCount  = 0;
let projCount = 0;
let certCount = 0;


// ─────────────────────────────────────────────────────────────────────────────
// INIT — add one of each block on page load
// ─────────────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  addExperience();
  addEducation();
  addProject();

  // Summary character counter
  const summary = document.getElementById("summary");
  const count = document.getElementById("summaryCount");
  summary.addEventListener("input", () => {
    count.textContent = `${summary.value.length} chars`;
    updateProgress();
  });

  // Track progress on any input change
  document.addEventListener("input", updateProgress);
  updateProgress();
});


// ─────────────────────────────────────────────────────────────────────────────
// CLONE TEMPLATE HELPER
// ─────────────────────────────────────────────────────────────────────────────
function cloneTemplate(id) {
  const tmpl = document.getElementById(id);
  return tmpl.content.cloneNode(true);
}


// ─────────────────────────────────────────────────────────────────────────────
// ADD BLOCKS
// ─────────────────────────────────────────────────────────────────────────────
function addExperience() {
  expCount++;
  const frag = cloneTemplate("exp-template");
  frag.querySelector(".num-label").textContent = expCount;
  document.getElementById("experience-list").appendChild(frag);
  updateProgress();
}

function addEducation() {
  eduCount++;
  const frag = cloneTemplate("edu-template");
  frag.querySelector(".num-label").textContent = eduCount;
  document.getElementById("education-list").appendChild(frag);
  updateProgress();
}

function addProject() {
  projCount++;
  const frag = cloneTemplate("proj-template");
  frag.querySelector(".num-label").textContent = projCount;
  document.getElementById("projects-list").appendChild(frag);
  updateProgress();
}

function addCert() {
  certCount++;
  const frag = cloneTemplate("cert-template");
  frag.querySelector(".num-label").textContent = certCount;
  document.getElementById("certs-list").appendChild(frag);
  updateProgress();
}


// ─────────────────────────────────────────────────────────────────────────────
// REMOVE BLOCK
// ─────────────────────────────────────────────────────────────────────────────
function removeBlock(btn) {
  const block = btn.closest(".repeatable-block");
  const list  = block.parentElement;

  // Prevent removing last experience
  if (block.dataset.type === "exp" &&
      list.querySelectorAll(".repeatable-block").length <= 1) {
    showError("At least one experience entry is required.");
    return;
  }
  block.remove();
  renumberBlocks(list);
  updateProgress();
}

function renumberBlocks(list) {
  list.querySelectorAll(".num-label").forEach((el, i) => {
    el.textContent = i + 1;
  });
}


// ─────────────────────────────────────────────────────────────────────────────
// BULLETS
// ─────────────────────────────────────────────────────────────────────────────
function addBullet(btn) {
  const wrap = btn.previousElementSibling; // .bullets-wrap
  const row  = document.createElement("div");
  row.className = "bullet-row";
  row.innerHTML = `
    <span class="bullet-icon">•</span>
    <input type="text" class="bullet-input" placeholder="Add achievement with a metric..." />
    <button class="btn-bullet-remove" onclick="removeBullet(this)">✕</button>
  `;
  wrap.appendChild(row);
}

function removeBullet(btn) {
  const wrap = btn.closest(".bullets-wrap");
  const rows = wrap.querySelectorAll(".bullet-row");
  if (rows.length > 1) {
    btn.closest(".bullet-row").remove();
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// PROGRESS TRACKER
// ─────────────────────────────────────────────────────────────────────────────
function updateProgress() {
  const fields = [
    document.getElementById("name"),
    document.getElementById("email"),
    document.getElementById("phone"),
    document.getElementById("summary"),
  ];

  let filled = 0;
  const total = 8; // rough sections

  fields.forEach(f => { if (f && f.value.trim()) filled++; });

  // Check experience
  const expBlocks = document.querySelectorAll("#experience-list .repeatable-block");
  if (expBlocks.length > 0) {
    const first = expBlocks[0];
    if (first.querySelector("[name='title']")?.value.trim()) filled++;
    if (first.querySelector("[name='company']")?.value.trim()) filled++;
  }

  // Check skills
  if (document.getElementById("lang-tools")?.value.trim()) filled++;
  if (document.getElementById("techniques")?.value.trim()) filled++;

  const pct = Math.round((filled / total) * 100);
  document.getElementById("progressBar").style.width = pct + "%";
  document.getElementById("progressLabel").textContent = `${pct}% complete`;
}


// ─────────────────────────────────────────────────────────────────────────────
// BUILD RESUME JSON FROM FORM
// ─────────────────────────────────────────────────────────────────────────────
function buildResumeData() {
  // Contact
  const contact = {
    name:      val("name"),
    email:     val("email"),
    phone:     val("phone"),
    city:      val("city"),
    linkedin:  val("linkedin")  || null,
    github:    val("github")    || null,
    website:   null,
    portfolio: null,
  };

  // Summary
  const summary = val("summary");

  // Experience
  const experience = [];
  document.querySelectorAll("#experience-list .repeatable-block").forEach(block => {
    const bullets = [];
    block.querySelectorAll(".bullet-input").forEach(inp => {
      if (inp.value.trim()) bullets.push(inp.value.trim());
    });
    if (!bullets.length) bullets.push("Contributed to team projects and initiatives.");

    experience.push({
      title:      blockVal(block, "title"),
      company:    blockVal(block, "company"),
      location:   blockVal(block, "location"),
      start_date: blockVal(block, "start_date"),
      end_date:   blockVal(block, "end_date") || "Present",
      bullets,
    });
  });

  // Education
  const education = [];
  document.querySelectorAll("#education-list .repeatable-block").forEach(block => {
    const inst = blockVal(block, "institution");
    const deg  = blockVal(block, "degree");
    if (inst || deg) {
      education.push({
        institution: inst,
        degree:      deg,
        start_date:  blockVal(block, "start_date"),
        end_date:    blockVal(block, "end_date"),
      });
    }
  });

  // Projects
  const projects = [];
  document.querySelectorAll("#projects-list .repeatable-block").forEach(block => {
    const name = blockVal(block, "name");
    const desc = blockVal(block, "description");
    if (name || desc) {
      projects.push({
        name,
        description: desc,
        link: blockVal(block, "link") || null,
      });
    }
  });

  // Skills
  const skills = {
    languages_tools: splitCSV("lang-tools"),
    techniques:      splitCSV("techniques"),
    soft_skills:     splitCSV("soft-skills"),
  };

  // Certifications
  const certifications = [];
  document.querySelectorAll("#certs-list .repeatable-block").forEach(block => {
    const name = blockVal(block, "name");
    if (name) {
      certifications.push({
        name,
        link: blockVal(block, "link") || null,
      });
    }
  });

  return { contact, summary, experience, education, projects, skills, certifications };
}

function val(id) {
  return document.getElementById(id)?.value.trim() || "";
}

function blockVal(block, name) {
  return block.querySelector(`[name="${name}"]`)?.value.trim() || "";
}

function splitCSV(id) {
  const raw = document.getElementById(id)?.value || "";
  return raw.split(",").map(s => s.trim()).filter(Boolean);
}


// ─────────────────────────────────────────────────────────────────────────────
// VALIDATION
// ─────────────────────────────────────────────────────────────────────────────
function validate(data) {
  if (!data.contact.name)  return "Please enter your full name.";
  if (!data.contact.email) return "Please enter your email address.";
  if (!data.contact.email.includes("@")) return "Please enter a valid email address.";
  if (!data.summary)       return "Please add a professional summary.";
  if (!data.experience.length) return "Please add at least one experience entry.";
  if (!data.experience[0].title)   return "Please enter a job title for Experience #1.";
  if (!data.experience[0].company) return "Please enter a company name for Experience #1.";
  return null; // no error
}


// ─────────────────────────────────────────────────────────────────────────────
// GENERATE PDF
// ─────────────────────────────────────────────────────────────────────────────
async function generatePDF() {
  const btn     = document.getElementById("generateBtn");
  const btnText = document.getElementById("btnText");
  const errBox  = document.getElementById("errorBox");

  // Clear previous error
  errBox.classList.add("hidden");
  errBox.textContent = "";

  // Build and validate data
  const data  = buildResumeData();
  const error = validate(data);
  if (error) {
    showError(error);
    return;
  }

  // UI: loading state
  btn.disabled = true;
  btn.classList.add("loading");
  btnText.innerHTML = '<span class="spinner"></span> Generating your PDF...';

  try {
    const response = await fetch("/generate", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(data),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || `Server error (${response.status})`);
    }

    // Download the PDF
    const blob     = await response.blob();
    const url      = URL.createObjectURL(blob);
    const name     = data.contact.name.replace(/\s+/g, "_");
    const link     = document.createElement("a");
    link.href      = url;
    link.download  = `${name}_ATS_Resume.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

    // UI: success state
    btn.classList.remove("loading");
    btn.classList.add("success");
    btnText.textContent = "✓ PDF Downloaded! Generate Again";

    // Show post-download ad (highest CTR moment)
    document.getElementById("postDownloadAd").classList.remove("hidden");

    // Reset button after 4s
    setTimeout(() => {
      btn.disabled = false;
      btn.classList.remove("success");
      btnText.innerHTML = '<span class="btn-icon">⚡</span> Generate My ATS Resume PDF';
    }, 4000);

  } catch (err) {
    btn.disabled = false;
    btn.classList.remove("loading");
    btnText.innerHTML = '<span class="btn-icon">⚡</span> Generate My ATS Resume PDF';
    showError(err.message || "Something went wrong. Please try again.");
  }
}


// ─────────────────────────────────────────────────────────────────────────────
// SHOW ERROR
// ─────────────────────────────────────────────────────────────────────────────
function showError(msg) {
  const box = document.getElementById("errorBox");
  box.textContent = "⚠️ " + msg;
  box.classList.remove("hidden");
  box.scrollIntoView({ behavior: "smooth", block: "center" });
}
