"""
EME Rotator Controller — Calculs ephemerides lunaires et solaires.
Module autonome sans dependance Qt.
Utilise Skyfield avec ephemerides JPL DE440s (precision sub-km).
"""

import logging
import math
import os
from datetime import datetime, timezone

import numpy as np
from skyfield.api import Loader, wgs84, Star
from skyfield import almanac

log = logging.getLogger(__name__)

# ════════════════════════════════════════════
# Chargement ephemerides JPL DE440s (une fois)
# ════════════════════════════════════════════

_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(_data_dir, exist_ok=True)
_load = Loader(_data_dir)
ts = _load.timescale()
eph = _load('de440s.bsp')


# ════════════════════════════════════════════
# Conversion Maidenhead
# ════════════════════════════════════════════

def locator_to_latlon(locator: str) -> tuple[float, float]:
    """Convertit un QRA Maidenhead (4, 6 ou 8 caracteres) en (lat_deg, lon_deg).

    Raises ValueError si le locator est invalide.
    """
    loc = locator.strip()
    length = len(loc)
    if length not in (4, 6, 8):
        raise ValueError(f"Locator doit faire 4, 6 ou 8 caracteres: '{loc}'")

    # Normaliser : champ en majuscules, sous-carre en minuscules
    loc = loc[0].upper() + loc[1].upper() + loc[2:]
    if length >= 6:
        loc = loc[:4] + loc[4].lower() + loc[5].lower() + loc[6:]

    # Field (2 lettres A-R)
    if not ('A' <= loc[0] <= 'R') or not ('A' <= loc[1] <= 'R'):
        raise ValueError(f"Champ invalide: '{loc[:2]}'")
    lon = (ord(loc[0]) - ord('A')) * 20.0 - 180.0
    lat = (ord(loc[1]) - ord('A')) * 10.0 - 90.0

    # Square (2 chiffres 0-9)
    if not loc[2].isdigit() or not loc[3].isdigit():
        raise ValueError(f"Carre invalide: '{loc[2:4]}'")
    lon += int(loc[2]) * 2.0
    lat += int(loc[3]) * 1.0

    if length == 4:
        return (lat + 0.5, lon + 1.0)

    # Subsquare (2 lettres a-x)
    if not ('a' <= loc[4] <= 'x') or not ('a' <= loc[5] <= 'x'):
        raise ValueError(f"Sous-carre invalide: '{loc[4:6]}'")
    lon += (ord(loc[4]) - ord('a')) * (2.0 / 24.0)
    lat += (ord(loc[5]) - ord('a')) * (1.0 / 24.0)

    if length == 6:
        return (lat + 1.0 / 48.0, lon + 1.0 / 24.0)

    # Extended (2 chiffres 0-9)
    if not loc[6].isdigit() or not loc[7].isdigit():
        raise ValueError(f"Carre etendu invalide: '{loc[6:8]}'")
    lon += int(loc[6]) * (2.0 / 240.0)
    lat += int(loc[7]) * (1.0 / 240.0)

    return (lat + 1.0 / 480.0, lon + 1.0 / 240.0)


# ════════════════════════════════════════════
# Helpers prives
# ════════════════════════════════════════════

def _moon_phase_name(phase_deg: float, illum_pct: float) -> str:
    """Nom de la phase lunaire (8 phases) — traduit via i18n."""
    try:
        from i18n import tr
    except ImportError:
        tr = lambda k, **kw: k
    if illum_pct < 2:
        return tr("phase_new")
    if illum_pct > 98:
        return tr("phase_full")
    if 48 < illum_pct < 52:
        return tr("phase_fq") if phase_deg < 180 else tr("phase_lq")
    if phase_deg < 90:
        return tr("phase_wax_cres")
    if phase_deg < 180:
        return tr("phase_wax_gibb")
    if phase_deg < 270:
        return tr("phase_wan_gibb")
    return tr("phase_wan_cres")


def _next_rise_set(body, location, t0, days=2.0, horizon_degrees=0.0):
    """Trouve le prochain lever et coucher apres t0.

    horizon_degrees : 0 = centre geometrique (defaut),
                      -0.8333 = bord superieur + refraction atmospherique.
    Returns (next_rise: datetime|None, next_set: datetime|None).
    """
    t1 = ts.tt_jd(t0.tt + days)
    try:
        f = almanac.risings_and_settings(eph, body, location,
                                         horizon_degrees=horizon_degrees)
        times, events = almanac.find_discrete(t0, t1, f)
    except Exception:
        return None, None

    next_rise = None
    next_set = None
    for t, event in zip(times, events):
        if event and next_rise is None:
            next_rise = t.utc_datetime()
        elif not event and next_set is None:
            next_set = t.utc_datetime()
        if next_rise and next_set:
            break
    return next_rise, next_set


