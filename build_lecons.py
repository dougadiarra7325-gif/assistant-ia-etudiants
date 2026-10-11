# -*- coding: utf-8 -*-
"""Génère les livrets PDF « Leçons essentielles » L1 / L2 / L3 (toutes séries)
pour l'assistant étudiant IAM. Contenu rédigé pour ce projet (résumés de révision)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

NAVY = HexColor("#0b2545")
GOLD = HexColor("#c9a227")
INK = HexColor("#1a1a1a")
MUT = HexColor("#5a6a7f")
LIGHT = HexColor("#eef2f8")

S = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, leading=27, textColor=NAVY),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=11.5, leading=15, textColor=MUT),
    "chap": ParagraphStyle("chap", fontName="Helvetica-Bold", fontSize=14.5, leading=18, textColor=white),
    "h": ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=8, spaceAfter=3),
    "p": ParagraphStyle("p", fontName="Helvetica", fontSize=10.6, leading=14.6, textColor=INK, alignment=TA_LEFT, spaceAfter=5),
    "li": ParagraphStyle("li", fontName="Helvetica", fontSize=10.6, leading=14.6, textColor=INK, leftIndent=10, spaceAfter=2),
    "key": ParagraphStyle("key", fontName="Helvetica-Oblique", fontSize=10.4, leading=14.2, textColor=HexColor("#4a3805")),
    "foot": ParagraphStyle("foot", fontName="Helvetica", fontSize=8.6, leading=11, textColor=MUT, alignment=TA_CENTER),
}


def header(level, series_note):
    flow = []
    t = Table([[Paragraph(f"Leçons essentielles — Licence {level}", S["title"])]],
              colWidths=[170 * mm])
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    flow.append(t)
    flow.append(Paragraph("Toutes séries confondues · Université IAM — Bamako", S["subtitle"]))
    flow.append(Paragraph("Résumés de révision rédigés pour les étudiants — Assistant Étudiant IAM (projet n°11, atelier IAM Code to Career). "
                          "Ces livrets aident à réviser ; ils ne remplacent pas les cours officiels ni les documents des enseignants.", S["subtitle"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(HRFlowable(width="100%", thickness=1.4, color=GOLD))
    flow.append(Spacer(1, 5 * mm))
    return flow


def chapter(title):
    t = Table([[Paragraph(title.upper(), S["chap"])]], colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 2, GOLD),
    ]))
    return [Spacer(1, 5 * mm), t, Spacer(1, 3 * mm)]


def lesson(title, paras, keys):
    flow = [Paragraph(title, S["h"])]
    for p in paras:
        flow.append(Paragraph(p, S["p"]))
    if keys:
        items = "".join(f"• {k}<br/>" for k in keys)
        t = Table([[Paragraph("<b>À retenir</b><br/>" + items, S["key"])]], colWidths=[170 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f7ecd0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ]))
        flow.append(t)
    flow.append(Spacer(1, 2.5 * mm))
    return [KeepTogether(flow)]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8.2)
    canvas.setFillColor(MUT)
    canvas.drawCentredString(A4[0] / 2, 12 * mm,
                             "Assistant Étudiant IAM — Douga dit Ibrahim Diarra (Bronbah Tech) · Page %d" % doc.page)
    canvas.restoreState()


def build(level, chapters, out):
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title=f"Leçons essentielles — Licence {level} (toutes séries)",
                            author="Assistant Étudiant IAM — Douga dit Ibrahim Diarra")
    flow = header(level, "")
    for chap_title, lessons in chapters:
        flow += chapter(chap_title)
        for title, paras, keys in lessons:
            flow += lesson(title, paras, keys)
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print(out, os.path.getsize(out), "octets")


# ================= LICENCE 1 =================
L1 = [
    ("Informatique — les bases", [
        ("1. Qu'est-ce qu'un algorithme ?", [
            "Un algorithme est une suite finie d'instructions précises et ordonnées qui permet de résoudre un problème. Comme une recette de cuisine, il prend des données en entrée, les traite étape par étape et produit un résultat. Tout programme informatique est la traduction d'un algorithme dans un langage que l'ordinateur comprend.",
            "On décrit souvent un algorithme en pseudo-code (langage humain structuré) avant de le coder. Les trois briques de base sont : les séquences (instructions l'une après l'autre), les conditions (si… alors… sinon…) et les boucles (répéter).",
        ], ["Un algorithme doit être précis, fini et correct.", "Pseudo-code d'abord, code ensuite."]),
        ("2. Variables, types et affectation", [
            "Une variable est un nom associé à une zone mémoire qui contient une valeur. L'affectation range une valeur dans la variable (âge ← 20). Les types courants : entier (int), réel (float), chaîne de caractères (string), booléen (vrai/faux).",
            "Bien nommer ses variables (note1, total_ventes) rend le programme lisible. Une expression combine variables et opérateurs (+, −, ×, ÷, modulo) pour calculer un résultat.",
        ], ["Variable = nom + valeur + type.", "Des noms clairs valent mieux que des commentaires."]),
        ("3. Conditions et boucles", [
            "La condition exécute des instructions seulement si un test est vrai : « si note ≥ 10 alors admis sinon recalé ». Les comparaisons utilisent =, ≠, <, >, ≤, ≥, et se combinent avec ET, OU, NON.",
            "Les boucles répètent un bloc : « pour i de 1 à 10 » quand le nombre de tours est connu, « tant que » quand il dépend d'une condition. Piège classique : la boucle infinie, quand la condition ne devient jamais fausse.",
        ], ["Toujours vérifier que la condition d'arrêt arrive.", "Indentations = structure lisible."]),
        ("4. L'ordinateur et le système d'exploitation", [
            "Un ordinateur combine du matériel (processeur, mémoire RAM, disque, écran) et des logiciels. Le processeur exécute les instructions ; la RAM contient le travail en cours et se vide à l'arrêt ; le disque conserve durablement les fichiers.",
            "Le système d'exploitation (Windows, Linux, Android, iOS) fait le lien entre l'utilisateur, les applications et le matériel : il gère les fichiers, la mémoire, les périphériques et la sécurité de base.",
        ], ["RAM = temporaire et rapide ; disque = durable.", "L'OS est le chef d'orchestre de la machine."]),
    ]),
    ("Mathématiques et statistiques", [
        ("5. Ensembles et logique de base", [
            "Un ensemble est une collection d'éléments distincts (ex. les étudiants d'une classe). Opérations : union (∪), intersection (∩), complémentaire. La logique étudie les propositions vraies ou fausses et leurs combinaisons (ET, OU, NON, implication) — c'est le socle des conditions en programmation.",
        ], ["∩ = éléments communs ; ∪ = tous les éléments.", "La table de vérité tranche les doutes."]),
        ("6. Statistique descriptive", [
            "La statistique descriptive résume des données : la moyenne (somme ÷ effectif), la médiane (valeur du milieu quand on trie), le mode (valeur la plus fréquente) et l'étendue (max − min). Les graphiques (barres, courbes, camemberts) rendent ces résumés lisibles.",
            "Exemple : notes 9, 12, 15 → moyenne 12 ; médiane 12. Avec des coefficients, on utilise la moyenne pondérée : Σ(note × coef) ÷ Σ(coef).",
        ], ["Moyenne sensible aux valeurs extrêmes ; médiane plus robuste.", "Un graphique se choisit selon le message."]),
    ]),
    ("Gestion et économie", [
        ("7. Introduction à l'économie", [
            "L'économie étudie les choix des individus, des entreprises et des États face à des ressources limitées. Deux notions de base : l'offre (ce que les producteurs proposent) et la demande (ce que les acheteurs veulent) ; leur rencontre forme les prix sur un marché.",
            "On distingue la microéconomie (comportements individuels) et la macroéconomie (croissance, chômage, inflation d'un pays entier).",
        ], ["Rareté des ressources ⇒ nécessité de choisir.", "Prix = rencontre de l'offre et de la demande."]),
        ("8. Comptabilité générale — les principes", [
            "La comptabilité enregistre toutes les opérations d'une entreprise. Principe fondamental : toute opération a une ressource et un emploi — c'est la partie double : chaque écriture au débit a sa contrepartie au crédit, pour les mêmes montants.",
            "Les documents clés : le journal (enregistrements chronologiques), le grand-livre (par compte), la balance, puis le bilan (photographie du patrimoine : actif = passif) et le compte de résultat (produits − charges = bénéfice ou perte).",
        ], ["Total débit = total crédit, toujours.", "Bilan = patrimoine ; résultat = performance de la période."]),
    ]),
    ("Communication et méthodologie", [
        ("9. Prendre des notes et travailler à l'université", [
            "À l'université, l'autonomie est la règle : les cours magistraux donnent la structure, le travail personnel fait la différence. Prends des notes avec tes mots, note les exemples, puis relis le soir même pendant 10 minutes — c'est là que la mémoire se fixe.",
            "Le système LMD organise l'année en 2 semestres, les cours en unités d'enseignement (UE) qui rapportent des crédits capitalisables : une UE validée est acquise définitivement.",
        ], ["Relire le jour même = révision la plus rentable.", "180 crédits = la Licence complète."]),
        ("10. Anglais — vocabulaire technique de base", [
            "Quelques mots incontournables : computer (ordinateur), software (logiciel), hardware (matériel), network (réseau), file (fichier), folder (dossier), password (mot de passe), data (données), screen (écran), to download (télécharger), to save (enregistrer).",
            "Méthode : apprends 5 mots par jour en les utilisant dans une phrase. La documentation technique et les meilleurs tutoriels sont en anglais : c'est un investissement direct pour ta carrière.",
        ], ["5 mots par jour = plus de 1 500 mots en 10 mois.", "L'anglais technique se lit d'abord, se parle ensuite."]),
    ]),
]


# ================= LICENCE 2 =================
L2 = [
    ("Programmation", [
        ("1. Python — fonctions, listes et dictionnaires", [
            "Une fonction regroupe un traitement réutilisable : def moyenne(notes): return sum(notes)/len(notes). Les listes stockent des collections ordonnées (notes = [12, 14, 9]) avec indexation à partir de 0, ajout (append) et parcours par boucle for.",
            "Les dictionnaires associent des clés à des valeurs : etudiant = {\"nom\": \"Awa\", \"note\": 15}. C'est la structure idéale pour représenter des fiches, des produits ou des paramètres. Combine fonctions + structures de données et tu peux résoudre la plupart des exercices de L2.",
        ], ["Découper le problème en petites fonctions testables.", "Liste = collection ordonnée ; dictionnaire = clé → valeur."]),
        ("2. La programmation orientée objet (bases)", [
            "La POO organise le code autour d'objets : une classe définit un modèle (attributs + méthodes), chaque objet est une instance de la classe. Exemple : la classe Etudiant (nom, matricule) avec la méthode se_presenter().",
            "Trois piliers : l'encapsulation (protéger les données), l'héritage (une classe spécialise une autre) et le polymorphisme (même interface, comportements différents). La POO paie quand les programmes grandissent.",
        ], ["Classe = moule ; objet = exemplaire fabriqué avec le moule.", "Modéliser d'abord les « choses » du problème."]),
    ]),
    ("Développement web et bases de données", [
        ("3. HTML, CSS, JavaScript — le trio du web", [
            "HTML structure la page (titres, paragraphes, formulaires), CSS la met en forme (couleurs, dispositions, responsive) et JavaScript la rend interactive (réagir aux clics, vérifier un formulaire, modifier la page sans la recharger). Un site moderne sépare toujours ces trois rôles.",
            "Le navigateur interprète ces trois langages côté client. Pour les données et les comptes, on ajoute un langage serveur (PHP, Python, Node.js) et une base de données.",
        ], ["Structure (HTML) ≠ style (CSS) ≠ comportement (JS).", "Penser « mobile d'abord » pour l'affichage."]),
        ("4. PHP et SQL — sites dynamiques", [
            "PHP s'exécute sur le serveur : il reçoit les formulaires, interroge la base de données et génère la page HTML envoyée au navigateur. Avec SQL, quatre ordres dominent : SELECT (lire), INSERT (ajouter), UPDATE (modifier), DELETE (supprimer).",
            "Exemple : SELECT nom, note FROM etudiants WHERE note >= 10 ORDER BY note DESC ; — lit les admis du meilleur au moins bon. Règle de sécurité absolue : ne jamais coller directement les saisies des utilisateurs dans une requête (injection SQL) ; utiliser des requêtes préparées.",
        ], ["Toujours des requêtes préparées contre l'injection SQL.", "Tester chaque requête dans la base avant de la coder."]),
        ("5. Modèle relationnel et clés", [
            "Une base relationnelle range les données dans des tables (lignes = enregistrements, colonnes = attributs). Chaque ligne est identifiée par une clé primaire unique ; une clé étrangère relie les tables entre elles (ex. la commande d'un client).",
            "Bien modéliser, c'est éviter les doublons : une information = un seul endroit. On parle de normalisation : elle protège contre les incohérences quand les données évoluent.",
        ], ["Clé primaire = identifiant unique de la ligne.", "Pas de doublons : une info, une place."]),
    ]),
    ("Systèmes et réseaux", [
        ("6. Réseaux — IP, LAN, WAN et services", [
            "Chaque machine d'un réseau possède une adresse IP qui l'identifie. Le LAN relie les appareils d'un même lieu (domicile, campus) via un switch ou un routeur ; le WAN relie des réseaux distants — Internet est le WAN mondial.",
            "Services indispensables : le DNS traduit les noms (exemple.com) en adresses IP ; le DHCP distribue automatiquement les adresses ; le protocole HTTP/HTTPS transporte les pages web (HTTPS = chiffré, à toujours préférer).",
        ], ["DNS = l'annuaire d'Internet.", "HTTPS partout, surtout pour les mots de passe."]),
        ("7. Systèmes d'exploitation — processus et fichiers", [
            "L'OS exécute des programmes sous forme de processus, partage le processeur entre eux (ordonnancement) et alloue la mémoire. Il organise le stockage en arborescence de dossiers et gère les droits d'accès (lire, écrire, exécuter) par utilisateur.",
            "Sous Linux, la ligne de commande est un outil professionnel : ls (lister), cd (naviguer), mkdir (créer un dossier), cp/mv (copier/déplacer), grep (chercher dans les fichiers).",
        ], ["Un processus = un programme en cours d'exécution.", "Les droits d'accès sont la première ligne de sécurité."]),
    ]),
    ("Gestion, marketing et probabilités", [
        ("8. Marketing digital — les fondamentaux", [
            "Le marketing digital fait connaître une offre sur internet : présence sur les réseaux sociaux, contenus utiles, publicité ciblée, référencement. Le parcours client type : découvrir → s'intéresser → faire confiance → acheter → recommander.",
            "On mesure tout : vues, clics, messages, ventes. Un petit commerce de Bamako peut commencer simplement : une page propre, des réponses rapides sur WhatsApp et des publications régulières valent mieux qu'une grosse campagne rare.",
        ], ["Régularité et réponses rapides battent les gros budgets rares.", "Ce qui ne se mesure pas ne s'améliore pas."]),
        ("9. Probabilités — l'essentiel", [
            "La probabilité d'un événement est un nombre entre 0 et 1 : nombre de cas favorables ÷ nombre de cas possibles (événements équiprobables). Exemple : obtenir un 6 avec un dé équilibré = 1/6 ≈ 16,7 %.",
            "Deux règles utiles : la probabilité du contraire vaut 1 − p ; pour deux événements indépendants qui doivent se produire ensemble, on multiplie leurs probabilités. Attention aux événements qui s'influencent : l'indépendance n'est pas automatique.",
        ], ["P(contraire) = 1 − P(événement).", "Indépendants ⇒ on multiplie ; sinon, prudence."]),
        ("10. Trésorerie et budget", [
            "La trésorerie est l'argent disponible tout de suite. Suivre ses entrées et sorties chaque semaine évite les mauvaises surprises : une activité rentable peut mourir d'un simple trou de trésorerie si les clients paient tard et les charges tout de suite.",
            "Outil simple et efficace : un tableau de suivi (date, libellé, entrée, sortie, solde) — sur papier, dans Excel ou dans une application. Le même réflexe sert pour un budget d'étudiant.",
        ], ["Rentabilité ≠ trésorerie : surveille les dates de paiement.", "Un solde suivi chaque semaine = zéro surprise."]),
    ]),
    ("Projet et insertion", [
        ("11. Gestion de projet — réussir un projet d'équipe", [
            "Un projet réussi tient en quatre habitudes : un objectif écrit en une phrase, des tâches découpées et attribuées (qui fait quoi pour quand), un point d'avancement court et régulier, et une démonstration testée avant le jour J — jamais la veille au soir.",
            "Versionne ton code sur Git/GitHub dès le premier jour : historique, travail à plusieurs sans s'écraser, et preuve publique de ton travail pour les recruteurs.",
        ], ["Découper, attribuer, dater, vérifier.", "Git dès le jour 1, pas la veille de la démo."]),
    ]),
]


# ================= LICENCE 3 =================
L3 = [
    ("Informatique avancée", [
        ("1. Génie logiciel — le cycle de vie", [
            "Un logiciel professionnel suit un cycle : analyse des besoins, conception, développement, tests, déploiement, maintenance. Sauter l'analyse est la première cause d'échec : on construit vite… le mauvais produit.",
            "Les méthodes agiles découpent le travail en petites livraisons fréquentes (sprints) avec retours des utilisateurs, plutôt qu'un énorme livrable unique à la fin. La documentation minimale utile : besoins, architecture, guide d'utilisation.",
        ], ["Comprendre le besoin avant de coder.", "Petites livraisons testées > gros tunnel sans retour."]),
        ("2. POO avancée et bonnes pratiques", [
            "En L3, on juge la qualité du code : noms explicites, fonctions courtes, responsabilités séparées (une classe = un rôle), gestion propre des erreurs. L'héritage doit rester rare et justifié ; la composition (assembler des objets) est souvent préférable.",
            "Les tests automatisés (au minimum : tester les fonctions critiques avec des cas normaux et des cas limites) transforment la peur de modifier le code en confiance.",
        ], ["Du code qu'on relit facilement est du code professionnel.", "Tester les cas limites, pas seulement le cas parfait."]),
        ("3. Sécurité informatique — menaces et défenses", [
            "Menaces courantes : phishing, mots de passe réutilisés, logiciels non mis à jour, injections SQL, pièces jointes piégées. La défense est en couches : authentification forte, droits minimums, sauvegardes testées, mises à jour, et utilisateurs formés — l'humain est le maillon le plus attaqué.",
            "Pour un développeur : valider toutes les entrées, hacher les mots de passe (jamais en clair), utiliser HTTPS, et ne jamais coder de secret (clé, mot de passe) dans le code source.",
        ], ["Un mot de passe ne se stocke jamais en clair.", "Sauvegarde non testée = sauvegarde imaginaire."]),
        ("4. Données et intelligence artificielle — panorama", [
            "L'IA moderne repose sur les données : collecter, nettoyer, représenter, puis entraîner des modèles qui détectent des régularités (classification, prédiction, génération de texte). La qualité des données décide de la qualité du résultat — « garbage in, garbage out ».",
            "Les grands modèles de langage (comme ceux des assistants IA) prédisent le texte le plus plausible : puissants pour expliquer, résumer et coder, mais ils peuvent se tromper avec assurance. Tout fait important produit par une IA doit être vérifié — surtout les dates, les chiffres et les sources officielles.",
        ], ["Données propres > modèle compliqué.", "Une réponse d'IA se vérifie avant de s'utiliser."]),
    ]),
    ("Gestion et droit", [
        ("5. Management et ressources humaines", [
            "Manager, c'est obtenir des résultats avec et par les autres : fixer des objectifs clairs, déléguer avec confiance, suivre sans étouffer, donner des retours honnêtes. Les RH structurent le parcours des personnes : recrutement, intégration, formation, évaluation, paie et climat de travail.",
            "Deux leviers souvent sous-estimés : la reconnaissance (dire ce qui est bien fait, précisément) et la clarté (chacun sait ce qu'on attend de lui et pour quand).",
        ], ["Objectif flou = résultat flou.", "Déléguer, c'est confier le résultat, pas seulement les tâches."]),
        ("6. Droit des affaires — notions clés", [
            "L'entreprise a une forme juridique (entreprise individuelle, SARL, SA…) qui détermine responsabilités et démarches. Le contrat est l'outil central : un accord écrit clair (qui fait quoi, pour quel prix, quels délais, que se passe-t-il en cas de problème) évite la plupart des litiges.",
            "Au Mali, l'immatriculation au Registre du Commerce et du Crédit Mobilier (RCCM) officialise l'activité et ouvre des droits (comptes professionnels, vérifications de plateformes, marchés publics).",
        ], ["Un bon contrat écrit vaut mieux qu'un long procès.", "Le RCCM est la porte d'entrée de la vie officielle d'une entreprise."]),
    ]),
    ("Mémoire et insertion professionnelle", [
        ("7. Méthodologie du mémoire", [
            "Le mémoire suit une architecture stable : introduction (contexte, problématique, hypothèses, plan), partie théorique (ce que dit la littérature), partie pratique (terrain, données, analyse), conclusion (réponse à la problématique, limites, pistes). La problématique — une vraie question à laquelle le mémoire répond — est le cœur du travail.",
            "Planning qui marche : sujet et plan détaillé dès le premier mois, recherche documentaire régulière, rédaction par petits blocs chaque semaine, relecture par un pair, et entraînement oral pour la soutenance. Commencer tard est l'erreur n°1 des mémoires.",
        ], ["Pas de problématique, pas de mémoire.", "Écrire chaque semaine bat écrire tout le dernier mois."]),
        ("8. CV, entretien et réseau professionnel", [
            "En fin de Licence, ton CV doit montrer des preuves : projets avec liens (GitHub, démos), stages, compétences précises. En entretien, la structure qui convainc : présente-toi en 30 secondes, raconte un projet (problème → ce que tu as fait → résultat), sois honnête sur ton niveau et curieux sur le poste.",
            "LinkedIn et GitHub sont ton vitrine permanente : photo professionnelle, titre clair, projets épinglés. Le réseau se construit en rendant service et en restant visible — pas seulement le jour où tu cherches un stage.",
        ], ["Des liens valent mieux que des adjectifs.", "Le réseau se cultive avant d'en avoir besoin."]),
    ]),
]

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    build(1, L1, os.path.join(base, "lecons-l1.pdf"))
    build(2, L2, os.path.join(base, "lecons-l2.pdf"))
    build(3, L3, os.path.join(base, "lecons-l3.pdf"))
