// ════════════════════════════════════════════════════════════════════
// App — logique principale Moon Predictions Web
// ════════════════════════════════════════════════════════════════════

import { loadLanguage, tr, applyToDom, locDate, locDateLong, getLang } from "./i18n.js";
import {
  $, $$, el,
  emePathLossPerigee, emeColor, qualityScore, qualityColor, qualitySquares,
  utcOffsetMs, formatHM, formatTz,
  EL_GREEN, EL_ORANGE, DUR_GREEN, DUR_ORANGE,
  DIST_GREEN, DIST_ORANGE, PL_GREEN, PL_ORANGE,
} from "./utils.js";
import { apiPasses, apiNowDetail, apiMoon, apiPassTimeline, apiLocator } from "./api.js";

const state = {
  lat: 0, lon: 0, altM: 0,
  callsign: "", locator: "",
  passes: [],
  periodIndex: 0,
  distRef: "topo",
  horizonMode: "geom",
  theme: "dark",
};

// ─── Persistance (localStorage) ───────────────────────────────────

const LS_KEY = "moonpredweb";
function loadPrefs() {
  try {
    const p = JSON.parse(localStorage.getItem(LS_KEY) || "{}");
    Object.assign(state, {
      callsign: p.callsign || "",
      locator: p.locator || "",
      altM: p.altM || 0,
      distRef: p.distRef || "topo",
      horizonMode: p.horizonMode || "geom",
      theme: p.theme || "dark",
    });
    if (p.elMin !== undefined) $("#el-min").value = p.elMin;
    if (p.scoreMin !== undefined) $("#score-min").value = p.scoreMin;
    if (p.freq !== undefined) $("#freq").value = p.freq;
    if (p.fontSize !== undefined) $("#font-size").value = p.fontSize;
    if (p.phase !== undefined) $("#phase-chk").checked = p.phase;
    if (p.localTime !== undefined) $("#local-time-chk").checked = p.localTime;
    if (p.lang) $("#lang").value = p.lang;
    $("#callsign").value = state.callsign;
    $("#locator").value = state.locator;
    $("#altitude").value = state.altM;
  } catch (e) {}
}

function savePrefs() {
  localStorage.setItem(LS_KEY, JSON.stringify({
    callsign: $("#callsign").value.trim(),
    locator: $("#locator").value.trim(),
    altM: parseFloat($("#altitude").value) || 0,
    elMin: parseInt($("#el-min").value),
    scoreMin: parseInt($("#score-min").value),
    freq: $("#freq").value,
    fontSize: parseInt($("#font-size").value),
    phase: $("#phase-chk").checked,
    localTime: $("#local-time-chk").checked,
    lang: $("#lang").value,
    distRef: state.distRef,
    horizonMode: state.horizonMode,
    theme: state.theme,
  }));
}

// ─── Theme ────────────────────────────────────────────────────────

function applyTheme() {
  document.body.className = `theme-${state.theme}`;
  $("#btn-theme").textContent = state.theme === "dark" ? "☀" : "☽";
  savePrefs();
  // Retracer si donnees presentes
  if (state.passes.length) renderTable();
}

function toggleTheme() {
  state.theme = state.theme === "dark" ? "light" : "dark";
  applyTheme();
}

// ─── Horizon effectif (EL min = horizon mecanique) ────────────────

function horizonDeg() {
  return state.horizonMode === "visual" ? -0.8333 : 0.0;
}
function effectiveHorizon() {
  const elMin = parseFloat($("#el-min").value) || 0;
  return Math.max(horizonDeg(), elMin);
}

// ─── Calcul ───────────────────────────────────────────────────────

async function compute() {
  const locator = $("#locator").value.trim();
  if (!locator) { alert(tr("msg_locator_missing")); return; }
  if (locator.length < 6) { alert(tr("msg_locator_short")); return; }

  state.altM = parseFloat($("#altitude").value) || 0;
  state.callsign = $("#callsign").value.trim();

  const freq = parseFloat($("#freq").value);
  const offset = state.periodIndex * 30 * 24;
  const periodLabel = state.periodIndex === 0 ? "1-30" : "31-60";

  $("#info-msg").textContent = tr("info_computing", { period: periodLabel });
  $("#passes-body").innerHTML = "";

  try {
    const { passes } = await apiPasses({
      locator,
      alt: state.altM,
      distRef: state.distRef,
      horizon: effectiveHorizon(),
      hours: 30 * 24,
      offset,
    });
    // Calcul ploss + score cote client
    for (const p of passes) {
      p.ploss = p.distKm > 0 ? 40 * Math.log10(p.distKm / 356500) : 0;
      p.score = qualityScore(
        p.maxEl, p.durationMin, p.ploss, p.moonSun || 180,
        p.libRateMin || p.libRate || 0, freq
      );
    }
    state.passes = passes;
    // Recuperer lat/lon (depuis locator)
    const { lat, lon } = await apiLocator(locator);
    state.lat = lat; state.lon = lon;
    state.locator = locator;

    const station = state.callsign ? `${state.callsign} ` : "";
    $("#info-msg").textContent = tr("info_result", {
      station, locator, alt: state.altM,
      count: passes.length, period: periodLabel,
    });
    savePrefs();
    renderTable();
  } catch (e) {
    $("#info-msg").textContent = `${tr("msg_error")} : ${e.message}`;
  }
}

