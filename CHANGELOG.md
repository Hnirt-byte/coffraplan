# Historique des versions

Détail complet de chaque version (demandes, écarts voulus, tests, non validé) : `docs/historique/HANDOFF_<version>.md`.
Chaque version est un tag git (`git diff v2.4 v2.5 -- app/` pour voir les changements).

## Non publié — « Importer un plan » : fenêtre unique DXF et PDF
**Demande (Kévin, 19/10/2026)** : remplacer « Importer un plan DXF » par une entrée unique, lire les PDF (textes extractibles),
détecter leurs nomenclatures de réservations, aperçu des pages, sélection de zone, saisie assistée quand le tableau n'est pas
lisible (PDF dont les textes sont vectorisés), même création et même provenance que le DXF ; appli toujours hors connexion.

**Fait** : PDF.js 6.4.299 (Apache-2.0, build legacy) intégré tel quel au HTML par `assembler.py` (empreintes SHA-256,
`vendor/pdfjs/`), chargé à l'ouverture d'un PDF, worker lancé en `file://`, aucune requête réseau. `modules/import/pdf.js` :
textes et traits par page (rotation et matrices appliquées, Y vers le haut), nature de chaque page (texte, mixte, vectoriel,
image). `nomenclatures.js` : page et format gardés sur les tableaux, provenance PDF (`page`, `zone`, `type:'saisie'`).
Fenêtre « 📥 Importer un plan » (barre, carte Plans, accueil) : DXF ou PDF, glisser-déposer, DWG / IFC refusés avec un message ;
PDF : onglets Nomenclature et Aperçu du plan (pages, zoom, tableaux encadrés, ligne encadrée), zone à analyser, saisie
assistée, création par le même chemin (contrôles du moteur, références sans doublon, annulation). Mode d'emploi § 7.22.
Banc `tests/t_pdf.py` (PDF fictifs écrits par `tests/pdf_fictifs.py`, sans bibliothèque).

**Écarts voulus** : titre et libellés « Importer un plan DXF » / « Importer DXF » → « Importer un plan » ; t_dxf_ui vérifie le
nouveau titre et l'acceptation des .pdf (vérification modifiée, documentée ici). HTML : 1,47 Mo → 3,3 Mo (PDF.js). Moteur,
débit, feuilles et exports inchangés (t_avap).

**Essai local sur un PDF réel (19/10/2026, hors dépôt, comptes seulement)** : 2 pages tournées de 270° lues, aperçu des deux
pages correct, nomenclature visible sur la page 2 ; 125 textes extractibles pour ≈ 17 500 tracés : les textes de la
nomenclature sont dessinés en traits, aucune ligne lue, aucune inventée ; rapport « saisie assistée ». Une ligne saisie avec
des valeurs fictives a donné un ouvrage avec sa provenance (page 2). Aucune requête réseau.

**Non validé** : Firefox, Safari, tablette réelle ; PDF d'autres logiciels que le générateur de test et ce plan ; tableaux
continués sur plusieurs pages sans en-tête ; OCR (non développé).

## Non publié — nomenclatures de réservations dans l'import DXF
**Demande (Kévin, 19/10/2026)** : un vrai plan de bureau d'études donnait 772 formes pour une nomenclature de 23 réservations
placée dans une présentation. Détecter les nomenclatures de réservations (espace Objet et présentations), garder toutes leurs
lignes sans filtre, rapprocher les lignes des géométries, les proposer en priorité dans la fenêtre, provenance étendue.

**Fait** : `dxf.js` : espace de chaque entité (code 67, BLOCK_RECORD → LAYOUT : nom de la présentation), textes (TEXT, MTEXT,
ATTRIB, MULTILEADER ; codes %%c, mise en forme MTEXT retirée) et traits droits de tous les espaces, contenu des blocs insérés
et des ACAD_TABLE (bloc de rendu) transformé dans le repère de l'espace qui les contient. Détecteur : contour d'une présentation
non proposé (autre repère que le dessin). `nomenclatures.js` (nouveau) : reconstruction des tableaux (grille de traits, sinon
position des textes ; titres de colonne sur plusieurs lignes, cellules multilignes ou vides, en-tête en haut ou en bas,
plusieurs tableaux), nature décidée sur l'en-tête et le titre (tableau d'aciers ou autre : signalé, écarté), lecture des
cotes sans invention (DN ≠ ouverture, SO / à définir / « / » → manquant, niveau et angle gardés en texte), rapprochement
trouvee / probable / multiple / absente (repère texte, attribut ou flèche de ligne de repère, proximité, cotes), espace
Objet seulement. Fenêtre : onglets « Nomenclature des réservations » (par défaut) et « Géométries du dessin » (géométries
rattachées retirées), sélection libre, cotes / forme / hauteur / référence / géométrie modifiables, création par le même
chemin (adaptateur, contrôles, références sans doublon). `origineImport` d'un ouvrage de nomenclature : `type:'nomenclature'`,
espace, présentation, tableau, ligne, repère, textes des cellules, géométrie (trouvée ou choisie), choix et corrections, indice
source. Mode d'emploi § 7.22. Banc `tests/t_nomenclature.py` (DXF fictifs `tests/dxf_nomenclatures.py`, 18 scénarios).

