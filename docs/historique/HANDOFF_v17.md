# HANDOFF v17 — Plans de Réservation – Coffrage Bois

> À donner en premier message d'une nouvelle conversation. Date : 2026-10-10. Utilisateur : Kévin TRINH.

## 1. Profil & règles de collaboration (À RESPECTER)
- Kévin : conducteur de travaux BTP (France), apprend à coder avec l'IA. Veut des solutions **concrètes et testables**, du code fonctionnel.
- Réponses **en français**, directes, denses, expertes. Pas de flatterie ni de remplissage.
- Le corriger directement s'il se trompe. Distinguer **certain / probable / hypothèse**.
- Ne jamais présenter comme « vérifié » ce qui n'a pas été lu/testé. Sourcer les faits récents.
- Rester concis ; structure : contexte → analyse → conclusion → action.

## 2. Le projet
Application **HTML mono-fichier** (JS vanilla, sans dépendance) : plans de coffrage bois pour réservations, poutres, dalles, voiles, parallélépipèdes, etc.
Fonctions : débit CP/bois, imbrication (nesting) des panneaux, gabarits 1:1 imprimables, vue 3D interactive, auto-contrôle avec corrections automatiques, récapitulatif chantier, export DXF, dossier PDF.

## 3. État actuel : **v17 livrée et validée**
- Fichier : `v17_Plans_Reservation_Coffrage.html` (~501 Ko). Copie de travail : `/home/claude/v17_Plans_Reservation_Coffrage.html` (build : `/home/claude/v17.html`).
- Campagne de tests : **38/38 suites vertes, 690 contrôles OK**.

### Livré en v17
1. **Gabarits 1:1** : 1 plan de découpe entier = 1 page (mode « traceur »), jamais de collage/tuilage ; A4/A3 seulement si la pièce tient entièrement.
2. **Poutres ≤ 7 m** (BM_LMAX=7000) : parties égales, coupe à chaque poteau quel que soit le Ø (bug de séparation corrigé). Vaut pour forme poutre et poutres de dalle.
3. **Dalle/poutre** : tube carton s'arrête **sous** la poutre (plan + 3D) ; fermeture sur poteau (1 poteau → joues du coffrage gauche prolongées ; plusieurs → 1 travée sur 2).
4. **Auto-contrôle** : corrige automatiquement chaque point (lisibilité, textes superposés…). Moteur ACFIX : un correctif n'est accepté que si la famille d'erreur disparaît, le nombre d'erreurs de la même règle baisse et aucune nouvelle erreur n'apparaît. `fixAllPlans` avec annulation.
5. **3D interactive** (`extA.js`) : rotation, pan, zoom curseur, pinch, double-clic → iso, clavier, presets (Iso/Dessus/Face/Côté/Dessous), éclaté, cases par type, « Masquer CP », clic → info pièce.
6. **Export DXF** (R12, mm, calques PLAN_*, CP_*, GABARIT_*, VUES_*, CARTOUCHE) + **Dossier PDF** (couverture, sommaire avec pages, plans, récap, numérotation `p. i / N`).
7. **Auto-contrôle chantier** (`extC.js`) : 5 contrôles + bouton « 🔍 Auto-contrôle » dans la vue chantier.
8. **Nouvelle convention de couleurs** (palette C2 validée) + mode N&B (hachures).
9. **Parallélépipède** avec panneaux plus longs que le CP : tronçons, joints sur **cadres de joint 50×50** (2 traverses + 2 montants par joint), 4 lignes de débit séparées.

