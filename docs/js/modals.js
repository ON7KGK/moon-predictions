// ════════════════════════════════════════════════════════════════════
// Modales : Conventions, Help, About, DayDetail, NowDetail
// ════════════════════════════════════════════════════════════════════

import { tr, locDate, locDateLong } from "./i18n.js";
import { $, el, utcOffsetMs, formatHM, formatTz, formatPhaseHTML, emeColor,
  EL_GREEN, EL_ORANGE, DIST_GREEN, DIST_ORANGE } from "./utils.js";
import { apiPassTimeline, apiNowDetail, apiLocator } from "./api.js";
import { computeSpreadingBistatic, computePolarizationOffset, computeMnr, locatorToLatLon, computeDopplerBistatic, computeMoonAzEl } from "./moon-calc.js";
import { MakeTime } from "https://esm.sh/astronomy-engine@2.1.19";

const APP_VERSION = "1.9.0-alpha";
const APP_DATE = "2026-04-19";

// Helpers DX + polarisation Home (lus depuis le DOM)
function getDxInfo() {
  const dx = ($("#dx-locator")?.value || "").trim();
  if (!dx) return null;
  try {
    const [lat, lon] = locatorToLatLon(dx);
    return { locator: dx.toUpperCase(), lat, lon };
  } catch (e) { return null; }
}
function getPolHome() {
  return parseInt($("#pol-home")?.value) || 90;
}

// ─── Helpers ──────────────────────────────────────────────────────

function openModal(contentNode, wide = false, narrow = false, extra = "") {
  const overlay = $("#modal-overlay");
  const content = $("#modal-content");
  content.className = `modal-content${wide ? " wide" : ""}${narrow ? " narrow" : ""}${extra ? " " + extra : ""}`;
  content.innerHTML = "";
  content.appendChild(contentNode);
  overlay.classList.remove("hidden");
  // Fermer au clic sur l'overlay (hors contenu)
  overlay.onclick = (e) => { if (e.target === overlay) closeModal(); };
  // ESC pour fermer
  const onKey = (e) => { if (e.key === "Escape") { closeModal(); document.removeEventListener("keydown", onKey); } };
  document.addEventListener("keydown", onKey);
}

// Timer d'auto-refresh pour le dialog NowDetail (nettoye a la fermeture)
let _nowRefreshTimer = null;
// Tracking rotation polarisation cumulee (reinit a chaque ouverture modale)
let _polCumLast = null;
let _polCumTotal = 0;

export function closeModal() {
  $("#modal-overlay").classList.add("hidden");
  if (_nowRefreshTimer !== null) {
    clearInterval(_nowRefreshTimer);
    _nowRefreshTimer = null;
  }
  _polCumLast = null;
  _polCumTotal = 0;
}

function closeBtn() {
  const row = el("div", { class: "close-row" });
  const btn = el("button", {}, tr("btn_close"));
  btn.addEventListener("click", closeModal);
  row.appendChild(btn);
  return row;
}

// ─── Help ─────────────────────────────────────────────────────────

export function showHelp() {
  const content = el("div");
  const body = el("div", { html: tr("help_content") });
  content.appendChild(body);
  content.appendChild(closeBtn());
  openModal(content);
}

// ─── About ────────────────────────────────────────────────────────

export function showAbout() {
  const content = el("div");
  content.appendChild(el("div", {
    html: `
      <h2 style="text-align:center;">☽ Moon Predictions Web</h2>
      <p style="text-align:center; color: var(--about-version); font-size: 1.1em;">
        Version ${APP_VERSION} — ${APP_DATE}
      </p>
      <hr>
      <p style="text-align:center;">${tr("about_desc")}</p>
      <hr>
      <p style="text-align:center;">
        ${tr("about_author")} ON7KGK — Michaël<br>
        ${tr("about_dev")} Claude Code (Anthropic)<br>
        ${tr("about_ephem")} astronomy-engine (MIT)
      </p>
      <hr>
      <p style="text-align:center;">
        ${tr("about_thanks")}<br>
        ${tr("about_thanks_text")}
      </p>
      <hr>
      <p style="text-align:center;">${tr("about_opensource")}</p>
      <hr>
      <p style="text-align:center;">${tr("about_license")}</p>
    `
  }));
  content.appendChild(closeBtn());
  openModal(content, false, true);
}

