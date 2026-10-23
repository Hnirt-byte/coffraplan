# Recette PDF — phase 12

La recette porte sur cinq documents autorisés, conservés hors du dépôt. Aucun
PDF, rendu, nom de client, repère ou cote réelle n'est publié ici. La référence
vient d'une lecture visuelle des rendus et d'une extraction indépendante de la
couche texte ; elle ne recopie pas les sorties de CoffraPlan. Les rapports par
document et preuves détaillées restent dans le répertoire privé local.

## Périmètre et méthode

- HTML autonome assemblé, Chromium et Playwright, accès réseau bloqué.
- Trois documents vectoriels à texte extractible ; deux documents vectoriels
  dont les tableaux en tracés nécessitent l'OCR local. Aucun scan réel disponible.
- Import de chaque original, nomenclature, dessin, repères, cotes et origines,
  incertitudes, préparation et tentatives de confirmation sans données suffisantes.
- Sur un document : parcours individuel puis lot, débits, contrôles, modèle 3D et
  contenu du dossier sélectionné. Les valeurs de support relues manuellement et
  les choix de joues sont consignés dans les preuves privées ; la fabrication
  physique et ces choix de chantier restent à confirmer.
- Sur un autre : correction manuelle des repères OCR dans la grille, puis refus
  d'une création standard incompatible avec le détail géométrique relu.
- Les textes OCR issus du premier passage du même fichier ont été réutilisés
  pour ces reprises de parcours ; ils ne proviennent pas d'un autre document.

## Bilan anonymisé des tableaux

| Catégorie | Documents réels | Lignes de référence / retrouvées | Lignes avec cotes numériques brutes conformes | Dont unité écrite justifiant les mm |
|---|---:|---:|---:|---:|
| Vectoriels à texte extractible | 3 | 83 / 83 | 83 | 76 |
| Vectoriels en tracés, OCR requis | 2 | 33 / 33 | 17 | 17 |
| Scans réels | 0 | non évalué | non évalué | non évalué |

Aucune ligne de tableau ajoutée ou omise constatée. Six cellules de repère OCR
ont nécessité une correction humaine ; les valeurs brutes et les corrections
restent séparées. Les autres lignes sans ouverture cotée exploitable (DN nominal
ou sans objet) n'ont pas été converties en dimensions de fabrication. Aucune
création initiale n'était complète sans intervention et confirmation.

Ces comptes concernent uniquement la vérité établie sur les tableaux, pas le
nombre de réservations physiques. Les omissions et faux positifs géométriques
ne sont pas quantifiés globalement. Les temps de traitement et interventions
par document figurent uniquement dans le rapport privé ; les traitements ont
partagé le CPU, et le temps humain n'a pas été chronométré.

## Défauts reproduits et corrections

La validation de la grille conservait les valeurs des cellules mais perdait les
intitulés originaux au profit de titres normalisés. L'information de rôle,
d'unité ou d'ordre des dimensions n'était plus consultable dans les preuves.
Les en-têtes sont maintenant copiés et transmis jusqu'à l'origine de l'ouvrage
confirmé. Ce correctif ne change pas les dimensions calculées et n'interprète
pas une en-tête douteuse comme une orientation ou une unité certaine.

Un deuxième défaut concernait l'identité : le même contour proposé pour des
repères distincts pouvait être interprété comme preuve d'un ouvrage commun.
Les liens ambigus sont maintenant écartés des identités et des preuves de
support, sans réécrire les cotes de nomenclature. Le contour demeure visible
mais sa création seule est bloquée jusqu'à un choix explicite de rattachement.
Une sélection unique prime ; des choix explicites concurrents sont bloquants.
Le rapprochement existant reste un indice, pas une preuve d'identité physique.

Le contrôle du dossier créé a révélé une troisième erreur : la ligne
« Faces cintrées » des hypothèses utilisait un ancien nom de champ et pouvait
afficher un diamètre nul malgré une géométrie correcte. Elle lit maintenant le
même diamètre que le moteur. Les débits et la géométrie restent inchangés ; le
banc vérifie aussi la valeur réellement présente dans les feuilles générées.

Le banc fictif `t_recette_pdf` contrôle la copie de provenance, la validation
réelle de la grille, l'affichage sans exécution HTML, les données manquantes,
l'export/reprise, la création sur saisies et confirmation explicites, ainsi que
les identités distinctes, les rattachements ambigus ou concurrents et les vrais
doublons. Les
algorithmes de lecture, rapprochement, imbrication et fabrication sont conservés.

## Portée de la conclusion

Cette recette évalue un outil de préparation assistée, avec relecture humaine ;
elle ne qualifie pas une reconnaissance automatique exhaustive. La vérité de
référence est établie sur les lignes des tableaux. Aucun taux de réussite global
sur les contours ou les occurrences physiques n'est calculé sans inventaire
indépendant exhaustif du dessin. Une proposition géométrique n'est pas une
réservation confirmée, et une quantité d'occurrences n'est pas une quantité à
fabriquer automatiquement.

Les incertitudes de support, d'orientation, de traversée et de détail doivent
rester visibles et bloquantes lorsqu'elles empêchent une proposition complète.
Les erreurs de lecture OCR nécessitent une correction humaine dans la grille ;
aucune règle propre à un document ou correction silencieuse de repère n'est
ajoutée. Une analyse partielle des traits sur une page dense reste signalée.

Une éventuelle v3.2 devra être présentée comme une préparation assistée avec
confirmation explicite, après relecture indépendante de la PR. Cette phase ne
permet pas de revendiquer une importation sans intervention, une prise en charge
de tous les détails, ni une qualification sur scans réels. Version v3.1 conservée.
Impression physique, tenue mécanique, tablette réelle et navigateurs hors
Chromium non vérifiés. Aucune autorisation de publication ou fusion implicite.
