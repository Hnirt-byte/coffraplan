# CoffraPlan · Kit de marque pour application HTML

Identité validée : « Coffra » clair + « Plan » orange, pictogramme isométrique de coffrage, fond bleu nuit. Ce kit permet une intégration dans une application existante de création de plans de coffrage.

## Commencer en 3 étapes

1. Décompresser `CoffraPlan_Kit.zip` à côté de ton projet HTML.
2. Envoyer à Claude **le code de ton application et ce kit**, puis coller le contenu de `PROMPT_A_COLLER_DANS_CLAUDE.md`.
3. Tester le résultat : création et cotation des plans, sauvegarde, chargement, impression, et affichage sur mobile.

**Important :** Claude n'a pas accès à ton application uniquement parce qu'il possède le kit. Il faut aussi lui transmettre le fichier HTML actuel, le dépôt GitHub ou l'ensemble des fichiers du projet.

## Fichiers conseillés

| Besoin | Fichier |
|---|---|
| En-tête existant, sur fond sombre | `logos/coffraplan-logo-barre-navigation.svg` |
| Logo complet + sous-titre, fond sombre | `logos/coffraplan-logo-fonce.svg` |
| Logo complet + sous-titre, fond clair | `logos/coffraplan-logo-clair.svg` |
| Pictogramme sans fond | `logos/coffraplan-symbole-transparent.svg` |
| Icône carrée d'application | `icons/coffraplan-app-icon.svg` |
| Favicon navigateur | `icons/coffraplan-favicon.svg` ou `icons/favicon.ico` |
| Icônes PWA / navigateur | `icons/coffraplan-icone-192.png`, `icons/coffraplan-icone-512.png`, `icons/apple-touch-icon.png` |
| Feuille de style optionnelle | `css/coffraplan-brand.css` |
| Aperçu d'en-tête en HTML | `exemples/exemple-integration-entete.html` |
| Instruction pour Claude.ai ou Claude Code | `PROMPT_A_COLLER_DANS_CLAUDE.md` |

## Palette

- Bleu nuit interface : `#192136`
- Bleu profond : `#111B2C`
- Fond panneau : `#202B45`
- Orange principal : `#FF8517`
- Orange clair : `#FFAD40`
- Blanc de titre : `#F9FBFF`
- Gris acier / texte secondaire : `#8C9BAE`

## Usage du SVG dans HTML

```html
<link rel="icon" type="image/svg+xml" href="assets/coffraplan/icons/coffraplan-favicon.svg">
<link rel="icon" type="image/x-icon" href="assets/coffraplan/icons/favicon.ico">
<img src="assets/coffraplan/logos/coffraplan-logo-barre-navigation.svg" alt="CoffraPlan" height="35">
```

Adapte les chemins au dossier de ton projet. Pour un unique HTML portable (sans dossier d'assets), demande à Claude d'intégrer les SVG **inline** et le favicon en data URI.

## Précision sur la fidélité visuelle

Les fichiers SVG sont des **illustrations vectorielles recréées pour l'intégration**, fidèles à la direction graphique retenue, mais ne sont **pas une vectorisation pixel-par-pixel** du visuel original produit précédemment. Celui-ci se trouve dans `references/`. Pour une reproduction strictement identique à cette image, il faudrait redessiner/calquer précisément chaque élément. Les logos de production sont indépendants de cette image.

## Version et noms

Le `v2.1` présent dans la démo est un exemple issu de la capture initiale : le numéro actuel de ton app fait foi. L'ancien nom interne ou d'éventuelles clés `localStorage` ne doivent pas être renommés automatiquement car cela pourrait casser la compatibilité avec les projets sauvegardés.

## Licence / usages

Ces illustrations ont été créées pour ton application. Elles n'incluent pas de polices de caractères redistribuées. Les noms de domaine et la disponibilité commerciale ou juridique de « CoffraPlan » n'ont pas été vérifiés.