// ─── Conventions ──────────────────────────────────────────────────

export function showConventions(state, onApply) {
  const content = el("div");
  content.appendChild(el("h2", {}, tr("conv_title")));
  content.appendChild(el("div", { html: `<p>${tr("conv_intro")}</p>` }));

  // Distance group
  const distGrp = el("fieldset", { class: "convention-group" });
  distGrp.appendChild(el("legend", {}, tr("conv_dist_group")));
  const distTopo = el("label", { class: state.distRef === "topo" ? "selected" : "" }, [
    el("input", { type: "radio", name: "distRef", value: "topo",
      ...(state.distRef === "topo" ? { checked: "" } : {}) }),
    tr("conv_dist_topo"),
  ]);
  const distGeo = el("label", { class: state.distRef === "geo" ? "selected" : "" }, [
    el("input", { type: "radio", name: "distRef", value: "geo",
      ...(state.distRef === "geo" ? { checked: "" } : {}) }),
    tr("conv_dist_geo"),
  ]);
  distGrp.appendChild(distTopo);
  distGrp.appendChild(distGeo);
  distGrp.appendChild(el("p", { class: "explain" }, [
    el("span", { html: tr("conv_dist_explain") })
  ]));
  content.appendChild(distGrp);

  // Horizon group
  const horGrp = el("fieldset", { class: "convention-group" });
  horGrp.appendChild(el("legend", {}, tr("conv_hor_group")));
  const horGeom = el("label", { class: state.horizonMode === "geom" ? "selected" : "" }, [
    el("input", { type: "radio", name: "horMode", value: "geom",
      ...(state.horizonMode === "geom" ? { checked: "" } : {}) }),
    tr("conv_hor_geom"),
  ]);
  const horVisual = el("label", { class: state.horizonMode === "visual" ? "selected" : "" }, [
    el("input", { type: "radio", name: "horMode", value: "visual",
      ...(state.horizonMode === "visual" ? { checked: "" } : {}) }),
    tr("conv_hor_visual"),
  ]);
  horGrp.appendChild(horGeom);
  horGrp.appendChild(horVisual);
  horGrp.appendChild(el("p", { class: "explain" }, [
    el("span", { html: tr("conv_hor_explain") })
  ]));
  content.appendChild(horGrp);

  // Surbrillance au clic radio
  content.querySelectorAll('input[type="radio"]').forEach(r => {
    r.addEventListener("change", () => {
      r.closest("fieldset").querySelectorAll("label").forEach(l => l.classList.remove("selected"));
      r.closest("label").classList.add("selected");
    });
  });

  // Buttons row
  const btnRow = el("div", { class: "close-row" });
  const btnCancel = el("button", {}, tr("btn_cancel"));
  btnCancel.addEventListener("click", closeModal);
  const btnOk = el("button", { class: "btn-primary" }, tr("btn_apply"));
  btnOk.addEventListener("click", () => {
    const newDist = content.querySelector('input[name="distRef"]:checked').value;
    const newHor = content.querySelector('input[name="horMode"]:checked').value;
    const changed = newDist !== state.distRef || newHor !== state.horizonMode;
    state.distRef = newDist;
    state.horizonMode = newHor;
    closeModal();
    if (changed) onApply();
  });
  btnRow.appendChild(btnCancel);
  btnRow.appendChild(btnOk);
  content.appendChild(btnRow);

  openModal(content);
}

// ─── Day detail ───────────────────────────────────────────────────

