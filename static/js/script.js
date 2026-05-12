"use strict";
let expC=0, eduC=0, projC=0, certC=0;

document.addEventListener("DOMContentLoaded", () => {
  addExp(); addEdu(); addProj();
  const sum = document.getElementById("f-summary");
  const cnt = document.getElementById("summaryCount");
  sum.addEventListener("input", () => { cnt.textContent = sum.value.length + " chars"; prog(); });
  document.addEventListener("input", prog);
  prog();
});

function clone(id) { return document.getElementById(id).content.cloneNode(true); }

function addExp()  { expC++;  const f=clone("tpl-exp");  f.querySelector(".rn").textContent=expC;  document.getElementById("exp-list").appendChild(f);  prog(); }
function addEdu()  { eduC++;  const f=clone("tpl-edu");  f.querySelector(".rn").textContent=eduC;  document.getElementById("edu-list").appendChild(f);  prog(); }
function addProj() { projC++; const f=clone("tpl-proj"); f.querySelector(".rn").textContent=projC; document.getElementById("proj-list").appendChild(f); prog(); }
function addCert() { certC++; const f=clone("tpl-cert"); f.querySelector(".rn").textContent=certC; document.getElementById("cert-list").appendChild(f); prog(); }

function delBlock(btn) {
  const b = btn.closest(".rep-block");
  const list = b.parentElement;
  if (list.id === "exp-list" && list.querySelectorAll(".rep-block").length <= 1) { showErr("At least one experience is required."); return; }
  b.remove();
  list.querySelectorAll(".rn").forEach((el,i) => el.textContent = i+1);
  prog();
}

function addBullet(btn) {
  const wrap = btn.previousElementSibling;
  const row = document.createElement("div");
  row.className = "brow";
  row.innerHTML = `<span class="bdot">•</span><input class="binp" type="text" placeholder="Add achievement with a metric..." /><button class="bx" onclick="delBullet(this)">✕</button>`;
  wrap.appendChild(row);
}
function delBullet(btn) {
  const wrap = btn.closest(".bwrap");
  if (wrap.querySelectorAll(".brow").length > 1) btn.closest(".brow").remove();
}

function prog() {
  const fields = ["f-name","f-email","f-phone","f-summary","f-langs","f-tech"].map(id => document.getElementById(id));
  let filled = fields.filter(f => f && f.value.trim()).length;
  const exps = document.querySelectorAll("#exp-list .rep-block");
  if (exps.length) {
    if (exps[0].querySelector("[name='title']")?.value.trim()) filled++;
    if (exps[0].querySelector("[name='company']")?.value.trim()) filled++;
  }
  const pct = Math.round((filled / 8) * 100);
  document.getElementById("progBar").style.width = pct + "%";
  document.getElementById("progLabel").textContent = pct < 10 ? "Start filling to track progress" : pct + "% complete";
}

function val(id) { return document.getElementById(id)?.value.trim() || ""; }
function bval(b, n) { return b.querySelector(`[name="${n}"]`)?.value.trim() || ""; }
function csv(id) { return (document.getElementById(id)?.value || "").split(",").map(s=>s.trim()).filter(Boolean); }

function build() {
  const contact = {
    name:      val("f-name"),
    email:     val("f-email"),
    phone:     val("f-phone"),
    city:      val("f-city"),
    linkedin:  val("f-linkedin")  || null,
    github:    val("f-github")    || null,
    portfolio: val("f-portfolio") || null,
    website:   val("f-website")   || null,
  };
  const experience = [];
  document.querySelectorAll("#exp-list .rep-block").forEach(b => {
    const bullets = [...b.querySelectorAll(".binp")].map(i=>i.value.trim()).filter(Boolean);
    if (!bullets.length) bullets.push("Contributed to team projects and objectives.");
    experience.push({ title: bval(b,"title"), company: bval(b,"company"), location: bval(b,"location"), start_date: bval(b,"start_date"), end_date: bval(b,"end_date") || "Present", bullets });
  });
  const education = [];
  document.querySelectorAll("#edu-list .rep-block").forEach(b => {
    const inst = bval(b,"institution"), deg = bval(b,"degree");
    if (inst || deg) education.push({ institution: inst, degree: deg, start_date: bval(b,"start_date"), end_date: bval(b,"end_date") });
  });
  const projects = [];
  document.querySelectorAll("#proj-list .rep-block").forEach(b => {
    const name = bval(b,"name"), desc = bval(b,"description");
    if (name || desc) projects.push({ name, description: desc, link: bval(b,"link") || null });
  });
  const certifications = [];
  document.querySelectorAll("#cert-list .rep-block").forEach(b => {
    const name = bval(b,"name");
    if (name) certifications.push({ name, link: bval(b,"link") || null });
  });
  return {
    contact,
    summary: val("f-summary"),
    experience, education, projects,
    skills: { languages_tools: csv("f-langs"), techniques: csv("f-tech"), soft_skills: csv("f-soft") },
    certifications,
  };
}

function validate(d) {
  if (!d.contact.name)       return "Please enter your full name.";
  if (!d.contact.email)      return "Please enter your email address.";
  if (!d.contact.email.includes("@")) return "Please enter a valid email.";
  if (!d.summary)            return "Please add a professional summary.";
  if (!d.experience.length)  return "Please add at least one experience entry.";
  if (!d.experience[0].title)   return "Please enter a job title for Experience #1.";
  if (!d.experience[0].company) return "Please enter a company for Experience #1.";
  return null;
}

async function generatePDF() {
  const btn = document.getElementById("genBtn");
  const txt = document.getElementById("genText");
  const err = document.getElementById("errBox");
  err.classList.add("hidden");

  const data = build();
  const e = validate(data);
  if (e) { showErr(e); return; }

  btn.disabled = true;
  btn.classList.add("loading");
  txt.innerHTML = '<span class="spinner"></span> Generating PDF...';

  try {
    const res = await fetch("/generate", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(data) });
    if (!res.ok) { const j = await res.json().catch(()=>{}); throw new Error(j?.error || `Error ${res.status}`); }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${data.contact.name.replace(/\s+/g,"_")}_ATS_Resume.pdf`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);

    btn.classList.remove("loading"); btn.classList.add("success");
    txt.textContent = "✓ PDF Downloaded! Generate Again";
    document.getElementById("postDlAd")?.classList.remove("hidden");

    setTimeout(() => {
      btn.disabled = false; btn.classList.remove("success");
      txt.innerHTML = '⚡ Generate ATS Resume PDF';
    }, 4000);
  } catch(e) {
    btn.disabled = false; btn.classList.remove("loading");
    txt.innerHTML = '⚡ Generate ATS Resume PDF';
    showErr(e.message || "Something went wrong. Please try again.");
  }
}

function showErr(msg) {
  const b = document.getElementById("errBox");
  b.textContent = "⚠️ " + msg;
  b.classList.remove("hidden");
  b.scrollIntoView({ behavior:"smooth", block:"center" });
}
