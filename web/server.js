// ════════════════════════════════════════════════════════════════════
// Moon Predictions Web — Serveur Express + API
// Sert les fichiers statiques dans public/ et expose les calculs sous /api.
// ════════════════════════════════════════════════════════════════════

import express from "express";
import path from "path";
import { fileURLToPath } from "url";
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
} from "./lib/moon-calc.js";
import { MakeTime } from "astronomy-engine";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json({ limit: "512kb" }));
app.use(express.static(path.join(__dirname, "public")));

// ─── Utilitaires ──────────────────────────────────────────────────

function asyncHandler(fn) {
  return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}

function parseStation(q) {
  const locator = (q.locator || "").trim();
  const [lat, lon] = locatorToLatLon(locator);
  const altM = parseFloat(q.alt) || 0;
  return { lat, lon, altM, locator };
}

// ─── Routes ───────────────────────────────────────────────────────

app.get("/api/ping", (req, res) => {
  res.json({ ok: true, time: new Date().toISOString() });
});

app.get("/api/locator", asyncHandler((req, res) => {
  const [lat, lon] = locatorToLatLon(req.query.locator);
  res.json({ lat, lon });
}));

app.get("/api/moon", asyncHandler((req, res) => {
  const { lat, lon, altM } = parseStation(req.query);
  const distRef = req.query.distRef || "topo";
  const horizonDeg = parseFloat(req.query.horizon) || 0;
  res.json(computeMoon(lat, lon, altM, distRef, horizonDeg));
}));

app.get("/api/sun", asyncHandler((req, res) => {
  const { lat, lon, altM } = parseStation(req.query);
  const horizonDeg = parseFloat(req.query.horizon) || 0;
  res.json(computeSun(lat, lon, altM, horizonDeg));
}));

app.get("/api/now-detail", asyncHandler((req, res) => {
  const { lat, lon, altM } = parseStation(req.query);
  const distRef = req.query.distRef || "topo";
  const horizonDeg = parseFloat(req.query.horizon) || 0;
  const freq = parseFloat(req.query.freq) || 10368e6;
  const t = MakeTime(new Date());
  const moon = computeMoon(lat, lon, altM, distRef, horizonDeg);
  const sun = computeSun(lat, lon, altM, horizonDeg);
  const lib = computeLibration(lat, lon, altM, t);
  const deg = computeDegradation(lat, lon, altM, t, freq);
  const ha = computeHourAngles(lat, lon, altM, t);
  const dsp = daysSincePerigee(t);
  res.json({ moon, sun, lib, deg, ha, daysSincePerigee: dsp, freq });
}));

app.get("/api/passes", asyncHandler((req, res) => {
  const { lat, lon, altM } = parseStation(req.query);
  const distRef = req.query.distRef || "topo";
  const horizonDeg = parseFloat(req.query.horizon) || 0;
  const hours = parseInt(req.query.hours) || 30 * 24;
  const offset = parseInt(req.query.offset) || 0;
  const passes = getMoonPasses(lat, lon, altM, hours, offset, horizonDeg);
  const enriched = [];
  for (const p of passes) {
    try {
      enriched.push(enrichMoonPass(lat, lon, altM, p, distRef));
    } catch (e) {
      // Skip pass if enrichment fails
    }
  }
  res.json({ passes: enriched });
}));

app.post("/api/pass-timeline", asyncHandler((req, res) => {
  const { lat, lon, altM, passData, freq, distRef } = req.body;
  const samples = samplePassTimeline(lat, lon, altM, passData,
    30, freq || 10368e6, 50, distRef || "topo");
  res.json({ samples });
}));

// ─── Gestion d'erreurs ────────────────────────────────────────────

app.use((err, req, res, next) => {
  console.error(err);
  res.status(400).json({ error: err.message });
});

// ─── Demarrage ────────────────────────────────────────────────────

app.listen(PORT, () => {
  console.log(`Moon Predictions Web running on http://localhost:${PORT}`);
});
