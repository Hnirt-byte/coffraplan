# PP-OCRv6 (reconnaissance de texte) sur ONNX Runtime Web, intégré tel quel

Utilisé par `modules/import/ppocr.js` (`CPI.ppocr`), branché dans `ocr.js` pour les **tableaux à grille** (`lireGrille`) et les
**repères dessinés** (`lireBlocs`) ; moteur par défaut depuis la phase 6, Tesseract restant au choix (fenêtre d'import,
« Moteur OCR »). Chargé au premier besoin. Tout est recopié dans `app/CoffraPlan.html` par `modules/import/assembler.py`, qui
vérifie les empreintes SHA-256 ci-dessous : aucun CDN, aucun téléchargement de modèle à l'usage, fonctionne en `file://`.

| Fichier | Origine | Licence | SHA-256 |
|---|---|---|---|
| `ort.min.js` | npm `onnxruntime-web@1.30.0`, `dist/ort.min.js` | MIT, © Microsoft Corporation (`LICENSE-onnxruntime-web`) | `7ae472a8ec976bcb69ad46b89b0a6ec8f3c5dbea4477674a26958672d1f3322d` |
| `ort-wasm-simd-threaded.mjs` | même paquet, `dist/` | MIT | `e13f7f94fc51b4ca72b12faeb1ee95f4ace6dfbc8939bc718aabdc0a27c4299b` |
| `ort-wasm-simd-threaded.wasm.gz` | même paquet, `dist/ort-wasm-simd-threaded.wasm` compressé par `gzip -9 -n` | MIT | `.gz` : `bf933930bc90cf4f613f36cdc41616b54cfd2e9930478b574aed6ed4ef9ff8ca` ; `.wasm` : `3398c10d07d229bd91b364548e130e0e51a8e5704b88c7c083ebbeb78842dee2` |
| `PP-OCRv6_rec_small.onnx.gz` | PyPI `rapidocr==3.10.0` (roue `rapidocr-3.10.0-py3-none-any.whl`), `rapidocr/models/PP-OCRv6_rec_small.onnx` compressé par `gzip -9 -n` ; même empreinte que celle publiée par RapidOCR (`default_models.yaml`, `multi_PP-OCRv6_rec_small`) | Apache-2.0 : poids © Baidu / PaddleOCR, conversion ONNX © RapidOCR (`LICENSE-Apache-2.0-PaddleOCR-RapidOCR`, `MODEL_LICENSES-rapidocr.md`) | `.gz` : `de992e86c5af5515a4709c43d22a6bc49033259736c2835859e6cd88040e76b7` ; `.onnx` : `6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884` |
| `PP-OCRv6_rec_small.dict.txt` | métadonnée `character` du modèle ONNX ci-dessus (18 708 signes, un par ligne ; classe 0 = blanc CTC, dernière classe = espace) | Apache-2.0 | `f7aa897ca828a4c7c9e2739c30f9161a33306d532f020bcdb91dcfb664a5507e` |

Archives d'origine : `onnxruntime-web-1.30.0.tgz` (npm, `shasum` b88b09117992e6f486321e931a826fd2f7775377) ;
`rapidocr-3.10.0-py3-none-any.whl` (PyPI, SHA-256 `2fc34e26cd0f48514804a94f8832283039c7334076bff60768b1fed9ad068050`).

## Licences (usage commercial)
- ONNX Runtime Web : MIT. PP-OCRv6 (code PaddleOCR et poids) : Apache-2.0, comme la conversion RapidOCR. Les deux permettent
  l'usage, la modification et la redistribution commerciale, à condition de garder les avis de licence (fichiers de ce dossier)
  et de signaler les modifications (aucune : fichiers recopiés tels quels, seulement compressés).
- Aucun service, aucune clé, aucun abonnement : l'inférence se fait dans la page.

## Dans le HTML
- Blocs `<script type="text/plain">` : `ppocr-ort-src`, `ppocr-ort-mjs`, `ppocr-dict` (texte tel quel), `ppocr-ort-wasm` et
  `ppocr-rec` (fichiers `.gz` en base64). Ne pas les modifier à la main.
- `ppocr.js` injecte `ort.min.js`, fournit le module de chargement et le wasm en URL blob (`ort.env.wasm.wasmPaths`), un seul fil
  (une page `file://` n'a pas `SharedArrayBuffer`), crée la session du modèle (décompressé par `DecompressionStream`).
- Entrée du modèle : `[N, 3, 48, W]` BGR, `(x / 255 − 0,5) / 0,5`, hauteur 48, largeur proportionnelle ; sortie `[N, T, 18 710]` ;
  décodage CTC glouton. Seule la **reconnaissance** est embarquée (pas la détection) : les lignes viennent de la géométrie
  (cellules de la grille, blocs de `CPI.geometrie.blocsTexte`). La lecture d'une zone sans grille (`lireZone`) reste à Tesseract.
- Poids ajouté au HTML : ≈ 30 Mo (modèle 18,5 Mo + wasm 3,7 Mo compressés, en base64).

## Mise à jour
1. `npm pack onnxruntime-web@<v>` ; `pip download rapidocr==<v> --no-deps` ; noter les empreintes des archives.
2. Copier les fichiers du tableau ; `gzip -9 -n -c <fichier> > <fichier>.gz` pour le wasm et le modèle ; dictionnaire : métadonnée
   `character` du modèle (`onnx.load(...).metadata_props`), un signe par ligne, sans ligne vide finale.
3. Reporter les empreintes dans `assembler.py` (liste `PPOCR`) et ici, puis `python modules/import/assembler.py`.
4. `python tests/run.py complet -j 4` (dont `t_ppocr` et `t_ocr`, qui vérifient le démarrage en `file://` sans réseau).
