# Tesseract.js (moteur OCR), intégré tel quel

Utilisé par `modules/import/ocr.js` (« Reconnaître le tableau (OCR) »), chargé seulement au premier clic. Tout est recopié
dans `app/CoffraPlan.html` par `modules/import/assembler.py`, qui vérifie les empreintes SHA-256 ci-dessous : aucun CDN,
aucun téléchargement de modèle à l'usage, fonctionne en `file://`.

| Fichier | Origine (paquet npm) | Licence | SHA-256 |
|---|---|---|---|
| `tesseract.min.js` | `tesseract.js@7.0.0`, `dist/tesseract.min.js` | Apache-2.0 (`LICENSE-tesseract.js.md`) | `000c27d9cd0def655f77b36c72a389c0ab13793aa31cb4d7aab56d09c0afbc7e` |
| `worker.min.js` | `tesseract.js@7.0.0`, `dist/worker.min.js` | Apache-2.0 | `576b7df7e3393e137e51849357c9adb53fe7ac1bb69bfa06cf3d61520f182c6d` |
| `tesseract-core-simd-lstm.js` | `tesseract.js-core@7.0.0` | Apache-2.0 (`LICENSE-tesseract.js-core`) | `e48e2f02ddae3716c8dd24bf41cd290d4efa96892d689cdc4013c2545d63f469` |
| `tesseract-core-simd-lstm.wasm.gz` | `tesseract.js-core@7.0.0`, `tesseract-core-simd-lstm.wasm` compressé par `gzip -9 -n` | Apache-2.0 | `.gz` : `bad86ecb17527e1725a505a34f7ad44fbe0ccec9013080532997d189d7849f79` ; `.wasm` : `34e8d50cac216427d86bf397d610fdd9f49492539bbcdfbfccc4eda20c810bea` |
| `fra.traineddata.gz` | `@tesseract.js-data/fra@1.0.0`, `4.0.0_best_int/fra.traineddata.gz` (modèle LSTM français de tessdata) | modèle Apache-2.0 (tessdata), paquet MIT | `d611139672b3752c7097e671e4a1d9209dfd37f2aeb081ef6487fba3351e9255` |

Archives npm d'origine (SHA-256) : `tesseract.js-7.0.0.tgz` `9a93bf51c3387f945d10a24bf8b3a4bf2e45c7c7161b8242aafbaf9d3c4b606a`,
`tesseract.js-core-7.0.0.tgz` `ba584355515eaff877552022853c0e71f2cb70466e759d1d6940484929718ee0`,
`tesseract.js-data-fra-1.0.0.tgz` `ffcef66c64e763499d56ea3f8d7470215390b7c3ab8f33df19a2ab0f2d88c0e5`.

## Dans le HTML
- Blocs `<script type="text/plain">` : `tess-src`, `tess-worker-src`, `tess-core-src` (scripts tels que publiés), `tess-wasm`
  et `tess-fra` (fichiers `.gz` en base64). Ne pas les modifier à la main.
- `ocr.js` construit un worker blob : données base64 + `fetch` limité au modèle (toute autre URL est refusée) + cœur + worker.
  Le wasm est décompressé dans la page (`DecompressionStream`) et passé au cœur (`wasmBinary`). Annulation = `terminate()`.
- Variante choisie : cœur `simd-lstm` (moteur LSTM seul, le plus léger) ; modèle `best_int` (bon compromis précision / poids).
  Poids ajouté au HTML : ≈ 2,65 Mo.

## Mise à jour
1. `npm pack tesseract.js@<v> tesseract.js-core@<v> @tesseract.js-data/fra@<v>` ; noter les SHA-256 des archives.
2. Copier les fichiers du tableau ; `gzip -9 -n -c tesseract-core-simd-lstm.wasm > tesseract-core-simd-lstm.wasm.gz`.
3. Reporter les empreintes dans `assembler.py` (liste `TESS`) et ici, puis `python modules/import/assembler.py`.
4. `python tests/run.py complet -j 4` (dont `t_ocr`, qui vérifie aussi le démarrage en `file://` sans réseau).