export async function showDayDetail(state, passData) {
  const freq = parseFloat($("#freq").value);
  const freqLabel = $("#freq").selectedOptions[0].textContent;
  const useLocal = $("#local-time-chk").checked;
  const tzOffset = useLocal ? utcOffsetMs() : 0;
  const tzSuffix = useLocal ? "" : " UTC";

  const content = el("div");
  const riseDt = new Date(new Date(passData.riseTime).getTime() + tzOffset);
  const title = `${tr("day_detail_title")} — ${locDateLong(riseDt)}`;
  content.appendChild(el("h2", {}, title));

  // En-tete resume
  const maxElT = new Date(new Date(passData.maxElTime).getTime() + tzOffset);
  const durH = Math.floor(passData.durationMin / 60);
  const durM = Math.floor(passData.durationMin % 60);
  const hdr = `${tr("col_el_max")}: ${passData.maxEl.toFixed(1)}° @ ${formatHM(maxElT, false)}${tzSuffix} — ${tr("col_duration")}: ${durH}h${String(durM).padStart(2,"0")} — ${tr("lbl_frequency")} ${freqLabel}`;
  content.appendChild(el("p", { style: "color: var(--fg-info);" }, hdr));

  const tableWrap = el("div", { style: "overflow-x: auto; max-height: 65vh;" });
  tableWrap.appendChild(el("p", {}, "⏳ " + tr("info_computing", { period: "..." })));
  content.appendChild(tableWrap);
  content.appendChild(closeBtn());
  openModal(content, true);

  // Appel API en arriere-plan
  try {
    const { samples } = await apiPassTimeline({
      lat: state.lat, lon: state.lon, altM: state.altM,
      passData, freq, distRef: state.distRef,
    });

    const cols = [
      `${tr("col_day_time")}${tzSuffix}`,
      tr("col_az"), tr("col_el"), tr("col_day_distance"),
      tr("col_day_pl_extra"), tr("col_day_decl"),
      tr("col_day_doppler", { freq: freqLabel }),
      tr("col_day_spread", { freq: freqLabel }),
      tr("col_day_tsky"), tr("col_day_dgr"),
      tr("col_day_libration"), tr("col_day_lha"),
      tr("col_day_ms"), tr("col_day_sun_az"), tr("col_day_sun_el"),
    ];

    const table = el("table", { id: "day-detail-table", style: "width: 100%;" });
    const thead = el("thead");
    const trh = el("tr");
    cols.forEach(c => trh.appendChild(el("th", {}, c)));
    thead.appendChild(trh);
    table.appendChild(thead);
    const tbody = el("tbody");
    for (const s of samples) {
      const tLocal = new Date(new Date(s.time).getTime() + tzOffset);
      const row = el("tr");
      row.appendChild(el("td", {}, formatHM(tLocal, false)));
      row.appendChild(el("td", {}, `${Math.round(s.az)}°`));
      row.appendChild(el("td", { class: emeColor(s.el, EL_GREEN, EL_ORANGE) }, `${s.el.toFixed(1)}°`));
      row.appendChild(el("td", { class: emeColor(s.distKm, DIST_GREEN, DIST_ORANGE, true) }, `${Math.round(s.distKm)} km`));
      const plCls = s.pathLossExtraDb < 1 ? "eme-green" : s.pathLossExtraDb < 2 ? "eme-orange" : "eme-red";
      row.appendChild(el("td", { class: plCls }, `${s.pathLossExtraDb >= 0 ? "+" : ""}${s.pathLossExtraDb.toFixed(2)} dB`));
      row.appendChild(el("td", {}, `${s.decl >= 0 ? "+" : ""}${s.decl.toFixed(1)}°`));
      row.appendChild(el("td", {}, `${s.dopplerHz >= 0 ? "+" : ""}${Math.round(s.dopplerHz)} Hz`));
      const spCls = s.spreadHz < 50 ? "eme-green" : s.spreadHz < 150 ? "eme-orange" : "eme-red";
      row.appendChild(el("td", { class: spCls }, `${Math.round(s.spreadHz)} Hz`));
      const tskyCls = s.skyTempK < 10 ? "eme-green" : s.skyTempK < 50 ? "eme-orange" : "eme-red";
      row.appendChild(el("td", { class: tskyCls }, `${s.skyTempK.toFixed(1)} K`));
      const dgrCls = s.degradationDb < 1 ? "eme-green" : s.degradationDb < 3 ? "eme-orange" : "eme-red";
      row.appendChild(el("td", { class: dgrCls }, `${s.degradationDb >= 0 ? "+" : ""}${s.degradationDb.toFixed(2)} dB`));
      const libCls = s.libRate < 0.10 ? "eme-green" : s.libRate < 0.25 ? "eme-orange" : "eme-red";
      row.appendChild(el("td", { class: libCls }, `${s.libRate.toFixed(2)}°/h`));
      row.appendChild(el("td", {}, `${s.lha >= 0 ? "+" : ""}${s.lha.toFixed(1)}°`));
      const msCls = s.moonSun < 5 ? "eme-red" : s.moonSun < 15 ? "eme-orange" : "eme-green";
      row.appendChild(el("td", { class: msCls }, `${Math.round(s.moonSun)}°`));
      const sunStyle = s.sunEl > 0 ? "" : "color: var(--fg-dim);";
      row.appendChild(el("td", { style: sunStyle }, `${Math.round(s.sunAz)}°`));
      const sunElStyle = s.sunEl > 0 ? "color: var(--eme-orange);" : "color: var(--fg-dim);";
      row.appendChild(el("td", { style: sunElStyle }, `${s.sunEl >= 0 ? "+" : ""}${Math.round(s.sunEl)}°`));
      tbody.appendChild(row);
    }
    table.appendChild(tbody);
    tableWrap.innerHTML = "";
    tableWrap.appendChild(table);
  } catch (e) {
    tableWrap.innerHTML = `<p style="color: var(--eme-red);">${tr("msg_error")} : ${e.message}</p>`;
  }
}

