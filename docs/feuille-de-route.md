# Feuille de route vers une version commerciale

Ordre proposé ; chaque étape se termine par des tests verts et une version taguée.

Audit technique et feuille de route de modernisation (phase 6, 21/10/2026) : `docs/audit-modernisation.md`.

1. **Fondations du dépôt** (fait en octobre 2026) : sources, tests, CLAUDE.md, mode d'emploi généré, CI.
2. **Crédibilité métier** (v2.6 : flèche des boîtes rectangulaires, note d'hypothèses, cartouche, noms retirés — faits)
   - Note d'hypothèses complète (à partir de `hypRows` et des règles du code), relue par un chef coffreur ou un
     bureau d'études.
   - Calculs manquants : flèche du CP entre renforts ; poussée réduite selon DIN 18218 (à acheter légalement) en
     option.
   - Conventions de dessin : échelle indiquée, cartouche d'entreprise, indices et visa, cotes d'implantation.
   - Noms de chantiers réels retirés.
3. **Version 3.0 — gel avant bêta** (liste fermée, décidée le 17/10/2026) :
   - v2.7 cohérence : revue croisée débit / découpe / 3D / CSV / DXF (fait) ;
   - v2.8 3D avec three.js : rendu (lumière, ombres, arêtes), cylindres lisses, toutes les pièces repérées au clic,
     compteurs en pièces, éclaté propre, tubes et poteaux lisibles ;
   - v2.9 retours terrain de Kévin (éclaté, perçages en 3D, mise en page des feuilles, rendu 3D) (fait) ;
   - v2.10 échelle réelle : vues cotées à une échelle normalisée à l'impression, indiquée sous la vue et au cartouche,
     barre d'échelle ; 3D des feuilles en WebGL ; correctifs A4 (fait). Reste : cotes d'implantation (repères d'axes) ;
   - v3.0 export glTF puis IFC, gel, mode d'emploi à jour, début de la bêta.
   Tout le reste : après la bêta.
4. **Application installable** (Tauri) : fichiers projet sur disque à la place du stockage navigateur,
   installeurs Windows et macOS, mises à jour signées. La clé de signature reste chez Kévin, sauvegardée deux fois.
5. **Bêta** chez 3 à 5 entreprises : retours, corrections, mode d'emploi relu.
6. **Commercialisation** : licence hors ligne signée (période de grâce, lecture seule à expiration), version Light,
   site vitrine, paiement par un revendeur (Paddle ou Lemon Squeezy), canal de mises à jour bêta / stable.
7. Plus tard : quantitatifs et coûts, flèche des autres formes.
