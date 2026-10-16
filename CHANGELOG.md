# Historique des versions

Détail complet de chaque version (demandes, écarts voulus, tests, non validé) : `docs/historique/HANDOFF_<version>.md`.
Chaque version est un tag git (`git diff v2.4 v2.5 -- app/` pour voir les changements).

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