**Essai local sur un plan réel (19/10/2026, comptes seulement, fichier hors dépôt)** : 23 lignes lues sur 23 attendues, 2
tableaux d'aciers écartés, 2 colonnes non reconnues gardées telles quelles ; chaque repère est dessiné plusieurs fois (vues,
coupes) : toutes les lignes « plusieurs possibles », jusqu'à 30 contours par ligne. Correction : les contours de mêmes cotes
sont proposés en premier (ils pouvaient tomber au-delà des 12 propositions affichées). Unité du dessin absente du fichier :
à choisir dans la fenêtre. Fenêtre ouverte sur ce plan dans Chromium : 23 lignes, aucune cochée, sans erreur JS.

**Test de bout en bout sur le plan réel (19/10/2026, hors dépôt, valeurs saisies fictives)** : scénarios rectangle complet,
DN / SO sans cotes, contours ambigus, sauvegarde / réouverture, annulation : conformes. Écart corrigé : la provenance d'une
géométrie rattachée (`origineImport.geometrie`) ne notait pas l'unité du dessin choisie dans la fenêtre, alors que `centre`
et `dims_source` sont dans cette unité ; ajout de `geometrie.unite` (clé optionnelle, anciens fichiers inchangés, moteur non
concerné). t_nomenclature vérifie la nouvelle clé.

**Écarts voulus** : un contour fermé dessiné dans une présentation n'est plus proposé comme réservation (il l'était, avec des
coordonnées de feuille). Aucun écart sur le débit, les feuilles et les exports (t_avap).

**Non validé** : création d'ouvrages à partir du plan réel ; ACAD_TABLE
réel (seule une entité minimale fabriquée est testée) ; fenêtres de présentation (VIEWPORT) non interprétées : un repère placé
seulement dans une présentation ne relie pas la ligne au dessin ; Chromium seulement.

## Non publié — import DXF dans l'appli
**Demande (Kévin, 19/10/2026)** : rendre l'import DXF utilisable dans CoffraPlan : fenêtre « Importer un plan DXF » (fichier,
unité, calques, liste et aperçu synchronisés), préparation (forme, hauteur commune ou par ligne, référence, chantier, ouvrage,
indice du plan source), création sur confirmation explicite seulement, annulable, provenance persistante dans le plan.

**Fait** : `modules/import/fenetre.js` (fenêtre, fonctions `dxi*`) ; `modules/import/assembler.py` assemble les 5 sources dans
le bloc `<script id="cpi-src">` de `app/CoffraPlan.html` (`--check` dans `tests/syntax.sh`). Appli : boutons d'accès (barre
du haut, carte Plans, accueil) ; clé optionnelle `origineImport` des plans importés, gardée par `addP` (mise à jour) et
`fixAllPlans`, retirée par `dupP`. Enveloppe du fichier projet inchangée, aucune migration (anciens plans sans la clé).
Références automatiques du lot attribuées après réservation des références du projet et de celles saisies dans le lot,
puis contrôle final avant tout ajout (relecture PR #5) ; rappel des réglages repris (CP, montage, options) avant création.
Mode d'emploi § 7.22. Banc `tests/t_dxf_ui.py` (ajouté aux suites rapides).

**Écarts voulus** : aucun sur le débit, les feuilles et les exports des plans existants (t_avap). Sur un plan importé, les
clés internes `data-vk` / `data-glk` des feuilles (empreintes du plan) incluent la provenance ; contenu identique.

**Non validé** : aucun DXF réel ni exporté par AutoCAD ; fenêtre vue dans Chromium seulement (ni Firefox, Safari, tablette).

## Non publié — lecteur DXF du module d'import
**Demande (Kévin, 18/10/2026)** : premier vrai lecteur DXF dans `modules/import/` (unités, calques, identifiants, polylignes
fermées droites, cercles, provenance), géométries ambiguës gardées en « non pris en charge », unité absente jamais devinée.

**Fait** : `modules/import/dxf.js` (DXF ASCII R12 à R2018 : LWPOLYLINE, POLYLINE + VERTEX, CIRCLE, `$INSUNITS`, table
LAYER, handles ; arcs, largeur non nulle, POLYLINE lissées (courbe ajustée, spline), blocs, 3D et autres types → « autre »
avec leur nature ; fichiers vides, binaires, tronqués ou non
DXF refusés). Détecteur : angle droit exigé (un quadrilatère croisé passait pour un rectangle), remarque « carré
potentiel ». README du module : table du décodeur, décisions de Kévin, protocole de validation sur un vrai plan. Banc
`tests/t_dxf.py` (fichiers écrits par ezdxf, chantier fictif ; ajouté aux suites rapides). `app/CoffraPlan.html` inchangé.

**Non validé** : aucun DXF réel ni exporté par AutoCAD lu ; pas d'interface d'import.

## Non publié — stabilité de t_ux (sélecteur de fichier)
**Demande (Kévin, 19/10/2026)** : trouver la cause de l'échec intermittent de t_ux (attente du sélecteur de fichier après
Ctrl+O), sans désactiver ni affaiblir le contrôle.

