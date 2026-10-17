# Historique des versions

Détail complet de chaque version (demandes, écarts voulus, tests, non validé) : `docs/historique/HANDOFF_<version>.md`.
Chaque version est un tag git (`git diff v2.4 v2.5 -- app/` pour voir les changements).

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
- Exemple « STEP SCEY » remplacé par un nom fictif.

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
