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

Rectangles en `LINE` indépendantes (phase 4) : `dxf.js` garde les extrémités d'une `LINE` plane (`segment`) ; `detecter`
regroupe les `LINE` de l'espace Objet par calque et les passe à `rectSegments` (graphe des extrémités raccordées à 1e-6 de
l'étendue près ; côté en plusieurs morceaux alignés réuni ; cycles de 4 côtés testés par `rectangle`). Proposé (candidat ajouté
après ceux des entités, `source.id` = identifiants des LINE joints par `+`, `geometrie.type:'polyligne'`, `geometrie.lignes`)
seulement sans ambiguïté : aucun autre trait du calque raccordé aux sommets (diagonales admises) ni posé sur un côté (cadre
subdivisé, cartouche, quadrillage écartés), et pas de polyligne reconnue aux mêmes centre et cotes (doublon). Les LINE gardent
leur entrée « non prise en charge » avec la remarque « côté du rectangle Rn » (ou la raison du refus). 4 LINE sur 2 calques :
non assemblées.

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
  `id="pdfjs-worker-src"`, ≈ 1,8 Mo ; HTML complet ≈ 6 Mo avec l'OCR). Chargé à la première ouverture d'un PDF (module importé par URL blob).
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
  « lecture automatique : n ligne(s) » ou « aucune nomenclature lisible automatiquement : OCR ou saisie assistée ».
- Nomenclatures : `nomenclatures.analyser` tel quel, une page = un espace (jamais de mélange entre pages) ; `N.page`,
  `N.format`. Rapprochement géométrique : seulement après « Repérer les réservations » (ci-dessous).
- Fenêtre : onglets « Nomenclature » et « Aperçu du plan » (pages, zoom, tableaux reconnus encadrés, ligne encadrée par
  « p. N ↗ »). Zone : cliquer-glisser, « Analyser la zone » (textes et traits de la zone, traits coupés au bord) : les tableaux
  lus automatiquement qui partagent des textes avec la zone sont remplacés (`N.id` = `Z1`…, `N.zone`) ; rien n'est ajouté si la
  zone ne donne pas de nomenclature de réservations. Saisie assistée : lignes tapées en consultant la page (`N.saisie`, `N.id`
  = `S<page>`), mêmes contrôles et même création ; ✕ retire une ligne saisie.
- Provenance (en plus des clés DXF de `provenance()`) : `format:'pdf'`, `type:'nomenclature'|'saisie'`, `page`, `zone`
  `{page, x0, y0, x1, y1, unite:'pt'}` (zone choisie, sinon cadre du tableau ; ligne saisie : zone choisie au moment de la
  saisie). Le PDF n'est jamais stocké.
- Limites : textes tournés ignorés pour les tableaux (comme en DXF) ; tableau continué sur une autre page sans en-tête
  répété : non relié (saisie assistée) ; PDF protégé par mot de passe refusé ; images JPEG 2000 / JBIG2 et
  textes CJK mal rendus dans l'aperçu (décodeurs non intégrés) ; testé dans Chromium seulement.

