# -*- coding: utf-8 -*-
"""Livrets « Leçons essentielles » v2 — 25 pages par licence, organisés PAR FILIÈRE.
Contenu de révision original, rédigé pour l'assistant étudiant IAM.
Calibration : socle de leçons + annexes (QCM corrigé, glossaire, sujets,
fiches de révision) + pages de notes lignées, ajustés pour 25 pages exactes."""
import os
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, PageBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
_FD = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DejaVuSans", os.path.join(_FD, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", os.path.join(_FD, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("DejaVuSans", normal="DejaVuSans", bold="DejaVuSans-Bold",
                              italic="DejaVuSans", boldItalic="DejaVuSans-Bold")


def esc(s):
    """Échappe le HTML littéral des exemples (ex. <img ...>) pour le parseur ReportLab."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


NAVY = HexColor("#0b2545")
GOLD = HexColor("#c9a227")
INK = HexColor("#1a1a1a")
MUT = HexColor("#5a6a7f")

S = {
    "title": ParagraphStyle("title", fontName="DejaVuSans-Bold", fontSize=22, leading=27, textColor=NAVY),
    "subtitle": ParagraphStyle("subtitle", fontName="DejaVuSans", fontSize=11.5, leading=15, textColor=MUT),
    "chap": ParagraphStyle("chap", fontName="DejaVuSans-Bold", fontSize=14.5, leading=18, textColor=white),
    "h": ParagraphStyle("h", fontName="DejaVuSans-Bold", fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=8, spaceAfter=3),
    "p": ParagraphStyle("p", fontName="DejaVuSans", fontSize=10.6, leading=14.6, textColor=INK, spaceAfter=5),
    "ex": ParagraphStyle("ex", fontName="DejaVuSans", fontSize=10.4, leading=14.2, textColor=HexColor("#123a6b")),
    "exo": ParagraphStyle("exo", fontName="DejaVuSans", fontSize=10.4, leading=14.2, textColor=HexColor("#5a3805")),
    "key": ParagraphStyle("key", fontName="DejaVuSans", fontSize=10.2, leading=13.8, textColor=HexColor("#4a3805")),
    "fiche": ParagraphStyle("fiche", fontName="DejaVuSans", fontSize=10.2, leading=13.8, textColor=INK, spaceAfter=4),
    "foot": ParagraphStyle("foot", fontName="DejaVuSans", fontSize=8.6, leading=11, textColor=MUT, alignment=TA_CENTER),
}
TARGET = 25


def header(level):
    return [Paragraph(f"Leçons essentielles — Licence {level}", S["title"]),
            Paragraph("Organisé par filière · Université IAM — Bamako", S["subtitle"]),
            Paragraph("Résumés de révision rédigés pour les étudiants — Assistant Étudiant IAM (projet n°11, atelier IAM Code to Career). "
                      "Chaque leçon : l'essentiel, un exemple, un mini-exercice et les points à retenir. "
                      "Ces livrets aident à réviser ; ils ne remplacent pas les cours officiels ni les documents des enseignants.", S["subtitle"]),
            Spacer(1, 4 * mm), HRFlowable(width="100%", thickness=1.4, color=GOLD), Spacer(1, 3 * mm)]


def chapter(title):
    t = Table([[Paragraph(esc(title.upper()), S["chap"])]], colWidths=[170 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LINEBELOW", (0, 0), (-1, -1), 2, GOLD)]))
    return [Spacer(1, 5 * mm), t, Spacer(1, 3 * mm)]


def boxed(text, style, bg):
    t = Table([[Paragraph(text, style)]], colWidths=[170 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def lesson(title, paras, exemple, exercice, keys):
    flow = [Paragraph(esc(title), S["h"])]
    for p in paras:
        flow.append(Paragraph(esc(p), S["p"]))
    if exemple:
        flow.append(boxed("<b>Exemple.</b> " + esc(exemple), S["ex"], HexColor("#eef2f8")))
        flow.append(Spacer(1, 2 * mm))
    if exercice:
        flow.append(Paragraph("<b>Mini-exercice.</b> " + esc(exercice), S["exo"]))
    if keys:
        items = "".join(f"• {esc(k)}<br/>" for k in keys)
        flow.append(boxed("<b>À retenir</b><br/>" + items, S["key"], HexColor("#f7ecd0")))
    flow.append(Spacer(1, 2.5 * mm))
    return flow


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DejaVuSans", 8.2)
    canvas.setFillColor(MUT)
    canvas.drawCentredString(A4[0] / 2, 12 * mm,
                             "Assistant Étudiant IAM — Douga dit Ibrahim Diarra (Bronbah Tech) · Page %d" % doc.page)
    canvas.restoreState()


def count_pages(path):
    return len(PdfReader(path).pages)


def build_booklet(level, chapters, out, annexes=None, loin=None):
    """Calibre le livret à TARGET pages : socle + annexes + fiches + pages de notes."""
    annexes = annexes or {}
    loin = loin or {}
    fiches = []
    for _c, lessons in chapters:
        for (title, _p, _e, _x, keys) in lessons:
            if keys:
                fiches.append((title, keys))
    tmp = out + ".tmp.pdf"

    def make(n_fiches, notes_lines):
        doc = SimpleDocTemplate(tmp, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                                topMargin=16 * mm, bottomMargin=16 * mm,
                                title=f"Leçons essentielles — Licence {level} (par filière, 25 pages)",
                                author="Assistant Étudiant IAM — Douga dit Ibrahim Diarra")
        flow = header(level)
        for chap_title, lessons in chapters:
            flow += chapter(chap_title)
            for (title, paras, exemple, exercice, keys) in lessons:
                p2 = list(paras)
                if title in loin:
                    p2.append(loin[title])
                flow += lesson(title, p2, exemple, exercice, keys)
        qcm = annexes.get("qcm") or []
        if qcm:
            flow += chapter("Annexe — QCM d'entraînement corrigé")
            flow.append(Paragraph("Réponds d'abord sans regarder la correction, puis vérifie : c'est ainsi qu'on retient.", S["p"]))
            for i, (q, opts, good, expl) in enumerate(qcm, 1):
                flow.append(Paragraph(f"<b>{i}. {esc(q)}</b>", S["p"]))
                flow.append(Paragraph(" &nbsp;&nbsp; ".join(f"{'ABC'[j]}) {esc(o)}" for j, o in enumerate(opts)), S["fiche"]))
                flow.append(Paragraph(f"Réponse : {'ABC'[good]} — {esc(expl)}", S["exo"]))
                flow.append(Spacer(1, 1.5 * mm))
        glo = annexes.get("glossaire") or []
        if glo:
            flow += chapter("Annexe — glossaire des termes clés")
            for (t, d) in glo:
                flow.append(Paragraph(f"<b>{esc(t)}</b> — {esc(d)}", S["fiche"]))
        suj = annexes.get("sujets") or []
        if suj:
            flow += chapter("Annexe — sujets d'entraînement")
            for (t, enonce, corr) in suj:
                flow.append(Paragraph(esc(t), S["h"]))
                flow.append(Paragraph(esc(enonce), S["p"]))
                if corr:
                    flow.append(Paragraph("<b>Éléments de correction.</b> " + esc(corr), S["exo"]))
                flow.append(Spacer(1, 2 * mm))
        if n_fiches:
            flow += chapter("Annexe — fiches de révision express")
            flow.append(Paragraph("Relis ces fiches la veille de l'examen : une fiche = une leçon résumée en quelques lignes.", S["p"]))
            for (title, keys) in fiches[:n_fiches]:
                flow.append(Paragraph(f"<b>{esc(title)}</b> — " + " · ".join(esc(k) for k in keys), S["fiche"]))
        if notes_lines:
            flow.append(PageBreak())
            flow += chapter("Mes notes")
            for _ in range(notes_lines):
                flow.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#c9d2e0"), spaceAfter=20))
        doc.build(flow, onFirstPage=footer, onLaterPages=footer)
        return count_pages(tmp)

    base = make(0, 0)
    if base > TARGET:
        raise SystemExit(f"L{level} : socle+annexes trop longs ({base} pages > {TARGET}).")
    chosen = None
    n_max = 0
    for n in range(len(fiches) + 1):
        p = make(n, 0)
        if p == TARGET:
            chosen = (n, 0)
            break
        if p > TARGET:
            break
        n_max = n
    if chosen is None:
        # recherche grossière par pas de 13 lignes, puis affinage ligne par ligne
        prev = 0
        lines = 0
        found = None
        while lines <= 760:
            lines += 13
            p = make(n_max, lines)
            if p == TARGET:
                found = lines
                break
            if p > TARGET:
                for cand in range(prev + 1, lines):
                    if make(n_max, cand) == TARGET:
                        found = cand
                        break
                break
            prev = lines
        if found is None:
            raise SystemExit(f"L{level} : calibration impossible (socle {base}).")
        chosen = (n_max, found)
    pages = make(*chosen)
    os.replace(tmp, out)
    print(f"L{level} : {pages} pages, {os.path.getsize(out)} octets, fiches={chosen[0]}, lignes_notes={chosen[1]}")


# ================= LICENCE 1 — PAR FILIÈRE =================
L1 = [
    ("Tronc commun", [
        ("1. Le système LMD et l'organisation de ton année", [
            "Le système LMD (Licence – Master – Doctorat) découpe ton parcours en semestres et en unités d'enseignement (UE). Chaque UE validée rapporte des crédits capitalisables : la Licence complète vaut 180 crédits. Une UE est acquise à partir de 10/20, souvent avec des compensations possibles entre matières d'une même UE selon le règlement de l'établissement.",
            "Concrètement, ton année réussit ou échoue dès les premières semaines : présence aux cours, travaux rendus à temps, révisions régulières. Tiens un tableau simple de tes UE, de tes notes et de tes crédits acquis pour voir ta progression d'un coup d'œil.",
        ], "Semestre 1 : 6 UE, 30 crédits. Si tu valides 5 UE sur 6, il te reste 25 crédits acquis et une UE à reprendre en session de rattrapage.",
            "Liste tes UE du semestre et le nombre de crédits de chacune. Total attendu : 30.",
            ["Licence = 6 semestres = 180 crédits.", "Une UE validée est acquise définitivement."]),
        ("2. Prendre des notes et réviser efficacement", [
            "Prendre des notes, ce n'est pas tout recopier : c'est écouter, comprendre, puis écrire l'essentiel avec tes propres mots, en notant les exemples du professeur et les points sur lesquels il insiste — ce sont souvent les sujets d'examen.",
            "La révision la plus rentable est courte et régulière : relire ses notes le soir même (10 minutes), faire des fiches par chapitre (définition + exemple + piège), puis s'entraîner sur d'anciens sujets en temps limité avant l'examen.",
        ], "Une bonne fiche tient sur une demi-page : le titre du chapitre, 3 idées clés, 1 exemple chiffré, 1 erreur fréquente à éviter.",
            "Transforme le dernier cours que tu as suivi en une fiche d'une demi-page.",
            ["Relire le jour même fixe la mémoire.", "Fiche = définition + exemple + piège."]),
        ("3. Statistique descriptive : moyenne, médiane, graphiques", [
            "La statistique descriptive résume un ensemble de données. La moyenne = somme des valeurs ÷ effectif. La médiane = la valeur du milieu quand les données sont triées. Le mode = la valeur la plus fréquente. L'étendue = maximum − minimum, elle mesure la dispersion de façon simple.",
            "Avec des coefficients, on calcule la moyenne pondérée : Σ(note × coefficient) ÷ Σ(coefficients). Les graphiques traduisent les chiffres en images : barres pour comparer, courbe pour une évolution, camembert pour des parts d'un tout.",
        ], "Notes 9, 12, 15, 12 → moyenne = 12 ; médiane = 12 ; mode = 12 ; étendue = 6.",
            "Calcule la moyenne pondérée de 12 (coef 2) et 15 (coef 3). Réponse attendue : 13,8.",
            ["Moyenne pondérée : les coefficients comptent.", "La médiane résiste mieux aux valeurs extrêmes."]),
        ("4. Logique et ensembles — les fondations", [
            "Un ensemble est une collection d'éléments distincts. Opérations de base : l'union (∪, tous les éléments), l'intersection (∩, les éléments communs) et le complémentaire (ce qui n'est pas dans l'ensemble). Les diagrammes de Venn dessinent ces opérations et évitent les erreurs de raisonnement.",
            "La logique étudie les propositions vraies ou fausses combinées par ET, OU, NON et l'implication (si… alors…). C'est exactement le langage des conditions en programmation : maîtriser la logique, c'est maîtriser les « si » de tous les langages.",
        ], "A = {1, 2, 3}, B = {3, 4} → A ∪ B = {1, 2, 3, 4} ; A ∩ B = {3}.",
            "Si A = étudiants en informatique et B = étudiants sportifs, que représente A ∩ B en une phrase ?",
            ["∩ = commun ; ∪ = total.", "Table de vérité : l'outil anti-erreur de la logique."]),
        ("5. Anglais technique — le vocabulaire de base", [
            "L'anglais est la langue de la documentation technique. Commence par le vocabulaire du quotidien numérique : computer (ordinateur), software (logiciel), hardware (matériel), network (réseau), file (fichier), folder (dossier), password (mot de passe), data (données), screen (écran), keyboard (clavier).",
            "Verbes utiles : to save (enregistrer), to download (télécharger), to upload (envoyer), to delete (supprimer), to search (chercher), to log in (se connecter). Méthode : 5 mots par jour, chacun utilisé dans une phrase — en 10 mois, tu dépasses 1 500 mots actifs.",
        ], "« Save your file before you close the software » = Enregistre ton fichier avant de fermer le logiciel.",
            "Traduis : « The password protects your data on the network ».",
            ["5 mots par jour valent mieux qu'un gros cours rare.", "Lire la doc en anglais devient vite un réflexe."]),
    ]),
    ("Filière Informatique", [
        ("6. Qu'est-ce qu'un algorithme ?", [
            "Un algorithme est une suite finie d'instructions précises, dans un ordre déterminé, qui transforme des données d'entrée en un résultat. C'est l'équivalent d'une recette : ingrédients (entrées), étapes (traitement), plat (sortie). Tout programme est un algorithme traduit dans un langage de programmation.",
            "On rédige d'abord l'algorithme en pseudo-code, avec trois briques : la séquence, la condition (si… alors… sinon…) et la boucle (répéter). Un bon algorithme est correct (il donne le bon résultat), fini (il s'arrête) et efficace (il ne fait pas de détours inutiles).",
        ], "Algorithme « thé » : faire bouillir l'eau → verser sur le thé → attendre 3 minutes → servir. Entrées : eau, thé ; sortie : thé prêt.",
            "Écris en pseudo-code l'algorithme qui décide si un étudiant est admis (note ≥ 10).",
            ["Entrées → traitement → sortie.", "Pseudo-code d'abord, code ensuite."]),
        ("7. Variables, types et affectation", [
            "Une variable associe un nom à une valeur stockée en mémoire. L'affectation (← ou =) range une valeur dans la variable. Les types fondamentaux : entier, réel, chaîne de caractères (texte), booléen (vrai/faux). Le type détermine les opérations possibles : on additionne des nombres, on concatène des textes.",
            "Des noms explicites (total_ventes plutôt que tv) rendent le programme lisible par les autres — et par toi dans trois mois. Une expression combine variables et opérateurs pour produire une nouvelle valeur.",
        ], "En Python : prix = 1500 ; quantite = 3 ; total = prix * quantite → total vaut 4500.",
            "Déclare une variable « ville » de type chaîne et une variable « age » de type entier, dans le langage de ton choix.",
            ["Variable = nom + valeur + type.", "Un bon nom vaut un commentaire."]),
        ("8. Conditions et boucles", [
            "La condition exécute un bloc seulement si un test est vrai : si note ≥ 10 alors « admis » sinon « recalé ». Les tests utilisent =, ≠, <, >, ≤, ≥ et se combinent avec ET, OU, NON.",
            "Les boucles répètent un bloc : « pour » quand le nombre de tours est connu (afficher la table de 7), « tant que » quand il dépend d'une condition (demander un mot de passe jusqu'à ce qu'il soit correct). Le piège classique est la boucle infinie : la condition d'arrêt doit toujours finir par arriver.",
        ], "Pour i de 1 à 3 : afficher i → affiche 1, 2, 3. La variable i fait avancer et arrêter la boucle.",
            "Écris une boucle qui affiche les nombres pairs de 2 à 10.",
            ["Vérifie toujours la condition d'arrêt.", "Pour = tours connus ; tant que = tours conditionnels."]),
        ("9. L'ordinateur : processeur, RAM, stockage", [
            "Le processeur (CPU) exécute les instructions et fait les calculs ; sa vitesse se mesure en GHz et il possède plusieurs cœurs pour travailler en parallèle. La RAM (mémoire vive) contient le travail en cours : rapide, mais elle se vide quand l'appareil s'éteint.",
            "Le stockage (disque dur ou SSD) conserve durablement fichiers et programmes, même éteint. Retenir la différence RAM/stockage évite la confusion la plus fréquente des débutants : « plus de RAM » ne veut pas dire « plus de place pour mes photos ».",
        ], "Un PC avec 8 Go de RAM et 256 Go de SSD : 8 Go pour travailler maintenant, 256 Go pour conserver.",
            "Classe du plus rapide au plus durable : RAM, SSD, disque dur externe. Justifie en une phrase chacun.",
            ["RAM = temporaire et rapide.", "Stockage = durable, SSD plus rapide que disque dur."]),
        ("10. Le système d'exploitation et les fichiers", [
            "Le système d'exploitation (Windows, Linux, Android, iOS) est le logiciel de base : il démarre la machine, lance les applications, gère la mémoire, les périphériques et les fichiers. Sans lui, aucun programme ne peut fonctionner.",
            "Les fichiers sont rangés dans des dossiers en arborescence. L'extension indique le type : .docx (texte), .xlsx (tableur), .pdf (document figé), .jpg (image), .mp3 (audio). Organiser ses dossiers dès la L1 (par semestre et par matière) fait gagner un temps énorme en L3.",
        ], "Arborescence saine : Études / L1 / Semestre 1 / Algorithmique / TD2.pdf.",
            "Crée sur papier l'arborescence de tes dossiers pour ce semestre.",
            ["L'OS fait le lien matériel ↔ applications.", "Une info bien rangée se retrouve en 10 secondes."]),
        ("11. Le Web : navigateur, moteur de recherche, et un premier regard sur HTML", [
            "Le navigateur (Chrome, Firefox, Edge) affiche les pages web ; le moteur de recherche (Google, Bing) aide à les trouver. Ne confonds pas les deux : le navigateur est la fenêtre, le moteur est l'annuaire. Une page web est construite en HTML : des balises qui structurent le contenu (titres, paragraphes, images, liens).",
            "Exemple de balise : <h1>Titre</h1> affiche un grand titre, <p>texte</p> un paragraphe, <a href=\"...\">lien</a> un lien cliquable. Tu approfondiras HTML en L2, mais comprendre dès maintenant que chaque page est un document structuré change ton regard sur le Web.",
        ], "Dans le code d'une page, <img src=\"photo.jpg\"> insère une image ; le texte entre balises devient le contenu visible.",
            "Écris le HTML minimal d'une page avec un titre « Ma première page » et un paragraphe de présentation.",
            ["Navigateur ≠ moteur de recherche.", "HTML = la structure de chaque page web."]),
        ("12. Tableur et traitement de texte — les outils du quotidien", [
            "Le traitement de texte (Word, LibreOffice Writer) sert à rédiger des documents structurés : titres hiérarchisés, listes, tableaux, sommaire automatique. Le tableur (Excel, Sheets) organise des données en lignes/colonnes et calcule automatiquement grâce aux formules.",
            "Formules de base du tableur : =SOMME(A1:A10) additionne, =MOYENNE(...) calcule la moyenne, =MAX/MIN donnent les extrêmes. Ces deux outils servent dans toutes les filières : notes, budgets, rapports, inventaires.",
        ], "Dans un tableur, si B2 contient 12 et B3 contient 15, =MOYENNE(B2:B3) affiche 13,5 sans calculatrice.",
            "Écris la formule qui additionne les cellules C1 à C20, puis celle qui en calcule la moyenne.",
            ["Une formule commence toujours par =.", "Styles de titres = sommaire automatique en un clic."]),
    ]),
    ("Filière Gestion — BBA (Administration des affaires)", [
        ("13. Introduction à l'économie : offre, demande, prix", [
            "L'économie étudie les choix face à des ressources limitées. Sur un marché, l'offre (quantités proposées par les vendeurs) et la demande (quantités souhaitées par les acheteurs) se rencontrent : le prix d'équilibre est celui où les deux s'accordent.",
            "Si la demande augmente à offre égale, les prix montent ; si l'offre augmente à demande égale, ils baissent. La microéconomie étudie ces comportements individuels ; la macroéconomie regarde le pays entier : croissance, chômage, inflation.",
        ], "En saison sèche, moins de mangues sur le marché (offre ↓) et autant d'acheteurs → le prix du kilo augmente.",
            "Explique en deux phrases ce qui arrive au prix des parapluies quand la saison des pluies commence.",
            ["Prix = rencontre de l'offre et de la demande.", "Rareté ⇒ choix ⇒ économie."]),
        ("14. L'entreprise : formes, fonctions, environnement", [
            "Une entreprise organise des ressources (humaines, matérielles, financières) pour produire des biens ou des services et les vendre. Ses grandes fonctions : produire, vendre (commercial/marketing), gérer l'argent (finance/comptabilité), gérer les personnes (RH) et s'approvisionner (achats/logistique).",
            "Son environnement comprend les clients, les concurrents, les fournisseurs, l'État et la société. Comprendre son environnement, c'est anticiper les opportunités et les menaces plutôt que les subir.",
        ], "Une boulangerie : production (le fournil), commercial (la boutique), finance (la caisse et les crédits fournisseurs), RH (les boulangers), achats (farine, levure).",
            "Pour une boutique de téléphones à Bamako, cite un acteur de chacune des cinq fonctions.",
            ["5 fonctions : produire, vendre, financer, recruter, approvisionner.", "L'environnement influence chaque décision."]),
        ("15. Découverte du management", [
            "Manager, c'est prévoir, organiser, commander/coordonner et contrôler (les fonctions classiques de Fayol). À ton niveau, retiens le cycle simple : fixer un objectif clair, organiser les moyens, suivre l'avancement, corriger ce qui dérive.",
            "Le management n'est pas réservé aux entreprises : gérer un projet d'équipe à l'université suit exactement le même cycle — objectif écrit, tâches réparties, points réguliers, bilan final.",
        ], "Projet de classe : objectif « présenter dans 10 jours », tâches réparties le jour 1, point d'avancement le jour 5, répétition le jour 9.",
            "Applique le cycle en 4 étapes à l'organisation d'un exposé de groupe.",
            ["Prévoir, organiser, coordonner, contrôler.", "Un objectif non écrit n'existe pas."]),
    ]),
    ("Filière Droit", [
        ("16. Introduction au droit : règles, sources, branches", [
            "Le droit est l'ensemble des règles qui organisent la vie en société et dont le respect est assuré par l'État. Ses sources principales : la Constitution, les lois, les règlements, la jurisprudence (décisions des tribunaux) et la coutume.",
            "Grandes branches : le droit public (rapports avec l'État : constitutionnel, administratif, pénal) et le droit privé (rapports entre personnes : civil, commercial, du travail). Identifier la branche d'un problème est la première étape de tout raisonnement juridique.",
        ], "Un litige entre un client et un commerçant relève du droit privé (commercial/civil) ; une amende de circulation relève du droit public (pénal/administratif).",
            "Classe ces situations : vol dans une boutique ; divorce ; permis de construire refusé.",
            ["Droit public = avec l'État ; droit privé = entre personnes.", "La hiérarchie des normes : Constitution au sommet."]),
        ("17. Le contrat : formation et effets (notions)", [
            "Un contrat est un accord de volontés qui crée des obligations. Pour être valable, il faut en principe : un consentement libre et éclairé, la capacité juridique des parties, un objet licite et déterminé, et une cause licite.",
            "Un contrat valablement formé tient lieu de loi entre les parties : chacune doit exécuter ce qu'elle a promis, de bonne foi. D'où l'importance d'écrire clairement qui fait quoi, pour quel prix et quels délais — la plupart des litiges naissent d'accords flous.",
        ], "Louer une salle pour un mariage avec un contrat écrit (date, prix, prestations) protège les deux parties ; un accord oral « on verra » n'en protège aucune.",
            "Cite les 4 conditions de validité d'un contrat et donne un contre-exemple pour chacune.",
            ["Consentement, capacité, objet, cause.", "Un contrat clair évite un procès."]),
    ]),
    ("Filière Comptabilité & Finance", [
        ("18. La partie double : débit et crédit", [
            "La comptabilité enregistre chaque opération avec une ressource et un emploi : c'est le principe de la partie double. Chaque écriture comporte un débit et un crédit de même montant, donc les totaux débit et crédit sont toujours égaux.",
            "Règle de lecture : un compte d'actif ou de charge augmente au débit ; un compte de passif ou de produit augmente au crédit. Acheter du matériel en espèces : débit « matériel », crédit « caisse » — l'argent change de poche, le total reste équilibré.",
        ], "Vente de marchandises pour 50 000 FCFA en espèces : débit Caisse 50 000, crédit Ventes 50 000.",
            "Enregistre (débit/crédit) : achat de fournitures 20 000 FCFA à crédit chez un fournisseur.",
            ["Total débit = total crédit, toujours.", "Chaque opération a une source et une destination."]),
        ("19. Bilan et compte de résultat : la photo et le film", [
            "Le bilan est la photographie du patrimoine à une date donnée : à l'actif ce que l'entreprise possède (matériel, stocks, créances, caisse), au passif ce qu'elle doit et ses capitaux propres. Actif = Passif, toujours.",
            "Le compte de résultat est le film de la période : produits (ventes) − charges (achats, salaires, loyers) = bénéfice ou perte. Confondre bilan et résultat est l'erreur classique du débutant : l'un est un stock, l'autre un flux.",
        ], "Une boutique possède 800 000 FCFA de stock et 200 000 en caisse (actif 1 000 000) ; elle doit 300 000 à ses fournisseurs → ses capitaux propres valent 700 000.",
            "Une entreprise vend pour 500 000 et dépense 420 000 en charges : bénéfice ou perte ? De combien ?",
            ["Bilan = stock à une date ; résultat = flux sur une période.", "Produits − charges = résultat."]),
    ]),
    ("Filières Marketing, RH et Logistique (découverte)", [
        ("20. Marketing : besoin, produit, les 4P", [
            "Le marketing part du besoin du client, pas du produit : comprendre qui achètera, quel problème on résout, à quel prix. Le mix marketing (4P) résume les leviers : Produit, Prix, Place (distribution), Promotion (communication).",
            "Un produit excellent sans distribution ni communication ne se vend pas ; un produit moyen bien ciblé et bien expliqué peut réussir. Le marketing commence donc par écouter le marché.",
        ], "Un jus de fruits local : Produit (jus de mangue frais), Prix (500 FCFA), Place (boutiques de quartier), Promotion (dégustation + statut WhatsApp).",
            "Construis les 4P pour un service de dépannage informatique à domicile.",
            ["On vend une solution à un besoin, pas un objet.", "4P : Produit, Prix, Place, Promotion."]),
        ("21. Ressources humaines et chaîne logistique : les notions", [
            "La fonction RH gère le parcours des personnes : recruter, intégrer, former, évaluer, rémunérer. Même une petite entreprise fait de la RH dès qu'elle embauche : définir le poste, choisir la bonne personne, la former et la motiver.",
            "La logistique organise les flux : approvisionner, stocker, transporter, livrer au bon endroit, au bon moment, au moindre coût. Un stock trop plein immobilise l'argent ; un stock vide perd des ventes — toute la logistique est un équilibre.",
        ], "Un magasin qui commande trop de téléphones bloque sa trésorerie ; celui qui en commande trop peu renvoie ses clients chez le concurrent.",
            "Pour une librairie, décris le flux logistique d'un livre, du fournisseur à l'étudiant.",
            ["RH = les bonnes personnes, formées et motivées.", "Logistique = le bon produit, au bon endroit, au bon moment."]),
    ]),
]


# ================= LICENCE 2 — PAR FILIÈRE =================
L2 = [
    ("Tronc commun", [
        ("1. Probabilités : l'essentiel pour la L2", [
            "La probabilité mesure la chance d'un événement entre 0 (impossible) et 1 (certain). Pour des cas équiprobables : P = nombre de cas favorables ÷ nombre de cas possibles. Deux règles à maîtriser : P(contraire) = 1 − P(événement) ; pour deux événements indépendants qui doivent arriver ensemble, on multiplie leurs probabilités.",
            "Attention au piège : des événements ne sont indépendants que si l'un n'influence pas l'autre. Tirer deux cartes sans remettre la première dans le paquet crée une dépendance — la deuxième probabilité change.",
        ], "Obtenir un nombre pair avec un dé : cas favorables 3 (2, 4, 6) sur 6 → P = 1/2 = 50 %.",
            "Un sac contient 4 billes rouges et 6 noires. Probabilité de tirer une rouge ? De ne pas tirer une rouge ?",
            ["P(contraire) = 1 − P.", "Indépendance : à vérifier, jamais à supposer."]),
        ("2. Réussir un exposé et une soutenance orale", [
            "Un exposé réussi repose sur un plan clair (introduction, 2-3 parties équilibrées, conclusion), des diapositives simples (une idée par diapositive, peu de texte, gros caractères) et une présentation entraînée à voix haute en se chronométrant.",
            "Le jour J : regarde le jury, parle lentement, appuie-toi sur des exemples concrets. Pour les questions : écoute jusqu'au bout, reformule si besoin, et réponds avec ce que tu sais — un raisonnement honnête vaut mieux qu'une invention.",
        ], "Diapositive efficace : un titre qui dit l'idée (« Les ventes ont doublé en mars ») + un graphique. Inefficace : 12 lignes de texte lues à voix haute.",
            "Prépare le plan (titres seulement) d'un exposé de 10 minutes sur « les réseaux sociaux et les petits commerces ».",
            ["Une idée par diapositive.", "S'entraîner à voix haute, chronométré."]),
        ("3. Anglais professionnel : se présenter et écrire un e-mail", [
            "Présentation type : « My name is …, I am a second-year computer science student at IAM University in Bamako. I am interested in web development and artificial intelligence. » Apprends ta présentation par cœur : c'est la première impression de chaque entretien.",
            "E-mail professionnel : objet clair (Subject: Application for an internship), salutation (Dear Sir or Madam,), phrases courtes, formule finale (Yours faithfully / Best regards). Un e-mail propre en anglais ouvre des portes : bourses, stages, programmes internationaux.",
        ], "Objet raté : « Hello » ; objet réussi : « Subject: Internship application — Computer Science student (IAM) ».",
            "Écris 4 lignes d'e-mail pour demander un stage d'été dans une entreprise informatique.",
            ["Subject précis = e-mail lu.", "Phrases courtes, politesse simple, zéro faute sur ton nom et tes coordonnées."]),
    ]),
    ("Filière Informatique", [
        ("4. Python : fonctions, listes, dictionnaires", [
            "Une fonction regroupe un traitement réutilisable avec des paramètres et un retour : def moyenne(notes): return sum(notes)/len(notes). Découper un problème en petites fonctions testables est LA compétence centrale de la L2.",
            "Les listes sont des collections ordonnées (index à partir de 0, append pour ajouter, boucle for pour parcourir). Les dictionnaires associent clés et valeurs — parfait pour une fiche étudiant : {\"nom\": \"Awa\", \"note\": 15}. Combine les deux et tu représentes presque toutes les données réelles.",
        ], "notes = [12, 14, 9, 15] ; moyenne(notes) renvoie 12.5. Un dictionnaire par étudiant, une liste de dictionnaires pour la classe.",
            "Écris une fonction qui reçoit une liste de prix et renvoie le total après une remise de 10 %.",
            ["Fonction = entrée → traitement → retour.", "Liste = ordonné ; dictionnaire = clé → valeur."]),
        ("5. Programmation orientée objet : classes et objets", [
            "La POO modélise le problème avec des objets : une classe définit le moule (attributs + méthodes), un objet est un exemplaire fabriqué à partir du moule. La classe Etudiant (nom, matricule, notes) produit des objets etudiant1, etudiant2, chacun avec ses propres données.",
            "Trois piliers : l'encapsulation (les données sont protégées, on passe par des méthodes), l'héritage (une classe spécialise une autre : EtudiantBoursier hérite d'Etudiant), le polymorphisme (une même méthode se comporte différemment selon l'objet). La POO devient indispensable quand les programmes grandissent.",
        ], "Classe Compte (titulaire, solde) avec méthodes deposer() et retirer() : chaque client a son objet Compte, le code bancaire est écrit une seule fois.",
            "Modélise une classe Produit pour une boutique : cite 3 attributs et 2 méthodes.",
            ["Classe = moule ; objet = exemplaire.", "Encapsulation, héritage, polymorphisme."]),
        ("6. HTML et CSS : construire une page propre", [
            "HTML structure le contenu avec des balises sémantiques : header, nav, main, section, footer pour l'ossature ; h1-h6, p, a, img, ul pour le contenu ; form, input, button pour les formulaires. Un HTML sémantique est mieux compris par les navigateurs, les moteurs de recherche et les lecteurs d'écran.",
            "CSS met en forme : sélecteurs (élément, .classe, #id), propriétés (color, font-size, margin, padding, display). Le modèle de boîte (contenu → padding → bordure → margin) explique 90 % des problèmes d'espacement des débutants. Le responsive design adapte la page aux téléphones via les media queries.",
        ], "<button class=\"btn\">Commander</button> avec .btn { background: #c9a227; padding: 10px 16px; border-radius: 8px; } donne un bouton doré arrondi.",
            "Écris le HTML d'un formulaire simple (nom, téléphone, bouton Envoyer) et le CSS qui centre le formulaire.",
            ["HTML sémantique d'abord, CSS ensuite.", "Modèle de boîte : contenu, padding, bordure, margin."]),
        ("7. JavaScript : rendre la page interactive", [
            "JavaScript réagit aux événements (clic, saisie, envoi de formulaire), lit et modifie le contenu de la page (le DOM) et fait des calculs côté visiteur. C'est lui qui vérifie un formulaire avant l'envoi ou qui affiche un panier qui se met à jour sans recharger la page.",
            "Briques essentielles : variables (let/const), conditions, boucles, fonctions, tableaux, objets, et l'écoute d'événements avec addEventListener. Avec fetch, JavaScript échange aussi des données avec un serveur — la base des applications web modernes.",
        ], "bouton.addEventListener('click', () => { compteur++; affichage.textContent = compteur; }) — chaque clic incrémente un compteur affiché.",
            "Écris en JavaScript une fonction qui reçoit un prix et affiche « Cher » s'il dépasse 50 000, sinon « Abordable ».",
            ["Événement → fonction → modification du DOM.", "const pour ce qui ne change pas, let sinon."]),
        ("8. PHP et SQL : le site dynamique complet", [
            "PHP s'exécute côté serveur : il reçoit les données des formulaires ($_GET, $_POST), interroge la base et génère le HTML de réponse. SQL manipule les données : SELECT pour lire, INSERT pour ajouter, UPDATE pour modifier, DELETE pour supprimer.",
            "Exemple complet : un formulaire d'inscription envoie nom et téléphone → PHP vérifie les champs → INSERT INTO etudiants (nom, telephone) VALUES (?, ?) avec une requête préparée → page de confirmation. La requête préparée est non négociable : elle bloque les injections SQL, l'attaque la plus classique contre les sites débutants.",
        ], "SELECT nom, note FROM etudiants WHERE note >= 10 ORDER BY note DESC ; → la liste des admis, du meilleur au moins bon.",
            "Écris la requête SQL qui compte le nombre d'étudiants d'une table etudiants, puis celle qui supprime l'étudiant d'id 7.",
            ["Toujours des requêtes préparées.", "Vérifier les données reçues avant de les enregistrer."]),
        ("9. Bases de données : modèle relationnel, clés, jointures", [
            "Une base relationnelle range les données en tables sans doublons : une information vit à un seul endroit. La clé primaire identifie chaque ligne de façon unique ; la clé étrangère relie les tables (une commande référence le client qui l'a passée).",
            "La jointure (JOIN) recompose l'information éclatée dans plusieurs tables : commandes JOIN clients ON commandes.client_id = clients.id donne la liste des commandes avec le nom de chaque client. Bien modéliser (normalisation) évite les incohérences quand les données changent.",
        ], "Sans clé étrangère, changer le nom d'un client obligerait à corriger chaque commande une par une ; avec la relation, on corrige une seule ligne.",
            "Pour une bibliothèque : propose 3 tables, leurs colonnes principales et les liens entre elles.",
            ["Clé primaire = identité ; clé étrangère = lien.", "Une info, une place : zéro doublon."]),
        ("10. Réseaux : IP, DNS, DHCP, HTTP/HTTPS", [
            "Chaque appareil d'un réseau a une adresse IP unique. Le LAN relie un même lieu (routeur/switch) ; Internet relie les réseaux du monde entier. Le routeur fait la frontière entre ton réseau local et Internet.",
            "Trois services à connaître : le DNS traduit les noms en adresses IP (groupeiam.com → son adresse), le DHCP distribue automatiquement les adresses aux appareils, et HTTP/HTTPS transporte les pages web — HTTPS chiffre l'échange, indispensable dès qu'il y a mots de passe ou paiements.",
        ], "Quand tu tapes un nom de site, ton navigateur demande d'abord au DNS « quelle est l'adresse ? », puis se connecte en HTTPS à cette adresse.",
            "Explique, dans l'ordre, ce qui se passe entre le moment où tu tapes une adresse web et l'affichage de la page.",
            ["DNS = annuaire ; DHCP = distribution automatique.", "HTTPS = HTTP + chiffrement."]),
        ("11. Système d'exploitation et ligne de commande", [
            "L'OS exécute les programmes sous forme de processus, partage le processeur entre eux et alloue la mémoire. Il organise le stockage en arborescence et contrôle les droits (lire, écrire, exécuter) pour chaque utilisateur — la première ligne de sécurité d'une machine.",
            "La ligne de commande Linux est un outil professionnel : ls (lister), cd (naviguer), pwd (où suis-je), mkdir (créer), cp/mv (copier/déplacer), rm (supprimer, prudence !), grep (rechercher dans les fichiers). Ces commandes servent sur les serveurs du monde entier.",
        ], "grep \"erreur\" journal.txt affiche toutes les lignes contenant « erreur » — en une seconde, là où l'œil mettrait dix minutes.",
            "Écris la suite de commandes pour créer un dossier « projet », y entrer, et lister son contenu.",
            ["Processus = programme en cours d'exécution.", "rm ne connaît pas la corbeille : vérifier avant d'effacer."]),
        ("12. Sécurité du quotidien : mots de passe et phishing", [
            "Un mot de passe fort est long (12 caractères et plus), unique par compte, et mélange lettres, chiffres et symboles — une phrase de passe comme « Bamako-soleil-2026! » est à la fois solide et mémorisable. Ajoute la double authentification partout où elle existe.",
            "Le phishing imite un service connu par message ou faux site pour voler identifiants et argent. Réflexes : vérifier l'expéditeur et l'adresse du site, se méfier de l'urgence fabriquée (« votre compte sera fermé »), et ne jamais donner ses codes : aucun service sérieux ne les demande par message.",
        ], "Message suspect : « Orange Money : votre compte est bloqué, envoyez votre code PIN pour le débloquer » — un opérateur ne demandera jamais un code PIN.",
            "Analyse un message que tu as reçu récemment : quels signes permettent de dire s'il est légitime ou frauduleux ?",
            ["Long, unique, mélangé + double authentification.", "L'urgence fabriquée est le signe n°1 de l'arnaque."]),
    ]),
    ("Filière Gestion — BBA", [
        ("13. Gestion de projet : rôles, tâches, livrables", [
            "Un projet se pilote avec quatre outils simples : un objectif écrit en une phrase, un découpage en tâches (qui fait quoi, pour quand), des points d'avancement courts, et des livrables vérifiables (une démo qui marche vaut mieux qu'un rapport qui promet).",
            "Les rôles doivent être explicites dès le départ : chef de projet (coordonne), développeurs/réalisateurs, testeur, présentateur. Les projets d'équipe échouent rarement sur la technique ; ils échouent sur les rôles flous et les tâches découvertes la veille.",
        ], "Tableau de bord minimal : tâche | responsable | date | état (à faire / en cours / fait). Mis à jour à chaque réunion de 15 minutes.",
            "Découpe le projet « site web pour une boulangerie » en 8 tâches avec responsables fictifs et dates.",
            ["Objectif écrit, tâches datées, rôles nommés.", "Une démo testée avant le jour J, jamais la veille."]),
        ("14. Entrepreneuriat et business plan", [
            "Entreprendre, c'est transformer une idée en activité qui trouve des clients. L'ordre qui marche : identifier un problème réel, vérifier que des gens paieraient pour la solution (en leur parlant, pas en imaginant), construire une offre simple, puis vendre et ajuster.",
            "Le business plan formalise tout cela : l'offre, le marché, la concurrence, l'organisation et les prévisions financières (coûts, prix, marge, seuil de rentabilité). Il sert d'abord à clarifier ta propre pensée, ensuite à convaincre partenaires et financeurs.",
        ], "Seuil de rentabilité simple : si tes charges fixes sont de 200 000 FCFA/mois et ta marge de 2 000 FCFA par produit, il faut vendre 100 produits par mois pour ne pas perdre d'argent.",
            "Pour un service de réparation de téléphones, liste 5 charges fixes et 3 charges variables.",
            ["Parler aux clients avant de construire.", "Marge × quantité doit couvrir les charges fixes."]),
        ("15. Trésorerie : suivre l'argent qui entre et sort", [
            "La trésorerie est l'argent disponible immédiatement. Une activité peut être rentable sur le papier et mourir d'un trou de trésorerie : si les clients paient à 30 jours et les fournisseurs tout de suite, la caisse se vide avant les rentrées.",
            "L'outil de pilotage est un tableau de suivi hebdomadaire : date, libellé, entrée, sortie, solde. Le même réflexe s'applique à ton budget d'étudiant : loyer, transport, nourriture, documents — ce qui se suit ne dérape pas en silence.",
        ], "Solde lundi : 80 000. Entrées de la semaine : +120 000. Sorties : −150 000. Solde vendredi : 50 000 — positif, mais la tendance alerte avant le découvert.",
            "Construis ton tableau de trésorerie personnelle pour le mois prochain (4 semaines, entrées et sorties prévues).",
            ["Rentabilité ≠ trésorerie.", "Un suivi hebdomadaire évite les mauvaises surprises."]),
    ]),
    ("Filières Droit, Comptabilité, Marketing, RH, Logistique", [
        ("16. Droit des affaires : l'entreprise et le RCCM", [
            "Créer une entreprise, c'est choisir une forme juridique (entreprise individuelle, SARL, SA…) selon le nombre d'associés, les risques et les ambitions. L'immatriculation au RCCM (Registre du Commerce et du Crédit Mobilier) officialise l'existence de l'activité.",
            "Ce statut officiel change concrètement la vie de l'entreprise : ouvrir des comptes professionnels, répondre à des appels d'offres, passer les vérifications des plateformes (publicité, paiements) et inspirer confiance aux partenaires.",
        ], "Un vendeur en ligne sans RCCM reste bloqué à certaines vérifications d'entreprise ; avec le RCCM, ses dossiers passent.",
            "Compare entreprise individuelle et SARL en 3 critères : création, responsabilité, image auprès des partenaires.",
            ["La forme juridique se choisit selon le risque et l'ambition.", "RCCM = porte d'entrée de la vie officielle."]),
        ("17. Comptabilité : lire un bilan et repérer l'essentiel", [
            "Lire un bilan, c'est répondre à trois questions : que possède l'entreprise (actif), que doit-elle (dettes), que vaut la part des propriétaires (capitaux propres) ? Le fonds de roulement (ressources stables − immobilisations) indique si l'activité de long terme est financée sainement.",
            "Deux ratios simples pour débuter : la liquidité (l'entreprise peut-elle payer ses dettes courtes ?) et l'endettement (dettes ÷ capitaux propres : trop élevé = fragile). On ne juge jamais sur un seul ratio, mais sur leur évolution.",
        ], "Actif : stock 600 000 + caisse 100 000 = 700 000. Dettes fournisseurs : 250 000. Capitaux propres = 450 000. Endettement = 250/450 ≈ 0,56 — modéré.",
            "Une entreprise a 900 000 d'actif et 600 000 de dettes : calcule ses capitaux propres et son ratio d'endettement.",
            ["Capitaux propres = actif − dettes.", "Un ratio se lit en tendance, pas isolément."]),
        ("18. Marketing digital : contenu, régularité, mesure", [
            "Le marketing digital d'un petit commerce repose sur trois piliers : une présence claire (page propre, coordonnées visibles, WhatsApp réactif), du contenu régulier qui aide ou divertit, et la mesure (vues, messages reçus, ventes) pour garder ce qui marche.",
            "Le parcours client : découvrir → s'intéresser → faire confiance → acheter → recommander. Chaque publication doit faire avancer le client d'une étape : une astuce crée la confiance, un témoignage rassure, une offre claire déclenche le message.",
        ], "Une astuce gratuite publiée chaque jour à heure fixe crée un rendez-vous ; une promotion publiée au hasard se perd dans le flux.",
            "Rédige le calendrier de contenu d'une semaine pour une boutique de vêtements (7 idées de publications).",
            ["Régularité > budget, au démarrage.", "Chaque contenu a un objectif dans le parcours client."]),
        ("19. RH et logistique : recruter juste, stocker juste", [
            "En RH, tout commence par la fiche de poste : missions, compétences, conditions. Un recrutement réussi = un poste clair + une sélection sur les compétences réelles (tests pratiques) + une intégration accompagnée les premières semaines.",
            "En logistique, la gestion des stocks équilibre deux coûts : stocker trop (argent immobilisé, invendus) et stocker trop peu (ruptures, clients perdus). Le stock minimum et le point de commande sont les deux repères qui évitent les ruptures surprises.",
        ], "Point de commande : si tu vends 5 pièces par jour et que le fournisseur livre en 4 jours, commande quand il reste 20 pièces (5 × 4), plus une petite marge de sécurité.",
            "Un commerce vend 8 articles/jour, livraison en 3 jours, marge de sécurité 6 : calcule son point de commande.",
            ["Fiche de poste claire = recrutement réussi à moitié.", "Point de commande = ventes/jour × délai + sécurité."]),
    ]),
]


# ================= LICENCE 3 — PAR FILIÈRE =================
L3 = [
    ("Tronc commun", [
        ("1. Méthodologie du mémoire : problématique et plan", [
            "Le mémoire répond à une problématique : une question précise, ni trop large (« l'informatique au Mali ») ni trop fermée, à laquelle ton travail apporte une réponse argumentée. Tout découle d'elle : le plan, les lectures, le terrain et la conclusion.",
            "Architecture classique : introduction (contexte, problématique, hypothèses, annonce du plan), partie théorique (concepts et travaux existants), partie pratique (terrain, données, analyse), conclusion (réponse à la problématique, limites, ouvertures). Le planning qui marche : sujet et plan détaillé dès le premier mois, rédaction régulière par petits blocs, relecture croisée, entraînement oral.",
        ], "Problématique faible : « Parler des réseaux sociaux ». Problématique solide : « Comment les petits commerces de Bamako utilisent-ils WhatsApp pour fidéliser leurs clients, et avec quels résultats mesurables ? »",
            "Transforme le sujet « la cybersécurité » en une problématique précise en une phrase.",
            ["Pas de problématique, pas de mémoire.", "Écrire chaque semaine bat tout écrire le dernier mois."]),
        ("2. CV, entretien et réseau : l'insertion professionnelle", [
            "Ton CV de fin de Licence doit montrer des preuves : projets avec liens publics (GitHub, démos), stages, compétences précises. « Motivé et dynamique » ne prouve rien ; « Portfolio en ligne + 3 projets déployés » prouve tout.",
            "En entretien, structure STAR pour raconter un projet : Situation, Tâche, Action, Résultat. Et construis ton réseau avant d'en avoir besoin : LinkedIn à jour, participation aux événements, aide rendue aux autres — les opportunités circulent entre personnes qui se connaissent.",
        ], "Réponse STAR : « Notre équipe devait livrer un portail d'emploi (S) ; je gérais la partie comptes utilisateurs (T) ; j'ai construit l'inscription et les rôles en Python (A) ; le jury a pu créer des comptes en direct pendant la démo (R). »",
            "Prépare ta réponse STAR pour ton meilleur projet en 4 phrases.",
            ["Des liens valent mieux que des adjectifs.", "Le réseau se cultive avant la recherche de stage."]),
        ("3. Anglais d'entretien : les questions classiques", [
            "Prépare en anglais les réponses aux questions universelles : « Tell me about yourself », « What are your strengths and weaknesses? », « Where do you see yourself in five years? », « Why should we hire you? ». Des réponses courtes, concrètes, avec un exemple à chaque fois.",
            "Pour « Tell me about yourself » : présent → parcours → objectif, en 30 secondes. « I am a final-year computer science student at IAM. I have built web projects — a job portal, an AI study assistant — and I am looking for an internship to grow as a developer. »",
        ], "Faiblesse bien présentée : « I used to disorganize my files; now I use a weekly planning system » — un défaut + le correctif mis en place.",
            "Écris ta réponse à « What are your strengths? » en 3 phrases avec un exemple.",
            ["Chaque affirmation appelle un exemple.", "30 secondes, pas 3 minutes."]),
    ]),
    ("Filière Informatique", [
        ("4. Génie logiciel : cycle de vie et méthodes agiles", [
            "Un logiciel professionnel suit un cycle : analyse des besoins, conception, développement, tests, déploiement, maintenance. La première cause d'échec n'est pas technique : c'est de construire vite le mauvais produit, faute d'avoir compris le besoin réel.",
            "Les méthodes agiles livrent par petits incréments (sprints d'une à deux semaines) avec retour des utilisateurs à chaque étape, au lieu d'un énorme livrable final découvert trop tard. La documentation utile reste minimale mais réelle : besoins, architecture, guide d'utilisation.",
        ], "Sprint type : semaine 1, l'inscription et la connexion marchent en démo ; semaine 2, le catalogue ; le client corrige le tir dès la semaine 1 au lieu de découvrir les erreurs au mois 3.",
            "Découpe la création d'une application de gestion de bibliothèque en 4 sprints logiques.",
            ["Comprendre le besoin avant de coder.", "Petites livraisons testées > long tunnel."]),
        ("5. Qualité du code et tests", [
            "Le code professionnel se juge à sa lisibilité : noms explicites, fonctions courtes avec un seul rôle, gestion propre des erreurs, pas de secrets (mots de passe, clés) écrits en dur dans le code. Un autre développeur — ou toi dans six mois — doit comprendre sans effort.",
            "Les tests automatisés vérifient les fonctions critiques : cas normaux ET cas limites (valeur zéro, texte vide, très grand nombre). Tester n'est pas du temps perdu : c'est ce qui permet de modifier le code sans peur de tout casser.",
        ], "Fonction diviser(a, b) : tester diviser(10, 2) = 5 (normal), diviser(5, 0) → erreur gérée (limite), diviser(0, 3) = 0 (limite).",
            "Pour une fonction qui calcule un prix avec remise, propose 4 cas de test pertinents.",
            ["Tester les cas limites, pas seulement le cas parfait.", "Aucun secret dans le code source, jamais."]),
        ("6. Sécurité appliquée : les défenses du développeur", [
            "Les attaques les plus fréquentes exploitent des fautes simples : entrées non validées (injection SQL, scripts injectés), mots de passe stockés en clair, sessions mal protégées, logiciels non mis à jour. La défense est en couches, et le développeur en est la première ligne.",
            "Check-list du développeur : requêtes préparées partout, mots de passe hachés avec un algorithme adapté, HTTPS obligatoire, droits minimums pour chaque compte, journaux d'erreurs surveillés, sauvegardes régulières et testées — une sauvegarde non testée est une sauvegarde imaginaire.",
        ], "Incident classique : une base de mots de passe en clair fuit → tous les comptes sont compromis partout où les utilisateurs réutilisaient le même mot de passe. Avec un hachage correct, la fuite devient beaucoup moins exploitable.",
            "Audite mentalement une petite application que tu connais : cite 3 risques et la défense associée à chacun.",
            ["Valider toutes les entrées, toujours.", "Hacher, jamais stocker en clair."]),
        ("7. Données et intelligence artificielle : comprendre avant d'utiliser", [
            "L'IA moderne apprend à partir de données : collecte, nettoyage, représentation, entraînement, évaluation. La règle d'or : la qualité des données décide de la qualité du résultat — des données fausses ou biaisées donnent un modèle faux ou biaisé, quelle que soit sa sophistication.",
            "Les grands modèles de langage génèrent le texte le plus plausible, pas le texte vrai : excellents pour expliquer, résumer, traduire et aider à coder, ils peuvent affirmer des erreurs avec assurance. Tout fait important venant d'une IA (date, chiffre, règle officielle) doit être vérifié à la source.",
        ], "Un assistant IA qui invente une date d'examen « plausible » peut faire rater un vrai examen : les faits officiels se vérifient toujours auprès du secrétariat.",
            "Cite 3 usages où l'IA t'aide sans risque, et 3 faits que tu ne lui confierais jamais sans vérification.",
            ["Données propres > modèle compliqué.", "Une réponse d'IA se vérifie avant de s'utiliser."]),
        ("8. Bases de données avancées : index et transactions", [
            "Un index accélère les recherches dans une table, comme l'index d'un livre : sans lui, la base lit toutes les lignes une à une. On indexe les colonnes souvent cherchées (matricule, e-mail), en sachant que chaque index ralentit légèrement les écritures.",
            "Une transaction regroupe plusieurs opérations qui doivent réussir ensemble ou échouer ensemble (principe « tout ou rien ») : un virement débite un compte ET crédite l'autre — jamais l'un sans l'autre. C'est la garantie qui protège l'argent et les stocks des incohérences.",
        ], "Virement de 20 000 : débit du compte A réussi, panne avant le crédit du compte B → la transaction annule tout, l'argent ne disparaît pas dans la nature.",
            "Pour une table de 100 000 étudiants, explique pourquoi chercher par matricule indexé est plus rapide que par nom non indexé.",
            ["Index = recherche rapide, écriture un peu plus lente.", "Transaction = tout ou rien."]),
    ]),
    ("Filière Gestion — BBA", [
        ("9. Stratégie d'entreprise : analyser avant d'agir", [
            "La stratégie consiste à choisir où l'entreprise va se battre et comment elle va gagner. L'analyse SWOT résume le diagnostic : Forces et Faiblesses (internes), Opportunités et Menaces (externes). Une bonne stratégie croise les deux : utiliser une force pour saisir une opportunité, corriger la faiblesse qui expose à une menace.",
            "L'avantage concurrentiel peut venir du prix, de la différence (qualité, service, rapidité) ou d'une niche précise. Vouloir tout à la fois — le moins cher ET le meilleur ET le plus rapide — est la stratégie qui échoue le plus sûrement.",
        ], "SWOT d'une boulangerie de quartier : Force = pain réputé ; Faiblesse = pas de livraison ; Opportunité = commandes WhatsApp des bureaux ; Menace = nouvelle boulangerie moderne. Stratégie : lancer la livraison WhatsApp aux bureaux.",
            "Fais la SWOT d'un petit commerce que tu connais, puis formule une stratégie en une phrase.",
            ["Interne = F/F ; externe = O/M.", "Choisir, c'est renoncer : une stratégie dit aussi ce qu'on ne fait pas."]),
        ("10. Finance : décider un investissement (VAN, en simple)", [
            "Investir, c'est dépenser aujourd'hui pour gagner demain. La Valeur Actuelle Nette (VAN) compare l'argent d'aujourd'hui et celui de demain : on actualise les gains futurs, on soustrait l'investissement initial. VAN positive → le projet crée de la valeur ; négative → il en détruit.",
            "Version terrain sans formules : additionne ce que le projet rapportera NET chaque année, compare au coût total en tenant compte du temps. Un projet qui rembourse son coût en 5 ans est rarement meilleur qu'un projet remboursé en 2 ans, à risque égal.",
        ], "Machine à 1 000 000 FCFA qui rapporte net 400 000 par an : remboursée en 2,5 ans. Même machine à 300 000 par an : 3,3 ans — la première option est préférable, à fiabilité égale.",
            "Un équipement coûte 600 000 et rapporte net 200 000/an. En combien d'années est-il remboursé ? Que se passe-t-il si les gains tombent à 150 000/an ?",
            ["Comparer des sommes de dates différentes exige l'actualisation.", "Délai de remboursement court = risque plus faible."]),
        ("11. Management et leadership en pratique", [
            "Manager, c'est obtenir des résultats avec et par les autres : objectifs clairs, rôles définis, suivi régulier, retours honnêtes. Le leadership ajoute la dimension humaine : donner du sens, montrer l'exemple, faire grandir les personnes.",
            "Deux leviers sous-estimés : la reconnaissance précise (« ton rapport de mardi a débloqué le client » — pas seulement « bon travail ») et la clarté des attentes (chacun sait ce qu'on attend de lui, pour quand, et comment ce sera jugé).",
        ], "Réunion efficace de 20 minutes : 3 points à l'ordre du jour, une décision par point, un responsable et une date par décision — puis un compte-rendu de 5 lignes.",
            "Prépare l'ordre du jour d'une réunion de bilan de projet d'équipe (5 points maximum).",
            ["Objectif flou = résultat flou.", "Déléguer, c'est confier le résultat, pas seulement les tâches."]),
    ]),
    ("Filières Droit, RH, Marketing, Logistique", [
        ("12. Droit des affaires : formes juridiques et contrats commerciaux", [
            "La forme juridique détermine la responsabilité des associés, les formalités et l'image de l'entreprise : l'entreprise individuelle est simple mais le patrimoine personnel est exposé ; la SARL protège mieux et rassure les partenaires ; la SA vise les projets plus grands.",
            "Le contrat commercial professionnel précise : les parties, l'objet exact, le prix et les modalités de paiement, les délais, les garanties et le sort des litiges. Neuf litiges sur dix naissent d'une clause absente ou floue — le temps passé à rédiger est toujours rentabilisé.",
        ], "Clause qui sauve : « Paiement : 50 % à la commande, 50 % à la livraison constatée » — contre le classique « on paiera après » qui ne dit ni quand ni comment.",
            "Rédige 3 clauses indispensables pour un contrat de création de site web pour un commerce.",
            ["Écrit clair > confiance aveugle.", "La forme juridique se choisit selon le risque."]),
        ("13. RH : évaluation, formation et paie (panorama)", [
            "Le cycle RH complet : recruter, intégrer, former, évaluer, rémunérer, faire évoluer. L'évaluation annuelle n'est pas un jugement : c'est un échange structuré sur les résultats, les progrès et les objectifs de l'année suivante — préparé par les deux parties.",
            "La formation continue est un investissement : une compétence nouvelle par personne et par an transforme une équipe en quelques années. La paie, elle, obéit à des règles strictes (contrat, cotisations, délais) : la rigueur y est non négociable.",
        ], "Objectif d'évaluation bien formulé : « réduire les délais de réponse clients de 24 h à 4 h d'ici juin » — mesurable et daté, au lieu de « mieux répondre aux clients ».",
            "Formule 2 objectifs annuels mesurables pour un vendeur en boutique.",
            ["Évaluer = échanger et projeter, pas sanctionner.", "Objectif = mesurable + daté."]),
        ("14. Marketing stratégique et logistique avancée (panorama)", [
            "Le marketing stratégique choisit ses batailles : segmentation (découper le marché), ciblage (choisir les segments), positionnement (l'idée simple qui doit rester dans la tête du client). Toutes les actions tactiques (publications, promotions) découlent de ces trois choix.",
            "Côté logistique, la supply chain moderne vise le flux tendu maîtrisé : stocks réduits mais rupture évitée grâce à la prévision et à des fournisseurs fiables. Le coût total compte — transport, stockage, ruptures — pas seulement le prix d'achat.",
        ], "Positionnement réussi en une phrase : « La boulangerie du quartier livrée à ton bureau avant 8 h » — client, promesse et différence sont dits en une ligne.",
            "Formule le positionnement d'un service que tu connais en une phrase (client + promesse + différence).",
            ["Segmenter, cibler, positionner — dans cet ordre.", "Le vrai coût logistique inclut les ruptures."]),
    ]),
]


# ================= ANNEXES L1 =================
LOIN_L1 = {
    "1. Le système LMD et l'organisation de ton année": "Pour aller plus loin : dès la première semaine, récupère le règlement des examens et le programme officiel de chaque UE. La plupart des mauvaises surprises (coefficients, conditions de compensation, sessions de rattrapage) sont écrites noir sur blanc dans ces documents que presque personne ne lit.",
    "6. Qu'est-ce qu'un algorithme ?": "Pour aller plus loin : la complexité mesure comment le temps de calcul grandit avec la taille des données. Chercher un nom dans une liste triée en la coupant en deux à chaque étape (recherche dichotomique) est immensément plus rapide que de la parcourir entièrement quand la liste est grande.",
    "8. Conditions et boucles": "Pour aller plus loin : les boucles « pour » et « tant que » peuvent toujours se remplacer l'une l'autre ; on choisit celle qui rend l'intention la plus claire. Et une boucle qui contient une autre boucle (boucles imbriquées) sert par exemple à parcourir un tableau à deux dimensions, ligne par ligne.",
    "11. Le Web : navigateur, moteur de recherche, et un premier regard sur HTML": "Pour aller plus loin : chaque page qu'un navigateur affiche a été récupérée par une requête HTTP(S) à un serveur. Regarder le code source d'une page simple (clic droit → « afficher le code source ») est le meilleur premier exercice de curiosité d'un étudiant en informatique.",
    "14. L'entreprise : formes, fonctions, environnement": "Pour aller plus loin : en L1, on te demandera souvent de distinguer l'entreprise de l'établissement (le lieu) et de la société (la forme juridique). Une même entreprise peut avoir plusieurs établissements ; une société est le cadre légal qui porte l'activité.",
    "18. La partie double : débit et crédit": "Pour aller plus loin : la balance des comptes additionne tous les débits et tous les crédits ; si les deux totaux diffèrent, une erreur s'est glissée dans les écritures. C'est le premier contrôle que réalise tout comptable avant d'établir le bilan.",
}

ANNEX_L1 = {
    "qcm": [
        ("Dans le système LMD, combien de crédits vaut la Licence complète ?", ["60 crédits", "120 crédits", "180 crédits"], 2, "3 ans × 60 crédits par an (30 par semestre) = 180 crédits."),
        ("Un algorithme doit être…", ["Le plus long possible", "Fini, précis et correct", "Écrit directement en langage machine"], 1, "Un algorithme est une suite finie et précise d'instructions qui donne le bon résultat."),
        ("Quel type de boucle convient quand le nombre de répétitions est connu ?", ["La boucle « tant que »", "La boucle « pour »", "Aucune boucle"], 1, "« Pour » est faite pour un nombre de tours déterminé à l'avance."),
        ("La RAM d'un ordinateur…", ["Conserve les fichiers après l'arrêt", "Se vide quand l'appareil s'éteint", "Remplace le disque dur"], 1, "La RAM est une mémoire vive temporaire ; le stockage, lui, est durable."),
        ("HTML sert à…", ["Calculer des salaires", "Structurer le contenu des pages web", "Protéger les mots de passe"], 1, "HTML définit la structure ; CSS la forme ; JavaScript le comportement."),
        ("Dans un tableur, la formule =MOYENNE(B2:B3) avec B2=12 et B3=15 donne…", ["13", "13,5", "27"], 1, "(12 + 15) ÷ 2 = 13,5."),
        ("Si la demande augmente alors que l'offre reste stable, le prix a tendance à…", ["Baisser", "Rester fixe", "Augmenter"], 2, "Plus d'acheteurs pour la même quantité → concurrence entre acheteurs → prix en hausse."),
        ("Le principe de la partie double signifie que…", ["On écrit chaque opération deux fois au même endroit", "Chaque écriture a un débit et un crédit de même montant", "On paie toujours en deux fois"], 1, "Ressource = emploi : les totaux débit et crédit sont toujours égaux."),
        ("Le compte de résultat calcule…", ["Le patrimoine à une date", "Produits − charges sur une période", "Le solde de caisse uniquement"], 1, "Le résultat est un flux sur une période ; le bilan est le stock (patrimoine) à une date."),
        ("Les 4P du marketing sont…", ["Produit, Prix, Place, Promotion", "Plan, Projet, Profit, Publicité", "Personnel, Processus, Preuve, Prix"], 0, "Le mix marketing classique : Produit, Prix, Place (distribution), Promotion."),
        ("Un contrat valable exige notamment…", ["Un tampon officiel dans tous les cas", "Consentement, capacité, objet licite, cause licite", "Un paiement d'avance"], 1, "Ce sont les quatre conditions classiques de validité d'un contrat."),
        ("L'intersection de A = {1, 2, 3} et B = {3, 4} est…", ["{1, 2, 3, 4}", "{3}", "{1, 2, 4}"], 1, "L'intersection ne garde que les éléments communs : ici, 3."),
        ("La médiane des valeurs 9, 12, 15 est…", ["9", "12", "15"], 1, "Valeurs triées : la médiane est celle du milieu, 12."),
        ("Le système d'exploitation sert à…", ["Remplacer les applications", "Faire le lien entre le matériel et les applications", "Se connecter à Internet uniquement"], 1, "L'OS gère matériel, mémoire, fichiers et applications."),
        ("« To download » signifie…", ["Supprimer", "Télécharger", "Enregistrer"], 1, "To download = télécharger ; to save = enregistrer ; to delete = supprimer."),
    ],
    "glossaire": [
        ("Algorithme", "suite finie d'instructions précises qui résout un problème."),
        ("Affectation", "action de ranger une valeur dans une variable."),
        ("Bilan", "photographie du patrimoine d'une entreprise à une date donnée."),
        ("Boucle", "structure qui répète un bloc d'instructions."),
        ("Capitalisable", "se dit d'un crédit d'UE acquis définitivement une fois l'UE validée."),
        ("Condition", "test qui décide quelles instructions exécuter (si… alors… sinon…)."),
        ("Crédit (comptabilité)", "colonne d'enregistrement des ressources et des augmentations de passif/produits."),
        ("Débit", "colonne d'enregistrement des emplois et des augmentations d'actif/charges."),
        ("Demande", "quantité d'un bien que les acheteurs souhaitent acquérir à un prix donné."),
        ("Extension", "suffixe d'un nom de fichier qui indique son type (.pdf, .jpg…)."),
        ("Médiane", "valeur du milieu d'une série triée."),
        ("Moteur de recherche", "service qui indexe le Web et aide à trouver des pages (Google, Bing)."),
        ("Navigateur", "logiciel qui affiche les pages web (Chrome, Firefox, Edge)."),
        ("Offre", "quantité d'un bien que les vendeurs proposent à un prix donné."),
        ("Pseudo-code", "description d'un algorithme en langage humain structuré, avant le codage."),
        ("RAM", "mémoire vive temporaire où l'ordinateur place le travail en cours."),
        ("Résultat (compte de)", "produits − charges d'une période ; bénéfice si positif, perte sinon."),
        ("Variable", "nom associé à une valeur stockée en mémoire, d'un type donné."),
    ],
    "sujets": [
        ("Sujet d'entraînement n°1 — Algorithmique et logique (30 minutes)",
         "1) Écris un algorithme qui lit deux notes et affiche la moyenne, puis « Admis » si elle est ≥ 10, « Recalé » sinon. 2) Avec A = {2, 4, 6, 8} et B = {4, 8, 10}, donne A ∪ B et A ∩ B. 3) Explique en trois lignes la différence entre une boucle « pour » et une boucle « tant que », avec un exemple de situation pour chacune.",
         "1) Lire n1, n2 ; m ← (n1+n2)/2 ; afficher m ; si m ≥ 10 afficher « Admis » sinon « Recalé ». 2) A ∪ B = {2, 4, 6, 8, 10} ; A ∩ B = {4, 8}. 3) « Pour » = nombre de tours connu (table de multiplication) ; « tant que » = arrêt conditionnel (saisie d'un mot de passe correct)."),
        ("Sujet d'entraînement n°2 — Gestion et comptabilité (30 minutes)",
         "Une boutique achète 40 téléphones à 25 000 FCFA l'unité et les revend 32 000 FCFA. 1) Calcule le coût d'achat total, le chiffre d'affaires si tout est vendu, et la marge totale. 2) Enregistre en partie double l'achat de 10 téléphones payés en espèces. 3) La boutique doit encore 150 000 FCFA à son fournisseur et possède 900 000 FCFA d'actif au bilan : que valent ses capitaux propres ?",
         "1) Coût : 40 × 25 000 = 1 000 000 ; CA : 40 × 32 000 = 1 280 000 ; marge = 280 000 FCFA. 2) Débit Achats de marchandises 250 000 / Crédit Caisse 250 000. 3) Capitaux propres = actif − dettes = 900 000 − 150 000 = 750 000 FCFA."),
    ],
}



# ================= L1 — COMPLÉMENTS =================
L1.append(("Compléments — approfondir et s'entraîner", [
    ("22. Histoire et culture de l'informatique", [
        "L'informatique moderne naît au XXe siècle : machines à calculer mécaniques, puis premiers ordinateurs électroniques dans les années 1940, transistor, circuit intégré, microprocesseur (années 1970), ordinateur personnel (années 1980), Web (1989) puis téléphone intelligent. Chaque génération a divisé les coûts et multiplié les usages.",
        "Comprendre cette trajectoire aide à relativiser les modes : les principes (données, algorithmes, réseaux) restent, les outils changent. Un bon étudiant apprend donc les principes à fond et les outils avec curiosité, sans s'y attacher définitivement.",
    ], "En 30 ans, la mémoire d'un téléphone est passée de quelques mégaoctets à plusieurs centaines de gigaoctets — un facteur supérieur à 100 000.",
        "Cite trois générations technologiques et un usage nouveau rendu possible par chacune.",
        ["Les principes durent, les outils passent.", "Chaque génération = plus petit, plus rapide, moins cher."]),
    ("23. Mathématiques financières — intérêts simples et pourcentages", [
        "Un pourcentage compare une partie à un tout ramené à 100 : partie ÷ tout × 100. Augmenter un prix de 10 %, c'est le multiplier par 1,10 ; le baisser de 10 %, par 0,90. Deux hausses successives de 10 % ne font pas +20 % mais +21 % (1,10 × 1,10 = 1,21) — le piège classique.",
        "L'intérêt simple rémunère un capital : I = C × t × n (capital × taux annuel × nombre d'années). Exemple : 100 000 FCFA à 5 % pendant 2 ans → intérêts = 100 000 × 0,05 × 2 = 10 000 FCFA.",
    ], "Un article à 20 000 FCFA soldé à −25 % coûte 20 000 × 0,75 = 15 000 FCFA.",
        "Calcule les intérêts simples de 250 000 FCFA placés à 4 % pendant 3 ans.",
        ["+10 % = × 1,10 ; −10 % = × 0,90.", "I = C × t × n pour l'intérêt simple."]),
    ("24. Communication écrite professionnelle", [
        "Un écrit professionnel (e-mail, lettre, compte rendu) se juge en dix secondes : objet clair, phrases courtes, une idée par paragraphe, formules de politesse adaptées. La structure gagnante : qui je suis, ce que je demande, les éléments utiles, la suite attendue.",
        "Relis toujours avant d'envoyer : fautes, destinataires, pièces jointes annoncées mais oubliées — le classique. Un e-mail soigné est la première preuve de sérieux d'un étudiant comme d'un professionnel.",
    ], "Objet efficace : « Demande de stage — étudiant L1 informatique (IAM) — juin-juillet » plutôt que « Bonjour » ou « Urgent ».",
        "Rédige un e-mail de 6 lignes pour demander un rendez-vous à un professeur au sujet d'un devoir.",
        ["Objet précis, phrases courtes, une idée par paragraphe.", "Relire avant d'envoyer — toujours."]),
    ("25. Culture numérique : chercher, vérifier, citer", [
        "Savoir chercher est une compétence : mots-clés précis, opérateurs simples (guillemets pour une expression exacte), choix de sources fiables (sites officiels, ouvrages, presse reconnue). Une information importante se vérifie toujours auprès d'au moins deux sources indépendantes.",
        "Citer ses sources (auteur, titre, date, lien) protège du plagiat et renforce ton travail. Copier sans citer, même « juste un paragraphe », est une faute académique qui peut coûter très cher aux examens comme en soutenance.",
    ], "Pour une date officielle d'examen, la source qui compte est l'administration de l'université — pas une rumeur de groupe WhatsApp ni une réponse d'IA.",
        "Pour le sujet « l'histoire du Web », propose 4 mots-clés de recherche et 2 types de sources fiables.",
        ["Deux sources indépendantes minimum pour un fait important.", "Citer = protéger son travail."]),
    ("26. Découverte de l'entrepreneuriat", [
        "Entreprendre commence par un problème réel observé autour de soi : une file d'attente interminable, un service absent, un produit trop cher. L'idée ne vaut rien sans exécution : parler aux futurs clients, tester une version simple, vendre, corriger.",
        "À Bamako comme ailleurs, beaucoup de petites entreprises naissent d'un savoir-faire (réparer, coudre, coder, cuisiner) et d'un téléphone : WhatsApp pour les commandes, les réseaux sociaux pour la vitrine, un carnet ou une application pour suivre l'argent.",
    ], "Un réparateur de téléphones qui répond vite sur WhatsApp et tient un carnet de réparations clair gagne la confiance du quartier — c'est déjà du marketing.",
        "Observe ton quartier : cite un problème quotidien et le service simple qui pourrait le résoudre.",
        ["Un problème réel vaut mille idées abstraites.", "Tester petit, vendre, corriger."]),
    ("27. Environnement de travail et organisation personnelle", [
        "La réussite en L1 est d'abord une affaire d'organisation : emploi du temps hebdomadaire visible, créneaux fixes de révision, téléphone en silencieux pendant les sessions de travail, et une liste de tâches réaliste chaque matin.",
        "La méthode des sessions courtes concentrées (25 à 45 minutes, pause de 5 à 10 minutes) bat les longues sessions distraits. Deux sessions propres par jour transforment un semestre.",
    ], "Planning type d'une soirée : 18h00-18h40 révision d'algorithmique, pause, 19h00-19h40 exercices de statistiques, 20h relecture des notes du jour (10 minutes).",
        "Construis ton planning de révision de la semaine prochaine, avec deux sessions par jour.",
        ["Créneaux fixes > bonnes intentions.", "Sessions courtes et concentrées, téléphone silencieux."]),
]))

ANNEX_L1["qcm"] += [
    ("Deux augmentations successives de 10 % donnent au total…", ["+20 %", "+21 %", "+19 %"], 1, "1,10 × 1,10 = 1,21, soit +21 %."),
    ("L'intérêt simple de 100 000 FCFA à 5 % pendant 2 ans vaut…", ["5 000 FCFA", "10 000 FCFA", "20 000 FCFA"], 1, "I = 100 000 × 0,05 × 2 = 10 000 FCFA."),
    ("Le Web a été inventé vers…", ["1969", "1989", "2007"], 1, "Tim Berners-Lee propose le Web en 1989 au CERN."),
    ("Pour vérifier un fait important, il faut au minimum…", ["Une seule source très connue", "Deux sources indépendantes", "Dix partages sur WhatsApp"], 1, "Le croisement de sources indépendantes est la règle de base de la vérification."),
    ("Un objet d'e-mail efficace doit être…", ["Le plus long possible", "Clair et précis", "Écrit en majuscules"], 1, "L'objet annonce le contenu : « Demande de stage — L1 informatique » ."),
    ("La méthode de travail la plus efficace en révision est…", ["Une nuit blanche avant l'examen", "Des sessions courtes et régulières", "Relire uniquement les titres"], 1, "La régularité et la concentration battent le sprint de dernière minute."),
    ("Une boucle « tant que » s'arrête quand…", ["Le programme se ferme", "Sa condition devient fausse", "Elle a tourné 100 fois"], 1, "« Tant que » répète pendant que la condition est vraie ; elle s'arrête quand elle devient fausse."),
    ("Le camembert (diagramme circulaire) sert surtout à montrer…", ["Une évolution dans le temps", "Des parts d'un tout", "Une comparaison de prix"], 1, "Parts d'un tout = camembert ; évolution = courbe ; comparaison = barres."),
    ("Dans « si note ≥ 10 alors admis », la condition est…", ["note", "≥ 10", "note ≥ 10"], 2, "La condition est le test complet : note ≥ 10."),
    ("Le rôle du marketing est d'abord de…", ["Décorer les produits", "Comprendre le besoin du client", "Fixer les salaires"], 1, "Le marketing part du besoin et du client, pas du produit."),
    ("Le grand-livre sert à…", ["Enregistrer les opérations jour par jour dans l'ordre", "Regrouper les écritures par compte", "Calculer les salaires"], 1, "Le journal est chronologique ; le grand-livre classe par compte."),
    ("La fonction RH s'occupe notamment de…", ["La publicité", "Le recrutement et la formation", "Les livraisons"], 1, "RH = recruter, intégrer, former, évaluer, rémunérer."),
    ("Un fichier nommé « devoir.pdf » est…", ["Une image", "Un document au format PDF", "Un programme"], 1, "L'extension .pdf indique un document figé, lisible partout."),
    ("« Software » désigne…", ["Le matériel", "Les logiciels", "L'écran"], 1, "Software = logiciels ; hardware = matériel."),
    ("Le passif du bilan représente…", ["Ce que l'entreprise possède", "Ce que l'entreprise doit + ses capitaux propres", "Uniquement la caisse"], 1, "Actif (ce qu'elle possède) = Passif (capitaux propres + dettes)."),
]
ANNEX_L1["glossaire"] += [
    ("Balance (comptabilité)", "tableau qui totalise débits et crédits de tous les comptes pour contrôle."),
    ("Chiffre d'affaires", "total des ventes d'une période."),
    ("Dichotomie", "recherche par divisions successives en deux dans un ensemble trié."),
    ("Grand-livre", "ensemble des comptes où sont classées les écritures du journal."),
    ("Intérêt simple", "rémunération d'un capital calculée uniquement sur le capital initial."),
    ("Journal (comptabilité)", "registre chronologique des opérations."),
    ("Plagiat", "présenter le travail d'autrui comme le sien, sans citation."),
    ("Seuil", "valeur à partir de laquelle un effet se déclenche (admission, rentabilité…)."),
]
ANNEX_L1["sujets"] += [
    ("Fiche méthode — Préparer un examen écrit en 7 jours",
     "Jour 1 : rassemble cours, TD et annales ; liste les chapitres et note ton niveau honnête sur chacun. Jours 2 à 4 : un ou deux chapitres par jour — relire, ficher, refaire les exercices sans regarder les corrections. Jour 5 : un sujet complet en temps limité, chronométré. Jour 6 : corrige tes erreurs, refais uniquement les exercices ratés, relis toutes tes fiches. Jour 7 (veille) : relecture légère le matin, aucune notion nouvelle l'après-midi, matériel préparé, coucher tôt. Le jour J : arrive en avance, lis tout le sujet avant de commencer, attaque par ce que tu maîtrises.",
     ""),
    ("Sujet d'entraînement n°3 — Culture numérique et calculs (30 minutes)",
     "1) Un commerçant augmente un prix de 15 % puis le baisse de 15 %. Retrouve-t-il le prix de départ ? Justifie par un calcul sur 10 000 FCFA. 2) Tu lis sur un réseau social qu'un examen est reporté : cite les deux vérifications que tu fais avant d'y croire. 3) Range ces inventions dans l'ordre chronologique : Web, microprocesseur, ordinateur personnel, transistor.",
     "1) Non : 10 000 × 1,15 = 11 500 ; 11 500 × 0,85 = 9 775 ≠ 10 000 (les pourcentages ne s'appliquent pas à la même base). 2) Vérifier le canal officiel de l'université et recouper avec une deuxième source fiable (affichage, secrétariat). 3) Transistor (1947) → microprocesseur (1971) → ordinateur personnel (années 1980) → Web (1989)."),
]



# ================= L2 — ANNEXES ET COMPLÉMENTS =================
LOIN_L2 = {
    "4. Python : fonctions, listes, dictionnaires": "Pour aller plus loin : les listes acceptent des « compréhensions » qui construisent une liste en une ligne, par exemple [n * 2 for n in notes]. C'est un style très pythonique que tu dois savoir lire, même si tu écris d'abord la version avec une boucle classique.",
    "6. HTML et CSS : construire une page propre": "Pour aller plus loin : Flexbox et Grid sont les deux systèmes de mise en page modernes de CSS. Flexbox aligne des éléments sur un axe (une barre de navigation), Grid organise en lignes et colonnes (une galerie). Maîtriser ces deux outils fait passer tes pages du bricolage au niveau professionnel.",
    "8. PHP et SQL : le site dynamique complet": "Pour aller plus loin : sépare toujours, dans tes fichiers PHP, la logique (traitements, requêtes) de l'affichage (HTML). Cette séparation — l'esprit du modèle MVC que tu verras en L3 — rend le code testable et modifiable sans tout casser.",
    "13. Gestion de projet : rôles, tâches, livrables": "Pour aller plus loin : un tableau Kanban (À faire / En cours / Fait) affiché en permanence vaut mieux qu'un long rapport hebdomadaire. Des outils gratuits comme Trello ou un simple tableau blanc suffisent pour une équipe étudiante.",
    "15. Trésorerie : suivre l'argent qui entre et sort": "Pour aller plus loin : distingue le besoin en fonds de roulement (l'argent immobilisé par les stocks et les délais de paiement des clients, moins les délais accordés par les fournisseurs) : c'est lui qui explique la plupart des trous de trésorerie des petites entreprises.",
}

ANNEX_L2 = {
    "qcm": [
        ("La probabilité de ne PAS obtenir un événement de probabilité 0,3 est…", ["0,3", "0,7", "1,3"], 1, "P(contraire) = 1 − 0,3 = 0,7."),
        ("En Python, def moyenne(notes): return sum(notes)/len(notes) définit…", ["Une variable", "Une fonction", "Une classe"], 1, "Le mot-clé def introduit une fonction ; return renvoie son résultat."),
        ("Dans un dictionnaire Python, on accède à une valeur par…", ["Son index numérique uniquement", "Sa clé", "Sa position dans l'alphabet"], 1, "Un dictionnaire associe des clés à des valeurs : etudiant[\"nom\"]."),
        ("La POO repose sur trois piliers : encapsulation, héritage et…", ["Compilation", "Polymorphisme", "Normalisation"], 1, "Le polymorphisme : une même interface, des comportements différents selon l'objet."),
        ("En HTML, pour créer un lien on utilise la balise…", ["<link>", "<a>", "<href>"], 1, "La balise <a href=\"...\"> crée un lien hypertexte."),
        ("Le modèle de boîte CSS comprend, de l'intérieur vers l'extérieur…", ["Margin, bordure, padding, contenu", "Contenu, padding, bordure, margin", "Contenu, margin, bordure, padding"], 1, "Contenu → padding (espace interne) → bordure → margin (espace externe)."),
        ("En JavaScript, addEventListener sert à…", ["Créer une variable", "Réagir à un événement (clic, saisie…)", "Se connecter à une base"], 1, "C'est le mécanisme d'écoute des événements sur les éléments de la page."),
        ("L'ordre SQL qui MODIFIE des données existantes est…", ["SELECT", "UPDATE", "DELETE"], 1, "UPDATE modifie ; SELECT lit ; DELETE supprime."),
        ("Une requête préparée protège contre…", ["Les coupures de courant", "L'injection SQL", "Les fautes d'orthographe"], 1, "Les paramètres sont séparés du code SQL : impossible d'injecter des ordres."),
        ("Une clé étrangère sert à…", ["Chiffrer la base", "Relier les tables entre elles", "Trier les résultats"], 1, "Elle référence la clé primaire d'une autre table."),
        ("Le DNS sert à…", ["Distribuer les adresses IP", "Traduire les noms de domaine en adresses IP", "Chiffrer les pages web"], 1, "DNS = l'annuaire d'Internet ; le DHCP, lui, distribue les adresses."),
        ("La commande Linux grep sert à…", ["Lister les fichiers", "Rechercher un texte dans des fichiers", "Créer un dossier"], 1, "grep \"motif\" fichier affiche les lignes contenant le motif."),
        ("Un mot de passe robuste est avant tout…", ["Court et mémorable", "Long, unique et mélangé", "Le même partout pour ne pas l'oublier"], 1, "Longueur + unicité + mélange, et double authentification si possible."),
        ("Le seuil de rentabilité est atteint quand…", ["Les ventes dépassent 100 unités", "La marge totale couvre les charges fixes", "Le stock est épuisé"], 1, "Marge unitaire × quantités = charges fixes : en dessous on perd, au-dessus on gagne."),
        ("La trésorerie représente…", ["Le bénéfice de l'année", "L'argent disponible immédiatement", "La valeur du stock"], 1, "C'est le liquide disponible, à distinguer du résultat comptable."),
        ("En gestion de projet, un livrable est…", ["Une réunion", "Un résultat vérifiable attendu à une date", "Un logiciel obligatoire"], 1, "Un livrable se constate : une démo qui marche, un document remis."),
        ("Le RCCM est…", ["Un impôt", "Le registre officiel d'immatriculation des commerces", "Un logiciel de comptabilité"], 1, "Registre du Commerce et du Crédit Mobilier : il officialise l'entreprise."),
        ("Le point de commande se calcule par…", ["Prix × quantité en stock", "Ventes par jour × délai de livraison + sécurité", "Stock maximal − stock minimal"], 1, "Il déclenche la commande assez tôt pour éviter la rupture pendant le délai du fournisseur."),
        ("Un ratio d'endettement élevé signifie…", ["Une entreprise très rentable", "Une dépendance forte aux dettes, donc une fragilité", "Un stock trop important"], 1, "Dettes ÷ capitaux propres élevé = les créanciers portent l'essentiel du risque."),
        ("Dans le parcours client digital, la première étape est…", ["Acheter", "Découvrir", "Recommander"], 1, "Découvrir → s'intéresser → faire confiance → acheter → recommander."),
        ("Une présentation orale efficace comporte…", ["Des diapositives remplies de texte lues à voix haute", "Une idée par diapositive et un entraînement chronométré", "Aucune préparation pour rester naturel"], 1, "Slides simples + entraînement à voix haute = la recette de base."),
        ("« Internship » signifie en anglais…", ["Entretien", "Stage", "Licence"], 1, "Internship = stage ; interview = entretien."),
        ("Deux événements sont indépendants si…", ["Ils se produisent le même jour", "L'un n'influence pas la probabilité de l'autre", "Leurs probabilités sont égales"], 1, "L'indépendance autorise la multiplication des probabilités."),
        ("En CSS, le sélecteur .btn vise…", ["L'élément d'id btn", "Tous les éléments de classe btn", "La balise btn"], 1, "Le point désigne une classe ; le dièse (#) désigne un id."),
        ("HTTPS apporte par rapport à HTTP…", ["La vitesse", "Le chiffrement des échanges", "La traduction des noms"], 1, "HTTPS = HTTP + TLS : les données voyagent chiffrées."),
        ("Un processus est…", ["Un fichier sur le disque", "Un programme en cours d'exécution", "Un utilisateur connecté"], 1, "Le programme devient processus quand l'OS l'exécute."),
        ("La classe, en POO, est…", ["Un objet particulier", "Le modèle qui définit attributs et méthodes", "Une base de données"], 1, "La classe est le moule ; les objets sont les exemplaires."),
        ("Le fonds de roulement compare…", ["Les ventes et les achats", "Les ressources stables et les immobilisations", "La caisse et la banque"], 1, "Ressources stables − immobilisations : s'il est positif, le long terme est financé sainement."),
        ("Pour éviter les ruptures de stock, on surveille surtout…", ["La couleur des produits", "Le stock minimum et le point de commande", "Le nombre de vendeurs"], 1, "Ces deux repères déclenchent les commandes au bon moment."),
        ("Une fiche de poste sert à…", ["Décorer le bureau", "Définir missions, compétences et conditions avant de recruter", "Calculer les salaires"], 1, "Un poste clair est la condition d'un recrutement réussi."),
    ],
    "glossaire": [
        ("Agile", "méthode de travail par petites livraisons fréquentes avec retours réguliers."),
        ("Business plan", "document qui présente un projet d'entreprise : offre, marché, organisation, finances."),
        ("Clé étrangère", "colonne qui référence la clé primaire d'une autre table."),
        ("Clé primaire", "identifiant unique d'une ligne dans une table."),
        ("DHCP", "service qui distribue automatiquement les adresses IP sur un réseau."),
        ("DNS", "service qui traduit les noms de domaine en adresses IP."),
        ("DOM", "représentation de la page web que JavaScript peut lire et modifier."),
        ("Encapsulation", "protection des données d'un objet, accessibles via ses méthodes."),
        ("Fonds de roulement", "ressources stables − immobilisations ; marge de sécurité financière."),
        ("Héritage (POO)", "mécanisme par lequel une classe spécialise une autre classe."),
        ("Injection SQL", "attaque qui insère du code SQL via une entrée non protégée."),
        ("Jointure (JOIN)", "opération qui combine les lignes de plusieurs tables liées."),
        ("Livrable", "résultat vérifiable attendu à l'issue d'une tâche ou d'un projet."),
        ("Normalisation", "organisation des tables pour éliminer les doublons et incohérences."),
        ("Phishing", "arnaque par faux message/site imitant un service connu pour voler des identifiants."),
        ("Point de commande", "niveau de stock qui déclenche une nouvelle commande."),
        ("Polymorphisme", "capacité d'une même interface à produire des comportements différents selon l'objet."),
        ("Processus", "programme en cours d'exécution, géré par le système d'exploitation."),
        ("Requête préparée", "requête SQL dont les paramètres sont transmis séparément du code."),
        ("Seuil de rentabilité", "niveau d'activité où la marge couvre exactement les charges fixes."),
        ("Sprint", "courte période de travail agile (1-2 semaines) aboutissant à une livraison."),
        ("Trésorerie", "argent immédiatement disponible d'une organisation."),
    ],
    "sujets": [
        ("Sujet d'entraînement n°1 — Web et bases de données (45 minutes)",
         "Une association veut un site avec inscription des membres (nom, téléphone, quartier). 1) Écris le HTML du formulaire d'inscription. 2) Crée la table SQL membres avec une clé primaire. 3) Écris, en PHP ou en pseudo-code, le traitement qui enregistre un membre avec une requête préparée. 4) Écris la requête qui liste les membres d'un quartier donné, triés par nom.",
         "1) Form avec method POST et inputs nom, telephone, quartier + bouton. 2) CREATE TABLE membres (id INT PRIMARY KEY AUTO_INCREMENT, nom VARCHAR(80), telephone VARCHAR(20), quartier VARCHAR(60)). 3) Préparer INSERT INTO membres (nom, telephone, quartier) VALUES (?, ?, ?), lier les valeurs nettoyées, exécuter, confirmer. 4) SELECT * FROM membres WHERE quartier = ? ORDER BY nom (paramètre lié)."),
        ("Sujet d'entraînement n°2 — Gestion (30 minutes)",
         "Un atelier de couture a 180 000 FCFA de charges fixes mensuelles. Chaque tenue dégage une marge de 3 000 FCFA. 1) Calcule le seuil de rentabilité en nombre de tenues. 2) L'atelier vend 75 tenues ce mois : gagne-t-il ou perd-il, et combien ? 3) Cite deux actions concrètes pour abaisser le seuil.",
         "1) 180 000 ÷ 3 000 = 60 tenues. 2) 75 × 3 000 = 225 000 de marge − 180 000 = +45 000 FCFA de bénéfice. 3) Réduire une charge fixe (négocier le loyer, mutualiser un local) ou augmenter la marge (monter légèrement le prix, réduire le coût des tissus par achats groupés)."),
        ("Fiche méthode — Travailler en équipe sur un projet noté",
         "Dès la première réunion : écrivez l'objectif en une phrase, découpez le travail en tâches datées avec un responsable unique par tâche, et fixez le rendez-vous de point d'avancement (15 minutes, toujours le même jour). Créez le dépôt Git et le document partagé le jour même. À chaque point : ce qui est fait (démontré, pas raconté), ce qui bloque, qui débloque. La semaine de la présentation : gel des nouveautés, tests, répétition complète chronométrée. Le secret des bonnes équipes n'est pas le talent individuel, c'est la visibilité permanente de l'avancement.",
         ""),
    ],
}

L2.append(("Compléments — approfondir et s'entraîner", [
    ("20. Algorithmique avancée : tris et recherche", [
        "Trier et chercher sont les deux opérations reines de l'algorithmique. La recherche dichotomique, dans un tableau trié, divise l'espace de recherche par deux à chaque étape : pour 1 000 000 d'éléments, environ 20 comparaisons suffisent, contre 500 000 en moyenne pour une recherche simple.",
        "Les tris classiques (à bulles, par sélection, par insertion) sont lents sur de gros volumes ; les tris rapides (fusion, rapide) découpent le problème en sous-problèmes. Retenir l'idée plutôt que le code : diviser pour régner.",
    ], "Chercher le mot « réseau » dans un dictionnaire : tu ouvres au milieu, puis tu réduis la moitié restante — c'est la dichotomie, que tu pratiques depuis l'enfance sans le savoir.",
        "Dans un tableau trié de 1 000 éléments, combien de comparaisons au maximum pour une dichotomie ? (Indice : 2^10 = 1 024.)",
        ["Dichotomie = tableau trié obligatoire.", "Diviser pour régner : tris fusion et rapide."]),
    ("21. Introduction aux API et au format JSON", [
        "Une API est un contrat d'échange entre logiciels : une application envoie une requête (souvent HTTP) et reçoit des données structurées, le plus souvent en JSON — un format texte de paires clé/valeur et de listes, lisible par les humains comme par les machines.",
        "Exemple d'usage : une application météo interroge l'API d'un service et affiche la réponse. Comprendre les requêtes GET/POST et le JSON est indispensable : les applications modernes sont des assemblages d'API.",
    ], "{\"nom\": \"Awa\", \"note\": 15} est un objet JSON : deux clés, « nom » (texte) et « note » (nombre).",
        "Écris un objet JSON décrivant un produit (nom, prix, stock) puis une liste de deux produits.",
        ["API = contrat d'échange entre logiciels.", "JSON = clés/valeurs et listes, en texte."]),
    ("22. Anglais — vocabulaire de l'entretien et du stage", [
        "Mots et expressions du monde du travail : internship (stage), application (candidature), resume/CV (CV), interview (entretien), skills (compétences), deadline (date limite), team (équipe), goal (objectif).",
        "Phrases prêtes : « I am applying for an internship in your company » (je postule pour un stage dans votre entreprise) ; « My main skills are Python and web development » ; « Thank you for your time » pour conclure poliment.",
    ], "Un e-mail de candidature commence par « Dear Sir or Madam » et se termine par « Yours faithfully » + ton nom complet.",
        "Traduis : « Je suis étudiant en deuxième année d'informatique et je cherche un stage de deux mois. »",
        ["Internship = stage ; application = candidature.", "Des phrases courtes et polies valent mieux qu'un anglais compliqué."]),
    ("23. Statistiques : lire et critiquer un graphique", [
        "Un graphique peut mentir sans falsifier les chiffres : axe vertical tronqué qui exagère une petite variation, échelle irrégulière, camembert en 3D qui déforme les parts, période choisie pour arranger le message.",
        "Réflexe critique en trois questions : d'où viennent les données ? L'axe commence-t-il à zéro ? La période et l'échantillon sont-ils représentatifs ? Ces questions valent pour les médias comme pour les rapports d'entreprise.",
    ], "Un graphique qui montre une hausse « spectaculaire » de 100 à 104 avec un axe démarrant à 95 transforme +4 % en montagne visuelle.",
        "Trouve dans un journal ou en ligne un graphique et applique-lui les trois questions critiques.",
        ["Un graphique est un argument, pas une preuve.", "Toujours vérifier l'axe, la source et la période."]),
]))


# ================= L3 — ANNEXES ET COMPLÉMENTS =================
LOIN_L3 = {
    "2. MVC : séparer modèle, vue, contrôleur": "Pour aller plus loin : les grands frameworks (Laravel pour PHP, Django pour Python) imposent le MVC. Savoir l'expliquer avec un exemple concret — une page qui affiche des produits — est une question classique d'entretien de stage.",
    "5. API REST : concevoir des services propres": "Pour aller plus loin : versionne tes URL (/api/v1/produits), documente chaque route (méthode, paramètres, réponse) comme un contrat public, et ne change jamais un format sans prévenir : tes clients dépendent de cette stabilité.",
    "9. Stratégie d'entreprise : vision, mission, avantage": "Pour aller plus loin : l'océan bleu consiste à créer un espace de marché nouveau plutôt qu'à se battre dans un océan rouge saturé — par exemple en ciblant un public négligé avec une offre plus simple et moins chère.",
    "12. E-commerce : vendre en ligne proprement": "Pour aller plus loin : mesure ton entonnoir (visites → vues produit → ajouts panier → commandes) : le maillon le plus faible indique exactement où travailler, au lieu de tout refaire au hasard.",
}

ANNEX_L3 = {
    "qcm": [
        ("Dans le MVC, le Contrôleur sert à…", ["Stocker les données", "Recevoir les demandes et coordonner modèle et vue", "Dessiner les pages"], 1, "Il fait le lien : il reçoit, traite via le modèle, choisit la vue."),
        ("La jointure qui garde TOUTES les lignes de la table de gauche est…", ["INNER JOIN", "LEFT JOIN", "CROSS JOIN"], 1, "LEFT JOIN conserve les lignes sans correspondance (avec NULL en face)."),
        ("GROUP BY sert à…", ["Trier les lignes", "Regrouper les lignes pour agréger (COUNT, SUM…)", "Supprimer les doublons"], 1, "Il regroupe selon une ou plusieurs colonnes, puis les fonctions d'agrégat calculent par groupe."),
        ("Une route REST pour supprimer le produit 5 est…", ["GET /produits/supprimer/5", "DELETE /produits/5", "POST /delete"], 1, "La méthode DELETE exprime l'action ; l'URL désigne la ressource."),
        ("Le code HTTP 201 signifie…", ["Erreur serveur", "Création réussie", "Non trouvé"], 1, "201 Created : une ressource vient d'être créée."),
        ("Un index en base de données sert surtout à…", ["Chiffrer les données", "Accélérer les recherches", "Réduire le nombre de tables"], 1, "Comme un index de livre : retrouver vite, au prix d'un peu d'espace."),
        ("Une attaque XSS consiste à…", ["Saturer un serveur", "Injecter un script dans une page vue par d'autres", "Deviner un mot de passe"], 1, "XSS = script malveillant exécuté dans le navigateur des visiteurs."),
        ("La sauvegarde 3-2-1 recommande…", ["3 mots de passe, 2 comptes, 1 clé", "3 copies, 2 supports différents, 1 hors site", "3 disques identiques au même endroit"], 1, "3 copies, 2 supports, 1 copie éloignée : protection contre panne, vol et sinistre."),
        ("En agile, le backlog est…", ["Le code terminé", "La liste priorisée des fonctionnalités à réaliser", "Le rapport final"], 1, "Le backlog ordonne ce qui reste à construire, du plus au moins prioritaire."),
        ("L'avantage concurrentiel durable repose sur…", ["Le prix le plus bas du marché", "Ce que l'entreprise fait mieux et qui est difficile à copier", "La publicité"], 1, "Compétence distinctive + difficulté d'imitation = durabilité."),
        ("Le pitch d'un projet doit d'abord énoncer…", ["Les technologies utilisées", "Le problème et les personnes concernées", "Le budget"], 1, "Sans problème clair, aucune solution ne convainc."),
        ("Les coûts cachés d'un produit incluent…", ["Uniquement la matière première", "Emballage, transport, retours, temps", "Le seul salaire du vendeur"], 1, "Le coût complet évite de vendre à perte sans le savoir."),
        ("Un bon CV de fin d'études met en avant…", ["Toutes les matières suivies", "Projets, stages, compétences et résultats concrets", "Les notes de toutes les années"], 1, "Des preuves (liens, chiffres, réalisations) plutôt que des listes."),
        ("Le RGPD concerne…", ["Le commerce international", "La protection des données personnelles (UE)", "Les réseaux sociaux"], 1, "Règlement européen de protection des données ; beaucoup de pays ont leurs propres lois analogues."),
        ("En SQL, HAVING filtre…", ["Les lignes avant regroupement", "Les groupes après GROUP BY", "Les colonnes affichées"], 1, "WHERE filtre les lignes ; HAVING filtre les groupes."),
        ("Tester un produit minimal (MVP) sert à…", ["Terminer plus vite sans réfléchir", "Valider l'idée auprès de vrais clients avant d'investir", "Éviter tout retour client"], 1, "Le MVP apprend, avec le minimum d'effort, si le besoin est réel."),
        ("La portée d'un routeur Wi-Fi domestique dépend surtout de…", ["La couleur de la box", "L'emplacement central et dégagé, loin des obstacles", "Le nombre d'antennes dessinées sur la boîte"], 1, "La hauteur et la centralité priment ; murs épais et métal bloquent le signal."),
        ("Un mot de passe de Wi-Fi robuste utilise…", ["Le nom de l'opérateur par défaut", "WPA2/WPA3 et une phrase longue", "Le numéro de téléphone du propriétaire"], 1, "Chiffrement moderne + phrase de passe longue = réseau domestique sain."),
        ("En gestion d'équipe, déléguer demande…", ["De tout vérifier minute par minute", "Un objectif clair, une échéance et un point de suivi", "De choisir la tâche la plus facile"], 1, "Déléguer = confier avec cadre, pas abandonner ni micro-gérer."),
        ("Le e-commerce exige légalement, au minimum…", ["Uniquement un numéro WhatsApp", "Une identité claire du vendeur, des prix affichés et des conditions connues", "Un magasin physique"], 1, "Transparence du vendeur, des prix et des conditions : c'est la base de la confiance."),
        ("L'entretien de recrutement évalue surtout…", ["La tenue vestimentaire uniquement", "Les compétences, l'attitude et la capacité à raconter ses projets", "La mémoire des cours"], 1, "Prépare des exemples concrets de réalisations : c'est ce qui convainc."),
    ],
    "glossaire": [
        ("API REST", "interface web où les verbes HTTP agissent sur des ressources identifiées par URL."),
        ("Backlog", "liste priorisée des fonctionnalités restant à réaliser dans un produit."),
        ("Contrôleur (MVC)", "composant qui reçoit les demandes et coordonne modèle et vue."),
        ("Coût complet", "coût d'un produit incluant les coûts directs et une part des charges indirectes."),
        ("Données personnelles", "toute information permettant d'identifier une personne (nom, téléphone, photo…)."),
        ("HAVING", "clause SQL qui filtre les groupes produits par GROUP BY."),
        ("Index (base)", "structure qui accélère les recherches dans une table."),
        ("LEFT JOIN", "jointure conservant toutes les lignes de la table de gauche."),
        ("Modèle (MVC)", "composant qui gère les données et les règles métier."),
        ("MVP", "produit minimal viable : la plus petite version testable auprès de vrais clients."),
        ("Pitch", "présentation courte et claire d'un projet, centrée sur le problème et la solution."),
        ("Sauvegarde 3-2-1", "3 copies des données, 2 supports différents, 1 copie hors site."),
        ("Vue (MVC)", "composant qui présente les données à l'utilisateur."),
        ("XSS", "attaque par injection de script dans une page consultée par d'autres utilisateurs."),
    ],
    "sujets": [
        ("Sujet d'entraînement n°1 — Application complète (1 heure)",
         "Un club d'étudiants veut gérer ses membres et ses cotisations. 1) Dessine les tables SQL (membres, cotisations) avec leurs liens. 2) Décris les écrans de l'application selon le MVC : quelles vues, quels contrôleurs ? 3) Liste les routes REST nécessaires pour les membres (lister, créer, modifier, supprimer). 4) Écris la requête du total des cotisations par membre.",
         "1) membres (id, nom, filiere), cotisations (id, membre_id → membres.id, montant, date_paiement). 2) Vues : liste, formulaire, détail ; Contrôleurs : Membres, Cotisations ; Modèles : Membre, Cotisation. 3) GET /membres, POST /membres, PUT /membres/{id}, DELETE /membres/{id}. 4) SELECT m.nom, SUM(c.montant) FROM membres m LEFT JOIN cotisations c ON c.membre_id = m.id GROUP BY m.id, m.nom."),
        ("Sujet d'entraînement n°2 — Projet et soutenance (30 minutes)",
         "Tu présentes demain le projet de ta L3 devant un jury. Rédige ton pitch de 2 minutes : le problème, ta solution, ce qui marche aujourd'hui (démonstration), les limites honnêtes et la suite. Ajoute les réponses préparées à deux questions probables du jury : « Pourquoi cette technologie ? » et « Qu'est-ce qui ne marche pas encore ? »",
         "Structure attendue : problème concret vécu par des utilisateurs nommés ; solution en une phrase ; démo courte et fiable ; choix technique justifié par les contraintes (gratuit, compétences de l'équipe, délai) ; limites dites sans honte avec le plan pour les corriger ; conclusion sur ce que le projet t'a appris. Un jury pardonne une limite avouée, jamais une limite découverte."),
        ("Fiche méthode — Préparer son insertion professionnelle dès la L3",
         "Quatre chantiers en parallèle : 1) le CV (une page, projets d'abord, liens GitHub/portfolio) ; 2) la présence en ligne (LinkedIn complet, GitHub propre avec des README clairs) ; 3) les preuves (démos en ligne, captures, recommandations d'enseignants ou de maîtres de stage) ; 4) la pratique d'entretien (présenter un projet en 2 minutes, répondre à « parle-moi de toi », poser des questions intelligentes). Prépare aussi ta liste d'entreprises ciblées et les contacts possibles AVANT la fin des cours : les stages se trouvent souvent par le réseau construit pendant l'année.",
         ""),
    ],
}

L3.append(("Compléments — approfondir et s'entraîner", [
    ("15. Approfondissement SQL : sous-requêtes et vues", [
        "Une sous-requête est une question dans la question : « les étudiants dont la moyenne dépasse la moyenne générale » s'écrit avec un SELECT dans le WHERE comparé à (SELECT AVG(note) FROM notes). Puissant, à utiliser quand une jointure ne suffit pas.",
        "Une vue (VIEW) est une requête enregistrée sous un nom, utilisable comme une table : elle simplifie les requêtes complexes répétées et peut masquer les colonnes sensibles. Le programme et les deux projets du club s'en servent au quotidien.",
    ], "CREATE VIEW notes_etudiants AS SELECT e.nom, n.matiere, n.note FROM etudiants e JOIN notes n ON n.etudiant_id = e.id ; ensuite, SELECT * FROM notes_etudiants devient possible.",
        "Écris la requête « les produits jamais commandés » (table produits, table lignes_commande avec produit_id) — avec une jointure externe ou un NOT IN, au choix.",
        ["Sous-requête = SELECT dans une autre requête.", "Vue = requête enregistrée, lisible comme une table."]),
    ("16. Introduction aux tests logiciels", [
        "Tester, c'est vérifier avant l'utilisateur que le logiciel fait ce qu'il doit. Trois niveaux : les tests unitaires (une fonction), les tests d'intégration (plusieurs morceaux ensemble) et les tests d'acceptation (le parcours complet de l'utilisateur).",
        "Un bon test est écrit comme une phrase : « quand je m'inscris avec un e-mail déjà utilisé, le système refuse avec un message clair ». Écrire le test AVANT le code (TDD) clarifie le besoin et évite une grande partie des erreurs.",
    ], "Notre portail d'emploi a été validé par 13 tests de flux (inscription, connexion, dépôt d'offre, candidature…) : chaque test rejoué après chaque modification garantit qu'on n'a rien cassé.",
        "Écris trois tests d'acceptation pour un formulaire de connexion (cas normal + deux cas d'erreur).",
        ["Unitaire, intégration, acceptation : trois niveaux.", "Tester = prouver que ça marche, pas espérer."]),
    ("17. Culture DevOps : livrer sans casser", [
        "DevOps rapproche développement et exploitation : intégration continue (chaque code poussé est testé automatiquement), déploiement fréquent en petites touches, surveillance des erreurs en production.",
        "Outils de base : Git (historique partagé), un service d'hébergement, et des sauvegardes automatiques. Le principe cardinal : de petits changements fréquents valent mieux qu'une grosse livraison rare et risquée.",
    ], "Publier l'assistant étudiant sur GitHub Pages à chaque petit correctif, après un test, plutôt qu'une « version finale » unique : c'est déjà l'esprit DevOps.",
        "Décris, pour un de tes projets, la chaîne complète : écriture du code → test → publication → vérification en ligne.",
        ["Petits changements, tests automatiques, livraisons fréquentes.", "Git + hébergement + sauvegardes : le socle DevOps."]),
    ("18. Éthique et métiers du numérique", [
        "Le numérique donne du pouvoir — données personnelles, influence des algorithmes, automatisation des emplois — et ce pouvoir appelle une responsabilité : protéger les données confiées, ne pas concevoir de mécanismes trompeurs, signaler les risques que l'on voit.",
        "En entretien comme en poste, cette conscience compte : savoir dire « ce produit collecte plus de données que nécessaire » ou « cette fonctionnalité peut nuire » est une compétence professionnelle, pas une faiblesse.",
    ], "Exemple concret : un site d'emploi qui vendrait la liste des e-mails des candidats à des publicitaires trahirait la confiance qui fait sa valeur — et, souvent, la loi.",
        "Cite un produit numérique que tu utilises et une question éthique qu'il soulève ; propose une réponse équilibrée.",
        ["Données personnelles = responsabilité.", "L'éthique fait partie du métier, pas un supplément."]),
]))

if __name__ == "__main__":
    import sys
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    todo = sys.argv[1:] or ["1", "2", "3"]
    if "1" in todo:
        build_booklet(1, L1, os.path.join(base, "lecons-l1.pdf"), ANNEX_L1, LOIN_L1)
    if "2" in todo and "ANNEX_L2" in globals():
        build_booklet(2, L2, os.path.join(base, "lecons-l2.pdf"), ANNEX_L2, LOIN_L2)
    if "3" in todo and "ANNEX_L3" in globals():
        build_booklet(3, L3, os.path.join(base, "lecons-l3.pdf"), ANNEX_L3, LOIN_L3)
