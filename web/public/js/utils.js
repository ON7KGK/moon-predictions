// ════════════════════════════════════════════════════════════════════
// Utils — helpers partages
// ════════════════════════════════════════════════════════════════════

export const C_LIGHT = 299_792_458;
export const D_PERIGEE_M = 356_500_000;
export const A_MOON_M = 1_737_400;
export const RHO_MOON = 0.065;

export const EL_GREEN = 20, EL_ORANGE = 10;
export const DUR_GREEN = 300, DUR_ORANGE = 120; // minutes
export const DIST_GREEN = 370_000, DIST_ORANGE = 390_000; // km
export const PL_GREEN = 1.0, PL_ORANGE = 2.0;

export function emePathLossPerigee(freqHz) {
  const lam = C_LIGHT / freqHz;
  const num = Math.pow(4 * Math.PI, 3) * Math.pow(D_PERIGEE_M, 4);
  const den = RHO_MOON * Math.PI * Math.pow(A_MOON_M, 2) * lam * lam;
  return 10 * Math.log10(num / den);
}

export function emeColor(value, greenMax, orangeMax, invert = false) {
  if (invert) {
    if (value <= greenMax) return "eme-green";
    if (value <= orangeMax) return "eme-orange";
    return "eme-red";
  }
  if (value >= greenMax) return "eme-green";
  if (value >= orangeMax) return "eme-orange";
  return "eme-red";
}

export function qualityScore(maxEl, durationMin, ploss, moonSun = 180, libRate = 0, freqHz = 10368e6) {
  const elScore = Math.min(maxEl / 9, 10);
  const durScore = Math.min(durationMin / 60, 10);
  const plScore = Math.max(10 - ploss * 4, 0);
  const msScore = Math.min(moonSun / 18, 10);
  const libScore = Math.max(10 - libRate * 20, 0);
  if (freqHz >= 1e9) {
    return libScore * 0.30 + plScore * 0.25 + elScore * 0.20
      + msScore * 0.15 + durScore * 0.10;
  }
  return elScore * 0.30 + durScore * 0.25 + plScore * 0.25 + msScore * 0.20;
}

export function qualityColor(score) {
  if (score >= 7) return "eme-green";
  if (score >= 4) return "eme-orange";
  return "eme-red";
}

export function qualitySquares(score) {
  const n = Math.max(0, Math.min(10, Math.round(score)));
  return "■".repeat(n) + "□".repeat(10 - n);
}

export function utcOffsetMs() {
  return -new Date().getTimezoneOffset() * 60 * 1000;
}

export function formatHM(date, useLocal = false) {
  const d = useLocal ? new Date(date) : new Date(date);
  if (useLocal) return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return `${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;
}

export function formatTz() {
  const offMin = -new Date().getTimezoneOffset();
  const sign = offMin >= 0 ? "+" : "-";
  const h = Math.floor(Math.abs(offMin) / 60);
  const m = Math.abs(offMin) % 60;
  return `(UTC${sign}${h}:${String(m).padStart(2, "0")})`;
}

// DOM helpers
export function $(sel) { return document.querySelector(sel); }
export function $$(sel) { return document.querySelectorAll(sel); }

export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function") {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else node.setAttribute(k, v);
  }
  (Array.isArray(children) ? children : [children]).forEach(c => {
    if (c === null || c === undefined) return;
    if (typeof c === "string") node.appendChild(document.createTextNode(c));
    else node.appendChild(c);
  });
  return node;
}
