# HANDOFF v2.1 — Plans de Réservation – Coffrage Bois

Fichier livré : `v2.1_Plans_Reservation_Coffrage.html` (base v2.0). Tests : `tests_v2.1/` (Playwright + Chromium).

## Demandes
1. Retirer les messages sans incidence sur la fabrication ; spéciale circulaire : faux conflit poteaux / forme concentrique ;
   les poteaux traversent la base et le fond sup. jusqu'à leurs limites basse et haute.
2. Revue complète des fonctions avancées, tests, corrections.

## 1. Poteaux de la forme spéciale
- **Hauteur** : du dessous de la boîte (0) au dessus du fond sup. (ou en tête sans fond sup.) en automatique (`specGeo().zPt`).
  Saisie manuelle = hauteur depuis le dessous. Migration v11 → v12 : h saisie + épaisseur de base (même niveau de tête).
- **Fonds percés** : base (toujours) et fond sup. (si la tête du poteau le dépasse), perçage = Ø poteau + jeu (champ
  « Perçage des fonds : Ø poteau + », 10 mm par défaut). Perçages portés par le débit (note de ligne), l'imbrication
  (y compris fonds en morceaux : un perçage à cheval sur un joint est reporté sur les deux morceaux), la feuille CP À DÉCOUPER
  (cercles + centres depuis ● dans le tableau), le gabarit 1:1 des fonds circulaires (perçages, axes centre → P1…Pn), le DXF
  (calque CP_PERCAGES), la 3D (perçages pris en compte dans les collisions), la coupe et le texte de montage.
- **Conflit avec la forme concentrique** : signalé seulement si le poteau coupe la PAROI (bois) de la forme concentrique ;
  poteau entièrement dedans ou dehors : rien. Message chiffré (axe, paroi).
- Supprimés : « Hauteur poteau > hauteur intérieure », « Poteaux entrent dans le fond supérieur », « les angles font foi »
  (en angles personnalisés, le nombre de poteaux = nombre d'angles, champ « Nombre » masqué ; aucun angle → erreur).
- Tubes carton pleins pour les collisions (`cyl`) : les tasseaux de joint s'interrompent au droit des poteaux (ils
  traversaient les tubes).

## 1 bis. Messages retirés (information déjà au débit / au plan, ou conseil sans incidence sur la fabrication)
joue > panneau → n longueurs (poutres) ; tronçon de coffrage très court ; raidisseurs très courts ; boîte sans gousset à
envisager ; biais + pente ; angle > 45° ; tronçons sur cadres de joint (parallélépipède) ; goussets sans objet / aucun gousset ;
niveau du fond sup. ramené en tête ; goussets > 1/3 ; aucune joue ; planches recoupées (entraxe conseillé) ; option poutres
sans poutre ; cerces de caisson (aucune intermédiaire) ; joues parallèles en biais (angle désormais dans la ligne de débit
« Joues pleine hauteur ») ; montants coupés au droit des cerces ; rive en bandes raboutées.
Conservés : erreurs géométriques, flambement, poteaux hors boîte / qui se chevauchent / qui coupent une paroi, goussets en
conflit, planches sur moins de 3 poutrelles, pièces plus étroites que le minimum, cintrage du CP non cintrable, poches, etc.

## 2. Revue des fonctions avancées
- `t_audit.py` (**nouveau**) : 420 plans aléatoires plausibles (13 formes × 30, toutes options) passés dans plan, contrôles,
  débit, imbrication, feuilles de découpe, 3D, gabarits, DXF, XLSX, CSV, corrections, auto-contrôle intégré, rechargement du
  formulaire. 0 exception, 0 valeur illisible, auto-contrôle conforme, débit cohérent (quantités, cotes, surfaces, repères).
- `t_ui.py` (**nouveau**) : boutons réels — ajouter / dupliquer / supprimer, annuler / rétablir, sauvegarde et chargement JSON
  (identiques), profil de chantier, bibliothèque, dossier PDF, récapitulatif et auto-contrôle chantier, corrections
  automatiques (+ annulation), déplacement à la souris, vue 3D, impression, brouillon.
- Corrigés pendant la revue :
  - conseil de flambement : ne propose plus une section qui ne suffit pas (v19-v2.0 : « passer en bois 63 × 175 » alors
    que 63 × 175 flambait aussi) ; sinon « ajouter des butons intermédiaires ou faire vérifier » ;
  - bornes : unité « mm » affichée pour un nombre (« Nombre de poteaux = 0 hors limites (1 mm → 48 mm) ») ;
  - lignes de perçage lisibles (retour à la ligne) dans les tableaux des feuilles CP À DÉCOUPER ;
  - code mort retiré (`flott`).

## Tests (Chromium)
| Suite | Résultat |
|---|---|
| t_audit (420 plans) | 1 635 OK / 0 KO |
| t_ui | 41 OK |
| t_special (**nouveau**, 10 cas poteaux) | 153 OK |
| t_gab_ident / t_gab_dalle | 8 878 / 119 751 OK |
| t_3d / t_renforts / t_poutre / t_export / t_forme | 145 / 207 / 50 / 29 / 16 OK |
| t_regress (36 scénarios vs v19-v2.0) | 36 OK — écarts volontaires listés dans `VOLONTAIRES` |

## Non validé
Impression réelle et assemblage des gabarits ; DXF en CAO ; Firefox / Safari ; Excel.
Hypothèse : jeu de perçage 10 mm par défaut (épaisseur du tube carton + jeu) — réglable, à confirmer selon les tubes utilisés.