# Matrice rotation galactique → ICRS J2000 (Hipparcos ESA 1997)
_R_GAL_TO_ICRS = np.array([
    [-0.0548755604, -0.8734370902, -0.4838350155],
    [ 0.4941094279, -0.4448296300,  0.7469822445],
    [-0.8676661490, -0.1980763734,  0.4559837762],
])


def _galactic_to_radec(gal_l_deg: float, gal_b_deg: float) -> tuple[float, float]:
    """Convertit galactique (l, b) degres en ICRS (ra, dec) degres."""
    l_r = math.radians(gal_l_deg)
    b_r = math.radians(gal_b_deg)
    xyz = np.array([math.cos(b_r) * math.cos(l_r),
                     math.cos(b_r) * math.sin(l_r),
                     math.sin(b_r)])
    eq = _R_GAL_TO_ICRS @ xyz
    ra = math.degrees(math.atan2(eq[1], eq[0])) % 360
    dec = math.degrees(math.asin(np.clip(eq[2], -1.0, 1.0)))
    return ra, dec


def _angular_sep_deg(az1: float, el1: float, az2: float, el2: float) -> float:
    """Separation angulaire en degres entre deux points (az, el) en degres."""
    a1, e1, a2, e2 = map(math.radians, (az1, el1, az2, el2))
    cos_s = (math.sin(e1) * math.sin(e2) +
             math.cos(e1) * math.cos(e2) * math.cos(a1 - a2))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_s))))


# ════════════════════════════════════════════
# Fonctions publiques
# ════════════════════════════════════════════

def compute_moon(lat: float, lon: float, alt_m: float = 0,
                 dist_reference: str = "topo",
                 horizon_degrees: float = 0.0) -> dict:
    """Calcule la position actuelle de la Lune et les donnees EME.

    dist_reference : "topo" (defaut, observateur -> Lune, recommande EME)
                     ou "geo" (centre Terre -> centre Lune).
    horizon_degrees : 0 (defaut, centre geometrique) ou -0.8333 (visuel).
    Returns dict avec : az, el, dist_km, illumination, phase_name,
                        next_rise (datetime|None), next_set (datetime|None)
    """
    location = wgs84.latlon(lat, lon, elevation_m=alt_m)
    observer = eph['earth'] + location
    t = ts.now()

    # Position (AZ/EL) toujours topocentrique (un observateur voit depuis sa
    # position, pas depuis le centre de la Terre).
    apparent = observer.at(t).observe(eph['moon']).apparent()
    alt, az, topo_distance = apparent.altaz()

    # Distance selon la convention choisie
    if dist_reference == "geo":
        geo_app = eph['earth'].at(t).observe(eph['moon']).apparent()
        _, _, distance = geo_app.radec()
        dist_km = distance.km
    else:
        dist_km = topo_distance.km

    illum = almanac.fraction_illuminated(eph, 'moon', t) * 100
    phase = almanac.moon_phase(eph, t)
    phase_name = _moon_phase_name(phase.degrees, illum)

    next_rise, next_set = _next_rise_set(eph['moon'], location, t,
                                         horizon_degrees=horizon_degrees)

    return {
        "az": float(round(az.degrees, 1)),
        "el": float(round(alt.degrees, 1)),
        "dist_km": float(round(dist_km, 0)),
        "illumination": float(round(illum, 1)),
        "phase_name": phase_name,
        "next_rise": next_rise,
        "next_set": next_set,
    }


def compute_sun(lat: float, lon: float, alt_m: float = 0,
                horizon_degrees: float = 0.0) -> dict:
    """Calcule la position actuelle du Soleil.

    Returns dict avec : az, el, next_rise (datetime|None), next_set (datetime|None)
    """
    location = wgs84.latlon(lat, lon, elevation_m=alt_m)
    observer = eph['earth'] + location
    t = ts.now()

    apparent = observer.at(t).observe(eph['sun']).apparent()
    alt, az, _ = apparent.altaz()

    next_rise, next_set = _next_rise_set(eph['sun'], location, t,
                                         horizon_degrees=horizon_degrees)

    return {
        "az": float(round(az.degrees, 1)),
        "el": float(round(alt.degrees, 1)),
        "next_rise": next_rise,
        "next_set": next_set,
    }


