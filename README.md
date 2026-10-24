# CoffraPlan

Plans de coffrage bois pour réservations et petits ouvrages : débit CP et bois, imbrication, gabarits 1:1, 3D, DXF,
dossier PDF, mode chantier. **Un seul fichier HTML**, hors connexion, sans installation.

- Application : le fichier unique `CoffraPlan.html`, à ouvrir dans Chrome ou Edge. Depuis la phase 8, il n'est plus enregistré dans
  le dépôt : il est **construit** à partir des sources (voir « Construire CoffraPlan » ci-dessous).
- Dernière version construite par GitHub : onglet **Actions** → workflow **Tests** → un run vert (branche `main` ou une PR) → en bas,
  section **Artifacts** → `CoffraPlan-<commit>` (zip contenant `CoffraPlan.html` et `CONSTRUCTION.txt` : commit exact, date, taille,
  empreinte SHA-256). Conservé 90 jours. Ce n'est pas une Release.
- Versions publiées, avec le HTML et le mode d'emploi PDF : onglet **Releases** du dépôt.
- Historique : [CHANGELOG.md](CHANGELOG.md) · Suite : [docs/feuille-de-route.md](docs/feuille-de-route.md)
- Règles du projet et carte du code (lues par Claude Code à chaque session) : [CLAUDE.md](CLAUDE.md)

© Kévin TRINH. Tous droits réservés. Dépôt privé.
Bibliothèques et ressources tierces intégrées (licences dans les dossiers `vendor`) : [three.js](https://threejs.org) r170 (MIT), PDF.js,
Tesseract.js, ONNX Runtime Web et PP-OCRv6, polices Barlow, Barlow Condensed et JetBrains Mono (OFL-1.1). Aucune requête réseau.

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
4. Construire CoffraPlan (à refaire après chaque modification des sources ; environ 2 s) :
   ```
   python modules/import/assembler.py           # → app/CoffraPlan.html (à ouvrir dans Chrome ou Edge)
   python modules/import/assembler.py --check   # vérifie que app/CoffraPlan.html correspond aux sources
   ```
5. Ensuite :
   ```
   python tests/run.py -j 4          # tests rapides (environ 2 min ; construit d'abord app/CoffraPlan.html)
   python docs/manuel/build.py       # mode d'emploi PDF → docs/manuel/
   ```
   Le test d'export XLSX ouvre le classeur avec LibreOffice (`soffice`). Sans LibreOffice, ce seul contrôle échoue.

### Publier une version
Préparer le numéro, les notes et le manuel dans une PR dédiée (voir CLAUDE.md), puis exécuter les validations.
Après fusion, CI post-fusion verte et **autorisation explicite de publication**, le tag correspondant à la version affichée
(`vX.Y`) déclenche GitHub Actions : tests complets, génération du manuel et Release avec `CoffraPlan_vX.Y.html` et
`CoffraPlan_vX.Y_Mode_emploi.pdf`. La préparation v3.2 ne crée ni tag ni Release.

## Dossiers
| Dossier | Contenu |
|---|---|
| `app/` | sources de l'application : `CoffraPlan.source.html` (HTML, CSS, script principal) et `vendor/three` ; `CoffraPlan.html` y est construit (non versionné) |
| `tests/` | bancs Playwright (`run.py`), références figées (`ref/`, `ref_v19.json`) |
| `docs/manuel/` | mode d'emploi : `manuel.html`, `captures.py` (captures d'écran), `build.py` (PDF) |
| `docs/historique/` | notes de passation de chaque version |
| `kit/` | identité graphique (logos, icônes, charte) |
