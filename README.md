# CoffraPlan

Plans de coffrage bois pour réservations et petits ouvrages : débit CP et bois, imbrication, gabarits 1:1, 3D, DXF,
dossier PDF, mode chantier. **Un seul fichier HTML**, hors connexion, sans installation.

- Application : [`app/CoffraPlan.html`](app/CoffraPlan.html). Il suffit de l'ouvrir dans Chrome ou Edge.
- Versions publiées, avec le HTML et le mode d'emploi PDF : onglet **Releases** du dépôt.
- Historique : [CHANGELOG.md](CHANGELOG.md) · Suite : [docs/feuille-de-route.md](docs/feuille-de-route.md)
- Règles du projet et carte du code (lues par Claude Code à chaque session) : [CLAUDE.md](CLAUDE.md)

© Kévin TRINH. Tous droits réservés. Dépôt privé.

## Travailler sur le projet

### Sans rien installer : Claude Code sur le web
Sur claude.ai/code, ouvrir une session sur le dépôt `Hnirt-byte/coffraplan`. Décrire la demande ; Claude modifie le code,
lance les tests et pousse une branche ou un commit.

### Sur ton PC (Windows) : VS Code + Claude Code
1. Installer [Git for Windows](https://git-scm.com/download/win), [Python 3.12](https://www.python.org/downloads/)
   (cocher « Add python.exe to PATH ») et [VS Code](https://code.visualstudio.com/).
2. Dans VS Code : *Clone Git Repository* → `https://github.com/Hnirt-byte/coffraplan.git`. VS Code propose les extensions
   recommandées (Claude Code, Python) : les installer, puis se connecter avec son compte Claude.
3. Dans le terminal de VS Code (menu *Terminal → Nouveau terminal*), une seule fois :
   ```
   pip install -r tests/requirements.txt
   python -m playwright install chromium
   ```
4. Ensuite :
   ```
   python tests/run.py -j 4          # tests rapides (environ 2 min)
   python docs/manuel/build.py       # mode d'emploi PDF → docs/manuel/
   ```
   Le test d'export XLSX ouvre le classeur avec LibreOffice (`soffice`). Sans LibreOffice, ce seul contrôle échoue.

### Publier une version
Mettre à jour le numéro (voir CLAUDE.md), commit, puis `git tag v2.6 && git push --tags`. GitHub Actions lance les
tests, génère le mode d'emploi et crée la Release (HTML + PDF).

## Dossiers
| Dossier | Contenu |
|---|---|
| `app/` | l'application (fichier unique, seule source) |
| `tests/` | bancs Playwright (`run.py`), références figées (`ref/`, `ref_v19.json`) |
| `docs/manuel/` | mode d'emploi : `manuel.html`, `captures.py` (captures d'écran), `build.py` (PDF) |
| `docs/historique/` | notes de passation de chaque version |
| `kit/` | identité graphique (logos, icônes, charte) |