def compute_cold_sky(lat: float, lon: float, alt_m: float = 0,
                     min_elevation: float = 10.0,
                     min_sun_sep: float = 25.0) -> dict:
    """Calcule les regions de ciel froid pour calibration Y-factor 10 GHz.

    Regions de reference (HB9DRI + poles galactiques) classees par temperature
    de bruit estimee a 10 GHz. La region la plus froide visible est recommandee.

    Returns dict : az, el, sun_sep, visible, sun_clear, source, noise_k,
                   candidates (liste de toutes les regions evaluees),
                   recommended_idx (index du candidat recommande)
    """
    location = wgs84.latlon(lat, lon, elevation_m=alt_m)
    observer = eph['earth'] + location
    t = ts.now()

    # Position du Soleil pour test de separation
    sun_app = observer.at(t).observe(eph['sun']).apparent()
    sun_alt, sun_az, _ = sun_app.altaz()
    sun_az_d = sun_az.degrees
    sun_el_d = sun_alt.degrees

    def _eval(ra_deg, dec_deg, source, noise_k):
        star = Star(ra_hours=ra_deg / 15.0, dec_degrees=dec_deg)
        app = observer.at(t).observe(star).apparent()
        alt_s, az_s, _ = app.altaz()
        az_d = az_s.degrees
        el_d = alt_s.degrees
        sep = _angular_sep_deg(az_d, el_d, sun_az_d, sun_el_d)
        return {
            "az": float(round(az_d, 1)), "el": float(round(el_d, 1)),
            "sun_sep": float(round(sep, 1)),
            "visible": bool(el_d >= min_elevation),
            "sun_clear": bool(sep >= min_sun_sep),
            "source": source,
            "noise_k": noise_k,
        }

    # Regions de ciel froid — coordonnees J2000, bruit estime a 10 GHz
    # Classees par temperature de bruit croissante (les plus froides en premier)
    #                     Nom              RA°     Dec°   ~K    Lat. galactique
    cold_sources = [
        ("Pole Gal. N",   192.86,  +27.13,   3),  # b=+90°, le plus froid
        ("Pole Gal. S",   _galactic_to_radec(0, -90)[0],
                          _galactic_to_radec(0, -90)[1],
                                               3),  # b=-90°
        ("Leo",           168.0,   +18.0,     5),  # b~+65°, tres froid
        ("Pictor",         80.0,   -53.0,    10),  # b~-35°, froid
        ("Cassiopeia",     15.0,   +72.0,    25),  # b~+10°, tiede (plan galactique)
        ("Taurus",         65.0,   +18.0,    25),  # b~-20°, tiede (Crab Nebula)
        ("Sagittarius",   285.0,   -30.0,    40),  # b~-20°, tiede (centre galactique)
    ]

    candidates = []
    for name, ra, dec, noise in cold_sources:
        pt = _eval(ra, dec, name, noise)
        candidates.append(pt)

    # Recommander le plus froid visible (deja trie par noise_k croissant)
    recommended_idx = 0
    for i, c in enumerate(candidates):
        if c["visible"] and c["sun_clear"]:
            recommended_idx = i
            break

    # Le "best" = le recommande (compat API existante)
    best = candidates[recommended_idx]
    best["candidates"] = candidates
    best["recommended_idx"] = recommended_idx
    return best


