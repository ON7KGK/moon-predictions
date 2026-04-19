// ════════════════════════════════════════════════════════════════════
// Moon Predictions Web — Calculs Lune/Soleil pour EME
// Port des fonctions de moon_calc.py vers astronomy-engine (JavaScript).
// Precision : ~10 m sur la Lune (vs sub-km pour JPL DE440s, suffisant EME).
// ════════════════════════════════════════════════════════════════════

// astronomy-engine via CDN ESM (pas de build step necessaire pour GH Pages)
// En cas de besoin de fonctionnement offline : copier le .js dans vendor/
// et changer l'URL par "./vendor/astronomy-engine.js"
import {
  Body,
  Observer,
  Equator,
  Horizon,
  SearchRiseSet,
  MoonPhase,
  Illumination,
  AstroTime,
  MakeTime,
  GeoMoon,
  SiderealTime,
} from "https://esm.sh/astronomy-engine@2.1.19";

const C_LIGHT = 299_792_458;
const T_CMB = 2.73;
const T_MOON = 230.0;
const R_MOON_KM = 1737.4;

// ─── Conversion Maidenhead locator → lat/lon ──────────────────────

export function locatorToLatLon(locator) {
  const loc = (locator || "").trim();
  const length = loc.length;
  if (![4, 6, 8].includes(length)) {
    throw new Error(`Locator doit faire 4, 6 ou 8 caracteres: '${loc}'`);
  }
  const L = loc[0].toUpperCase() + loc[1].toUpperCase() + loc.slice(2);
  const a = L.charCodeAt(0), b = L.charCodeAt(1);
  const A = "A".charCodeAt(0), R = "R".charCodeAt(0);
  if (a < A || a > R || b < A || b > R) {
    throw new Error(`Champ invalide: '${L.slice(0, 2)}'`);
  }
  let lon = (a - A) * 20 - 180;
  let lat = (b - A) * 10 - 90;
  const d2 = L[2], d3 = L[3];
  if (!/\d/.test(d2) || !/\d/.test(d3)) {
    throw new Error(`Carre invalide: '${L.slice(2, 4)}'`);
  }
  lon += parseInt(d2) * 2;
  lat += parseInt(d3) * 1;
  if (length === 4) return [lat + 0.5, lon + 1.0];

  const s4 = L[4].toLowerCase().charCodeAt(0);
  const s5 = L[5].toLowerCase().charCodeAt(0);
  const aa = "a".charCodeAt(0), xx = "x".charCodeAt(0);
  if (s4 < aa || s4 > xx || s5 < aa || s5 > xx) {
    throw new Error(`Sous-carre invalide: '${L.slice(4, 6)}'`);
  }
  lon += (s4 - aa) * (2 / 24);
  lat += (s5 - aa) * (1 / 24);
  if (length === 6) return [lat + 1 / 48, lon + 1 / 24];

  const d6 = L[6], d7 = L[7];
  if (!/\d/.test(d6) || !/\d/.test(d7)) {
    throw new Error(`Carre etendu invalide: '${L.slice(6, 8)}'`);
  }
  lon += parseInt(d6) * (2 / 240);
  lat += parseInt(d7) * (1 / 240);
  return [lat + 1 / 480, lon + 1 / 240];
}

// ─── Helpers ──────────────────────────────────────────────────────

function dateToAstro(date) {
  return MakeTime(date instanceof Date ? date : new Date(date));
}

function angularSepDeg(az1, el1, az2, el2) {
  const r = Math.PI / 180;
  const cs = Math.sin(el1 * r) * Math.sin(el2 * r)
    + Math.cos(el1 * r) * Math.cos(el2 * r) * Math.cos((az1 - az2) * r);
  return Math.acos(Math.max(-1, Math.min(1, cs))) * 180 / Math.PI;
}

