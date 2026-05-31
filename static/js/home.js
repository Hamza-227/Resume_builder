"use strict";
// Dashboard ring on hero
const ring = document.querySelector(".sr-fill");
if (ring) setTimeout(() => { ring.style.strokeDashoffset = "17"; }, 600);

// Bar animations on hero mockup
document.querySelectorAll(".db-fill").forEach(el => {
  setTimeout(() => { el.style.width = el.dataset.w || "0%"; }, 800);
});
