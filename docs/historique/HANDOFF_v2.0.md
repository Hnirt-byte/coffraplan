# HANDOFF v2.0 — Plans de Réservation – Coffrage Bois

Fichier livré : `v2.0_Plans_Reservation_Coffrage.html` (base v19, version affichée dans l'en-tête). Tests : `tests_v2.0/`.
Numérotation : v19 était la dernière « vNN » ; on passe en v2.x.

## Demande
Les gabarits 1:1 ne correspondaient pas aux plans de découpe → solution « en une fois ».
Décisions utilisateur : pas de gabarit pour les coupes droites ; collage accepté ; anciens gabarits « outils » supprimés ;
priorité dalle de couverture (la pièce en cause dépendait de plusieurs paramètres).

## Cause
Les gabarits v19 étaient calculés à part, depuis la forme de l'ouvrage, et non depuis les pièces de la feuille CP À DÉCOUPER :
- voile : une plaque entière (G1, 3080 mm) au lieu des morceaux S1a, S1b, F1a… dessinés sur les panneaux ;
- fond circulaire : bouts d'arc « à faire pivoter » au lieu des demi-fonds F1a / F1b ;
- goulotte : « G1 segment de fond » sans plan de découpe correspondant ;
- spéciale circulaire : **aucun gabarit** alors que la feuille contient des pièces cintrées ;
- dalle : gabarits « corde » tournés suivant l'arc (exacts depuis v19, mais d'un autre aspect que la feuille).

## Solution v2.0 : le gabarit EST la pièce de la feuille CP À DÉCOUPER, en vraie grandeur
- `cutNest(d,R)` : une seule imbrication pour les feuilles CP À DÉCOUPER **et** les gabarits (mêmes pièces, mêmes positions,
  y compris le cas « pour 1 exemplaire, à répéter »).
- `polyArcs(P)` : arcs d'une pièce lus sur son contour (suites d'arêtes lisses), cercle exact, extrémités recalculées à
  l'intersection avec l'arête droite voisine → tracé exact même si le polygone de débit est grossier.
- `gabNestPieces` : un gabarit par repère et par orientation ; cadre = encombrement de la pièce sur le panneau ; graduations
  depuis le coin ● du cadre ; **toutes** les positions du coin du cadre depuis le coin ● de chaque panneau (= tableau de la
  feuille CP À DÉCOUPER) ; repère au nom de la feuille (R01-S1a…).
- `gabDallePieces` : planches D dans le repère du panneau (zone des arcs + 100 mm, ou pièce entière), repères ● identiques
  à la feuille (dalMarks). Plus de corde inclinée ni de parties d'arc.
- `gabTiles` / `gabCrosses` : pièce plus grande que la feuille → feuilles à assembler (recouvrement 20 mm, bande bleutée,
  croix ✚ visibles sur les deux feuilles), rouleau / A3 / A4.
- `gouNest` : nouvelle feuille « CP À DÉCOUPER — FOND DE GOULOTTE » (même calepinage que le débit, tête-bêche si retenu),
  reprise dans le DXF et dans les gabarits.
- `circPoly` : nombre de côtés adapté (flèche ≤ 0,05 mm) ; 72 côtés fixes en v19 → jusqu'à 1,4 mm d'écart sur un fond Ø 3 m
  (feuille de débit et DXF).
- Supprimés : `gabVoile`, `gabCirc`, `gabGoulotte`, `gabArcBand`, `gabDalle` (arc générique), `gCtrl`, gabarits corde / parties.
- Textes de montage et aide de la fenêtre gabarit mis à jour.

## Tests (Chromium)
| Suite | Objet | Résultat |
|---|---|---|
| `t_gab_ident.py` | **Nouveau.** Identité feuille CP À DÉCOUPER ↔ gabarit, 21 cas × rouleau / A3 / A4 : complétude, position = tableau, contour, évidement, cadre, rayons exacts, aucune pièce droite, pages 1:1, feuilles qui couvrent tout, recouvrement 20 mm, croix | 8 878 OK / 0 KO |
| `t_gab_dalle.py` | Campagne dalle (31 config. ciblées + 60 aléatoires), adaptée à v2.0 | 119 751 OK / 0 KO |
| `t_regress.py` | Débit v2.0 = v19 (36 scénarios) | 36 OK |
| `t_forme`, `t_3d`, `t_renforts`, `t_poutre`, `t_export` | inchangés | 16 / 145 / 207 / 50 / 29 OK |

`t_gab_ident` lancé sur la v19 : 48 KO sur 63 cas — aucun gabarit ne correspond à une pièce de la feuille (42 cas) et
aucun gabarit pour les pièces cintrées de la spéciale circulaire (6 cas).

### Modifications de tests (documentées)
- `t_gabarit.py` (v18-v19) retiré : il testait les anciens générateurs supprimés ; remplacé par `t_gab_ident.py` + `t_gab_dalle.py`.
- `t_gab_dalle.py` : configuration « arc générique » retirée (fonction supprimée) ; message « dalle rectangulaire » adapté ;
  contrôle des pages = chaque gabarit imprimé (plus de « trop grande ») ; contrôle des arcs DXF par cercle de rayon imposé
  (centre ajusté, écart ≤ 0,1 mm), robuste aux arcs courts et aux demi-cercles.
- `t_regress.py` : référence = v19 (`ref_v19.json`).

## Non validé
Impression réelle (traceur, A3 / A4) et assemblage des feuilles ; DXF en CAO ; Firefox / Safari ; Excel.
