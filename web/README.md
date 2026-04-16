# Moon Predictions — Version Web

Version web responsive de **Moon Predictions** pour radioamateurs EME.
Accessible depuis n'importe quel navigateur moderne (desktop, tablette, mobile).

Port JavaScript de l'application Python/Qt, utilisant
[`astronomy-engine`](https://github.com/cosinekitty/astronomy) pour les calculs
(précision ~10 m sur la position lunaire — largement suffisant pour EME).

## Fonctionnalités

- Liste des passages lunaires sur 30 ou 60 jours
- Ligne **MAINTENANT** — position actuelle de la Lune
- **Clic sur une ligne de passage** → détail par tranches de 30 min
  (AZ, EL, distance, Doppler, Spread, TSky, DGR, libration, Sun AZ/EL…)
- **Clic sur la ligne MAINTENANT** → dashboard temps-réel (DGR, Doppler,
  Home Echo, LHA/GHA, jours depuis périgée…)
- Filtres temps réel : EL min (qui agit aussi comme **horizon mécanique**),
  Score min, fréquence (50 MHz à 24 GHz)
- Interface **multilingue** : Français / Nederlands / English
- **Thème clair / sombre** avec couleurs EME adaptées
- **Conventions de calcul** configurables (topocentrique/géocentrique,
  horizon géométrique/visuel)
- **Responsive** : utilisable sur smartphone à la parabole
- Export **TXT** et **PDF** (via impression navigateur)
- Prefs persistées dans `localStorage` (callsign, locator, langue, thème…)

## Prérequis

- **Node.js ≥ 18**

## Installation

```bash
cd moon-predictions-app/web
npm install
```

## Démarrage

```bash
npm start
```

Puis ouvrir [http://localhost:3000](http://localhost:3000) dans le navigateur.

## Déploiement (pour ton ami qui héberge)

### Option 1 — Simple, sur un VPS Linux

```bash
# 1. Cloner ou copier le répertoire web/
scp -r moon-predictions-app/web/ user@server:/home/user/moon-predictions

# 2. Sur le serveur
cd moon-predictions
npm install --omit=dev
PORT=3000 npm start
```

Pour lancer au démarrage, créer un service systemd :

```ini
# /etc/systemd/system/moon-predictions.service
[Unit]
Description=Moon Predictions Web
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/user/moon-predictions
Environment=PORT=3000
ExecStart=/usr/bin/node server.js
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable moon-predictions
sudo systemctl start moon-predictions
```

### Option 2 — Derrière un reverse proxy nginx

```nginx
server {
    listen 80;
    server_name moon.example.com;
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Option 3 — Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

## Structure du projet

```
web/
├── package.json
├── server.js                     # Express + routes API
├── lib/
│   └── moon-calc.js              # Calculs (astronomy-engine)
├── public/
│   ├── index.html
│   ├── css/
│   │   ├── themes.css            # Palettes clair/sombre
│   │   └── app.css
│   ├── js/
│   │   ├── app.js                # Logique principale
│   │   ├── i18n.js               # Système de langues
│   │   ├── modals.js             # Conventions, Help, About, détails
│   │   ├── api.js                # Appels fetch
│   │   └── utils.js              # Helpers
│   └── texts/
│       ├── fr.json               # Toutes les traductions FR
│       ├── nl.json               # NL
│       └── en.json               # EN
└── README.md
```

## API Endpoints

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/api/ping` | Test santé serveur |
| `GET` | `/api/locator?locator=JO20BM85` | Conversion Maidenhead → lat/lon |
| `GET` | `/api/moon?locator=...&alt=...&distRef=topo&horizon=0` | Position actuelle |
| `GET` | `/api/sun?locator=...&alt=...` | Position Soleil |
| `GET` | `/api/now-detail?locator=...&alt=...&freq=10368e6` | Dashboard MAINTENANT |
| `GET` | `/api/passes?locator=...&alt=...&hours=720&offset=0` | Liste des passages |
| `POST` | `/api/pass-timeline` | Détail toutes les 30 min d'un passage |

## Précision

Les calculs utilisent [astronomy-engine](https://github.com/cosinekitty/astronomy)
qui offre ~10 m de précision sur la position lunaire. Pour l'EME 10 GHz (lobe ~2°,
soit ~13 km à la Lune), c'est largement suffisant.

La version desktop Python utilise Skyfield + JPL DE440s (précision sub-km) —
un peu plus précis mais rarement nécessaire pour les skeds.

## Remerciements

Un grand merci à :
- **Eric ON5TA**, **Michel ON7FI** et **Christophe ON6ZQ** pour leurs retours
  experts et suggestions d'améliorations
- [astronomy-engine](https://github.com/cosinekitty/astronomy) par Don Cross (MIT)

## Signaler un bug

Cette application est **open source**. Tout bug constaté peut être envoyé à
[on7kgk@outlook.com](mailto:on7kgk@outlook.com) ou signalé via
[GitHub Issues](https://github.com/ON7KGK/moon-predictions/issues).

## Crédits

Version web — ON7KGK Michaël & Claude Code (Anthropic)

Licence : GPL-3.0
