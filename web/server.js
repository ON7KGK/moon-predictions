// ════════════════════════════════════════════════════════════════════
// Moon Predictions Web — Serveur statique pur (100% client-side)
// Depuis v1.8.5 tout le calcul se fait dans le navigateur (astronomy-engine
// via CDN ESM). Ce serveur ne fait qu'envoyer les fichiers de public/.
// La charge CPU est donc 0 cote serveur, peu importe le nombre de visiteurs.
// ════════════════════════════════════════════════════════════════════

import express from "express";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, "public")));

app.listen(PORT, () => {
  console.log(`Moon Predictions Web (static) running on http://localhost:${PORT}`);
});