## 4. Architecture & build
- Sources : `/home/claude/src17/` → `base.html` + `ext1..ext9.js, extA.js, extB.js, extC.js` concaténés **par ordre alphabétique** par `python3 /home/claude/src17/build.py` → `/home/claude/v17.html`.
- Un seul `<script>` : les ext ultérieurs redéfinissent des fonctions via le pattern wrapper `{const _f=f;f=function(){…}}`.
- Fichiers clés : `ext2.js` (`nestPieces`, supporte `sh.poly`/`sh.cutsX`), `ext4.js` (moteur 3D, page montage), `extA.js` (3D interactive), `extB.js` (DXF + dossier), `extC.js` (auto-contrôle chantier).
- Modèle poutre `bmBuild` : travées entre bornes (voile, poteau d'extrémité, chaque poteau intermédiaire), pièces ≤ 7000, couronne CP quand r > b/2+eJ, cadre d'about bois + lisse de raccord, haut du tube = dessous du fond.
- Gabarits : `gabPieces/gabFit/gabHtml/openGab`, @page nommées, `overflow:visible` à l'impression.
- Lisibilité : `declutter(root)` (anti-chevauchement + lignes de rappel), `d.txt` (normal/compact/mini).
- 3D : `S3()` solides à rôles (base/wall/ring/top/in/ctx), `render3`, `cam3`, `PLAN3`, `camIso`, `explode3`, `retag3`. Pots/croix/goulotte en miroir pour correspondre au plan (y plan vers le bas, y modèle vers le haut).
- Migration : `migr()` ; `dlBmEmpty()`.

## 5. Tests
- Dossier `/home/claude/tests_v17/` ; les tests référencent `/home/claude/v14.html`, substitué par le chemin de l'app.
- Campagne complète : `cd /home/claude/tests_v17 && nohup python3 run_all.py /home/claude/v17.html > out.log 2>&1 &` (~10 min ; **lancer en arrière-plan et sonder**, les appels shell expirent à 2 min).
- Outils : Playwright Python (Chromium uniquement), shapely, ezdxf (`pip --break-system-packages`), pdfinfo/pdftoppm/pdftotext.
- Suites ajoutées en v17 : `lotF` (T27) … `lotL` (T33). `visual.py` : références PNG dans `tests_v17/ref_png`, rebaselinées sur v17.
- Si l'environnement est neuf : ces fichiers peuvent ne plus exister → demander à Kévin de rejoindre/réattacher l'HTML v17 et reconstruire les tests si besoin. **Le HTML v17 est la source de vérité** (il embarque tout le code).

## 6. Décisions de conception actées
- Palette : joues CP `#EBD9B4`, fond inf `#B4532A`, fond sup `#E8A92E`, goussets `#F26B1D`, cloisons/montants CP `#C98BA0`, bois `#6B4423`, tubes carton `#8E8A84`, poches `#D7263D`, PVC `#4F5358`, béton `#C4C4C4`. Identique 2D/3D/légende/fiche. Pas de vert/bleu hors définition.
- Gabarit : 1 pièce = 1 page (traceur).
- DXF : R12, mm, encodage CP-1252 + `\U+XXXX`.
- Cadre de joint 50×50 = **choix de conception** à valider par la pratique chantier.
- Poutre : parties égales ≤ 7 m.

## 7. À NE PAS FAIRE / REFUSER
- Ne pas réintroduire collage/tuilage des gabarits.
- Ne pas faire monter le tube carton jusqu'au haut de la poutre.
- Termes interdits : « poteaux béton », « flottaison », « fixation anti-flottaison ».
- Ne pas modifier un test pour le faire passer sans changement intentionnel documenté.
- Ne pas affirmer qu'un point est validé s'il n'a pas été testé (impression traceur, DXF en CAO, Firefox/Safari non testés).

## 8. Limites connues
- Seul Chromium testé. Impression traceur réelle non testée (simulée via PDF).
- DXF R12 sans champ d'unité : régler l'import en **mm**. Les vues du DXF ne sont pas à l'échelle.
- Tests modifiés volontairement : `lotB` (explosion dalle, platelage masqué), `lotC` (CARTON_F), `lot9` (declutter neutralisé dans la mutation), `visual` (refs).

## 9. Checklist de validation manuelle par Kévin (8 points)
1. Vue spéciale : orientation 3D = plan.
2. 3D sur mobile (gestes).
3. Dalle : platelage opaque / poutrelles.
4. DXF ouvert en CAO, unités mm.
5. Dossier PDF : numérotation des pages.
6. Traceur à 100 % : carré de contrôle de 100 mm.
7. Auto-contrôle chantier + DXF calepinage.
8. Parallélépipède 3000 / 40° : joints.

## 10. Pistes pour la suite (non demandées)
Tests Firefox/WebKit ; validation terrain du cadre de joint ; retours de la checklist ci-dessus ; export DXF avec échelle réelle des vues.