def get_moon_passes(lat: float, lon: float, alt_m: float = 0,
                    hours: int = 24, start_offset_hours: int = 0,
                    horizon_degrees: float = 0.0) -> list[dict]:
    """Liste les passages de la Lune au-dessus de l'horizon.

    start_offset_hours : decalage en heures depuis maintenant (ex: 720 = +30j)
    horizon_degrees : 0 = centre geometrique, -0.8333 = visuel (bord + refraction).
    Returns list de dict : rise_time, set_time, max_el, max_el_time, duration_min
    """
    location = wgs84.latlon(lat, lon, elevation_m=alt_m)
    observer = eph['earth'] + location
    moon_body = eph['moon']

    t0 = ts.now()
    t0 = ts.tt_jd(t0.tt + start_offset_hours / 24.0)
    t1 = ts.tt_jd(t0.tt + hours / 24.0)

    # Si la Lune est deja levee, chercher le lever precedent
    app = observer.at(t0).observe(moon_body).apparent()
    alt0, _, _ = app.altaz()
    search_start = ts.tt_jd(t0.tt - 1) if alt0.degrees > 0 else t0

    try:
        f = almanac.risings_and_settings(eph, moon_body, location,
                                         horizon_degrees=horizon_degrees)
        times, events = almanac.find_discrete(search_start, t1, f)
    except Exception:
        return []

    passes = []
    i = 0
    n = len(times)

    while i < n:
        # Chercher un lever
        if not events[i]:
            i += 1
            continue

        rise_t = times[i]

        # Trouver le coucher correspondant
        j = i + 1
        while j < n and events[j]:
            j += 1
        if j >= n:
            break
        set_t = times[j]

        # Filtrer : passes dans la fenetre [t0, t1]
        if set_t.tt < t0.tt:
            i = j + 1
            continue

        # Elevation max par echantillonnage vectorise
        jd_arr = np.linspace(rise_t.tt, set_t.tt, 50)
        t_arr = ts.tt_jd(jd_arr)
        alts, _, _ = observer.at(t_arr).observe(moon_body).apparent().altaz()
        el_arr = alts.degrees
        idx = int(el_arr.argmax())
        max_el = float(el_arr[idx])
        max_el_time = t_arr[idx].utc_datetime()

        rise_time = rise_t.utc_datetime()
        set_time = set_t.utc_datetime()
        duration = (set_time - rise_time).total_seconds() / 60.0

        passes.append({
            "rise_time": rise_time,
            "set_time": set_time,
            "max_el": round(max_el, 1),
            "max_el_time": max_el_time,
            "duration_min": round(duration, 0),
        })

        i = j + 1

    return passes


def _short_phase_name(phase_deg: float, illum_pct: float) -> str:
    """Nom court de la phase lunaire — traduit via i18n."""
    try:
        from i18n import tr
    except ImportError:
        tr = lambda k, **kw: k
    if illum_pct < 2:
        return tr("phase_s_new")
    if illum_pct > 98:
        return tr("phase_s_full")
    if 48 < illum_pct < 52:
        return tr("phase_s_fq") if phase_deg < 180 else tr("phase_s_lq")
    if phase_deg < 90:
        return tr("phase_s_wax_cres")
    if phase_deg < 180:
        return tr("phase_s_wax_gibb")
    if phase_deg < 270:
        return tr("phase_s_wan_gibb")
    return tr("phase_s_wan_cres")


def _libration_at(observer, t_sky):
    """Calcule la libration selenographique (lat, lon) au temps donne.

    Utilise les constantes IAU 2009 pour l'orientation de la Lune.
    Retourne (lib_lon_deg, lib_lat_deg).
    """
    obs_moon = observer.at(t_sky).observe(eph['moon']).apparent()
    pos = obs_moon.position.au
    pos_unit = pos / np.linalg.norm(pos)

    T = (t_sky.tt - 2451545.0) / 36525.0
    d = t_sky.tt - 2451545.0

    # Pole Nord lunaire (IAU 2009)
    ra_pole = math.radians(269.9949 + 0.0031 * T)
    dec_pole = math.radians(66.5392 + 0.0130 * T)

    # Rotation propre (meridien principal)
    W = math.radians((38.3213 + 13.17635815 * d) % 360)

    # Repere selenographique en ICRF
    z_sel = np.array([
        math.cos(dec_pole) * math.cos(ra_pole),
        math.cos(dec_pole) * math.sin(ra_pole),
        math.sin(dec_pole)
    ])
    n = np.array([-math.sin(ra_pole), math.cos(ra_pole), 0.0])
    e = np.cross(z_sel, n)
    e = e / np.linalg.norm(e)
    x_sel = n * math.cos(W) + e * math.sin(W)
    y_sel = np.cross(z_sel, x_sel)

    # Projection du vecteur de visee
    px = np.dot(pos_unit, x_sel)
    py = np.dot(pos_unit, y_sel)
    pz = np.dot(pos_unit, z_sel)

    lib_lat = math.degrees(math.asin(np.clip(pz, -1, 1)))
    lib_lon = math.degrees(math.atan2(py, px))
    return lib_lon, lib_lat


