# Historique des versions

Détail complet de chaque version (demandes, écarts voulus, tests, non validé) : `docs/historique/HANDOFF_<version>.md`.
Chaque version est un tag git (`git diff v2.4 v2.5 -- app/` pour voir les changements).

## Phase 9C — proposition de coffrage et création confirmée (version v3.1 conservée)

**Demande** : passer d'une réservation PDF à une proposition contrôlée, puis créer
un seul ouvrage après relecture et confirmation explicite.

**Fait** : `creation.js` prépare les données et appelle les moteurs existants ;
`creation-ui.js` ajoute « Proposer un coffrage » aux lignes PDF et aux contours
proposés. Provenance par valeur, inconnues visibles, corrections conservées ; les
mesures de l'analyse ne deviennent utilisables qu'après confirmation des échelles.
Rayon et épaisseur sans valeur fiable restent vides. Flèches par `GEO.sag`, cordes
par `voileGeo` : joues parallèles = corde commune, radiales = corde extérieure,
aucun développé assimilé à une corde. Tolérance géométrique facultative dans le
profil chantier, modifiable par ouvrage et pour une création ; sans tolérance,
aucune nécessité de cintrage décidée. Choix explicite de solution et des joues,
récapitulatif, case de confirmation finale ; aucun projet modifié auparavant.

Mannequin droit / simple : moteur `para` existant à biais et pente nuls, ouvert sur
les deux parements. Mannequin cintré : moteur `voile`, construction mannequin.
Fourreau : moteur `circ`, longueur de traversée saisie, jamais déduite de
l'épaisseur de la paroi courbe. La solution simple sur voile circulaire exige
joues parallèles et deux flèches dans la tolérance confirmée. Le choix cintré peut
rester explicite sans tolérance. Identité du PDF (SHA-256) et de la réservation
conservée dans `origineImport.creationCles` : validations répétées, réimport et
chemins d'import PDF historiques ne créent pas de doublon de cette identité.

**Compatibilité / écarts voulus** : aucun algorithme de fabrication modifié,
aucune migration de projet ; métadonnées facultatives et enveloppe v10 inchangée.
Les ouvrages antérieurs gardent leur débit, leurs feuilles et leurs exports. Pas
de changement de version, de configuration Cloud, de tag ou de Release.

**Tests** : nouveau banc fictif `t_creation` (données fiables / manquantes,
confirmation, joues / cordes / flèches / tolérance, création unique, stockage,
contrôles / débit / feuilles / visualisation existants). Résultats des campagnes
et avant/après exacts consignés dans la PR ; exemple utilisateur dans le manuel.

**Limites** : traversées normales sans biais ni pente ; développés et cordes
intérieures radiales à reporter manuellement en bonne corde. Un chanfrein, une
feuillure ou un détail particulier du plan ne sont pas reproduits automatiquement
par cette proposition : compléter l'étude de fabrication. Reconnaissance, cotes
OCR et réglages de fabrication restent à relire ; aucune validation automatique.
Pas d'impression physique, d'AutoCAD, de Firefox ou Safari validé dans cette phase.
Plans réels, rendus et diagnostic détaillé conservés hors du dépôt.

## Phase 9B — contours contextuels dans les voiles (non publiée, version v3.1 conservée)

**Demande** : retrouver les réservations raccordées aux parements, sans exiger un
rectangle fermé indépendant ni supprimer les protections contre les faux positifs.

**Fait** : `contours.js`, recherche locale à partir d'un repère de nomenclature fiable,
de diagonales, de traverses (fragments admis) et de parements concordants. Les limites
inférées sont marquées « contour reconstruit », affichées en tirets et conservées avec
leurs preuves dans les exports/provenances. Elles ne donnent aucune cote de fabrication
et ne confirment aucune cote du tableau par mesure. Cercle fermé segmenté relu dans son
sous-chemin avec contrôle des milieux ; OCR des petits repères sur les planches réduites,
sans changer l'échelle physique ; rappels séparés des lettres ; ponctuation périphérique
du repère ignorée dans la clé seulement, brut conservé. Aucun ouvrage créé automatiquement,
aucun calcul de fabrication ou de débit modifié. `AGENTS.md` renvoie aux règles de `CLAUDE.md`.

**Limites** : diagonales et traverses suffisantes requises ; ambiguïté, OCR incertain ou
échelle absente restent signalés, valeurs non établies = `null`. L'API support DXF existe,
mais son analyse et la reconstruction ne sont pas raccordées à la fenêtre DXF (PDF uniquement).
Plans et rapports confidentiels exclus du dépôt. Voir `modules/import/README.md`, § Phase 9B.

**Tests ciblés** : `t_contours` (30 contrôles : voiles droits/circulaires, fragments,
facteurs graphiques, quadrillages, zones, repères voisins, provenance, aucune cote ni
création automatique) et `t_rapprochement` (34 contrôles existants) passent. Les campagnes
complètes, l'avant/après et la CI sont consignés dans la PR de livraison.

**Non validé** : reconnaissance exhaustive des plans réels, toutes les vues tournées,
ouvertures sans diagonales/traverses suffisantes et mesures sans calibrage confirmé.
Firefox, Safari, Excel/AutoCAD et impression physique non essayés dans cette phase.

## Phase 9A — géométrie du support d'une réservation (non publiée, sans numéro de version)
**Demande (Kévin, 22/10/2026)** : faire comprendre à CoffraPlan la géométrie du support dans lequel se situe une réservation repérée
sur un plan PDF ou DXF (voile droit, voile circulaire), en séparant forme de l'ouverture, nature du support et solution de coffrage ;
moteur indépendant, testable, déterministe ; aucune création d'ouvrage, aucun changement des calculs de débit, panneaux ou gabarits,
forme voile jamais activée à l'import, aucun LLM ni API ; aucun seuil arbitraire de 500 mm ; `#appVer` reste v3.1 ; aucun tag ni Release.

**Fait** (détail : `modules/import/README.md`, § Phase 9A)
- `modules/import/support.js` (`CPI.support`) : analyse locale autour du contour ou du repère ; faces droites (lignes parallèles,
  directions des côtés du contour) ou circulaires (arcs concentriques : ARC / bulge DXF, Bézier PDF, chaînes de segments) ; une
  réservation qui ne va pas d'une face à l'autre n'est jamais rattachée à un support (bande signalée seulement) ; deux supports d'égale
  vraisemblance → `inconnu` ; quadrillages, tableaux, cartouches, vues en élévation et de ferraillage, contours écartés : non analysés.
  Faces d'un seul côté de la réservation, ou contour repris par proximité du repère : support seulement « possible » (preuve), jamais
  dans le résultat.
- Valeurs en mm avec leur provenance (`cote_explicite`, `mesure`, `calcul`, `saisie`) ; `null` si absente. Échelle de la page et de la
  vue comparées ; échelle incohérente (deux échelles, ou largeur mesurée sans rapport avec les cotes du tableau) : mesures non utilisées.
  Une cote voisine n'est retenue que confirmée par la mesure. Orientation de l'ouverture (largeur suivant la paroi ≠ hauteur) par les
  colonnes Largeur / Hauteur ou par la mesure le long de la paroi ; sinon `null`.
- Flèches aux deux parements par `GEO.sag` du moteur (reçu en paramètre, aucun calcul dupliqué) ; pistes motivées (fourreau pour une
  ouverture circulaire, coffrage rectangulaire en paroi droite, comparaison flèche / tolérance saisie en paroi circulaire) ;
  `solution_proposee` toujours `a_determiner`, `validation_utilisateur_requise` toujours vrai ; `correspondance_voile` (L, l, h, Ø cuve,
  `dRef`) proposée pour le voile cintré, jamais appliquée.
- Lecteurs, sans effet sur l'existant : `CPI.pdf.chemins` renvoie aussi les pièces de Bézier (`courbes`) et relit une page par zones
  (`{zones}`) ; `dxf.js` relève `arcs` et `traitsArcs` à part (entités, traits, détecteur et tableaux inchangés).
- Fenêtre d'import : `dxsAnalyser` en fin de « 🔎 Analyser le dessin » (lignes en concordance forte ou partielle ; contour écarté le plus
  proche du repère repris, support seulement « possible » ; pages très chargées relues localement) → `DXI.SP` et clé `supports` de
  l'export JSON. Aucune interface nouvelle.

