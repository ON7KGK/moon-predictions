// ════════════════════════════════════════════════════════════════════
// API 100% CLIENT — wrappers locaux (pas de fetch serveur)
//
// Meme interface que web/public/js/api.js pour compatibilite avec
// app.js et modals.js, mais tous les calculs se font dans le navigateur.
// Permet l'hebergement sur GitHub Pages / CDN / tout serveur statique.
// ════════════════════════════════════════════════════════════════════

import {
  locatorToLatLon,
  computeMoon,
  computeSun,
  computeLibration,
  computeDegradation,
  computeHourAngles,
  daysSincePerigee,
  getMoonPasses,
  enrichMoonPass,
  samplePassTimeline,
} from "./moon-calc.js";
import { MakeTime } from "https://esm.sh/astronomy-engine@2.1.19";

export async function apiLocator(locator) {
  const [lat, lon] = locatorToLatLon(locator);
  return { lat, lon };
}

export async function apiMoon(params) {
  const locator = params.locator;
  const altM = parseFloat(params.alt) || 0;
  const distRef = params.distRef || "topo";
  const horizon = parseFloat(params.horizon) || 0;
  const [lat, lon] = locatorToLatLon(locator);
  return computeMoon(lat, lon, altM, distRef, horizon);
}

export async function apiPasses(params) {
  const locator = params.locator;
  const altM = parseFloat(params.alt) || 0;
  const distRef = params.distRef || "topo";
  const horizon = parseFloat(params.horizon) || 0;
  const hours = parseInt(params.hours) || 30 * 24;
  const offset = parseInt(params.offset) || 0;
  const [lat, lon] = locatorToLatLon(locator);
  const passes = getMoonPasses(lat, lon, altM, hours, offset, horizon);
  const enriched = [];
  for (const p of passes) {
    try {
      enriched.push(enrichMoonPass(lat, lon, altM, p, distRef));
    } catch (e) {
      // Passage ignore si l'enrichissement echoue
    }
  }
  return { passes: enriched };
}

export async function apiNowDetail(params) {
  const locator = params.locator;
  const altM = parseFloat(params.alt) || 0;
  const distRef = params.distRef || "topo";
  const horizon = parseFloat(params.horizon) || 0;
  const freq = parseFloat(params.freq) || 10368e6;
  const [lat, lon] = locatorToLatLon(locator);
  const t = MakeTime(new Date());
  const moon = computeMoon(lat, lon, altM, distRef, horizon);
  const sun = computeSun(lat, lon, altM, horizon);
  const lib = computeLibration(lat, lon, altM, t);
  const deg = computeDegradation(lat, lon, altM, t, freq);
  const ha = computeHourAngles(lat, lon, altM, t);
  const dsp = daysSincePerigee(t);
  return { moon, sun, lib, deg, ha, daysSincePerigee: dsp, freq };
}

export async function apiPassTimeline(body) {
  const { lat, lon, altM, passData, freq, distRef } = body;
  const samples = samplePassTimeline(lat, lon, altM, passData,
    30, freq || 10368e6, 50, distRef || "topo");
  return { samples };
}
