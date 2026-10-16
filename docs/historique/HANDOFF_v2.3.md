# HANDOFF v2.3 — CoffraPlan

Fichier livré : `CoffraPlan_v2.3.html` (base v2.2, fichier unique). Tests : `tests_v2.3/` (Playwright + Chromium).
Demande : axes a, b, c, e de la revue UX (plan modifié non mis à jour, fenêtres de l'appli, liste des plans, aperçu non bloquant).
Moteur métier, format de fichier, exports et impression inchangés (t_avap v2.2 / v2.3 : 956 sorties identiques).

## a. Plan affiché modifié mais pas mis à jour
- Référence = formulaire tel que chargé depuis le plan (`setForm(P[EI])` puis `coll()`, mis en cache par contenu du plan) :
  pas de faux signalement sur les plans anciens ou migrés (120 plans v2.2 de toutes formes ouverts : 0 faux positif).
- Bouton « ✔ METTRE À JOUR R01 » (l'icône 💾 reste réservée à la sauvegarde du fichier) ; pastille rouge et ligne
  « ● R01 modifié — non enregistré dans le plan » quand le formulaire diffère du plan ; « R01 affiché — aucune modification » sinon.
- Revenir à la valeur d'origine (saisie ou Ctrl+Z) retire le signalement.
- Ouvrir un autre plan avec une saisie en cours : message « R01 : modifications non enregistrées laissées de côté · Revenir »
  (10 s) ; « Revenir » rouvre R01 avec la saisie. Recliquer le plan déjà affiché ne l'écrase plus.
- Ctrl+S avec un plan modifié : le message de sauvegarde précise que ces modifications ne sont pas incluses.
- Après rechargement de l'onglet (brouillon restauré), le signalement est recalculé.

## b. Fenêtres de l'appli (0 boîte du navigateur)
- `uiDlg` / `uiAlert` / `uiConfirm` / `uiPrompt` (couche `#dlg`, au-dessus des autres fenêtres) : titre, message explicite,
  boutons nommés (« Enregistrer quand même », « Remplacer », « Tout supprimer » en rouge…), Entrée / Échap,
  focus clavier gardé dans la question (Tab / Maj+Tab), raccourcis neutralisés pendant une question.
- Messages d'information → message discret (toast) ; champ manquant ou illisible → message + curseur dans le champ.
- Supprimer un plan : immédiat, « Plan R03 supprimé · Annuler » pendant 10 s (rétabli à sa place). Tout supprimer : question
  puis « Annuler » possible.
- `addP(asNew, ok)` : les deux confirmations (référence en double, incohérences) relancent `addP` avec l'étape validée.
  `fixAllPlans(go)`, `impJ` (fonction `apply`), `libSave` et la mise à jour des plans d'un ouvrage (profil) : même principe.
- `toast(m, action, fn, ms)` accepte un bouton d'action.

## c. Liste des plans
- Recherche (tous les mots, sans accents) sur chantier, ouvrage, référence, désignation, indice, forme ; compteur « n / N ».
- Regroupement chantier · ouvrage (ordre alphabétique, effectif par groupe) ; tri dans chaque ouvrage : saisie / référence
  (ordre naturel : R2 avant R10) / forme ; tri mémorisé (`localStorage.resaSort`).
- Nom de la forme sous la référence ; plans accessibles au clavier (Tab, Entrée) ; la recherche ne relance ni calcul ni historique.

## e. Aperçu non bloquant
- Si le dernier recalcul (contrôles + aperçu) a pris plus de 300 ms, la frappe dans un champ texte ne relance plus le calcul :
  aperçu grisé + bandeau « ✎ Aperçu en attente — Entrée ou Tab pour recalculer (ou cliquer ici) ». Recalcul à Entrée, à la
  sortie du champ, au clic sur le bandeau ; listes et cases recalculent tout de suite (« ⏳ Calcul de l'aperçu… »).
- Formes légères : comportement inchangé (recalcul pendant la frappe). Mesuré ici : goulotte ≈ 700-800 ms, dalle
  ≈ 400-500 ms (contrôles) → mode « en attente » ; rectangulaire ≈ 20 ms.
- Pendant l'attente, les alertes du panneau ne sont pas recalculées (elles le sont à la validation du champ).

## Tests (Chromium)
| Suite | Résultat |
|---|---|
| t_v23 (**nouveau** : a, b, c, e par l'interface ; aucune boîte du navigateur ; 120 plans v2.2 sans faux signalement) | 56 OK |
| t_avap (v2.2 / v2.3, 148 plans, 956 sorties) | 958 OK — identiques |
| t_ux / t_ui | 87 / 41 OK |
| t_audit / t_special / t_3d / t_regress / t_renforts / t_poutre / t_export / t_forme | 1 635 / 153 / 145 / 36 / 207 / 50 / 29 / 16 OK |
| t_gab_ident / t_gab_dalle | 8 878 / 119 751 OK |
Tests modifiés (changement volontaire d'interface) : t_ui et t_ux cliquent « OK » dans la fenêtre de l'appli là où
`confirm` / `prompt` étaient acceptés automatiquement ; t_ux attend « v2.3 ».

## Non validé / limites
Firefox / Safari ; durée réelle du recalcul sur ton poste (seuil 300 ms fixe) ; Échap n'annule toujours pas un déplacement à la souris en cours.
