# Module d'import de plans (fondation, hors appli)

État : **squelette et contrat seulement**. Aucun décodeur DXF / IFC / PDF n'est écrit. Le module n'est **pas** inclus dans
`app/CoffraPlan.html` : l'appli, ses résultats et son format de sauvegarde sont inchangés. Banc : `tests/t_import.py`.

| Fichier | Composant | Dépend de |
|---|---|---|
| `lecteur.js` | A. Lecteur de plan : fichier source → document normalisé | rien |
| `detecteur.js` | B. Détecteur : document normalisé → réservations **potentielles** | rien |
| `adaptateur.js` | C. Adaptateur : réservation **confirmée** → plan CoffraPlan contrôlé par le moteur | moteur reçu en paramètre |

Chaque fichier est du JS vanilla (ES2017), sans DOM ni stockage, et s'enregistre dans un seul espace de noms global
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
Rectangle reconnu : contour fermé de 4 sommets (5 si refermé), côtés opposés et diagonales égaux à `tol` près (0,5 % de la
diagonale). Cercle : `r > 0`. Tout le reste : `non_pris_en_charge`, avec la raison et la géométrie conservée.
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

## 3. Fichiers séparés et HTML autonome (étude, rien de mis en place)

Constat : l'appli n'a pas d'étape de construction et doit rester un seul fichier hors connexion. Le module vit à part pour
être testé seul. Quand il entrera dans l'appli, proposition d'assemblage local déterministe, sans dépendance :
- un script Python (bibliothèque standard) remplace un bloc balisé dans `app/CoffraPlan.html`, par exemple
  `<script id="cpi-src">…</script>` placé avant le `<script>` principal, par la concaténation de `lecteur.js`,
  `detecteur.js`, `adaptateur.js` dans cet ordre ;
- mode `--check` (en CI) : échoue si le bloc du HTML diffère des sources ; le HTML reste la seule chose livrée ;
- `app/CoffraPlan.html` reste éditable à la main, seul ce bloc est généré.
Comparé à un bundler (esbuild, Rollup) : inutile pour 3 fichiers sans import, et ajouterait des dépendances npm à maintenir.

## 4. Intégration progressive proposée

1. **Fait** : contrat, squelette, banc `t_import` sur objets fictifs.
2. Lecteur DXF (R12 / 2000+ ASCII) : `LWPOLYLINE`, `POLYLINE`, `CIRCLE`, `$INSUNITS`, calques ; arcs → `autre`.
   Testé sur des DXF produits par `ezdxf` (déjà dans `tests/requirements.txt`) puis sur de vrais plans de Kévin.
3. Bloc `cpi-src` + script d'assemblage + `--check` en CI ; aucune fonction encore visible.
4. Fenêtre « Importer un plan » calquée sur `openSeries` : liste des candidats (✓ / à compléter / non pris en charge),
   filtre par calque, saisie de `h`, choix de la forme, confirmation ligne par ligne, création par le chemin de `serCreate`.
5. Décision à prendre avec Kévin : garder ou non la provenance dans le plan (nouvelle clé → migration dans `migr`).
6. IFC (`IfcOpeningElement`, hauteur connue), puis PDF vectoriel après étude.

## Limites et non vérifié
- Aucun fichier DXF / IFC / PDF réel lu : le contrat A est un choix de conception, à éprouver avec le premier décodeur.
- Hypothèses : réservation rectangulaire → coffrage `rect` / `carre` sans fond par défaut ; cercle → fourreau `circ`.
  Les autres formes (voile cintré, poutre, goulotte…) ne sont pas reconnues.
- Orientation (`angle`) et position (`centre`) ne sont gardées que dans la provenance : un plan CoffraPlan n'a pas de
  position absolue.
- `limErr` lit le libellé d'unité dans le formulaire pour ses messages : sans formulaire, le message dirait « mm ».