function phaseName(phaseDeg, illumPct, short = false) {
  // Noms de phase (clefs i18n) — le front traduit
  if (illumPct < 2) return short ? "phase_s_new" : "phase_new";
  if (illumPct > 98) return short ? "phase_s_full" : "phase_full";
  if (illumPct > 48 && illumPct < 52) {
    return phaseDeg < 180
      ? (short ? "phase_s_fq" : "phase_fq")
      : (short ? "phase_s_lq" : "phase_lq");
  }
  if (phaseDeg < 90) return short ? "phase_s_wax_cres" : "phase_wax_cres";
  if (phaseDeg < 180) return short ? "phase_s_wax_gibb" : "phase_wax_gibb";
  if (phaseDeg < 270) return short ? "phase_s_wan_gibb" : "phase_wan_gibb";
  return short ? "phase_s_wan_cres" : "phase_wan_cres";
}

// ─── Position de la Lune / Soleil ─────────────────────────────────

function moonAltAzDist(observer, t) {
  // topocentrique (observer = lat/lon/alt)
  const eq = Equator(Body.Moon, t, observer, true, true);
  const hor = Horizon(t, observer, eq.ra, eq.dec, "normal");
  // distance : Equator retourne dist en AU (topocentric)
  return {
    az: hor.azimuth,
    el: hor.altitude,
    distKm: eq.dist * 149_597_870.7,
    ra: eq.ra,
    dec: eq.dec,
  };
}

function geoMoonDistKm(t) {
  // Distance geocentrique
  const v = GeoMoon(t);
  const au = Math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
  return au * 149_597_870.7;
}

function sunAltAz(observer, t) {
  const eq = Equator(Body.Sun, t, observer, true, true);
  const hor = Horizon(t, observer, eq.ra, eq.dec, "normal");
  return { az: hor.azimuth, el: hor.altitude };
}

// ─── Lever / coucher ──────────────────────────────────────────────

function nextRiseSet(body, observer, tStart, days = 2, horizonDeg = 0) {
  // SearchRiseSet : direction +1 = rise, -1 = set
  let nextRise = null, nextSet = null;
  try {
    const rise = SearchRiseSet(body, observer, +1, tStart, days, horizonDeg);
    if (rise) nextRise = rise.date;
  } catch (e) {}
  try {
    const set = SearchRiseSet(body, observer, -1, tStart, days, horizonDeg);
    if (set) nextSet = set.date;
  } catch (e) {}
  return { nextRise, nextSet };
}

// ─── compute_moon ─────────────────────────────────────────────────

export function computeMoon(lat, lon, altM = 0,
    distReference = "topo", horizonDegrees = 0.0) {
  const observer = new Observer(lat, lon, altM);
  const t = MakeTime(new Date());
  const { az, el } = moonAltAzDist(observer, t);

  const distKm = distReference === "geo"
    ? geoMoonDistKm(t)
    : moonAltAzDist(observer, t).distKm;

  const illumObj = Illumination(Body.Moon, t);
  const illum = illumObj.phase_fraction * 100;
  const phaseDeg = MoonPhase(t);

  const { nextRise, nextSet } = nextRiseSet(
    Body.Moon, observer, t, 2, horizonDegrees);

  return {
    az: Math.round(az * 10) / 10,
    el: Math.round(el * 10) / 10,
    distKm: Math.round(distKm),
    illumination: Math.round(illum * 10) / 10,
    phaseName: phaseName(phaseDeg, illum),
    nextRise: nextRise ? nextRise.toISOString() : null,
    nextSet: nextSet ? nextSet.toISOString() : null,
  };
}

export function computeSun(lat, lon, altM = 0, horizonDegrees = 0) {
  const observer = new Observer(lat, lon, altM);
  const t = MakeTime(new Date());
  const { az, el } = sunAltAz(observer, t);
  const { nextRise, nextSet } = nextRiseSet(
    Body.Sun, observer, t, 2, horizonDegrees);
  return {
    az: Math.round(az * 10) / 10,
    el: Math.round(el * 10) / 10,
    nextRise: nextRise ? nextRise.toISOString() : null,
    nextSet: nextSet ? nextSet.toISOString() : null,
  };
}

