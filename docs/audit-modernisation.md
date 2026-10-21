# Audit technique et feuille de route de modernisation (phase 6, 21/10/2026)

Demande de Kévin (directive « modernisation du moteur de reconnaissance ») : technologies gratuites, locales, exploitables
commercialement ; aucune API payante, aucun abonnement, aucun plan envoyé à un serveur ; HTML autonome pour l'essentiel, moteur
local CPU / GPU permis pour les fonctions avancées (future distribution Windows) ; pas de réécriture complète en une PR ; cotes,
unités et quantités validées de façon déterministe.

Légende : **certain** = lu dans le code ou mesuré ; **probable** = déduit de plusieurs indices ; **hypothèse** = à vérifier.

## 1. Reconnaissance (OCR) — fait dans cette phase

### Candidats comparés
| Moteur | Version (date de la source) | Licence code / poids | Local, hors ligne | Essayé ici | Verdict |
|---|---|---|---|---|---|
| Tesseract.js (référence) | 7.0.0, modèle fra best_int | Apache-2.0 / Apache-2.0 | oui, navigateur (wasm) | oui | gardé au choix, et pour les zones sans grille |
| **PP-OCRv6 small, reconnaissance** | PP-OCRv6 publié le 11/06/2026 ; ONNX de RapidOCR 3.10.0 | Apache-2.0 / Apache-2.0 | oui, navigateur (ONNX Runtime Web 1.30.0, MIT) | **oui : intégré** | **nouveau moteur par défaut** |
| PP-OCRv6 tiny | idem | Apache-2.0 | oui | oui (Python) | moins juste (textes, « O » des angles) |
| PP-OCRv5 mobile | PaddleOCR 3.x | Apache-2.0 | oui | oui (Python) | nettement moins juste sur ces plans |
| PP-OCRv6 détection (pages entières) | idem | Apache-2.0 | oui | oui (Python, tuiles 300 dpi) | utile aux repères ; non embarqué (voir § 1.4) |
| PaddleOCR.js (`@paddleocr/paddleocr-js` 0.4.2) | npm | Apache-2.0 | oui (navigateur) | non : ses modèles se téléchargent depuis des hôtes bloqués ici | même moteur que ci-dessus ; notre intégration directe évite toute requête |
| PP-StructureV3 | PaddleOCR 3.x (pas de note 2026 propre trouvée) | Apache-2.0 | oui, Python (CPU / GPU) | non : modèles sur hôtes bloqués | à essayer pour la structure des tableaux, en moteur local |
| PaddleOCR-VL-1.6 (≈ 0,9 G paramètres) | publié le 28/05/2026 | Apache-2.0 (fiche du modèle) | oui, GPU conseillé | non : hôtes bloqués | usage ciblé, sorties vérifiables seulement (voir § 1.4) |
| Docling | 2.9x à 2.12x selon les miroirs (version exacte à vérifier sur PyPI) | MIT ; modèles : licences propres | oui, Python | non : modèles sur hôtes bloqués | conversion de documents bureautiques ; peu adapté aux plans |

Sources : fiche PaddleOCR-VL-1.6 (huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6), notes PaddleOCR (paddleocr.ai), PyPI / miroirs
pour Docling, `MODEL_LICENSES.md` de RapidOCR 3.10.0 (joint dans `modules/import/vendor/ppocr/`).
**Hôtes bloqués dans l'environnement de développement** : huggingface.co, modelscope.cn, paddle-model-ecology.bj.bcebos.com,
github.com (téléchargements). Seuls PyPI et npm étaient joignables : seuls les modèles publiés dans ces dépôts ont pu être mesurés.

### Protocole
Trois plans PDF réels (A : ouvrage circulaire, tableau et repères en tracés, 2 pages ; B : texte extractible, tableau à en-têtes
fusionnés ; C : planche tournée, tout en tracés). Ils restent hors du dépôt. Vérités terrain **indépendantes de CoffraPlan** : A et C
relevées à la main sur des rendus 250 dpi, B lue dans la couche texte (pdftotext). Le quatrième PDF annoncé n'était pas dans la
session : non mesuré. Mesures dans Chromium, sur l'appli réelle (même grille, mêmes découpes, seul le moteur change).

### Résultats — qualité brute (466 cellules non vides des trois tableaux)
| Champ | Tesseract 7 (retenu) | PP-OCRv6 (retenu) |
|---|---|---|
| Repères | 61 / 63 | **63 / 63** |
| Dimensions | 90 / 93 | **93 / 93** |
| Niveaux / altitudes | 70 / 73 (3 vraies erreurs : 560 → 260, 4,31 → 4,51 × 2) | **73 / 73** |
| Angles | 21 / 23 | **23 / 23** |
| Textes libres | 195 / 214 | 195 / 214 (égal) |
| Tout | 437 / 466 | **447 / 466** |
| Cellules signalées incertaines | 59 | 23 |
| Temps de lecture des 3 tableaux | 42 s | 98 s (**2,3 × plus lent**) |

« Retenu » = texte après les corrections typographiques prudentes de `corriger` (le brut reste gardé). Mémoire JS mesurée
identique (le modèle vit dans le tas WebAssembly ; non mesuré finement).

Qualité métier finale (nomenclature et analyse du dessin) : voir CHANGELOG, § Phase 6.

### 1.4 Suite recommandée pour l'OCR
1. **Moteur local hors navigateur (Windows, Tauri)** : ONNX Runtime natif multi-fil (et DirectML / CUDA) avec les mêmes modèles ;
   gain de vitesse attendu de 5 à 10 × (probable : mesuré 6 s en Python 4 fils contre 70 s dans le navigateur pour 535 cellules).
   Même contrat `lire(images) → {texte, conf, orientation}` : rien à changer dans `ocr.js` hors du transport.
2. **Détection PP-OCRv6** (pages entières, zones sans grille) embarquée dans ce moteur local : remplacerait `lireZone` (Tesseract)
   et compléterait `blocsTexte` pour les repères écrits en vrai texte d'image (scans).
3. **PP-StructureV3** à mesurer en moteur local sur les mêmes trois plans (dès que les hôtes de modèles sont autorisés) : structure
   de tableaux sans grille et cellules fusionnées.
4. **PaddleOCR-VL-1.6** : seulement en option locale (GPU), pour **proposer** une lecture d'un tableau difficile ou d'un cartouche ;
   chaque valeur proposée doit se rattacher à une boîte de la page et repasser par les mêmes contrôles déterministes (unités,
   cotes, quantités) ; jamais de cote de fabrication tirée du modèle sans relecture.
5. Vitesse dans le navigateur, sans changer de moteur : WebGPU (ONNX Runtime Web) quand le navigateur l'offre ; lecture en cascade
   (Tesseract d'abord, PP-OCR sur les cellules douteuses seulement) si la vitesse devient bloquante.

## 2. Autres domaines

(Section complétée ci-dessous.)
