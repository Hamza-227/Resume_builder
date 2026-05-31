"use strict";
let uploadedFile=null;
const dz=document.getElementById("dropZone");
if(dz){
  dz.addEventListener("dragover",e=>{e.preventDefault();dz.classList.add("dragover")});
  dz.addEventListener("dragleave",()=>dz.classList.remove("dragover"));
  dz.addEventListener("drop",e=>{e.preventDefault();dz.classList.remove("dragover");const f=e.dataTransfer.files[0];if(f)setFile(f);});
}
function handleFile(f){if(f)setFile(f);}
window.handleFile=handleFile;
function setFile(f){
  if(!f.name.toLowerCase().endsWith(".pdf")){showCheckErr("Please upload a PDF file.");return;}
  if(f.size>5*1024*1024){showCheckErr("File too large. Max 5MB.");return;}
  uploadedFile=f;
  document.getElementById("fileName").textContent=f.name;
  document.getElementById("fileSelected").classList.remove("hidden");
  document.getElementById("checkErr").classList.add("hidden");
  document.getElementById("checkBtn").disabled=false;
}
async function checkResume(){
  if(!uploadedFile){showCheckErr("Please select a PDF file first.");return;}
  const btn=document.getElementById("checkBtn"),txt=document.getElementById("checkText");
  btn.disabled=true;btn.classList.add("loading");
  txt.innerHTML='<span class="spinner"></span> Analyzing…';
  try{
    const fd=new FormData();fd.append("file",uploadedFile);
    const res=await fetch("/check-ats",{method:"POST",body:fd});
    if(!res.ok){const j=await res.json().catch(()=>({}));throw new Error(j.error||`Error ${res.status}`);}
    renderResults(await res.json());
  }catch(e){showCheckErr(e.message||"Analysis failed. Please try again.");}
  finally{btn.disabled=false;btn.classList.remove("loading");txt.innerHTML='📊 Check ATS Score';}
}
window.checkResume=checkResume;

function renderResults(d){
  const card=document.getElementById("results-card");
  card.classList.remove("hidden");
  card.scrollIntoView({behavior:"smooth",block:"start"});
  // Animate number
  const numEl=document.getElementById("scoreNum");
  const start=performance.now();
  const anim=now=>{const p=Math.min((now-start)/1400,1),ease=1-Math.pow(1-p,3);numEl.textContent=Math.round(d.total_score*ease);if(p<1)requestAnimationFrame(anim);};
  requestAnimationFrame(anim);
  // Ring
  const ring=document.getElementById("srFill2");
  const col=d.total_score>=75?"#4ade80":d.total_score>=50?"#fbbf24":"#f87171";
  ring.style.stroke=col;ring.style.filter=`drop-shadow(0 0 6px ${col}88)`;
  setTimeout(()=>{ring.style.strokeDashoffset=326.7-(d.total_score/100)*326.7;},100);
  // Verdict
  const vEl=document.getElementById("scoreVerdict");
  if(d.total_score>=75){vEl.textContent="✓ Good ATS Compatibility";vEl.className="verdict v-great";}
  else if(d.total_score>=50){vEl.textContent="⚠ Needs Improvement";vEl.className="verdict v-ok";}
  else{vEl.textContent="✗ Likely ATS Rejected";vEl.className="verdict v-poor";}
  const cats=d.categories;
  document.getElementById("bline").innerHTML=`Text: <b>${cats.text_extraction.score}/20</b> &middot; Sections: <b>${cats.sections.score}/20</b> &middot; Format: <b>${cats.format.score}/20</b> &middot; Keywords: <b>${cats.keywords.score}/20</b>`;
  // Bars
  const barsEl=document.getElementById("catBars");barsEl.innerHTML="";
  [["Text Extraction","text_extraction"],["Section Headers","sections"],["Length & Format","format"],["Metrics & Keywords","keywords"],["Contact & Links","contact"],["Red Flag Check","red_flags"]].forEach(([label,key])=>{
    const cat=d.categories[key],pct=Math.round((cat.score/cat.max)*100);
    const col=pct>=75?"#4ade80":pct>=50?"#fbbf24":"#f87171";
    const div=document.createElement("div");div.className="cbar";
    div.innerHTML=`<span class="cbar-label">${label}</span><div class="cbar-track"><div class="cbar-fill" style="width:0%;background:${col}" data-w="${pct}%"></div></div><span class="cbar-val">${cat.score}/${cat.max}</span>`;
    barsEl.appendChild(div);
  });
  setTimeout(()=>{barsEl.querySelectorAll(".cbar-fill").forEach(el=>el.style.width=el.dataset.w);},200);
  // Recs
  const rl=document.getElementById("recsList");rl.innerHTML="";
  d.recommendations.forEach((rec,i)=>{
    const pc=rec.priority==="high"?"ph":rec.priority==="medium"?"pm":"pl";
    const bc=rec.priority==="high"?"bh":rec.priority==="medium"?"bm":"bl";
    const div=document.createElement("div");div.className=`rec-item ${pc}`;
    div.innerHTML=`<div class="rec-n">${i+1}</div><div class="rec-body"><strong>${rec.title}<span class="rec-badge ${bc}">${rec.priority.toUpperCase()}</span></strong><p>${rec.description}</p></div>`;
    rl.appendChild(div);
  });
}
function showCheckErr(msg){const b=document.getElementById("checkErr");b.textContent="⚠ "+msg;b.classList.remove("hidden");}