// ─── Rendu de la table ────────────────────────────────────────────

function renderTable() {
  const minEl = parseInt($("#el-min").value);
  const minScore = parseInt($("#score-min").value) / 10;
  const showPhase = $("#phase-chk").checked;
  const useLocal = $("#local-time-chk").checked;
  const tzOffset = useLocal ? utcOffsetMs() : 0;
  const tzSuffix = useLocal ? "" : " UTC";
  const freq = parseFloat($("#freq").value);
  const freqLabel = $("#freq").selectedOptions[0].textContent;
  const plPerigee = emePathLossPerigee(freq);

  const filtered = state.passes.filter(d => d.maxEl >= minEl && d.score >= minScore);

  // Header
  const cols = [
    tr("col_date"),
    `${tr("col_rise")}${tzSuffix}`,
    `${tr("col_set")}${tzSuffix}`,
    tr("col_duration"),
    tr("col_el_max"),
    `${tr("col_el_max_time")}${tzSuffix}`,
    tr("col_az_rise"),
    tr("col_az_set"),
    tr("col_decl"),
    tr("col_distance"),
    tr("col_extra_pl"),
    tr("col_total_pl", { freq: freqLabel }),
    tr("col_moon_sun"),
    tr("col_libration"),
    tr("col_spread_min", { freq: freqLabel }),
    tr("col_spread_max", { freq: freqLabel }),
    tr("col_quality"),
  ];
  if (showPhase) cols.push(tr("col_phase"));

  const header = $("#passes-header");
  header.innerHTML = "";
  const tips = ["tip_date","tip_rise","tip_set","tip_duration","tip_el_max",
    "tip_el_max_time","tip_az_rise","tip_az_set","tip_decl","tip_distance",
    "tip_extra_pl","tip_total_pl","tip_moon_sun","tip_libration","tip_spread_min",
    "tip_spread_max","tip_quality","tip_phase"];
  cols.forEach((c, i) => {
    const th = el("th", { title: tr(tips[i] || "") || "" });
    th.textContent = c;
    header.appendChild(th);
  });

  // Body
  const body = $("#passes-body");
  body.innerHTML = "";

  // Ligne MAINTENANT (async) + auto-refresh toutes les 5 secondes
  if (state.lat !== 0 || state.lon !== 0) {
    const nowRow = el("tr", { class: "now-row", title: tr("tip_row_click") });
    for (let i = 0; i < cols.length; i++) nowRow.appendChild(el("td", {}, "..."));
    body.appendChild(nowRow);
    nowRow.addEventListener("click", () => showNowDetail());
    fillNowRow(nowRow, freq, showPhase, tzOffset, plPerigee);
    // Stopper l'ancien timer (evite les doublons si renderTable rappelé)
    if (window._nowRowTimer) clearInterval(window._nowRowTimer);
    window._nowRowTimer = setInterval(() => {
      // Ligne peut avoir ete detachée (re-render) -> stop
      if (!document.body.contains(nowRow)) {
        clearInterval(window._nowRowTimer);
        window._nowRowTimer = null;
        return;
      }
      fillNowRow(nowRow, freq, showPhase, tzOffset, plPerigee);
    }, 5000);
  }

  // Lignes passages
  for (const d of filtered) {
    const riseDt = new Date(new Date(d.riseTime).getTime() + tzOffset);
    const setDt = new Date(new Date(d.setTime).getTime() + tzOffset);
    const maxElDt = new Date(new Date(d.maxElTime).getTime() + tzOffset);
    const durH = Math.floor(d.durationMin / 60);
    const durM = Math.floor(d.durationMin % 60);

    const row = el("tr", {
      class: "pass-row",
      title: tr("tip_row_click"),
    });
    row.addEventListener("click", () => showDayDetail(d));

    const f = (v) => v.toString();
    const fmtT = (dt) => `${String(dt.getUTCHours()).padStart(2,"0")}:${String(dt.getUTCMinutes()).padStart(2,"0")}`;

    row.appendChild(el("td", {}, locDate(riseDt)));
    row.appendChild(el("td", {}, fmtT(riseDt)));
    row.appendChild(el("td", {}, fmtT(setDt)));
    row.appendChild(el("td", { class: emeColor(d.durationMin, DUR_GREEN, DUR_ORANGE) }, `${durH}h${String(durM).padStart(2,"0")}`));
    row.appendChild(el("td", { class: emeColor(d.maxEl, EL_GREEN, EL_ORANGE) }, `${d.maxEl.toFixed(1)}°`));
    row.appendChild(el("td", {}, fmtT(maxElDt)));
    row.appendChild(el("td", {}, `${Math.round(d.azRise)}°`));
    row.appendChild(el("td", {}, `${Math.round(d.azSet)}°`));
    row.appendChild(el("td", {}, `${d.decl >= 0 ? "+" : ""}${d.decl.toFixed(1)}°`));
    row.appendChild(el("td", { class: emeColor(d.distKm, DIST_GREEN, DIST_ORANGE, true) }, `${Math.round(d.distKm)} km`));
    row.appendChild(el("td", { class: emeColor(d.ploss, PL_GREEN, PL_ORANGE, true) }, `+${d.ploss.toFixed(1)} dB`));
    row.appendChild(el("td", { class: emeColor(d.ploss, PL_GREEN, PL_ORANGE, true) }, `${(plPerigee + d.ploss).toFixed(1)} dB`));
    const ms = d.moonSun || 180;
    row.appendChild(el("td", { class: ms < 5 ? "eme-red" : ms < 15 ? "eme-orange" : "eme-green" }, `${Math.round(ms)}°`));
    const libR = d.libRateMin || d.libRate || 0;
    row.appendChild(el("td", { class: libR < 0.10 ? "eme-green" : libR < 0.25 ? "eme-orange" : "eme-red" }, `${libR.toFixed(2)}°/h`));

    const spMin = (d.spreadMin || d.dopplerSpread || 0) * freq / 10.368e9;
    const spMinT = d.spreadMinTime
      ? formatHM(new Date(new Date(d.spreadMinTime).getTime() + tzOffset), false)
      : "";
    const spMinCls = spMin < 50 ? "eme-green" : spMin < 150 ? "eme-orange" : "eme-red";
    row.appendChild(el("td", { class: spMinCls }, `${Math.round(spMin)} Hz${spMinT ? " @ " + spMinT : ""}`));

    const spMax = (d.spreadMax || d.dopplerSpread || 0) * freq / 10.368e9;
    const spMaxT = d.spreadMaxTime
      ? formatHM(new Date(new Date(d.spreadMaxTime).getTime() + tzOffset), false)
      : "";
    const spMaxCls = spMax < 50 ? "eme-green" : spMax < 150 ? "eme-orange" : "eme-red";
    row.appendChild(el("td", { class: spMaxCls }, `${Math.round(spMax)} Hz${spMaxT ? " @ " + spMaxT : ""}`));

    row.appendChild(el("td", { class: qualityColor(d.score) }, `${qualitySquares(d.score)} ${d.score.toFixed(1)}`));
    if (showPhase) row.appendChild(el("td", {}, `${tr(d.phase || "")} (${(d.illum || 0).toFixed(0)}%)`));

    body.appendChild(row);
  }

  // Footer
  const now = new Date();
  const calcTime = useLocal
    ? `${now.toISOString().slice(0, 10)} ${formatHM(now, true)} ${formatTz()}`
    : `${now.toISOString().slice(0, 10)} ${formatHM(now, false)} UTC`;
  $("#footer-msg").textContent = tr("footer_calc", { time: calcTime });

  // Update TZ label
  $("#tz-label").textContent = useLocal ? formatTz() : "";
}