// ─── Libration & Doppler spread ───────────────────────────────────

// Libration selenographique TOPOCENTRIQUE — formules IAU 2009.
// Equivalent de _libration_at() dans moon_calc.py.
// Inclut la libration diurne (rotation terrestre), essentielle pour le
// calcul du Doppler spread EME depuis un observateur a latitude non nulle.
function librationAt(observer, t) {
  // Position apparente topocentrique de la Lune
  const eq = Equator(Body.Moon, t, observer, true, true);
  // RA/Dec + distance -> vecteur cartesien ICRS
  const raRad = eq.ra * Math.PI / 12; // ra est en heures
  const decRad = eq.dec * Math.PI / 180;
  const d = eq.dist; // AU
  const pos = [
    d * Math.cos(decRad) * Math.cos(raRad),
    d * Math.cos(decRad) * Math.sin(raRad),
    d * Math.sin(decRad),
  ];
  const norm = Math.hypot(pos[0], pos[1], pos[2]);
  const posUnit = [pos[0] / norm, pos[1] / norm, pos[2] / norm];

  // IAU 2009 : pole Nord lunaire + rotation propre
  // t.tt = jours TT depuis J2000. T en siecles juliens.
  const T = t.tt / 36525.0;
  const dd = t.tt;
  const raPole = (269.9949 + 0.0031 * T) * Math.PI / 180;
  const decPole = (66.5392 + 0.0130 * T) * Math.PI / 180;
  let W = (38.3213 + 13.17635815 * dd) % 360;
  if (W < 0) W += 360;
  const Wrad = W * Math.PI / 180;

  // Repere selenographique en ICRF
  const cosDp = Math.cos(decPole);
  const zSel = [
    cosDp * Math.cos(raPole),
    cosDp * Math.sin(raPole),
    Math.sin(decPole),
  ];
  const n = [-Math.sin(raPole), Math.cos(raPole), 0];
  // e = zSel x n
  const e = [
    zSel[1] * n[2] - zSel[2] * n[1],
    zSel[2] * n[0] - zSel[0] * n[2],
    zSel[0] * n[1] - zSel[1] * n[0],
  ];
  const eNorm = Math.hypot(e[0], e[1], e[2]);
  const eU = [e[0] / eNorm, e[1] / eNorm, e[2] / eNorm];
  const cW = Math.cos(Wrad), sW = Math.sin(Wrad);
  const xSel = [
    n[0] * cW + eU[0] * sW,
    n[1] * cW + eU[1] * sW,
    n[2] * cW + eU[2] * sW,
  ];
  // ySel = zSel x xSel
  const ySel = [
    zSel[1] * xSel[2] - zSel[2] * xSel[1],
    zSel[2] * xSel[0] - zSel[0] * xSel[2],
    zSel[0] * xSel[1] - zSel[1] * xSel[0],
  ];

  // Projections
  const px = posUnit[0] * xSel[0] + posUnit[1] * xSel[1] + posUnit[2] * xSel[2];
  const py = posUnit[0] * ySel[0] + posUnit[1] * ySel[1] + posUnit[2] * ySel[2];
  const pz = posUnit[0] * zSel[0] + posUnit[1] * zSel[1] + posUnit[2] * zSel[2];

  const libLat = Math.asin(Math.max(-1, Math.min(1, pz))) * 180 / Math.PI;
  const libLon = Math.atan2(py, px) * 180 / Math.PI;
  return { lon: libLon, lat: libLat };
}