def compute_libration(lat: float, lon: float, alt_m: float,
                      t_sky) -> dict:
    """Calcule la libration lunaire et le Doppler spread EME.

    Returns dict : lib_lon, lib_lat, lib_rate (deg/h),
                   doppler_spread_hz (a 10.368 GHz)
    """
    location = wgs84.latlon(lat, lon, elevation_m=alt_m)
    observer = eph['earth'] + location

    lon0, lat0 = _libration_at(observer, t_sky)

    # Taux de libration (derivee centree sur ±30 min)
    dt = 0.5 / 24  # 30 min en jours juliens
    t1 = ts.tt_jd(t_sky.tt - dt)
    t2 = ts.tt_jd(t_sky.tt + dt)
    lon1, lat1 = _libration_at(observer, t1)
    lon2, lat2 = _libration_at(observer, t2)

    # Gerer le wrap-around en longitude (±180)
    dlon = lon2 - lon1
    if dlon > 180: dlon -= 360
    if dlon < -180: dlon += 360
    dlon_dt = dlon / 1.0  # deg/h (1h = 2 × 30min)
    dlat_dt = (lat2 - lat1) / 1.0

    lib_rate = math.sqrt(dlon_dt**2 + dlat_dt**2)

    # Doppler spread a 10.368 GHz
    # v_tangentielle = lib_rate × R_lune × pi/180
    R_MOON = 1737.4  # km
    v_tan = lib_rate * R_MOON * math.pi / 180 * 1000 / 3600  # m/s
    spread = 2 * v_tan * 10.368e9 / 3e8  # Hz

    return {
        "lib_lon": round(lon0, 2),
        "lib_lat": round(lat0, 2),
        "lib_rate": round(lib_rate, 4),
        "doppler_spread_hz": round(spread, 0),
    }


def enrich_moon_pass(lat: float, lon: float, alt_m: float,
                     pass_data: dict,
                     dist_reference: str = "topo") -> dict:
    """Enrichit un dict passage avec distance, illum, phase, AZ, decl, moon-sun,
    libration et Doppler spread.

    dist_reference : "topo" (defaut) ou "geo".
    Utilise Skyfield + JPL DE440s (precision sub-km).
    """
    location = wgs84.latlon(lat, lon, elevation_m=alt_m)
    observer = eph['earth'] + location

    # Au moment de l'EL max
    t_max = ts.from_datetime(pass_data["max_el_time"])
    app_moon = observer.at(t_max).observe(eph['moon']).apparent()
    _, _, topo_dist = app_moon.altaz()
    if dist_reference == "geo":
        geo_app = eph['earth'].at(t_max).observe(eph['moon']).apparent()
        _, _, geo_dist = geo_app.radec()
        pass_data["dist_km"] = geo_dist.km
    else:
        pass_data["dist_km"] = topo_dist.km

    # Illumination
    illum = almanac.fraction_illuminated(eph, 'moon', t_max) * 100
    pass_data["illum"] = round(illum, 1)

    # Phase
    phase_deg = almanac.moon_phase(eph, t_max).degrees
    pass_data["phase"] = _short_phase_name(phase_deg, illum)

    # AZ au lever
    t_rise = ts.from_datetime(pass_data["rise_time"])
    app_rise = observer.at(t_rise).observe(eph['moon']).apparent()
    _, az_r, _ = app_rise.altaz()
    pass_data["az_rise"] = az_r.degrees

    # AZ au coucher
    t_set = ts.from_datetime(pass_data["set_time"])
    app_set = observer.at(t_set).observe(eph['moon']).apparent()
    _, az_s, _ = app_set.altaz()
    pass_data["az_set"] = az_s.degrees

    # Declinaison
    _, dec, _ = app_moon.radec()
    pass_data["decl"] = dec.degrees

    # Separation Moon-Sun
    app_sun = observer.at(t_max).observe(eph['sun']).apparent()
    alt_m_d, az_m_d, _ = app_moon.altaz()
    alt_s_d, az_s_d, _ = app_sun.altaz()
    pass_data["moon_sun"] = _angular_sep_deg(
        az_m_d.degrees, alt_m_d.degrees, az_s_d.degrees, alt_s_d.degrees)

    # Libration et Doppler spread au moment de l'EL max
    lib = compute_libration(lat, lon, alt_m, t_max)
    pass_data["lib_lat"] = lib["lib_lat"]
    pass_data["lib_lon"] = lib["lib_lon"]
    pass_data["lib_rate"] = lib["lib_rate"]
    pass_data["doppler_spread"] = lib["doppler_spread_hz"]

    return pass_data
