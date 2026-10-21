# Stockage des projets (phase 7)

Ce document décrit où CoffraPlan garde les projets dans le navigateur. Il détaille la migration depuis l'ancien stockage, la gestion des erreurs et des conflits, et ce qui a réellement été essayé en `file://`.
Code : `app/CoffraPlan.html`, fonctions `sto*` (après `svP`). Essais : `tests/t_stockage.py`.

## 1. Principe
- **Stockage principal : IndexedDB.**
  - Base `coffraplan`, version de schéma **1**, magasin `projet`.
  - La clé `courant` contient le projet entier :
    `{schema, rev, date, app, onglet, plans, profils, modeles, ent}`.
    Les plans, profils, modèles et le cartouche entreprise sont écrits **en une seule transaction**.
  - La clé `meta` contient `{schema, migration:{etat, date, empreinte, plans}, ignorees:[empreintes]}`.
- **Données de travail en mémoire.**
  - `P`, `PROF`, `LIBU` et `ENT` restent en mémoire, et les calculs restent synchrones.
  - `svP`, `svProf`, `svLib` et `svEnt` demandent une écriture (`stoSauver`).
- **Écritures en file.**
  - Une seule écriture à la fois. Chacune lit l'état **le plus récent** au moment d'écrire.
  - Plusieurs modifications rapides donnent une ou deux écritures, et jamais le retour d'une version plus ancienne.
- **Révision `rev`.**
  - Chaque écriture vérifie, dans la même transaction, que le projet enregistré est encore celui que l'onglet a lu ou écrit.
  - Sinon, l'écriture est **refusée** et signalée (« Modifié ailleurs »). Aucune écriture n'est faite sans un choix explicite.
  - **Forçage** (« Garder la version de cet onglet », confirmé) : autorisation **à usage unique**, limitée à la révision que l'utilisateur
    a vue (`STO.forcer = {rev}`), retirée dès l'écriture suivante, **même si elle échoue**. Une révision plus récente écrite ensuite
    ailleurs provoque un nouveau refus.
- **Format du fichier de sauvegarde inchangé** : `{app:'plans-reservation', v:10, date, plans, profils, modeles, ent}`.
- **Préférences d'affichage non concernées** : thème, tri, impression, cases du mode chantier, brouillon du formulaire et suivi de la sauvegarde externe (`resaSavedH`, `resaExpAt`) restent dans `localStorage`. Ce sont de petites valeurs propres au navigateur.

## 2. Démarrage (`stoDemarrer`), dans l'ordre
1. L'ancien stockage est lu : les clés `resa3`, `resaProf`, `resaLib` et `resaEnt`, leur empreinte et leur validité.
2. La base est ouverte. En cas d'échec, le mode passe à **`local`** :
   - même enregistrement que les versions précédentes (`localStorage`) ;
   - indicateur « ⚠ Stockage de secours » et bandeau « enregistrement automatique fiable indisponible ».
3. La base est relue. En cas d'échec, le mode passe à **`bloque`** : aucune écriture, pour ne rien écraser, avec un bandeau qui propose l'export.
4. Copie de secours (voir § 4) :
   - une seule copie (ou plusieurs copies identiques) prolongeant exactement le projet enregistré (même `rev` de départ) : reprise,
     puis effacée une fois enregistrée ;
   - copie identique au projet enregistré : effacée ;
   - **plusieurs copies différentes de même révision de départ** (onglets fermés pendant un enregistrement) : aucune reprise, aucune
     suppression ; fenêtre « Copie(s) de secours non reprise(s) » : export de chaque copie séparément, reprise d'une copie sur
     confirmation seulement, « Décider plus tard », suppression sur confirmation ;
   - toute autre copie : présentée de la même façon, jamais appliquée d'office.