**Cause** : `expect_file_chooser` de Playwright active l'interception du sélecteur sans attendre l'accusé du navigateur ;
le Ctrl+O envoyé juste après pouvait ouvrir le sélecteur avant l'interception, et l'événement était perdu (30 s d'attente).
L'appli, elle, répondait bien : sur un échec reproduit, `impJ` avait cliqué le champ fichier avec activation utilisateur.

**Fait** : `tests/lib.py` (`open_app`), `t_ux` et `t_v23` (`page`) activent l'interception à la création de la page
(écouteur `filechooser` sans effet). Les contrôles sont inchangés : t_ux échoue toujours si Ctrl+O n'ouvre plus le sélecteur.
Reproduction hors banc : 1 échec sur 40 puis 1 sur 150 avant, 0 sur 150 après. `app/CoffraPlan.html` inchangé.

## Non publié — nettoyage des noms de chantiers réels
**Demande (Kévin, 18/10/2026)** : retirer des fichiers suivis les références à des chantiers réels, remplacées par des noms
fictifs (`CHANTIER_DEMO_A`).

**Fait** : t_v23 (liste des plans : groupes, tri, recherche) avec un chantier fictif, mêmes contrôles ; t_v26 : le garde-fou
vérifie tous les fichiers suivis et compare des empreintes SHA-256 au lieu d'écrire les noms ; `tests/ref/v18.html` : seul le
texte d'exemple du champ « Nom du chantier » change (référence figée, géométrie intacte) ; exemple d'en-tête du kit et capture
`kit/references/visuel-valide-original.png` retouchés ; ligne v2.6 de ce journal reformulée. `app/CoffraPlan.html` inchangé.

**Historique** : réécrit le 18/10/2026 (git-filter-repo, branches poussées en force) ; tous les SHA ont changé. Tags v2.10 /
v3.0 et Releases à recréer à la main ; copies clonées ou en cache non effaçables.

## Non publié — module d'import de plans (fondation)
**Demande (Kévin, 18/10/2026)** : préparer l'architecture d'un module d'import de plans (lecteur, détecteur de
réservations, adaptateur CoffraPlan), sans écrire l'import DXF / IFC / PDF et sans toucher aux fonctions existantes.

**Fait** : `modules/import/` (hors appli) : `lecteur.js`, `detecteur.js`, `adaptateur.js`, contrat et cartographie
(`README.md`). Banc `tests/t_import.py` (ajouté aux suites rapides) ; `tests/syntax.sh` contrôle aussi ces fichiers.
`app/CoffraPlan.html` inchangé : aucun écart de calcul, de feuilles ni d'export ; format de sauvegarde inchangé.

**Non validé** : aucun vrai fichier DXF / IFC / PDF lu ; le contrat du lecteur sera éprouvé par le premier décodeur (DXF).

## v3.0 — exports 3D / BIM, cotes d'implantation, gel avant bêta
**Demandes (Kévin, 18/10/2026)** : 1. export glTF (.glb) depuis la vue 3D et la carte Export (même modèle, m, Y vers le haut,
une pièce = un nœud nommé par son repère, un nœud par ouvrage, couleurs de la palette, assemblé ou éclaté) ; 2. export IFC4
assemblé (projet / site / bâtiment / niveau, mm, origine locale, CP = IfcPlate, bois = IfcMember, tubes et poches =
IfcBuildingElementProxy, un IfcElementAssembly par ouvrage, extrusions ou facettes, Pset « CoffraPlan » et quantités) ;
3. cotes d'implantation (axes de l'ouvrage, cotes depuis les axes, en bleu) ; 4. gel et préparation de la bêta.

