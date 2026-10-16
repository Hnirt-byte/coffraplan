# HANDOFF v2.2 — CoffraPlan (ex « Plans de Réservation – Coffrage Bois »)

Fichier livré : `CoffraPlan_v2.2.html` (base v2.1, fichier unique autonome : logo et favicon intégrés, aucune ressource
externe ajoutée). Tests : `tests_v2.2/` (Playwright + Chromium).

## Demandes (prompt « COFFRAPLAN » + kit graphique)
Identité CoffraPlan · rappel de sauvegarde · alertes cliquables + raccourcis + aide · thème clair / sombre / auto.
Contrainte : aucun changement du moteur métier, du format de fichier, des exports ni de l'impression.

## 1. Identité
- Barre supérieure : logo du kit (`coffraplan-logo-barre-navigation.svg`) intégré en SVG, recadré (viewBox 0 10 362 66),
  30 px de haut, proportions conservées. « Coffra » suit le thème (`--logo-t` : blanc en sombre, bleu nuit en clair),
  « Plan » reste orange. Largeur des mots fixée (`textLength`) : mise en page identique quelle que soit la police installée
  (Inter n'est pas fourni par le kit).
- Écran < 800 px : pictogramme seul (même SVG, `preserveAspectRatio="xMinYMid slice"` + largeur 36 px), libellés des
  boutons masqués (icônes + infobulles), barre sur une ligne jusqu'à 360 px.
- Favicon : SVG du kit + PNG 32 px en data URI. Identifiants des dégradés préfixés `cpl`.
- Titre de l'onglet « CoffraPlan — Plans de coffrage » ; pied des feuilles « Conçu par Kévin TRINH · Conducteur de travaux ·
  CoffraPlan » ; fichier de sauvegarde `coffraplan_AAAA-MM-JJ.json`.
- Conservés volontairement : clé `app:'plans-reservation'` et `v:10` dans le .json, clés localStorage `resa*`
  (compatibilité des sauvegardes existantes, comme demandé dans le LISEZ_MOI du kit).
- Couleurs : l'orange de l'appli (#e8820c) est gardé (il est dans toutes les feuilles imprimées) ; le logo garde son
  orange #ff8517. Écart minime, volontaire.

## 2. Thèmes
- Sélecteur « ◐ Auto / ☀ Clair / ☾ Sombre » dans la barre. Défaut : Auto (`prefers-color-scheme`, suivi en direct).
  Choix mémorisé (`localStorage.resaTheme`). Appliqué par un petit script dans `<head>` avant les styles : pas de flash.
- Une seule palette de variables CSS par thème (`:root` / `:root[data-theme=light]`) ; nouvelles variables :
  `--acct` (orange des textes, foncé en clair pour le contraste), `--redt`, `--okt`, `--hi`, `--logo-t`.
  Couleurs claires codées en dur dans l'interface remplacées par ces variables.
- Non touchés par le thème : feuilles de plan (`.ps`, couleurs fixes), boutons d'écran posés sur les feuilles (couleurs
  fixées), vue 3D (`#v3d` garde le jeu sombre), fenêtre des gabarits 1:1, impression (fond blanc).

## 3. Rappel de sauvegarde
- « Modifié » = le contenu du fichier .json (plans + profils + modèles) diffère de la dernière sauvegarde ou du dernier
  chargement (empreinte FNV-1a, `localStorage.resaSavedH`). Revenir à l'état sauvegardé = plus modifié. Le formulaire non
  enregistré, le choix du plan affiché, le thème, la souris, l'aide ne comptent pas (rien de nouveau à sauvegarder ;
  le brouillon du formulaire reste gardé dans le navigateur comme avant).
- Indicateur : pastille orange sur 💾 + bandeau existant du panneau (reformulé).
- Rappel (encart en bas à droite) 5 min après la 1re modification non sauvegardée de la session ; « Plus tard » (ou Échap)
  = nouveau rappel 15 min plus tard ; jamais par-dessus une fenêtre ouverte ou la vue 3D ; jamais à l'ouverture ni après
  un chargement sans nouvelle modification.
