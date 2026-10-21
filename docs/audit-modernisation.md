# Audit technique et feuille de route de modernisation (phase 6, 21/10/2026 ; mis à jour en phase 7)

Demande de Kévin (directive « modernisation du moteur de reconnaissance ») : technologies gratuites, locales, exploitables
commercialement ; aucune API payante, aucun abonnement, aucun plan envoyé à un serveur ; HTML autonome pour l'essentiel, moteur
local CPU / GPU permis pour les fonctions avancées (future distribution Windows) ; pas de réécriture complète en une PR ; cotes,
unités et quantités validées de façon déterministe.

Légende : **certain** = lu dans le code ou mesuré ; **probable** = déduit de plusieurs indices ; **hypothèse** = à vérifier.

## 0. Décisions actées après la phase 6 (Kévin, 21/10/2026)
- **GAMMA reste à 25 kN/m³** jusqu'à une revue normative propre au calcul des coffrages. EN 1991-1-1, tableau A.1, donne 26 kN/m³ pour un béton
  ordinaire armé frais ; EN 12812 retient 25 kN/m³ pour les situations d'étaiement concernées. La revue vérifiera l'édition applicable et
  proposera un paramètre réglable. Ne pas modifier `GAMMA` avant.
- **Priorité actuelle : IndexedDB et protection des projets** (phase 7 : `docs/stockage.md`). Protéger les projets passe avant toute
  nouvelle fonction.
- **Packaging, choix futur** : le HTML autonome de distribution sera produit par la CI à partir des sources versionnées, plutôt que de
  garder un HTML de plus de 36 Mo à chaque commit. Pas de Git LFS par défaut. À préparer après la sécurisation du stockage.
- **Étapes ultérieures** : modernisation de la reconnaissance documentaire (tableaux voisins du plan D, titres de vues atypiques,
  PP-StructureV3 et modèles visuels documentaires) et moteur OCR natif accéléré pour l'application Windows.

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
relevées à la main sur des rendus 250 dpi, B lue dans la couche texte (pdftotext). D (vue en plan sous toiture, A0 tourné, couche texte, tableau des réservations de 46 lignes à côté d'un tableau de
trappes) a été ajouté en cours de phase ; sa vérité terrain vient de sa couche texte. Mesures dans Chromium, sur l'appli réelle (même grille, mêmes découpes, seul le moteur change).

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

Plan D (46 lignes, OCR de la zone du tableau, vérité = couche texte) : PP-OCRv6 46 / 46 repères, cotes et niveaux, 0 cellule
douteuse, 50 s ; Tesseract 43 / 46, 15 douteuses, 23 s.

## 2. Défauts révélés par le plan D (hors moteur OCR) — corrigés en phase 8
- **Lecture automatique d'un tableau en texte voisin d'un autre tableau** (`nomenclatures.js`) [C, mesuré] : le tableau des
  réservations (46 lignes) est coupé après la 14e ligne ; la suite est mêlée au tableau des trappes et au « NOTA GENERAL ». Contournement
  actuel : zone choisie + « Analyser la zone » → 46 lignes justes. Correction proposée : découper par le cadre (traits) avant les
  colonnes de texte.
- **Titre de vue « Sous Toiture » + « 1 : 25 »** non reconnu (`vues.js`) [C] : la vue reste « autre », sans titre ; la règle prudente
  de la phase 5.1 interdit alors tout comptage d'occurrences (0 compté). Proposition : un titre suivi d'une échelle écrite est un
  titre de vue, le type venant du mot-clé ou, à défaut, de l'unique grande vue de la page.

- **Phase 8, résultat sur le plan D réel** (hors dépôt, lecture automatique sans zone) :
  - nomenclature : 46 / 46 lignes (repères, cotes mm, niveaux, finitions, désignations) ;
  - trappes : tableau distinct ;
  - vue « Sous Toiture » 1:25 : vue en plan ;
  - occurrences : 31 comptées, toutes justes. 33 repères sont dessinés ; R01 et R02, présents deux fois sans quantité, restent non décidés.
- **Cause réelle du défaut de tableau** [C, mesuré] :
  - aucun trait du tableau n'est relevé, car le plafond `SEG_MAX` de 60 000 traits par page est atteint (environ 400 000 sur ce plan) ;
  - le tableau voisin, construit en premier, s'étendait le long d'une ligne de valeurs jusqu'à la nomenclature.
  - Corrigé par les couloirs des en-têtes.
  - **Reste** : `SEG_MAX` lui-même (régions de vue partielles sur les plans très chargés). À traiter avec le moteur natif ou un relevé
    des traits par zone.

## 3. Autres domaines (audit en lecture seule du code, 21/10/2026)
Indicateurs [C] : HTML 36,5 Mo (modèle PP-OCR 24,9 Mo en base64, soit 68 %) ; script principal 642 ko, 5 751 lignes, 518 fonctions
nommées ; 12 redéfinitions par enveloppe sur 7 fonctions (`showChantier`, `prev`, `shP`, `gen`, `coll`, `setForm0`, `printAll`) ;
17 clés `resa*` ; 34 suites Playwright (aucun test unitaire hors navigateur) ; 40 `catch(e){}` vides.