**Fait**
- **glTF 2.0 binaire** (`glbFile`) : écrit sans bibliothèque (JSON + bloc binaire) ; triangulation par three.js r170 (déjà
  intégré, non modifié). Un nœud racine par ouvrage (référence du plan), un nœud par pièce nommé par son repère, matériaux PBR
  (métal 0, rugosité 0,85) aux couleurs de la palette, « extras » : repère, désignation, dimensions, épaisseur, matériau.
  Mètres, Y vers le haut. Case « éclaté » : éclaté de la vue 3D à 100 %. Boutons : carte Export (🧊 glTF) et vue 3D (⬇ glTF).
- **IFC4** (`ifcFile`, texte STEP) : IfcProject / IfcSite / IfcBuilding / IfcBuildingStorey, unités mm / m² / m³, sans
  géoréférencement ; un IfcElementAssembly par ouvrage nommé par sa référence, placé pour que le croisement de ses axes X / Y
  soit à l'origine ; pièces IfcPlate (SHEET), IfcMember (MEMBER), IfcBuildingElementProxy (USERDEFINED : Tube carton, Tube PVC,
  Poche) ; prismes extrudés (IfcExtrudedAreaSolid, profils polygonaux, cercles, couronnes, perçages des poteaux en vides),
  autres pièces en facettes (IfcFacetedBrep) ; couleurs (IfcSurfaceStyle), matériaux (IfcMaterial), Pset « CoffraPlan »
  (Repère, Désignation, Dimensions, Épaisseur, Matériau, Chantier, Référence du plan), quantités Qto_PlateBaseQuantities /
  Qto_MemberBaseQuantities / Qto_BuildingElementProxyQuantities. GlobalId déterministes (même plan → mêmes identifiants).
  Chantier : un fichier par ouvrage, réunis dans un ZIP.
- **Pièces exportées = pièces du débit** (`bimModel`, `bimSplit`, `bimTags`) : les parois plus grandes que le panneau sont
  découpées aux joints du débit (J1a, J1b… ; phase des joints des parois cintrées reprise de `jointGeo`, nouvelle clé `R.ja`),
  le fond de goulotte en n secteurs, les pièces identiques prennent le repère de leur jumelle, les autres sont rapprochées d'une
  ligne du débit par leurs cotes, leur surface ou leur famille (planches découpées de la dalle). Les cerces évidées des caissons
  de voile (4 morceaux en 3D) forment une seule pièce, comme au débit.
- **Classe IFC « coffrage »** : vérifié dans les schémas IFC4 et IFC4X3_ADD2 fournis avec ifcopenshell — aucune classe
  d'élément physique de coffrage ; seul `IfcConstructionProductResourceTypeEnum.FORMWORK` existe, pour une *ressource*
  (IfcConstructionProductResource) sans placement ni géométrie. Classes retenues : celles demandées.
- **Cotes d'implantation** (vues en plan) : axes de l'ouvrage en bleu (trait mixte) repérés X (bulle à gauche) et Y (bulle en
  haut), cotes signées depuis les axes (+ vers la droite / le haut de la feuille) ; forme spéciale avec poteaux : tableau
  d'implantation des poteaux (x, y). **Toutes les formes** (généralisation décidée par Kévin le 18/10/2026 après essai sur 3 formes).
  Origine : centre de l'ouvrage, sauf voile cintré (Y = axe radial, X = corde à mi-épaisseur), poutre (X = axe de la poutre,
  Y = milieu de la portée nu à nu, tableau des poteaux intermédiaires), parallélépipède (X = axe du voile, Y = normale au voile
  au centre ; bords de l'ouverture cotés sur les deux parements), goulotte en arc (Y = axe de symétrie, X = milieu de l'emprise).
  Voile à joues radiales : « L ext (corde) » écrite avec « L int (corde) » sous le plan, pour laisser la place aux cotes signées.
- Version v3.0 ; mode d'emploi : § 7.20 Exports 3D / BIM, § 7.21 Cotes d'implantation, captures.

