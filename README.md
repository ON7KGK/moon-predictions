# Moon Predictions

Standalone Moon pass forecast application for radio amateurs practicing EME (Earth-Moon-Earth).

> **⚠ Version 1.9.0-alpha** — program under active development. Some features are experimental.

Three variants share the same physics core:
- **Desktop** (Windows / Linux) — Python + PyQt6
- **Web** hosted version — Node.js static server, 100 % client-side calculations
- **GitHub Pages** — pure static HTML/JS, calculations in your browser

Current web demo hosted by Christophe ON6ZQ: <https://moon.on6zq.be/moon-predictions/>
GitHub Pages variant (client-side only): <https://on7kgk.github.io/moon-predictions/>

---

## English

### Features

- List of Moon passes over 30 or 60 days
- Live "NOW" row showing current Moon position (AZ/EL, distance, phase, libration, Doppler spread)
- Per pass: rise, set, max elevation, duration, rise/set AZ, declination
- EME computations:
  - Topocentric Moon-Earth distance (accurate path-loss)
  - Extra path loss vs perigee, total path loss at chosen frequency
  - Libration rate (°/h) and Doppler spread (Hz) at chosen frequency
  - Moon-Sun angle (solar noise)
- Adaptive 0-10 quality score:
  - VHF/UHF (< 1 GHz): elevation and duration dominate
  - Microwave (≥ 1 GHz): libration becomes critical (30 % of score)
- Real-time filters: min EL, min score, frequency (50 MHz to 24 GHz)
- UTC or local time
- Multilingual UI: English / French / Dutch
- Light / dark theme with EME-tuned colours
- Configurable calculation conventions (topocentric/geocentric, geometric/visual horizon)
- TXT and PDF export
- Direct link to EME Observer (SA5IKN) for skeds

### Advanced EME features (v1.9.0-alpha)

- **DX locator** input — enables a full bistatic Home↔DX view
- **Home polarization** input (H = 0°, V = 90°, or custom slant in degrees)
- **Bistatic spread** (MoonSked / SA5IKN compatible): `2 · f · |v_h − v_d| · R / c`
- **Spatial polarization offset** using the Hustig/Pettis KL7WE formula (referenced in the MoonSked Appendix 1)
- **MNR** (Maximum Non-Reciprocity, after N1BUG) — warns of one-way QSO risk
- **Real-time dashboard** laid out like MoonSked's Moon Track window:
  - Range · DGR/Sky/Spreading · Geocentric GHA/Decl
  - Home · UTC clock · DX
  - DX data row: AZ · EL · Doppler · Polarity · MNR
  - Big home AZ · TX/RX sequence · big home EL
  - Topocentric · RX polarisation · TX polarisation
- Updates at **2 Hz** (500 ms) like MoonSked
- URL query parameters (for users who purge cookies):
  `?lang=en&call=ON7KGK&locator=JO20BM&el=118&dx=JN48LL&pol=90`

### Download