## Repérage des réservations sur le dessin d'un PDF (`geometrie.js`, fenêtre `dxr*`, phase 4)
- Tracés relus à la demande (rien gardé à l'ouverture) : `CPI.pdf.chemins(pdf, n)` → `{page, w, h, segments:[{id, a, b}],
  contours:[{id, pts, courbes}], coupe}`, points de la page affichée, Y vers le haut (rotation comprise, même repère que les
  textes) ; chemins de découpe (`W n`) ignorés ; au plus 400 000 segments par page (`coupe` signalé). Même parcours des
  opérateurs que les traits des tableaux (`cheminsPage`).
- `CPI.geometrie.detecterPage(geo, {fichier, textes, cadres, zone})` → `{candidats, ignores, coupe}` :
  rectangles par `CPI.detecteur.rectSegments` (rectangle « re », contour fermé ou traits séparés : même résultat ; tolérance
  de raccord 0,25 pt) ; cercles : contour fermé en courbes de Bézier (ou ≥ 8 sommets) dont sommets et milieux de courbes sont à
  2 % près sur un cercle d'emprise carrée ; même cercle tracé et rempli compté une fois ; moins de 2 pt : ignoré.
  Candidat au contrat du détecteur, `unite:'pt'`, `source.page`, `geometrie.page`, `bbox`, `annot:{repere?, cotes?}`.
- Écartés (« non exploitable », raison gardée) : dans un tableau reconnu ou une zone OCR (`cadres`) ; ≥ 60 % de la page
  (cadre de feuille ou de vue) ; ≥ 40 % (ouvrage, local, vue) ; côtés touchés par d'autres extrémités de traits (subdivisé :
  tableau, cartouche) ; 3 sommets ou plus partagés (cellule de quadrillage) ; 3 textes ou plus à l'intérieur ; plus de 30
  extrémités de traits à l'intérieur (cadre de détail, texte dessiné). Doutes notés sans écarter : sommet raccordé (mur ?),
  grand contour (≥ 25 %), traits intérieurs, diagonales.
- Textes voisins (moins de 4 hauteurs de texte, contour le plus proche) : repère (`R12`, `TR-3`, `F1`…, pas un nombre seul) ;
  cote écrite (`650x800`, `Ø250`, unité éventuelle) lue par `nomenclatures.cotes` ; « R12 650x800 » donne les deux.
- Échelle (par page, jamais devinée) : calibration (2 points accrochés au sommet de trait le plus proche à 8 px, distance
  réelle saisie en mm → mm par point) ou échelle écrite sur la page (« Éch. 1/50 », proposée, appliquée sur clic :
  50 × 25,4 / 72 mm par point, valable si le PDF est à la taille réelle de la feuille). Cotes proposées : cote écrite avec unité
  (sans échelle), ou sans unité si l'échelle permet de la déduire (à 10 % près) ; sinon mesure à l'échelle arrondie au mm ;
  sinon rien (« à compléter »). Toujours modifiables.
- Nomenclature : `associer(…, {mm})` compare repères et contours d'une même page (textes `page` ↔ contours `page`), cotes en
  mm par l'échelle de la page ; « trouvée » (repère voisin + cotes identiques) rattachée d'office, modifiable ; plusieurs
  contours : liste au choix dans l'onglet Nomenclature ; un contour rattaché quitte la liste repérée (pas de doublon), un
  contour seulement « possible » y est signalé ; même référence cochée des deux côtés : refusée.
- Fenêtre (onglet Aperçu) : « 🔎 Analyser le dessin » (toutes les pages, ou la zone choisie sur sa page ; relancer garde les
  corrections, voir plus bas), contours violets cliquables (ligne sélectionnée ↔ contour orange), tableau : page, repère,
  forme, cotes, origine des cotes, h, référence, état (repérée · à confirmer · à compléter · refusée), contours écartés à part.
  Création : `adaptateur.versPlan` avec les cotes en mm (contrôles du moteur), rien de coché d'office.
- Provenance (`origineImport`, `type:'detection'`) : `fichier`, `format`, `page`, `id` (segments ou contour PDF), `candidat`,
  `forme_detectee`, `centre`, `boite` et `dims_source` en pt, `zone`, `echelle` (`mm_par_pt` + 2 points et distances, ou
  échelle lue et son texte), `repere`, `annotation`, `cotes:{origine:'annotation'|'mesure'|'saisie', proposees, retenues}`,
  `choix`, `corrige` (`cotes`, `forme`, `ref`), `a_verifier`. Le PDF n'est jamais stocké.
- Limites : côtés en arc (réservation dans un voile circulaire), rectangles dont un côté est interrompu ou partagé par un mur
  ou une hachure qui touche le contour, contours ouverts, blocs complexes : non proposés (la réservation reste retrouvable
  par son repère, voir le rapprochement) ; PDF numérisé : aucune détection (OCR des nomenclatures et saisie assistée seulement).

## Repères dessinés et rapprochement nomenclature ↔ dessin (`rapprochement.js`, phase 4 finalisée)
- Principe : la nomenclature donne les cotes de fabrication ; le dessin identifie, localise et, quand il le peut, contrôle.
  Aucune cote n'est remplacée par une mesure ; une ligne non retrouvée reste créable avec ses cotes.
- Textes dessinés en traits (export DAO qui vectorise ses polices) : `CPI.pdf.chemins` rend aussi `petits` (emprises à plat des
  sous-chemins < 20 pt) ; `CPI.geometrie.blocsTexte(geo, {cadres})` les regroupe en lignes de texte (écart ≤ 1,2 hauteur : le
  « 1 » sans empattement des polices de DAO est très espacé ; même bande verticale), garde 2,5 à 30 pt de haut, ≤ 200 pt de
  long, hors tableaux. `CPI.ocr.lireBlocs(pdf, n, blocs, o)` : page rendue par tuiles (celles qui contiennent des blocs), blocs
  découpés, mis à ~32 px de hauteur de lettre, collés en mosaïques (écart 3 hauteurs entre découpes), une reconnaissance
  Tesseract (psm 11) par mosaïque ; lectures courtes douteuses qui ressemblent à un repère relues seules (psm 7, ≤ 200 par
  page). Texte OCR au format de `lireZone` + `ocr.box`, `ocr.mots` (confiance par mot), `ocr.relu`. Gardés par page pour les
  analyses suivantes ; jamais d'OCR intégrale de la page A0.
- `CPI.geometrie.rappels(geo, texte, index)` : traits partant à moins d'une hauteur du texte (≥ 2 hauteurs de long), suivis
  sur un coude ; leurs bouts désignent ce que le repère montre. `CPI.geometrie.index(geo)` : index des segments par case.
- `CPI.rapprochement.rapprocher(lignes, textes, candidats, {mm, rappels, exclus})` → `{lignes: {id: résultat}, hors, colonnes}` :
  - textes : ceux du PDF et ceux lus par OCR, hors tableaux reconnus ; colonnes de ≥ 5 textes alignés régulièrement espacés
    (tableau non reconnu) écartées ;
  - repère identique (clé `cleRep` du texte entier ou d'un de ses mots : « |D16 », « D8 / », « D 7 ») ; lecture OCR : confiance
    des mots du repère seulement ; < 30 % : ignorée ; < 75 %, corrigée, ou rapprochée par confusion S/5, O/0, I/1, L/1, B/8,
    Z/2, G/6 (`cleFloue`) : localisation **incertaine** ; repère purement numérique : texte entier seulement, incertain ;
  - contour désigné : le plus proche du repère ou du bout d'une ligne de rappel (≤ 4 hauteurs de texte), seulement s'il se
    détache nettement du suivant ; cotes écrites voisines (≤ 6 hauteurs du repère ou 4 du contour) : « l x h », « Ø », nombre seul ;
  - vérification de chaque cote du tableau (repères fiables seulement) : `confirmee` (cote écrite égale, à 1 % ou 2 mm ; sans
    unité écrite, essayée en mm, cm, m : « 40x40 » d'un plan en cm confirme 400 × 400 mm), `mesuree` (contour à l'échelle de sa
    page, à 5 %), `conflit` (cote écrite complète « l x h » ou « Ø » différente, même ordre de grandeur ou unité écrite),
    `non_verifiable` (absente : jamais un conflit) ; un nombre seul différent, une mesure différente, une forme différente :
    simples remarques ;
  - concordance : `forte` (repère fiable, toutes les cotes confirmées ou mesurées), `partielle` (repère fiable, une partie
    vérifiable, ou aucune), `probable` (repère incertain, ou cotes seules : contour de mêmes cotes mesurées sur la page du
    tableau, jamais d'une autre page), `conflit`, `absente` ; un contour est proposé d'office (`statut:'trouvee'`) s'il est
    unique, ou unique par page (vues) ; plusieurs sur une page : au choix ;
  - interpages : un repère identique suffit ; jamais les cotes seules ; toutes les localisations d'un repère sont les preuves
    d'une seule entrée (vues, coupes, détails ; leurs contours rattachés, jamais reproposés) ; quantité du tableau gardée et
    comparée au nombre de localisations par page (`coherente`), jamais déduite ;
  - `hors` : repères de même préfixe que ceux du tableau sans ligne correspondante (« D24 »).
- Fenêtre : onglet Nomenclature, colonne Source : concordance, localisations cliquables (page affichée, repère surligné, lignes
  de rappel en tirets ; « ? » = incertaine), état de chaque cote du tableau, quantité, doutes ; liste « aucun contour / contours /
  ✕ rejeter le rapprochement » ; bilan (fortes, partielles, probables, conflits, non retrouvées, localisations, contours
  rattachés, formes et repères hors nomenclature). Formes non rattachées : « Formes du dessin hors nomenclature ».
- Nouvelle analyse : identité d'un contour = page, forme, emprise à 0,5 pt (`dxrCle`) ; même contour retrouvé (même après une
  analyse par zone qui l'avait exclu) : identifiant, cotes, hauteur, forme, référence, coche reprises ; rattachement d'une
  ligne gardé ; contour disparu : rattachement retiré et signalé, jamais transféré à un autre. Erreur ou arrêt : message
  lisible, bouton rendu, résultats précédents gardés.
- Provenance d'une ligne créée (`origineImport.rapprochement`) : `concordance`, `rejete`, `localisations` (page, position,
  texte, source pdf/ocr, brut, confiance, corrections, zone en pt, fiable, doutes, contour, cotes voisines), `cotes` (état et
  preuves de chaque cote), `quantite`, `note`.
- Limites : DXF : rapprochement inchangé (`associer`) ; repères tournés (texte vertical) non lus ; une note qui cite un repère
  (« 5x D11 ») ou une liste d'articles hors tableau peut donner une localisation de trop (visible, rejetable) ; cotes
  écrites lues seulement si horizontales ; échelle d'une vue de détail différente de celle de la page : mesure fausse (simple
  remarque, jamais un conflit).

## Reconnaissance OCR (`ocr.js`, fenêtre `dxo*`)
- But : lire une nomenclature dont les textes sont dessinés en tracés ou numérisés. Complète la lecture texte, ne la remplace
  pas : « Analyser la zone » (textes extractibles) et « Reconnaître le tableau (OCR) » sont deux actions distinctes ; si la
  zone contient déjà un tableau bien lu par le texte, l'OCR demande confirmation avant de se lancer.
- Moteur : Tesseract.js 7.0.0, cœur `simd-lstm`, modèle français `best_int` (`vendor/tesseract/README.md` : versions, licences,
  empreintes). Worker blob construit depuis les blocs du HTML, chargé au premier clic ; aucune requête réseau (t_ocr).
- Chaîne (`CPI.ocr.lireZone(pdf, zone, o)`) : rendu de la zone par le PDF.js existant (`CPI.pdf.rendreZone`, rotation de page
  appliquée), 300 dpi plafonnés (`PX_MAX` 14 Mpx, côté ≤ 6000 px) ; prétraitement léger sur la copie rendue (gris, étirement du
  contraste, traits longs relevés comme traits du tableau puis effacés) — le PDF n'est jamais modifié ; lecture psm 11, puis
  2e passe remise à l'échelle (hauteur médiane des mots ≈ 40 px), passe retenue = meilleure confiance pondérée ; cellules
  encrées mais vides relues seules (psm 7). Mots → textes en points PDF (Y vers le haut), groupés en phrases, avec
  `ocr:{brut, conf, corrections, incertain, box}` (seuil de doute `SEUIL` = 75).
- Tableau : `nomenclatures.analyser` tel quel sur ces textes et traits (avec ou sans bordures, cellules sur plusieurs lignes,
  tableaux d'aciers écartés : colonne `acier`). Aucun second moteur métier.
- Corrections automatiques (`corriger`, puis `grille` selon la colonne) : O/o → 0, I/l/| → 1, S → 5, B → 8 dans une suite de
  chiffres seulement (1re lettre d'un repère gardée), @ © ® → Ø devant des chiffres, « (rnm) » → « (mm) ». Un nombre seul peu sûr dans une ouverture (« 250 », « 900 », « 2500 » :
  Ø peut-être mal lu) n'est jamais converti en diamètre : valeur gardée, ambiguïté signalée, Ø à préciser par l'utilisateur. Valeur brute toujours gardée ; toute correction autre que casse / espaces est signalée. Repères
  en double ou hors de la suite des voisins signalés. Rien n'est inventé : cellule illisible = vide signalée ; DN laissé
  dans « Réseau », jamais converti en cote ; altitude laissée dans « Niveau », jamais prise pour une hauteur de coffrage.
- Grille de vérification (sous l'aperçu) : Repère, Désignation, Type ou nature, Dimensions d'ouverture, Réseau, Niveau ou
  altitude, Observations, autres colonnes non vides, État ; toutes les cellules éditables, cellules douteuses en orange avec
  le texte brut et la confiance en infobulle, cellule montrée sur la page quand elle a le focus ; insérer, fusionner, retirer
  (rétablissable) une ligne ; une ligne au repère douteux n'est jamais retirée sans action de l'utilisateur. OCR relancé :
  corrections et lignes ajoutées gardées (clé = repère lu à l'origine `cle0`). Nouvelle zone sans nomenclature : la grille précédente reste affichée avec ses corrections,
  marquée « reconnaissance précédente » (jamais présentée comme résultat de la nouvelle zone).
- « Ajouter à la nomenclature » (`versNomenclature`, via `nomenclatures.ligne`) : `N.ocr = true`, `N.id` = `O1`, `O2`… ;
  lignes déjà lues par le texte sur la même page non ajoutées (pas de doublon) ; nouvel OCR d'une même zone : remplace le
  précédent sans perdre les coches ; rien n'est coché d'office. Création : même chemin que DXF / PDF.
- Provenance : `type:'ocr'`, `format:'pdf'`, `page`, `zone`, `repere`, `textes` (retenus), `indice`, `unite`, `dims_source`,
  `a_verifier` (lectures incertaines, ligne ajoutée à la main) et `ocr:{brut, confiance, corrections, corrige (valeurs
  saisies par l'utilisateur), incertain, ajoutee, moteur}`. Ni image ni PDF stockés ; jamais lue par le moteur.
- Limites : précision dépendante du rendu (petits corps, nuages de révision, textes barrés) ; une seule zone à la fois ;
  textes tournés non lus dans le tableau ; ≈ 1 à 8 s par tableau sur la machine de test ; Chromium seulement (Firefox, Safari
  non testés) ; vrais scans non testés (seul un scan fictif l'est). Test réseau de t_ocr : les requêtes Google Fonts de
  l'interface (héritées, hors OCR) sont bloquées mais ignorées ; toute autre requête fait échouer le test.

## Phase 5 : lecture des tableaux, vues techniques, occurrences (`vues.js`)
- Tableaux (`nomenclatures.js`) : titres de colonnes Nb, Nb., Nombre, Qté, Quantité, Fonction, Largeur, Hauteur, Ø,
  Diamètre, unité dans le titre (« Largeur (mm) », « Hauteur mm ») ou en 2e ligne ; `dimsLigne` : ouverture écrite, puis Ø,
  puis Ø vide ou « - » → Largeur × Hauteur, sinon ambiguïté signalée (Ø et L × H remplis : aucune cote choisie) ; un tiret
  ou une cellule vide = absent ; un DN ne remplace jamais le Ø ; `L.nb` = quantité entière (création : un ouvrage, `nb`).
  Tableau tourné de 90°, 180° ou 270° : orientation choisie par score de lecture (`tourne`, `textesEnGrille`).
- OCR (`ocr.js`) : grille de traits reconnue → une lecture par cellule, résolution choisie entre 24 et 36 px de lettre ;
  variantes niveaux de gris et couleur d'encre dominante (grille, nuages de révision d'une autre couleur effacés) ; zone
  manuelle : la grille identifiable est gardée, titres et rôles des colonnes corrigeables, corrections gardées à la relance.
- Vues (`CPI.vues.detecter(geo, textes, {cadres})` → `{vues, carte}`) : titres = textes ≥ 1,8 × la hauteur médiane avec un
  mot-clé (plan, vue, coupe, élévation, façade, détail, ferraillage, armatures, renfort ; lecture OCR approchée acceptée à
  2 lettres près pour les mots longs) ; « Partie supérieure / inférieure » seul = sous-titre du ferraillage le plus proche ;
  partie d'ouvrage (dalle, radier, voile, poutre…) ; échelle « 1/n » et niveau écrits près du titre. Régions : grille
  d'occupation des tracés (cases de 0,8 % de la page, tableaux exclus), composantes connexes rattachées au titre le plus
  proche ; composante sans titre assez grande = vue `autre`. Trait long ouvert (une extrémité libre : axe, ligne de cote,
  trait de liaison) : relie des cases mais n'étend pas une région ; composante très étendue (> 45 % de la largeur ou 60 % de
  la hauteur) qu'aucun titre ne préfère : jamais rattachée au titre voisin ; îlot de dessin < 10 % du plus gros, hors de
  l'emprise : hors de la vue (cases rendues). Région > 30 % de la page, couvrant le titre d'une autre vue ou recouvrant à
  plus de 50 % une autre vue titrée → `incertaine` (+ motif) : retirée des régions de `situer` (cases dessinées seulement),
  jamais comptée par `consolider`, et le rapprochement (`vueIncertaine`) n'en tire ni contour proposé d'office ni concordance
  forte. Champs : `id` stable `V<page>-<n>` (ordre de lecture), `page`,
  `region` (pt), `titre`, `type` (plan, coupe, elevation, detail, ferraillage_superieur, ferraillage_inferieur, ferraillage,
  autre), `partie`, `echelle`, `niveau`, `confiance` + `motifs`. `situer(carte, x, y)` → id de vue ou `null`.
- Rapprochement : option `vue(page, x, y)` ; contour et cotes voisines cherchés dans la vue du repère seulement.
- `CPI.vues.consolider(ligne, résultat, vues)` : quantité du tableau = référence ; occurrences physiques comptées dans la
  meilleure vue (plan, sinon ferraillage, sinon autre ; lecture incertaine comptée seulement en plan) ; les repères des autres
  vues de même partie à la même position relative (± 10 %) sont des représentations de ces occurrences ; coupe, élévation,
  détail : rattachées seulement à une occurrence unique. Toute autre observation (positions incompatibles ou ambiguës, autre
  partie, vue incertaine, hors vue, aucune occurrence) : rôle `non_rattachee` + `motif`, dans les notes « à vérifier ».
  → `{attendue, localisees, representations, nonRattachees, observations, restantes, depasse, physiques, roles, notes}`.
- `CPI.vues.classer(contour, vue, repères)` (formes hors nomenclature, section repliée `#dxrH`) : `examiner` (repère, cote
  écrite, diagonales), `representation` (repère du tableau), `parasite` (vue de ferraillage, coupe / élévation / détail sans
  indice, forme isolée) avec sa raison ; rien n'est supprimé.
- Export « ⬇ Analyse (JSON) » (`dxrJSON`, `format: 'coffraplan-analyse-plan', v: 1`) : `tables`, `tableRows`, `views`,
  `graphicalObservations` (contours et repères), `physicalOccurrences`, `associations`, `evidence` (preuves des cotes),
  `uncertainties`. Structure prévue pour une future IA locale ; aucune IA dans cette phase.
- Provenance : `origineImport.rapprochement.localisations[].vue` / `.role`, `origineImport.rapprochement.occurrences`.
- Banc `t_vues.py` (plans fictifs de `tests/vues_fictifs.py`). Limites : titres de vue tournés non lus ; deux vues collées
  sans blanc entre elles peuvent se confondre ; position relative entre vues = vues de même cadrage.

## Phase 5.1 : corrections après essais sur trois plans réels (sans nouvelle fonction)
- Unités (`cotes`, `dimsLigne`) : seule l'unité écrite contre la cote compte (« 500x500 mm », « Ø250mm ») ; une autre valeur de la
  cellule (« 500x500 — 4,86m », hauteur d'axe fusionnée) ne la donne jamais. Unité de la cellule contraire à celle du titre de colonne :
  cote gardée, `dims.conflitUnite`, unité à confirmer ; la fenêtre ne la remplace jamais par l'unité de l'en-tête (`dxnU`), seulement
  par un choix de l'utilisateur. Provenance : `L.uniteOrigine` ('titre de colonne' | 'cellule'), `origineImport.unite_origine`.
- Grille OCR (`ocr.grille`) : Diamètre, Largeur, Hauteur, Longueur vont dans « Dimensions d'ouverture » seulement si le tableau n'a pas
  de colonne Ouverture ; sinon « Autres colonnes » (jamais fusionnées avec l'ouverture).
- Colonnes : « Réservation(s) » n'est un titre de repères que seul ou avec « N° » ; « Axe réservations », « Niveau réservation »,
  « Hauteur (d')axe … » → niveau ; « Longueur » = 2e cote si pas de « Hauteur » (« longueur développée » reste aciers).
- En-tête à plusieurs niveaux : textes (`construire`) : largeur du tableau prise sur la 1re ligne de valeurs, lignes d'en-tête voisines
  sans chiffre ajoutées, titre au-dessus de plusieurs colonnes = titre de groupe (`colonne.groupe`, unité transmise) ; écart de
  coupure entre titres `ECART` = 60 hauteurs de texte (colonne de commentaires large) ; grille (`depuisGrille`) : cellule d'en-tête
  fusionnée sur n colonnes éclatée quand une ligne a n mots.
- Nature `trappes` (`nature`) : titre ou colonne trappe, regard, tampon, feuillure, ouverture équipée, châssis, caillebotis, sans
  mot de réservation dans le titre → tableau écarté (`ecartes[].lignes` consultables), jamais proposé à la création ; OCR : grille
  de trappes refusée comme une grille d'aciers. JSON : `excludedTables`.
- DN dans la colonne Ouverture (décision de Kévin, 21/10/2026) : réservation circulaire probable, `L.dn = {D, texte}`, message
  « diamètre réel de réservation à confirmer », aucune cote tirée du DN ; création impossible sans cote saisie.
- OCR sur la zone d'un tableau déjà lu automatiquement (`dxoValider`) : remplacement proposé (lignes en correspondance par repère,
  sinon par rang ; choix gardés ; nombre de lignes retirées annoncé) ; refus : rien d'ajouté ni de retiré.
- Vues (`vues.js`) : « vue dessus / dessous » = plan ; « plan » aussi après « vue » ; titre de 1,45 à 1,8 × la médiane admis pour un
  mot portant lui-même un mot-clé de vue ; renvoi (« voir », « cf ») et paragraphe (3 lignes ou plus, ou 3 textes de même hauteur à
  moins de 2,5 hauteurs : notes, cartouche) rejetés ; « Renforts » sans « ferraillage » = détail ; titre sans tracé : pas une vue ;
  cadre de feuille (≥ 90 % de la page) jamais rattaché à un titre ; dessin sans titre à 80 % dans une vue titrée : partie de cette
  vue ; seule une région **sans titre** de plus de 30 % de la page est incertaine par son aire.
- Repères (`rapprochement.js`, `natureMention`) : chaque mention a une `nature` : `repere` (isolé), `identifiant` (« 1-D1 »,
  « D10-EXT » quand le repère du tableau n'a pas de tiret), `multiplicateur` (« 2x D10 », « 5x » à gauche), `annotation` (autres
  mots : renvoi, note) ; seules les mentions `repere` comptent, les autres restent des observations non rattachées avec leur motif.
  `blocsTexte` : un tiret (tracé plat ≤ 1,5 hauteur de lettre) est regroupé avec ses lettres, l'OCR lit « 1-D1 » entier.
- Comptage (`consolider`) : jamais dans une vue sans titre ; pas de repli sur le ferraillage si une vue en plan du document est
  incertaine ; même repère plusieurs fois dans la vue retenue sans quantité au tableau : aucune occurrence décidée, observations à
  vérifier.
- Banc `t_phase51.py` (cas synthétiques anonymes de chaque défaut). Limites restantes : repères et titres verticaux non lus (planche
  tournée) ; réservations à côtés courbes non détectées ; mots isolés d'un cartouche lus par OCR peuvent encore former une vue.

## Phase 6 : moteur de reconnaissance PP-OCRv6 (`ppocr.js`, branché dans `ocr.js`)
- Moteur : **PP-OCRv6 small**, reconnaissance seule (Apache-2.0, PaddleOCR ; ONNX de RapidOCR 3.10.0) sur **ONNX Runtime Web
  1.30.0** (MIT), WebAssembly SIMD, un fil ; embarqué dans le HTML (blocs `ppocr-*`, empreintes vérifiées par `assembler.py`,
  provenance et licences : `vendor/ppocr/README.md`). Aucune requête réseau, aucune clé, aucun service. Chargement ≈ 1 s.
- Contrat commun (`CPI.ppocr.lire(images, {vertical, annule})`) : une image = une ligne → `{texte, conf (0-100, moyenne des
  probabilités des caractères), chars:[{t, c}], orientation (0 | 90 | 270)}` ; illisible → texte vide, jamais complété.
- Choix du moteur : `CPI.ocr.choisirMoteur('ppocr' | 'tesseract' | null)`, `CPI.ocr.moteur()` ; sélecteur « Moteur OCR » de la
  fenêtre (`#dxoMot`, clé `resaOcrMot`) ; PP-OCRv6 par défaut s'il est dans le fichier. `lireZone` (zone sans grille, scan) reste à
  Tesseract : la reconnaissance seule ne découpe pas une page en lignes (la détection PP-OCR n'est pas embarquée).
- Tableaux à grille (`lireGrille`) : même grille, mêmes variantes gris / couleur, même détection du tiret seul ; `mosaique` passe à
  `mosaiquePP` : chaque cellule découpée en lignes par `bandes` (projection horizontale, recadrage serré sur l'encre : une ligne noyée
  dans une cellule haute perd lettres et espaces ; traits intérieurs d'un en-tête fusionné effacés, ligne coupée à chaque trait
  vertical ; deux lignes serrées sans interligne coupées à leur rangée la moins encrée) ; Ø contrôlé par `oslash` sur le premier signe
  (`premier`) ; pas de relecture Tesseract. `corriger` ramène la typographie du modèle multilingue : × entre deux nombres → x,
  ∅ et Φ devant un nombre → Ø, « 一 » → -, signes pleine chasse → ASCII (brut gardé).
- Repères dessinés (`lireBlocs` → `lireBlocsPP`) : mêmes tuiles et découpes, marge réduite (¼ de hauteur au lieu de ½ : PP-OCR lit
  toute la découpe, pas de rognage au caractère) ; signes isolés des bords (« | ») retirés ; `ocr.moteur`, `ocr.orientation`, `rot`.
  **Textes verticaux** : `blocsTexte(g, {verticaux:true})` (seulement avec PP-OCR) groupe aussi les tracés en colonnes (bloc
  `vertical:true`, refusé s'il est couvert à plus de moitié par des blocs horizontaux : repères empilés) ; lu dans les deux sens, le
  plus sûr gardé (90° = de bas en haut, 270° = de haut en bas) ; un bloc horizontal recouvert par un bloc vertical lu (lettre vue
  seule) : la lecture la plus sûre des deux reste.
- Mesures avant / après (trois plans réels, hors dépôt, vérités terrain relevées à la main ou lues dans la couche texte,
  indépendantes de CoffraPlan ; Chromium) : voir CHANGELOG, § Phase 6.
- Banc `t_ppocr.py` (hors connexion, ligne, vertical, découpage, tableau fictif par les deux moteurs, repères verticaux).
- Limites : plus lent que Tesseract dans le navigateur (un seul fil en `file://`) ; Ø parfois lu « 0 » ou absent (contrôle
  géométrique `oslash` seulement) ; zones sans grille toujours à Tesseract ; la détection PP-OCR (pages entières), PP-StructureV3,
  PaddleOCR-VL et Docling n'ont pas pu être essayés ici (hôtes de téléchargement bloqués) : voir `docs/audit-modernisation.md`.

## 3. Construction du livrable (phase 8)

- `app/CoffraPlan.source.html` contient le HTML, le CSS et le script principal, avec un marqueur `<!--@bloc ID-->` par bloc généré.
- `python modules/import/assembler.py` construit `app/CoffraPlan.html` (non versionné). Il remplace :
  - `cpi-src` par `lecteur.js`, `dxf.js`, `pdf.js`, `ocr.js`, `ppocr.js`, `detecteur.js`, `nomenclatures.js`, `geometrie.js`,
    `rapprochement.js`, `vues.js`, `adaptateur.js`, `fenetre.js`, dans cet ordre, chacun précédé de son nom ;
  - `fonts-src` (`<style>`, `@font-face` en base64) par les polices de `app/vendor/fonts` ;
  - `three-src` par `app/vendor/three` ;
  - `pdfjs-*`, `tess-*` et `ppocr-*` par `vendor/`, avec les empreintes SHA-256 vérifiées et les `.gz` en base64.
- Le résultat est déterministe : mêmes sources, mêmes octets. L'écriture est atomique et n'a lieu que si le contenu change.
- Sur les sources de main `b94a01e`, le livrable était identique octet pour octet au HTML versionné jusque-là.
- `--check` échoue si `app/CoffraPlan.html` est absent ou différent des sources. Il est lancé par :
  - `tests/syntax.sh` (étape « Syntaxe » de la CI) ;
  - t_dxf_ui, t_ocr, t_pdf, t_ppocr et t_build.
- L'appli reste un fichier unique, hors connexion, sans CDN ni serveur.

## Phase 8 : tableaux juxtaposés, titres de vue sans mot-clé, cartouche
- **Tableaux juxtaposés** (`construire`) :
  - Quand les traits d'une page ne sont pas relevés (plafond `SEG_MAX` de `pdf.js`, plan très chargé), un tableau est lu par la position de ses textes.
  - Avant correction, le tableau construit en premier s'étendait de proche en proche (écart ≤ 60 h) le long d'une ligne de valeurs, jusqu'au tableau voisin dont les lignes sont aux mêmes hauteurs, et lui prenait ses lignes.
  - Désormais, l'en-tête d'un autre tableau (autre hauteur, sans recouvrement horizontal) borne le tableau de son côté (`g.entetes`, couloir `limL` / `limR`, centre des textes). Cela s'applique à l'extension de largeur, aux lignes, au titre et aux traits.
  - Aucun seuil propre à un plan.
- **Titres de vue sans mot-clé** (`titres`) :
  - Un grand texte sans « vue », « plan », « coupe »… (« Sous Toiture ») devient un titre seulement avec son échelle écrite (« 1 : 25 », « 1/50 ») juste dessous ou sur la même ligne, en texte plus petit, à moins de 2,6 hauteurs.
  - C'est une vue en plan si le texte nomme un niveau vu de dessus ou de dessous (sous / dessus / dessous + toiture, dalle, plancher…, `NIVEAUX`) et si le dessin rattaché est conséquent (≥ `DV_DEDUIT` cases). Sinon, le type est « autre » et la vue n'est jamais comptée.
  - Confiance au plus moyenne, motif écrit. L'échelle appartient à cette vue seulement.
- **Cartouche** (`cart`, dans `detecter`) : un titre placé dans un petit cadre d'angle de feuille (≤ 10 % de la page) contenant au moins 3 autres textes n'est jamais un titre de vue.
- Banc `t_plan_d.py` : plan fictif anonyme type D (`tests/plan_d_fictif.py`) et cas négatif (« Sous Toiture » dans une note, ou sans échelle).
- Limite connue : `SEG_MAX` reste à 60 000 traits par page. Sur un plan très chargé, les traits des tableaux et d'une partie du dessin ne sont pas relevés (lecture par textes, régions de vue partielles).

## Phase 9A : géométrie du support d'une réservation (`support.js`, `CPI.support`)
Trois notions séparées : **forme de l'ouverture** (rect, carré, circ), **nature du support** (`voile_droit`, `voile_circulaire`,
`autre`, `inconnu`), **solution de coffrage** (jamais choisie ici : `solution_proposee` reste `a_determiner`, des pistes motivées
seulement). Aucun seuil de taille d'ouverture : la flèche est calculée par `GEO.sag` du moteur (reçu en paramètre `sag`, aucun calcul
métier dupliqué), à la corde = largeur **suivant la paroi** et aux deux parements, puis comparée à une tolérance **saisie**.

- **Entrées** : `CPI.support.analyser(obs, env, o)`.
  - `obs` = `{repere, candidat (contour de CPI.geometrie / CPI.detecteur) | point, h, page, vue}`.
  - `env` = `CPI.support.envPdf(chemins, textes)` ou `CPI.support.envDxf(doc, {espace, presentation})`.
  - `o` = `{k (mm par unité du dessin), echelle:{source, autres:[{k, source}]}, ligne (nomenclature, association fiable seulement),
    saisie:{epaisseur_mm, rayon_interieur_mm, largeur_suivant_paroi_mm}, tolerance_mm, sag, cadres, repris, eps, fenetre}`.
- **Analyse locale** (fenêtre de 6 fois la taille du contour autour de lui, hors tableaux, sans le contour lui-même) :
  - faces droites : segments colinéaires réunis en lignes ; paire adjacente de part et d'autre de la réservation, assez longue hors de
    l'ouverture ; pour un rectangle, seulement les directions de ses côtés ; « traversée » si le contour va d'une face à l'autre ;
  - faces circulaires : arcs de même centre, rayons de part et d'autre de la réservation, arcs présents près d'elle ; arcs pris dans
    les ARC / CIRCLE / polylignes à bulge d'un DXF, les courbes de Bézier d'un PDF (`arcsBezier` : cercle par 3 points, contrôlé en
    4 autres points), les chaînes de segments courts qui suivent un cercle (`arcsChaines`, courbe aplatie : rayon approché, signalé) ;
  - rejets : quadrillage (au moins 5 lignes régulièrement espacées), réservation plus large que la bande, ligne qui traverse l'ouverture
    (axe, cote) ; deux supports d'égale vraisemblance (autre direction, autre centre) → `inconnu`, rien n'est choisi ; courbes non
    circulaires seules → `autre`, aucun rayon ;
  - refus d'analyse : contour écarté par le repérage (sauf `repris`), observation dans un tableau ou un cartouche, vue en élévation,
    vue de ferraillage (armatures en lignes parallèles : faux voile constaté sur un plan réel) ;
  - réservation entre deux faces sans aller de l'une à l'autre (pièce entre deux murs, réservation de dalle, élévation) : support
    `inconnu`, bande signalée (`bande_possible`) ; contour `repris` : support seulement possible (`support_possible`, valeurs dans la
    preuve), le résultat reste `inconnu` (constaté sur un plan réel : gaine voisine prise pour la réservation) ; de même pour des faces
    présentes d'un seul côté de la réservation (extrémité de voile, ou lignes de cote alignées sur le contour : constaté sur un plan réel) ;
  - arcs d'un même centre à 1 % du rayon près (centre du groupe = celui de l'arc le plus long) ; deux candidats circulaires de même
    centre et mêmes rayons à 2 % près = une seule paroi (faces lues l'une en Bézier, l'autre en segments : centres ajustés différents).
- **Valeurs (mm) et provenance** (`provenance['support.epaisseur_mm'] = {origine:'cote_explicite'|'mesure'|'calcul'|'saisie', source, detail}`) :
  - échelle : celle donnée (page ou vue) ; deux échelles différentes, ou largeur mesurée qui ne correspond à aucune cote du tableau →
    « échelle incohérente », mesures non utilisées ; sans échelle, une épaisseur saisie ou cotée au tableau (« ép. 250 mm ») donne une
    échelle déduite (valeurs en provenance `calcul`, signalées) ;
  - épaisseur : saisie > cote écrite contre la paroi **confirmée par la mesure** > cote de la nomenclature > mesure ; une cote voisine
    non confirmée n'est jamais attribuée (proximité ≠ certitude) ;
  - rayon intérieur : saisie > cote « R=… » / « Ø … » confirmée par la mesure (face intérieure ou extérieure) > nomenclature > mesure ;
  - largeur suivant la paroi et orientation : colonnes Largeur / Hauteur du tableau (explicite) ; « a x b » orienté par la mesure le
    long de la paroi (500 × 1 000 : 500 suivant la courbure, hauteur 1 000) ; sinon `null` et « orientation non confirmée » ;
  - `correspondance_voile` : proposition `{forme:'voile', L, l, h, DcuveM, dRef:'int', joues:null}` pour le voile cintré du moteur,
    jamais appliquée.
- **Sortie** : `{repere, observation, ouverture, support, coffrage:{solution_proposee:'a_determiner', pistes, fleche_interieure_mm,
  fleche_exterieure_mm, tolerance_mm}, correspondance_voile, provenance, preuves, incertitudes, validation_utilisateur_requise:true}`.
  `CPI.support.consolider([…], {sag})` réunit les vues d'un même repère : chaque vue garde ses valeurs, provenances et preuves
  (`observations[]`, preuves marquées `vue`) ; nature du support en désaccord → `inconnu`, aucune valeur de support, aucune flèche, aucune
  `correspondance_voile` ; valeurs concordantes à 2 % gardées, sinon `null` + incertitude ; rayon extérieur, flèches (`GEO.sag` sur les
  valeurs consolidées) et correspondance recalculés ou retirés, jamais hérités d'une vue ; contradiction non résolue → confiance « faible ».
- **Lecteurs** (sans effet sur le reste) : `CPI.pdf.chemins` renvoie aussi `courbes` (pièces de Bézier des sous-chemins de plus de
  20 pt, plafond 200 000, `coupeCourbes`) et accepte `{zones:[[x0,y0,x1,y1]…]}` : relecture **locale** d'une page très chargée (les
  plafonds s'appliquent après le tri). `dxf.js` relève `arcs` (ARC, CIRCLE, côtés courbes des polylignes à bulge, blocs compris :
  rotation, miroir, échelle uniforme) et `traitsArcs` (côtés droits de ces polylignes) **à part** : `entites` et `traits` inchangés
  (les ARC restent « autre », le détecteur et les tableaux ne les voient pas).
- **Fenêtre** (`dxsAnalyser`, appelée à la fin de « 🔎 Analyser le dessin ») : localisations fiables des lignes en concordance forte ou
  partielle ; repère sans contour proposé : contour écarté le plus proche du repère, sans rival (réservation dessinée dans l'épaisseur
  d'un voile, sommets raccordés aux faces), repris : support « possible » seulement ; échelle de la page et de la vue comparées ; relecture locale
  des pages coupées. Résultats dans `DXI.SP` et dans l'export JSON (`supports`, état `supportsAnalyse` : `reussie` | `echec` + erreur |
  `non_lancee`) ; un échec (`DXI.SPerr`) est signalé dans le bilan (aperçu et onglet Nomenclature), le reste restant utilisable ; nomenclature, contours, ouvrages inchangés ; aucune
  interface nouvelle (lots suivants).
- Banc `t_support.py` (plans fictifs `tests/support_fictifs.py`, constructions `tests/support_cas.js`).

## Phase 9B : contours contextuels PDF (`contours.js`, `CPI.contours`)

- Voie complémentaire à `geometrie.detecterPage`, activée avec les repères de la
  nomenclature (`ctx.reperes`). Les rejets ordinaires des tableaux, cartouches et
  quadrillages ne sont pas supprimés.
- Un repère exact et fiable (texte PDF ou OCR ≥ 75 %) localise la recherche, directement
  ou via ses lignes de rappel. Deux diagonales qui se croisent dans leur partie centrale,
  deux traverses dessinées (éventuellement fragmentées, couverture contrôlée) et deux
  parements traversés doivent concorder. Un quadrillage régulier ou des hypothèses
  concurrentes ne sont pas promus. La recherche est bornée autour du repère ; une zone
  trop chargée est laissée indécidée.
- Une reconstruction est un candidat **à confirmer**, avec `geometrie.ferme:false` et
  `reconstruction:{type:'diagonales_parements',explicite:false,repere,diagonales,traverses,preuves}`.
  Les traits sources, couvertures et preuves de parements sont conservés. L'aperçu la
  dessine en tirets et les listes indiquent « contour reconstruit ». Cette métadonnée
  accompagne l'export d'analyse et la provenance d'un éventuel import confirmé.
- Aucun L × h de fabrication n'est tiré des limites reconstruites ; elles ne confirment
  pas non plus les cotes du tableau par mesure. La nomenclature ou une saisie explicite
  reste nécessaire. La nature du support peut être reconnue avec une confiance faible,
  mais rayon, épaisseur et flèche restent `null` sans échelle/cote confirmée. Aucune
  conversion d'agrandissement graphique en échelle physique.
- Les faces circulaires fermées aplaties sont relues dans leur sous-chemin : contrôle
  du rayon sur les sommets **et** les milieux (un rectangle dont les coins sont sur un
  cercle n'est pas une face circulaire). La mesure est approchée et signalée.
- Sur les petites planches, lecture OCR des blocs plus petits, rendu par tuiles jusqu'à
  24 px/pt et séparation des rappels fins et longs accolés aux lettres. Ce réglage est
  graphique, sans modification de `DXI.cal`. Les accolades/crochets/parenthèses autour
  d'un repère du tableau sont ignorés dans sa clé de rapprochement seulement ; le brut
  reste affiché et la normalisation est notée. Aucune correction de chiffre par voisinage.
- Limites : une ouverture sans diagonales et sans traverses suffisantes n'est pas
  reconstruite ; repère manquant ou douteux, rival, vue de ferraillage/élévation et
  géométrie tronquée peuvent laisser le support inconnu. La reconnaissance des vues
  tournées et des nuages de révision reste imparfaite.
- **DXF** : `CPI.support.envDxf` et l'analyse de ses arcs existent et sont testés comme
  API, mais `dxsAnalyser` dans la fenêtre exige un PDF. Ni l'analyse du support DXF ni
  cette reconstruction contextuelle ne sont raccordées à l'interface DXF.
- Banc : `tests/t_contours.py`, géométries entièrement fictives ; fait partie des suites
  rapides et complètes. Les plans réels et les rapports détaillés restent hors du dépôt.

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
- Non lus comme géométries : blocs (`INSERT`), hachures, arcs, DXF binaire ; contours d'une présentation non proposés ;
  `LINE` séparées : seulement les rectangles sans ambiguïté (même calque, aucun autre trait raccordé).
- Nomenclatures : éprouvées sur des DXF ezdxf fictifs seulement (TEXT + LINE, MTEXT sans grille, blocs, présentation active ou
  non) ; ACAD_TABLE : entité minimale fabriquée, jamais un fichier AutoCAD ; textes tournés ignorés pour les tableaux ;
  largeur des textes estimée (0,6 h par caractère) ; fenêtres de présentation non interprétées ; MINSERT : première occurrence ;
  attributs et blocs dynamiques non testés sur un vrai fichier ; quantité (« Qté », « Nb ») gardée en texte et reportée dans `L.nb`
  depuis la phase 5 (création : un ouvrage, `nb` = quantité).
- Hypothèses : réservation rectangulaire → coffrage `rect` / `carre` sans fond par défaut ; cercle → fourreau `circ`.
  Les autres formes (voile cintré, poutre, goulotte…) ne sont pas reconnues.
- Orientation (`angle`) et position (`centre`) ne sont gardées que dans la provenance : un plan CoffraPlan n'a pas de
  position absolue.
- `limErr` lit le libellé d'unité dans le formulaire pour ses messages : sans formulaire, le message dirait « mm ».
- Fenêtre testée dans Chromium seulement (t_dxf_ui) : ni Firefox, ni Safari, ni tablette réelle. Aperçu : polylignes et
  cercles seulement ; la fenêtre ne propose que rect / carré (avec ou sans fond) et fourreau.
- Modèle de plan repris du formulaire (CP, options de la forme affichée, ex. goussets) : vérifier le formulaire avant import.
- Au-delà de 300 géométries non prises en charge, la liste n'affiche que les 300 premières (le bilan les compte toutes).

## Phase 9C — proposition et création confirmée depuis un PDF

- `CPI.creation.proposer(analyse, saisie, contexte)` : valeurs en mm et provenance,
  inconnues, flèches, choix possibles et données manquantes ; sans DOM ni stockage.
  Seules les cotes explicites et les saisies sont disponibles d'emblée ; les autres
  valeurs de l'analyse exigent `mesuresConfirmees`. Ni les limites reconstruites ni
  les points PDF ne deviennent des cotes de fabrication ici.
- `CPI.creation.preparer(proposition, {confirme:true, ref}, {modele, moteur})`
  réutilise `migr`, `canon`, `voileGeo`, `limErr`, `checks`, `badDims`. Aucune formule
  de fabrication ajoutée. `para` à angles nuls pour le mannequin droit / simple,
  `voile` en mannequin ouvert pour le cintré, `circ` pour le fourreau.
- `creation-ui.js`, fonctions `dxc*` : brouillon en mémoire de la fenêtre, preuves
  et incertitudes visibles, saisie / correction avec origine, récapitulatif puis
  case et bouton finaux. Seul `dxcCreer` ajoute à `P`. Modifier une donnée après le
  récapitulatif invalide sa confirmation. Le projet et ses profils restent intacts
  pendant la préparation ; les modèles sont lus par le mécanisme existant.
- Les deux cordes sont celles de `voileGeo` : parallèles = même corde aux deux
  parements, radiales = `L` extérieure, `cInt` calculée par le moteur. Pas de
  conversion implicite depuis un développé ou une corde intérieure radiale.
  Flèches calculées par `GEO.sag` sur chaque corde. Pas de seuil universel.
- Profils : `tolCourb` facultatif en mm au chantier et dans `ouv[ouvrage]` ; absent
  ou `null` = non renseigné. Priorité ouvrage puis chantier, correction locale
  possible sans changer le profil. Zéro est accepté, valeurs négatives / illisibles
  refusées. Cette tolérance géométrique ne remplace pas la flèche mécanique du CP.
- `origineImport` garde analyse, proposition, valeurs / origines / corrections,
  note utilisateur, choix et confirmation. `creationCles` combine empreinte SHA-256
  du PDF et identité de ligne (page, nomenclature, ID de ligne) / contour stable ; elle est aussi posée et contrôlée
  par l'ancien chemin PDF. L'empreinte n'embarque aucun contenu du PDF.
  Les anciens ouvrages dépourvus de cette clé restent lisibles ; leur protection
  contre les doublons reste le contrôle existant des références.
- Un clic crée un ouvrage (`nb=1`), pas un lot déduit du nombre de vues. La longueur
  du fourreau doit être saisie et ses contraintes de traversée confirmées. Pour le
  moteur `circ`, épaisseur, rayon, joues et tolérance de courbure ne sont pas des
  prérequis : ils n'entrent pas dans son calcul et restent dans les preuves source.
- Banc `tests/t_creation.py`, seulement des PDF et géométries fictifs, en campagnes
  rapide et complète. Exemple pas à pas : manuel §7.22. Les cas réels restent privés.


## Phase 10A — cotes écrites, preuves et détails particuliers

`cotes-preuves.js` expose `CPI.cotesPreuves.analyser({analyse, repere, textes,
vues, occurrences, homonyme, contours, zoneTable})` et `affecter(dossier,id,champ)`.
Module pur, intégré par l'assembleur avant la création ; il réutilise les textes
PDF / OCR, nomenclatures, occurrences et vues existants. Ni second lecteur ni
formule de fabrication. Aucune mesure en points PDF n'est convertie ici.

- Les cotes explicites déjà attribuées par l'analyse / nomenclature sont conservées.
  Une annotation peut préremplir largeur, hauteur, diamètre de réservation,
  épaisseur du voile, rayon **intérieur** ou longueur de traversée si elle contient
  un seul repère exact non homonyme, un rôle nommé et une unité attachée (mm, cm,
  m). OCR : confiance ≥ 90 %, sans correction. Une échelle de cartouche ne donne
  jamais l'unité d'un nombre. Cette grammaire volontairement étroite ne traite pas
  les fragments de textes séparés comme une annotation unique.
- Même vue ou voisinage seuls : proposition à confirmer ; sans rôle, cote inconnue.
  Les autres cotes explicites du document restent visibles pour sélection manuelle,
  avec avertissement d'absence de lien. Le brut OCR et la lecture corrigée sont
  conservés séparément (et affichés si différents). Pas d'attribution d'un diamètre de cuve
  au diamètre de réservation, ni de conversion d'un diamètre / rayon extérieur en
  rayon intérieur. Un développé ne peut pas être affecté comme corde.
- Lecture numérique complète avant conversion : entiers, virgule décimale,
  groupes de trois chiffres séparés par espace ordinaire, insécable ou fine
  insécable (`1 200`, `1 200`, `1 200`), éventuellement avec décimales (`1 200,50`).
  Point décimal reconnu hors groupement ambigu à trois chiffres (`1.25 m`).
  `1.200`, les points multiples et les ponctuations mixtes (`1.200,50`,
  `1,200.50`) restent **ambigus**, sans normalisation ni millimètres proposés.
  Un nombre groupé ne produit pas de candidats partiels. Unités contre la valeur
  seulement ; nombres non finis, nuls, négatifs ou groupements irréguliers refusés.
  Dans la ligne candidate, saisir une valeur non ambiguë en mm puis « Confirmer
  et retenir ». L'interprétation saisie, le rôle confirmé et la chaîne source
  restent dans la provenance ; toute modification invalide le récapitulatif.
- Plusieurs valeurs établies pour un même champ : statut contradictoire, champ
  vidé, récapitulatif bloqué. L'utilisateur retient une preuve ou confirme
  explicitement sa saisie d'arbitrage. Une correction ultérieure invalide cet
  arbitrage et toute confirmation finale. Les preuves écartées restent présentes.
- La section « Cotes retrouvées dans le PDF » affiche brut, unité, mm justifiés,
  page, vue identifiée, rôle, motif et statut. « Voir la source » utilise `dxpOver`
  et l'aperçu existant. Aucun contenu n'est envoyé sur le réseau.
- Les mentions de chanfrein, feuillure, décrochement, sections multiples ou biais
  ne sont attribuées que sur un repère exact unique, non homonyme et de lecture
  fiable. Un autre repère explicite prime sur la vue commune. Sans repère, avec
  plusieurs repères ou des homonymes, les mentions restent dans
  `indicesNonAttribues`, consultables et non bloquantes ; l'utilisateur peut les
  signaler explicitement si elles concernent l'ouvrage. La vue commune seule ne
  prouve jamais une attribution. Un contour associé hors des formes connues
  est signalé sans le qualifier de chanfrein. L'utilisateur peut également
  signaler une particularité. **Les détails attribués et les signalements utilisateur bloquent la création standard** :
  leur fabrication reste à étudier, aucune option de validation d'un rectangle
  fictivement équivalent n'est proposée.
- `origineImport.cotesPdf` et `proposition.cotesPdf` : candidats, conflits,
  preuves retenues, rôle confirmé, saisies brutes, valeurs / origines, arbitrages
  et détails. Métadonnées facultatives conservées par le stockage et l'export
  JSON existants ; enveloppe projet v10 inchangée. Un dossier non créé reste dans
  `DXI.CP` et l'export local d'analyse (`cotesPdf`) ; il ne modifie pas le projet.
  Comme les brouillons 9C, il faut exporter ce dossier avant de fermer l'import.

Banc `t_cotes` et PDF **fictifs** dans `cotes_fictifs.py`, en campagnes rapide et
complète ; `t_creation` historique conservé. Exemple utilisateur dans le manuel.
Limites : pas d'interprétation générale des lignes de cote, pas de regroupement
sémantique de fragments PDF / OCR, pas de déduction automatique d'un rayon à partir
de diamètres de cuve, pas de fabrication des détails particuliers. Pour le cas
réel de cuve étudié précédemment, le chanfrein reste hors moteur : aucune
fabrication à l'identique n'est annoncée. Plans et diagnostics réels hors Git.


## Phase 10B — feuillure traversante et étude du chanfrein

Depuis la proposition PDF, choisir le détail (`aucun`, `feuillure`,
`chanfrein45`, `autre`). Une feuillure doit être explicitement qualifiée ; une
preuve attribuée de chanfrein, d'autre forme ou de biais n'est pas effacée par
ce choix. Les mentions non attribuées de 10A restent consultables.

### Feuillure : conventions de fabrication

Le `rect` / `carre` historique est une boîte ouverte suivant Z. Il ne peut pas
remplacer directement un mannequin de voile dont les deux ouvertures sont sur
X = 0 et X = e : cela inverserait aussi la hauteur utilisée pour la poussée.
Le modèle retenu est donc **`para`, angles nuls**, avec `feuilTraversee:true`
et `fL`, `fH`, `fNiv` comme paramètres métier facultatifs. Les anciens plans
sans ce champ ne changent pas. `origineImport` reste une provenance seulement.

`feuilTraverseRect` adapte le repère du modèle existant :

| Rect de référence | Mannequin traversant |
|---|---|
| L | largeur d'ouverture `ppB` |
| l | hauteur d'ouverture `ppH` |
| h | traversée `ppE` |
| haut z=h | parement A, X=0 |
| fNiv depuis le haut | départ depuis A vers B, pas depuis le linteau |
| fH | profondeur suivant la traversée |
| fL | largeur hors du vide L × H |

Le corps CP et ses assemblages restent ceux de `para`. Seuls le débit de ses
quatre tasseaux et leurs solides sont réemployés du `rect`, transformés par
`(x,y,z) → (e-z, x-L/2, y-H/2)` ; la réflexion inverse les faces orientées.
Les tasseaux ont des abouts carrés, deux longs filants et deux courts entre eux.
Les contrôles du `rect` imposent les limites existantes de feuillure et
`fNiv + fH <= ppE`. Les biais/pentes sont refusés pour cette option.

La feuille « FEUILLURE TRAVERSANTE », obligatoire même sans annexes, réemploie
les vues cotées du rect dans son repère de fabrication explicitement légendé.
Les autres vues para représentent le corps CP et le signalent. La 3D vectorielle
et WebGL utilisent les mêmes solides transformés ; DXF et BIM les reprennent,
avec BREP pour les tasseaux dans IFC/GLB. Pièces à coupes droites : pas de
nouveau gabarit cintré, les cotes de découpe restent celles du débit. La fixation,
le passage entre banches et la tenue mécanique restent à vérifier sur chantier.

### Cotes et confirmation

Les rôles nommés `largeur feuillure`, `profondeur feuillure` et `départ feuillure`
peuvent alimenter respectivement `fL`, `fH`, `fNiv` dans les mêmes conditions
strictes que les cotes 10A (repère unique, unité attachée, lecture fiable).
Zéro n'est admissible que pour le départ. Sa présence dans un PDF ne confirme
pas le sens de mesure : la qualification explicite de la convention A/B reste
obligatoire. Contradictions, corrections, qualification et paramètres sont
conservés dans la proposition et `origineImport.cotesPdf` après création.

Exemple **fictif** : largeur 600, hauteur 800, voile 240, CP 18, feuillure 40 × 30,
départ 20 mm. Choisir rectangle / voile droit / solution simple / feuillure,
compléter les valeurs et arbitrer toute contradiction. Confirmer la convention
A/B et la traversée normale ; examiner l'aperçu puis le récapitulatif, confirmer
la création. Résultat : CP 2 × 600 × 240 et 2 × 764 × 240 ; tasseaux
2 × 680 et 2 × 800, section 40 × 30, posés entre X=20 et X=50. La hauteur
métier reste 800. Changer une valeur annule le récapitulatif ; revalider la même
identité PDF ne crée pas un deuxième ouvrage.

### Chanfrein : géométrie à étudier

`geometries-particulieres.js` expose le module pur
`CPI.geometriesParticulieres.chanfrein45(parametres,provenance)` : L, e, H,
retrait, ep (mm), angle GA/DA/DB/GB, orientation explicite. Section horizontale
XY, A y=0, B y=e, gauche x=0, droite x=L ; Z vertical. Il retourne sommets,
faces, segments de référence, cotes, provenance, hypothèses et erreurs.
Un seul angle est remplacé par deux points de retrait égal ; section constante
sur H, angle 45°. Retrait strictement positif et inférieur à L et e.
L'interface exige aussi la confirmation de cette convention.

L'aire du vide n'est **pas** un débit CP. Les moteurs actuels ne définissent
pas la cinquième face, les jonctions obliques et les déductions CP d'un
assemblage pentagonal ; fabriquer un `para` de repli serait incorrect.
La variante reste `fabricable:false`, création bloquée même avec toutes les
valeurs. Aucun ouvrage n'entre dans les sorties de fabrication. La géométrie
d'étude est consultable et exportable via l'analyse locale (`DXI.CP`), avant
fermeture de l'import. D13 n'est pas annoncé reproduit. Voiles circulaires,
plusieurs détails, profils variables et chanfreins multiples hors périmètre.

Banc `t_geometries_particulieres` : PDF fictif et dimensions calculables
indépendamment, contrôles, confirmation/unicité, CP/bois, volumes et positions
3D, imbrication, DXF, WebGL, IFC relu par ifcopenshell, GLB relu, JSON v10 et
IndexedDB, quatre angles du chanfrein et blocage de toute fabrication.


## Phase 10C — fabrication du mannequin chanfreiné 45°

La V1 fabrique un seul chanfrein vertical GA / DA / DB / GB, sur une ouverture
rectangulaire traversant normalement un voile droit, orientation `vers_beton`.
`vers_vide` reste en étude. Le modèle pur `chanfrein45` de 10B reste inchangé ;
`CPI.geometriesParticulieres.chanfrein45Fabrication(parametres, provenance)`
calcule désormais les **pièces de CP**, pas seulement le volume théorique du vide.
Aucun accès au DOM, au projet ou au stockage.

### Assemblage et coupes

Repère : X = largeur L, Y = traversée e, Z = hauteur H ; A à y=0, B à y=e.
Le CP est **dans l'enveloppe du vide**. Aucun panneau ne ferme A ou B.
Les cinq familles de pièces, toutes dans le CP choisi, sont :

| Pièce logique / débit | Forme et position |
|---|---|
| C1 / J1 | Dessus pentagonal, Z = H−t à H |
| C2 / J2 | Dessous pentagonal, Z = 0 à t |
| C3 / J3 | Joue du côté chanfreiné, entre dessous et dessus |
| C4 / J4 | Joue opposée, entre dessous et dessus |
| C5 / J5 | Diagonale, entre dessous et dessus |

`t` désigne l'épaisseur CP, `r` le retrait, `k = √2−1` et `h = H−2t`.
Pour GA, la joue C3 et la diagonale se rencontrent sur le segment
`(0,r) → (t,r+kt)` : onglets opposés **22,5°**. L'autre extrémité de la diagonale
est coupée dans le plan du parement A, avec un biseau **45°**.
Les angles de scie sont mesurés depuis une coupe droite (0°).
Les autres positions sont les réflexions exactes du même assemblage.

| Panneau vertical | Face coffrante | Dos / brut avant biseaux |
|---|---|---|
| Joue C3 | longueur e−r, hauteur h | dos e−r−kt ; brut (e−r) × h |
| Joue C4 | longueur e, hauteur h | coupe droite ; brut e × h |
| Diagonale C5 | longueur r√2, hauteur h | dos r√2+t−kt ; brut (r√2+t) × h |

La face repérée est coffrante vers le béton. Sur le détail C5, l'abscisse s va
de la jonction avec la joue vers le parement ouvert, et w vers le dos du CP.
La coupe en épaisseur est `(0,0), (r√2,0), (r√2+t,t), (kt,t)`.
Le départ du dos à la jonction est kt, et son extrémité au parement est décalée
de t. Ces deux coupes ne doivent pas être remplacées par une longueur r√2
appliquée aux deux faces du panneau.

Les contours des dessus/dessous sont les pentagones complets du vide, avec une
coupe **45° dans le plan**, lame non inclinée. Toutes les coordonnées XY des
patrons sont vues du dessus de l'ouvrage assemblé ; la face coffrante du dessous
est sous son panneau. Marquer A/B et la face coffrante avant retournement.

### Calcul partagé et limites

Le contrat pur retourne les empreintes, plages Z, faces orientées, contours de
découpe, épaisseurs, contacts, angles, aire de découpe et volumes brut/net.
`chanfreinGeo` adapte ce contrat au moteur `para` :
`(x,y,z) module → (y, x−L/2, z−H/2) moteur`. Cette réflexion impose d'inverser
l'ordre des faces. Le même calcul alimente le débit, la 2D, la 3D et les exports.

Le modèle conserve les croix **50×50 existantes** de `para` et leur nombre,
sans inventer une nouvelle section ni une résistance. Elles sont réparties dans
la zone non affectée par le chanfrein : de `r+kt` à e (chanfrein en A), ou de 0
à `e−r−kt` (chanfrein en B). Leur épaisseur 50 mm et leurs contacts sont contrôlés.
Si elles ne peuvent pas être placées, la configuration est refusée.

Outre les contrôles historiques du CP et des dimensions, sont bloqués :

- H ≤ 2t, retrait nul/négatif, coin ou orientation inconnus ;
- e−r−kt ≤ 0 ou L−r−(√2+1)t ≤ 0 : joue ou ouverture dégénérée / interférence ;
- orientation différente de `vers_beton`, version inconnue, plusieurs chanfreins ;
- feuillure, biais, pente, renforts en croix supplémentaires ou absence des
  traverses 50×50 de cette V1 ;
- pièce ne tenant pas entière dans le format CP choisi : raccord non pris en charge.

La compatibilité géométrique ne valide ni la poussée, ni les fixations ou le
maintien. Les avertissements de `para` restent visibles. Aucune reprise de la
hauteur e comme hauteur de pression : H demeure la hauteur verticale.

### Débit, découpe et sorties

Le débit conserve les contours pentagonaux des deux horizontaux. Sa surface
est celle des découpes **avant biseaux** ; le volume net physique après biseaux
est distinct du brut, également dans les quantités IFC. Les joues et la diagonale
sont tracées en bruts rectangulaires avec leurs chants biseautés explicitement
cotés. `nestPieces` et `cpNest` utilisent les vrais contours, MaxRects réserve
leurs cadres englobants. Les chutes des coins ne sont pas supposées réutilisées.

Deux feuilles obligatoires donnent les cinq découpes et le détail agrandi des
biseaux, même sans annexes activées. La feuille principale distingue vide et
CP, ainsi que les élévations A/B ouvertes. Montage, débit bois, vectoriel,
WebGL et éclaté utilisent le modèle partagé. Toutes les coupes étant droites,
les coordonnées et angles permettent le traçage ; aucun faux gabarit cintré
ni assemblage de pages n'est produit.

DXF : contours réels de l'imbrication, diagonales, repères et vues cotées, en mm
(arrondi historique à 0,001 mm). GLB et IFC : vrais panneaux polygonaux/BREP,
positions, repères, dimensions et volumes conservés. Les dimensions brutes de
la diagonale sont affichées au millième de mm ; la précision du GLB reste celle
du Float32. Aucun export de fabrication pour les variantes restées en étude.

### Exemple et parcours fictifs

L=600, e=240, H=800, r=40, t=18, GA. Le vide a une aire de 143 200 mm² et un
volume de 114 560 000 mm³. Hauteur des panneaux verticaux : 764 mm.
Dessus/dessous : pentagones `(0,40), (40,0), (600,0), (600,240), (0,240)`.
Joue chanfreinée : brut 200 × 764 ; joue opposée : 240 × 764.
Diagonale : face 56,568542 mm, dos 67,112698 mm, brut 74,568542 × 764 mm.
Départ du dos à l'onglet : 7,455844 mm. Ces valeurs ne sont pas interchangeables.

Dans la proposition PDF, choisir rectangle / voile droit / solution simple /
chanfrein 45°, compléter les valeurs et le coin, choisir `vers_beton`, confirmer
les coupes et l'assemblage, arbitrer toute contradiction. L'aperçu présente les
panneaux réels. Vérifier le récapitulatif, puis confirmer la création. Aucun
ouvrage avant confirmation ; toute correction invalide le récapitulatif.
Les preuves restent conservées et un autre détail attribué reste bloquant.

Champ métier optionnel `chanfrein45:{version:1,retrait,angle,orientation}`,
épaisseur dans le CP du plan ; aucune dépendance du moteur à `origineImport`.
Formulaire manuel, duplication, IndexedDB et JSON v10 restituent les mêmes pièces.
Aucun changement de stockage ni modification imposée aux anciens projets.

Banc `t_chanfrein_fabrication` : géométries et PDF fictifs, quatre coins,
épaisseurs/retraits variables, calculs indépendants Shapely, contacts et absence
d'interférence, surfaces/volumes bruts et nets, contours 2D et DXF relus, volumes
et positions GLB/IFC, WebGL, confirmation, contradictions, provenance et persistance.
Le banc 10B conserve l'étude `vers_vide`, la feuillure et ses assertions.
Le générateur historique et les comparaisons avant/après restent inchangés.
D13 n'est pas annoncé reproduit. Essais physiques, vrais AutoCAD, Firefox/Safari
et impression réelle non vérifiés.

## Phase 11 — préparation des réservations et dossier ciblé

`preparation-ui.js` étend la fenêtre d'import et les propositions 9C–10C. Il ne
relance pas l'OCR et n'ajoute aucun calcul de fabrication. L'inventaire utilise
les lignes `NL`, les contours existants, les rapprochements et `dxcCles` : une
ligne homonyme reste distincte, les contours rattachés avec preuve fiable ou
choix explicite ne sont pas comptés une seconde fois. Les associations incertaines
restent à examiner. Le repère affiché et la référence proposée gardent les zéros
du texte source ; `dxcRep` reste la normalisation des rapprochements.

### Tableau et fiches

L'onglet **Préparation des réservations** présente les références, pages,
tableaux/vues, formes, cotes connues et manquantes, supports, détails et preuves.
Filtres : statut, page, tableau/vue, référence, forme, créées/restantes. Le bilan
compte les identités, pas les observations graphiques.

Les sept statuts sont : À examiner, À compléter, Prêt à confirmer, Validé pour
le lot, Créé, Non pris en charge, Ignoré. Un résultat calculable n'est jamais une
validation utilisateur. Les actions de navigation (précédente, suivante,
prochaine à compléter, retour au tableau) gardent chaque brouillon.

`dxcNouveau` initialise le dossier de preuves existant. `dxcProposition` et
`dxcPreparer` acceptent aussi un brouillon et ses valeurs de formulaire sans
changer le formulaire principal. La fiche individuelle et le lot appellent les
mêmes `CPI.creation.proposer/preparer/modele`, `migr`, `canon`, `limErr`, `checks`,
`voileGeo`, et les contrôles feuillure 10B / chanfrein 10C. La fonction
`dxcControlePreuves` est commune : contradictions, qualifications des détails et
preuves attribuées restent bloquantes tant qu'elles ne sont pas traitées.

Le chantier et l'ouvrage sont ceux de la fenêtre. Les modèles de fabrication
proviennent de `dxiModels`, du formulaire et des profils existants ; leur copie
est conservée par proposition. CP et montage peuvent être corrigés dans la
fiche. L'actualisation des réglages communs ne remplace pas silencieusement les
réglages des brouillons : reprise explicite dans chaque fiche. Les modèles
personnels se choisissent dans le formulaire avant l'import. Aucune épaisseur
de voile, hauteur, rayon, échelle ou particularité géométrique n'est propagée.
Les exemplaires reprennent la quantité de la ligne lorsqu'elle existe, sinon
1 exemplaire à confirmer ; une quantité nulle/illisible est bloquante.

**Valider cette proposition pour le lot** affiche le récapitulatif existant et
requiert une case de confirmation puis une validation explicite. Aucun ajout à
`P`. Le brouillon conserve cotes initiales/retenues, corrections, arbitrages,
choix, réglages, preuves et une empreinte déterministe de l'état relu. Une
modification des données, du contexte, des réglages ou des preuves invalide cet
état. L'empreinte n'est pas une signature de sécurité d'un document externe.

### Lot tout ou rien et coexistence des imports

Aucune ligne n'est présélectionnée, même après reprise d'un fichier. Seules les
propositions validées peuvent être cochées. **Créer les ouvrages validés**
affiche références, dimensions, détails, modèle, CP, montage, exemplaires et
alertes. Une seconde confirmation explicite précède l'ajout.

`dxprLot` reconstitue l'inventaire et les preuves, recalcule chaque proposition,
compare son empreinte à la validation et contrôle les identités PDF déjà créées
ou répétées. `dxiRefs` travaille sur les copies préparées pour réserver les
références automatiques et refuser les collisions avec le projet ou dans le lot.
Si une ligne échoue ou a changé depuis le récapitulatif, aucun plan n'est ajouté.
Les autres brouillons restent disponibles.

Après réussite, les plans reçoivent leurs UID et `dxcOrigine` conserve preuves,
corrections, confirmation et `creationCles`. L'ajout est effectué ensemble en
mémoire ; `profFromPlans` et la sauvegarde existante enregistrent le projet et
ses profils. Les erreurs de stockage restent signalées par les mécanismes
IndexedDB existants ; l'ajout en mémoire ne garantit pas une écriture disque en
cas de quota/conflit. Le double clic ne peut pas rejouer le lot consommé.

**Annuler le dernier lot créé** compare les ouvrages par UID et par contenu.
Si l'un a été modifié ou retiré, l'annulation est refusée. Sinon seuls ces UID
sont retirés ; les autres plans sont préservés. Les profils créés sont conservés.
L'annulation est disponible dans cette séance de préparation, pas après reprise
d'un fichier de brouillon.

L'ancien import PDF de boîtes conserve ses usages et sa confirmation historique.
Avant toute création, il appelle désormais `dxcControlePreuves` : une
contradiction ou un détail particulier ne peut pas passer par cette voie pour
éviter la qualification 10A–10C. Le message oriente vers la préparation pour
corriger/qualifier un mannequin traversant. La création individuelle reste
accessible et utilise les mêmes propositions et origines que le lot. Le bouton
historique appelle le récapitulatif du lot lorsque l'onglet Préparation est actif.
Le parcours DXF est inchangé.

### Export et reprise locaux

**Exporter la préparation** produit `coffraplan-preparation-pdf`, version 1 :
empreinte SHA-256 du PDF, nom, contexte, analyse normalisée, identités, preuves,
corrections, arbitrages, réglages, statuts d'ignorance et empreintes de validation.
Ni PDF complet, ni image de page, ni base64 du document n'y sont stockés. Aucun
brouillon n'entre dans `P` ; le projet reste en enveloppe v10.

Pour **Reprendre une préparation**, ouvrir d'abord le PDF original puis choisir
le JSON. La correspondance est vérifiée sur le SHA-256 des octets, pas le nom.
Les références de pages, contours et identités sont contrôlées ; les validations
sont recalculées et celles devenues incohérentes sont invalidées. Les identités
déjà présentes dans le projet passent à Créé. Le chargement ne crée aucun ouvrage
et ne restaure aucune sélection de lot.

L'export d'analyse historique reste disponible. Une ancienne analyse dépourvue
d'empreinte vérifiable n'est pas acceptée comme préparation confirmée : son nom
ne suffit pas à prouver qu'elle concerne le PDF ouvert. Reprendre ses données
avec le PDF, puis exporter une préparation au nouveau format.

### Dossier de fabrication sélectionné

Depuis la liste des plans, **Préparer un dossier de fabrication** présente les
plans du chantier courant par ouvrage, avec recherche de référence, tout
sélectionner/désélectionner et sélection par ouvrage. Une sélection par plan
(UID, ou identité temporaire de l'objet pour un ancien plan sans UID), sans
modification des plans. Les quantités `nb` multiplient les débits et exemplaires,
pas les lignes de plans.

`doscChoisis` fournit la seule liste transmise à `chantierData` puis à
`dossierHtml(list)`. `chantierPlans` et son repli historique ne sont pas employés
pour élargir cette sélection. L'aperçu donne plans, ouvrages, exemplaires,
panneaux/surface CP, bois et alertes. Les plans incohérents bloquent la génération.
`acChantier` accepte également cette liste explicite pour les essais du
récapitulatif existant.

Le dossier réemploie garde, sommaire, `gen`, découpes, montage, fiches atelier
selon `PRT.fa`, `chantierPages` et bon de commande consolidé. Découpes et montage
sont inclus pour ce dossier ; les options générales d'impression sont rétablies
ensuite. Les feuilles particulières 10B/10C restent présentes. Les repères et
calculs de fabrication ne sont pas modifiés. `openDossier`, `dosNumber` et
`printDossier` assurent aperçu, pagination et **Imprimer / Enregistrer au format
PDF** via le navigateur ; aucun téléchargement PDF natif n'est annoncé.
Le retour restitue le formulaire antérieur, et la génération ne modifie pas `P`.

Le dossier sélectionné demande `dossierHtml(list, true)` et génère **toutes** les
feuilles consolidées, au-delà de l'ancienne limite de 40 pages. Les sorties
historiques sans sélection gardent leur pagination. `chantierCpErreurs`, partagé
avec l'auto-contrôle, refuse les pièces non placées (référence, dimensions et
matériau affichés) ainsi que les quantités estimées sans imbrication exacte.
Au-delà de 1 500 pièces par matériau, répartir les ouvrages en plusieurs dossiers.
Une estimation de surface n'est pas un plan de découpe complet. L'aperçu signale
les estimations par « ≈ » et un avertissement ; le bouton de génération les bloque.
Une erreur de génération laisse le sélecteur ouvert avec un message de refus,
sans remplacer l'aperçu par un dossier incomplet. Les réglages d'impression sont
restitués même en cas d'erreur.


### Parcours fictif et limites

Le banc `t_preparation_chantier` crée huit lignes dans un PDF fictif : R01 complète,
R02 épaisseur manquante, R03 deux épaisseurs contradictoires, R04 feuillure,
R05 chanfrein GA fabricable, R06 orientation non fabricable, R07 multi-sections,
R08 déjà créée. Après correction/arbitrage et qualification, R01–R05 sont
validées individuellement, sélectionnées et créées ensemble. R06/R07 restent
bloquées et R08 n'est pas recréée. L'utilisateur sélectionne ensuite R01, R04 et
R05 pour un dossier qui exclut effectivement R02, R03 et R08.

Essais supplémentaires : homonymes, contours rattachés, filtres/navigation,
modification du CP, empreintes périmées, collisions, refus atomique, double clic,
annulation, export/reprise et identité du PDF, quantités et consolidation,
pagination, feuilles particulières, impression appelée et retour au formulaire,
thèmes et fenêtre Chromium 1024×768. Le correctif de relecture contrôle aussi
les 120 pièces d'un dossier fictif de 100 panneaux (plus de 40 pages consolidées),
leurs références, dimensions et positions dans le HTML réellement affiché,
l'exclusion d'un plan non sélectionné, le refus d'une pièce surdimensionnée
injectée à l'entrée du véritable MaxRects et le refus des quantités estimées.
Aucun nouveau calcul mécanique, aucun OCR,
serveur ou stockage supplémentaire. Impression physique, tablette réelle,
AutoCAD, navigateurs hors Chromium et tenue sur chantier non vérifiés.


## Phase 12 — provenance des en-têtes et recette réelle

Lors de la validation d'une grille, `CPI.ocr.versNomenclature` conserve, si
présents, les en-têtes lus dans `N.entetesSource` (copie indépendante). Les
colonnes normalisées et leur interprétation numérique restent inchangées.
`dxcAnalyse.source` transmet cette preuve à la fiche **Données et preuves
disponibles**, à l'export/reprise de préparation et à `origineImport` après
confirmation. Un en-tête OCR ambigu reste affiché tel que lu ; elle
n'autorise aucune conversion d'unité ni attribution automatique de l'ordre des
dimensions. Les anciennes préparations sans ce champ restent lisibles.

Le banc `t_recette_pdf` utilise exclusivement des données fictives. Les essais
sur documents réels et leur lecture indépendante sont conservés localement,
hors Git ; seule la synthèse anonymisée `docs/recette-pdf-phase12.md` est publiée.


La recette a également révélé qu'un texte de repère fiable ne prouve pas
l'appartenance du contour voisin. `dxnContoursLignes` résout les demandes issues
des occurrences et du sélecteur de rattachement existants. Un choix explicite
unique prime ; plusieurs demandes automatiques restent ambiguës. Deux choix
explicites du même contour constituent un conflit bloquant.

`dxcCles`, l'inventaire de préparation, les preuves de forme et l'analyse des
supports emploient ces seuls liens univoques. Un support provenant d'une
association ambiguë est ignoré et l'incertitude affichée. Le contour disputé
reste consultable mais sa création isolée demande d'abord un rattachement dans
**Nomenclature**. Les lignes conservent leurs identités propres et leurs cotes
de tableau ; une ligne créée ne transforme pas les autres en « déjà créées ».
La création d'une même ligne / d'un contour réellement rattaché reste unique.
Les anciens ouvrages, leurs cotes et leurs calculs ne sont pas modifiés.


La ligne d'hypothèses **Faces cintrées** lit le champ courant `DcuveM` ; l'ancien
champ `Dcuve` y produisait une fausse valeur nulle sans affecter la géométrie.
Le banc de recette contrôle les hypothèses et les feuilles réellement générées
sur deux cuves fictives. Aucun calcul de fabrication n'est modifié.
