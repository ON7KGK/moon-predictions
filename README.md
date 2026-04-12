# Moon Predictions — Standalone App

Application Python autonome de prévision des passages lunaires pour les amateurs EME.

**Indépendante** du EME Rotator Controller — fonctionne sans aucun matériel,
juste pour calculer et afficher les passages de la Lune visibles depuis votre QTH.

## Fonctionnalités

- Liste des passages de la Lune sur **30 ou 60 jours** glissants
- Pour chaque passage : lever, coucher, **élévation max**, durée, AZ lever/coucher
- Calculs EME : **distance Lune-Terre**, path loss extra (vs périgée), path loss total selon fréquence
- **Score qualité 0-10** combinant élévation, durée, distance et angle Moon-Sun
- Filtres : EL min, score min, fréquence (50 MHz à 24 GHz)
- Heures **UTC ou locales**
- Position actuelle de la Lune (AZ/EL/phase) en haut de l'écran
- Export **CSV** et **TXT**
- Interface sombre, lisible

## Installation

```bash
cd moon-predictions-app
pip install -r requirements.txt
```

Première exécution : Skyfield télécharge automatiquement les éphémérides JPL DE440s
(~32 Mo) dans le dossier `data/`. Cela prend quelques secondes — connexion Internet
requise **uniquement la première fois**. Ensuite tout fonctionne hors ligne.

## Lancement

```bash
python main.py
```

## Utilisation

1. Entrer son **indicatif** (optionnel) et son **QRA locator** (6 ou 8 caractères minimum)
2. Indiquer l'**altitude** (mètres au-dessus du niveau de la mer)
3. Choisir la **fréquence EME** (10 GHz par défaut)
4. Cliquer **Calculer**
5. Filtrer / trier les passages selon ses critères
6. Exporter en **TXT** ou **PDF** pour partage ou archivage

## Code de couleur

| Couleur | Excellence |
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

## Précision

Les calculs utilisent **Skyfield** avec les éphémérides **JPL DE440s** :
- Précision de position lunaire : **sub-kilomètre**
- Précision élévation : **±0.003°**
- Largement suffisant pour le tracking EME 10 GHz (lobe ~2°)

## Crédits

- **Auteur** : ON7KGK & Claude (Anthropic)
- **Éphémérides** : NASA JPL DE440s via [Skyfield](https://rhodesmill.org/skyfield/)
- **Icône** : [Crescent icons created by Arkinasi - Flaticon](https://www.flaticon.com/free-icons/crescent)

Licence : MIT