export function computeLibration(lat, lon, altM, t) {
  const observer = new Observer(lat, lon, altM);
  const t0 = t instanceof AstroTime ? t : MakeTime(t);
  const { lon: l0, lat: b0 } = librationAt(observer, t0);
  // Derivee numerique centree sur +-30 min (total 1h)
  const dtDays = 0.5 / 24;
  const tm = t0.AddDays(-dtDays);
  const tp = t0.AddDays(+dtDays);
  const { lon: l1, lat: b1 } = librationAt(observer, tm);
  const { lon: l2, lat: b2 } = librationAt(observer, tp);
  let dlon = l2 - l1;
  if (dlon > 180) dlon -= 360;
  if (dlon < -180) dlon += 360;
  const dlat = b2 - b1;
  const libRate = Math.sqrt(dlon * dlon + dlat * dlat); // deg/h
  // Doppler spread a 10.368 GHz (EME monostatique = facteur 4)
  // B_D = 4 * omega * R_moon * f / c  (Cole KL7UW, W5ZN, NK6K)
  const vTan = libRate * R_MOON_KM * Math.PI / 180 * 1000 / 3600;
  const spread = 4 * vTan * 10.368e9 / C_LIGHT;
  return {
    libLon: Math.round(l0 * 100) / 100,
    libLat: Math.round(b0 * 100) / 100,
    libRate: Math.round(libRate * 10000) / 10000,
    dopplerSpreadHz: Math.round(spread),
  };
}

// Taux de libration |omega| en deg/h vu d'un observateur donne
function librationRateAt(observer, t) {
  const dtDays = 0.5 / 24;
  const tm = t.AddDays(-dtDays);
  const tp = t.AddDays(+dtDays);
  const { lon: l1, lat: b1 } = librationAt(observer, tm);
  const { lon: l2, lat: b2 } = librationAt(observer, tp);
  let dlon = l2 - l1;
  if (dlon > 180) dlon -= 360;
  if (dlon < -180) dlon += 360;
  const dlat = b2 - b1;
  return Math.sqrt(dlon * dlon + dlat * dlat);
}

// Spreading Doppler bistatique Home -> Lune -> DX en Hz
// Formule : 2 * f * (v_home + v_dx) * R_moon / c
// Se reduit a l'Echo Width monostatique quand DX = Home.
export function computeSpreadingBistatic(latH, lonH, altH, latD, lonD, altD, t,
    freqHz = 10368e6) {
  const obsH = new Observer(latH, lonH, altH);
  const obsD = new Observer(latD, lonD, altD);
  const t0 = t instanceof AstroTime ? t : MakeTime(t);
  const rateH = librationRateAt(obsH, t0);
  const rateD = librationRateAt(obsD, t0);
  const vH = rateH * R_MOON_KM * Math.PI / 180 * 1000 / 3600;
  const vD = rateD * R_MOON_KM * Math.PI / 180 * 1000 / 3600;
  return 2 * freqHz * (vH + vD) / C_LIGHT;
}

// ─── Polarisation spatiale & MNR ─────────────────────────────────
// Formule Hustig/Pettis KL7WE, via manuel MoonSked Appendix 1.

function polHustig(latDeg, azDeg, elDeg) {
  const L = latDeg * Math.PI / 180;
  const A = azDeg * Math.PI / 180;
  const E = elDeg * Math.PI / 180;
  const num = Math.sin(L) * Math.cos(E) - Math.cos(L) * Math.cos(A) * Math.sin(E);
  const den = Math.cos(L) * Math.sin(A);
  return Math.atan2(num, den) * 180 / Math.PI;
}

export function computePolarizationOffset(latH, lonH, latD, lonD, t) {
  const t0 = t instanceof AstroTime ? t : MakeTime(t);
  const obsH = new Observer(latH, lonH, 0);
  const obsD = new Observer(latD, lonD, 0);
  const { az: azH, el: elH } = moonAltAzDist(obsH, t0);
  const { az: azD, el: elD } = moonAltAzDist(obsD, t0);
  const pH = polHustig(latH, azH, elH);
  const pD = polHustig(latD, azD, elD);
  let off = pH - pD;
  while (off > 90) off -= 180;
  while (off < -90) off += 180;
  return off;
}