Installers are built for Windows and Linux on the [GitHub Releases page](https://github.com/ON7KGK/moon-predictions/releases):

| Platform | File |
|---|---|
| Windows | `MoonPredictions-Setup-<version>.exe` (NSIS installer, code-signed by SignPath) |
| Linux x64 | `MoonPredictions-<version>-linux-x64.tar.gz` |

> macOS build is currently unavailable (Nuitka/PyQt6 incompatibility, migration to PySide6 under study).

### Install from source

```bash
cd moon-predictions-app
pip install -r requirements.txt
python main.py
```

On first run, Skyfield automatically downloads JPL DE440s ephemerides (~32 MB) into `data/`. An Internet connection is required **only on first launch** — everything runs offline afterwards.

### Colour code

| Colour | Meaning |
|---|---|
| 🟢 Green | Excellent |
| 🟠 Orange | Fair |
| 🔴 Red | Poor |

Thresholds:
- **Max EL**: green ≥ 20°, orange ≥ 10°
- **Duration**: green ≥ 5 h, orange ≥ 2 h
- **Distance**: green ≤ 370 000 km, orange ≤ 390 000 km (near perigee is better)
- **Extra path loss**: green ≤ 1 dB, orange ≤ 2 dB
- **Moon-Sun angle**: green ≥ 15°, orange ≥ 5°
- **Libration**: green < 0.10°/h, orange < 0.25°/h, red ≥ 0.25°/h
- **Doppler spread**: green < 50 Hz, orange < 150 Hz, red ≥ 150 Hz
- **MNR**: green < 3 dB, orange < 10 dB, red ≥ 10 dB (one-way likely)

### Calculation conventions

A **Conventions** button lets you choose the references used.
Defaults are optimised for amateur radio EME:

**Earth-Moon distance**
- **Topocentric** (default, EME-recommended): real distance from antenna to Moon — this is what the radio signal travels.
- **Geocentric**: distance from Earth centre (classical astronomy convention, used by mooncalc.org etc.).
  The difference can reach ~6 378 km (one Earth radius) when the Moon is at zenith.
  Topocentric distance is required for accurate EME path-loss.

**Rise / set horizon**
- **Geometric 0°** (default, EME-recommended): Moon is rising/setting when its **centre** crosses the geometric horizon — the right reference for an EME link budget; below 0° the Moon is blocked by the Earth.
- **Visual −0.83°**: classical astronomy convention, Moon is "up" when its **upper limb** appears (semi-diameter + atmospheric refraction).
  For radio signals at UHF/microwave, refraction is negligible and the Moon's "limb" is meaningless for a radar echo, so the geometric horizon is the correct choice.

### Accuracy

Calculations use **Skyfield** with NASA's **JPL DE440s** ephemerides:
- Moon position: **sub-kilometre** precision
- Elevation: **±0.003°**
- Libration: **IAU 2009**

Spread / polarization / MNR formulas follow:
- K1JT Taylor — *High-Accuracy Prediction and Measurement of Lunar Echoes*, QEX 2016
- G3WDG Suckling — *Predicting Libration Fading on the EME Path* (2010)
- GM4JJJ Anderson — *MoonSked User Guide* (Appendix 1: Hustig/Pettis polarization, N1BUG MNR theory)
- SA5IKN — *EME Observer* documentation (bistatic spread formula)

### Credits

- **Author**: Michaël ON7KGK
- **Co-development**: Claude Code (Anthropic)
- **Ephemerides**: NASA JPL DE440s via [Skyfield](https://rhodesmill.org/skyfield/)
- **Icon**: [Crescent icons by Arkinasi — Flaticon](https://www.flaticon.com/free-icons/crescent)

### Acknowledgements

Huge thanks to:
- **Eric ON5TA**, **Michel ON7FI**, **Christophe ON6ZQ** for expert feedback and improvement suggestions
- **Christophe ON6ZQ** for hosting the current web demo at <https://moon.on6zq.be/moon-predictions/>
- **David GM4JJJ** (†) for MoonSked — the long-time EME reference this project learns from
- **SA5IKN** for the open *EME Observer* at <https://dxer.site/eme-observer/>
- **Joe Taylor K1JT** for WSJT-X and the physics foundations

### Reporting a bug

This application is **open source**. Report any issue to [on7kgk@outlook.com](mailto:on7kgk@outlook.com) or via [GitHub Issues](https://github.com/ON7KGK/moon-predictions/issues).

License: GPL-3.0

---

## Français

### Fonctionnalités

- Liste des passages de la Lune sur 30 ou 60 jours au choix
- Ligne de la position actuelle de la Lune (AZ/EL, distance, phase, libration, Doppler spread)
- Pour chaque passage : lever, coucher, élévation max, durée, AZ lever/coucher, déclinaison
- Calculs EME :
  - Distance Lune-Terre topocentrique (plus précis pour le path loss)
  - Path loss extra (vs périgée) et path loss total selon la fréquence choisie
  - Libration (°/h) et Doppler spread (Hz) à la fréquence choisie
  - Angle Moon-Sun (bruit solaire)
- Score qualité 0-10 adaptatif :
  - VHF/UHF (< 1 GHz) : élévation et durée dominent
  - Micro-ondes (≥ 1 GHz) : libration devient critique (30 % du score)
- Filtres temps réel : EL min, score min, fréquence (50 MHz à 24 GHz)
- Heures UTC ou locales
- Interface multilingue : Français / Nederlands / English
- Thème clair / sombre avec couleurs EME adaptées
- Conventions de calcul configurables (topocentrique/géocentrique, horizon géométrique/visuel)
- Export TXT et PDF
- Lien direct vers EME Observer (SA5IKN) pour les skeds

### Fonctionnalités EME avancées (v1.9.0-alpha)

- Champ **Locator DX** — active une vue bistatique Home↔DX complète
- Champ **Polarisation Home** (H = 0°, V = 90°, ou slant personnalisé)
- **Spread bistatique** compatible MoonSked / SA5IKN : `2 · f · |v_h − v_d| · R / c`
- **Décalage spatial de polarisation** formule Hustig/Pettis KL7WE (référencée dans l'Appendix 1 du manuel MoonSked)
- **MNR** (Maximum Non-Reciprocity, d'après N1BUG) — alerte sur le risque de QSO one-way
- **Dashboard temps réel** avec un layout MoonSked Moon Track :
  - Range · DGR/Sky/Spreading · Geocentric GHA/Decl
  - Home · horloge UTC · DX
  - Ligne DX : AZ · EL · Doppler · Polarity · MNR
  - AZ home géant · séquence TX/RX · EL home géant
  - Topocentrique · polarisation RX · polarisation TX
- Rafraîchissement **2 Hz** (500 ms) comme MoonSked
- Paramètres d'URL (pour utilisateurs qui purgent leurs cookies) :
  `?lang=fr&call=ON7KGK&locator=JO20BM&el=118&dx=JN48LL&pol=90`

### Téléchargement

Les mises à jour Windows et Linux sont disponibles sur la [page Releases GitHub](https://github.com/ON7KGK/moon-predictions/releases) :

| Plateforme | Fichier |
|---|---|
| Windows | `MoonPredictions-Setup-<version>.exe` (installeur NSIS, signé SignPath) |
| Linux x64 | `MoonPredictions-<version>-linux-x64.tar.gz` |

> macOS non disponible pour l'instant (incompatibilité Nuitka/PyQt6, migration vers PySide6 à l'étude).

### Installation depuis le code source

```bash
cd moon-predictions-app
pip install -r requirements.txt
python main.py
```

Au premier lancement, Skyfield télécharge automatiquement les éphémérides JPL DE440s (~32 Mo) dans `data/`. Internet requis **uniquement la première fois**, ensuite tout fonctionne hors ligne.

### Code couleur

| Couleur | Signification |
|---|---|
| 🟢 Vert | Excellent |
| 🟠 Orange | Moyen |
| 🔴 Rouge | Faible |

Critères :
- **EL max** : vert ≥ 20°, orange ≥ 10°
- **Durée** : vert ≥ 5 h, orange ≥ 2 h
- **Distance** : vert ≤ 370 000 km, orange ≤ 390 000 km (proche périgée = mieux)
- **Path loss extra** : vert ≤ 1 dB, orange ≤ 2 dB
- **Angle Moon-Sun** : vert ≥ 15°, orange ≥ 5°
- **Libration** : vert < 0.10°/h, orange < 0.25°/h, rouge ≥ 0.25°/h
- **Doppler spread** : vert < 50 Hz, orange < 150 Hz, rouge ≥ 150 Hz
- **MNR** : vert < 3 dB, orange < 10 dB, rouge ≥ 10 dB (one-way probable)

### Conventions de calcul

Un bouton **Conventions** permet de choisir les références utilisées. Les défauts sont optimisés EME :

**Distance Terre-Lune**
- **Topocentrique** (défaut, recommandé EME) : distance réelle antenne-Lune, celle que parcourt le signal radio.
- **Géocentrique** : distance depuis le centre de la Terre (convention astronomique classique, mooncalc.org, etc.).
  Différence jusqu'à ~6 378 km quand la Lune est au zénith. Topocentrique indispensable pour le path loss EME.

**Horizon lever / coucher**
- **Géométrique 0°** (défaut, recommandé EME) : Lune considérée levée/couchée quand son **centre** traverse l'horizon géométrique. Référence pour le bilan de liaison EME.
- **Visuel −0.83°** : convention astronomique classique, bord supérieur + réfraction. En EME la réfraction est négligeable et le « bord » de la Lune n'a pas de sens pour un écho radar.

### Précision

Les calculs utilisent **Skyfield** avec les éphémérides **JPL DE440s** de la NASA :
- Précision position lunaire : **sub-kilomètre**
- Précision élévation : **±0.003°**
- Précision libration : **IAU 2009**

Formules spread / polarisation / MNR issues de :
- K1JT Taylor — *High-Accuracy Prediction and Measurement of Lunar Echoes*, QEX 2016
- G3WDG Suckling — *Predicting Libration Fading on the EME Path* (2010)
- GM4JJJ Anderson — *MoonSked User Guide* (Appendix 1 : polarisation Hustig/Pettis, MNR N1BUG)
- SA5IKN — documentation *EME Observer* (formule spread bistatique)

### Crédits

- **Auteur** : Michaël ON7KGK
- **Co-développement** : Claude Code (Anthropic)
- **Éphémérides** : NASA JPL DE440s via [Skyfield](https://rhodesmill.org/skyfield/)
- **Icône** : [Crescent icons by Arkinasi — Flaticon](https://www.flaticon.com/free-icons/crescent)

### Remerciements

Un grand merci à :
- **Eric ON5TA**, **Michel ON7FI**, **Christophe ON6ZQ** pour leurs retours experts et suggestions d'améliorations
- **Christophe ON6ZQ** pour l'hébergement de la démo web actuelle à <https://moon.on6zq.be/moon-predictions/>
- **David GM4JJJ** (†) pour MoonSked — la référence EME de longue date dont ce projet s'inspire
- **SA5IKN** pour *EME Observer* ouvert à <https://dxer.site/eme-observer/>
- **Joe Taylor K1JT** pour WSJT-X et les fondements physiques

### Signaler un bug

Application **open source**. Tout bug peut être signalé à [on7kgk@outlook.com](mailto:on7kgk@outlook.com) ou via [GitHub Issues](https://github.com/ON7KGK/moon-predictions/issues).

Licence : GPL-3.0

---

## Code signing policy

Free code signing is provided by [SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org).

**Team roles**
- Committers and Approvers: [ON7KGK](https://github.com/ON7KGK)

**Privacy**
This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it. Ephemeris data (JPL DE440s) is downloaded automatically on first run from NASA servers; no personal data is transmitted.

**Third-party components**
This software uses [Skyfield](https://rhodesmill.org/skyfield/) (MIT), [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) (GPL-3.0), [NumPy](https://numpy.org/) (BSD-3), and [astronomy-engine](https://github.com/cosinekitty/astronomy) (MIT, for the web/docs variants).
