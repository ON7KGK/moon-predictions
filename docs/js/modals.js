// ════════════════════════════════════════════════════════════════════
// Modales : Conventions, Help, About, DayDetail, NowDetail
// ════════════════════════════════════════════════════════════════════

import { tr, locDate, locDateLong } from "./i18n.js";
import { $, el, utcOffsetMs, formatHM, formatTz, emeColor, EL_GREEN, EL_ORANGE,
  DIST_GREEN, DIST_ORANGE } from "./utils.js";
import { apiPassTimeline, apiNowDetail, apiLocator } from "./api.js";

const APP_VERSION = "1.8.2";
const APP_DATE = "2026-04-16";

// ─── Helpers ──────────────────────────────────────────────────────

function openModal(contentNode, wide = false, narrow = false) {
  const overlay = $("#modal-overlay");
  const content = $("#modal-content");
  content.className = `modal-content${wide ? " wide" : ""}${narrow ? " narrow" : ""}`;
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

export function closeModal() {
  $("#modal-overlay").classList.add("hidden");
  if (_nowRefreshTimer !== null) {
    clearInterval(_nowRefreshTimer);
    _nowRefreshTimer = null;
  }
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
  openModal(content);

  // Premier rendu immediat
  await _renderNowDetailBody(body, state, refreshHint);

  // Auto-refresh toutes les 5 secondes
  if (_nowRefreshTimer !== null) clearInterval(_nowRefreshTimer);
  _nowRefreshTimer = setInterval(() => {
    _renderNowDetailBody(body, state, refreshHint);
  }, 5000);
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

    const spread = lib.dopplerSpreadHz * freq / 10.368e9;
    const dop = deg.dopplerHz;

    // Heure actuelle (pour montrer la mise a jour)
    const now = new Date();
    const nowTxt = useLocal
      ? `${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")} ${formatTz()}`
      : `${String(now.getUTCHours()).padStart(2,"0")}:${String(now.getUTCMinutes()).padStart(2,"0")}:${String(now.getUTCSeconds()).padStart(2,"0")} UTC`;

    body.innerHTML = `
      <div class="status" style="color: ${hiColor};">
        ● ${tr(visible ? "now_label" : "now_label_off").replace(/^[●○]\s*/, "")}
        <span class="${statusClass}">${status}</span>
        <span style="font-size:0.75em; color: var(--fg-dim); font-weight: normal; margin-left:12px;">${nowTxt}</span>
      </div>

      <div class="group">
        <div class="group-title">${tr("now_grp_position")}</div>
        <div class="row">
          <div class="item"><span class="k">AZ :</span> <span class="big">${moon.az.toFixed(1)}°</span></div>
          <div class="item"><span class="k">EL :</span> <span class="big ${statusClass}">${moon.el >= 0 ? "+" : ""}${moon.el.toFixed(1)}°</span></div>
          <div class="item"><span class="k">${tr("now_lbl_distance")} :</span> ${Math.round(moon.distKm)} km</div>
          <div class="item"><span class="k">${tr("now_lbl_decl")} :</span> ${ha.decDeg >= 0 ? "+" : ""}${ha.decDeg.toFixed(2)}°</div>
        </div>
        <div class="row">
          <div class="item"><span class="k">${tr("now_lbl_phase")} :</span> ${tr(moon.phaseName)} (${Math.round(moon.illumination)}%)</div>
        </div>
      </div>

      <div class="group">
        <div class="group-title">${tr("now_grp_riseset")}</div>
        <div class="row">
          <div class="item"><span class="k">${tr("col_rise")} :</span> ${riseTxt}</div>
          <div class="item"><span class="k">${tr("col_set")} :</span> ${setTxt}</div>
          <div class="item"><span class="k">${tr("col_duration")} :</span> ${durTxt}</div>
        </div>
      </div>

      <div class="group">
        <div class="group-title">${tr("now_grp_eme")} (${freqLabel})</div>
        <div class="row">
          <div class="item"><span class="k">${tr("now_lbl_dgr")} :</span> <span class="${deg.degradationDb < 1 ? "eme-green" : deg.degradationDb < 3 ? "eme-orange" : "eme-red"}">${deg.degradationDb >= 0 ? "+" : ""}${deg.degradationDb.toFixed(2)} dB</span></div>
          <div class="item"><span class="k">${tr("now_lbl_tsky")} :</span> <span class="${deg.skyTempK < 10 ? "eme-green" : deg.skyTempK < 50 ? "eme-orange" : "eme-red"}">${deg.skyTempK.toFixed(1)} K</span></div>
          <div class="item"><span class="k">${tr("now_lbl_doppler")} :</span> ${dop >= 0 ? "+" : ""}${Math.round(dop)} Hz</div>
          <div class="item"><span class="k">${tr("now_lbl_echo")} :</span> ${dop >= 0 ? "+" : ""}${Math.round(dop)} Hz</div>
        </div>
        <div class="row">
          <div class="item"><span class="k">${tr("now_lbl_spread")} :</span> <span class="${spread < 50 ? "eme-green" : spread < 150 ? "eme-orange" : "eme-red"}">${Math.round(spread)} Hz</span></div>
          <div class="item"><span class="k">${tr("now_lbl_libration")} :</span> <span class="${lib.libRate < 0.10 ? "eme-green" : lib.libRate < 0.25 ? "eme-orange" : "eme-red"}">${lib.libRate.toFixed(2)}°/h</span></div>
          <div class="item"><span class="k">${tr("now_lbl_pl_extra")} :</span> <span class="${deg.pathLossExtraDb < 1 ? "eme-green" : deg.pathLossExtraDb < 2 ? "eme-orange" : "eme-red"}">${deg.pathLossExtraDb >= 0 ? "+" : ""}${deg.pathLossExtraDb.toFixed(2)} dB</span></div>
        </div>
      </div>

      <div class="group">
        <div class="group-title">${tr("now_grp_astro")}</div>
        <div class="row">
          <div class="item"><span class="k">${tr("now_lbl_lha")} :</span> ${ha.lhaDeg >= 0 ? "+" : ""}${ha.lhaDeg.toFixed(2)}°</div>
          <div class="item"><span class="k">${tr("now_lbl_gha")} :</span> ${ha.ghaDeg.toFixed(2)}°</div>
          <div class="item"><span class="k">${tr("now_lbl_dsp")} :</span> ${daysSincePerigee.toFixed(1)} ${tr("now_lbl_days")}</div>
        </div>
      </div>
    `;
    if (refreshHint) {
      refreshHint.textContent = tr("refresh_hint");
    }
  } catch (e) {
    body.innerHTML = `<p style="color: var(--eme-red);">${tr("msg_error")} : ${e.message}</p>`;
  }
}