async function fillNowRow(row, freq, showPhase, tzOffset, plPerigee) {
  try {
    const data = await apiNowDetail({
      locator: $("#locator").value.trim(),
      alt: state.altM,
      distRef: state.distRef,
      horizon: effectiveHorizon(),
      freq,
    });
    const { moon, sun, lib, deg, ha } = data;
    const visible = moon.el > 0;
    row.classList.toggle("off", !visible);
    const useLocal = $("#local-time-chk").checked;
    const statusTxt = visible ? tr("now_visible") : tr("now_below");
    const riseTxt = moon.nextRise
      ? formatHM(new Date(new Date(moon.nextRise).getTime() + tzOffset), false)
      : "---";
    const setTxt = moon.nextSet
      ? formatHM(new Date(new Date(moon.nextSet).getTime() + tzOffset), false)
      : "---";
    let durTxt = "---";
    if (moon.nextRise && moon.nextSet) {
      const durMs = new Date(moon.nextSet) - new Date(moon.nextRise);
      const dh = Math.floor(Math.abs(durMs) / 3600000);
      const dm = Math.floor(Math.abs(durMs) / 60000) % 60;
      durTxt = `${dh}h${String(dm).padStart(2,"0")}`;
    }
    const spread = lib.dopplerSpreadHz * freq / 10.368e9;
    const nowUtc = new Date().toISOString().slice(11, 16) + " UTC";

    const nowClass = visible ? "now-hi" : "";
    const cells = [
      tr(visible ? "now_label" : "now_label_off"),
      riseTxt, setTxt, durTxt,
      `${moon.el >= 0 ? "+" : ""}${moon.el.toFixed(1)}° ${statusTxt}`,
      nowUtc,
      `${Math.round(moon.az)}°`,
      "---",
      `${ha.decDeg >= 0 ? "+" : ""}${ha.decDeg.toFixed(1)}°`,
      `${Math.round(moon.distKm)} km`,
      `+${deg.pathLossExtraDb.toFixed(1)} dB`,
      `${(plPerigee + deg.pathLossExtraDb).toFixed(1)} dB`,
      `${Math.round(angularSep(moon.az, moon.el, sun.az, sun.el))}°`,
      `${lib.libRate.toFixed(2)}°/h`,
      `${Math.round(spread)} Hz`,
      `${Math.round(spread)} Hz`,
      visible ? `${qualitySquares(qualityScore(Math.max(moon.el, 0), 0, deg.pathLossExtraDb, 180, lib.libRate, freq))} ${qualityScore(Math.max(moon.el, 0), 0, deg.pathLossExtraDb, 180, lib.libRate, freq).toFixed(1)}` : "---",
    ];
    if (showPhase) cells.push(`${tr(moon.phaseName)} (${Math.round(moon.illumination)}%)`);
    // Clear and refill
    row.innerHTML = "";
    cells.forEach(text => {
      const td = el("td", { class: nowClass }, text);
      row.appendChild(td);
    });
  } catch (e) {
    console.error("fillNowRow:", e);
  }
}