// MNR = Maximum Non-Reciprocity (N1BUG Z-TRACK / MoonSked Appendix 1)
// Pire cas de non-reciprocite EME pour un offset spatial donne.
export function computeMnr(offsetDeg) {
  const cos2 = Math.abs(Math.cos(2 * offsetDeg * Math.PI / 180));
  if (cos2 < 1e-3) return 25.0;
  return Math.min(-20 * Math.log10(cos2), 25.0);
}

// ─── Doppler shift (central, aller-retour) ────────────────────────

export function computeDopplerShift(lat, lon, altM, t, freqHz = 10368e6) {
  const observer = new Observer(lat, lon, altM);
  const t0 = t instanceof AstroTime ? t : MakeTime(t);
  const dtSec = 30;
  const dtDays = dtSec / 86400;
  const tm = t0.AddDays(-dtDays);
  const tp = t0.AddDays(+dtDays);
  const d1 = moonAltAzDist(observer, tm).distKm * 1000; // m
  const d2 = moonAltAzDist(observer, tp).distKm * 1000;
  const vRadial = (d2 - d1) / (2 * dtSec); // m/s (+ = eloigne)
  return -2.0 * vRadial * freqHz / C_LIGHT;
}

// Doppler bistatique Home TX -> Lune -> DX RX (un-sens total).
// Formule : -(v_home_los + v_dx_los) * f / c
export function computeDopplerBistatic(latH, lonH, altH, latD, lonD, altD,
    t, freqHz = 10368e6) {
  const dopH = computeDopplerShift(latH, lonH, altH, t, freqHz); // = -2 v_h f/c
  const dopD = computeDopplerShift(latD, lonD, altD, t, freqHz); // = -2 v_d f/c
  return (dopH + dopD) / 2.0;
}

// Az/El topocentrique Lune vue d'un observateur (pour DX).
export function computeMoonAzEl(lat, lon, altM, t) {
  const observer = new Observer(lat, lon, altM);
  const t0 = t instanceof AstroTime ? t : MakeTime(t);
  const { az, el, distKm } = moonAltAzDist(observer, t0);
  return { az, el, distKm };
}

// ─── Conversions galactiques (pour TSky) ──────────────────────────

const R_GAL_TO_ICRS = [
  [-0.0548755604, -0.8734370902, -0.4838350155],
  [0.4941094279, -0.4448296300, 0.7469822445],
  [-0.8676661490, -0.1980763734, 0.4559837762],
];

function radecToGalactic(raDeg, decDeg) {
  const r = Math.PI / 180;
  const ra = raDeg * r, dec = decDeg * r;
  const eq = [Math.cos(dec) * Math.cos(ra), Math.cos(dec) * Math.sin(ra),
    Math.sin(dec)];
  // Transpose de R_GAL_TO_ICRS
  const gal = [
    R_GAL_TO_ICRS[0][0] * eq[0] + R_GAL_TO_ICRS[1][0] * eq[1] + R_GAL_TO_ICRS[2][0] * eq[2],
    R_GAL_TO_ICRS[0][1] * eq[0] + R_GAL_TO_ICRS[1][1] * eq[1] + R_GAL_TO_ICRS[2][1] * eq[2],
    R_GAL_TO_ICRS[0][2] * eq[0] + R_GAL_TO_ICRS[1][2] * eq[1] + R_GAL_TO_ICRS[2][2] * eq[2],
  ];
  const l = ((Math.atan2(gal[1], gal[0]) * 180 / Math.PI) + 360) % 360;
  const b = Math.asin(Math.max(-1, Math.min(1, gal[2]))) * 180 / Math.PI;
  return { l, b };
}

