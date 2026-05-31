"use strict";
let expC=0,eduC=0,projC=0,certC=0;

document.addEventListener("DOMContentLoaded",()=>{
  addExp();addEdu();addProj();
  const sum=document.getElementById("f-summary"),cnt=document.getElementById("sumCount");
  if(sum&&cnt){sum.addEventListener("input",()=>{cnt.textContent=sum.value.length+" chars";prog()});}
  document.addEventListener("input",prog);
  prog();
});

const clone=id=>document.getElementById(id).content.cloneNode(true);
function addExp(){expC++;const f=clone("tpl-exp");f.querySelector(".rn").textContent=expC;document.getElementById("exp-list").appendChild(f);prog();}
function addEdu(){eduC++;const f=clone("tpl-edu");f.querySelector(".rn").textContent=eduC;document.getElementById("edu-list").appendChild(f);prog();}
function addProj(){projC++;const f=clone("tpl-proj");f.querySelector(".rn").textContent=projC;document.getElementById("proj-list").appendChild(f);prog();}
function addCert(){certC++;const f=clone("tpl-cert");f.querySelector(".rn").textContent=certC;document.getElementById("cert-list").appendChild(f);prog();}
window.addExp=addExp;window.addEdu=addEdu;window.addProj=addProj;window.addCert=addCert;

function delBlock(btn){
  const b=btn.closest(".rep-block"),list=b.parentElement;
  if(list.id==="exp-list"&&list.querySelectorAll(".rep-block").length<=1){showErr("At least one experience entry is required.");return;}
  b.remove();list.querySelectorAll(".rn").forEach((el,i)=>el.textContent=i+1);prog();
}
window.delBlock=delBlock;
function addBullet(btn){
  const wrap=btn.previousElementSibling;
  const row=document.createElement("div");row.className="brow";
  row.innerHTML=`<span class="bdot">•</span><input class="binp" type="text" placeholder="Achievement with metric…" /><button class="bx" onclick="delBullet(this)">✕</button>`;
  wrap.appendChild(row);
}
function delBullet(btn){const w=btn.closest(".bwrap");if(w.querySelectorAll(".brow").length>1)btn.closest(".brow").remove();}
window.addBullet=addBullet;window.delBullet=delBullet;

function prog(){
  const ids=["f-name","f-email","f-phone","f-summary","f-langs","f-tech"];
  let filled=ids.filter(id=>{const el=document.getElementById(id);return el&&el.value.trim();}).length;
  const exps=document.querySelectorAll("#exp-list .rep-block");
  if(exps.length){if(exps[0].querySelector("[name='title']")?.value.trim())filled++;if(exps[0].querySelector("[name='company']")?.value.trim())filled++;}
  const pct=Math.round((filled/8)*100);
  const bar=document.getElementById("progFill"),lbl=document.getElementById("progPct");
  if(bar)bar.style.width=pct+"%";
  if(lbl)lbl.textContent=pct+"%";
}

const val=id=>document.getElementById(id)?.value.trim()||"";
const bval=(b,n)=>b.querySelector(`[name="${n}"]`)?.value.trim()||"";
const csv=id=>(document.getElementById(id)?.value||"").split(",").map(s=>s.trim()).filter(Boolean);

function build(){
  const contact={name:val("f-name"),email:val("f-email"),phone:val("f-phone"),city:val("f-city"),linkedin:val("f-linkedin")||null,github:val("f-github")||null,portfolio:val("f-portfolio")||null,website:val("f-website")||null};
  const experience=[];
  document.querySelectorAll("#exp-list .rep-block").forEach(b=>{
    const bullets=[...b.querySelectorAll(".binp")].map(i=>i.value.trim()).filter(Boolean);
    if(!bullets.length)bullets.push("Contributed to team objectives and project delivery.");
    experience.push({title:bval(b,"title"),company:bval(b,"company"),location:bval(b,"location"),start_date:bval(b,"start_date"),end_date:bval(b,"end_date")||"Present",bullets});
  });
  const education=[];
  document.querySelectorAll("#edu-list .rep-block").forEach(b=>{
    const inst=bval(b,"institution"),deg=bval(b,"degree");
    if(inst||deg)education.push({institution:inst,degree:deg,start_date:bval(b,"start_date"),end_date:bval(b,"end_date")});
  });
  const projects=[];
  document.querySelectorAll("#proj-list .rep-block").forEach(b=>{
    const name=bval(b,"name"),desc=bval(b,"description");
    if(name||desc)projects.push({name,description:desc,link:bval(b,"link")||null});
  });
  const certifications=[];
  document.querySelectorAll("#cert-list .rep-block").forEach(b=>{
    const name=bval(b,"name");if(name)certifications.push({name,link:bval(b,"link")||null});
  });
  return{contact,summary:val("f-summary"),experience,education,projects,skills:{languages_tools:csv("f-langs"),techniques:csv("f-tech"),soft_skills:csv("f-soft")},certifications};
}

function validate(d){
  if(!d.contact.name)return"Please enter your full name.";
  if(!d.contact.email)return"Please enter your email address.";
  if(!d.contact.email.includes("@"))return"Please enter a valid email address.";
  if(!d.summary)return"Please add a professional summary.";
  if(!d.experience.length)return"Please add at least one experience entry.";
  if(!d.experience[0].title)return"Please enter a job title for Experience #1.";
  if(!d.experience[0].company)return"Please enter a company for Experience #1.";
  return null;
}

async function generatePDF(){
  const btn=document.getElementById("genBtn"),txt=document.getElementById("genText"),err=document.getElementById("errBox");
  err.classList.add("hidden");
  const data=build(),e=validate(data);
  if(e){showErr(e);return;}
  btn.disabled=true;btn.classList.add("loading");
  txt.innerHTML='<span class="spinner"></span> Generating your PDF…';
  try{
    const res=await fetch("/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
    if(!res.ok){const j=await res.json().catch(()=>({}));throw new Error(j?.error||`Error ${res.status}`);}
    const blob=await res.blob(),url=URL.createObjectURL(blob);
    const a=document.createElement("a");a.href=url;a.download=`${data.contact.name.replace(/\s+/g,"_")}_ATS_Resume.pdf`;
    document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
    btn.classList.remove("loading");btn.classList.add("success");
    txt.textContent="✓ PDF Downloaded! Generate Again";
    setTimeout(()=>{btn.disabled=false;btn.classList.remove("success");txt.innerHTML='⚡ Generate ATS Resume PDF';},4000);
  }catch(e){
    btn.disabled=false;btn.classList.remove("loading");txt.innerHTML='⚡ Generate ATS Resume PDF';
    showErr(e.message||"Something went wrong. Please try again.");
  }
}
window.generatePDF=generatePDF;

function showErr(msg){const b=document.getElementById("errBox");b.textContent="⚠ "+msg;b.classList.remove("hidden");b.scrollIntoView({behavior:"smooth",block:"center"});}