**Écarts voulus** (t_avap, contre v2.10) : vues en plan de toutes les formes — cote « L/2 » et « l/2 » remplacées par des cotes
signées ±L/2, ±l/2 depuis les axes, bulles X / Y, tableaux des poteaux ; voile radial : cotes de corde regroupées ; DXF : calques
VUES_* modifiés (axes, cotes), autres calques identiques. Débit, CSV, découpe et gabarits identiques. t_v210 : contrôle du numéro de version retiré (porté par t_ux et t_v30) ; t_v26, t_v28 : « v2.x ou suivante » admet aussi v3.x ; t_ux : version v3.0.
`tests/requirements.txt` : ifcopenshell 0.9.0.post1 (tests seulement).

**Tests** : t_v30 (nouveau) : 36 scénarios + 10 plans aléatoires par forme — IFC relu par ifcopenshell sans erreur de schéma,
une pièce IFC par pièce du débit (repère et nombre), volumes CP et bois = débit (± 1 %), volume géométrique = quantité
déclarée ; GLB assemblé et éclaté (en-tête, nœuds, noms, couleurs, unités, volumes) ; boutons ; cotes d'implantation sur 22 cas (toutes les formes et variantes).
Validateur Khronos glTF (npm `gltf-validator`, hors banc) : 72 fichiers, 0 erreur, 0 avertissement.
Campagne complète (`run.py complet -j 4`, t_avap contre v2.10) : 22/22 suites OK — t_v30 5 560, t_avap 694, t_audit 1 635,
t_gab_ident 8 878, t_gab_dalle 119 753. t_v29 (transition de la vue 3D) a échoué une fois sous charge sur une série rapide,
vert seul puis dans la campagne : sensible au temps, pas lié aux cotes.

**Limites connues (bêta)**
- glTF et IFC **non ouverts dans un vrai logiciel** (Revit, ArchiCAD, BIMcollab, Solibri, visionneuse glTF) : seuls ifcopenshell
  et le validateur Khronos les ont lus.
- Pas de géoréférencement ni de files du bâtiment : l'ouvrage arrive à l'origine du projet, à déplacer à la main.
- Plans aléatoires extrêmes (3 sur 386 essayés) : un couvre-joint ou un cadre d'about non rapproché de sa ligne du débit, un
  écart de volume de CP de 1,3 % entre la 3D et le débit (préexistant, poutre).
- Poutrelles de la dalle, tubes carton et tube PVC : exportés mais hors débit (nommés « R01-poutrelle », « R01-tube carton »).
- Béton existant (contexte transparent de la vue 3D) non exporté.
- Cotes d'implantation de la poutre : pas de cotes signées ±b/2 (largeur cotée, X = axe de la poutre). Dalle avec poutres :
  axes des poutres cotés depuis le centre comme en v2.10. Lisibilité vérifiée sur captures de cas types seulement.
- Toujours non validé : impression papier réelle, DXF dans AutoCAD, Firefox / Safari, tablette réelle, Excel, carte graphique
  réelle ; règles « à valider » de `hypRows` en attente de relecture professionnelle.

## v2.10 — échelle réelle, 3D des feuilles, correctifs A4
**Demandes (Kévin, 18/10/2026)** : v2.10 cotes et échelle réelles, plus : 1. impression A4 : vues et informations
masquées ; 2. vue 3D des feuilles encore à l'ancienne qualité, toutes formes ; 3. dalle, 3D éclatée à 100 % : le platelage
disparaît au lieu de s'élever ; 4. perçage des fonds : Ø poteau + 0 mm par défaut.

**Fait**
- **Vues à l'échelle normalisée** à l'impression : chaque vue cotée à échelle unique est redessinée avec un facteur (géométrie
  réduite, cotes et textes à leur taille) pour tomber sur l'échelle normalisée immédiatement inférieure à la place disponible
  (1/1, 1/2, 1/5, 1/10, 1/20, 1/25, 1/50, 1/75, 1/100, 1/125, 1/200). Échelle écrite après le titre de la vue, barre d'échelle
  graduée, échelles de la feuille au cartouche avec « impr. 100 % A3/A4 — fabriquer aux cotes ». Réglage « Échelle des vues » :
  Normalisée (défaut) ou Agrandie à la case (comportement v2.9). Sans échelle : vues à plusieurs échelles (poutres, poches,
  goulotte, parallélépipède), plans de découpe, 3D, courbure de voile amplifiée.
- **Impression A4** : les règles d'affichage « écran étroit » (< 800 px) ne s'appliquent plus qu'à l'écran ; Chrome pouvait
  les appliquer à la page A4 imprimée (grille à une colonne → colonne Informations écrasée, vues superposées). Dimensions
  longues (« · extrémités coupées en biais… ») repliées sous la cote : la colonne Débit du voile ne part plus en « suite ».