export function computeSkyTemp(lat, lon, altM, t, freqHz = 10368e6) {
  const observer = new Observer(lat, lon, altM);
  const t0 = t instanceof AstroTime ? t : MakeTime(t);
  const eq = Equator(Body.Moon, t0, observer, true, true);
  const raDeg = eq.ra * 15; // RA is in hours
  const decDeg = eq.dec;
  const { l, b } = radecToGalactic(raDeg, decDeg);
  // Modele simplifie Haslam 408 MHz
  const absB = Math.abs(b);
  let tGal408 = 20 + 180 * Math.exp(-absB / 12);
  // Bosse centre galactique
  const lCentered = l <= 180 ? l : l - 360;
  if (absB < 15 && Math.abs(lCentered) < 30) {
    tGal408 += 400 * Math.exp(
      -(lCentered * lCentered) / 400 - (b * b) / 50);
  }
  // Extrapolation spectrale
  const tGal = tGal408 * Math.pow(408e6 / freqHz, 2.5);
  return T_CMB + tGal;
}

export function computeDegradation(lat, lon, altM, t,
    freqHz = 10368e6, tSysK = 50.0) {
  const observer = new Observer(lat, lon, altM);
  const t0 = t instanceof AstroTime ? t : MakeTime(t);
  const { distKm } = moonAltAzDist(observer, t0);
  // Path loss extra vs perigee : distance GEOCENTRIQUE (convention MoonSked,
  // perigee 356500 km defini Terre-centre -> Lune-centre). Facteur 40 = d^4 aller-retour.
  const distGeoKm = geoMoonDistKm(t0);
  const plExtra = distGeoKm > 0 ? 40 * Math.log10(distGeoKm / 356500) : 0;
  const tSky = computeSkyTemp(lat, lon, altM, t0, freqHz);
  const tRef = tSysK + T_CMB + T_MOON;
  const tNow = tSysK + tSky + T_MOON;
  const noiseDb = 10 * Math.log10(tNow / tRef);
  const degDb = plExtra + noiseDb;
  const dopHz = computeDopplerShift(lat, lon, altM, t0, freqHz);
  return {
    degradationDb: degDb,
    pathLossExtraDb: plExtra,
    skyTempK: tSky,
    dopplerHz: dopHz,
    distKm,
  };
}

// ─── Hour angles & perigee ────────────────────────────────────────

export function computeHourAngles(lat, lon, altM, t) {
  const observer = new Observer(lat, lon, altM);
  const t0 = t instanceof AstroTime ? t : MakeTime(t);
  const eq = Equator(Body.Moon, t0, observer, true, true);
  // GMST en heures (SiderealTime retourne en heures)
  const gstHours = SiderealTime(t0);
  const gha = ((gstHours - eq.ra) * 15 + 360) % 360;
  let lha = (gha + lon) % 360;
  if (lha < 0) lha += 360;
  if (lha > 180) lha -= 360;
  return { lhaDeg: lha, ghaDeg: gha, decDeg: eq.dec };
}

export function daysSincePerigee(t) {
  const t0 = t instanceof AstroTime ? t : MakeTime(t);
  // Echantillonnage toutes les 3h sur 32 jours dans le passe
  const stepDays = 3 / 24;
  const nSteps = 32 * 8;
  let minDist = Infinity;
  let minTt = t0.tt;
  for (let i = nSteps; i >= 0; i--) {
    const tSample = t0.AddDays(-i * stepDays);
    const d = geoMoonDistKm(tSample);
    if (d < minDist) { minDist = d; minTt = tSample.tt; }
  }
  return t0.tt - minTt;
}

// ─── Passages (lever/coucher) ─────────────────────────────────────

