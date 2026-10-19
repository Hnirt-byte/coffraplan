# Module d'import de plans

État : **intégré à l'appli** (fenêtre unique « Importer un plan » : DXF et PDF). Lecteur DXF ASCII (`dxf.js`), détecteur, adaptateur et
fenêtre sont des sources séparées (plus `nomenclatures.js`), assemblées dans `app/CoffraPlan.html` (bloc `<script id="cpi-src">`, § 3). PDF à texte
extractible pris en charge (`pdf.js`, § Import PDF) ; pas de décodeur IFC. Bancs : `tests/t_import.py` (contrat), `tests/t_dxf.py` (vrais DXF écrits par ezdxf),
`tests/t_dxf_ui.py` (interface réelle : lecture, aperçu, confirmation, création, provenance, annulation, hors connexion).

| Fichier | Composant | Dépend de |
|---|---|---|
| `lecteur.js` | A. Lecteur de plan : fichier source → document normalisé | rien |
| `dxf.js` | Décodeur DXF ASCII, inscrit dans `CPI.lecteur.DECODEURS.dxf` (charger après `lecteur.js`) | `lecteur.js` |
| `pdf.js` | Lecteur PDF (`CPI.pdf.lire` asynchrone, `rendre`, `fermer`) : pages → textes et traits par page (§ PDF) | PDF.js 6.4.299 (`vendor/pdfjs`, blocs du HTML) |
| `detecteur.js` | B. Détecteur : document normalisé → réservations **potentielles** | rien |
| `nomenclatures.js` | B'. Nomenclatures de réservations : textes et traits du DXF → tableaux, lignes, rapprochement avec les candidats de B (§ 5) | rien |
| `adaptateur.js` | C. Adaptateur : réservation **confirmée** → plan CoffraPlan contrôlé par le moteur | moteur reçu en paramètre |
| `fenetre.js` | D. Fenêtre « Importer un plan » (DXF, PDF) : fichier → A → B → choix de l'utilisateur → C → ajout des plans | l'appli (appelée au clic, jamais au chargement) |
| `assembler.py` | Assemblage des 7 sources JavaScript dans le HTML ; `--check` : échoue si le HTML diffère | Python, bibliothèque standard |

A, B et C sont du JS vanilla (ES2017), sans DOM ni stockage, et s'enregistre dans un seul espace de noms global
`CPI` (`CPI.lecteur`, `CPI.detecteur`, `CPI.adaptateur`). A et B tournent dans une page vide (vérifié par t_import).

## 1. Cartographie utile à l'intégration (lue dans `app/CoffraPlan.html`, v3.0)

Chaîne d'un plan : **saisie** `coll()` (formulaire → objet plan, `v:12`) → **enregistrement** `addP()` (contrôles puis
`P.push`, `svP()` → `localStorage.resa3`) → **calcul** `canon(migr(d))` → `limErr` / `checks(d,g)` / `badDims` →
`debit(d,g)` → `model3(d,R)` / `gen(d)` → sorties (`dxfPlanFile`, `ifcFile` → `bimModel`, `glbFile`, `debitCSV`…).

