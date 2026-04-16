// ════════════════════════════════════════════════════════════════════
// API wrapper — fetch vers /api/*
// ════════════════════════════════════════════════════════════════════

async function getJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error((await r.json()).error || r.statusText);
  return r.json();
}

async function postJson(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error((await r.json()).error || r.statusText);
  return r.json();
}

export async function apiLocator(locator) {
  return getJson(`/api/locator?locator=${encodeURIComponent(locator)}`);
}

export async function apiPasses(params) {
  const q = new URLSearchParams(params).toString();
  return getJson(`/api/passes?${q}`);
}

export async function apiNowDetail(params) {
  const q = new URLSearchParams(params).toString();
  return getJson(`/api/now-detail?${q}`);
}

export async function apiMoon(params) {
  const q = new URLSearchParams(params).toString();
  return getJson(`/api/moon?${q}`);
}

export async function apiPassTimeline(body) {
  return postJson("/api/pass-timeline", body);
}