- Fermeture / rechargement de l'onglet avec modifications : avertissement du navigateur (`beforeunload`).
- Sauvegarde = mécanisme existant (`expJ`, téléchargement), format inchangé. État remis à « sauvegardé » seulement si le
  fichier a été généré et remis au navigateur sans erreur. Pas de sauvegarde automatique.
- Reprise d'un navigateur v2.1 : ancien compteur `resaDirty` = 0 → sauvegardé ; > 0 → modifié ; puis supprimé.

## 4. Raccourcis, alertes cliquables, aide
| Raccourci | Action |
|---|---|
| Ctrl/⌘ + S | Sauvegarder (actif aussi pendant une saisie) |
| Ctrl/⌘ + O | Charger un projet |
| Ctrl/⌘ + P | Imprimer avec la mise en page de l'appli (`printAll`) au lieu de l'impression brute du navigateur |
| Ctrl/⌘ + Z | Annuler (historique existant : formulaire + plan affiché ; dans un champ en cours de frappe : annulation native) |
| Ctrl/⌘ + Y, Ctrl/⌘ + Maj + Z | Rétablir |
| Échap | Ferme l'aide « ? » d'un champ, la fenêtre ouverte, « Plus tard » sur le rappel, sinon quitte le champ |
| ? | Fenêtre d'aide des raccourcis (hors saisie) ; aussi bouton « ? » de la barre |
| Entrée | Sur une alerte sélectionnée : aller au champ |
Vue 3D : ses touches existantes (flèches, + / −, Échap) restent prioritaires.
- Alertes ⚠ / ⛔ du panneau : un clic (ou Entrée) amène au champ concerné, le sélectionne et le surligne 1,6 s, sans rien
  modifier. Erreurs de bornes : champ exact. Contrôles : table `CHKF` (poteaux, concentrique, renforts, goussets,
  cintrage, poutres, lisse haute, entraxe poutrelles, feuillure, fond sup., traverses de cerce). Alerte sans champ
  identifié : non cliquable.
- États : focus clavier visible (contour orange), survol, désactivé (curseur interdit), infobulles et libellés
  accessibles sur toutes les commandes de la barre.

## Correction hors demande
- `liveCalc` plantait (« Cannot read properties of null (reading 'N') ») quand des renforts sont demandés sans aucune barre
  posée : le panneau d'alertes n'était alors plus mis à jour. Présent en v2.1 (vu par intermittence dans t_ui).
  Garde ajoutée (affichage seulement).

## Tests (Chromium)
| Suite | Résultat |
|---|---|
| t_ux (**nouveau** : identité, thèmes, rappel avec horloge simulée, raccourcis, alertes, aide, contrastes ≥ 4,5, feuille et impression identiques au pixel en sombre / clair) | 87 OK / 0 KO |
| t_avap (**nouveau** : v2.1 / v2.2 sur 148 plans, 956 sorties : contrôles, débit, feuilles, CP à découper, gabarits, DXF, CSV) | 958 OK — identiques |
| t_audit (420 plans) / t_ui (×3) / t_special / t_3d | 1 635 / 41 ×3 / 153 / 145 OK |
| t_regress (36 scénarios) / t_renforts / t_poutre / t_export / t_forme | 36 / 207 / 50 / 29 / 16 OK |
| t_gab_ident / t_gab_dalle | 8 878 / 119 751 OK |

## Non validé
Firefox / Safari (favicon SVG non pris en charge par Safari, PNG en secours) ; rendu du logo avec la police réelle du
poste ; impression papier réelle ; avertissement de fermeture (Chrome ne l'affiche qu'après une interaction avec la page) ;
raccourcis sous macOS testés par simulation de ⌘ uniquement. Hors connexion : les polices Google (déjà présentes avant)
sont remplacées par les polices du système.
