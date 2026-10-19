# CoffraPlan — règles du projet pour Claude

CoffraPlan produit des plans de coffrage bois pour réservations et petits ouvrages (formes rectangulaires, circulaires,
voiles, dalles, poutres, goulottes, formes spéciales) : débit CP et bois, imbrication, gabarits 1:1, 3D, DXF, dossier PDF,
suivi de chantier. L'auteur et propriétaire est Kévin TRINH, conducteur de travaux BTP en France. Il apprend le
développement : il progresse vite mais n'est pas développeur senior.

## Collaboration (à respecter)
- Répondre **en français**, de façon directe et dense, sans flatterie ni remplissage. Structure : contexte → analyse →
  conclusion → action.
- Distinguer **certain / probable / hypothèse**. Ne jamais écrire « vérifié » ou « validé » pour ce qui n'a pas été lu
  ou testé. Corriger Kévin directement quand il se trompe.
- Préférer des solutions concrètes et testables. Quand plusieurs approches existent, les comparer brièvement et
  recommander la meilleure pour son niveau.
- Fin de chaque livraison : ce qui n'a pas été fait ou vérifié, et les risques, en 1 à 2 lignes.
- Clés de signature, jetons, mots de passe : jamais dans le dépôt ni dans la conversation (secrets GitHub uniquement).
- Normes : uniquement des sources légales (AFNOR, Cobaz, éditeurs). Jamais de copie piratée.

## Interdits métier
- Termes interdits dans l'appli, la doc et les tests : « poteaux béton », « flottaison », « fixation anti-flottaison ».
- Pas de collage ou tuilage des gabarits : 1 pièce = 1 page, en mode traceur.
- Le tube carton s'arrête **sous** la poutre ; il ne monte pas jusqu'au haut de la poutre.
- Ne pas modifier un test pour le faire passer, sauf changement voulu, documenté dans le commit et dans CHANGELOG.md.
- Ne pas déclarer validé ce qui n'est pas testé : impression traceur ou papier réelle, DXF dans un vrai AutoCAD,
  Firefox / Safari, tablette réelle, Excel. Seul Chromium est testé automatiquement.

## Architecture
- **`app/CoffraPlan.html` est la seule source** : HTML, CSS et JS vanilla, sans étape de construction ; environ 6 Mo (dont PDF.js ≈ 1,8 Mo et OCR ≈ 2,65 Mo).
  Seule dépendance : **three.js r170** (licence MIT), intégrée telle quelle en fin de fichier dans
  `<script type="text/plain" id="three-src">`, chargée à la première ouverture de la vue 3D (`v3Three`). Ne pas la modifier ;
  pour la mettre à jour, remplacer ce bloc par `build/three.module.min.js` d'une version publiée.
  - Un `<script id="thm">` dans le `<head>` applique le thème avant l'affichage. Un seul `<script>` principal suit.
  - Certaines fonctions sont **redéfinies plus loin** par enveloppe (`{const _f=f;f=function(){…}}`), par exemple
    `gen` et `printAll`. Avant de modifier une fonction, chercher toutes ses définitions (`grep -n "function nom("`).
- Moteur et plans :
  - données : `migr` → `canon` → `checks` (contrôles), `badDims`, `limErr` ;
  - géométrie : `voileGeo`, `manGeo` (mannequin de voile), `rxGeo` (renforts en croix, Euler coefficient 3), `gsGeo`
    (goussets), `gouGeo` (goulotte, avec cache), `bmBuild` (poutres ≤ 7 m en parties égales) ;
  - débit et découpe : `debit` (CP + `R.bois`), `nestPieces` (imbrication), `cpCutPages` ;
  - feuilles : `gen` (feuilles HTML/SVG ; mise en page `PRT.lay` = `full` | `compact` | `views`) ; `hypRows` /
    `hypLine` (hypothèses) ; `fitPrint` (réduit la police si une case déborde).