export function getMoonPasses(lat, lon, altM,
    hours = 720, startOffsetHours = 0, horizonDegrees = 0) {
  const observer = new Observer(lat, lon, altM);
  const tStartReq = MakeTime(new Date(Date.now() + startOffsetHours * 3600 * 1000));
  const endTt = tStartReq.tt + hours / 24;

  // Si la Lune est deja levee au debut de la fenetre, reculer la recherche
  // d'1 jour pour inclure le passage en cours (comme moon_calc.py).
  const { el: elStart } = moonAltAzDist(observer, tStartReq);
  const searchStart = elStart > horizonDegrees
    ? tStartReq.AddDays(-1)
    : tStartReq;

  const passes = [];
  let current = searchStart;
  let safety = 200;
  while (current.tt < endTt && safety-- > 0) {
    let rise, set;
    try {
      rise = SearchRiseSet(Body.Moon, observer, +1, current,
        (endTt - current.tt) + 1, horizonDegrees);
    } catch (e) { rise = null; }
    if (!rise) break;
    try {
      set = SearchRiseSet(Body.Moon, observer, -1, rise, 2, horizonDegrees);
    } catch (e) { set = null; }
    if (!set) break;
    // Ignorer les passages entierement avant le debut de la fenetre
    if (set.tt < tStartReq.tt) {
      current = set.AddDays(0.001);
      continue;
    }
    if (rise.tt > endTt) break;
    // Echantillonnage d'elevation pour trouver le max (AddDays pour
    // conversion TT correcte — NE PAS utiliser MakeTime avec JD)
    const nSamples = 50;
    const ttSpan = set.tt - rise.tt;
    let maxEl = -Infinity, maxElDate = rise.date;
    for (let i = 0; i <= nSamples; i++) {
      const frac = i / nSamples;
      const tSample = rise.AddDays(frac * ttSpan);
      const { el } = moonAltAzDist(observer, tSample);
      if (el > maxEl) { maxEl = el; maxElDate = tSample.date; }
    }
    passes.push({
      riseTime: rise.date.toISOString(),
      setTime: set.date.toISOString(),
      maxEl: Math.round(maxEl * 10) / 10,
      maxElTime: maxElDate.toISOString(),
      durationMin: Math.round((set.date - rise.date) / 60000),
    });
    current = set.AddDays(0.001);
  }
  return passes;
}

// ─── Enrichissement d'un passage (spread min/max, az rise/set, ...) ─

export function enrichMoonPass(lat, lon, altM, passData,
    distReference = "topo") {
  const observer = new Observer(lat, lon, altM);
  const tMax = MakeTime(new Date(passData.maxElTime));
  const eqMax = Equator(Body.Moon, tMax, observer, true, true);
  const distKm = distReference === "geo"
    ? geoMoonDistKm(tMax)
    : eqMax.dist * 149_597_870.7;
  passData.distKm = distKm;
  // Illumination & phase
  const illumObj = Illumination(Body.Moon, tMax);
  const illum = illumObj.phase_fraction * 100;
  passData.illum = Math.round(illum * 10) / 10;
  const phaseDeg = MoonPhase(tMax);
  passData.phase = phaseName(phaseDeg, illum, true);
  // AZ rise/set
  const tRise = MakeTime(new Date(passData.riseTime));
  const tSet = MakeTime(new Date(passData.setTime));
  const hRise = Horizon(tRise, observer, Equator(Body.Moon, tRise, observer, true, true).ra,
    Equator(Body.Moon, tRise, observer, true, true).dec, "normal");
  const hSet = Horizon(tSet, observer, Equator(Body.Moon, tSet, observer, true, true).ra,
    Equator(Body.Moon, tSet, observer, true, true).dec, "normal");
  passData.azRise = hRise.azimuth;
  passData.azSet = hSet.azimuth;
  // Declinaison
  passData.decl = eqMax.dec;
  // Moon-Sun
  const hSun = sunAltAz(observer, tMax);
  const hMoon = { az: Horizon(tMax, observer, eqMax.ra, eqMax.dec, "normal").azimuth,
    el: Horizon(tMax, observer, eqMax.ra, eqMax.dec, "normal").altitude };
  passData.moonSun = angularSepDeg(hMoon.az, hMoon.el, hSun.az, hSun.el);
  // Libration + spread ref a EL max
  const libRef = computeLibration(lat, lon, altM, tMax);
  passData.libLat = libRef.libLat;
  passData.libLon = libRef.libLon;
  passData.libRate = libRef.libRate;
  passData.dopplerSpread = libRef.dopplerSpreadHz;
  // Echantillonnage 30 points pour spread min/max
  const nSamples = 30;
  const durationMs = new Date(passData.setTime) - new Date(passData.riseTime);
  let sprMin = Infinity, sprMax = -Infinity;
  let sprMinTime = passData.maxElTime, sprMaxTime = passData.maxElTime;
  let libMin = 0, libMax = 0;
  for (let i = 0; i < nSamples; i++) {
    const frac = nSamples > 1 ? i / (nSamples - 1) : 0.5;
    const dt = new Date(new Date(passData.riseTime).getTime() + frac * durationMs);
    const tS = MakeTime(dt);
    const lib = computeLibration(lat, lon, altM, tS);
    if (lib.dopplerSpreadHz < sprMin) {
      sprMin = lib.dopplerSpreadHz;
      sprMinTime = dt.toISOString();
      libMin = lib.libRate;
    }
    if (lib.dopplerSpreadHz > sprMax) {
      sprMax = lib.dopplerSpreadHz;
      sprMaxTime = dt.toISOString();
      libMax = lib.libRate;
    }
  }
  passData.spreadMin = sprMin;
  passData.spreadMinTime = sprMinTime;
  passData.spreadMax = sprMax;
  passData.spreadMaxTime = sprMaxTime;
  passData.libRateMin = libMin;
  passData.libRateMax = libMax;
  return passData;
}

