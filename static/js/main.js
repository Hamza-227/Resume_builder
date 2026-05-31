"use strict";
// ─── THEME ────────────────────────────────────────────────────────
const html = document.documentElement;
const stored = localStorage.getItem("ratsTheme") || "dark";
html.setAttribute("data-theme", stored);

const themeBtn = document.getElementById("themeToggle");
if (themeBtn) {
  const icon = themeBtn.querySelector(".theme-icon");
  icon.textContent = stored === "dark" ? "☀" : "🌙";
  themeBtn.addEventListener("click", () => {
    const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
    html.setAttribute("data-theme", next);
    localStorage.setItem("ratsTheme", next);
    icon.textContent = next === "dark" ? "☀" : "🌙";
  });
}

// ─── NAVBAR ───────────────────────────────────────────────────────
const navbar = document.getElementById("navbar");
const burger = document.getElementById("navBurger");
const navMenu = document.getElementById("navMenu");

// Scroll shadow
if (navbar) {
  const onScroll = () => navbar.classList.toggle("scrolled", window.scrollY > 24);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}

// Mobile menu
if (burger && navMenu) {
  burger.addEventListener("click", () => {
    const open = navMenu.classList.toggle("open");
    burger.setAttribute("aria-expanded", open);
    const spans = burger.querySelectorAll("span");
    spans[0].style.transform = open ? "rotate(45deg) translate(5px,5px)" : "";
    spans[1].style.opacity  = open ? "0" : "1";
    spans[2].style.transform = open ? "rotate(-45deg) translate(5px,-5px)" : "";
  });
  navMenu.querySelectorAll(".nav-item").forEach(a =>
    a.addEventListener("click", () => navMenu.classList.remove("open"))
  );
}

// ─── FAQ — SMOOTH ACCORDION ───────────────────────────────────────
function toggleFaq(btn) {
  const item = btn.closest(".faq-item");
  const wasOpen = item.classList.contains("open");
  document.querySelectorAll(".faq-item.open").forEach(i => i.classList.remove("open"));
  if (!wasOpen) item.classList.add("open");
}
window.toggleFaq = toggleFaq;

// ─── ANIMATED COUNTERS ────────────────────────────────────────────
function animateCount(el, target, duration = 1600) {
  const startTime = performance.now();
  const update = now => {
    const p = Math.min((now - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(target * ease).toLocaleString();
    if (p < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

// ─── SCROLL REVEAL ────────────────────────────────────────────────
const io = new IntersectionObserver(
  entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      e.target.classList.add("revealed");
      // Counters
      const num = e.target.querySelector(".stat-num[data-target]");
      if (num) animateCount(num, +num.dataset.target);
      io.unobserve(e.target);
    });
  },
  { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
);

// Counter stat items
document.querySelectorAll(".stat-num[data-target]").forEach(el => {
  const item = el.closest(".stat-item");
  if (item) io.observe(item);
});
// Reveal elements
document.querySelectorAll("[data-reveal], .tool-card, .bp-card, .testi-card, .step").forEach(el => io.observe(el));

// Also trigger hero dashboard ring animation
const heroDashRing = document.querySelector(".sr-fill");
if (heroDashRing) {
  setTimeout(() => { heroDashRing.style.strokeDashoffset = "17"; }, 400);
}

// ─── TOOL CARD GLOW TRACKING ──────────────────────────────────────
document.querySelectorAll(".tool-card:not(.tool-card-soon)").forEach(card => {
  card.addEventListener("mousemove", e => {
    const r = card.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * 100;
    const y = ((e.clientY - r.top)  / r.height) * 100;
    const glow = card.querySelector(".tool-glow");
    if (glow) glow.style.background =
      `radial-gradient(circle at ${x}% ${y}%, rgba(59,130,246,.2), transparent 60%)`;
  });
});

// ─── SMOOTH SCROLL ────────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener("click", e => {
    const t = document.querySelector(a.getAttribute("href"));
    if (t) { e.preventDefault(); t.scrollIntoView({ behavior: "smooth", block: "start" }); }
  });
});