// ─── Now detail ───────────────────────────────────────────────────

export async function showNowDetail(state) {
  const content = el("div");
  content.appendChild(el("h2", {}, tr("now_detail_title")));
  const body = el("div", { class: "now-dashboard" });
  body.appendChild(el("p", {}, "⏳..."));
  content.appendChild(body);
  // Indicateur d'auto-refresh
  const refreshHint = el("p", {
    style: "text-align:center; color: var(--fg-dim); font-size:0.85em; margin:8px 0;",
  }, "");
  content.appendChild(refreshHint);
  content.appendChild(closeBtn());
  openModal(content, false, false, "moontrack");

  // Premier rendu immediat
  await _renderNowDetailBody(body, state, refreshHint);

  // Auto-refresh temps reel (500 ms = 2 Hz, comme MoonSked Moon Track)
  if (_nowRefreshTimer !== null) clearInterval(_nowRefreshTimer);
  _nowRefreshTimer = setInterval(() => {
    _renderNowDetailBody(body, state, refreshHint);
  }, 500);
}

async function _renderNowDetailBody(body, state, refreshHint) {
  const freq = parseFloat($("#freq").value);
  const freqLabel = $("#freq").selectedOptions[0].textContent;
  const useLocal = $("#local-time-chk").checked;
  const tzOffset = useLocal ? utcOffsetMs() : 0;
  const tzSuffix = useLocal ? "" : " UTC";

  try {
    const locator = $("#locator").value.trim();
    const horizon = state.horizonMode === "visual" ? -0.8333 : 0;
    const elMin = parseFloat($("#el-min").value) || 0;
    const effHor = Math.max(horizon, elMin);
    const data = await apiNowDetail({
      locator, alt: state.altM, distRef: state.distRef,
      horizon: effHor, freq,
    });
    const { moon, sun, lib, deg, ha, daysSincePerigee } = data;
    const visible = moon.el > 0;
    const status = visible ? tr("now_visible") : tr("now_below");
    const statusClass = visible ? "eme-green" : "eme-red";
    const hiColor = visible ? "var(--now-visible-hi)" : "var(--now-invisible-hi)";

    const riseTxt = moon.nextRise
      ? `${formatHM(new Date(new Date(moon.nextRise).getTime() + tzOffset), false)}${tzSuffix}`
      : "---";
    const setTxt = moon.nextSet
      ? `${formatHM(new Date(new Date(moon.nextSet).getTime() + tzOffset), false)}${tzSuffix}`
      : "---";
    let durTxt = "---";
    if (moon.nextRise && moon.nextSet) {
      const durMs = Math.abs(new Date(moon.nextSet) - new Date(moon.nextRise));
      const dh = Math.floor(durMs / 3600000);
      const dm = Math.floor(durMs / 60000) % 60;
      durTxt = `${dh}h${String(dm).padStart(2, "0")}`;
    }

    // Lire lat/lon/alt de la station Home depuis l'UI (pas de state object ici)
    const homeLocator = ($("#locator").value || "").trim();
    const hAlt = parseFloat($("#altitude").value) || 0;
    let hLat = 0, hLon = 0;
    try { [hLat, hLon] = locatorToLatLon(homeLocator); } catch (e) {}

    // Spread : monostatique (Echo Width) ou bistatique (Spreading) si DX
    const dxInfo = getDxInfo();
    let spread = lib.dopplerSpreadHz * freq / 10.368e9;
    let spreadLbl = tr("now_lbl_spread");
    if (dxInfo) {
      spread = computeSpreadingBistatic(hLat, hLon, hAlt, dxInfo.lat, dxInfo.lon, 0, MakeTime(new Date()), freq);
      spreadLbl = `${tr("now_lbl_spreading")} → ${dxInfo.locator}`;
    }
    const dop = deg.dopplerHz;

    // Bloc polarisation + MNR si DX configure
    let polBlock = "";
    if (dxInfo) {
      const polH = getPolHome();
      const polOff = computePolarizationOffset(
        hLat, hLon, dxInfo.lat, dxInfo.lon, MakeTime(new Date()));
      const polD = ((polH + polOff) % 180 + 180) % 180;
      const mnr = computeMnr(polOff);
      const homeLbl = polH === 0 ? "H (0°)" : polH === 90 ? "V (90°)" : `Slant (${polH}°)`;
      const mnrCls = mnr < 3 ? "eme-green" : mnr < 10 ? "eme-orange" : "eme-red";
      polBlock = `
        <div class="group">
          <div class="group-title">${tr("now_grp_polarization")} → ${dxInfo.locator}</div>
          <div class="row">
            <div class="item"><span class="k">${tr("now_lbl_pol_home")} :</span> ${homeLbl}</div>
            <div class="item"><span class="k">${tr("now_lbl_pol_dx")} :</span> ${polD.toFixed(0)}° <span style="color:var(--fg-dim); font-size:0.85em;">(${tr("now_lbl_pol_offset")} ${polOff >= 0 ? "+" : ""}${polOff.toFixed(1)}°)</span></div>
          </div>
          <div class="row">
            <div class="item"><span class="k">${tr("now_lbl_mnr")} :</span> <span class="${mnrCls}">${mnr.toFixed(1)} dB</span> <span style="color:var(--fg-dim); font-size:0.85em; margin-left:8px;">${tr("now_lbl_mnr_hint")}</span></div>
          </div>
        </div>`;
    }

    // Heure actuelle UTC (grosse horloge centrale)
    const now = new Date();
    const hhmmss = `${String(now.getUTCHours()).padStart(2,"0")}:${String(now.getUTCMinutes()).padStart(2,"0")}:${String(now.getUTCSeconds()).padStart(2,"0")}`;

    // Phase graphique (emoji)
    const phaseEmoji = formatPhaseHTML("", moon.illumination).replace(/<[^>]*>/g, "").trim() || "●";

    // Infos DX (Az/El/Doppler bistatique/Polarity/MNR) si DX rempli
    let dxAz = 0, dxEl = 0, dxDop = 0, polOff = 0, polHomeDeg = 90, mnr = 0;
    let hasDx = false;
    let dxCallsign = "DXSTATION";
    let dxLatLbl = "0.00", dxLonLbl = "0.00";
    if (dxInfo) {
      hasDx = true;
      const t0 = MakeTime(new Date());
      const dxAzEl = computeMoonAzEl(dxInfo.lat, dxInfo.lon, 0, t0);
      dxAz = dxAzEl.az;
      dxEl = dxAzEl.el;
      dxDop = computeDopplerBistatic(hLat, hLon, hAlt, dxInfo.lat, dxInfo.lon, 0, t0, freq);
      polOff = computePolarizationOffset(hLat, hLon, dxInfo.lat, dxInfo.lon, t0);
      polHomeDeg = getPolHome();
      mnr = computeMnr(polOff);
      dxLatLbl = dxInfo.lat.toFixed(2);
      // Convention MoonSked : longitude West-positive (inverse du geographique E+)
      dxLonLbl = (-dxInfo.lon).toFixed(2);
      // Tracking rotation cumulee (unwrapped) depuis ouverture modale
      if (_polCumLast === null) {
        _polCumLast = polOff;
        _polCumTotal = polOff;
      } else {
        let delta = polOff - _polCumLast;
        if (delta > 90) delta -= 180;
        else if (delta < -90) delta += 180;
        _polCumTotal += delta;
        _polCumLast = polOff;
      }
    } else {
      _polCumLast = null;
      _polCumTotal = 0;
    }
    const polCumTotal = _polCumTotal;
    const mnrCls = mnr < 3 ? "eme-green" : mnr < 10 ? "eme-orange" : "eme-red";

    // TX/RX indicateur (convention EAST, periode 2 min : premieres 2 min TX, 2 min RX)
    const totalSec = now.getUTCMinutes() * 60 + now.getUTCSeconds();
    const periodSec = 120; // 2 min
    const isTx = Math.floor(totalSec / periodSec) % 2 === 0;
    const txRxLbl = isTx ? "TX" : "RX";
    const txRxCls = isTx ? "tx-mode" : "rx-mode";

    // Pol Home libelle
    const homePolLbl = polHomeDeg === 0 ? "H" : polHomeDeg === 90 ? "V" : `${polHomeDeg}\u00b0`;
    // TX polarity a utiliser par DX (= Home pol + offset, note -offset a appliquer coté TX MoonSked)
    const txPolDeg = ((polHomeDeg - polOff) % 180 + 180) % 180;

    // Home locator + lat/lon
    const homeLatLbl = hLat.toFixed(2);
    // Convention MoonSked : longitude West-positive (inverse du geographique E+)
    const homeLonLbl = (-hLon).toFixed(2);

    // Range DGR mini (juste le path loss extra, convention MoonSked)
    const rangeDgrMini = `(${(deg.pathLossExtraDb).toFixed(2)}dB)`;
    const rangeCls = deg.pathLossExtraDb < 1 ? "eme-green" : deg.pathLossExtraDb < 2 ? "eme-orange" : "eme-red";

    // Date courte localisee
    const dateLbl = locDate(now) + " " + now.getFullYear();

    body.innerHTML = `
      <div class="mt-grid">

        <div class="mt-box mt-range">
          <div class="mt-title">Range</div>
          <div class="mt-range-val">${Math.round(moon.distKm).toLocaleString("fr-FR")} Km</div>
          <div class="mt-range-dgr">${rangeDgrMini}</div>
          <div class="mt-range-bar ${rangeCls}"></div>
        </div>

        <div class="mt-box mt-dgr">
          <div>Total DGR <b>${deg.degradationDb >= 0 ? "+" : ""}${deg.degradationDb.toFixed(2)} dB</b></div>
          <div>Sky Temp <b>${deg.skyTempK.toFixed(1)} K</b></div>
          <div style="margin-top:4px;">${hasDx ? tr("now_lbl_spreading") : tr("now_lbl_spread")}
            <b class="${spread < 50 ? "eme-green" : spread < 150 ? "eme-orange" : "eme-red"}">${Math.round(spread)} Hz</b></div>
        </div>

        <div class="mt-box mt-geo">
          <div class="mt-title">Geocentric</div>
          <div>GHA <b>${ha.ghaDeg.toFixed(1)}°</b></div>
          <div>Decl <b>${ha.decDeg >= 0 ? "+" : ""}${ha.decDeg.toFixed(1)}°</b></div>
          <div class="mt-phase">${phaseEmoji}</div>
        </div>

        <div class="mt-perigee">
          <span>${daysSincePerigee.toFixed(0)} ${tr("now_lbl_days_since_perigee")}</span>
          <span style="margin-left:20px; color: var(--fg-dim);">${dateLbl}</span>
        </div>

        <div class="mt-box mt-home">
          <div class="mt-title">Home</div>
          <div><b>${(locator || "---").toUpperCase()}</b></div>
          <div>Lat <b>${homeLatLbl}</b></div>
          <div>Lon <b>${homeLonLbl}</b></div>
        </div>

        <div class="mt-box mt-utc">
          <div class="mt-title">UTC</div>
          <div class="mt-clock">${hhmmss}</div>
        </div>

        <div class="mt-box mt-dx-info">
          <div class="mt-title">DX</div>
          <div><b style="color: var(--link-color);">${hasDx ? dxInfo.locator : "—"}</b></div>
          ${hasDx ? `<div>Lat <b>${dxLatLbl}</b></div><div>Lon <b>${dxLonLbl}</b></div>` : `<div style="color: var(--fg-dim); font-size:0.85em;">${tr("now_hint_enter_dx")}</div>`}
        </div>

        <div class="mt-dx-row">
          <span class="mt-title-inline">DX</span>
          ${hasDx ? `
            <span>Azimuth <b>${dxAz.toFixed(2)}°</b></span>
            <span>Elevation <b>${dxEl >= 0 ? "+" : ""}${dxEl.toFixed(2)}°</b></span>
            <span>${Math.round(freq/1e6)}MHz Doppler <b>${dxDop >= 0 ? "+" : ""}${Math.round(dxDop)}Hz</b></span>
            <span>Polarity <b>${polOff >= 0 ? "+" : ""}${polOff.toFixed(0)}°</b></span>
            <span>MNR <b class="${mnrCls}">${mnr.toFixed(0)}dB</b></span>
          ` : `<span style="color: var(--fg-dim);">${tr("now_hint_enter_dx")}</span>`}
        </div>

        <div class="mt-box mt-az">
          <div class="mt-title">Azimuth</div>
          <div class="mt-big">${moon.az.toFixed(2)}°</div>
        </div>

        <div class="mt-txrx">
          <div class="mt-txrx-top">EAST &nbsp; 2 Mins</div>
          <div class="mt-txrx-mode ${txRxCls}">${txRxLbl}</div>
          <div>Home Echo</div>
          <div class="mt-txrx-echo">${dop >= 0 ? "+" : ""}${Math.round(dop)}Hz</div>
        </div>

        <div class="mt-box mt-el">
          <div class="mt-title">Elevation</div>
          <div class="mt-big ${visible ? "eme-green" : "eme-red"}">${moon.el >= 0 ? "+" : ""}${moon.el.toFixed(2)}°</div>
        </div>

        <div class="mt-box mt-topo">
          <div class="mt-title">Topocentric</div>
          <div>LHA <b>${ha.lhaDeg.toFixed(2)}°</b></div>
          <div>GHA <b>${ha.ghaDeg.toFixed(2)}°</b></div>
          <div>Decl <b>${ha.decDeg >= 0 ? "+" : ""}${ha.decDeg.toFixed(2)}°</b></div>
        </div>

        <div class="mt-box mt-rxpol" id="mt-rxpol-box">
          <div class="mt-title">RX Polarisation</div>
          <!-- Contenu injecte une seule fois (voir wiring ci-dessous) -->
        </div>

        <div class="mt-box mt-txpol" title="${tr('tip_tx_pol_box').replace(/"/g, '&quot;')}">
          <div class="mt-title">TX Polarisation</div>
          ${hasDx ? `
            <div><b>${homePolLbl}</b></div>
            <div title="${tr('tip_tx_pol_inst').replace(/"/g, '&quot;')}">Δ ${polOff >= 0 ? "+" : ""}${polOff.toFixed(0)}°</div>
            <div style="color: var(--fg-dim); font-size: 0.85em;" title="${tr('tip_tx_pol_cum').replace(/"/g, '&quot;')}">Σ ${polCumTotal >= 0 ? "+" : ""}${polCumTotal.toFixed(0)}°</div>
          ` : `<div style="color: var(--fg-dim);">—</div>`}
        </div>

      </div>
    `;

    // RX Polarisation : creer les radios UNE SEULE FOIS, puis sync leur etat
    // a chaque refresh SAUF si l'utilisateur interagit (focus sur input num).
    const rxBox = body.querySelector("#mt-rxpol-box");
    if (rxBox && !rxBox.dataset.built) {
      rxBox.dataset.built = "1";
      const controls = document.createElement("div");
      controls.innerHTML = `
        <label style="display:inline-block; margin-right:6px;">
          <input type="radio" name="mt-rxpol" value="0"> H</label>
        <label style="display:inline-block; margin-right:6px;">
          <input type="radio" name="mt-rxpol" value="90"> V</label>
        <div>
          <label><input type="radio" name="mt-rxpol" value="deg"> Degrees</label>
          <input type="number" id="mt-rxpol-deg" min="0" max="180" value="${polHomeDeg}" style="width:50px;">
        </div>`;
      rxBox.appendChild(controls);
      const mtRxDeg = rxBox.querySelector("#mt-rxpol-deg");
      rxBox.querySelectorAll('input[name="mt-rxpol"]').forEach(r => {
        r.addEventListener("change", () => {
          if (r.value === "0") $("#pol-home").value = "0";
          else if (r.value === "90") $("#pol-home").value = "90";
          else if (r.value === "deg" && mtRxDeg) $("#pol-home").value = mtRxDeg.value;
          $("#pol-home").dispatchEvent(new Event("change"));
        });
      });
      if (mtRxDeg) {
        mtRxDeg.addEventListener("input", () => {
          // Quand utilisateur tape : passer en mode Degrees + propager
          const degRadio = rxBox.querySelector('input[value="deg"]');
          if (degRadio) degRadio.checked = true;
          $("#pol-home").value = mtRxDeg.value;
          $("#pol-home").dispatchEvent(new Event("change"));
        });
      }
    }
    // Sync l'etat visuel des radios avec polHomeDeg, mais eviter d'ecraser
    // l'input numerique si l'utilisateur est en train de taper dedans.
    if (rxBox) {
      const hRadio = rxBox.querySelector('input[value="0"]');
      const vRadio = rxBox.querySelector('input[value="90"]');
      const dRadio = rxBox.querySelector('input[value="deg"]');
      const degInput = rxBox.querySelector("#mt-rxpol-deg");
      if (hRadio) hRadio.checked = (polHomeDeg === 0);
      if (vRadio) vRadio.checked = (polHomeDeg === 90);
      if (dRadio) dRadio.checked = (polHomeDeg !== 0 && polHomeDeg !== 90);
      // Ne pas ecraser la valeur saisie si le champ est focus
      if (degInput && document.activeElement !== degInput) {
        degInput.value = polHomeDeg;
      }
    }
    if (refreshHint) {
      refreshHint.textContent = tr("refresh_hint");
    }
  } catch (e) {
    body.innerHTML = `<p style="color: var(--eme-red);">${tr("msg_error")} : ${e.message}</p>`;
  }
}
