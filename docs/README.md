# Moon Predictions — Version 100% client (GitHub Pages)

Variante **statique** de Moon Predictions. Tous les calculs tournent dans
le navigateur → **zéro charge CPU serveur**, hébergeable n'importe où
(GitHub Pages, Netlify, nginx, S3…).

## Différences avec la version `web/`

| | `web/` (Node.js) | `docs/` (client-only) |
|---|---|---|
| Serveur | Express + Node.js | Fichiers statiques |
| Calculs | Côté serveur | **Côté navigateur** |
| CPU hôte | 1-10 % par user | **0 %** |
| Scalabilité | Limitée | **Illimitée** |
| Offline | Non | Possible (après 1er accès, via cache navigateur) |
| Premier chargement | ~50 KB | ~250 KB (astronomy-engine inclus via CDN) |

Les deux versions donnent exactement les **mêmes résultats** — c'est le
même code JS qui tourne juste à un endroit différent.

## Tester localement

Les fichiers de `docs/` peuvent être servis par n'importe quel serveur
HTTP statique. Exemples :

```bash
# Python (pre-installé partout)
cd moon-predictions-app/docs
python -m http.server 8000

# Node.js (si dispo)
npx http-server -p 8000

# VS Code : extension "Live Server" → clic droit sur index.html
```

Puis ouvrir [http://localhost:8000](http://localhost:8000).

> **Important** : ouvrir `index.html` directement (double-clic) ne marche
> pas à cause du CORS des ES modules. Passer par un serveur HTTP, même local.

## Déployer sur GitHub Pages

### Méthode 1 — Pages depuis `/docs` (la plus simple)

1. Pusher le dossier `docs/` sur la branche `main` du repo GitHub
2. GitHub → **Settings** → **Pages**
3. **Source** : Deploy from a branch
4. **Branch** : `main` → **/docs** → **Save**
5. Attendre ~1 min → URL : `https://<user>.github.io/<repo>/`

Dans notre cas : `https://on7kgk.github.io/moon-predictions/`

### Méthode 2 — GitHub Actions (plus flexible)

Voir `.github/workflows/pages.yml` (crée automatiquement après activation).

## astronomy-engine via CDN

Le fichier `js/moon-calc.js` importe astronomy-engine depuis
[esm.sh](https://esm.sh) :

```js
import { ... } from "https://esm.sh/astronomy-engine@2.1.19";
```

Au premier chargement, le navigateur télécharge la lib (~200 KB) et la
met en cache. Les chargements suivants sont instantanés.

### Mode offline

Si le CDN est bloqué (entreprise, pays), télécharger manuellement la
version ESM et la servir localement :

```bash
cd docs/js
curl -o astronomy-engine.js https://esm.sh/astronomy-engine@2.1.19
# Puis changer l'URL dans moon-calc.js et api.js vers "./astronomy-engine.js"
```

## Structure

```
docs/
├── index.html            — UI principale (même que web/)
├── .nojekyll             — dit à GitHub Pages de ne pas traiter avec Jekyll
├── css/
│   ├── themes.css
│   └── app.css
├── js/
│   ├── app.js            — logique principale (identique web/)
│   ├── i18n.js           — langues FR/NL/EN (identique web/)
│   ├── utils.js          — helpers (identique web/)
│   ├── modals.js         — fenêtres (identique web/)
│   ├── moon-calc.js      — calculs astro (import CDN)
│   └── api.js            — wrapper qui appelle moon-calc EN LOCAL
└── texts/                — traductions (identique web/)
```

## Licence

GPL-3.0, même que le reste du projet.