// ─── Timeline d'un passage (details 30 min) ────────────────────────

export function samplePassTimeline(lat, lon, altM, passData,
    intervalMin = 30, freqHz = 10368e6, tSysK = 50.0,
    distReference = "topo") {
  const observer = new Observer(lat, lon, altM);
  const tRise = new Date(passData.riseTime);
  const tSet = new Date(passData.setTime);
  // Aligner sur demi-heure pile
  const firstMinute = (Math.floor(tRise.getMinutes() / intervalMin) + 1) * intervalMin;
  let tCur;
  if (firstMinute >= 60) {
    tCur = new Date(tRise);
    tCur.setMinutes(0, 0, 0);
    tCur.setHours(tCur.getHours() + 1);
  } else {
    tCur = new Date(tRise);
    tCur.setMinutes(firstMinute, 0, 0);
  }
  const samples = [];
  while (tCur <= tSet) {
    const tSky = MakeTime(tCur);
    const { az, el, distKm: topoDist } = moonAltAzDist(observer, tSky);
    if (el < 0) {
      tCur = new Date(tCur.getTime() + intervalMin * 60000);
      continue;
    }
    const distKm = distReference === "geo"
      ? geoMoonDistKm(tSky)
      : topoDist;
    const lib = computeLibration(lat, lon, altM, tSky);
    const deg = computeDegradation(lat, lon, altM, tSky, freqHz, tSysK);
    const sun = sunAltAz(observer, tSky);
    const ms = angularSepDeg(az, el, sun.az, sun.el);
    const eq = Equator(Body.Moon, tSky, observer, true, true);
    const gstHours = SiderealTime(tSky);
    const gha = ((gstHours - eq.ra) * 15 + 360) % 360;
    let lha = (gha + lon) % 360;
    if (lha > 180) lha -= 360;
    samples.push({
      time: new Date(tCur).toISOString(),
      az, el, distKm,
      decl: eq.dec,
      lha,
      dopplerHz: deg.dopplerHz,
      spreadHz: lib.dopplerSpreadHz * freqHz / 10.368e9,
      libRate: lib.libRate,
      skyTempK: deg.skyTempK,
      degradationDb: deg.degradationDb,
      pathLossExtraDb: deg.pathLossExtraDb,
      moonSun: ms,
      sunAz: sun.az,
      sunEl: sun.el,
    });
    tCur = new Date(tCur.getTime() + intervalMin * 60000);
  }
  return samples;
}