5. Si le projet enregistré existe, il est ouvert. L'ancien stockage est ensuite comparé :
   - **déjà migré ou écarté** par l'utilisateur (empreinte connue) : rien ;
   - **illisible** : bandeau ; il n'est ni transféré ni modifié, et peut être exporté tel quel ;
   - **identique** au projet enregistré (cas d'une migration interrompue avant sa marque) : la migration est marquée réussie ;
   - **différent**, **même sans plan ni modèle** (projet vidé volontairement, profils ou cartouche seuls) : **conflit**. Un projet
     enregistré n'est jamais remplacé d'office par l'ancien stockage. Rien n'est remplacé. Une fenêtre propose d'exporter les deux, de garder le projet enregistré, de reprendre l'ancien stockage (avec confirmation) ou de décider plus tard (question reposée à l'ouverture suivante).
6. S'il n'y a pas de projet enregistré mais un ancien stockage valide : **migration**. La création est contrôlée dans la transaction :
   si un autre onglet a créé le projet entre-temps, elle est refusée ; le projet existant est ouvert, la migration simplement marquée
   s'il est identique à l'ancien stockage, sinon le choix est proposé.

## 3. Migration (`stoMigrer`), non destructive
1. L'ancien stockage est lu avec les mêmes conversions que les versions précédentes (`migr` sur chaque plan).
2. Il est copié dans `courant` (`rev` 1).
3. L'écriture est **relue**.
4. Le contenu relu est **comparé** au contenu copié (plans, profils, modèles, cartouche).
5. La **marque** `meta.migration` est écrite (état `ok`, empreinte de l'ancien stockage).
6. Un message est affiché : « … transféré(s) vers le nouveau stockage du navigateur (ancien stockage conservé) ».

L'ancien stockage n'est **jamais** modifié ni supprimé dans cette phase.

En cas d'échec à n'importe quelle étape :
- le mode passe à `local`, et les projets restent ouverts depuis l'ancien stockage ;
- un bandeau indique l'erreur et l'étape, et propose « Exporter le projet » et « Réessayer » ;
- au lancement suivant, une copie déjà faite mais non marquée est reconnue identique, puis marquée.

## 4. Erreurs et récupération
| Cas | Comportement |
|---|---|
| IndexedDB absent ou bloqué | mode `local` (ancien enregistrement, limité), indicateur « ⚠ Stockage de secours », bandeau, sauvegarde fichier proposée |
| Écriture refusée (quota, erreur du navigateur, transaction interrompue) | projet enregistré intact ; modification gardée dans la page ; indicateur « ⚠ Non enregistré », bandeau, message (une fois par séance) ; nouvelle tentative à la modification suivante ou par « Réessayer » ; export toujours possible |
| Données de l'ancien stockage invalides | non transférées, non modifiées ; exportables telles quelles (`coffraplan-ancien-stockage-brut`) ; « Ne plus le signaler » possible |
| Migration interrompue | voir § 3 |
| Plusieurs onglets ou plusieurs copies du HTML (en `file://`, tous les fichiers locaux partagent la même base dans Chromium) | l'autre onglet est prévenu (`BroadcastChannel`, et une relecture au retour sur l'onglet) ; son écriture est refusée tant qu'il n'a pas rechargé ; choix : recharger, exporter, ou garder sa version (confirmation) |
| Fermeture ou rechargement pendant une écriture (IndexedDB abandonne une transaction non terminée) | copie de secours synchrone `resaSecours.<onglet>` dans `localStorage` (au `beforeunload` / `pagehide`), reprise au démarrage suivant (§ 2.4) ; le navigateur demande aussi confirmation de quitter |
| Chargement d'un fichier alors que le projet a des modifications non sauvegardées | contenu du fichier annoncé (plans, chantiers, profils, modèles, cartouche, date), avertissement, « Annuler » ; après chargement, message seulement une fois l'enregistrement réussi |

## 5. Essais réels en `file://` (Chromium 1194 de Playwright, profils persistants)
Seul Chromium a été essayé.

| Situation | Résultat observé |
|---|---|
| Ouverture initiale, enregistrement, rechargement de la page | projet retrouvé |
| Fermeture du navigateur puis réouverture (même profil) | projet retrouvé, migration non refaite |
| Autre version du HTML, même dossier | même base, même projet |
| HTML **renommé et déplacé** dans un autre dossier | même base, même projet. Toutes les pages `file://` ont l'origine unique `file://` : n'importe quel fichier HTML local ouvert dans ce profil peut donc lire cette base |
| Nouveau profil de navigateur | aucun projet : seul le fichier `.json` transporte le travail |

Non essayés : Firefox, Safari, Edge, navigateurs mobiles et tablettes.
- **Hypothèse, non vérifiée** : Firefox isole les fichiers locaux. Un HTML déplacé ou renommé y perdrait l'accès aux projets, et IndexedDB pourrait même y être refusé en `file://`, ce qui donnerait le mode `local`.

Dans tous les cas, la procédure sûre reste : 💾 Sauvegarder le `.json`, puis 📂 Charger dans le nouvel emplacement ou le nouveau navigateur.

## 6. Limites connues
- La base n'est pas chiffrée. En `file://` dans Chromium, elle est partagée par tous les fichiers HTML locaux du profil.
- Une copie de secours trop grosse pour `localStorage` (environ 5 Mo, probable) n'est pas posée. Il reste l'avertissement du navigateur à la fermeture.
- L'ancien stockage `resa3` n'est plus mis à jour : une version précédente de CoffraPlan ouverte dans le même navigateur voit les projets d'avant la migration. Ses modifications sont détectées comme un conflit à l'ouverture suivante de cette version.
- Le suivi de la sauvegarde externe (`resaSavedH`) reste propre au navigateur ; il n'est pas lié à un fichier précis.