| Domaine | Classement | Constat principal | Technologie gratuite / commerciale utile | Gain · effort · priorité |
|---|---|---|---|---|
| Géométrie (`voileGeo`, `rxGeo`, `gouGeo`, `bmBuild`, `model3`) | adapté | traitements au cas par cas, `model3` très dense ; couvert par `t_coh` [C] | garder ; Clipper2 (Boost) seulement si un défaut d'union / décalage apparaît [H] | maintenabilité · S · basse |
| Calculs de coffrage (`GAMMA`, `plateW`, `flecheCP`, `CPMEC`) | améliorable (contenu) | `filmep` absent de `CPMEC` → flèche non vérifiée pour ce CP [C] ; raidisseurs de poutre par règle fixe « à valider » [C] ; γ = 25 kN/m³ à rapprocher d'EN 1991-1-1 tableau A.1 (24 + 1 armatures + 1 béton frais) [P, à lire sur la norme achetée ; décision actée, ne pas changer sans Kévin] | aucune bibliothèque ; cas de référence chiffrés (formules publiées) figés en test | précision, crédibilité · M · haute |
| Débits et imbrication (`debit`, `nestPieces`, `maxRects`) | améliorable | MaxRects : coupes non garanties « guillotine » [C] ; formes non rectangulaires placées par leur rectangle englobant [C] ; > 360 pièces : pas de calepinage [C] | mode guillotine (port de RectangleBinPack, domaine public) ; SVGnest (MIT) pour formes libres ; **pas Deepnest (GPL-3)** | réalisme chantier · M · haute |
| Plans et feuilles (`gen`, `scaleSvgs`, `gabHtml`) | améliorable | PDF par `window.print` : l'échelle réelle dépend des réglages d'impression [C] ; impression réelle non validée | jsPDF + svg2pdf.js (MIT) pour gabarits 1:1 en PDF à la taille de la pièce | précision 1:1 · M · moyenne-haute |
| 3D (three.js r170, `v3GL*`, `render3`) | adapté | permutation d'états globaux (`glWith`) fragile [P] | garder three.js | — · — · basse |
| Exports DXF R12 / IFC4 / glTF | adapté | aucune relecture par un lecteur tiers hors IFC [C] | en tests seulement : ezdxf `audit` (MIT), glTF-Validator Khronos (Apache-2.0), `ifcopenshell.validate` | robustesse · S · haute |
| Interface (`uiDlg`, `#md`, `onEdit`) | améliorable | `#md` sans `role="dialog"` ni gestion du focus ; focus non rendu après `dlgEnd` [C] | axe-core (MPL-2.0) en test | accessibilité, marchés publics · S · moyenne |
| Architecture, données, distribution | améliorable (stockage traité en phase 7) | phase 6 : tous les plans dans `localStorage['resa3']` (quota ≈ 5 Mo [P], échec signalé une fois [C]) → **phase 7 : IndexedDB, migration vérifiée, erreurs visibles, conflits signalés (`docs/stockage.md`)** ; 36 Mo chargés à chaque ouverture ; enveloppes ; pas de linter ; seul Chromium testé | IndexedDB (natif) ; Playwright WebKit / Firefox ; ESLint (MIT) + `@ts-check` ; Tauri (MIT / Apache-2.0 : WebView2 sous Windows, WebKit sous macOS) avec modèles OCR en fichiers séparés et ONNX Runtime natif | données, maintenance, distribution · S à M · haute |

## 4. Feuille de route (ordre : gain, précision, effort, commercialisation ; une PR par ligne, aucune réécriture d'ensemble)
1. ~~Plans hors de `localStorage`~~ : **fait en phase 7**.
   - IndexedDB, avec migration non destructive de `resa3` (copie, relecture, comparaison, marque).
   - Copie de secours à la fermeture, refus d'écraser une version écrite ailleurs.
   - Mode de secours annoncé, et sauvegarde ou restauration contrôlée.
   - Restent :
     - le suivi de la sauvegarde externe par fichier ;
     - les essais Firefox / Safari ;
     - la suppression de l'ancien stockage, dans une phase ultérieure et avec l'accord de Kévin.
2. ~~Défauts du plan D~~ : **fait en phase 8** (couloirs des en-têtes, titre reconnu par son échelle, cartouche écarté). Reste `SEG_MAX`.
3. Validateurs tiers dans les tests : ezdxf audit, glTF-Validator, `ifcopenshell.validate`.
4. Suites rapides sous Playwright WebKit et Firefox (non bloquantes d'abord) : prépare Safari et Tauri macOS.
5. Moteur OCR local pour la version Windows (ONNX Runtime natif, multi-fil, DirectML / CUDA ; même contrat) + détection PP-OCRv6 ;
   puis mesure de PP-StructureV3 et, en option GPU, de PaddleOCR-VL-1.6 (sorties rattachées à une boîte, jamais de cote inventée).
6. Mode d'imbrication guillotine, au choix par chantier.
7. Cas de référence de calcul figés (`plateW`, `flecheCP`, Euler de `rxGeo`) ; `filmep` dans `CPMEC` avec fiche fabricant datée ;
   γ tranché par Kévin sur le texte de la norme.
8. ESLint + `@ts-check` ; puis remplacement progressif des enveloppes par des points d'extension (d'abord `gen` / `FS`).
9. Gabarits 1:1 en PDF natif (jsPDF + svg2pdf.js), barre de contrôle 100 mm gardée ; impression réelle à valider.
10. Accessibilité des fenêtres (`#md`, retour du focus) + axe-core en test.
11. ~~HTML produit par la CI~~ : **fait en phase 8**. Livrable construit depuis les sources, non versionné, sans Git LFS. Artefact CI
    `CoffraPlan-<commit>`. Reste, pour la version installable : modèles OCR en fichiers séparés.
