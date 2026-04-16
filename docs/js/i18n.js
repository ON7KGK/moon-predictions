// ════════════════════════════════════════════════════════════════════
// i18n — chargement FR / NL / EN depuis /texts/*.json
// ════════════════════════════════════════════════════════════════════

let _strings = {};
let _lang = "fr";

export async function loadLanguage(lang) {
  if (!["fr", "nl", "en"].includes(lang)) lang = "fr";
  _lang = lang;
  try {
    const resp = await fetch(`/texts/${lang}.json`, { cache: "no-cache" });
    _strings = await resp.json();
  } catch (e) {
    console.error("Loading language failed:", e);
    _strings = {};
  }
  document.documentElement.lang = lang;
  applyToDom();
}

export function tr(key, params = {}) {
  let text = _strings[key] || key;
  for (const [k, v] of Object.entries(params)) {
    text = text.replaceAll(`{${k}}`, v);
  }
  return text;
}

export function getLang() { return _lang; }

// Applique tous les data-i18n du DOM
export function applyToDom() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    el.textContent = tr(key);
  });
  // Tooltips via data-tip
  document.querySelectorAll("[data-tip]").forEach(el => {
    const key = el.getAttribute("data-tip");
    const txt = tr(key);
    if (txt && txt !== key) el.setAttribute("title", txt);
  });
}

// Dates localisées
export function locDate(dt) {
  const d = new Date(dt);
  const day = tr(`day_${d.getDay() === 0 ? 6 : d.getDay() - 1}`);
  const mon = tr(`mon_${d.getMonth() + 1}`);
  return `${day} ${String(d.getDate()).padStart(2, "0")} ${mon}`;
}

export function locDateLong(dt) {
  const d = new Date(dt);
  const day = tr(`day_${d.getDay() === 0 ? 6 : d.getDay() - 1}`);
  const mon = tr(`mon_${d.getMonth() + 1}`);
  return `${day} ${String(d.getDate()).padStart(2, "0")} ${mon} ${d.getFullYear()}`;
}
