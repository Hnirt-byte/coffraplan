# Prompt prêt à coller dans Claude.ai / Claude Code

Je te fournis **mon application HTML existante** de création de plans de coffrage et le dossier de marque `CoffraPlan_Kit` (ou son fichier ZIP).

## Mission

Intégrer dans MON application existante la nouvelle identité visuelle **CoffraPlan**, en conservant intégralement le fonctionnement actuel. L'identité validée est un pictogramme isométrique de coffrage gris et orange, un mot-symbole « Coffra » blanc suivi de « Plan » orange, sur une interface bleu nuit. Tu trouveras les véritables fichiers SVG/PNG/ICO fournis dans le kit. Ne régénère pas de logo et ne le remplace pas par un emoji ou une approximation CSS.

## À modifier

1. Remplacer dans l'en-tête l'ancien titre visuel « Plans Réservation » et son pictogramme par `logos/coffraplan-logo-barre-navigation.svg` (prioritaire). Adapter légèrement sa taille pour qu'il soit bien aligné à gauche avec les commandes existantes. Si l'application utilise un thème clair, utiliser à la place `logos/coffraplan-logo-clair.svg` à l'endroit pertinent. Le logo ne doit jamais être déformé, rogné ni trop petit.
2. Conserver le numéro de version réel existant (par ex. « v2.1 »), sans le remplacer arbitrairement par v1.0. L'afficher discrètement à droite du logo s'il était présent auparavant.
3. Modifier le `<title>` du document en « CoffraPlan » (avec version seulement si elle était déjà exploitée).
4. Ajouter le favicon depuis `icons/coffraplan-favicon.svg` et, si possible, `icons/favicon.ico`. Si PWA installable, définir aussi `icons/coffraplan-icone-192.png`, `icons/coffraplan-icone-512.png` et `icons/apple-touch-icon.png` selon l'architecture déjà en place. Ne crée pas de PWA si l'application n'en a pas besoin.
5. Préserver la palette actuelle (bleu nuit, anthracite, orange) et réutiliser seulement au besoin `css/coffraplan-brand.css`. Réutiliser les styles existants plutôt que réécrire toute l'interface.
6. Garder un en-tête responsive : pas de chevauchement du logo avec Imprimer, Sauvegarder, Charger, Annuler ou Rétablir. Pour les écrans étroits, réduire la taille du logo ou prévoir une disposition adaptée sans sacrifier les commandes.
7. Les éléments de marque de l'en-tête doivent rester hors de la zone imprimée : ils ne doivent pas altérer les planches de débit et les plans de pose.

## Contraintes non négociables

- **C'est une modification VISUELLE ciblée, pas une refonte.** Ne change aucune règle métier ni aucun calcul.
- Ne touche pas à la génération des panneaux, découpes, cotations, calepinages, repères D1/D2..., numérotation, légendes, formats d'impression ou mise en page des feuilles.
- Ne change pas la logique de sauvegarde/chargement, l'état de l'application, les projets existants, les exports ou la bibliothèque des formes.
- Conserve tous les boutons, raccourcis et fonctionnalités présents dans le code source.
- Ne supprime aucun code métier. N'introduis pas de CDN ou dépendance externe uniquement pour l'identité visuelle.
- Si l'application est un fichier HTML **autonome** que j'ouvre localement, propose une solution autonome : intégration des SVG en inline et favicon data URI lorsque des chemins vers `assets/` ne sont pas viables. Évite alors toute ressource distante ou dépendance réseau.
- Si elle est structurée en plusieurs fichiers, utilise des chemins relatifs et copie les assets dans un dossier `assets/coffraplan/` cohérent. Vérifie les chemins relatifs depuis le HTML réel.
- N'inclus pas les images de démonstration `references/` dans le produit final : ce sont des références artistiques, pas des assets de production.
- Si un changement implique de renommer des identifiants, clés de stockage, variables ou fichiers de données pour remplacer « Plans Réservation », **ne le fais pas** sans expliquer le risque de migration et me demander mon accord. Seuls les libellés visibles et métadonnées de présentation doivent changer.

## Méthode de travail

1. Examine le HTML, CSS, JavaScript et les assets existants. Repère les zones strictement nécessaires à l'intégration.
2. Présente en quelques lignes les modifications et fichiers concernés, puis applique-les directement si tu as accès aux fichiers.
3. Fais une intégration minimale et justifie uniquement les changements non évidents.
4. Vérifie visuellement que l'en-tête reste fidèle à l'interface d'origine, que le logo est net et que tous les contrôles restent visibles.
5. Vérifie les fonctionnalités principales avant/après (création de plan, mise à jour des cotes, sauvegarde, chargement, impression) ; si tu ne peux pas exécuter un test, indique-le explicitement au lieu de le déclarer réussi.
6. Fournis le **fichier HTML final complet**, ou le **patch exact** pour les fichiers d'un projet. Ne me donne pas uniquement des extraits impossibles à intégrer.

## Livrable

Une application portant le nom **CoffraPlan**, avec son pictogramme et son identité orange/bleu nuit, **strictement aussi fonctionnelle qu'avant**, intégrant les assets du kit et conservant la version actuelle.