- Sorties : `gabHtml` (gabarits 1:1), `dxfPlanFile` (DXF R12 en mm, CP-1252, textes compatibles txt.shx via `dxfTxt`),
  `debitCSV`, export XLSX ou ZIP, dossier PDF, 3D (`open3D`, `render3`).
- Interface :
  - fenêtres et messages : `uiDlg` / `uiAlert` / `uiConfirm` / `uiPrompt`, `toast` ;
  - liste des plans : `rnL` ; aperçu : `onEdit` (différé à partir de 300 ms de calcul) ;
  - fonctions avancées : `openSeries`, `showCmp`, `openChm` (mode chantier), `autoControl` ;
  - sauvegarde : `projHash` avec le rappel de sauvegarde.
- Stockage navigateur : clés `resa*` (`resaTheme`, `resaPrint`, `resaFold`, `resaChk`…). Fichier projet :
  `{app:'plans-reservation', v:10, plans, profils, modeles}`. **Ne pas casser la lecture des anciens fichiers** :
  ajouter une migration dans `migr`.
- v2.6 : `CPT` (catalogue CP par âme) et `CPMEC` (modules EN 789 + sources) ; `flecheCP` / `plateW` (flèche des joues,
  boîtes rectangulaires) ; `ENT` / `entBlock` / `openEnt` (cartouche entreprise, clé `ent` du fichier) ; `FH` / `expJ`
  / `impJ` (enregistrement direct File System Access, repli téléchargement) ; `showNote` (note d'hypothèses, VIEW='note').
- v2.7 : poches des poutres en caisson CP dans `beam3`. Banc `tests/t_coh.py` (cohérence croisée) : à garder vert à chaque
  modification du moteur ou de la 3D.
- v2.8 : vue 3D WebGL (`v3GLInit`, `v3GLBuild`, `v3DrawGL`, `v3GLLabels`, `v3GLPick`) sur le même modèle `model3`, même caméra
  (`cam3`, `v3View`) ; repli vectoriel `render3` sans WebGL (`window.V3_NOGL` pour le forcer). `render3` reste utilisé pour les
  feuilles imprimées et le DXF. `plate3` / `gk3` / `n3` : cotes d'une plaque, repère de groupe, compte des pièces.
- v2.9 : pied de feuille hors de la grille (`</div>${ft}</div>`), colonnes `minmax(0,…)` (vue 72 % / tableau 28 % avec `.ps-w2`),
  `fitSvgs` (vues recadrées sur leur dessin), `CUT_PER=2` panneaux par feuille de découpe (aussi `dalCutPages`, récapitulatif) ;
  éclaté : `EX_SPREAD` (écartement depuis le centre), `EX_JOINT` (pièces rattachées décollées de leur paroi), `sep3`
  (séparation résiduelle, groupes = coques) ; 3D : fonds percés (`ExtrudeGeometry` avec trous, `v3GLHole` pour les coques),
  textures (`v3GLTex`), survol (`v3GLHover`), transitions (`v3Preset`).
- v2.10 : échelle normalisée à l'impression — `ESC(t,s)` repère une vue à échelle unique (`data-k` = unités / mm, `data-vk` =
  plan + rang) ; `scaleSvgs` (dans `fitPrint`) régénère le plan via `gen` avec `ESCX.m` (facteur < 1) pour tomber sur une échelle
  de `ECH`, textes inchangés, puis fixe la taille en px ; `unscaleSvgs` rétablit. Réglage `PRT.ech` = `norm` | `fit`. Vues à
  plusieurs échelles, découpes, 3D, courbure amplifiée : sans `ESC`. Feuilles MONTAGE : `glSheets` remplace la vue vectorielle
  (`data-glk`) par une image WebGL (`glSnap`, `glWith` permute `V3D`/`GL3` le temps d'un rendu synchrone, `v3GLFrame` partagé
  avec la vue interactive) ; `glPrint` attend les images avant `window.print`. Règles « écran étroit » en `@media screen`
  (sinon Chrome peut les appliquer à l'impression A4). Dalle : le platelage s'élève en éclaté (plus d'`exMode`).
- v3.0 : exports BIM — `bimModel` (pièces de `model3` regroupées par coque `rg` ou pièce en morceaux `pg`, origine = centre de
  l'emprise), `bimSplit` (tronçons du débit : faces enregistrées `s.jw`, phase des joints cintrés `R.ja` de `jointGeo`),
  `bimTags` (repères), `bimGeo` / `bimVol` / `bimQty` / `bimInfo` ; `glbFile` (glTF binaire, m, Y vers le haut), `ifcFile`
  (IFC4 STEP, mm, GlobalId déterministes `ifcGuid`), `expBim` (carte Export, vue 3D). Cotes d'implantation : `axImpl` (axes X / Y
  en bleu) et `sgn` (cotes signées). Banc `tests/t_v30.py` (ifcopenshell).
- Module d'import de plans : `modules/import/` — lecteur (A, + `dxf.js`), détecteur (B), adaptateur (C), fenêtre « Importer un
  plan DXF » (D, `fenetre.js`, fonctions `dxi*`, état `DXI`) ; contrat et cartographie dans `modules/import/README.md`. Espace
  de noms `CPI`. A et B sans DOM ni moteur ; C reçoit `migr` / `canon` / `limErr` / `checks` / `badDims` en paramètre.
  **Intégré au HTML** dans le bloc généré `<script id="cpi-src">` : modifier les sources puis `python modules/import/assembler.py`
  (`--check` dans `tests/syntax.sh` et t_dxf_ui) ; ne jamais éditer ce bloc à la main. Provenance d'un plan importé : clé
  optionnelle `origineImport` (métadonnée, jamais lue par le moteur), gardée par `addP` (mise à jour) et `fixAllPlans`,
  retirée par `dupP`. Bancs `tests/t_import.py`, `t_dxf.py`, `t_dxf_ui.py` (interface réelle).
  Nomenclatures de réservations : `nomenclatures.js` (`analyser`, `associer`, `cotes`, `provenance`) sur les textes / traits
  relevés par `dxf.js` (espaces Objet / présentations, blocs, ACAD_TABLE) ; vue « Nomenclature » de la fenêtre (`dxn*`) ;
  `origineImport.type = 'nomenclature'`. Toutes les lignes proposées, aucun filtre. Banc `t_nomenclature.py`
  (DXF fictifs de `tests/dxf_nomenclatures.py`).
  Import PDF : `pdf.js` (`CPI.pdf.lire` / `rendre` / `fermer`) sur **PDF.js 6.4.299** (Apache-2.0, build legacy) copié tel quel
  dans `modules/import/vendor/pdfjs/` et recopié par `assembler.py` dans `<script type="text/plain" id="pdfjs-src">` et
  `id="pdfjs-worker-src"` (empreintes SHA-256 vérifiées ; ne pas éditer ces blocs). Une page PDF = un espace, coordonnées en
  points ; aucune cote tirée du dessin. Fenêtre unique « 📥 Importer un plan » (DXF + PDF) ; PDF : aperçu, zone, saisie
  assistée (`dxp*`). Banc `t_pdf.py` (PDF fictifs de `tests/pdf_fictifs.py`).
  OCR des nomenclatures en tracés ou numérisées : `ocr.js` (`CPI.ocr.lireZone` / `grille` / `versNomenclature`) sur
  **Tesseract.js 7.0.0** (cœur simd-lstm, modèle fra best_int ; Apache-2.0) copié dans `modules/import/vendor/tesseract/`
  (README : empreintes, mise à jour) et recopié par `assembler.py` dans les blocs `tess-*` (ne pas les éditer) ; worker blob,
  aucune requête réseau. Rendu de zone par `CPI.pdf.rendreZone`, tableau par `nomenclatures.analyser` (pas de 2e moteur),
  grille de vérification `dxo*`, `origineImport.type = 'ocr'` + clé `ocr` (brut, confiance, corrigé). Banc `t_ocr.py`
  (PDF fictifs de `tests/pdf_ocr_fictifs.py` : textes en contours, scan ; fontTools + police Liberation / DejaVu).
- Version affichée : élément `#appVer` (« v3.0 »). Les tests t_ux et t_v30 vérifient ce numéro.

## Décisions actées (ne pas changer sans l'accord de Kévin)
- Palette : joues CP `#EBD9B4`, fond inférieur `#B4532A`, fond supérieur `#E8A92E`, goussets `#F26B1D`, cloisons et
  montants CP `#C98BA0`, bois `#6B4423`, tubes carton `#8E8A84`, poches `#D7263D`, PVC `#4F5358`, béton `#C4C4C4`.
  Mêmes couleurs en 2D, en 3D, dans la légende et sur la fiche.
- Poussée : hydrostatique complète 25 kN/m³ × h (EN 1991-1-1).
- CP par défaut : filmé phénolique bouleau 18 mm (EN 636-3, classe 3). Flèche des joues calculée pour les boîtes
  rectangulaires seulement (critère portée / 300, réglable par chantier) ; autres formes : « non vérifiée », c'est écrit.
  Toute nouvelle valeur de rigidité doit citer sa source (fiche fabricant datée) dans `CPMEC`.
- Mannequin de voile : au moins un renfort perpendiculaire au plus grand côté (R03 → 1 montant).
- Cadre de joint 50×50 du parallélépipède : choix de conception, à valider sur chantier.
- Impression par défaut : « Plan pleine page » ; feuilles annexes décochées ; sommaire « Jamais » (option « Si > 5
  feuilles »).
- Règles marquées « Règle de l'appli — à valider » dans `hypRows` : goussets, raidisseurs de poutre… Elles attendent la
  relecture d'un professionnel. Ne pas les présenter comme normatives.

## Tests (Playwright Python + Chromium)
```
pip install -r tests/requirements.txt && python -m playwright install chromium
python tests/run.py -j 4              # suites rapides, environ 2 min
python tests/run.py complet -j 4      # + avant/après, revue de 420 plans, gabarits (long)
python tests/run.py t_v25             # une suite
sh tests/syntax.sh                    # syntaxe JS
```
- `tests/lib.py` (`open_app`, `Suite`) teste `app/CoffraPlan.html`. Une autre version se teste avec la variable
  `APP=chemin`.
- **t_avap** (avant / après) donne les mêmes entrées à la version git `AVAP_REF` (défaut `HEAD`) et au fichier de travail,
  puis compare débit, feuilles, DXF et CSV. Le lancer avant chaque commit qui touche au moteur. Tout écart doit être
  voulu, et expliqué dans t_avap et CHANGELOG.md.
- Chaque nouvelle version ajoute sa suite `tests/t_vXY.py`, qui vérifie ce qu'apporte la version.
- `tests/ref/v18.html` est une référence figée pour t_forme. Ne pas la modifier.

## Version, livraison
1. Fixer le numéro dans `#appVer`, dans t_ux et dans CHANGELOG.md (section en tête : demandes, fait, écarts voulus,
   tests, non validé).
2. Lancer `python tests/run.py complet -j 4` : tout doit passer.
3. Commit, puis tag `vX.Y` poussé : GitHub Actions publie une *Release* avec `CoffraPlan_vX.Y.html` et le mode d'emploi
   PDF.
- Mode d'emploi : `python docs/manuel/build.py` (captures sur l'appli du dépôt, puis PDF). Mettre à jour
  `docs/manuel/manuel.html` à chaque fonction visible ajoutée. `{{VERSION}}` et `{{MOIS}}` sont remplacés automatiquement.

## À faire avant toute diffusion commerciale
- Noms de chantiers réels retirés de l'appli en v2.6 ; l'historique git les contient encore : garder ce dépôt privé.
- Rédiger la note d'hypothèses complète à partir de `hypRows` et de la revue des règles du code ; la faire relire par
  un chef coffreur ou un bureau d'études.
- Appli installable (Tauri) avec sauvegarde en fichiers, licence, version Light : voir docs/feuille-de-route.md.
