# Instructions pour Codex

Lire intégralement `CLAUDE.md` avant toute intervention : il fait référence pour
l’architecture, les conventions, les interdictions métier et les tests. Pour
l’import de plans, consulter aussi `modules/import/README.md` et les sections
pertinentes de `CHANGELOG.md` et `docs/audit-modernisation.md`.

- Répondre en français et distinguer faits vérifiés, hypothèses et limites.
- Travailler sur une branche dédiée ; aucun commit direct sur `main`, aucune
  fusion automatique. Pas de tag, Release ou changement de version sans accord.
- Ne jamais éditer `app/CoffraPlan.html` : le reconstruire avec l’assembleur.
- Préserver les projets existants et la génération des coffrages ; ne jamais
  inventer de cote, d’épaisseur ou de rayon.
- Garder les plans réels et leurs rendus hors du dépôt, des commits, des PR et
  des artefacts publics ; ne pas publier d’informations confidentielles.
- Rapporter les commandes, résultats des tests et points non vérifiés. Attendre
  la validation avant une fusion ou le démarrage d’une nouvelle phase.

## Sorties du terminal

RTK est installé dans "$HOME/.local/bin/rtk".
Utiliser ce chemin explicite pour les commandes compatibles générant
des sorties volumineuses, notamment Git et les tests.

Exemples :
- "$HOME/.local/bin/rtk" git status
- "$HOME/.local/bin/rtk" git diff
- "$HOME/.local/bin/rtk" gain

Si une commande échoue ou si le résultat filtré ne suffit pas au diagnostic,
consulter la sortie originale. Conserver toutes les validations requises.