function angularSep(az1, el1, az2, el2) {
  const r = Math.PI / 180;
  const cs = Math.sin(el1 * r) * Math.sin(el2 * r)
    + Math.cos(el1 * r) * Math.cos(el2 * r) * Math.cos((az1 - az2) * r);
  return Math.acos(Math.max(-1, Math.min(1, cs))) * 180 / Math.PI;
}

// ─── Modales (imports dynamiques des modules de modales) ──────────

async function showConventions() {
  const m = await import("./modals.js");
  m.showConventions(state, () => { compute(); });
}
async function showHelp() {
  const m = await import("./modals.js");
  m.showHelp();
}
async function showAbout() {
  const m = await import("./modals.js");
  m.showAbout();
}
async function showDayDetail(passData) {
  const m = await import("./modals.js");
  m.showDayDetail(state, passData);
}
async function showNowDetail() {
  const m = await import("./modals.js");
  m.showNowDetail(state);
}

// ─── Export TXT / PDF ─────────────────────────────────────────────

function exportTxt() {
  if (!state.passes.length) { alert(tr("msg_no_data")); return; }
  const useLocal = $("#local-time-chk").checked;
  const tzOffset = useLocal ? utcOffsetMs() : 0;
  const freq = parseFloat($("#freq").value);
  const callsign = state.callsign || "";
  const locator = state.locator || "";
  let out = `Moon Predictions  -  ${callsign} ${locator}  alt ${state.altM}m\n`;
  out += `Calcul : ${new Date().toISOString().slice(0, 16)} UTC\n`;
  out += "=".repeat(100) + "\n";
  for (const d of state.passes) {
    const riseDt = new Date(new Date(d.riseTime).getTime() + tzOffset);
    const setDt = new Date(new Date(d.setTime).getTime() + tzOffset);
    const maxElDt = new Date(new Date(d.maxElTime).getTime() + tzOffset);
    const fmtT = (dt) => `${String(dt.getUTCHours()).padStart(2,"0")}:${String(dt.getUTCMinutes()).padStart(2,"0")}`;
    out += `${locDateLong(riseDt).padEnd(18)} | `
      + `${fmtT(riseDt)} - ${fmtT(setDt)} (${Math.floor(d.durationMin / 60)}h${String(Math.floor(d.durationMin % 60)).padStart(2, "0")}) | `
      + `EL ${d.maxEl.toFixed(1).padStart(5)}° @ ${fmtT(maxElDt)} | `
      + `AZ ${Math.round(d.azRise).toString().padStart(3)}->${Math.round(d.azSet).toString().padStart(3)} | `
      + `D${(d.decl >= 0 ? "+" : "") + d.decl.toFixed(1).padStart(5)}° | `
      + `${Math.round(d.distKm).toString().padStart(6)}km | `
      + `PL+${d.ploss.toFixed(1).padStart(4)}dB | `
      + `Q${d.score.toFixed(1).padStart(4)}\n`;
  }
  const blob = new Blob([out], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "moon_predictions.txt";
  a.click();
  URL.revokeObjectURL(url);
}

function exportPdf() {
  if (!state.passes.length) { alert(tr("msg_no_data")); return; }
  window.print();
}

// ─── Bindings ─────────────────────────────────────────────────────

async function init() {
  loadPrefs();
  await loadLanguage($("#lang").value || "fr");
  applyTheme();

  $("#btn-compute").addEventListener("click", compute);
  $("#btn-save").addEventListener("click", () => {
    savePrefs();
    $("#btn-save").textContent = tr("btn_saved");
    setTimeout(() => $("#btn-save").textContent = tr("btn_save"), 1500);
  });
  $("#btn-theme").addEventListener("click", toggleTheme);
  $("#btn-conventions").addEventListener("click", showConventions);
  $("#btn-help").addEventListener("click", showHelp);
  $("#btn-about").addEventListener("click", showAbout);
  $("#btn-export-txt").addEventListener("click", exportTxt);
  $("#btn-export-pdf").addEventListener("click", exportPdf);
  $("#btn-1-30").addEventListener("click", () => {
    state.periodIndex = 0;
    $("#btn-1-30").classList.add("active");
    $("#btn-31-60").classList.remove("active");
    if (state.passes.length || $("#locator").value) compute();
  });
  $("#btn-31-60").addEventListener("click", () => {
    state.periodIndex = 1;
    $("#btn-31-60").classList.add("active");
    $("#btn-1-30").classList.remove("active");
    if (state.passes.length || $("#locator").value) compute();
  });

  $("#el-min").addEventListener("input", () => {
    $("#el-min-val").textContent = $("#el-min").value + "°";
    clearTimeout(window._elMinTimer);
    window._elMinTimer = setTimeout(() => {
      if (state.passes.length && $("#locator").value) compute();
    }, 500);
  });
  $("#score-min").addEventListener("input", () => {
    $("#score-min-val").textContent = (parseInt($("#score-min").value) / 10).toFixed(1);
    clearTimeout(window._refreshTimer);
    window._refreshTimer = setTimeout(renderTable, 150);
  });
  $("#phase-chk").addEventListener("change", renderTable);
  $("#local-time-chk").addEventListener("change", renderTable);
  $("#freq").addEventListener("change", () => {
    if (state.passes.length) {
      // Recalcul score avec nouvelle frequence
      const freq = parseFloat($("#freq").value);
      for (const p of state.passes) {
        p.score = qualityScore(
          p.maxEl, p.durationMin, p.ploss, p.moonSun || 180,
          p.libRateMin || p.libRate || 0, freq
        );
      }
      renderTable();
    }
    savePrefs();
  });
  $("#font-size").addEventListener("change", () => {
    document.body.style.fontSize = `${$("#font-size").value}px`;
    savePrefs();
  });
  document.body.style.fontSize = `${$("#font-size").value}px`;

  $("#lang").addEventListener("change", async () => {
    await loadLanguage($("#lang").value);
    savePrefs();
    if (state.passes.length) renderTable();
  });

  // Initial labels
  $("#el-min-val").textContent = $("#el-min").value + "°";
  $("#score-min-val").textContent = (parseInt($("#score-min").value) / 10).toFixed(1);
  $("#tz-label").textContent = $("#local-time-chk").checked ? formatTz() : "";

  // Auto-compute si locator deja saisi
  if ($("#locator").value.trim().length >= 6) {
    setTimeout(compute, 300);
  }
}

init();
