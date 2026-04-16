# Moon Predictions

Application autonome de prévision des passages lunaires pour radiomateurs pratiquant l'EME.

## Fonctionnalités

- Liste des passages de la Lune sur 30 ou 60 jours au choix
- Ligne de la position actuelle de la lune (AZ/EL, distance, phase,    libration, Doppler spread)
- Pour chaque passage : lever, coucher, élévation max, durée, AZ lever/coucher, déclinaison
- Calculs EME :
  - Distance Lune-Terre topocentrique (plus précis pour le path loss)
  - Path loss extra (vs périgée) et path loss total selon la fréquence choisie
  - Libration (°/h) et Doppler spread (Hz) à la fréquence choisie
  - Angle Moon-Sun (bruit solaire)
- Score qualité 0-10 adaptatif selon la fréquence : 
  - VHF/UHF (< 1 GHz) : élévation et durée dominent
  - Micro-ondes (≥ 1 GHz) : libration devient critique (30 % du score)
- Filtres temps réel : EL min, score min, fréquence (50 MHz à 24 GHz)
- Heures UTC ou locales au choix
- Interface multilingue : Français / Nederlands / English
- Thème clair / sombre avec couleurs EME adaptées à chaque thème
- Conventions de calcul configurables (topocentrique/géocentrique, horizon géométrique/visuel)
- Export TXT et PDF
- Lien direct vers EME Observer (SA5IKN) pour les skeds

## Téléchargement

Les mises à jour sont disponibles pour Windows et Linux dans les Releases ici :
[page Releases GitHub](https://github.com/ON7KGK/moon-predictions/releases) :

| Plateforme | Fichier |
|---|---|
| Windows | `MoonPredictions-Setup-<version>.exe` (installeur NSIS) |
| Linux x64 | `MoonPredictions-<version>-linux-x64.tar.gz` |

> Note : la version macOS n'est pas disponible pour l'instant (incompatibilité
> Nuitka avec PyQt6 sur macOS, migration vers PySide6 à l'étude).

### Installation depuis le code source

```bash
cd moon-predictions-app
pip install -r requirements.txt
python main.py
```

Première exécution : Skyfield télécharge automatiquement les éphémérides JPL DE440s
(~32 Mo) dans le dossier `data/`. Connexion Internet requise **uniquement la première
fois**. Ensuite tout fonctionne hors ligne.

## Utilisation

1. Entrer son **indicatif** (optionnel) et son **QRA locator** (6 ou 8 caractères minimum)
2. Indiquer l'**altitude** (mètres ASL)
3. Choisir la **fréquence EME** (10 GHz par défaut)
4. Si on souhaite modifier la méthode de calcul (geo/topo) cliquer dans   
**Conventions** 
5. Cliquer **Calculer**
6. Filtrer / trier les passages selon ses critères
7. Exporter en **TXT** ou **PDF** pour partage ou archivage
8. Choix du thème **Clair** ou **Sombre**

Au premier affichage, si le locator est déjà sauvegardé, le calcul se lance automatiquement.

## Code de couleur

| Couleur | Signification |
|---|---|
| 🟢 Vert | Excellent |
| 🟠 Orange | Moyen |
| 🔴 Rouge | Faible |

Critères :
- **EL max** : vert ≥ 20°, orange ≥ 10°
- **Durée** : vert ≥ 5h, orange ≥ 2h
- **Distance** : vert ≤ 370 000 km, orange ≤ 390 000 km (proche périgée = mieux)
- **Path loss extra** : vert ≤ 1 dB, orange ≤ 2 dB
- **Angle Moon-Sun** : vert ≥ 15°, orange ≥ 5°
- **Libration** : vert < 0.10°/h, orange < 0.25°/h, rouge ≥ 0.25°/h
- **Doppler spread** : vert < 50 Hz, orange < 150 Hz, rouge ≥ 150 Hz


## Conventions de calcul

Un bouton **Conventions** permet de choisir les références utilisées pour les calculs.
Les défauts sont optimisés pour l'EME radioamateur :

### Distance Terre-Lune

Choix de la méthode de calcul avec le bouton **Conventions**

- **Topocentrique** (défaut, recommandé EME) : distance réelle entre l'antenne
  et la Lune. C'est la distance que le signal radio parcourt.
- **Géocentrique** : distance depuis le centre de la Terre (convention astronomique
  classique, utilisée par les logiciels comme mooncalc.org).

La différence peut atteindre ~6 378 km (rayon terrestre) à la Lune au zénith.
Pour le calcul du path loss EME, la distance topocentrique est indispensable.

### Horizon lever / coucher

- **Géométrique 0°** (défaut, recommandé EME) : la Lune est considérée levée/couchée
  quand son **centre** traverse l'horizon géométrique. C'est la référence pour le
  bilan de liaison EME — en dessous de 0° la Lune est bloquée par la Terre.
- **Visuel −0.83°** : convention astronomique classique. La Lune est « levée »
  quand son **bord supérieur** apparaît (demi-diamètre + réfraction atmosphérique).

En EME, la réfraction atmosphérique est négligeable pour les signaux radio
(bien moindre qu'en optique), et le « bord » de la Lune n'a pas de sens pour un
écho radar. L'horizon géométrique est donc le bon choix.

> **Pourquoi deux conventions ?** Les logiciels d'astronomie générale
> (mooncalc.org, Stellarium, etc.) utilisent le plus souvent la distance
> géocentrique et l'horizon visuel car ils ciblent l'observation visuelle de la Lune.
> Pour le calcul d'une liaison radio, les conventions EME sont plus précises.

## Précision

Les calculs utilisent **Skyfield** avec les éphémérides **JPL DE440s** de la NASA :
- Précision de position lunaire : **sub-kilomètre**
- Précision élévation : **±0.003°**
- Précision libration : **IAU 2009**

## Crédits

- **Auteur** : ON7KGK & Claude Code (Anthropic)
- **Éphémérides** : NASA JPL DE440s via [Skyfield](https://rhodesmill.org/skyfield/)
- **Icône** : [Crescent icons created by Arkinasi - Flaticon](https://www.flaticon.com/free-icons/crescent)

## Remerciements

Un grand merci à :
- **Eric ON5TA**, **Michel ON7FI** et **Christophe ON6ZQ** pour leurs retours experts et suggestions d'améliorations
Merci à Christophe pour son hébergement de la version Web actuellement en démo : https://moon.on6zq.be/moon-predictions/ 

## Signaler un bug

Cette application est **open source**. Tout bug constaté peut être envoyé à
[on7kgk@outlook.com](mailto:on7kgk@outlook.com) ou signalé via
[GitHub Issues](https://github.com/ON7KGK/moon-predictions/issues).

Licence : GPL-3.0

---

## Code signing policy

Free code signing will be provided by [SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org).

**Team roles:**
- Committers and Approvers: [ON7KGK](https://github.com/ON7KGK)

**Privacy:**
This program will not transfer any information to other networked systems
unless specifically requested by the user or the person installing or
operating it. Ephemeris data (JPL DE440s) is downloaded automatically
on first run from NASA servers; no personal data is transmitted.

**Third-party components:**
This software uses [Skyfield](https://rhodesmill.org/skyfield/) (MIT),
[PyQt6](https://www.riverbankcomputing.com/software/pyqt/) (GPL-3.0),
and [NumPy](https://numpy.org/) (BSD-3).
