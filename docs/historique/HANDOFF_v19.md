# HANDOFF v19 — Plans de Réservation – Coffrage Bois

Fichier livré : `v19_Plans_Reservation_Coffrage.html` (base v18). Tests : `tests_v19/` (Playwright + Chromium, shapely, ezdxf, openpyxl).

## Demandes v19

1. **Suppression de la forme « Puisard avec fond »** (doublon de « Carré avec fond »).
2. **Campagne poussée gabarits 1:1 ↔ plan de débit des planches**, dalle de couverture en priorité.

## 1. Puisard

- Option retirée du sélecteur, des listes `RECT` / `FOND` / `LIM_RECT`, des titres `TM`, de l'auto-test des repères.
- Modèle de bibliothèque remplacé par « Puisard carré avec fond 600 × 600 × h 500 » (forme carré avec fond).
- **Migration** (`migr`, appliquée aussi par `setForm` et au chargement d'un modèle de bibliothèque) : ancien plan `puisard`
  → `carre_fond` si L = l, sinon `rect_fond` (l'ancienne forme acceptait L ≠ l).
- Preuve du doublon : le scénario de non-régression `puisard` reconstruit en carré avec fond donne un débit **identique** à la v18
  (W, CP, bois) ; `t_forme.py` vérifie aussi un puisard 1200 × 700 (→ réservation avec fond) et un puisard à feuillure.

## 2. Gabarits dalle — défauts trouvés et corrigés

| # | Défaut v18 | Effet chantier | Correction v19 |
|---|---|---|---|
| 1 | Gabarits « corde » (arc en diagonale) **dessinés en miroir** | A posé sur A, B sur B : l'arc tracé du mauvais côté de la corde (dans la pièce, écart = 2 × flèche) | A → B orienté pour que l'arc soit à gauche ; gabarit posé face imprimée visible |
| 2 | Pièce dont les deux extrémités de la coupe droite sont sur le cercle (demi-disque, segment) : la corde prise pour un arc | Gabarit absurde, cote de coupe droite absente de la feuille de débit | `dalArcRuns` : un arc = suite d'arêtes dont le milieu est aussi sur le cercle |
| 3 | Pièce à plusieurs arcs (petites dalles) : un seul arc pris | Arc manquant | Un gabarit par arc (« ARC 1/2 ») |
| 4 | Repères d'arc espacés jusqu'à 790 mm le long de l'arc sur arcs raides (stations toujours sur un seul axe) | Traçage à la latte imprécis | Arc découpé en tronçons plats (stations X) / raides (stations Y) : écart ≤ pas × √2 |
| 5 | Intersections cercle / bord ignorées à < 0,5 mm d'un coin | Contour faux jusqu'à 18 mm près du coin, extrémité d'arc non repérée | Intersections conservées jusqu'aux coins |
| 6 | Arc trop long pour la page (A3, A4, petit rouleau) : gabarit non imprimable | « trop grande » | Gabarits partiels successifs dont les extrémités sont des repères ● de la feuille de débit (déjà tracés) |
| 7 | Cote d'arc pouvant tomber sous le panneau | Confondue avec une cote de coupe verticale | Cotes d'arc forcées dans le cadre du panneau |
| 8 | Coin intérieur au cercle à < 0,6 mm pris pour un point d'arc | Repère hors panneau (X = −1) | Tolérance 0,05 mm (sommets d'arc calculés exactement) |
| 9 | Code mort `gabDraw` / `gabDalleD` (v16, sans repères) et `dalTrace` | — | Supprimés |

A / B des gabarits corde : cotes au 1/10 mm + rappel du repère ● de la feuille CP À DÉCOUPER quand A / B en est un.
Mesures des repères sur gabarit corde : amorce de 12 mm au lieu de lignes traversant le gabarit.
Pas des repères : lisibilité 24 px (au lieu de 26) → pas de 250 mm aussi sur CP 2500 × 1525 et 3000 × 1500.

## Tests

| Suite | Objet | Résultat |
|---|---|---|
| `t_gab_dalle.py` (+ `gabx.js`, `gabcheck.py`) | **Nouveau.** Vérification géométrique indépendante (shapely) : 32 configurations ciblées + 60 aléatoires (graine 19) | 119 870 OK / 0 KO |
| `t_gabarit.py` | Gabarits toutes formes (v18) — cas dalle A3 retiré (couvert par t_gab_dalle) | 3 021 OK |
| `t_forme.py` | **Nouveau.** Suppression / migration du puisard | 16 OK |
| `t_regress.py` | Débit v19 = v18 (`ref_v18.json`), 36 scénarios | 36 OK |
| `t_3d`, `t_renforts`, `t_poutre`, `t_export` | inchangés | 145 / 207 / 50 / 29 OK |

La même campagne `t_gab_dalle` lancée sur la v18 : **1 107 KO sur 22 configurations / 32** (preuve qu'elle détecte les défauts
que l'ancien test, circulaire car il comparait le gabarit à la même fonction `dalMarks`, laissait passer).

### Modifications de tests (documentées)
- `t_gabarit.py` : configuration dalle A3 retirée (suppose un gabarit par pièce ; les parties d'arc sont contrôlées par t_gab_dalle).
- `t_regress.py` : référence = v18 (l'historique v17 → v18 reste dans tests_v18).
- `gabcheck.py` : rayon de rattachement d'une cote à son repère 30 → 40 px (positions candidates des libellés jusqu'à ~35 px).

## Non validé
Impression traceur réelle, ouverture DXF en CAO, Firefox / Safari, Excel (inchangé depuis v18).
