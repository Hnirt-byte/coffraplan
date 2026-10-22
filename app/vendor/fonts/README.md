# Polices embarquées (phase 8)

Polices de l'interface et des feuilles imprimées : **Barlow** (400, 500, 600), **Barlow Condensed** (400, 500, 600, 700, 900) et
**JetBrains Mono** (400, 500). Ce sont les graisses que l'application demandait auparavant à Google Fonts.

- Provenance : paquets npm `@fontsource/barlow`, `@fontsource/barlow-condensed` et `@fontsource/jetbrains-mono` 5.3.0,
  dossier `files/`. Seuls les sous-ensembles `latin` et `latin-ext` sont repris, au format woff2, sans modification.
- Licence : SIL Open Font License 1.1 (fichiers `LICENSE-*` de ce dossier). Usage commercial et intégration dans un logiciel
  autorisés, sans vente des polices seules.
- Intégration : `modules/import/assembler.py` (liste `POLICES` : famille, graisse, fichier, SHA-256, `unicode-range`) les écrit en
  `@font-face` dans le bloc `<style id="fonts-src">` du livrable, en base64. Aucune requête réseau.
- Poids : 350 Ko de fichiers, environ 470 Ko dans le HTML.
- Mise à jour :
  1. `npm pack @fontsource/<famille>@<version>` ;
  2. copier les fichiers woff2 voulus ;
  3. reporter les empreintes et les `unicode-range` (fichiers CSS du paquet) dans `POLICES` ;
  4. lancer `python modules/import/assembler.py`.