- **3D des feuilles MONTAGE** rendue en WebGL (même moteur que la vue interactive : grain, plis, ombres), image JPEG 2500 px,
  repères, légende et rose d'orientation par-dessus ; cadrage sur l'emprise. L'impression attend les images (15 s au plus).
  Sans WebGL ou en noir et blanc : vue vectorielle.
  En aperçu, images faites 1,2 s après la dernière saisie, et pas du tout en rendu 3D logiciel (PC sans carte
  graphique : trop lent, l'aperçu garde la vue vectorielle ; l'impression fait les images).
- **Dalle en éclaté** : le platelage s'élève au-dessus des coffrages (comme un fond supérieur) au lieu de s'effacer.
- **Perçage des fonds** : jeu par défaut 0 mm (Ø poteau exact) ; les anciens fichiers sans valeur prennent 0 mm.

**Écarts voulus** (t_avap) : spéciale avec poteaux, perçages Ø poteau + 0 au lieu de + 10 (débit, CSV, découpe, feuilles) ;
dalle, feuille de montage éclatée : note « platelage masqué » retirée, repères du platelage ajoutés. t_v25 : contrôle
« Ø poteau + 10 mm » passé à « + 0 mm » (changement demandé). t_3d : la dalle passe désormais par le contrôle commun de
l'éclaté (plus de mode « masqué »), sans modification du test. t_ux : Ctrl+P attend l'ouverture de l'impression jusqu'à 20 s
(au lieu de 400 ms), l'impression attendant désormais les images 3D des feuilles.

**Tests** : t_v210 (nouveau) 109 OK ; 21/21 suites OK (t_avap 1 076, t_coh 156, t_audit 1 635, t_gab_dalle 119 753).

**Non validé** : impression papier réelle — l'échelle n'est juste que si la boîte d'impression reste à 100 % sur le même
format (la barre d'échelle permet de le contrôler) ; carte graphique réelle et tablette ; navigateurs autres que Chromium.
Cotes d'implantation (repères d'axes) non traitées.

## v2.9 — retours terrain
**Demandes (retour de Kévin du 17/10/2026)** : 1. éclaté de la dalle : joues de poutre et poutrelles en contact, vérifier
toutes les formes ; 2. spéciale circulaire avec poteaux : trous absents des fonds en 3D ; 3. impression : vues écrasées
par les cases d'information, vues prioritaires, uniformiser ; 4. légende du pied de feuille mal alignée ; 5. calepinage de
la dalle : 4 panneaux par feuille illisibles, 2 maximum, uniformiser ; 6. rendu 3D de niveau professionnel.

**Fait**
- **Pied de feuille** sorti de la grille des cases : toujours pleine largeur, libellés de la légende jamais coupés.
- **Vues prioritaires** : colonnes de largeur fixe (un tableau large ne pousse plus les vues) ; feuilles « vue + tableau »
  à 72 % / 28 % ; chaque dessin recadré sur son contenu (`fitSvgs`) ; feuille INFORMATIONS (dalle, poutre) sans vignette
  du plan, en 3 colonnes Informations | Hypothèses | Débit (pleine page).
- **CP à découper et planches découpées de la dalle : 2 panneaux maxi par feuille**, l'un sous l'autre, dessinés environ
  2 × plus grands (feuilles du plan, planches de la dalle, récapitulatif chantier).
- **Éclaté** : écartement depuis le centre, pièces rattachées (couvre-joints, lisses, tasseaux) décollées de leur paroi,
  séparation des pièces encore proches ; dalle : coffrage des poutres descendu sous les poutrelles. Contrôle : aucune pièce
  à moins de 3 mm d'une autre sur les 36 scénarios.
- **Perçages des poteaux** dessinés en 3D dans la base et le fond supérieur (y compris en écorché).
- **Rendu 3D** : grain de bois sur CP et bois, plis du contreplaqué sur les chants, lumière d'appoint (dessous lisibles),
  quadrillage du sol (500 mm), transitions douces entre vues, mise en évidence au survol.