**Correctifs de relecture (PR #19)** : `consolider` (plusieurs vues) ne garde plus une `correspondance_voile`, des flèches ou une confiance
forte héritées d'une vue : nature en désaccord → `inconnu` sans valeur de support ; valeur en conflit → `null` et valeurs dépendantes
(rayon extérieur, flèches, Ø cuve) recalculées par `GEO.sag` ou retirées ; confiance « faible » ; valeurs et preuves de chaque vue
conservées (`observations[]`). Échec de l'analyse des supports (`DXI.SPerr`) affiché dans le bilan d'import ; export JSON :
`supportsAnalyse` (`reussie` / `echec` + erreur / `non_lancee`). Tests ajoutés dans `t_support` (voile droit contre voile circulaire,
deux vues circulaires contradictoires, vues concordantes, échec simulé).

**Plans réels (hors dépôt, Chromium), mêmes scénarios qu'en phase 8** : tableaux, repères, cotes, vues, occurrences et rapprochements
**identiques** pour A, B (zone et automatique), C, D ; seuls les temps changent (analyse du support et relecture locale : D 67 → 71 s,
A 161 → 174 s, B 125 → 147 s, C 224 → 242 s ; passages séquentiels, autres processus actifs). Supports analysés : 13 réservations
associées (D 4, A 7, B 1, C 1) ; **aucun support affirmé**, tous « inconnu » : vues de détail ou de ferraillage, contours repris
(support possible), réservations entre deux murs sans les toucher (bande signalée), faces d'un seul côté, deux supports possibles.
Contrôle visuel des découpes : avant les règles de durcissement, 4 faux voiles (armatures sur A, gaine sur D, lignes de cote sur C,
bande de pièce sur D), tous retirés. Plan B : la cuve réelle est bien lue (face extérieure en Bézier, intérieure en segments), mais le
contour de la réservation posée dans sa paroi n'est pas repéré par la phase 4 : support non évalué sur un vrai voile circulaire.

**Écarts voulus** : aucun test existant modifié. Export JSON de l'analyse : nouvelle clé `supports` (les autres clés inchangées).
Nouvelle suite `t_support` (plans fictifs `tests/support_fictifs.py`, constructions `tests/support_cas.js`), ajoutée aux suites rapides.

**Tests** : `python tests/run.py complet -j 4` : 37 / 37 suites vertes (22/10/2026, Chromium), dont `t_support` (71 après les correctifs de relecture) ; `t_avap` : 1 090 / 1 090
contre main `6d5b4e5` (moteur, feuilles, DXF et CSV identiques). Livrable construit (après correctifs) : 37 043 190 octets SHA-256
`40e1b0e3bbfab728e9c6fd97bc52e04d79cc02a8983b5e56b7c8b35fbd4f993f`.

**Non validé** : aucun vrai plan ne contient de réservation repérée dans un voile circulaire (plan B : contour non repéré en amont) ;
seuils géométriques internes (2° de parallélisme, 1 % de centre, 10 % d'accord cote / mesure, rival à 60 %) éprouvés sur cas fictifs
et quatre plans seulement ; DXF réels avec ARC ou bulge non essayés (seulement DXF écrits par ezdxf) ; Firefox, Safari non essayés.

## Phase 8 — construction du livrable par la CI ; tableaux juxtaposés et titres de vue (plan D) (non publiée, sans numéro de version)
**Demande (Kévin, 22/10/2026)** : faire produire le HTML autonome par GitHub Actions sans le versionner ; corriger les deux défauts
du plan D (tableaux voisins mêlés, titre « Sous Toiture 1 : 25 » non reconnu) ; aucun changement des calculs, de la 3D, des exports,
du format JSON ; pas de Tauri ni de nouveau modèle ; `#appVer` reste v3.1 ; aucun tag ni Release.

**Lot A, construction** (détail : `modules/import/README.md` § 3, CLAUDE.md)
- `app/CoffraPlan.source.html` (HTML, CSS, script principal) + marqueurs `<!--@bloc ID-->` ; `modules/import/assembler.py` construit
  `app/CoffraPlan.html` (déterministe, écriture atomique) ; `--check` le vérifie. three.js r170 extrait dans `app/vendor/three`
  (identique octet pour octet à `three@0.170.0/build/three.module.min.js`, empreinte SHA-256 vérifiée comme les autres dépendances).
- Reproductibilité : sur les sources de main `b94a01e`, livrable **identique octet pour octet** au HTML versionné (36 515 091 octets).
- Correctif de relecture : le livrable demandait les polices à Google Fonts (seule requête réseau, tolérée jusqu'ici par les tests) ;
  Barlow, Barlow Condensed et JetBrains Mono (mêmes graisses, OFL-1.1, `@fontsource` 5.3.0, sous-ensembles latin / latin-ext)
  sont maintenant embarquées (`app/vendor/fonts`, bloc `fonts-src`, empreintes vérifiées) ; plus aucune requête réseau, mise en
  page conservée sans connexion. `t_build` surveille toutes les requêtes dès la 1re navigation, sans domaine exclu.
- `app/CoffraPlan.html` retiré de l'index (historique non réécrit) et ignoré ; pas de Git LFS ; poids OCR toujours versionnés.
- CI (`tests.yml`) : construction + `--check`, syntaxe, tests (rapides / complets / hebdomadaire inchangés), puis artefact
  `CoffraPlan-<commit>` (HTML + `CONSTRUCTION.txt` : commit construit, tête de PR, run, date, taille, SHA-256) seulement si tout est
  vert, conservé 90 jours ; aucune Release. `release.yml` (tag) construit le HTML avant de le publier.
- Tests : `run.py` construit une fois ; une suite lancée seule construit ; `t_avap` construit la version de référence si son HTML
  n'est pas versionné ; nouvelle suite `t_build` (source, reproductibilité, `--check`, dépendance altérée refusée, git, livrable en
  file:// sans réseau : IndexedDB, PDF.js, PP-OCRv6, Tesseract, three.js, exports DXF / IFC / glTF / CSV).

**Lot B, plan D** (détail : `modules/import/README.md`, § Phase 8)
- Cause réelle du défaut 1 (mesurée) : les traits du plan D (≈ 400 000) dépassent le plafond `SEG_MAX` (60 000) : aucun trait du
  tableau n'est relevé, lecture par la position des textes ; le tableau de trappes voisin, construit en premier, s'étendait le long de
  sa 1re ligne de valeurs (écart ≤ 60 h) jusqu'à la nomenclature et lui prenait R15-V08. Correction générique : couloirs des en-têtes
  (l'en-tête d'un autre tableau, à une autre hauteur, borne le tableau de son côté).
- Défaut 2 : titre sans mot-clé de vue reconnu par son échelle écrite juste dessous ; vue en plan si le texte nomme un niveau vu de
  dessus / dessous et si le dessin rattaché est conséquent ; sinon « autre » (jamais compté) ; confiance au plus moyenne ; échelle
  rattachée à cette vue seulement.
- Constaté sur le plan fictif puis sur le plan A : un titre de cartouche (« VUE EN PLAN … », « Plan guide », « voir plan … ») pouvait
  devenir une vue (jusqu'à une confiance forte sur le fictif). Titre placé dans un petit cadre d'angle de feuille avec au moins 3 autres
  textes : jamais une vue.

**Mesures sur les plans réels (hors dépôt ; Chromium ; vérités : couche texte pour D, relevés de la phase 6)**
- **Plan D, lecture automatique sans zone** : nomenclature 14 → **46 / 46 lignes** ; repères, cotes en mm, niveaux, finitions,
  désignations 46 / 46 ; tableau de trappes distinct (3 lignes, écarté) ; aucune ligne de note, aucun doublon, aucune ligne inventée.
- **Plan D, vues** : « Sous Toiture » + « 1 : 25 » : vue en plan (confiance moyenne), échelle 1:25 sur cette vue, région = dessin
  principal ; le cartouche « VUE EN PLAN - SOUS TOITURE » n'est pas une vue. Occurrences comptées 0 → **31, toutes justes** (repères
  isolés du dessin relevés indépendamment par pdftotext : 33 ; R01 et R02, présents deux fois sans quantité au tableau, restent non
  décidés comme le veut la règle de la phase 5.1). Le nombre d'occurrences n'est jamais déduit du nombre de lignes.
- **Plans A, B (zone et automatique), C** : tableaux, repères, cotes, niveaux, occurrences **identiques** à la phase 6 ; plan A,
  page 1 : 2 fausses vues tirées du cartouche (« Plan », « plan ferraillage 50 ») retirées (vues incertaines 3 → 2 ; aucune
  occurrence n'y était comptée).
- Temps (passages séquentiels, mêmes scénarios qu'en phase 6) : A 170 → 161 s, B 120 → 125 s, C 238 → 224 s ; D (lecture automatique
  sans zone + analyse du dessin) : 67 s.

**Écarts voulus** : `t_avap` adapté (construit la version de référence depuis git quand son HTML n'est pas versionné : sans cela, il ne
pourrait plus comparer). Aucun autre test existant modifié. Nouvelles suites `t_build` et `t_plan_d` (plan fictif anonyme `tests/plan_d_fictif.py`,
cas négatif « Sous Toiture » dans une note ou sans échelle, cartouche).

**Tests** : `python tests/run.py complet -j 4` : 36 / 36 suites vertes (22/10/2026, Chromium), dont `t_build` (21), `t_plan_d` (17), `t_ux` (polices réelles),
`t_stockage`, `t_ppocr`, `t_3d`, `t_export` ; `t_avap` : 1 090 / 1 090 avec la référence par défaut (construite depuis HEAD) et contre le main
validé `b94a01e` (`AVAP_REF=origin/main`) : moteur, feuilles, DXF et CSV identiques. Livrable construit (polices embarquées) : 36 991 952 octets, SHA-256 `17df713ac45edb454d7ba6b98ae935ee12157d5c9f7cecf13cd20d1746a509dd`.

**Non validé, limites** : `SEG_MAX` (60 000 traits par page) reste un plafond : sur un plan très chargé, les régions de vue sont
partielles et les tableaux sont lus par leurs textes ; artefact CI : téléchargement manuel depuis l'onglet Actions (90 jours) ;
reconnaissance des titres déduits éprouvée sur un seul plan réel et des cas fictifs ; Firefox, Safari, tablette non essayés.

## Phase 7 — stockage fiable et sauvegarde des projets (non publiée, sans numéro de version)
**Demande (Kévin, 22/10/2026)** : supprimer le risque de perte silencieuse des projets lié au stockage du navigateur, sans toucher aux
fonctions métier ; IndexedDB en stockage principal ; migration non destructive ; sauvegarde et restauration vérifiées ; erreurs
explicites ; essais réels en file:// ; OCR, calculs, GAMMA, géométrie, 3D, feuilles et exports inchangés ; pas de Tauri, pas de
changement du packaging ; `#appVer` reste v3.1 ; aucun tag ni Release.

**Fait** (détail : `docs/stockage.md`)
- Stockage principal IndexedDB (base `coffraplan`, schéma 1) : projet entier (plans, profils, modèles, cartouche) en une transaction ;
  données de travail toujours en mémoire (calculs synchrones) ; écritures en file, chacune sur l'état le plus récent ; révision `rev`
  contrôlée dans la transaction (autre onglet, autre copie du HTML : écriture refusée et signalée, jamais d'écrasement silencieux).
- Migration de l'ancien stockage (`resa3`, `resaProf`, `resaLib`, `resaEnt`) : validation, copie, relecture, comparaison, marque ;
  ancien stockage jamais modifié ni supprimé ; échec → mode de secours (ancien enregistrement), erreur visible, export, « Réessayer » ;
  migration interrompue reprise ; ancien stockage différent du projet enregistré → choix explicite (exporter les deux, garder,
  reprendre, décider plus tard) ; ancien stockage illisible → signalé, exportable tel quel.
- Copie de secours synchrone à la fermeture pendant un enregistrement (`resaSecours.<onglet>`), reprise au démarrage suivant seulement si
  elle prolonge exactement le projet enregistré.
- Interface : indicateur d'enregistrement local (« ✓ Enregistré ici », « ⏳ Enregistrement… », « ⚠ Non enregistré », « ⚠ Modifié
  ailleurs », « ⚠ Stockage de secours ») distinct du rappel de sauvegarde fichier, qui est conservé ; bandeau d'actions (exporter,
  réessayer, recharger, choisir) ; chargement d'un fichier : contenu annoncé avant remplacement, projet non sauvegardé signalé,
  confirmation après enregistrement réel ; téléchargement : « fichier remis au navigateur » au lieu de « enregistrée ».
- Fichier de sauvegarde inchangé (`{app:'plans-reservation', v:10, plans, profils, modeles, ent}`).
- Relecture de la PR #17 (corrections avant fusion) :
  - A : un projet enregistré n'est jamais remplacé d'office par l'ancien stockage, même sans plan ni modèle (profils, cartouche,
    projet vidé) : choix proposé ; migration automatique seulement sans projet enregistré, création contrôlée dans la transaction
    (onglets démarrés en même temps) ;
  - B : plusieurs copies de secours différentes de même révision de départ : aucune reprise ni suppression, récupération explicite
    (export séparé, reprise sur confirmation) ; reprise automatique gardée pour une copie unique non ambiguë ;
  - forçage : autorisation à usage unique, limitée à la révision vue, retirée même après un échec d'écriture.
- Documentation : `docs/stockage.md`, mode d'emploi (§ 6), audit (décisions actées après la phase 6, section stockage), CLAUDE.md.

**Essais file:// (Chromium, profils persistants)** : rechargement, fermeture / réouverture, autre HTML du même dossier, HTML renommé et
déplacé : projets retrouvés (origine `file://` unique pour tous les fichiers locaux) ; nouveau profil : aucun projet (le fichier .json
seul transporte le travail). Firefox, Safari, Edge, tablette : non essayés.

**Écarts voulus (tests existants)** — l'ancien stockage n'est plus écrit en fonctionnement normal :
- `t_dxf_ui` (12) : l'état après « Annuler » est relu dans IndexedDB (`stoEnregistre`) au lieu de `localStorage.resa3` ;
- `t_v26` : le cartouche enregistré est relu dans IndexedDB au lieu de `localStorage.resaEnt` ;
- `t_v24` : le stockage plein est simulé sur IndexedDB (`QuotaExceededError` à l'écriture) au lieu de `localStorage` ; le message
  attendu (« refuse d'enregistrer ») est inchangé.
Nouvelle suite `t_stockage` (13 scénarios demandés + IndexedDB absent, ancien stockage illisible, fermeture pendant un enregistrement ;
+ relecture : projet enregistré vide, zéro plan avec profil et cartouche, migration initiale concurrente, deux copies de secours de même
révision, forçage après échec : 58 contrôles).

**Tests** : `python tests/run.py complet -j 4` : 34 / 34 suites vertes (22/10/2026, Chromium), dont `t_stockage` (58 contrôles), `t_ux`,
`t_ppocr`, `t_3d`, `t_export` ; `t_avap` relancé contre le main validé (`AVAP_REF=origin/main`) : 1 090 / 1 090, moteur, feuilles, DXF
et CSV identiques.

**Non validé, limites** : Firefox / Safari / Edge / tablette ; vraie saturation d'un disque (quota simulé) ; base non chiffrée et partagée
par tous les HTML locaux du profil en file:// ; copie de secours limitée par la taille de `localStorage` ; une version précédente de
CoffraPlan ouverte dans le même navigateur voit les projets d'avant la migration (ses modifications sont détectées comme conflit).

## Phase 6 — moteur de reconnaissance PP-OCRv6 local (non publiée, sans numéro de version)
**Demande (Kévin, 21/10/2026)** : moderniser le moteur de reconnaissance avec la meilleure technologie gratuite, locale et
exploitable commercialement ; aucune API payante, aucun abonnement, aucun plan envoyé à un serveur ; HTML autonome ; comparer
PaddleOCR / PP-OCR, PP-StructureV3, PaddleOCR-VL-1.6, Docling et Tesseract.js sur les plans réels avec des vérités terrain
indépendantes ; architecture à adaptateurs ; audit et feuille de route des autres domaines ; une seule PR ; aucun tag ni Release ;
`#appVer` reste v3.1 ; moteur de coffrage, 3D et exports inchangés.

**Fait** (détail : `modules/import/README.md`, § Phase 6 ; provenance et licences : `modules/import/vendor/ppocr/README.md`)
- `ppocr.js` : PP-OCRv6 small (reconnaissance, Apache-2.0) sur ONNX Runtime Web 1.30.0 (MIT), WebAssembly, embarqué (blocs `ppocr-*`,
  empreintes vérifiées par `assembler.py`) ; contrat `lire(images) → {texte, conf, chars, orientation}` ; aucune requête réseau.
- `ocr.js` : choix du moteur (`choisirMoteur`, `moteur`) ; PP-OCRv6 par défaut pour les tableaux à grille et les repères dessinés,
  Tesseract au choix et pour les zones sans grille ; `bandes` (lignes d'une cellule, traits d'en-tête fusionné effacés, lignes serrées
  séparées) ; Ø contrôlé sur le premier signe ; `corriger` : × entre nombres, ∅ / Φ devant un nombre, « 一 », pleine chasse ;
  provenance `ocr.moteur`, `ocr.orientation`.
- `geometrie.js` : `blocsTexte({verticaux})` : repères écrits à la verticale, lus dans les deux sens (90° / 270°).
- Fenêtre : sélecteur « Moteur OCR » (`#dxoMot`, clé `resaOcrMot`) ; mode d'emploi mis à jour.
- `docs/audit-modernisation.md` : candidats (versions, licences, essais), protocole, mesures, audit des autres domaines, feuille de route.

**Mesures** (4 plans réels hors dépôt, Chromium ; vérités : relevé manuel 250 dpi pour A et C, couche texte pour B et D)
- Qualité brute des tableaux A, B, C (466 cellules, même grille, seul le moteur change) — Tesseract → PP-OCRv6 : repères 61 → 63 / 63,
  dimensions 90 → 93 / 93, niveaux 70 → 73 / 73, angles 21 → 23 / 23, textes libres 195 → 195 / 214, total 437 → 447 / 466 ;
  cellules signalées incertaines 59 → 23 ; temps 42 → 98 s.
- Plan D (46 lignes, OCR de la zone) : repères, cotes et niveaux 43 → 46 / 46 ; cellules incertaines 15 → 0 ; 23 → 50 s.
- Qualité métier (avant = phase 5.1 / Tesseract → après) : A repères 22 → 23 / 23, cotes 7 / 7, occurrences comptées justes 19 → 22
  (aucune fausse) ; B identique (30 / 30 repères, cotes et niveaux, 28 occurrences justes) ; C cotes en mm 8 → 10 / 10, repères lus
  sur le dessin 0 → 3 ; D : repères du dessin issus de la couche texte, concordances partielles 31 → 33.
- Temps (passages séquentiels) : A 71 → 170 s, B 107 → 120 s, C 61 → 238 s (analyse du dessin 3 à 6 × plus lente : un seul fil
  WebAssembly en `file://`, et 4 à 10 × plus de blocs lus, verticaux compris).
- **Meilleur** : repères, cotes, niveaux, angles, en-têtes, signalements ; textes verticaux lus. **Équivalent** : textes libres.
  **Moins bon** : vitesse ; poids du HTML (6 → 36,5 Mo).
- Non essayés (hôtes de modèles bloqués dans l'environnement : huggingface.co, modelscope.cn, bcebos.com) : PP-StructureV3,
  PaddleOCR-VL-1.6, Docling, modèles officiels de PaddleOCR.js, détection PP-OCRv6 dans le navigateur.

**Écarts voulus** (tests existants) : `t_ocr` : le contrôle du bouton « Annuler » choisit Tesseract le temps de l'essai (PP-OCR finit le
petit tableau avant que la progression soit observable : c'est l'interface qui est contrôlée) ; la provenance attendue nomme
PP-OCRv6 au lieu de Tesseract. Nouvelle suite `t_ppocr` (18 contrôles).

**Tests** : `python tests/run.py complet -j 4` : 33 / 33 suites vertes (21/10/2026, Chromium), dont t_avap (moteur, feuilles, DXF,
CSV identiques), t_ocr, t_ppocr.

**Défauts révélés par le plan D, hors OCR, non corrigés ici** : tableau en texte voisin d'un autre tableau coupé à la lecture
automatique (contournement : zone + « Analyser la zone ») ; titre « Sous Toiture 1 : 25 » non reconnu comme vue (0 occurrence comptée).

**Non validé** : Firefox, Safari, tablette ; ordinateurs lents (mémoire, temps) ; autres plans réels ; repères verticaux en vrai texte
d'image (scans) ; Ø parfois absent de la lecture PP-OCR (contrôle géométrique seulement).

## Phase 5.1 — corrections après essais sur trois plans réels (non publiée, sans numéro de version)
**Demande (Kévin, 21/10/2026)** : corriger les défauts révélés par la campagne de validation de la phase 5 (trois plans réels,
hors dépôt) avant toute nouvelle fonction ; moteur, 3D et exports inchangés ; `#appVer` reste v3.1 ; aucun ouvrage créé d'office.
**Décision de Kévin (DN)** : un DN dans la colonne Ouverture signale une réservation circulaire probable ; DN gardé comme
information, jamais utilisé comme diamètre ; « diamètre réel de réservation à confirmer » ; création impossible sans cote confirmée.

**Fait** (détail : `modules/import/README.md`, § Phase 5.1)
- A1 unités : seule l'unité écrite contre la cote compte ; « 500x500 — 4,86m » n'est plus lu 500 × 500 m ; unité de la cellule
  contraire à celle de la colonne → `conflitUnite`, unité à confirmer, jamais remplacée par l'en-tête à la création (`dxnU`) ;
  provenance `L.uniteOrigine` / `origineImport.unite_origine` ; grille OCR : Largeur / Hauteur / Diamètre jamais fusionnées avec une
  colonne Ouverture.
- A2 colonnes : « réservation(s) » n'est un titre de repères que seul ; Axe / Niveau réservation, Hauteur (d')axe → niveau ;
  Longueur ; en-têtes à plusieurs niveaux reconstruits (textes et grille OCR), unité du titre de groupe (« DIMENSIONS (mm) »).
- A3 nature `trappes` (trappes, regards, feuillures…) : tableau écarté, lignes consultables, jamais créées ; aciers inchangés.
- A4 OCR sur un tableau déjà lu : remplacement proposé explicitement (correspondances, choix gardés, lignes retirées annoncées).
- B1 vues : dessus / dessous = plan ; titre de 1,45 à 1,8 × la médiane admis avec un mot-clé de vue ; renvoi, paragraphe, bloc de
  notes : pas un titre ; « Renforts » = détail ; titre sans dessin : pas une vue ; cadre de feuille jamais rattaché ; partie sans titre
  d'une vue rattachée ; une grande vue titrée n'est plus incertaine par sa seule aire.
- B2 repères : nature de chaque mention (repère isolé, identifiant « 1-D1 », multiplicateur « 2x », annotation) ; tiret regroupé
  avec ses lettres avant OCR ; seules les mentions isolées localisent.
- B3 comptage : jamais dans une vue sans titre ; pas de repli sur le ferraillage si la vue en plan est douteuse ; repère étiqueté
  plusieurs fois sans quantité au tableau : nombre non décidé.

**Essai sur les trois plans réels (hors dépôt, Chromium, mêmes scénarios que la campagne)** — avant (phase 5) → après :
- PDF A (ouvrage circulaire, tableau et repères en tracés, 2 pages ; zone + OCR du tableau) : 23 lignes, 22 repères, 7/7 cotes l × h
  (inchangé) ; 10 DN gardés sans cote ; vues incertaines 4 → 3 ; vue en plan p. 2 : non reconnue → reconnue ; occurrences comptées
  15 (toutes fausses : treillis « 1-Dx », détails) → 19, toutes sur la vue en plan ; observations non rattachées 33 → 7.
- PDF B (texte extractible, vues dessus 1:100 / dessous 1:50) — lecture automatique : repères 0/30 → 30/30, cotes en mm 0 → 30/30,
  niveaux NGF séparés 0 → 30, trappes mêlées aux réservations 4 → 0 ; vues : dessous « autre » incertaine → plan ; 2 fausses vues de
  cartouche → 0 ; occurrences comptées justes 0 → 28 (R09, étiqueté deux fois sans quantité : non décidé ; R07 sans étiquette).
  OCR manuel de la même zone : 64 lignes (doublons) → remplacement proposé puis 30 lignes.
- PDF C (planche tournée, tout en tracés ; zone + OCR) : cotes lues en mètres 4 → 0 ; cotes justes en mm 0 → 8/10 (R01 / R03 :
  « 3550 » lu par l'OCR, signalé) ; tableau tourné reconnu (270°) ; aciers écartés. Repères et titres verticaux toujours non lus.
- Temps (passage séquentiel) : A 91 → 71 s, B (automatique + analyse) 77 s, C 83 → 61 s (passage « avant » en parallèle : majoré).

**Écarts voulus** : aucun test existant modifié. Nouvelle suite `t_phase51` (cas synthétiques anonymes de chaque défaut).
Comportements changés volontairement : une vue sans titre ne compte plus d'occurrences ; un titre sans dessin n'est plus une vue.

**Tests** : campagne complète `python tests/run.py complet -j 4` : 32/32 suites vertes (21/10/2026, Chromium), dont t_avap
(moteur, feuilles, DXF, CSV identiques) et t_phase51 (33 contrôles). Hors du bloc généré `cpi-src`, `app/CoffraPlan.html` est identique à
la phase 5 (vérifié octet par octet).

**Non validé** : Firefox, Safari, tablette ; autres plans réels ; repères et titres verticaux (planche tournée) ; réservations à côtés
courbes ; un mot isolé de cartouche lu par OCR peut encore former une vue (PDF A, sans occurrence comptée dedans).

## Phase 5 — lecture des nomenclatures, vues techniques, occurrences (non publiée, sans numéro de version)
**Demande (Kévin, 20/10/2026)** : améliorer la lecture des nomenclatures, reconnaître les vues techniques d'un plan PDF et
dédoublonner les occurrences d'une réservation, avec un gain mesurable sur le PDF de référence ; structures JSON pour une
future IA locale (aucune IA ici) ; `#appVer` reste v3.1 ; moteur, 3D et exports inchangés.
**Décision de Kévin** : quantité > 1 au tableau → un seul ouvrage, `nb` = quantité.

**Fait**
- Nomenclatures : colonnes Nb, Nb., Nombre, Qté, Quantité, Fonction, Largeur, Hauteur, Ø, Diamètre (unité dans le titre ou
  dessous) ; ordre des cotes : ouverture écrite, Ø, Ø vide ou « - » → Largeur × Hauteur, sinon ambiguïté signalée ; tiret ou
  vide = absent ; DN jamais pris pour le Ø ; tableaux tournés de 90°, 180°, 270° ; en-tête cherché sous un cartouche.
- OCR : lecture cellule par cellule sur la grille de traits (24 ou 36 px de lettre), variantes niveaux de gris et couleur
  d'encre dominante (nuages de révision effacés), colonnes réaffectables, corrections gardées à la relance ; repères encadrés
  lus ; « 53 » → S3 dans une colonne S1, S2… (signalé).
- Vues techniques (`vues.js`) : plan, coupe, élévation, détail, ferraillage supérieur / inférieur, autre ; id stable, page,
  région, titre, type, partie, échelle, niveau, confiance ; contours et repères rattachés à leur vue ; proximité repère ↔
  contour cherchée dans une même vue.
- Occurrences : quantité attendue (tableau = référence), localisées (une seule vue comptée : plan, sinon ferraillage),
  représentations, restantes ; jamais de multiplication par le nombre de vues ; provenance `occurrences`, `vue`, `role`.
- Formes hors nomenclature : section repliée sous la nomenclature, classées à examiner / représentation / parasite probable,
  chacune avec sa raison ; rien supprimé.
- Export « ⬇ Analyse (JSON) » : tables, tableRows, views, graphicalObservations, physicalOccurrences, associations,
  evidence, uncertainties.

**Corrections après relecture indépendante (Kévin, 21/10/2026)**
- A — limites des vues : un trait long ouvert (axe, ligne de cote, trait de liaison) relie des cases sans étendre une
  région ; un bloc très étendu (cartouche, notes) n'est plus rattaché au titre voisin ; un petit îlot accroché par un trait
  (bulle d'axe) reste hors de l'emprise ; région trop étendue, couvrant le titre d'une autre vue ou empiétant sur une autre
  vue titrée → vue **aux limites incertaines** : jamais comptée pour les occurrences, contour jamais proposé d'office ni
  concordance forte par elle seule (`vueIncertaine` du rapprochement).
- B — observations : occurrence physique, représentation **rattachée** à une occurrence (même position relative, ou
  occurrence unique pour une coupe / élévation / détail) et **observation non rattachée ou ambiguë** (rôle `non_rattachee`,
  motif, compte « non rattachée(s) », incertitude `observation_non_rattachee` du JSON). Quantité du tableau inchangée, aucun
  ouvrage ajouté.

**Écarts voulus (tests)** : t_detection et t_rapprochement ouvrent la section repliée « Formes du dessin hors nomenclature »
avant de la lire ; t_pdf lit la colonne Source en 11e position (colonne Nb ajoutée). Nouvelle suite `t_vues` (plans fictifs anonymes).
Après relecture : t_vues attend 3 représentations (et non plus 5) dans le cas « coupe + ferraillage à une autre position »,
les deux autres observations étant non rattachées (correction B) ; ajout des cas « vues reliées par une ligne de cote, axe
à bulle, bloc de notes » (A) et « même repère, positions incompatibles » (B).

**Essai sur le PDF de référence (hors dépôt, Chromium)** — v3.1 → phase 5 (20/10) → après corrections (21/10) :
- tableau (OCR de la zone) : 0/7 ligne lue → 7/7 lignes, 7/7 quantités, 7/7 cotes ; R4 Ø65 (Ø50 de la désignation non pris) ;
- vues : 24 → 25 ; la vue « ferraillage radier » couvrait 1621…3376 × 0…2384 pt (moitié droite de la page : cartouche,
  notes) ; elle est ramenée à 744…1983 × 0…992 pt, marquée incertaine (elle touche le titre d'une vue voisine) ; le bloc de
  droite devient une vue sans titre incertaine ; 4 vues incertaines sur 25 ;
- occurrences : 7 localisées sur 9 (R1 1/2, R4 0/1) ; R1 et R5 sont des lectures OCR incertaines (« ri », « RS ») contrôlées
  à l'œil sur un rendu de la page : bonnes ; la 2e R1 et R4 sont dessinées sur la page 1 mais non lues par l'OCR ; la seule
  localisation de R4 (page 2, vue de ferraillage) est une observation non rattachée, à vérifier ; aucune multiplication ;
- formes : 44 proposées au même niveau → 5 rattachées, 41 reclassées automatiquement « parasite probable » dans la section
  repliée (aucune vérifiée une à une).

**Tests** : campagne complète `python tests/run.py complet -j 4` : 31/31 suites vertes (20/10/2026, Chromium), dont t_avap
(moteur, feuilles, DXF, CSV identiques).

**Non validé** : Firefox, Safari, tablette ; autres plans réels que celui de référence ; deux vues dessinées l'une contre
l'autre sans blanc restent partagées approximativement (signalé « limites incertaines ») ; titres de vue tournés non lus.

## v3.1 — importer un plan DXF ou PDF
**Demande (Kévin, 20/10/2026)** : préparer la version v3.1 à partir des travaux faits depuis v3.0, sans fonction nouvelle.
Détail technique de chaque étape (demandes, écarts voulus, tests) : sections « Détail v3.1 » de `CHANGELOG.md`.

**Nouveautés**
- **📥 Importer un plan** : une seule fenêtre pour les plans DXF et PDF du bureau d'études. Les réservations lues
  deviennent des ouvrages CoffraPlan, avec les cotes du plan. Rien n'est créé sans sélection et confirmation, les ouvrages
  déjà saisis ne sont pas modifiés, et le débit d'un ouvrage importé est le même que celui de la même saisie à la main.
- **DXF** : formes dessinées (rectangles, y compris en 4 traits séparés, et cercles) et nomenclatures de réservations
  (tableaux, textes, blocs, espaces Objet et présentations). L'unité du dessin est demandée quand le fichier ne la donne pas.
- **PDF** : aperçu des pages, zoom, choix d'une zone, lecture des tableaux quand le texte du PDF est lisible, et saisie
  assistée sinon (on recopie les cotes en regardant la page).
- **Lecture des nomenclatures dessinées en traits ou numérisées (OCR)**, directement dans le fichier, sans connexion
  internet : une grille de vérification signale en orange les cellules douteuses ; on corrige, ajoute, fusionne ou retire des
  lignes avant de créer les ouvrages.
- **🔎 Analyser le dessin** (PDF) : CoffraPlan retrouve les réservations sur le plan et les rapproche des lignes de la
  nomenclature. Chaque ligne reçoit un état : concordance forte, partielle, correspondance probable, conflit, non retrouvée.
  Les cotes du tableau restent prioritaires ; un clic sur une localisation affiche la page et le repère ; un rapprochement
  faux peut être rejeté, et les corrections sont gardées si l'on relance l'analyse.
- **Traçabilité** : chaque ouvrage importé garde son origine (fichier, page, ligne, repère, textes et cotes lus, résultat de
  l'OCR et du rapprochement). Elle est conservée dans la sauvegarde et à la réouverture du projet.

**Corrections**
- Ouverture d'un PDF juste après la fermeture d'un autre : le message « fichier PDF illisible » pouvait s'afficher à tort.
- Arrêt de la lecture OCR au mauvais moment : une erreur pouvait apparaître dans la console du navigateur (sans effet visible).
- Bouton « Annuler » pendant la lecture OCR : un clic pouvait être ignoré, car le bouton était recréé à chaque avancement de
  la barre de progression. Il reste désormais le même jusqu'à la fin de la lecture.

**Limites connues — à lire avant usage sur chantier**
- **Vérifier les associations automatiques** : sans cote écrite près du repère ni échelle, une concordance reste au mieux
  « partielle ». Une note ou une liste qui cite un repère peut donner une fausse localisation : contrôler chaque ligne avant
  de créer les ouvrages.
- **OCR** : les textes tournés (nomenclature dessinée à la verticale) ne sont pas lus ; utiliser alors la saisie assistée.
  Compter une vingtaine de secondes par grande page.
- **Contours courbes** : les réservations à côtés courbes (voile circulaire, par exemple) ne sont pas reconnues sur le dessin.
- Beaucoup de formes « hors nomenclature » (cadres de ferraillage notamment) sont proposées, jamais cochées d'office.
- Pas de fichier DWG ; pas de rapprochement détaillé pour les DXF.
- **Navigateurs** : vérifié sous Chrome / Edge (Chromium) seulement. Firefox, Safari et tablette ne sont pas validés.
- Non vérifiés non plus : impression papier ou traceur, DXF dans AutoCAD, glTF / IFC dans Revit ou une visionneuse.
- Le fichier HTML pèse environ 6 Mo (lecteur PDF et moteur OCR intégrés pour fonctionner hors connexion).

**Écarts voulus** : numéro v3.1 ; `t_ux` attend v3.1 ; `t_v30` vérifie « v3.x » (le numéro exact reste contrôlé par `t_ux`).
Moteur, débit, feuilles et exports inchangés.

**Tests** : campagne complète `python tests/run.py complet -j 4` : 30/30 suites vertes (20/10/2026, Chromium) ; mode d'emploi v3.1 généré.
Détail des essais sous charge : section « Détail v3.1 — correctifs finaux avant publication ».

## Détail v3.1 — correctifs finaux avant publication
**Demande (Kévin, 20/10/2026)** : corriger avant la publication les deux anomalies relevées sous surcharge pendant la
préparation de v3.1, sans développement fonctionnel ; ne rien modifier pour t_ux.

**Constats (préparation, 20/10/2026)** : scénario t_ux « alerte au clavier (Entrée) », échoué une fois en CI après la fusion
de la stabilisation : 24 passages conformes sur 24 sous charge (-j 4), non reproduit, test inchangé, intermittence notée.
Sous une charge plus forte que la CI (même suite lancée 4 fois en parallèle) : t_pdf « faux PDF : erreur de lecture
affichée » 1 fois sur 8 ; t_ocr 2 fois sur 14 (clic « Annuler » d'une reconnaissance en cours jamais abouti ; une exception
dont le détail n'a pas été conservé, cause non établie, aucune correction inventée).

**Fait**
- `tests/t_pdf.py` (défaut du test) : après le refus du DWG, `#dxiZ .hint` existe déjà ; l'attente portait sur ce seul
  élément et pouvait lire l'ancien message. Le test attend maintenant que le message du faux PDF (« %PDF absent ») remplace
  celui du DWG et vérifie que « DWG » n'y figure plus ; contrôle du bouton de création désactivé conservé.
- `modules/import/fenetre.js` (défaut de l'appli) : `dxoProg` réécrivait tout son HTML à chaque progression et recréait le
  bouton « Annuler » ; il le crée une fois par opération, puis ne met à jour que le texte et la barre ; `dxoStop()` et le
  nettoyage en fin d'opération inchangés. HTML réassemblé (`assembler.py`).

**Écarts voulus** : `t_ocr` : vérification ajoutée (« progression OCR : bouton « Annuler » inchangé pendant les
actualisations » : même élément après au moins 3 actualisations, puis annulation effective). Elle échoue sur l'appli
précédente (main e9870fc) et passe après correction. `t_pdf` : attente et libellé du contrôle du faux PDF précisés.

## Détail v3.1 — stabilisation avant Release
**Demande (Kévin, 20/10/2026)** : examiner l'instabilité de `t_pdf` sous charge et corriger la seule cause identifiée, sans
relance automatique ni test désactivé ; aucune évolution métier.

**Fait** : deux défauts préexistants de l'appli, révélés par la campagne `-j 4` (la charge élargit la fenêtre de course).
- `pdf.js` (depuis 11ef359) : `fermer()` ne faisait pas attendre la libération du document ; PDF.js partage son worker et refuse
  un nouveau document tant qu'une libération est en cours (« PDFWorker.create - the worker is being destroyed ») → « fichier PDF
  illisible » si un PDF est ouvert juste après en avoir fermé un. `lire()` attend désormais la dernière libération.
- `ocr.js` : un arrêt de l'OCR pendant la conversion de l'image laissait Tesseract.js écrire dans un worker détruit (TypeError
  « postMessage » non interceptée, `t_ocr` intermittent). L'image est convertie en PNG avant l'appel (même entrée que Tesseract
  produisait lui-même) et un arrêt survenu entre-temps lève « annulé ».

**Écarts voulus** : vérifications ajoutées, sans rien modifier d'existant : `t_pdf` (3 lectures enchaînées sur fermeture
immédiate, échouait 3 fois sur 3 avant), `t_ocr` (arrêt pendant la préparation de l'image, échouait avant). Moteur, débit,
feuilles et exports inchangés.

## Détail v3.1 — finalisation du rapprochement nomenclature ↔ dessin (phase 4)
**Demande (Kévin, 20/10/2026)** : rapprochement automatique et déterministe nomenclature ↔ dessin (repère, fiabilité,
proximité, lignes de rappel, forme, cotes, page / vue, quantité) ; cotes du tableau prioritaires, concordance partielle
admise, conflit seulement sur la même dimension ; OCR ciblé des repères dessinés en traits ; multipage par repère seulement,
plusieurs vues = une ligne, quantité jamais inventée ; états forte / partielle / probable / conflit / non retrouvée / hors
nomenclature ; corrections gardées à la relance ; correctifs de relecture (critères multipages, identité stable, plus de
`Math.min/max(...tableau)` dans `detecteur.js`, erreur lisible sans fenêtre bloquée).

**Fait** : `pdf.js` : petits tracés (`petits`) relevés par `chemins`. `geometrie.js` : `blocsTexte` (repères dessinés
regroupés), `rappels` (lignes de rappel, un coude), `index`, `emprise` (bornes sans décomposition de tableau). `ocr.js` :
`lireBlocs` (mosaïque des blocs, tuiles de rendu, relecture ligne des repères douteux, brut / confiance / corrections /
zone conservés). `rapprochement.js` (nouveau) : occurrences du repère (clé exacte ou approchée → incertaine, confiance < 30 %
ignorée, listes en colonne écartées), contour et cotes écrites voisins, vérification cote par cote (unité essayée si non
écrite), états, quantité (source tableau, localisations, cohérence), contour principal unique ou un par page.
`detecteur.js` : bornes par boucle (`bornes`). Fenêtre : « 🔎 Analyser le dessin » (toutes les pages ou la zone, option OCR,
Arrêter), état et détail par ligne, localisations cliquables, « ✕ rejeter le rapprochement », bilan, formes « hors
nomenclature » ; identité stable des contours (`dxrCle`, mémoire `D.RK`) ; erreur affichée et fenêtre rendue. Provenance
`origineImport.rapprochement`. Mode d'emploi § 7.22 réécrit.

**Écarts voulus** : `t_detection.py` : message attendu « 2 page(s) : 10 forme(s) possible(s) » (l'analyse couvre désormais
toutes les pages au lieu de la page affichée) et attente sur `!DXI.rJob` (analyse asynchrone). Nouvelle suite
`t_rapprochement.py` (34 vérifications, `tests/rapprochement_fictifs.py`) dans les suites rapides. Moteur, débit, feuilles
et exports inchangés.

**Essai local sur le PDF et le DXF réels (20/10/2026, hors dépôt, comptes seulement)** : PDF (2 pages A0, textes vectorisés) :
nomenclature lue par OCR, 23 lignes ; analyse ≈ 28 s, 1 425 textes dessinés lus ; 0 forte, 16 partielles, 5 probables,
0 conflit, 2 non retrouvées (une absente du plan, une mal lue au tableau), 21 lignes localisées (31 localisations, 8 en plan
et en détail), 3 contours rattachés, 17 formes hors nomenclature (surtout des cadres de ferraillage). Aucune cote vérifiable
(pas de cote écrite près des repères, pas d'échelle). Version précédente : 23 non retrouvées. DXF : inchangé (5 rectangles
en `LINE`), pas de rapprochement détaillé.

**Non validé** : Chromium seul ; réservations à côtés courbes non reconnues ; faux positifs possibles (listes et notes
contenant un repère) ; durée de l'OCR sur grands plans ; DXF sans rapprochement détaillé.

## Détail v3.1 — repérage géométrique des réservations (PDF vectoriel et DXF)
**Demande (Kévin, 20/10/2026, phase 4)** : repérer les réservations directement dans le dessin d'un PDF vectoriel (page ou
zone), en proposer les dimensions (échelle jamais supposée : calibration simple ou cote écrite), les rapprocher des
nomenclatures sans doublon, les créer après validation par l'adaptateur existant, provenance complète ; DXF : rectangles en
4 `LINE` indépendantes. Sans nouvelle bibliothèque, hors connexion, rien de coché ni créé d'office.

**Fait** : `geometrie.js` (nouveau, intégré par `assembler.py`) : rectangles et cercles d'une page, parasites écartés avec leur
raison (cadre de feuille, cartouche subdivisé, cellules, tableaux, cadres de détail, très grands contours), repères et cotes
écrites voisins. `pdf.js` : parcours des tracés commun (`cheminsPage`), `CPI.pdf.chemins` (relu à la demande). `detecteur.js` :
`rectSegments` (graphe d'extrémités, côtés en morceaux réunis) et rectangles en `LINE` d'un même calque, sans ambiguïté, sans
doubler une polyligne ; `dxf.js` garde les extrémités des `LINE`. `nomenclatures.associer` : contours et repères d'une même page
PDF, cotes comparées à l'échelle de la page. Fenêtre (`dxr*`) : « 🔎 Repérer les réservations », contours cliquables, échelle
(2 points ou « Éch. 1/50 » lue sur la page), tableau éditable (forme, cotes, h, référence), états repérée / à confirmer /
à compléter / non exploitable, création par `adaptateur.versPlan`, provenance `type:'detection'`. Mode d'emploi § 7.22.
Banc `tests/t_detection.py` (38 vérifications) sur `tests/detection_fictifs.py` (PDF 2 pages dont une tournée, DXF).

**Écarts voulus** : aucun test existant modifié. PDF : la nomenclature peut désormais être rattachée à un contour du dessin
(seulement après « Repérer ») ; DXF : 4 `LINE` formant un rectangle sans ambiguïté deviennent un candidat de plus (les fichiers
des bancs existants n'en contiennent pas). Moteur, débit, feuilles et exports inchangés.

**Essai local sur le PDF et le DXF réels (20/10/2026, hors dépôt, comptes seulement)** : PDF (plan de ferraillage, 2 pages A0,
textes en grande partie vectorisés, pas d'échelle écrite lisible) : page 1, 5 contours proposés, 52 écartés ; page 2,
15 proposés, 45 écartés ; 0 repère lu (textes dessinés en traits) ; < 2,5 s par page. Les réservations du voile circulaire
(côtés en arc) ne sont pas reconnues ; une partie des propositions sont des cadres d'étiquettes : la vérification ligne à
ligne reste indispensable. DXF réel : 5 rectangles en `LINE` assemblés (2 calques), lecture + détection ≈ 1,3 s.

**Non validé** : Chromium seulement ; aucun PDF de plan de réservations réel avec repères en texte ; tablette ; impression.

## Détail v3.1 — reconnaissance OCR locale des nomenclatures PDF
**Demande (Kévin, 19/10/2026, phase 3)** : lire les nomenclatures de réservations dont les textes sont dessinés en tracés ou
numérisés, sur une zone de l'aperçu, en local (aucune API, aucun CDN, aucun modèle téléchargé, `file://`, HTML autonome) ;
valeurs brutes gardées, doutes signalés, grille de vérification éditable, rien de coché d'office, aucun filtre, même
création et provenance OCR ; moteur de coffrage inchangé.

**Fait** : Tesseract.js 7.0.0 (cœur `simd-lstm`, modèle français `best_int`, Apache-2.0) copié dans
`modules/import/vendor/tesseract/` et intégré par `assembler.py` (blocs `tess-*`, empreintes SHA-256 vérifiées, wasm et modèle
en gzip + base64), lancé dans un worker blob au premier clic. `ocr.js` (nouveau) : rendu de la zone par le PDF.js existant
(`CPI.pdf.rendreZone`), prétraitement léger de la copie, deux passes de lecture, cellules vides relues, mots → textes et
traits de la page, tableau par `nomenclatures.analyser`, corrections prudentes selon la colonne (O/0, I/1, S/5, B/8 ; @ → Ø ; un nombre seul n'est jamais converti en Ø),
doutes (confiance < 75, correction, repère en double ou hors suite). Fenêtre : « Reconnaître le tableau (OCR) » à côté
d'« Analyser la zone », progression, annulation, grille de vérification (cellules éditables et signalées, emplacement sur la
page, insérer / fusionner / retirer, corrections gardées si l'OCR est relancé), ajout à la nomenclature sans doublon avec la
lecture texte. `nomenclatures.js` : colonne `acier` (tableaux d'aciers écartés), un en-tête ne contient pas de chiffre,
`ligne()` exporté, provenance `type:'ocr'` + clé `ocr` (brut, confiance, corrections, valeurs corrigées, incertain).
Mode d'emploi § 7.22 « Reconnaître le tableau (OCR) ». Banc `tests/t_ocr.py` (50 vérifications) sur des PDF fictifs écrits
par `tests/pdf_ocr_fictifs.py` (textes en contours de glyphes via fontTools, tableau numérisé, page tournée, avec et sans
bordures).

**Écarts voulus** : message d'un PDF sans nomenclature lisible « … : saisie assistée » → « … : OCR ou saisie assistée » ;
t_pdf vérifie le nouveau libellé (vérification modifiée, documentée ici). HTML : 3,34 Mo → 6,0 Mo (moteur OCR). CI : polices
Liberation / DejaVu installées, `fonttools` ajouté aux dépendances de test. Moteur, débit, feuilles et exports inchangés.

**Corrections de relecture (Kévin, 20/10/2026)** : (1) un nombre seul peu sûr dans les dimensions n'est plus converti en
diamètre (« 250 » → « Ø50 », « 900 » → « Ø00 », « 2500 » → « Ø500 » auparavant) : valeur gardée, ambiguïté signalée, Ø à
préciser par l'utilisateur ; t_ocr : la vérification « Ø reconnu ou interprété » devient « Ø reconnu, sinon nombre brut gardé
et signalé » (vérification modifiée, voulue) + test de non-régression 250 / 900 / 2500. (2) Nouvelle zone sans nomenclature
après un tableau reconnu : la grille précédente n'est plus présentée comme le résultat ; elle reste affichée avec ses
corrections, marquée « reconnaissance précédente » ; test du scénario tableau A puis zone B. Plan réel : résultats inchangés.
Test réseau de t_ocr : les requêtes Google Fonts de l'interface (héritées, hors OCR) sont bloquées et ignorées ; toute autre
requête fait échouer le test.

**Essai local sur le PDF réel (19/10/2026, hors dépôt, comptes seulement)** : tableau de la page 2 (vectorisé) reconnu en
≈ 7 s : 23 lignes sur 23, toutes les colonnes reconnues. Cellules comparées à la nomenclature du DXF du même plan : 15
erronées sur 207, dont 12 signalées ; repères 2 erreurs sur 23 (signalées), ouvertures, niveaux, angles, types et
désignations sans erreur ; erreurs restantes surtout dans les observations (nuages de révision) et le DN. Correction d'une
cellule dans la grille, ajout (aucune ligne cochée), création d'un ouvrage rectangulaire avec provenance OCR : conformes.
Aucune requête réseau.

**Non validé** : Firefox, Safari, tablette réelle (seul Chromium est testé) ; véritables scans (seul un scan fictif est testé) ;
autres PDF réels (autres logiciels de DAO) ;
temps et mémoire sur un poste modeste ; textes tournés dans un tableau ; tableaux sur plusieurs pages.

## Détail v3.1 — « Importer un plan » : fenêtre unique DXF et PDF
**Demande (Kévin, 19/10/2026)** : remplacer « Importer un plan DXF » par une entrée unique, lire les PDF (textes extractibles),
détecter leurs nomenclatures de réservations, aperçu des pages, sélection de zone, saisie assistée quand le tableau n'est pas
lisible (PDF dont les textes sont vectorisés), même création et même provenance que le DXF ; appli toujours hors connexion.

**Fait** : PDF.js 6.4.299 (Apache-2.0, build legacy) intégré tel quel au HTML par `assembler.py` (empreintes SHA-256,
`vendor/pdfjs/`), chargé à l'ouverture d'un PDF, worker lancé en `file://`, aucune requête réseau. `modules/import/pdf.js` :
textes et traits par page (rotation et matrices appliquées, Y vers le haut), nature de chaque page (texte, mixte, vectoriel,
image). `nomenclatures.js` : page et format gardés sur les tableaux, provenance PDF (`page`, `zone`, `type:'saisie'`).
Fenêtre « 📥 Importer un plan » (barre, carte Plans, accueil) : DXF ou PDF, glisser-déposer, DWG / IFC refusés avec un message ;
PDF : onglets Nomenclature et Aperçu du plan (pages, zoom, tableaux encadrés, ligne encadrée), zone à analyser, saisie
assistée, création par le même chemin (contrôles du moteur, références sans doublon, annulation). Mode d'emploi § 7.22.
Banc `tests/t_pdf.py` (PDF fictifs écrits par `tests/pdf_fictifs.py`, sans bibliothèque).

**Écarts voulus** : titre et libellés « Importer un plan DXF » / « Importer DXF » → « Importer un plan » ; t_dxf_ui vérifie le
nouveau titre et l'acceptation des .pdf (vérification modifiée, documentée ici). HTML : 1,47 Mo → 3,3 Mo (PDF.js). Moteur,
débit, feuilles et exports inchangés (t_avap).

**Essai local sur un PDF réel (19/10/2026, hors dépôt, comptes seulement)** : 2 pages tournées de 270° lues, aperçu des deux
pages correct, nomenclature visible sur la page 2 ; 125 textes extractibles pour ≈ 17 500 tracés : les textes de la
nomenclature sont dessinés en traits, aucune ligne lue, aucune inventée ; rapport « saisie assistée ». Une ligne saisie avec
des valeurs fictives a donné un ouvrage avec sa provenance (page 2). Aucune requête réseau.

**Non validé** : Firefox, Safari, tablette réelle ; PDF d'autres logiciels que le générateur de test et ce plan ; tableaux
continués sur plusieurs pages sans en-tête ; OCR (non développé).

## Détail v3.1 — nomenclatures de réservations dans l'import DXF
**Demande (Kévin, 19/10/2026)** : un vrai plan de bureau d'études donnait 772 formes pour une nomenclature de 23 réservations
placée dans une présentation. Détecter les nomenclatures de réservations (espace Objet et présentations), garder toutes leurs
lignes sans filtre, rapprocher les lignes des géométries, les proposer en priorité dans la fenêtre, provenance étendue.

**Fait** : `dxf.js` : espace de chaque entité (code 67, BLOCK_RECORD → LAYOUT : nom de la présentation), textes (TEXT, MTEXT,
ATTRIB, MULTILEADER ; codes %%c, mise en forme MTEXT retirée) et traits droits de tous les espaces, contenu des blocs insérés
et des ACAD_TABLE (bloc de rendu) transformé dans le repère de l'espace qui les contient. Détecteur : contour d'une présentation
non proposé (autre repère que le dessin). `nomenclatures.js` (nouveau) : reconstruction des tableaux (grille de traits, sinon
position des textes ; titres de colonne sur plusieurs lignes, cellules multilignes ou vides, en-tête en haut ou en bas,
plusieurs tableaux), nature décidée sur l'en-tête et le titre (tableau d'aciers ou autre : signalé, écarté), lecture des
cotes sans invention (DN ≠ ouverture, SO / à définir / « / » → manquant, niveau et angle gardés en texte), rapprochement
trouvee / probable / multiple / absente (repère texte, attribut ou flèche de ligne de repère, proximité, cotes), espace
Objet seulement. Fenêtre : onglets « Nomenclature des réservations » (par défaut) et « Géométries du dessin » (géométries
rattachées retirées), sélection libre, cotes / forme / hauteur / référence / géométrie modifiables, création par le même
chemin (adaptateur, contrôles, références sans doublon). `origineImport` d'un ouvrage de nomenclature : `type:'nomenclature'`,
espace, présentation, tableau, ligne, repère, textes des cellules, géométrie (trouvée ou choisie), choix et corrections, indice
source. Mode d'emploi § 7.22. Banc `tests/t_nomenclature.py` (DXF fictifs `tests/dxf_nomenclatures.py`, 18 scénarios).

**Essai local sur un plan réel (19/10/2026, comptes seulement, fichier hors dépôt)** : 23 lignes lues sur 23 attendues, 2
tableaux d'aciers écartés, 2 colonnes non reconnues gardées telles quelles ; chaque repère est dessiné plusieurs fois (vues,
coupes) : toutes les lignes « plusieurs possibles », jusqu'à 30 contours par ligne. Correction : les contours de mêmes cotes
sont proposés en premier (ils pouvaient tomber au-delà des 12 propositions affichées). Unité du dessin absente du fichier :
à choisir dans la fenêtre. Fenêtre ouverte sur ce plan dans Chromium : 23 lignes, aucune cochée, sans erreur JS.

**Test de bout en bout sur le plan réel (19/10/2026, hors dépôt, valeurs saisies fictives)** : scénarios rectangle complet,
DN / SO sans cotes, contours ambigus, sauvegarde / réouverture, annulation : conformes. Écart corrigé : la provenance d'une
géométrie rattachée (`origineImport.geometrie`) ne notait pas l'unité du dessin choisie dans la fenêtre, alors que `centre`
et `dims_source` sont dans cette unité ; ajout de `geometrie.unite` (clé optionnelle, anciens fichiers inchangés, moteur non
concerné). t_nomenclature vérifie la nouvelle clé.

**Écarts voulus** : un contour fermé dessiné dans une présentation n'est plus proposé comme réservation (il l'était, avec des
coordonnées de feuille). Aucun écart sur le débit, les feuilles et les exports (t_avap).

**Non validé** : création d'ouvrages à partir du plan réel ; ACAD_TABLE
réel (seule une entité minimale fabriquée est testée) ; fenêtres de présentation (VIEWPORT) non interprétées : un repère placé
seulement dans une présentation ne relie pas la ligne au dessin ; Chromium seulement.

## Détail v3.1 — import DXF dans l'appli
**Demande (Kévin, 19/10/2026)** : rendre l'import DXF utilisable dans CoffraPlan : fenêtre « Importer un plan DXF » (fichier,
unité, calques, liste et aperçu synchronisés), préparation (forme, hauteur commune ou par ligne, référence, chantier, ouvrage,
indice du plan source), création sur confirmation explicite seulement, annulable, provenance persistante dans le plan.

**Fait** : `modules/import/fenetre.js` (fenêtre, fonctions `dxi*`) ; `modules/import/assembler.py` assemble les 5 sources dans
le bloc `<script id="cpi-src">` de `app/CoffraPlan.html` (`--check` dans `tests/syntax.sh`). Appli : boutons d'accès (barre
du haut, carte Plans, accueil) ; clé optionnelle `origineImport` des plans importés, gardée par `addP` (mise à jour) et
`fixAllPlans`, retirée par `dupP`. Enveloppe du fichier projet inchangée, aucune migration (anciens plans sans la clé).
Références automatiques du lot attribuées après réservation des références du projet et de celles saisies dans le lot,
puis contrôle final avant tout ajout (relecture PR #5) ; rappel des réglages repris (CP, montage, options) avant création.
Mode d'emploi § 7.22. Banc `tests/t_dxf_ui.py` (ajouté aux suites rapides).

**Écarts voulus** : aucun sur le débit, les feuilles et les exports des plans existants (t_avap). Sur un plan importé, les
clés internes `data-vk` / `data-glk` des feuilles (empreintes du plan) incluent la provenance ; contenu identique.

**Non validé** : aucun DXF réel ni exporté par AutoCAD ; fenêtre vue dans Chromium seulement (ni Firefox, Safari, tablette).

## Détail v3.1 — lecteur DXF du module d'import
**Demande (Kévin, 18/10/2026)** : premier vrai lecteur DXF dans `modules/import/` (unités, calques, identifiants, polylignes
fermées droites, cercles, provenance), géométries ambiguës gardées en « non pris en charge », unité absente jamais devinée.

**Fait** : `modules/import/dxf.js` (DXF ASCII R12 à R2018 : LWPOLYLINE, POLYLINE + VERTEX, CIRCLE, `$INSUNITS`, table
LAYER, handles ; arcs, largeur non nulle, POLYLINE lissées (courbe ajustée, spline), blocs, 3D et autres types → « autre »
avec leur nature ; fichiers vides, binaires, tronqués ou non
DXF refusés). Détecteur : angle droit exigé (un quadrilatère croisé passait pour un rectangle), remarque « carré
potentiel ». README du module : table du décodeur, décisions de Kévin, protocole de validation sur un vrai plan. Banc
`tests/t_dxf.py` (fichiers écrits par ezdxf, chantier fictif ; ajouté aux suites rapides). `app/CoffraPlan.html` inchangé.

**Non validé** : aucun DXF réel ni exporté par AutoCAD lu ; pas d'interface d'import.

## Détail v3.1 — stabilité de t_ux (sélecteur de fichier)
**Demande (Kévin, 19/10/2026)** : trouver la cause de l'échec intermittent de t_ux (attente du sélecteur de fichier après
Ctrl+O), sans désactiver ni affaiblir le contrôle.

**Cause** : `expect_file_chooser` de Playwright active l'interception du sélecteur sans attendre l'accusé du navigateur ;
le Ctrl+O envoyé juste après pouvait ouvrir le sélecteur avant l'interception, et l'événement était perdu (30 s d'attente).
L'appli, elle, répondait bien : sur un échec reproduit, `impJ` avait cliqué le champ fichier avec activation utilisateur.

**Fait** : `tests/lib.py` (`open_app`), `t_ux` et `t_v23` (`page`) activent l'interception à la création de la page
(écouteur `filechooser` sans effet). Les contrôles sont inchangés : t_ux échoue toujours si Ctrl+O n'ouvre plus le sélecteur.
Reproduction hors banc : 1 échec sur 40 puis 1 sur 150 avant, 0 sur 150 après. `app/CoffraPlan.html` inchangé.

## Détail v3.1 — nettoyage des noms de chantiers réels
**Demande (Kévin, 18/10/2026)** : retirer des fichiers suivis les références à des chantiers réels, remplacées par des noms
fictifs (`CHANTIER_DEMO_A`).

**Fait** : t_v23 (liste des plans : groupes, tri, recherche) avec un chantier fictif, mêmes contrôles ; t_v26 : le garde-fou
vérifie tous les fichiers suivis et compare des empreintes SHA-256 au lieu d'écrire les noms ; `tests/ref/v18.html` : seul le
texte d'exemple du champ « Nom du chantier » change (référence figée, géométrie intacte) ; exemple d'en-tête du kit et capture
`kit/references/visuel-valide-original.png` retouchés ; ligne v2.6 de ce journal reformulée. `app/CoffraPlan.html` inchangé.

**Historique** : réécrit le 18/10/2026 (git-filter-repo, branches poussées en force) ; tous les SHA ont changé. Tags v2.10 /
v3.0 et Releases à recréer à la main ; copies clonées ou en cache non effaçables.

## Détail v3.1 — module d'import de plans (fondation)
**Demande (Kévin, 18/10/2026)** : préparer l'architecture d'un module d'import de plans (lecteur, détecteur de
réservations, adaptateur CoffraPlan), sans écrire l'import DXF / IFC / PDF et sans toucher aux fonctions existantes.

**Fait** : `modules/import/` (hors appli) : `lecteur.js`, `detecteur.js`, `adaptateur.js`, contrat et cartographie
(`README.md`). Banc `tests/t_import.py` (ajouté aux suites rapides) ; `tests/syntax.sh` contrôle aussi ces fichiers.
`app/CoffraPlan.html` inchangé : aucun écart de calcul, de feuilles ni d'export ; format de sauvegarde inchangé.

**Non validé** : aucun vrai fichier DXF / IFC / PDF lu ; le contrat du lecteur sera éprouvé par le premier décodeur (DXF).

## v3.0 — exports 3D / BIM, cotes d'implantation, gel avant bêta
**Demandes (Kévin, 18/10/2026)** : 1. export glTF (.glb) depuis la vue 3D et la carte Export (même modèle, m, Y vers le haut,
une pièce = un nœud nommé par son repère, un nœud par ouvrage, couleurs de la palette, assemblé ou éclaté) ; 2. export IFC4
assemblé (projet / site / bâtiment / niveau, mm, origine locale, CP = IfcPlate, bois = IfcMember, tubes et poches =
IfcBuildingElementProxy, un IfcElementAssembly par ouvrage, extrusions ou facettes, Pset « CoffraPlan » et quantités) ;
3. cotes d'implantation (axes de l'ouvrage, cotes depuis les axes, en bleu) ; 4. gel et préparation de la bêta.

**Fait**
- **glTF 2.0 binaire** (`glbFile`) : écrit sans bibliothèque (JSON + bloc binaire) ; triangulation par three.js r170 (déjà
  intégré, non modifié). Un nœud racine par ouvrage (référence du plan), un nœud par pièce nommé par son repère, matériaux PBR
  (métal 0, rugosité 0,85) aux couleurs de la palette, « extras » : repère, désignation, dimensions, épaisseur, matériau.
  Mètres, Y vers le haut. Case « éclaté » : éclaté de la vue 3D à 100 %. Boutons : carte Export (🧊 glTF) et vue 3D (⬇ glTF).
- **IFC4** (`ifcFile`, texte STEP) : IfcProject / IfcSite / IfcBuilding / IfcBuildingStorey, unités mm / m² / m³, sans
  géoréférencement ; un IfcElementAssembly par ouvrage nommé par sa référence, placé pour que le croisement de ses axes X / Y
  soit à l'origine ; pièces IfcPlate (SHEET), IfcMember (MEMBER), IfcBuildingElementProxy (USERDEFINED : Tube carton, Tube PVC,
  Poche) ; prismes extrudés (IfcExtrudedAreaSolid, profils polygonaux, cercles, couronnes, perçages des poteaux en vides),
  autres pièces en facettes (IfcFacetedBrep) ; couleurs (IfcSurfaceStyle), matériaux (IfcMaterial), Pset « CoffraPlan »
  (Repère, Désignation, Dimensions, Épaisseur, Matériau, Chantier, Référence du plan), quantités Qto_PlateBaseQuantities /
  Qto_MemberBaseQuantities / Qto_BuildingElementProxyQuantities. GlobalId déterministes (même plan → mêmes identifiants).
  Chantier : un fichier par ouvrage, réunis dans un ZIP.
- **Pièces exportées = pièces du débit** (`bimModel`, `bimSplit`, `bimTags`) : les parois plus grandes que le panneau sont
  découpées aux joints du débit (J1a, J1b… ; phase des joints des parois cintrées reprise de `jointGeo`, nouvelle clé `R.ja`),
  le fond de goulotte en n secteurs, les pièces identiques prennent le repère de leur jumelle, les autres sont rapprochées d'une
  ligne du débit par leurs cotes, leur surface ou leur famille (planches découpées de la dalle). Les cerces évidées des caissons
  de voile (4 morceaux en 3D) forment une seule pièce, comme au débit.
- **Classe IFC « coffrage »** : vérifié dans les schémas IFC4 et IFC4X3_ADD2 fournis avec ifcopenshell — aucune classe
  d'élément physique de coffrage ; seul `IfcConstructionProductResourceTypeEnum.FORMWORK` existe, pour une *ressource*
  (IfcConstructionProductResource) sans placement ni géométrie. Classes retenues : celles demandées.
- **Cotes d'implantation** (vues en plan) : axes de l'ouvrage en bleu (trait mixte) repérés X (bulle à gauche) et Y (bulle en
  haut), cotes signées depuis les axes (+ vers la droite / le haut de la feuille) ; forme spéciale avec poteaux : tableau
  d'implantation des poteaux (x, y). **Toutes les formes** (généralisation décidée par Kévin le 18/10/2026 après essai sur 3 formes).
  Origine : centre de l'ouvrage, sauf voile cintré (Y = axe radial, X = corde à mi-épaisseur), poutre (X = axe de la poutre,
  Y = milieu de la portée nu à nu, tableau des poteaux intermédiaires), parallélépipède (X = axe du voile, Y = normale au voile
  au centre ; bords de l'ouverture cotés sur les deux parements), goulotte en arc (Y = axe de symétrie, X = milieu de l'emprise).
  Voile à joues radiales : « L ext (corde) » écrite avec « L int (corde) » sous le plan, pour laisser la place aux cotes signées.
- Version v3.0 ; mode d'emploi : § 7.20 Exports 3D / BIM, § 7.21 Cotes d'implantation, captures.

**Écarts voulus** (t_avap, contre v2.10) : vues en plan de toutes les formes — cote « L/2 » et « l/2 » remplacées par des cotes
signées ±L/2, ±l/2 depuis les axes, bulles X / Y, tableaux des poteaux ; voile radial : cotes de corde regroupées ; DXF : calques
VUES_* modifiés (axes, cotes), autres calques identiques. Débit, CSV, découpe et gabarits identiques. t_v210 : contrôle du numéro de version retiré (porté par t_ux et t_v30) ; t_v26, t_v28 : « v2.x ou suivante » admet aussi v3.x ; t_ux : version v3.0.
`tests/requirements.txt` : ifcopenshell 0.9.0.post1 (tests seulement).

**Tests** : t_v30 (nouveau) : 36 scénarios + 10 plans aléatoires par forme — IFC relu par ifcopenshell sans erreur de schéma,
une pièce IFC par pièce du débit (repère et nombre), volumes CP et bois = débit (± 1 %), volume géométrique = quantité
déclarée ; GLB assemblé et éclaté (en-tête, nœuds, noms, couleurs, unités, volumes) ; boutons ; cotes d'implantation sur 22 cas (toutes les formes et variantes).
Validateur Khronos glTF (npm `gltf-validator`, hors banc) : 72 fichiers, 0 erreur, 0 avertissement.
Campagne complète (`run.py complet -j 4`, t_avap contre v2.10) : 22/22 suites OK — t_v30 5 560, t_avap 694, t_audit 1 635,
t_gab_ident 8 878, t_gab_dalle 119 753. t_v29 (transition de la vue 3D) a échoué une fois sous charge sur une série rapide,
vert seul puis dans la campagne : sensible au temps, pas lié aux cotes.

**Limites connues (bêta)**
- glTF et IFC **non ouverts dans un vrai logiciel** (Revit, ArchiCAD, BIMcollab, Solibri, visionneuse glTF) : seuls ifcopenshell
  et le validateur Khronos les ont lus.
- Pas de géoréférencement ni de files du bâtiment : l'ouvrage arrive à l'origine du projet, à déplacer à la main.
- Plans aléatoires extrêmes (3 sur 386 essayés) : un couvre-joint ou un cadre d'about non rapproché de sa ligne du débit, un
  écart de volume de CP de 1,3 % entre la 3D et le débit (préexistant, poutre).
- Poutrelles de la dalle, tubes carton et tube PVC : exportés mais hors débit (nommés « R01-poutrelle », « R01-tube carton »).
- Béton existant (contexte transparent de la vue 3D) non exporté.
- Cotes d'implantation de la poutre : pas de cotes signées ±b/2 (largeur cotée, X = axe de la poutre). Dalle avec poutres :
  axes des poutres cotés depuis le centre comme en v2.10. Lisibilité vérifiée sur captures de cas types seulement.
- Toujours non validé : impression papier réelle, DXF dans AutoCAD, Firefox / Safari, tablette réelle, Excel, carte graphique
  réelle ; règles « à valider » de `hypRows` en attente de relecture professionnelle.

## v2.10 — échelle réelle, 3D des feuilles, correctifs A4
**Demandes (Kévin, 18/10/2026)** : v2.10 cotes et échelle réelles, plus : 1. impression A4 : vues et informations
masquées ; 2. vue 3D des feuilles encore à l'ancienne qualité, toutes formes ; 3. dalle, 3D éclatée à 100 % : le platelage
disparaît au lieu de s'élever ; 4. perçage des fonds : Ø poteau + 0 mm par défaut.

**Fait**
- **Vues à l'échelle normalisée** à l'impression : chaque vue cotée à échelle unique est redessinée avec un facteur (géométrie
  réduite, cotes et textes à leur taille) pour tomber sur l'échelle normalisée immédiatement inférieure à la place disponible
  (1/1, 1/2, 1/5, 1/10, 1/20, 1/25, 1/50, 1/75, 1/100, 1/125, 1/200). Échelle écrite après le titre de la vue, barre d'échelle
  graduée, échelles de la feuille au cartouche avec « impr. 100 % A3/A4 — fabriquer aux cotes ». Réglage « Échelle des vues » :
  Normalisée (défaut) ou Agrandie à la case (comportement v2.9). Sans échelle : vues à plusieurs échelles (poutres, poches,
  goulotte, parallélépipède), plans de découpe, 3D, courbure de voile amplifiée.
- **Impression A4** : les règles d'affichage « écran étroit » (< 800 px) ne s'appliquent plus qu'à l'écran ; Chrome pouvait
  les appliquer à la page A4 imprimée (grille à une colonne → colonne Informations écrasée, vues superposées). Dimensions
  longues (« · extrémités coupées en biais… ») repliées sous la cote : la colonne Débit du voile ne part plus en « suite ».
- **3D des feuilles MONTAGE** rendue en WebGL (même moteur que la vue interactive : grain, plis, ombres), image JPEG 2500 px,
  repères, légende et rose d'orientation par-dessus ; cadrage sur l'emprise. L'impression attend les images (15 s au plus).
  Sans WebGL ou en noir et blanc : vue vectorielle.
  En aperçu, images faites 1,2 s après la dernière saisie, et pas du tout en rendu 3D logiciel (PC sans carte
  graphique : trop lent, l'aperçu garde la vue vectorielle ; l'impression fait les images).
- **Dalle en éclaté** : le platelage s'élève au-dessus des coffrages (comme un fond supérieur) au lieu de s'effacer.
- **Perçage des fonds** : jeu par défaut 0 mm (Ø poteau exact) ; les anciens fichiers sans valeur prennent 0 mm.

**Écarts voulus** (t_avap) : spéciale avec poteaux, perçages Ø poteau + 0 au lieu de + 10 (débit, CSV, découpe, feuilles) ;
dalle, feuille de montage éclatée : note « platelage masqué » retirée, repères du platelage ajoutés. t_v25 : contrôle
« Ø poteau + 10 mm » passé à « + 0 mm » (changement demandé). t_3d : la dalle passe désormais par le contrôle commun de
l'éclaté (plus de mode « masqué »), sans modification du test. t_ux : Ctrl+P attend l'ouverture de l'impression jusqu'à 20 s
(au lieu de 400 ms), l'impression attendant désormais les images 3D des feuilles.

**Tests** : t_v210 (nouveau) 109 OK ; 21/21 suites OK (t_avap 1 076, t_coh 156, t_audit 1 635, t_gab_dalle 119 753).

**Non validé** : impression papier réelle — l'échelle n'est juste que si la boîte d'impression reste à 100 % sur le même
format (la barre d'échelle permet de le contrôler) ; carte graphique réelle et tablette ; navigateurs autres que Chromium.
Cotes d'implantation (repères d'axes) non traitées.

## v2.9 — retours terrain
**Demandes (retour de Kévin du 17/10/2026)** : 1. éclaté de la dalle : joues de poutre et poutrelles en contact, vérifier
toutes les formes ; 2. spéciale circulaire avec poteaux : trous absents des fonds en 3D ; 3. impression : vues écrasées
par les cases d'information, vues prioritaires, uniformiser ; 4. légende du pied de feuille mal alignée ; 5. calepinage de
la dalle : 4 panneaux par feuille illisibles, 2 maximum, uniformiser ; 6. rendu 3D de niveau professionnel.

**Fait**
- **Pied de feuille** sorti de la grille des cases : toujours pleine largeur, libellés de la légende jamais coupés.
- **Vues prioritaires** : colonnes de largeur fixe (un tableau large ne pousse plus les vues) ; feuilles « vue + tableau »
  à 72 % / 28 % ; chaque dessin recadré sur son contenu (`fitSvgs`) ; feuille INFORMATIONS (dalle, poutre) sans vignette
  du plan, en 3 colonnes Informations | Hypothèses | Débit (pleine page).
- **CP à découper et planches découpées de la dalle : 2 panneaux maxi par feuille**, l'un sous l'autre, dessinés environ
  2 × plus grands (feuilles du plan, planches de la dalle, récapitulatif chantier).
- **Éclaté** : écartement depuis le centre, pièces rattachées (couvre-joints, lisses, tasseaux) décollées de leur paroi,
  séparation des pièces encore proches ; dalle : coffrage des poutres descendu sous les poutrelles. Contrôle : aucune pièce
  à moins de 3 mm d'une autre sur les 36 scénarios.
- **Perçages des poteaux** dessinés en 3D dans la base et le fond supérieur (y compris en écorché).
- **Rendu 3D** : grain de bois sur CP et bois, plis du contreplaqué sur les chants, lumière d'appoint (dessous lisibles),
  quadrillage du sol (500 mm), transitions douces entre vues, mise en évidence au survol.

**Écarts voulus** : t_avap compare désormais les feuilles et les CP à découper sur l'ensemble des lignes de tableaux et des
textes des dessins (et non plus le balisage) ; 43 plans gagnent des étiquettes (dessins agrandis), 4 plans voient au plus
4 étiquettes courtes déplacées (repère d'une vue éclatée, numéros) ; débit, contrôles, CSV, DXF inchangés. t_gab_dalle :
lecteur des feuilles de planches adapté à 2 panneaux par feuille (cellule 640).

**Tests** : t_v29 (nouveau) 80 OK ; 20/20 suites OK (t_avap 1 010, t_coh 156, t_audit 1 635, t_gab_dalle 119 753).

**Non validé** : impression papier réelle (rendus PDF Chromium A3 et A4 contrôlés), navigateur autre que Chromium (la
règle `:has()` des colonnes demande Chrome 105+, Firefox 121+, Safari 15.4+), carte graphique réelle.

## v2.8 — vue 3D WebGL
**Demande** : 3D de niveau professionnel (choix : three.js).

**Fait**
- Vue 3D interactive rendue par la carte graphique (three.js r170, MIT, intégré au fichier, chargé à la première ouverture,
  hors connexion) : éclairage, ombres portées au sol, parois courbes lisses (normales radiales, sans hachures de facettes),
  arêtes vives seulement. Même modèle, même caméra, mêmes commandes (vues, éclaté, types, repères, clic, clavier, tactile).
- Étiquettes posées sur une partie visible (lancer de rayon), clic → pièce et repère.
- Légende et fiche de la pièce : nombre de **pièces** (une coque en facettes = 1 pièce) au lieu du nombre de facettes.
- Repères : chaque ligne CP du débit portée par une pièce 3D de mêmes cotes ; lignes sans pièce repérée passées de 92 à
  17 sur 155 plans (restent : planches découpées de la dalle, regroupées par panneau ; tronçons de parallélogramme).
- Sans WebGL : rendu vectoriel d'avant, mêmes fonctions. Feuilles imprimées et DXF : rendu vectoriel inchangé.

**Écarts voulus** (t_avap : 26 plans) : étiquettes de repères supplémentaires sur la feuille de montage.

**Tests** : t_v28 (nouveau) 15 OK ; 19/19 suites OK (t_avap 1 064, t_coh 156, t_audit 1 635).

**Non validé** : carte graphique réelle (tests sur rendu logiciel SwiftShader), tablette, performances sur un PC ancien.

## v2.7 — cohérence
**Demande** : avant commercialisation, améliorer la 3D, la cohérence des plans et les fonctions ; ordre retenu :
cohérence (v2.7), 3D three.js (v2.8), cotes et échelle réelles (v2.9), export 3D / BIM et gel bêta (v3.0).

**Fait**
- **Revue de cohérence croisée** (`tests/t_coh.py`, 155 plans : 36 scénarios + 10 plans aléatoires par forme) : chaque
  pièce du débit retrouvée dans les pièces à découper (aire), l'imbrication (aucune pièce non placée), le modèle 3D
  (volume de CP et de bois ± 1 %), le CSV et le DXF (repères).
- Écart trouvé et corrigé : **poches des poutres** dessinées en 3D comme un bloc plein alors que le débit compte un caisson
  CP (dessous, 2 côtés, fond) → caisson CP modélisé, repères J… au clic, volume 3D = débit.
- Écart trouvé, reporté en v2.8 : sur 37 plans sur 155, certains repères du débit ne sont portés par aucune pièce 3D
  (cloisons en tronçons, goussets, pièces de poche multiples, panneaux de platelage) ; liste dans `tests/out/coherence.json`.

**Écarts voulus** (t_avap : 13 plans, expliqués) : 3D des poutres et dalles avec poutres (poches), donc feuille de montage et vue 3D du DXF. Débit, plans, CSV inchangés.

**Tests** : t_coh 156 OK (nouveau, dans les suites rapides) ; 18/18 suites OK (t_avap 1 051, t_audit 1 635, t_gab_dalle 119 751).

## v2.6 — crédibilité
**Demandes** : étape « crédibilité » de la feuille de route — calcul de flèche du CP, note d'hypothèses, cartouche
d'entreprise, enregistrement dans un vrai fichier, noms de chantiers réels retirés. CP par défaut : filmé phénolique
classe 3 (EN 636-3), 18 mm.

**Fait**
- Catalogue CP par âme : **filmé bouleau** (défaut ; WISA-Form Birch, Riga Form, Metsä Form), filmé combi, filmé
  peuplier / eucalyptus, CTBX okoumé, cintrable. Rigidités publiées : Koskisen (bouleau, combi ; mêmes valeurs UPM
  WISA-Form Birch), FCBA POB 21.02 (okoumé humide). Pas de valeur retenue pour le peuplier / eucalyptus et le cintrable.
- **Flèche des joues** des boîtes rectangulaires (`flecheCP`, `plateW`) : plaque (Ritz) appuyée aux angles, aux cloisons CP
  pleine hauteur et au pied, bord haut libre, poussée hydrostatique ; module mini (sens du fil non garanti) ; × 1,5
  (EN 1995-1-1, contreplaqué en classe de service 3) ; cisaillement calé sur le tableau de charges Riga Form 03/2026
  (−6 % … +13 %). Critère portée / 300 (fabricants), réglable dans le profil chantier. Alerte ⚠ + correction
  automatique (cloisons CP, CP plus épais). Hypothèses et note : valeurs et sources.
- **Note d'hypothèses** (carte Plans) : synthèse chantier (plans, hypothèses générales, limites, sources, visas) + une
  feuille A4 portrait par plan (poussée, renfort le plus sollicité, flèche, hypothèses, contrôles restants).
- **Cartouche entreprise** (carte Impression) : nom, ligne libre, dessinateur, logo ; cases Vérifié / Visa et
  « Non à l'échelle — fabriquer aux cotes » sur toutes les feuilles de plan. Enregistré dans le navigateur et dans le
  fichier projet (clé `ent`, format v 10 inchangé ; les versions précédentes ignorent cette clé).
- **Enregistrement direct** (Chrome / Edge, File System Access) : Ctrl+S réécrit le fichier choisi ou ouvert ;
  Ctrl+Maj+S = enregistrer sous ; autres navigateurs : téléchargement comme avant.
- Exemple de nom de chantier réel remplacé par un nom fictif.

**Écarts voulus** (t_avap 148 plans : tous expliqués) : désignation « CP filmé bouleau » (feuilles, débit, CSV, DXF) ;
nouvelle alerte de flèche sur 35 plans du banc (boîtes sans cloisons ou hautes) ; bloc entreprise du cartouche.
t_regress : 3 scénarios documentés (2 alertes de flèche, 1 désignation). Bancs : enregistrement par téléchargement
forcé dans `lib.open_app`, t_ux et t_v23 (`NOFS`) ; t_ux attend la clé `ent` ; t_v25 : ligne « Flèche du CP » calculée.

**Tests** : t_v26 (nouveau) 34 OK ; 16 suites existantes OK (dont t_audit 1 635, t_gab_dalle 119 751).

**Non validé** : enregistrement direct dans un vrai Chrome / Edge (testé avec un faux fichier) ; flèche à confronter à
des mesures ou à un bureau d'études ; logo d'entreprise à l'impression papier.

## v2.5 — mise en page des feuilles
- Réglage « Mise en page des feuilles » : **Plan pleine page** (défaut, feuille 1 = vues seules + feuille 1b débit ·
  informations · hypothèses), **Compacte** (mise en page v2.4), **Vues uniquement**.
- Ligne d'hypothèses dans le cartouche ; case Hypothèses (`hypRows`) : valeur et origine de chaque hypothèse.
- Calculs, débit, gabarits, DXF, CSV, 3D inchangés (t_avap identique en compacte).

## v2.4 — passe complète
- Cartes repliables, accueil, série depuis un tableau, comparaison de deux indices, mode chantier tablette.
- Mannequin de voile : renfort minimal quand un côté est plus grand que l'autre. Axe des poteaux de la spéciale :
  200 mm par défaut.
- Feuilles annexes décochées et sommaire « Jamais » par défaut ; DXF lisible avec txt.shx (AutoCAD).
- Audit : code mort retiré, cache de géométrie de la goulotte, avertissement si le stockage est plein.
- Retouche : police + 2 pt dans les cases Débit et Informations.

## v2.3 — confort
- Plan modifié non mis à jour signalé, fenêtres de l'application à la place de celles du navigateur, liste des plans
  (recherche, regroupement, tri), aperçu non bloquant.

## v2.2 — identité CoffraPlan
- Logo, favicon, thème clair / sombre / auto, rappel de sauvegarde, alertes cliquables, raccourcis clavier.

## v2.1
- Messages sans incidence sur la fabrication retirés ; poteaux de la forme spéciale traversant base et fond supérieur ;
  revue des fonctions avancées.

## v2.0
- Gabarits 1:1 alignés sur les plans de découpe (dalle de couverture en priorité).

## v19
- Forme « Puisard avec fond » supprimée (doublon), anciens plans migrés ; campagne gabarits ↔ débit.

## v18
- Gabarits relatifs au repère ● du panneau, vue éclatée du voile cintré, bouton Exporter unique (DXF, CSV, XLSX, ZIP),
  renforts et poutres complétés.

## v17
- Gabarits 1 pièce = 1 page, poutres ≤ 7 m, auto-contrôle avec corrections, 3D interactive, DXF + dossier PDF,
  palette de couleurs actée.