| Fonction | Rôle | Couplage relevé | Usage par le module |
|---|---|---|---|
| `migr(d)` (+ `migr11`) | met à niveau un ancien plan (→ v12) | pur | appelée par C |
| `canon(d0)` (+ `canonExt`) | cotes saisies → cotes de calcul (ép. CP, Ø int/ext) | pur | appelée par C |
| `limErr(d)` | bornes du tableau `LIM` | `fmtLim` lit `data-u` du champ dans le DOM (libellé d'unité seulement) | appelée par C |
| `checks(d,g)` | cohérence (⛔ err / crit / ⚠ warn) ; `g` = `voileGeo(d)` pour un voile, sinon `null` | pur | appelée par C |
| `badDims(W)` | vrai si une alerte `err` | pur | appelée par C |
| `debit(d,g)`, `model3(d,R)`, `gen(d)` | débit, 3D, feuilles | `gen` enveloppée 2 fois (l. ≈ 5166 `FS`, ≈ 6026 `ESCX`) | **non** appelées par le module (le test vérifie seulement qu'un plan converti passe) |
| `coll()` / `setForm0()` | formulaire ↔ plan | enveloppées (l. ≈ 5179-5180, champ `txt`) | `coll()` fournit le **modèle** de plan |
| `serAnalyse` / `serCreate` (`openSeries`) | série de plans depuis un tableau collé : forme + cotes → modèle `coll()` → `limErr` / `checks` → aperçu ✓ / ⚠ / ⛔ → création sur confirmation | DOM (formulaire, fenêtre) | **modèle à suivre** pour l'interface d'import |
| `loadText` / `impJ` | lecture d'un projet JSON (`migr` sur chaque plan) | DOM, remplace `P` | non touché |
| `projJson` | sauvegarde `{app:'plans-reservation', v:10, plans, profils, modeles, ent}` | — | non touché |

Champs d'un plan produits par l'adaptateur (mêmes clés que `coll()`) : rect / carré (+ fond) `L`, `l`, `h` (mm, `l = L`
pour un carré) ; fourreau `circ` `D` (Ø extérieur du tube = Ø du vide), `h`, `mat` ; communs `ch`, `ouv`, `ref`, `ind`,
`nb`, `mont`, `forme`, `cp`, `ep`, `date`, options de la forme. **Aucune clé nouvelle** : la provenance reste à côté du plan.

Points d'intégration les moins risqués, du plus sûr au moins sûr :
1. **Fenêtre séparée, calquée sur `openSeries`** : nouveau bouton, nouvelle fenêtre ; les plans confirmés sont ajoutés par
   le même chemin que `serCreate` (`P.push`, `svP`, annulation par toast). Aucun code existant modifié hors d'un bouton.
2. Modèle de plan = `coll()` après `el('iForme').value=f; updF()` sous `_loading`, puis restauration du formulaire
   (exactement ce que fait `serAnalyse`).
3. À éviter : toucher `addP`, `loadText`, `migr` ou `gen` pour l'import.

## 2. Contrat de données

### A → document normalisé (`CPI.lecteur.lirePlan(source)`)
`source = {format:'normalise'|'dxf'|'ifc'|'pdf', nom, contenu}`. Seul `normalise` est lu aujourd'hui ; les autres renvoient
`{ok:false, raison:'format_non_pris_en_charge'}`. Un décodeur futur s'inscrit dans `CPI.lecteur.DECODEURS[format]` et doit
rendre ce document :

```
{ format, fichier,            // provenance
  unite: 'mm'|'cm'|'m'|null,  // null = le fichier ne la donne pas (DXF $INSUNITS = 0) : jamais devinée
  entites: [
    {id, calque, type:'polyligne', points:[[x,y],…], ferme:bool, h?},  // segments droits uniquement
    {id, calque, type:'cercle', centre:[x,y], r, h?},
    {id, calque, type:'autre', nature?} ] }                             // tout le reste (arc, ellipse, spline, polyligne à arcs…)
```
`id` = identifiant source (handle DXF, GlobalId IFC…), unique ; `calque` = calque ou classe source ; `h` = hauteur si le
format la porte (IFC), absente en 2D. Coordonnées et cotes dans `unite`. `verifierDocument` refuse : unité inconnue, `id`
absent ou en double, type inconnu, cercle sans centre / rayon, points illisibles → `{ok:false, raison:'document_invalide', erreurs}`.
Règle pour les décodeurs : une polyligne à arcs (bulge) devient `autre`, jamais une polyligne aplatie.

### Décodeur DXF (`dxf.js`)
| Élément DXF | Document normalisé |
|---|---|
| `$INSUNITS` 4 / 5 / 6 | `unite` `mm` / `cm` / `m` ; 0 ou absent (toujours absent en R12) → `null` ; pouces, pieds… → fichier refusé |
| `$ACADVER` | `version` (ex. `AC1015`) |
| table `LAYER` + calques des entités | `calques` (liste des noms) |
| handle (code 5) | `id` ; sans handle (R12 sans `$HANDLING`) → `#n` (rang dans ENTITIES) |
| calque (code 8) | `calque` (`0` si absent) |
| `LWPOLYLINE`, `POLYLINE` + `VERTEX` … `SEQEND` (2D) | `polyligne` ; `ferme` = drapeau 1, ou dernier sommet exactement égal au premier |
| `CIRCLE` | `cercle` (`centre`, `r`) |
| polyligne à arcs (code 42 ≠ 0) | `autre`, nature « … avec arcs » |
| polyligne avec largeur non nulle (LWPOLYLINE 40 / 41 / 43 ; POLYLINE 40 / 41 de l'en-tête ou d'un VERTEX) | `autre`, « … avec largeur non nulle » (la ligne médiane n'est pas le contour du vide) |
| POLYLINE lissée (70 : bit 2 courbe ajustée, bit 4 spline ; VERTEX 70 : bits 1, 8, 16) | `autre`, « POLYLINE lissée (courbe ajustée ou spline) » |
| extrusion (0,0,−1) (objet en miroir) | X changé de signe : coordonnées dans le repère général |
| autre extrusion, POLYLINE 3D / maillage | `autre` (hors du plan XY) |
| `INSERT` | `autre` « bloc non décomposé » (les blocs ne sont pas explosés) |
| tout autre type (LINE, ARC, TEXT, HATCH, DIMENSION…) | `autre`, nature = type DXF |

Refus explicites (`document_invalide` avec le message) : fichier vide, DXF binaire, code de groupe illisible (fichier non
DXF), paires incomplètes ou fin `EOF` absente (fichier tronqué), section `ENTITIES` absente, unité non métrique, valeur
numérique illisible, `POLYLINE` sans `SEQEND`. `entites` = section `ENTITIES` seulement (espace Objet et présentation active),
chacune avec `espace` (`objet` | `papier`) et `presentation` (nom lu par BLOCK_RECORD → LAYOUT ; `null` en R12).

En plus, pour les nomenclatures (champs facultatifs du document) :
| Champ | Contenu |
|---|---|
| `presentations` | noms des présentations (objets LAYOUT, sans « Model ») |
| `textes` | `{id, calque, espace, presentation, nature, texte, x, y, h, w, rot, bloc?, fleches?}` : TEXT, ATTRIB (visible), MTEXT (une entrée par ligne `\P`, mise en forme retirée), MULTILEADER (texte + pointes de flèche) ; `%%c` → Ø, `%%d` → °, `%%p` → ± ; `x, y` = centre estimé (largeur ≈ 0,6 h par caractère) ; flèche d'un LEADER rattachée à son texte (code 340) |
| `traits` | segments droits (LINE, côtés des polylignes sans arc) : `{calque, espace, presentation, a, b}` |
| `signalements` | limites rencontrées (ACAD_TABLE sans bloc de rendu, bloc introuvable, MINSERT, fichier très chargé…) |
Sources : `ENTITIES`, présentations non actives (`BLOCKS` `*Paper_Space<n>`), contenu des blocs `INSERT` (point de base, échelle,
rotation, miroir ; calque 0 → calque de l'insertion ; 8 niveaux au plus) et des `ACAD_TABLE` par leur bloc de rendu `*T…`
(codes 2, 10/20, 11/21). Coordonnées dans le repère de l'espace qui contient l'objet : jamais mélangées entre espaces.
Encodage : le texte est reçu déjà décodé ; l'interface devra lire les R12 en CP-1252 et les R2007+ en UTF-8.

### Décisions de Kévin (18/10/2026, relecture de la PR #1)
- Rectangle → `rect`, ou `carre` si les côtés sont égaux ; cercle → `circ` (fourreau).
- Les cotes du contour (le vide à réaliser) = encombrement **extérieur** de la boîte ou du fourreau dans CoffraPlan.
- Ne **jamais** ajouter automatiquement deux épaisseurs de CP.
- Confirmation explicite de l'utilisateur avant toute création d'ouvrage (`confirme:true`).
- Provenance hors du plan pour l'instant ; elle devra devenir **persistante** avant l'intégration fonctionnelle : fichier
  source, calque, identifiant, coordonnées, orientation et indice (l'indice n'existe pas en DXF : il viendra de la saisie).
  À vérifier ensuite : provenance conservée après modification du plan via `coll()`.
- 19/10/2026 (demande d'intégration) : provenance **dans le plan**, clé optionnelle `origineImport`, enveloppe JSON inchangée ;
  hauteur commune facultative, modifiable par ligne ; formes avec fond seulement sur choix explicite.
- Pas de refactorisation supplémentaire du moteur existant.

### B → candidats (`CPI.detecteur.detecter(doc, {tol})`)
Un candidat par entité, dans l'ordre :
```
{ id:'R1', type:'rect'|'circ'|null, statut:'a_confirmer'|'non_pris_en_charge',
  unite,                                  // celle du document, sans conversion
  source:{fichier, format, calque, id},   // provenance
  geometrie,                              // copie intégrale de l'entité source
  centre:[x,y]|null,
  dims: {L, l, angle} | {D} | null,       // L = grand côté, l = petit côté, angle du grand côté (°, 0 ≤ a < 180)
  h: nombre|null, manquants:['h','unite'…], remarques:[…] }
```
Rectangle reconnu : contour fermé de 4 sommets (5 si refermé), côtés opposés et diagonales égaux, angle droit au premier
sommet (écarte le quadrilatère croisé), à `tol` près (0,5 % de la diagonale). Côtés égaux : remarque « carré potentiel ». Cercle : `r > 0`. Tout le reste : `non_pris_en_charge`, avec la raison et la géométrie conservée.
**B ne produit jamais de statut validé** : une forme ambiguë (quadrilatère presque rectangle) reste non prise en charge.

### C → plan (`CPI.adaptateur.versPlan(candidat, confirmation, ctx)`)
- `confirmation = {confirme:true, forme?, h?, unite?, ref?, nb?}` — `h` en mm (saisie CoffraPlan) ; `confirme` doit valoir
  exactement `true`.
- `ctx = {moteur:{migr, canon, limErr, checks, badDims}, modele}` — fonctions de l'appli passées en paramètre ; `modele` =
  plan de la forme visée (chantier, CP, options en sont repris).
- Forme par défaut : `circ` pour un cercle ; `carre` si |L − l| < 0,5 mm, sinon `rect`. Formes permises : rect → `rect`,
  `carre`, `rect_fond`, `carre_fond` ; cercle → `circ`. Cotes converties en mm, arrondies à 0,01 mm.

| Résultat | Quand |
|---|---|
| `{ok:true, plan, provenance, alertes}` | plan accepté par `limErr` et `checks` ; `alertes` = avertissements ⚠ |
| `non_confirme` | pas de `confirme:true` |
| `non_pris_en_charge` | candidat non reconnu (raison du détecteur dans `messages`) |
| `a_completer` + `manquants` | `h` ou `unite` absents (ni dans le fichier ni dans la confirmation) |
| `forme_incompatible` | ex. cercle → rect, rectangle 1200 × 600 → carré |
| `modele_manquant` | pas de modèle, ou modèle d'une autre forme |
| `invalide` + `messages` + `plan` | le moteur refuse les cotes (bornes `LIM`, alertes ⛔) |

`provenance = {fichier, format, calque, id, candidat, unite_source, unite, centre, dims_source, h_saisie}`. C ne modifie ni
`P`, ni le stockage, ni le modèle : il renvoie un nouvel objet ; l'enregistrement reste une action de l'utilisateur.

## Nomenclatures de réservations (`nomenclatures.js`, fenêtre `dxn*`)
`CPI.nomenclatures.analyser(doc)` → `{nomenclatures, ecartes, signalements}`, par espace (Objet, chaque présentation) :
1. **En-tête** : textes sans chiffre portant un mot-clé de colonne (Repère / Réf. / N°, Désignation, Type / Élément, Ouverture /
   Trémie / Dimensions / l×h, Diamètre / Ø, DN / Réseau, Niveau / Altimétrie / NGF / Hauteur / dalle, Angle / Orientation,
   Observations, Lot / Entreprise…) alignés (± 1 h) ; au moins 3 textes et 2 sortes ; coupé aux écarts > 30 h et au 2e « repère ».
2. **Bande d'en-tête** : entre deux traits horizontaux de la grille, sinon textes à mot-clé ou « (mm) », « l×h » à ± 1,3 h.
3. **Colonnes** : traits verticaux de la grille (entre les extrémités du trait qui borde l'en-tête) ; sans grille, entre deux titres
   au milieu du plus large intervalle libre de textes. **Lignes** : bandes de la grille ; sans grille, une ligne par repère, les
   lignes de texte sans repère rattachées au repère le plus proche. Côté des lignes : celui qui en a le plus (en-tête en bas admis).
4. **Nature** (en-tête + titre, jamais les lignes) : réservations (mots trémie, fourreau, ouverture, carottage… et colonnes
   ouverture / niveau / angle / réseau / diamètre) ; aciers (acier, HA, poids, façonnage…) ; autre (indice, modification…).
   Seules les nomenclatures de réservations sont proposées ; les autres tableaux vont dans `ecartes` avec la raison.
5. **Lignes** : toutes gardées : `{id, rang, ids, calques, cellules (textes bruts), repere, description, type, observations, lot,
   quantite, niveau, angle, reseau, ouverture, dims, a_verifier}`. `dims` (unité du tableau, non convertie) : colonne ouverture
   d'abord (`650x800` → `{type:'rect',a:650,b:800}`, `Ø300` → `{type:'circ',D:300}`) ; DN, cote seule, SO / à définir / « / » →
   `null` + motif ; colonne « Diamètre » ou Largeur + Hauteur → cote proposée « à confirmer ». Niveau et angle : texte seulement.
6. **Qualité** : `bonne` (grille complète, tous les repères, toutes les colonnes reconnues), `à vérifier`, `faible`, et motifs.

`associer(noms, candidats, doc, {uniteDessin, unites, exclus})` : repères du dessin (TEXT, MTEXT, attributs, lignes de repère ;
textes des tableaux exclus) normalisés (`D03` = `D3` = `d 3`), contour à moins de 4 h du texte ou d'une pointe de flèche,
cotes comparées en mm (1 % ou 2 mm). États : `trouvee` (un seul contour, cotes identiques, repère non numérique : rattaché
d'office, modifiable), `probable` (un contour, cotes différentes ou non comparables ; ou repère absent et une seule géométrie de
mêmes cotes), `multiple` (plusieurs contours : vue, coupe, détail ; ou plusieurs géométries de mêmes cotes), `absente`. Espace
Objet seulement : un repère d'une présentation est signalé, la fenêtre de présentation (VIEWPORT) n'est pas interprétée.

Fenêtre : onglet « Nomenclature des réservations » par défaut (sinon comportement inchangé) ; aucune ligne cochée d'office ;
cotes (mm), forme, hauteur, référence (repère du tableau ou automatique), géométrie modifiables ; création par `versPlan`
(`candidat()` → candidat au format de B). Géométrie rattachée : retirée de l'onglet « Géométries du dessin ».
Provenance (`provenance()`) : `{fichier, format, type:'nomenclature', espace, presentation, calque, id (géométrie | null),
nomenclature, titre, ligne, rang, repere, ids, textes:{titre de colonne: cellule}, unite_source, unite, dims_source,
geometrie:{id, calque, candidat, statut:'trouvee'|'choisie', unite (unité du dessin de centre et dims_source), centre, dims_source} | null, choix:{forme, cotes, ref ('' =
automatique), unite_tableau}, corrige:['cotes','ref'], a_verifier, h_saisie, indice, date}`.

## Import PDF (`pdf.js`, fenêtre `dxp*`)
- Bibliothèque : PDF.js 6.4.299 (Mozilla, Apache-2.0), build « legacy » copié sans modification dans `vendor/pdfjs/`
  (empreintes SHA-256 vérifiées par `assembler.py`) et recopié dans le HTML (`<script type="text/plain" id="pdfjs-src">`,
  `id="pdfjs-worker-src"`, ≈ 1,8 Mo : HTML ≈ 3,3 Mo). Chargé à la première ouverture d'un PDF (module importé par URL blob).
  Worker : le module est transformé à la volée en script classique (`import.meta.url` → `self.location.href`, `export`
  final retiré) car une page ouverte en `file://` ne peut pas lancer un worker de module ; repli : PDF.js dans la page.
  Options : polices standard, CMap, wasm et ICC désactivés (`null`) : aucune requête réseau (vérifié par t_pdf).
- Document normalisé : `format:'pdf'`, `unite:null`, `entites:[]` (aucune géométrie proposée : une longueur sur la page
  n'est pas une cote réelle), `presentations:['Page 1'…]`, `pages:[{n, w, h (points, page affichée), rotation, textes,
  textesIllisibles, chemins, segments, images, nature}]`, `textes` (`espace:'papier'`, `presentation:'Page n'`, `page`, `x, y`
  centre, `h` ≈ 0,7 corps, `w`, `rot`) et `traits` horizontaux / verticaux (`page`) ; coordonnées en points, Y vers le haut,
  rotation de page et matrices appliquées. Morceaux de texte voisins sur une même ligne de base réunis.
- Nature d'une page : `texte` (≥ 3 textes), `mixte` (plus de 50 tracés par texte : textes probablement vectorisés en
  partie), `vectoriel` (tracés, < 3 textes), `image` (image seule : numérisation), `vide`. Rapport dans la fenêtre :
  « lecture automatique : n ligne(s) » ou « aucune nomenclature lisible automatiquement : saisie assistée ».
- Nomenclatures : `nomenclatures.analyser` tel quel, une page = un espace (jamais de mélange entre pages) ; `N.page`,
  `N.format`. Rapprochement géométrique : aucun pour un PDF.
- Fenêtre : onglets « Nomenclature » et « Aperçu du plan » (pages, zoom, tableaux reconnus encadrés, ligne encadrée par
  « p. N ↗ »). Zone : cliquer-glisser, « Analyser la zone » (textes et traits de la zone, traits coupés au bord) : les tableaux
  lus automatiquement qui partagent des textes avec la zone sont remplacés (`N.id` = `Z1`…, `N.zone`) ; rien n'est ajouté si la
  zone ne donne pas de nomenclature de réservations. Saisie assistée : lignes tapées en consultant la page (`N.saisie`, `N.id`
  = `S<page>`), mêmes contrôles et même création ; ✕ retire une ligne saisie.
- Provenance (en plus des clés DXF de `provenance()`) : `format:'pdf'`, `type:'nomenclature'|'saisie'`, `page`, `zone`
  `{page, x0, y0, x1, y1, unite:'pt'}` (zone choisie, sinon cadre du tableau ; ligne saisie : zone choisie au moment de la
  saisie). Le PDF n'est jamais stocké.
- Limites : textes tournés ignorés pour les tableaux (comme en DXF) ; tableau continué sur une autre page sans en-tête
  répété : non relié (saisie assistée) ; PDF protégé par mot de passe refusé ; pas d'OCR ; images JPEG 2000 / JBIG2 et
  textes CJK mal rendus dans l'aperçu (décodeurs non intégrés) ; testé dans Chromium seulement.

## 3. Fichiers séparés et HTML autonome (en place)

- `python modules/import/assembler.py` remplace le bloc `<script id="cpi-src">…</script>` de `app/CoffraPlan.html` (placé
  avant le `<script>` principal) par `lecteur.js`, `dxf.js`, `detecteur.js`, `nomenclatures.js`, `adaptateur.js`, `fenetre.js`, dans cet ordre,
  chacun précédé de son nom. Résultat déterministe (fins de ligne normalisées), bibliothèque standard Python seulement.
- `--check` échoue si le bloc diffère des sources : lancé par `tests/syntax.sh` (étape « Syntaxe » de la CI) et par t_dxf_ui.
  Une source modifiée sans réassemblage fait donc échouer la CI.
- Le reste du HTML s'édite toujours à la main ; l'appli reste un fichier unique, hors connexion, sans CDN ni serveur.

## Intégration dans l'appli (fenêtre D)
- Accès : bouton `#bDxi` « 📥 Importer un plan » (barre du haut, carte Plans, accueil). Format reconnu au contenu (`%PDF-`,
  DWG `AC10…` refusé avec un message, IFC refusé) puis à l'extension ; glisser-déposer sur la fenêtre. `impJ`
  (chargement d'un projet .json) n'est pas touché.
- Lecture du fichier : UTF-8 strict, sinon CP-1252 (R12 à R2004). Unité absente → choix mm / cm / m exigé avant toute création.
- Modèles de plan par forme : `coll()` après changement de forme et `applyProf(true)`, avec le chantier et l'ouvrage de la
  fenêtre, puis formulaire, plan affiché (`EI`) et historique rétablis (méthode de `serAnalyse`).
- Chaque ligne passe par `versPlan` (contrôles `limErr` / `checks` / `badDims`) ; statuts : ✓ prêt, ⚠ prêt avec alertes,
  « à compléter » (unité, hauteur, chantier), ⛔ refusé (moteur, référence déjà utilisée dans l'ouvrage ou en double dans le
  lot), non pris en charge (liste à part, jamais créé).
- Création (chemin de `serCreate`) : seulement les lignes cochées « Créer », prêtes et sur un calque coché ; `P.push` (aucun
  plan remplacé), références vides attribuées par `nextRef` en sautant celles du projet et celles saisies dans le lot (`dxiRefs`, contrôle
  final : un doublon annule la création), `planUid`, `svP`, profils, liste ; « Annuler » dans le message retire
  le lot et rétablit l'état d'avant.
- Provenance (décision de Kévin, 19/10/2026) : `plan.origineImport = {fichier, format, calque, id, candidat, unite_source,
  unite, centre, dims_source:{L, l, angle} | {D}, h_saisie, indice, date}` ; `unite_source` = unité du fichier (`null` si
  absente), `unite` = unité retenue ; `indice` = indice du plan source saisi. Métadonnée seulement : le moteur ne la lit pas.
  Enveloppe du fichier projet inchangée. Gardée par `addP` en mise à jour et par `fixAllPlans` ; absente d'un plan créé par
  « Nouveau » ou `dupP` (copie indépendante). Le contenu du DXF n'est jamais stocké.

## 4. Intégration progressive proposée

1. **Fait** : contrat, squelette, banc `t_import` sur objets fictifs.
2. **Fait** : lecteur DXF (R12 / 2000+ ASCII) : `LWPOLYLINE`, `POLYLINE`, `CIRCLE`, `$INSUNITS`, calques ; arcs → `autre`.
   Testé sur des DXF produits par `ezdxf` (déjà dans `tests/requirements.txt`) puis sur de vrais plans de Kévin.
3. **Fait** : bloc `cpi-src`, `assembler.py`, `--check` en CI.
4. **Fait** : fenêtre « Importer un plan DXF » (aperçu, filtre par calque, hauteur, forme, confirmation, création, annulation).
5. **Fait** : provenance dans le plan (`origineImport`, clé optionnelle : pas de migration nécessaire, les anciens plans n'en ont pas).
6. IFC (`IfcOpeningElement`, hauteur connue), puis PDF vectoriel après étude.

## Protocole de validation sur un vrai plan de chantier (à faire, hors Git)
1. Kévin choisit un plan réel en DXF ASCII ; le fichier reste sur son poste (dossier hors dépôt, jamais commité, jamais
   joint à une PR).
2. Lecture locale : page vide + `lecteur.js`, `dxf.js`, `detecteur.js` (comme `t_dxf`), fichier lu en texte ; noter
   seulement des comptes : version, unité, nombre de calques, d'entités par type, de candidats rect / circ / non pris en charge.
3. Contrôle croisé dans AutoCAD sur 5 à 10 réservations : cotes, centre, orientation, calque, handle (`LIST`).
4. Relever les cas manqués (blocs, arcs, contours non fermés, réservations dessinées en lignes) ; chaque cas devient un
   DXF **fictif** reproduit avec ezdxf dans `t_dxf.py`, sans coordonnées ni noms du plan réel.
5. Compte rendu dans le fil de projet : uniquement les comptes et les écarts, aucun nom de chantier ni extrait du plan.

## Essai local sur le plan réel de la nomenclature (23 lignes, présentation)
Fichier confidentiel : il reste sur le poste de Kévin, hors du dépôt.
1. `git pull` puis `pip install -r tests/requirements.txt` (une fois).
2. `python tests/essai_plan_reel.py "<chemin du DXF>" --attendu 23` : bilan **anonyme** (comptes seulement : nombre de lignes,
   cellules remplies par colonne, cotes lues, états des rapprochements, tableaux écartés). Résultat attendu : `Total : 23 ligne(s)`,
   code de sortie 0. Le bilan peut être recopié dans le fil ; rien d'autre du plan.
3. Puis dans CoffraPlan : « 📥 Importer un plan », onglet Nomenclature : comparer les 23 lignes au tableau d'AutoCAD (cellules,
   cotes proposées, motifs « à vérifier »).
4. Écart constaté : le décrire sans contenu du plan (ex. « colonne Ouverture lue vide sur 3 lignes, cellules en MTEXT
   multiligne ») ; il sera reproduit sur un DXF fictif dans `tests/dxf_nomenclatures.py`.

## Limites et non vérifié
- Lecteur DXF éprouvé sur des fichiers ezdxf (R12, R2000) seulement : aucun plan réel, aucun fichier exporté par
  AutoCAD, Revit ou un autre logiciel n'a été lu.
- Non lus comme géométries : blocs (`INSERT`), réservations dessinées en `LINE` séparées, hachures, arcs, DXF binaire ; contours
  d'une présentation non proposés.
- Nomenclatures : éprouvées sur des DXF ezdxf fictifs seulement (TEXT + LINE, MTEXT sans grille, blocs, présentation active ou
  non) ; ACAD_TABLE : entité minimale fabriquée, jamais un fichier AutoCAD ; textes tournés ignorés pour les tableaux ;
  largeur des textes estimée (0,6 h par caractère) ; fenêtres de présentation non interprétées ; MINSERT : première occurrence ;
  attributs et blocs dynamiques non testés sur un vrai fichier ; quantité (« Qté ») gardée en texte, pas reportée dans `nb`.
- Hypothèses : réservation rectangulaire → coffrage `rect` / `carre` sans fond par défaut ; cercle → fourreau `circ`.
  Les autres formes (voile cintré, poutre, goulotte…) ne sont pas reconnues.
- Orientation (`angle`) et position (`centre`) ne sont gardées que dans la provenance : un plan CoffraPlan n'a pas de
  position absolue.
- `limErr` lit le libellé d'unité dans le formulaire pour ses messages : sans formulaire, le message dirait « mm ».
- Fenêtre testée dans Chromium seulement (t_dxf_ui) : ni Firefox, ni Safari, ni tablette réelle. Aperçu : polylignes et
  cercles seulement ; la fenêtre ne propose que rect / carré (avec ou sans fond) et fourreau.
- Modèle de plan repris du formulaire (CP, options de la forme affichée, ex. goussets) : vérifier le formulaire avant import.
- Au-delà de 300 géométries non prises en charge, la liste n'affiche que les 300 premières (le bilan les compte toutes).