**Écarts voulus** : t_avap compare désormais les feuilles et les CP à découper sur l'ensemble des lignes de tableaux et des
textes des dessins (et non plus le balisage) ; 43 plans gagnent des étiquettes (dessins agrandis), 4 plans voient au plus
4 étiquettes courtes déplacées (repère d'une vue éclatée, numéros) ; débit, contrôles, CSV, DXF inchangés. t_gab_dalle :
lecteur des feuilles de planches adapté à 2 panneaux par feuille (cellule 640).

**Tests** : t_v29 (nouveau) 80 OK ; 20/20 suites OK (t_avap 1 010, t_coh 156, t_audit 1 635, t_gab_dalle 119 753).

**Non validé** : impression papier réelle (rendus PDF Chromium A3 et A4 contrôlés), navigateur autre que Chromium (la
règle `:has()` des colonnes demande Chrome 105+, Firefox 121+, Safari 15.4+), carte graphique réelle.

## v2.8 — vue 3D WebGL
**Demande** : 3D de niveau professionnel (choix : three.js).

**Fait**
- Vue 3D interactive rendue par la carte graphique (three.js r170, MIT, intégré au fichier, chargé à la première ouverture,
  hors connexion) : éclairage, ombres portées au sol, parois courbes lisses (normales radiales, sans hachures de facettes),
  arêtes vives seulement. Même modèle, même caméra, mêmes commandes (vues, éclaté, types, repères, clic, clavier, tactile).
- Étiquettes posées sur une partie visible (lancer de rayon), clic → pièce et repère.
- Légende et fiche de la pièce : nombre de **pièces** (une coque en facettes = 1 pièce) au lieu du nombre de facettes.
- Repères : chaque ligne CP du débit portée par une pièce 3D de mêmes cotes ; lignes sans pièce repérée passées de 92 à
  17 sur 155 plans (restent : planches découpées de la dalle, regroupées par panneau ; tronçons de parallélogramme).
- Sans WebGL : rendu vectoriel d'avant, mêmes fonctions. Feuilles imprimées et DXF : rendu vectoriel inchangé.

**Écarts voulus** (t_avap : 26 plans) : étiquettes de repères supplémentaires sur la feuille de montage.

**Tests** : t_v28 (nouveau) 15 OK ; 19/19 suites OK (t_avap 1 064, t_coh 156, t_audit 1 635).

**Non validé** : carte graphique réelle (tests sur rendu logiciel SwiftShader), tablette, performances sur un PC ancien.

## v2.7 — cohérence
**Demande** : avant commercialisation, améliorer la 3D, la cohérence des plans et les fonctions ; ordre retenu :
cohérence (v2.7), 3D three.js (v2.8), cotes et échelle réelles (v2.9), export 3D / BIM et gel bêta (v3.0).

**Fait**
- **Revue de cohérence croisée** (`tests/t_coh.py`, 155 plans : 36 scénarios + 10 plans aléatoires par forme) : chaque
  pièce du débit retrouvée dans les pièces à découper (aire), l'imbrication (aucune pièce non placée), le modèle 3D
  (volume de CP et de bois ± 1 %), le CSV et le DXF (repères).
- Écart trouvé et corrigé : **poches des poutres** dessinées en 3D comme un bloc plein alors que le débit compte un caisson
  CP (dessous, 2 côtés, fond) → caisson CP modélisé, repères J… au clic, volume 3D = débit.
- Écart trouvé, reporté en v2.8 : sur 37 plans sur 155, certains repères du débit ne sont portés par aucune pièce 3D
  (cloisons en tronçons, goussets, pièces de poche multiples, panneaux de platelage) ; liste dans `tests/out/coherence.json`.

**Écarts voulus** (t_avap : 13 plans, expliqués) : 3D des poutres et dalles avec poutres (poches), donc feuille de montage et vue 3D du DXF. Débit, plans, CSV inchangés.

**Tests** : t_coh 156 OK (nouveau, dans les suites rapides) ; 18/18 suites OK (t_avap 1 051, t_audit 1 635, t_gab_dalle 119 751).

## v2.6 — crédibilité
**Demandes** : étape « crédibilité » de la feuille de route — calcul de flèche du CP, note d'hypothèses, cartouche
d'entreprise, enregistrement dans un vrai fichier, noms de chantiers réels retirés. CP par défaut : filmé phénolique
classe 3 (EN 636-3), 18 mm.

**Fait**
- Catalogue CP par âme : **filmé bouleau** (défaut ; WISA-Form Birch, Riga Form, Metsä Form), filmé combi, filmé
  peuplier / eucalyptus, CTBX okoumé, cintrable. Rigidités publiées : Koskisen (bouleau, combi ; mêmes valeurs UPM
  WISA-Form Birch), FCBA POB 21.02 (okoumé humide). Pas de valeur retenue pour le peuplier / eucalyptus et le cintrable.
- **Flèche des joues** des boîtes rectangulaires (`flecheCP`, `plateW`) : plaque (Ritz) appuyée aux angles, aux cloisons CP
  pleine hauteur et au pied, bord haut libre, poussée hydrostatique ; module mini (sens du fil non garanti) ; × 1,5
  (EN 1995-1-1, contreplaqué en classe de service 3) ; cisaillement calé sur le tableau de charges Riga Form 03/2026
  (−6 % … +13 %). Critère portée / 300 (fabricants), réglable dans le profil chantier. Alerte ⚠ + correction
  automatique (cloisons CP, CP plus épais). Hypothèses et note : valeurs et sources.
- **Note d'hypothèses** (carte Plans) : synthèse chantier (plans, hypothèses générales, limites, sources, visas) + une
  feuille A4 portrait par plan (poussée, renfort le plus sollicité, flèche, hypothèses, contrôles restants).
- **Cartouche entreprise** (carte Impression) : nom, ligne libre, dessinateur, logo ; cases Vérifié / Visa et
  « Non à l'échelle — fabriquer aux cotes » sur toutes les feuilles de plan. Enregistré dans le navigateur et dans le
  fichier projet (clé `ent`, format v 10 inchangé ; les versions précédentes ignorent cette clé).
- **Enregistrement direct** (Chrome / Edge, File System Access) : Ctrl+S réécrit le fichier choisi ou ouvert ;
  Ctrl+Maj+S = enregistrer sous ; autres navigateurs : téléchargement comme avant.
- Exemple de nom de chantier réel remplacé par un nom fictif.

**Écarts voulus** (t_avap 148 plans : tous expliqués) : désignation « CP filmé bouleau » (feuilles, débit, CSV, DXF) ;
nouvelle alerte de flèche sur 35 plans du banc (boîtes sans cloisons ou hautes) ; bloc entreprise du cartouche.
t_regress : 3 scénarios documentés (2 alertes de flèche, 1 désignation). Bancs : enregistrement par téléchargement
forcé dans `lib.open_app`, t_ux et t_v23 (`NOFS`) ; t_ux attend la clé `ent` ; t_v25 : ligne « Flèche du CP » calculée.

**Tests** : t_v26 (nouveau) 34 OK ; 16 suites existantes OK (dont t_audit 1 635, t_gab_dalle 119 751).

**Non validé** : enregistrement direct dans un vrai Chrome / Edge (testé avec un faux fichier) ; flèche à confronter à
des mesures ou à un bureau d'études ; logo d'entreprise à l'impression papier.

## v2.5 — mise en page des feuilles
- Réglage « Mise en page des feuilles » : **Plan pleine page** (défaut, feuille 1 = vues seules + feuille 1b débit ·
  informations · hypothèses), **Compacte** (mise en page v2.4), **Vues uniquement**.
- Ligne d'hypothèses dans le cartouche ; case Hypothèses (`hypRows`) : valeur et origine de chaque hypothèse.
- Calculs, débit, gabarits, DXF, CSV, 3D inchangés (t_avap identique en compacte).

## v2.4 — passe complète
- Cartes repliables, accueil, série depuis un tableau, comparaison de deux indices, mode chantier tablette.
- Mannequin de voile : renfort minimal quand un côté est plus grand que l'autre. Axe des poteaux de la spéciale :
  200 mm par défaut.
- Feuilles annexes décochées et sommaire « Jamais » par défaut ; DXF lisible avec txt.shx (AutoCAD).
- Audit : code mort retiré, cache de géométrie de la goulotte, avertissement si le stockage est plein.
- Retouche : police + 2 pt dans les cases Débit et Informations.

## v2.3 — confort
- Plan modifié non mis à jour signalé, fenêtres de l'application à la place de celles du navigateur, liste des plans
  (recherche, regroupement, tri), aperçu non bloquant.

## v2.2 — identité CoffraPlan
- Logo, favicon, thème clair / sombre / auto, rappel de sauvegarde, alertes cliquables, raccourcis clavier.

## v2.1
- Messages sans incidence sur la fabrication retirés ; poteaux de la forme spéciale traversant base et fond supérieur ;
  revue des fonctions avancées.

## v2.0
- Gabarits 1:1 alignés sur les plans de découpe (dalle de couverture en priorité).

## v19
- Forme « Puisard avec fond » supprimée (doublon), anciens plans migrés ; campagne gabarits ↔ débit.

## v18
- Gabarits relatifs au repère ● du panneau, vue éclatée du voile cintré, bouton Exporter unique (DXF, CSV, XLSX, ZIP),
  renforts et poutres complétés.

## v17
- Gabarits 1 pièce = 1 page, poutres ≤ 7 m, auto-contrôle avec corrections, 3D interactive, DXF + dossier PDF,
  palette de couleurs actée.
