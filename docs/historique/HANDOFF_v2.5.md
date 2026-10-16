# HANDOFF v2.5 — CoffraPlan

Fichier livré : `CoffraPlan_v2.5.html` (base v2.4). Tests : `tests_v2.5/`.

## Demande
Ne pas charger les plans avec les hypothèses : regrouper « Débit · traçage · contrôles », « Informations » et
« Hypothèses » sur une feuille à part ; réglage au choix. Défaut : « Plan pleine page » ; autres choix : « Compacte »,
« Vues uniquement ».

## Fait
- **Réglage « Mise en page des feuilles »** (carte Impression, aide « ? ») — `PRT.lay` = `full` (défaut) | `compact` | `views`,
  mémorisé dans le navigateur (`resaPrint`).
  - *Plan pleine page* : feuille 1 = vues seules (vue de dessus sur toute la largeur, vues B et A sur une demi-largeur
    chacune) ; **feuille 1b** juste après : débit · traçage · contrôles | informations | hypothèses (au dos en recto-verso
    si le plan démarre sur une page recto).
  - *Compacte* : mise en page historique (identique à la v2.4, vérifié).
  - *Vues uniquement* : vues seules, pas de feuille 1b.
  - Formes multi-feuilles (dalle, poutre…) : les feuilles CP à découper gardent leur tableau des pièces ; le tableau du
    plan de pose (calage des rangées) passe sur la feuille INFORMATIONS en pleine page ; pas de feuille INFORMATIONS en
    « vues uniquement ». Les hypothèses s'ajoutent sous « Informations ».
- **Ligne d'hypothèses dans le cartouche** de toutes les feuilles (3 modes) : poussée hydrostatique 25 kN/m³ × h · CP
  utilisés · tolérances et parement selon CCTP (+ « détail feuille 1b » en pleine page).
- **Case Hypothèses** (`hypRows`) : hypothèse, valeur retenue, origine (Norme · Calcul · Saisie · Règle de l'appli — à
  valider · Fournisseur · Marché) — poussée (EN 1991-1-1), CP, flèche du CP **non vérifiée**, renforts (Euler, coeff. 3,
  effort et Ncr calculés), goussets automatiques (règle à valider), mannequin de voile (entraxes, renfort minimal,
  fibre neutre), cintrage (fiche fournisseur), poteaux (perçage), raidisseurs de poutre (règle à valider), platelage,
  trait de scie, montage, tolérances / parement (CCTP), étaiement (hors périmètre).
- Calculs, débit, CP à découper, gabarits, DXF, CSV, 3D : inchangés.

## Tests (Chromium)
| Suite | Résultat |
|---|---|
| t_v25 (**nouveau** : 3 modes × 7 formes, feuille 1b, ligne d'hypothèses, contenu des hypothèses, impression sans débordement) | 64 OK |
| t_avap v2.4 / v2.5 en mise en page compacte (ligne d'hypothèses neutralisée) | 1 090 OK — identiques |
| t_v24 / t_ux / t_v23 / t_ui | 90 / 87 / 51 / 41 OK (désormais en pleine page par défaut) |
| t_audit (420 plans, auto-contrôle de lisibilité compris, en pleine page) / t_regress / t_special / t_3d | 1 635 / 36 / 153 / 145 OK |
| t_renforts / t_poutre / t_export / t_forme / t_gab_ident / t_gab_dalle | 207 / 50 / 29 / 16 / 8 878 / 119 751 OK |

## Non fait / limites
- Recto-verso : la feuille 1b tombe au dos du plan si le plan commence sur une page recto ; avec plusieurs plans et des
  feuilles annexes en nombre impair, un plan peut commencer sur un verso (pas de page blanche ajoutée).
- Note d'hypothèses complète (document) : à rédiger à partir de `hypRows` + revue des règles du code.
- Mode d'emploi : §4 et §7.13 à mettre à jour (mise en page).
