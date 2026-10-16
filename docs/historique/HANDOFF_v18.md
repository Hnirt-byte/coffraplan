# HANDOFF v18 — Plans de Réservation – Coffrage Bois

Fichier livré : `v18_Plans_Reservation_Coffrage.html` (HTML mono-fichier, JS vanilla, un seul `<script>`). Base : v17.
Tests : `tests_v18/` (Playwright Python + Chromium, shapely, ezdxf, openpyxl, LibreOffice pour la relecture XLSX).

## État des tests (2026-10-10, Chromium uniquement)

| Suite | Objet | Résultat |
|---|---|---|
| `syntax.sh` | `node --check` du script | OK |
| `t_gabarit.py` | gabarits 1:1 ↔ plan de débit (dalle, voile, toutes formes à gabarit) | 3247 OK / 0 KO |
| `t_3d.py` | vue éclatée de toutes les formes, goussets dans la réservation, cerces du caisson | 145 OK / 0 KO |
| `t_regress.py` | débit v18 = v17 hors changements volontaires (liste `VOLONTAIRES`) | 30 OK / 0 KO |
| `t_renforts.py` | renforts 3D ↔ débit (nombre, longueurs, côté, repères), 36 scénarios | 207 OK / 0 KO |
| `t_poutre.py` | lisses basse/haute 63×75, raidisseurs, option « sous poutrelle » | 50 OK / 0 KO |
| `t_export.py` | menu Exporter : DXF, CSV, XLSX, ZIP relus (ezdxf / openpyxl / LibreOffice) | 29 OK / 0 KO |

Lancement : `cd tests_v18 && bash syntax.sh && python3 t_xxx.py` (chaque suite < 2 min sauf t_gabarit/t_renforts : lancer en arrière-plan).
Erreurs JS de la page (pageerror + console.error) remontées en KO par `lib.py`.

## Modifications par point

1. **Gabarits 1:1 ↔ débit** — cotes A/B des planches découpées (mode corde) désormais relatives au repère ● du panneau (v17 : relatives au coin de la pièce → faux). `dalMarks()` partagé entre débit et gabarit. Contour des plaques voile = `platePolyRaw()` (décalage radial exact des joues), évidement et joints de découpe affichés. Discrétisation des arcs : flèche ≤ 0,1 mm (précision DXF).
2. **Voile cintré** — vue éclatée : toutes les pièces s'écartent (`exVec3`, vecteurs absolus/parents) pour toutes les formes. Goussets du mannequin replacés dans le plan tangent à mi-rayon, côté intérieur de la joue (sortaient de 76 mm à L corde 3000). Caisson : croix bois/goussets remplacés par des **cerces CP au gabarit évidées** (`caisCer`, entraxe ≤ 600, rive 100), au débit, au plan, en coupe et en 3D.
3. **Export** — un seul bouton 📤 Exporter à côté de Dossier PDF : DXF (plan / calepinage chantier), CSV, XLSX, ZIP (plan affiché ou chantier). JSON renommé « 💾 Sauvegarder ». **DWG non généré** (voir décisions).
4. **XLSX** — classeur 4 onglets : Synthèse (à commander), Débit CP (blocs par plan, sous-totaux, total), Débit bois (total ml), Barres bois. En-têtes figés, filtres, largeurs, paysage ajusté en largeur, titres répétés, pied de page.
5. **Renforts** — massif : lisses sur les 4 côtés en 3D. Système commun `jointGeo()` des renforts de joint (couvre-joints, lisses, tasseaux) partagé débit/3D avec évitement des obstacles ; équerres de rive en 3D ; renforts interrompus au droit des poteaux (spécial). Contrôle automatique 3D ↔ débit sur 36 scénarios.
6. **Poutres** — lisses basse et haute 63×75 contre chaque joue, raidisseurs entre lisses (dont un à chaque joint de joue). Option « lisse haute sous les poutrelles » + hauteur de poutrelle, appliquée à toutes les poutres du plan ; contrôle bloquant si la place restante < 100 mm.

## Décisions

- DWG : format propriétaire. LibreDWG n'écrit de façon stable que r2000 et antérieur (manuel GNU) ; ODA File Converter = licence non claire (essai 60 j mentionné). → pas de DWG généré ; procédure : ouvrir le DXF dans AutoCAD / BricsCAD / DraftSight puis « Enregistrer sous… DWG ».
- Caisson : cerces CP au gabarit (choix utilisateur).
- Joues de poutre découpées : joints au droit d'un raidisseur, pas de couvre-joint.
- Contraintes maintenues : pas de collage/tuilage des gabarits ; tube carton ne monte pas au haut de la poutre ; termes interdits absents.

## Modifications de tests (documentées, pas pour masquer un défaut applicatif)
Faux négatifs corrigés dans les tests : bandes d'arc des formes circulaires, somme des surfaces de plaques évidées découpées, centre d'arc, filtre des poutrelles voisines, `text-transform: uppercase` dans un contrôle de texte.

## Non validé (à contrôler manuellement)
- Impression traceur des gabarits 1:1 (mesurer une cote ≥ 1 m au mètre ruban).
- Ouverture des DXF dans un vrai logiciel de CAO (validé seulement par ezdxf).
- XLSX ouvert dans Excel (validé par openpyxl + LibreOffice).
- Firefox / Safari / mobile.
- Goulotte : rendu lent (~550 ms), préexistant en v17.

## Architecture (repères pour la suite)
- Patches v18 appliqués par script Python (remplacement exact avec compte d'occurrences).
- 3D : `model3()`, rôles `base/wall/ring/top/in/ctx`, `exVec3`/`explode3`, registre des parois `s.jw` (`reg()`), `joint3()`.
- Débit : `debit()`, `R.jg` (renforts de joint), `r.cells` (plaques découpées).
- Poutres : `bmPar` (`lhs`, `hpt`), `bmBuild` (`zLH`), `bmDebit`, `beam3`, `bmSecDraw`.
- Export : `xlsxBook`, `debitData`, `debitXlsx`, `zipBytes`, `exportFiles`, `openExport`.
