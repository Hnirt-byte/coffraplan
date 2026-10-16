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
- **`app/CoffraPlan.html` est la seule source** : HTML, CSS et JS vanilla, sans dépendance ni étape de construction ;
  environ 600 Ko et 5 500 lignes.
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
- Version affichée : élément `#appVer` (« v2.5 »). Le test t_ux vérifie ce numéro.

## Décisions actées (ne pas changer sans l'accord de Kévin)
- Palette : joues CP `#EBD9B4`, fond inférieur `#B4532A`, fond supérieur `#E8A92E`, goussets `#F26B1D`, cloisons et
  montants CP `#C98BA0`, bois `#6B4423`, tubes carton `#8E8A84`, poches `#D7263D`, PVC `#4F5358`, béton `#C4C4C4`.
  Mêmes couleurs en 2D, en 3D, dans la légende et sur la fiche.
- Poussée : hydrostatique complète 25 kN/m³ × h (EN 1991-1-1). Flèche du CP **non vérifiée** ; c'est écrit sur les
  feuilles.
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
- Retirer les noms de chantiers réels de l'appli, par exemple le texte d'aide « Ex: STEP SCEY ». L'historique git les
  contient aussi : garder ce dépôt privé.
- Rédiger la note d'hypothèses complète à partir de `hypRows` et de la revue des règles du code ; la faire relire par
  un chef coffreur ou un bureau d'études.
- Appli installable (Tauri) avec sauvegarde en fichiers, licence, version Light : voir docs/feuille-de-route.md.
