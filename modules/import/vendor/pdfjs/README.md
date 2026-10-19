# PDF.js (Mozilla), intégré tel quel

- Paquet npm `pdfjs-dist@6.4.299` (publié le 03/10/2026), licence Apache-2.0 (`LICENSE`). Aucune dépendance d'exécution.
- Fichiers `legacy/build/pdf.min.mjs` et `legacy/build/pdf.worker.min.mjs`, copiés sans modification. Build « legacy » :
  le build standard 6.x exige des fonctions JS très récentes (`Map.prototype.getOrInsertComputed`) absentes de Chromium 141.
- Empreintes SHA-256 vérifiées par `modules/import/assembler.py` (qui les recopie dans `app/CoffraPlan.html`, blocs
  `pdfjs-src` et `pdfjs-worker-src`) :
  - `pdf.min.mjs` : `bccc24ea711db8e44503629519904a5292d73b9daaa214bbe7cdcc282b0f4259`
  - `pdf.worker.min.mjs` : `145d2dd3ab0c86151011dba95acfa2d5336e2accd59388ea43dbee0efddaaec6`
  - archive `pdfjs-dist-6.4.299.tgz` : `86269b40170eb41740ea05ad2102d71d33de4f122b34eb2f478be0ea7779c415`
- Non intégrés : polices standard, CMap (textes CJK), décodeurs wasm (images JPEG 2000 / JBIG2), visionneuse. Effet : rendu de
  ces cas dégradé dans l'aperçu ; aucune requête réseau n'est faite pour les chercher.
- Mise à jour : `npm pack pdfjs-dist@<version>`, copier les deux fichiers `legacy/build/*.min.mjs`, reporter les empreintes dans
  `assembler.py` et ici, puis `python modules/import/assembler.py` et `python tests/run.py complet -j 4` (dont `t_pdf`).
