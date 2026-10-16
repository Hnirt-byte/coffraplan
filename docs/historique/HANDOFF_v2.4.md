# HANDOFF v2.4 — CoffraPlan (passe complète)

Fichier livré : `CoffraPlan_v2.4.html` (base v2.3, fichier unique). Tests : `tests_v2.4/` (Playwright + Chromium, ezdxf).

## Demandes
Passe complète : audit technique ; formulaire repliable + accueil ; série depuis un tableau ; comparer deux indices ;
mode chantier tablette ; défaut de la spéciale (axe poteaux). Ajouts en cours de passe : renfort du mannequin de voile
quand un côté est plus grand que l'autre ; feuilles annexes décochées par défaut ; sommaire « Si > 5 feuilles », défaut
« Jamais » ; DXF vu dans AutoCAD (caractères « ? », titres).

## 1. Métier (écarts voulus, documentés)
- **Mannequin de voile** (`manGeo`) : au moins un renfort perpendiculaire au plus grand côté. Largeur entre joues >
  hauteur des joues et aucun montant par l'entraxe → 1 montant au milieu (reprend la portée de l'appui et du linteau) ;
  hauteur > largeur et aucune cerce → 1 cerce à mi-hauteur. Entraxe saisi à 0 (= aucun) respecté. Côtés égaux : rien.
  Ex. R03 (corde 670, h 270) : 1 montant 63 × 75 L 234 au débit bois, sur le plan et en 3D (sans interpénétration).
- **Forme spéciale** : axe des poteaux par défaut 300 → 200 mm (poteaux Ø 200 dans la forme concentrique Ø 800 :
  plus d'alerte à l'ouverture). Plans existants inchangés (valeur enregistrée).
- **Impression** : Feuilles CP à découper, Montage 3D, Fiche atelier, Noir et blanc décochés par défaut ; sommaire
  « Jamais » par défaut, option « Si > 5 feuilles » (au lieu de 3). Un navigateur où ces cases ont déjà été modifiées garde
  son réglage.

## 2. Audit technique
- Code mort retiré (12 fonctions jamais appelées : xlsxBlob, zipStore, travLen, gabFit, pip2, chantierSheets, pieceTags,
  debitCSVSelfTest, nestCount, platePoly, normPoly, jouePiecesSelfTest), retrait vérifié par analyse syntaxique (acorn).
- Performance : `gouGeo` appelé ~11 fois par recalcul de goulotte (≈ 55 ms chacun) → cache (8 entrées) : recalcul
  goulotte ≈ 750 → ≈ 200 ms ; elle ne passe donc plus en « aperçu en attente » (t_v23 : 51 vérifications au lieu de 56,
  la partie « forme lourde » devient sans objet ici).
- Robustesse : écriture refusée par le navigateur (stockage plein / bloqué) → message une fois par session, au lieu
  d'une perte silencieuse.
- Sécurité : textes hostiles (balises HTML) dans chantier, ouvrage, repère, indice, modèle, tableau collé → aucun
  écran n'exécute ni n'insère quoi que ce soit (16 écrans testés).
- DXF : la police par défaut d'AutoCAD (txt.shx) n'a pas — × · → ≈ « » ’ … : remplacés (- x - -> ~ " ' ...) ;
  Ø ° ± écrits en codes AutoCAD %%c %%d %%p. Titres de section : titre court + sous-titre, même hauteur dans tout le
  fichier (d'après la largeur des panneaux, agrandie pour les grands plans), écarts entre sections réduits.
  Géométrie inchangée (t_avap : entités par calque identiques).

## 3. Interface
- **Cartes repliables** (Chantier, Type, Dimensions, Contreplaqué, Options, Impression, Traceur, Plans) : clic ou
  Entrée sur le titre, résumé d'une ligne quand repliée, état mémorisé ; une alerte vers un champ d'une carte repliée
  la déplie.
- **Accueil** (aucun plan) : 3 étapes, 3 modèles courants, série, charger, raccourcis ; « Masquer » mémorisé.
- **Série depuis un tableau** (bouton dans « Plans » et accueil) : coller depuis Excel (tabulations, « ; » ou « , »),
  en-tête facultatif (Réf · Forme · L · l · h · Ø · Nombre · Ouvrage · Indice · Désignation ; sans en-tête : Réf, Forme,
  L, l, h, Nombre). Forme reconnue par nom, abréviation ou synonyme (fourreau → circulaire…), déduite des cotes si
  absente. Contrôle ligne par ligne (bornes, incohérences, référence déjà utilisée, colonne sans objet) avant
  création ; lignes en erreur non créées ; « Annuler » 10 s. Chantier obligatoire ; autres réglages = plan affiché.
- **Comparer deux indices** (bouton « ⇄ Comparer » du plan affiché ; même repère proposé par défaut) : feuille A4
  imprimable — saisies différentes, lignes de débit modifiées / ajoutées / supprimées (surlignées), contrôles nouveaux /
  levés, case visa.
- **Mode chantier** (📱 dans la barre) : plein écran, une feuille à la fois ajustée à la largeur, ‹ › / flèches /
  balayage, choix du plan, lecture seule, « ✓ Repères » à cocher par plan (compteur, gardés dans ce navigateur, hors
  fichier projet).

## Retouche (même version)
- Cases « Débit · traçage · contrôles » et « Informations » des feuilles (`.inf`) : police + 2 pt (écran et impression,
  titres et notes compris). À l'impression, l'ajustement automatique existant réduit la police si une case déborde
  (ex. voile cintré : 8,7 px) ; aucune feuille « suite » ajoutée sur les plans types.

## Tests (Chromium)
| Suite | Résultat |
|---|---|
| t_v24 (**nouveau** : renfort mannequin, défauts, audit, DXF / txt.shx, repli, accueil, série, comparaison, mode chantier) | 90 OK |
| t_avap v2.3 / v2.4 (148 plans) | 953 OK — écarts tous expliqués : DXF de 131 plans (textes / titres, géométrie identique par calque) ; special_rect (axe des poteaux par défaut) |
| t_ux / t_v23 / t_ui | 87 / 51 / 41 OK |
| t_audit (420 plans) / t_regress / t_special / t_3d | 1 635 / 36 / 153 / 145 OK |
| t_renforts / t_poutre / t_export / t_forme | 207 / 50 / 29 / 16 OK |
| t_gab_ident / t_gab_dalle | 8 878 / 119 751 OK |

**Correction du banc** : en v2.3, `t_avap.py` comparait par erreur la v2.2 à elle-même (chemin par défaut de la version
« après » non mis à jour). Corrigé ; comparaison v2.2 / v2.3 refaite : 958 OK, sorties identiques (le constat livré en v2.3
est donc confirmé).
Bancs de test : `lib.py`, `t_ux.py`, `t_v23.py` activent les feuilles annexes (désormais décochées par défaut) pour
continuer à en couvrir le contenu.

## Non validé
DXF ouvert dans AutoCAD réel (rendu vérifié avec ezdxf seulement) ; tablette réelle (balayage simulé à la souris) ;
Firefox / Safari ; impression papier.
