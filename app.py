# -*- coding: utf-8 -*-
"""
Assistant IA pour étudiants — Projet n°11 (atelier IAM Code to Career).
Chatbot en français qui répond aux questions fréquentes des étudiants de l'Université IAM :
emplois du temps, examens, procédures administratives, règlements, atelier Code to Career.
Moteur : base de questions/réponses (SQLite) + recherche par mots-clés normalisée.
Les questions sans réponse sont journalisées ; l'administrateur enrichit la base depuis l'espace admin.
Auteur : Douga dit Ibrahim Diarra — Université IAM, Bamako.
"""
import io
import csv
import json
import os
import re
import sqlite3
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from functools import wraps

from flask import (Flask, Response, abort, flash, g, jsonify, redirect,
                   render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE, "assistant.db"))
OWNER_EMAIL = "dougadiarra7325@gmail.com"
CATEGORIES = ["Atelier Code to Career", "Emplois du temps", "Examens",
              "Administration", "Règlements", "Études et orientation", "Divers"]

SEED_QNA = [
    # ---------------- Atelier Code to Career ----------------
    ("Atelier Code to Career", "C'est quoi l'atelier IAM Code to Career ?",
     "code to career,atelier,code career,c2c",
     "IAM Code to Career est un atelier intensif organisé par l'Université IAM (Institut Africain de Management) de Bamako et piloté par DataInsights. Pendant une semaine, les étudiants en informatique (L1 à L3) travaillent sur la pratique industrielle, le recrutement IT, la programmation, les agents IA, le personal branding et un projet d'équipe à présenter à la fin."),
    ("Atelier Code to Career", "Quels sont les horaires de l'atelier ?",
     "horaire,heures,heure,quand commence,quand finit,emploi du temps atelier",
     "L'atelier a lieu du lundi au vendredi : de 9h00 à 15h00, sauf le vendredi de 9h00 à 13h00. Sois à l'heure : chaque journée commence par une session d'ouverture d'environ 1h30 à 2h sur la pratique industrielle et le recrutement IT."),
    ("Atelier Code to Career", "Qui dirige l'atelier Code to Career ?",
     "chef,dirige,responsable,encadrant,abdoulaye,traore,datainsights",
     "L'atelier est piloté par DataInsights. Le chef d'atelier est Abdoulaye TRAORE, Responsable IT. Écoute bien ses consignes : c'est lui qui valide les projets des équipes."),
    ("Atelier Code to Career", "Quels sont les projets d'équipe proposés ?",
     "projets,liste des projets,projet equipe,choisir projet,themes",
     "Il y a 12 projets : 1) Souscription aux assurances, 2) Découvrir le Mali (tourisme), 3) Entreprises et prestataires, 4) Offres d'emploi au Mali, 5) Agriculteurs et acheteurs, 6) Base de données des corps armés, 7) Portefeuille mobile, 8) Rendez-vous médicaux, 9) Marketplace de l'artisanat malien, 10) Gestion scolaire, 11) Assistant IA pour étudiants, 12) Portfolio et CV en ligne. Chaque équipe choisit selon son niveau (L1, L2, L3)."),
    ("Atelier Code to Career", "Qu'est-ce qu'on doit livrer à la fin de l'atelier ?",
     "livrable,livrables,delivrer,rendre,final,presentation,demo,github",
     "Chaque équipe doit livrer : une démonstration fonctionnelle de son projet, le code versionné sur GitHub, une présentation courte devant le groupe, et le projet intégré au CV et au profil en ligne de chaque membre. Prépare ta démo à l'avance et teste-la avant le jour J."),
    ("Atelier Code to Career", "Pourquoi on nous demande un profil LinkedIn et GitHub ?",
     "linkedin,github,profil,personal branding,pourquoi linkedin",
     "Parce que les recruteurs IT regardent les profils en ligne avant les CV. Un profil GitHub avec des projets réels et un LinkedIn complet (photo, parcours, projets) montrent ce que tu sais faire. L'atelier consacre un module entier au personal branding : LinkedIn, GitHub et portfolio."),
    ("Atelier Code to Career", "C'est quoi le pitch de 30 secondes ?",
     "pitch,presentation 30,presenter,se presenter",
     "Le pitch de 30 secondes sert à te présenter comme un pro : ton nom, ton niveau (ex. Licence 2 informatique à l'IAM), ce que tu sais faire, un ou deux projets concrets, et ton objectif. Exemple de structure : « Bonjour, je m'appelle …, étudiant en … à l'IAM. Je travaille sur … . Mon objectif est … . » Entraîne-toi à voix haute jusqu'à le dire naturellement."),
    # ---------------- Emplois du temps ----------------
    ("Emplois du temps", "Où trouver mon emploi du temps ?",
     "emploi du temps,planning,horaire cours,edt,salle",
     "Les emplois du temps des cours sont affichés par l'administration de l'université (panneaux d'affichage et secrétariat de ton département). Pendant la semaine de l'atelier Code to Career, l'horaire est fixe : 9h00-15h00 (vendredi 9h00-13h00). Pense à photographier l'emploi du temps officiel dès qu'il est affiché."),
    ("Emplois du temps", "À quelle heure commencent les cours ?",
     "heure cours,commence,debut cours,matin",
     "Pendant l'atelier Code to Career, les journées commencent à 9h00 précises. Pour les cours ordinaires, l'heure de début dépend de ton emploi du temps officiel affiché par l'administration — vérifie-le chaque semaine, il peut changer."),
    ("Emplois du temps", "Que faire si je suis en retard ou absent ?",
     "retard,absent,absence,justifier,manquer cours",
     "Préviens ton enseignant ou le secrétariat dès que possible et justifie ton absence avec un document (certificat médical, attestation). Les absences non justifiées peuvent jouer sur ton assiduité et ton accès aux examens. Pendant l'atelier, les retards répétés sont très mal vus par les encadrants."),
    # ---------------- Examens ----------------
    ("Examens", "Quand ont lieu les examens ?",
     "examens,dates examens,compositions,session,partiels",
     "Les dates exactes des examens sont fixées et affichées par l'administration de l'IAM (affichage officiel et secrétariat). Je n'ai pas le calendrier officiel des sessions dans ma base : vérifie le panneau d'affichage de ton département et note les dates dès leur publication."),
    ("Examens", "Comment bien réviser pour les examens ?",
     "reviser,preparer examen,conseils revision,apprendre,methodes",
     "Méthode qui marche : 1) relis tes cours chaque semaine au lieu de tout découvrir la veille ; 2) refais les exercices et les TP sans regarder la correction ; 3) explique la notion à voix haute comme à un camarade ; 4) dors suffisamment la veille. Pour la programmation : code un peu chaque jour, c'est la pratique qui compte."),
    ("Examens", "Que se passe-t-il en cas de fraude à un examen ?",
     "fraude,triche,tricher,copier,sanction examen",
     "La fraude aux examens (copie, téléphone, documents interdits) est une faute grave dans toutes les universités : elle peut entraîner l'annulation de l'épreuve, un zéro, voire des sanctions disciplinaires. Ne prends jamais ce risque — un échec se rattrape, une exclusion non."),
    # ---------------- Administration ----------------
    ("Administration", "Comment s'inscrire ou se réinscrire à l'IAM ?",
     "inscription,reinscription,s inscrire,inscrire,dossier inscription",
     "L'inscription et la réinscription se font au secrétariat de l'université pendant les périodes officielles annoncées par l'administration. Prépare ton dossier (pièce d'identité, diplômes/attestations, photos, frais d'inscription) et respecte les délais affichés : les retardataires paient parfois des pénalités. Pour la liste exacte des pièces, demande au secrétariat."),
    ("Administration", "Comment obtenir un certificat de scolarité ?",
     "certificat,scolarite,attestation,document",
     "Le certificat de scolarité se demande au secrétariat de l'université, en général avec ta carte d'étudiant ou une pièce d'identité. Prévois un délai de traitement de quelques jours et, selon les cas, des frais de timbre. Anticipe : ne le demande pas la veille du jour où tu en as besoin."),
    ("Administration", "Comment obtenir mon relevé de notes ?",
     "releve,notes,bulletin,releve de notes,resultats",
     "Les relevés de notes sont délivrés par le secrétariat après la publication officielle des résultats et les délibérations. Présente-toi avec ta carte d'étudiant. Si tu constates une erreur sur ton relevé, signale-la rapidement au secrétariat avec tes preuves (copies d'examen, notes de TP)."),
    ("Administration", "J'ai perdu ma carte d'étudiant, que faire ?",
     "carte,perdu,perte,carte etudiant,refaire",
     "Déclare la perte au secrétariat de l'université dès que possible : on t'indiquera la procédure pour refaire la carte (déclaration, photo, frais éventuels). En attendant, garde une pièce d'identité officielle sur toi pour les contrôles et les examens."),
    ("Administration", "Comment contacter l'administration de l'IAM ?",
     "contacter,secretariat,administration,telephone,bureau,accueil",
     "Le point de contact principal est le secrétariat / l'accueil de l'Université IAM à Bamako, aux heures d'ouverture des bureaux. Pour une démarche précise (certificat, relevé, inscription), présente-toi en personne avec ta carte d'étudiant : c'est le moyen le plus rapide d'avoir une réponse fiable."),
    # ---------------- Règlements ----------------
    ("Règlements", "Quelles sont les règles de vie à l'université ?",
     "reglement,regles,discipline,comportement,interieur",
     "Les règles générales : respecter les enseignants, le personnel et les camarades ; être assidu et ponctuel ; prendre soin du matériel ; garder les salles propres ; respecter le règlement intérieur affiché par l'administration. Le règlement officiel complet est disponible au secrétariat — mes réponses donnent les principes généraux, pas le texte officiel."),
    ("Règlements", "L'assiduité compte-t-elle pour les examens ?",
     "assiduite,presence,obligatoire,absences examens",
     "Oui : dans la plupart des formations, une assiduité insuffisante peut empêcher de composer ou entraîner des pénalités. Justifie toujours tes absences auprès du secrétariat et garde tes justificatifs."),
    # ---------------- Études et orientation ----------------
    ("Études et orientation", "Quels langages apprend-on à l'atelier ?",
     "langages,python,javascript,java,php,sql,programmation atelier",
     "L'atelier couvre Python, JavaScript, Java, PHP et SQL, en plus de Git/GitHub, des agents IA et des modules de recrutement (CV, entretiens, réseautage). Si tu débutes sur un langage, commence par les bases et pratique sur un petit projet : c'est exactement l'esprit des 12 projets d'équipe."),
    ("Études et orientation", "Quels métiers après une Licence informatique ?",
     "metiers,debouches,emploi informatique,carriere,developpeur",
     "Après une Licence en informatique : développeur web ou mobile, technicien systèmes et réseaux, administrateur de bases de données, support IT, data analyst junior, community manager tech, ou poursuite en Master. Ce qui fait la différence à la sortie : des projets réels à montrer (GitHub), un bon profil LinkedIn et des stages."),
    ("Études et orientation", "Comment créer un bon CV d'étudiant ?",
     "cv,curriculum,faire cv,modele cv",
     "Un bon CV d'étudiant tient sur une page : nom complet, contact, formation, compétences techniques, projets (avec liens GitHub), expériences (stages, projets personnels) et langues. Mets tes projets en avant plutôt que de longues phrases. Astuce : un portfolio en ligne lié au CV renforce beaucoup ta candidature."),
    # ---------------- Divers ----------------
    ("Divers", "Qui es-tu ?",
     "qui es tu,ton nom,tu es qui,assistant,bot",
     "Je suis l'assistant des étudiants de l'IAM, créé dans le cadre du projet n°11 de l'atelier IAM Code to Career. Je réponds aux questions fréquentes des étudiants : atelier, emplois du temps, examens, démarches administratives et orientation. Pose-moi une question !"),
    ("Divers", "Qui t'a créé ?",
     "cree,createur,qui a fait,auteur,douga",
     "J'ai été conçu par Douga dit Ibrahim Diarra, étudiant en Licence 2 informatique à l'Université IAM de Bamako, comme projet n°11 de l'atelier IAM Code to Career (prototype fonctionnel avec base de questions/réponses enrichissable par l'administrateur)."),
    ("Divers", "Que sais-tu faire ?",
     "que sais tu,sais tu faire,fonctionnalites,aide,que peux tu",
     "Je peux répondre sur : l'atelier IAM Code to Career (horaires, projets, livrables, pitch), les emplois du temps, les examens, les démarches administratives (inscription, certificat de scolarité, relevé de notes, carte d'étudiant), les règlements généraux et l'orientation en informatique. Si je n'ai pas la réponse, je note ta question pour que l'équipe l'ajoute à ma base."),
    # ---------------- IAM, filières et CV ----------------
    ("IAM et filières", "C'est quoi l'IAM ?",
     "iam,c est quoi iam,institut africain de management,universite iam,ecole iam,groupe iam",
     "L'IAM, c'est l'Institut Africain de Management : un groupe d'enseignement supérieur présent notamment au Sénégal et au Mali. À Bamako, l'Université IAM forme des étudiants dans des parcours liés à la gestion, au droit, à la communication et à l'informatique. C'est aussi là que se déroule l'atelier IAM Code to Career."),
    ("IAM et filières", "Quelles sont les filières de l'IAM ?",
     "filieres,filiere,formations,programmes,parcours,diplomes,bba,big,mib,mba,gbba",
     "Dans les parcours associés au Groupe IAM, on retrouve notamment : BBA/GBBA, BIG et Master Informatique, Droit, Communication & Digital Business, Banque & Ingénierie Financière, Comptabilité-Contrôle-Audit, Gestion des Ressources Humaines / Capital Humain, Marketing & Intelligence d'Affaires, Logistique / Supply Chain, Management de la Qualité, ainsi que des parcours MBA, DBA, MIB et MIAF. Les filières ouvertes peuvent varier selon le campus et l'année : confirme toujours la liste actuelle auprès de l'administration."),
    ("IAM et filières", "Quelle filière choisir pour travailler dans l'informatique ?",
     "filiere informatique,choisir filiere info,big,informatique de gestion,master informatique,orientation informatique",
     "Pour travailler dans l'informatique, vise un parcours informatique comme BIG ou Master Informatique quand ils sont ouverts sur ton campus. Ce qui compte ensuite : programmation (Python, JavaScript, PHP, SQL), projets réels sur GitHub, portfolio, stages et capacité à présenter ton travail."),
    ("CV et candidature", "Que mettre dans un CV d'étudiant ?",
     "mettre,mettre cv,contenu,sections,rubriques,composer,contenu cv,sections cv,rubriques cv,quoi mettre,composer cv",
     "Un CV d'étudiant clair contient : 1) en-tête avec nom complet, téléphone, e-mail, ville et liens GitHub/LinkedIn/portfolio ; 2) un profil de 2 lignes ; 3) formation ; 4) compétences techniques ; 5) projets avec liens ; 6) expériences ou stages ; 7) langues et centres d'intérêt utiles. Reste sur une page si tu es étudiant."),
    ("CV et candidature", "Aide-moi à écrire mon CV",
     "aide cv,ecrire cv,rediger cv,faire mon cv,commencer cv,preparer cv",
     "Je peux t'aider à structurer ton CV. Prépare ces informations : nom complet, filière et niveau, objectif professionnel, compétences, projets (avec liens GitHub ou portfolio), expériences/stages, langues. Ensuite suis cet ordre : en-tête, profil court, formation, compétences, projets, expériences, langues. Pour chaque projet, écris : le nom, les technologies utilisées, ce que l'application fait et le lien pour la voir."),
    ("CV et candidature", "Comment présenter mes projets dans un CV ?",
     "projets cv,decrire projet,presenter projet,portfolio cv,github cv,lien projet",
     "Présente chaque projet en 2 lignes maximum : le nom du projet, la technologie, le problème résolu et le résultat. Exemple : « Assistant IA pour étudiants — Flask, SQLite, GitHub Pages : chatbot qui répond aux questions des étudiants de l'IAM, avec base documentée et vraie IA Gemini activable. » Ajoute toujours le lien GitHub ou la démo si elle existe."),
    ("Divers", "Bonjour",
     "bonjour,salut,bonsoir,hello,coucou",
     "Bonjour ! Je suis l'assistant des étudiants de l'IAM. Je peux t'aider sur l'IAM et ses filières, l'atelier Code to Career, les cours, les examens, les démarches administratives, les CV et l'orientation. Pose-moi ta question."),
    ("Divers", "Qui est Douga dit Ibrahim Diarra ?",
     "douga,ibrahim diarra,qui est douga,diarra,createur du site,auteur du projet",
     "Douga dit Ibrahim Diarra est un étudiant en Licence 2 informatique à l'Université IAM de Bamako et le créateur de cet assistant (projet n°11 de l'atelier IAM Code to Career). Il a aussi construit un portfolio en ligne et un portail d'offres d'emploi au Mali dans le même atelier, et il développe Bronbah Tech."),
    ("Divers", "Peux-tu discuter avec moi ?",
     "discuter,conversation,parler,question generale,autre sujet,discute",
     "Oui, on peut discuter. Je suis surtout entraîné pour les sujets étudiants : IAM, filières, cours, examens, CV, portfolio, projets et orientation. Si la vraie IA est activée sur cet appareil, je peux aussi répondre à des questions plus générales ; sinon, je réponds avec ma base documentée et je te dis honnêtement quand je ne sais pas."),
    # ---------------- Définitions et filières ----------------
    ("Définitions et filières", "C'est quoi l'informatique ?",
     "informatique,c est quoi informatique,definition informatique,science informatique",
     "L'informatique est la science du traitement automatique de l'information par les ordinateurs. Elle couvre la programmation, les réseaux, les bases de données, les systèmes, la cybersécurité et l'intelligence artificielle. À l'IAM, la filière informatique (BIG, Master Informatique) prépare à des métiers comme développeur, administrateur réseaux ou data analyst."),
    ("Définitions et filières", "C'est quoi un algorithme ?",
     "algorithme,c est quoi algorithme,definition algorithme",
     "Un algorithme est une suite d'instructions précises et ordonnées qui permet de résoudre un problème ou d'accomplir une tâche. Imagine une recette de cuisine : des étapes à suivre dans l'ordre pour obtenir un résultat. Tout programme informatique est construit à partir d'algorithmes."),
    ("Définitions et filières", "C'est quoi le BBA ?",
     "bba,c est quoi bba,bachelor,business administration,administration des affaires",
     "Le BBA (Bachelor of Business Administration) est une licence en administration des affaires : une formation généraliste en gestion d'entreprise — management, marketing, finance, comptabilité et ressources humaines. C'est la voie classique pour travailler en entreprise ou créer sa propre activité."),
    ("Définitions et filières", "C'est quoi le GBBA ?",
     "gbba,global bba,c est quoi gbba",
     "Le GBBA (Global BBA) est la version internationale du BBA : le même socle en gestion d'entreprise, avec une dimension internationale renforcée (langues, ouverture sur l'étranger). Il prépare à des carrières de management dans des contextes multiculturels."),
    ("Définitions et filières", "C'est quoi un MBA ?",
     "mba,c est quoi mba,master business,dbà,dba",
     "Le MBA (Master of Business Administration) est un diplôme de niveau master en management, souvent suivi après quelques années d'expérience professionnelle. Il sert à monter en compétences pour diriger des équipes ou des entreprises. Le DBA est son équivalent de niveau doctorat pour les cadres."),
    ("Définitions et filières", "C'est quoi la filière Droit ?",
     "droit,filiere droit,juriste,avocat,sciences juridiques",
     "La filière Droit forme aux règles qui organisent la société et les affaires : droit privé, droit public, droit des affaires, droit du travail. Débouchés : juriste d'entreprise, métiers de la justice (avec les concours et étapes requis), administration, banques et assurances."),
    ("Définitions et filières", "C'est quoi le marketing ?",
     "marketing,c est quoi marketing,mercatique",
     "Le marketing, c'est l'ensemble des méthodes pour comprendre les clients et leur proposer la bonne offre : étudier le marché, définir le produit, le prix, la distribution et la communication. Aujourd'hui, une grande partie se fait en ligne : c'est le marketing digital."),
    ("Définitions et filières", "C'est quoi la comptabilité ?",
     "comptabilite,c est quoi comptabilite,comptable,audit",
     "La comptabilité consiste à enregistrer, classer et analyser toutes les opérations financières d'une entreprise (achats, ventes, salaires, impôts) pour produire des documents fiables : journal, bilan, compte de résultat. Débouchés : comptable, auditeur, contrôleur de gestion."),
    ("Définitions et filières", "C'est quoi la finance et la banque ?",
     "finance,banque,c est quoi finance,ingenierie financiere,epargne,credit,investissement",
     "La finance s'occupe de gérer l'argent : épargne, crédit, investissement, budget et risques. La filière Banque & Ingénierie Financière prépare aux métiers des banques, des assurances et des services financiers (conseiller clientèle, analyste, gestionnaire)."),
    ("Définitions et filières", "C'est quoi les ressources humaines ?",
     "ressources humaines,rh,c est quoi rh,recrutement,capital humain",
     "Les ressources humaines (RH) gèrent les personnes dans l'entreprise : recrutement, contrats, paie, formation, évaluation et climat de travail. La filière GRH / Capital Humain prépare aux métiers de chargé de recrutement, gestionnaire de paie ou responsable RH."),
    ("Définitions et filières", "C'est quoi la logistique ?",
     "logistique,supply chain,c est quoi logistique,transport,stock,chaine logistique",
     "La logistique (supply chain) organise le parcours des marchandises : achats, stockage, transport et distribution jusqu'au client, au meilleur coût et dans les délais. Débouchés : gestionnaire de stock, responsable logistique, acheteur, transitaire."),
    ("Définitions et filières", "C'est quoi la communication digitale ?",
     "communication digitale,communication digital business,reseaux sociaux,community manager,publicite en ligne",
     "La communication digitale, c'est faire connaître une marque ou un produit sur internet : réseaux sociaux, contenus, sites web, publicité en ligne et image de marque. Débouchés : community manager, chargé de communication, créateur de contenu, responsable marketing digital."),
    ("Définitions et filières", "C'est quoi une base de données ?",
     "base de donnees,c est quoi base donnees,sql,bdd,sqj",
     "Une base de données est un ensemble organisé d'informations stockées dans un ordinateur, que l'on peut interroger et mettre à jour rapidement. Exemple : la liste des étudiants, leurs notes et leurs inscriptions. On la manipule souvent avec le langage SQL."),
    ("Définitions et filières", "C'est quoi Internet ?",
     "internet,c est quoi internet,web,site web",
     "Internet est le réseau mondial qui relie des milliards d'ordinateurs et de téléphones pour échanger des informations. Le Web (les sites et pages que tu visites avec un navigateur) n'est qu'un des services d'Internet, avec la messagerie, la vidéo ou les réseaux sociaux."),
    # ---------------- Vie universitaire ----------------
    ("Vie universitaire", "Comment trouver un stage ?",
     "stage,trouver stage,chercher stage,candidature stage,entreprise stage",
     "Pour trouver un stage : 1) prépare un CV propre et une lettre de motivation courte ; 2) cible les entreprises de ton domaine et dépose des candidatures spontanées ; 3) active ton réseau (enseignants, camarades, LinkedIn) ; 4) relance poliment après une semaine ; 5) prépare-toi à présenter tes projets — un portfolio ou un GitHub actif fait souvent la différence."),
    ("Vie universitaire", "C'est quoi un mémoire ?",
     "memoire,c est quoi memoire,soutenance,travail fin etudes,problematique",
     "Le mémoire est le grand travail de fin d'études : tu choisis un sujet, tu poses une problématique, tu mènes une recherche documentée, tu rédiges un document structuré, puis tu le défends oralement devant un jury — c'est la soutenance. Commence tôt : le choix du sujet et le plan prennent plus de temps qu'on ne croit."),
    ("Vie universitaire", "C'est quoi un crédit et une UE ?",
     "credit,credits,ue,unite enseignement,semestre,lmd,capitaliser",
     "Dans le système LMD, les cours sont regroupés en unités d'enseignement (UE) réparties par semestres. Chaque UE validée rapporte des crédits : une fois obtenus, ces crédits sont capitalisés, c'est-à-dire acquis définitivement. En général, une licence complète représente 180 crédits."),
    ("Vie universitaire", "C'est quoi le rattrapage ?",
     "rattrapage,session rattrapage,deuxieme session,echoue,reprendre examen",
     "Le rattrapage (ou deuxième session) est une seconde chance de composer dans les UE non validées à la session normale, selon le règlement de l'établissement. Il ne concerne que les matières en échec : concentre tes révisions sur celles-là et vérifie les dates affichées par l'administration."),
    ("Vie universitaire", "Comment gérer son budget d'étudiant ?",
     "budget,gerer argent,depenses,epargne etudiant,argent poche",
     "Méthode simple : 1) liste tes dépenses fixes (transport, repas, forfait, fournitures) ; 2) fixe une limite par semaine et tiens-la ; 3) mets de côté une petite somme dès que tu reçois de l'argent, même 500 FCFA ; 4) évite les dettes pour des envies — distingue toujours besoin et envie avant d'acheter."),
    ("Vie universitaire", "Comment s'organiser pour étudier ?",
     "organiser,organisation,planning etudes,gerer temps,emploi du temps personnel",
     "Organisation qui marche : un planning hebdomadaire réaliste, des sessions courtes mais régulières (25 à 50 minutes concentrées), le téléphone loin pendant les sessions, et 10 minutes chaque soir pour préparer le lendemain. Relis tes cours le jour même : c'est là que la mémoire se fixe."),
    ("Vie universitaire", "Comment se préparer à un entretien de stage ou d'embauche ?",
     "entretien,preparer entretien,stage entretien,embauche,questions entretien",
     "Préparation : 1) renseigne-toi sur l'entreprise ; 2) prépare une présentation de 30 secondes (ton pitch) ; 3) choisis deux projets concrets à raconter ; 4) prépare une ou deux questions à poser à la fin ; 5) arrive en avance, tenu propre, téléphone éteint. Sois honnête sur ton niveau : un recruteur pardonne un débutant, pas un menteur."),
    ("Vie universitaire", "À quoi sert la bibliothèque universitaire ?",
     "bibliotheque,livres,emprunter,etudier bibliotheque,ressources",
     "La bibliothèque sert à emprunter des livres de cours, réviser au calme, consulter des ressources que tu n'as pas à acheter et parfois travailler en groupe. C'est un vrai avantage gratuit : utilise-la avant les examens plutôt que de tout chercher sur internet au dernier moment."),
    # ---------------- Calculs et notes ----------------
    ("Calculs et notes", "Comment calculer sa moyenne ?",
     "calculer moyenne,moyenne,coefficients,coefficient,moyenne notes,comment moyenne,coefficients moyenne",
     "Avec des coefficients : multiplie chaque note par son coefficient, additionne tout, puis divise par la somme des coefficients. Sans coefficients : additionne les notes et divise par leur nombre. Tu peux aussi me le demander directement, par exemple : « moyenne de 12, 14, 9, 15 » ou « calcule (12×2 + 14×3) / 5 » — je sais calculer."),
    ("Calculs et notes", "C'est quoi un pourcentage ?",
     "pourcentage,c est quoi pourcentage,pour cent,calculer pourcentage",
     "Un pourcentage est une part sur 100. Pour calculer X % d'un montant, multiplie le montant par X puis divise par 100 : par exemple 15 % de 20 000 FCFA = 3 000 FCFA. Tu peux me demander directement : « calcule 15 % de 20000 » — je le fais tout de suite."),
    ("Calculs et notes", "Comment convertir des FCFA en euros ?",
     "convertir,fcfa,euros,taux de change,conversion,franc cfa",
     "Le franc CFA (XOF) a un taux fixe avec l'euro : 1 € = 655,957 FCFA, soit environ 656 FCFA. Pour convertir des FCFA en euros, divise par 656 : par exemple 65 600 FCFA ≈ 100 €. Pour les dollars ou d'autres devises, le taux change chaque jour : vérifie le taux du jour."),
    # ---------------- IAM : frais et diplômes ----------------
    ("Administration", "Quels sont les frais de scolarité à l'IAM ?",
     "frais,scolarite,prix,coute,combien coute,tarifs,montant annuel,payer etudes,scolarite iam",
     "Pour la Licence à l'IAM de Bamako, les frais de scolarité communiqués sont : 1re année : 1 095 000 FCFA ; 2e année : 1 025 000 FCFA ; 3e année : 1 000 000 FCFA. Ces montants peuvent varier selon la filière et l'année : confirme toujours le montant exact et les échéances de paiement au secrétariat ou au service de la scolarité."),
    ("Études et orientation", "C'est quoi la Licence ?",
     "licence,c est quoi licence,diplome licence,bac+3",
     "La Licence est le diplôme universitaire obtenu en 3 ans après le baccalauréat (6 semestres, 180 crédits dans le système LMD). C'est le premier niveau : après la Licence, on peut travailler ou continuer vers le Master."),
    ("Études et orientation", "C'est quoi le Master ?",
     "master,c est quoi master,diplome master,bac+5,mastere",
     "Le Master est le diplôme obtenu en 2 ans après la Licence (4 semestres, 120 crédits), soit un niveau bac+5. Il permet de se spécialiser et d'accéder à des postes à responsabilités, ou de continuer vers le doctorat."),
    ("Études et orientation", "C'est quoi le système LMD ?",
     "lmd,systeme lmd,licence master doctorat,reforme lmd",
     "Le système LMD (Licence – Master – Doctorat) organise les études supérieures en 3 niveaux : Licence en 3 ans, Master en 2 ans, Doctorat en 3 ans. Les cours sont découpés en semestres et en unités d'enseignement (UE) qui rapportent des crédits capitalisables."),
    ("Vie universitaire", "C'est quoi un semestre ?",
     "semestre,c est quoi semestre,annee scolaire,semestre 1,semestre 2",
     "Un semestre est une moitié d'année universitaire, d'environ 5 à 6 mois. Une année compte 2 semestres : par exemple la Licence 1 couvre les semestres 1 et 2, la Licence 2 les semestres 3 et 4. Chaque semestre a ses propres cours (UE) et ses examens."),
    ("Vie universitaire", "Comment réussir sa première année à l'université ?",
     "reussir,premiere annee,conseils reussite,debuter universite,l1",
     "Pour réussir ta première année : 1) va à tous les cours dès le début — les bases ratées se paient toute l'année ; 2) relis tes cours chaque semaine ; 3) pose des questions aux enseignants et aux aînés ; 4) organise ton planning et ton budget dès le premier mois ; 5) forme un petit groupe de travail sérieux. La régularité bat toujours le sprint de dernière minute."),
    # ---------------- Cours d'informatique ----------------
    ("Cours d'informatique", "C'est quoi une variable ?",
     "variable,c est quoi variable,programmer variable",
     "Une variable est un nom donné à une boîte qui stocke une valeur dans un programme : un nombre, un texte, un résultat. Exemple en Python : age = 20. On peut lire la valeur, la modifier et l'utiliser dans des calculs."),
    ("Cours d'informatique", "C'est quoi une boucle ?",
     "boucle,c est quoi boucle,for,while,repetition programmation",
     "Une boucle permet de répéter des instructions sans les réécrire : par exemple afficher 100 fois la même ligne ou parcourir une liste. Les plus connues sont « for » (nombre de répétitions connu) et « while » (répéter tant qu'une condition est vraie). Attention aux boucles infinies : la condition doit finir par devenir fausse."),
    ("Cours d'informatique", "C'est quoi une fonction en programmation ?",
     "fonction,c est quoi fonction,procedure,methode programmation",
     "Une fonction est un bloc de code nommé, réutilisable, qui accomplit une tâche précise. Elle peut recevoir des paramètres (des entrées) et renvoyer un résultat. Exemple : une fonction calculer_moyenne(notes) que tu appelles chaque fois que tu en as besoin, au lieu de recopier le calcul."),
    ("Cours d'informatique", "C'est quoi Python ?",
     "python,c est quoi python,langage python",
     "Python est un langage de programmation réputé simple à lire et à apprendre. Il sert à tout : sites web, automatisation, analyse de données, intelligence artificielle. C'est un excellent premier langage pour un étudiant en informatique."),
    ("Cours d'informatique", "C'est quoi HTML ?",
     "html,c est quoi html,balises,page web",
     "HTML est le langage de structure des pages web : avec des balises, il définit les titres, paragraphes, images, liens et formulaires. Ce n'est pas un langage de programmation : il décrit le contenu, CSS le met en forme et JavaScript le rend interactif."),
    ("Cours d'informatique", "C'est quoi CSS ?",
     "css,c est quoi css,style page web,feuille de style",
     "CSS est le langage qui met en forme les pages web : couleurs, tailles, espacements, disposition, adaptation aux téléphones. HTML donne la structure, CSS donne l'apparence — comme le squelette et les vêtements d'une page."),
    ("Cours d'informatique", "C'est quoi JavaScript ?",
     "javascript,js,c est quoi javascript,langage javascript",
     "JavaScript est le langage qui rend les pages web interactives : menus, formulaires qui réagissent, animations, applications dans le navigateur. Il fonctionne aussi côté serveur avec Node.js. Avec HTML et CSS, c'est le trio de base du développement web."),
    ("Cours d'informatique", "C'est quoi PHP ?",
     "php,c est quoi php,langage serveur",
     "PHP est un langage de programmation côté serveur, très utilisé pour les sites dynamiques : formulaires, comptes utilisateurs, boutiques, blogs (WordPress par exemple). Le serveur exécute le code PHP et envoie au navigateur une page HTML prête à afficher."),
    ("Cours d'informatique", "C'est quoi SQL ?",
     "sql,c est quoi sql,requete,select,base donnees langage",
     "SQL est le langage pour interroger et manipuler les bases de données : SELECT pour lire, INSERT pour ajouter, UPDATE pour modifier, DELETE pour supprimer. Presque toutes les applications qui stockent des informations utilisent SQL, avec des systèmes comme MySQL, PostgreSQL ou SQLite."),
    ("Cours d'informatique", "C'est quoi un réseau informatique ?",
     "reseau,c est quoi reseau,lan,wan,routeur,switch",
     "Un réseau informatique relie plusieurs appareils (ordinateurs, téléphones, imprimantes) pour partager des données et des ressources. Un petit réseau local s'appelle LAN (maison, bureau) ; Internet est le plus grand des réseaux, qui relie des réseaux entre eux (WAN)."),
    ("Cours d'informatique", "C'est quoi une adresse IP ?",
     "adresse ip,ip,c est quoi ip,ipv4",
     "Une adresse IP est le numéro qui identifie un appareil sur un réseau, un peu comme une adresse postale. Exemple IPv4 : 192.168.1.10. Sans adresse IP, les appareils ne pourraient pas se retrouver ni échanger de données."),
    ("Cours d'informatique", "C'est quoi un système d'exploitation ?",
     "systeme exploitation,os,c est quoi systeme exploitation,windows linux android",
     "Le système d'exploitation est le logiciel de base d'un appareil (Windows, Linux, Android, iOS) : il fait le lien entre le matériel et tes applications, gère les fichiers, la mémoire et les écrans. Sans lui, l'ordinateur ne peut rien lancer."),
    ("Cours d'informatique", "C'est quoi la RAM ?",
     "ram,memoire vive,c est quoi ram,memoire ram",
     "La RAM (mémoire vive) est la mémoire rapide et temporaire où l'ordinateur place ce qu'il utilise en ce moment : applications ouvertes, documents en cours. Elle se vide quand l'appareil s'éteint. À ne pas confondre avec le stockage (disque, SSD) qui conserve les fichiers durablement."),
    ("Cours d'informatique", "C'est quoi un processeur ?",
     "processeur,cpu,c est quoi processeur,calculateur",
     "Le processeur (CPU) est le « cerveau » de l'ordinateur : il exécute les instructions des programmes, fait les calculs et coordonne le reste. Sa vitesse se mesure en gigahertz (GHz) et il peut avoir plusieurs cœurs pour traiter plusieurs tâches en parallèle."),
    ("Cours d'informatique", "C'est quoi un fichier et un dossier ?",
     "fichier,dossier,c est quoi fichier,extension,document numerique",
     "Un fichier est un contenu enregistré : un texte, une photo, une vidéo, un programme. Son nom se termine souvent par une extension qui indique son type (.pdf, .jpg, .docx). Un dossier est un conteneur qui sert à ranger et organiser les fichiers."),
    ("Cours d'informatique", "C'est quoi un navigateur web ?",
     "navigateur,c est quoi navigateur,chrome,firefox,moteur recherche difference",
     "Un navigateur web est le logiciel qui affiche les sites internet : Chrome, Firefox, Edge, Safari. À ne pas confondre avec le moteur de recherche (Google, Bing) qui, lui, aide à trouver les sites. Le navigateur est la fenêtre, le moteur de recherche est l'annuaire."),
    ("Cours d'informatique", "C'est quoi le cloud ?",
     "cloud,nuage,c est quoi cloud,stockage en ligne",
     "Le cloud (« nuage ») signifie que tes fichiers et services sont hébergés sur des serveurs distants, accessibles par internet depuis n'importe quel appareil : Google Drive, iCloud, OneDrive. Pratique pour sauvegarder et partager, mais tes données dépendent alors de la connexion et du fournisseur."),
    ("Cours d'informatique", "C'est quoi la cybersécurité ?",
     "cybersecurite,securite informatique,c est quoi cybersecurite,piratage protection",
     "La cybersécurité regroupe les moyens de protéger les systèmes et les données contre les attaques : vols de comptes, virus, arnaques. Les réflexes de base : mots de passe forts et uniques, double authentification, mises à jour, et méfiance envers les messages qui demandent des codes ou de l'argent."),
    ("Cours d'informatique", "Comment créer un mot de passe fort ?",
     "mot de passe fort,securiser compte,password,proteger compte",
     "Un mot de passe fort est long (12 caractères et plus), unique pour chaque compte, et mélange lettres, chiffres et symboles. Astuce : une phrase facile à retenir pour toi mais dure à deviner, par exemple « Bamako-soleil-2026! ». Ajoute la double authentification quand elle existe, et ne partage jamais tes codes."),
    ("Cours d'informatique", "C'est quoi le phishing ?",
     "phishing,hameconnage,c est quoi phishing,arnaque message,faux site",
     "Le phishing (hameçonnage) est une arnaque : un faux message ou un faux site imite un organisme connu (banque, opérateur, réseau social) pour te voler tes identifiants ou ton argent. Réflexes : vérifier l'adresse de l'expéditeur et du site, ne jamais cliquer sur un lien qui presse, et ne jamais donner ses codes — aucun service sérieux ne les demande par message."),
    # ---------------- Matières et outils ----------------
    ("Matières et outils", "C'est quoi l'économie ?",
     "economie,c est quoi economie,science economique",
     "L'économie étudie comment les personnes, les entreprises et les États produisent, échangent et utilisent les ressources et l'argent. On distingue la microéconomie (les choix des individus et des entreprises) et la macroéconomie (le pays entier : croissance, chômage, prix)."),
    ("Matières et outils", "C'est quoi la gestion de projet ?",
     "gestion de projet,c est quoi gestion projet,management projet,planifier projet",
     "La gestion de projet consiste à organiser un travail pour atteindre un objectif dans un délai et un budget donnés : définir les tâches, les répartir, suivre l'avancement et gérer les problèmes. C'est exactement ce que tu fais dans un projet d'équipe à l'atelier : rôles, échéances et livrables clairs."),
    ("Matières et outils", "C'est quoi l'entrepreneuriat ?",
     "entrepreneuriat,entrepreneur,c est quoi entrepreneuriat,creer entreprise",
     "L'entrepreneuriat, c'est créer et développer sa propre activité : trouver une idée utile, étudier le marché, trouver des clients et faire grandir l'entreprise. Cela demande de la créativité, de la persévérance et une bonne organisation — des qualités qui s'apprennent."),
    ("Matières et outils", "C'est quoi un business plan ?",
     "business plan,plan affaires,c est quoi business plan,projet entreprise document",
     "Un business plan est le document qui présente un projet d'entreprise : l'offre, les clients visés, la concurrence, l'organisation et les chiffres prévisionnels (coûts, prix, bénéfices espérés). Il sert à clarifier le projet et à convaincre des partenaires ou des financeurs."),
    ("Matières et outils", "C'est quoi la trésorerie ?",
     "tresorerie,c est quoi tresorerie,liquidites,encaisse",
     "La trésorerie est l'argent réellement disponible à court terme dans une entreprise ou une association : ce qui est en caisse et sur les comptes, après les entrées et les sorties. Une entreprise peut vendre beaucoup et manquer de trésorerie si les clients paient en retard — c'est un point de vigilance permanent."),
    ("Matières et outils", "C'est quoi Excel ?",
     "excel,tableur,c est quoi excel,formule somme",
     "Excel est un tableur : il organise les données en lignes et colonnes et fait des calculs automatiques grâce aux formules (SOMME, MOYENNE, etc.), des tris et des graphiques. Il sert partout : budgets, notes, stocks, listes de clients. Savoir l'utiliser est une compétence demandée dans presque tous les métiers de gestion."),
    ("Matières et outils", "C'est quoi Word ?",
     "word,traitement de texte,c est quoi word,rediger document",
     "Word est un logiciel de traitement de texte : il sert à rédiger et mettre en forme des documents (rapports, lettres, CV, mémoires) avec titres, listes, tableaux et images. Bien l'utiliser fait gagner un temps énorme sur les travaux universitaires."),
    ("Matières et outils", "C'est quoi PowerPoint ?",
     "powerpoint,presentation diapositives,c est quoi powerpoint,slides",
     "PowerPoint sert à créer des présentations en diapositives pour les cours, les exposés et les soutenances. Une bonne présentation : peu de texte par diapositive, de gros titres lisibles, des images utiles — et c'est toi qui expliques, pas les diapositives."),
    ("Matières et outils", "Comment faire un bon exposé ?",
     "expose,faire expose,presenter expose,conseils expose oral",
     "Un bon exposé : 1) un plan clair (introduction, 2 ou 3 parties, conclusion) ; 2) des diapositives simples, peu de texte ; 3) des exemples concrets ; 4) un entraînement à voix haute en te chronométrant ; 5) un regard vers le public, pas vers l'écran. Prépare aussi 2 ou 3 questions que le jury pourrait poser."),
    ("Matières et outils", "Pourquoi apprendre l'anglais ?",
     "anglais,apprendre anglais,pourquoi anglais,langue anglaise",
     "L'anglais ouvre des portes : la documentation technique, les tutoriels et beaucoup d'offres d'emploi et de bourses sont en anglais, surtout en informatique. Méthode simple : un peu chaque jour (applications, vidéos sous-titrées, vocabulaire technique de ta filière) vaut mieux qu'une grosse session rare."),
    ("Matières et outils", "C'est quoi la statistique ?",
     "statistique,c est quoi statistique,donnees,moyenne mediane",
     "La statistique est la science qui collecte, organise et interprète des données chiffrées pour décider : moyennes, pourcentages, graphiques, enquêtes. Elle sert partout : notes d'une classe, ventes d'une boutique, résultats d'un sondage. Attention : un chiffre seul ne prouve rien sans comprendre comment il a été obtenu."),
    ("Matières et outils", "C'est quoi une probabilité ?",
     "probabilite,c est quoi probabilite,hasard,chance",
     "Une probabilité mesure la chance qu'un événement se produise, entre 0 (impossible) et 1 (certain), ou en pourcentage. Exemple : en lançant une pièce équilibrée, la probabilité d'obtenir pile est de 1/2, soit 50 %. C'est la base des jeux de hasard, des assurances et d'une partie des statistiques."),
    ("Matières et outils", "Comment prendre des notes en cours ?",
     "prendre notes,notes cours,methode notes,ecouter cours",
     "Pour bien prendre des notes : écoute d'abord, écris l'essentiel avec tes mots (pas tout mot à mot), utilise des abréviations et de la place pour compléter, note les exemples donnés par le professeur. Le soir même, relis et souligne les points clés : 10 minutes qui valent une heure de révision plus tard."),
    ("Matières et outils", "Comment faire une recherche documentaire ?",
     "recherche documentaire,sources,c est quoi recherche documentaire,trouver informations fiables",
     "Une bonne recherche documentaire : 1) définis précisément ton sujet et tes mots-clés ; 2) cherche dans des sources fiables (livres, sites officiels, articles) plutôt que le premier résultat venu ; 3) vérifie l'auteur et la date ; 4) croise au moins deux sources ; 5) cite tes sources dans ton travail. C'est la différence entre un devoir solide et un copier-coller."),
    ("Matières et outils", "Comment préparer un examen oral ?",
     "examen oral,preparer oral,soutenance orale,conseils oral",
     "Pour un oral : maîtrise ton plan par cœur (pas le texte mot à mot), prépare des exemples concrets pour chaque partie, entraîne-toi à voix haute devant quelqu'un, et prépare les questions probables du jury. Le jour J : arrive en avance, respire, parle lentement et regarde le jury. Ne pas savoir répondre à tout n'est pas grave : explique ton raisonnement."),
    ("Matières et outils", "C'est quoi un graphique ?",
     "graphique,diagramme,c est quoi graphique,representer donnees,courbe barres",
     "Un graphique représente des données en image pour les comprendre d'un coup d'œil : barres pour comparer, courbe pour montrer une évolution, camembert pour des parts d'un tout. Le bon graphique dépend du message : comparer, suivre dans le temps ou répartir."),
    ("Études et orientation", "C'est quoi la bibliothèque universitaire de l'assistant ?",
     "bibliotheque,bibliotheque universitaire,cours complets,225 cours,cours par filiere,bibliotheque iam",
     "📚 La Bibliothèque Universitaire de l'Assistant IAM regroupe 225 cours complets : Informatique, BBA et Droit, pour les Licences 1, 2 et 3 (25 cours par niveau). Chaque cours arrive avec son PDF de 25 pages et plus : leçons détaillées, exemples, exercices corrigés, QCM et vidéos YouTube pour comprendre. Ouvre la « Bibliothèque Universitaire » depuis la page d'accueil de l'assistant : tu choisis ta filière, ton niveau, puis ton cours, et tu peux suivre ta progression."),
    ("Études et orientation", "Où trouver les leçons en PDF ?",
     "lecons pdf,pdf lecons,telecharger lecons,livrets,cours pdf,documents revision,supports cours",
     "Les livrets de révision gratuits sont dans la section « Leçons PDF » de cette page : un livret de 25 pages pour la Licence 1, un pour la Licence 2 et un pour la Licence 3, chacun organisé par filière (informatique, gestion-BBA, droit, comptabilité, marketing…), avec QCM corrigés, glossaire et sujets d'entraînement, en téléchargement direct. Une grande bibliothèque complète (25 cours par niveau et par filière) est aussi en préparation chez Bronbah Tech. Pour les formations complètes d'Adrian (Bronbah Tech), la commande se fait sur WhatsApp au 73 25 58 73 : le PDF complet est envoyé après l'inscription de 13 000 FCFA."),
]

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cle-de-developpement-a-changer")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    with open(os.path.join(BASE, "schema.sql"), encoding="utf-8") as f:
        db.executescript(f.read())
    cols = [r[1] for r in db.execute("PRAGMA table_info(chatlog)").fetchall()]
    if "source" not in cols:
        db.execute("ALTER TABLE chatlog ADD COLUMN source TEXT NOT NULL DEFAULT 'kb'")
    existing = {r[0] for r in db.execute("SELECT question FROM qna").fetchall()}
    missing = [row for row in SEED_QNA if row[1] not in existing]
    if missing:
        db.executemany(
            "INSERT INTO qna (categorie, question, keywords, reponse) VALUES (?,?,?,?)",
            missing)
    db.commit()
    db.close()


def get_setting(key, default=""):
    row = get_db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    db = get_db()
    db.execute("INSERT INTO settings (key, value) VALUES (?,?) "
               "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    db.commit()


# ------------------------------------------------------------- moteur de réponse
STOPWORDS = {"le", "la", "les", "de", "des", "du", "un", "une", "et", "est",
             "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "a", "au",
             "aux", "en", "dans", "sur", "pour", "avec", "que", "qui", "quoi",
             "comment", "quand", "ou", "ce", "se", "sa", "son", "mes", "mon",
             "ma", "tes", "ton", "ta", "cette", "ces", "pas", "plus", "faire"}
ACRONYMES = {"cv", "ia", "rh", "ue", "sql", "php", "bba", "mba", "dba",
             "big", "gbba", "lmd", "web"}


def normalize(text):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def answer_question(text):
    """Retourne (qna_row | None, suggestions). Recherche par mots-clés pondérés."""
    norm = normalize(text)
    words = [w for w in norm.split() if w not in STOPWORDS and (len(w) > 2 or w in ACRONYMES)]
    rows = get_db().execute("SELECT * FROM qna").fetchall()
    best, best_score = None, 0
    scored = []
    for row in rows:
        score = 0
        for kw in row["keywords"].split(","):
            kw = normalize(kw.strip())
            if not kw:
                continue
            if " " in kw:
                if kw in norm:
                    score += 3 * len(kw.split())
            elif kw in words:
                score += 2
        q_words = [w for w in normalize(row["question"]).split()
                   if w not in STOPWORDS and (len(w) > 2 or w in ACRONYMES)]
        score += sum(1 for w in q_words if w in words)
        if score > 0:
            scored.append((score, row))
        if score > best_score:
            best, best_score = row, score
    if best is not None and best_score >= 3:
        return best, []
    scored.sort(key=lambda x: -x[0])
    return None, [r for _, r in scored[:3]]


# ------------------------------------------------------- vraie IA (Gemini, gratuit)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
              + GEMINI_MODEL + ":generateContent")

SYSTEME_IA = (
    "Tu es l'assistant des étudiants de l'Université IAM (Institut Africain de "
    "Management) de Bamako, au Mali. Tu réponds en français simple et clair, en "
    "2 à 6 phrases maximum, avec un ton aidant pour des étudiants. "
    "Faits sûrs à utiliser : l'atelier IAM Code to Career est piloté par "
    "DataInsights, chef d'atelier Abdoulaye TRAORE ; horaires de l'atelier : "
    "lundi à vendredi 9h00-15h00 (vendredi 9h00-13h00) ; 12 projets d'équipe ; "
    "livrables : démonstration, code sur GitHub, présentation, projet intégré au "
    "CV et au profil en ligne. Tu peux aussi présenter l'IAM et ses grandes "
    "familles de parcours (gestion/BBA, informatique, droit, communication "
    "digitale, banque/finance, comptabilité/audit, ressources humaines, "
    "marketing, logistique), en précisant que les filières ouvertes varient "
    "selon le campus et l'année. "
    "Règles strictes : n'invente JAMAIS de dates officielles (examens, "
    "inscriptions, résultats) ni de numéros de téléphone : pour ces sujets, dis "
    "de vérifier auprès du secrétariat ou de l'affichage officiel de l'IAM. "
    "Tu peux expliquer des notions de cours (programmation, informatique), "
    "donner des conseils d'étude, aider à rédiger ou améliorer un CV étudiant, "
    "et répondre simplement à des questions générales de conversation. Si la "
    "question n'a aucun rapport avec la vie étudiante ou les études, réponds "
    "brièvement puis propose de revenir aux sujets étudiants."
)


def gemini_key():
    return (os.environ.get("GEMINI_API_KEY") or get_setting("gemini_key", "")).strip()


def ai_answer(question, contexte):
    """Vraie IA, deux chemins :
    1) le relais IA (GET, déployé sur Netlify — contourne les réseaux qui bloquent
       les appels POST sortants) ; 2) l'API Gemini directe si une vraie clé est
       configurée. Retourne le texte ou None si l'IA est indisponible."""
    systeme = SYSTEME_IA
    if contexte:
        systeme += ("\n\nInformations de la base officielle de l'assistant "
                    "(à utiliser en priorité si elles répondent) :\n" + contexte)
    relay = get_setting("relay_url", "").rstrip("/")
    token = get_setting("relay_token", "")
    if relay and token:
        qs = urllib.parse.urlencode(
            {"q": question, "system": systeme, "token": token})
        try:
            with urllib.request.urlopen(relay + "/ia?" + qs, timeout=25) as resp:
                text = resp.read().decode("utf-8").strip()
            if text and text != "empty":
                return text
        except Exception:
            pass
    key = gemini_key()
    if not (key.startswith("AIza") and len(key) >= 30):
        return None
    prompt = systeme + "\n\nQuestion de l'étudiant : " + question
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 500},
    }).encode("utf-8")
    req = urllib.request.Request(GEMINI_URL, data=body, method="POST", headers={
        "Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
        return text or None
    except Exception:
        return None


# -------------------------------------------------------------------- utilitaires
def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    return get_db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not current_user():
            flash("Connecte-toi pour continuer.", "info")
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        u = current_user()
        if not u or not u["is_admin"]:
            abort(403)
        return f(*a, **kw)
    return wrapper


@app.context_processor
def inject_user():
    return {"me": current_user(), "CATEGORIES": CATEGORIES}


# ------------------------------------------------------------------------ routes
@app.route("/")
def index():
    exemples = get_db().execute(
        "SELECT question FROM qna WHERE categorie='Atelier Code to Career' LIMIT 4").fetchall()
    return render_template("index.html", exemples=[r["question"] for r in exemples])


# ---------------- Calculatrice intégrée ----------------
def _fmt_num(v):
    if v != v or v in (float("inf"), float("-inf")):
        return "∞"
    r = round(v, 4)
    s = f"{r:.4f}".rstrip("0").rstrip(".") if "." in f"{r:.4f}" else str(r)
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    ent, _, dec = s.partition(".")
    groupes = []
    while len(ent) > 3:
        groupes.append(ent[-3:])
        ent = ent[:-3]
    groupes.append(ent)
    out = " ".join(reversed(groupes))
    if dec:
        out += "," + dec
    return ("-" if neg else "") + out


def _eval_ast(node):
    import ast as _ast
    if isinstance(node, _ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, _ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, _ast.BinOp):
        a, b = _eval_ast(node.left), _eval_ast(node.right)
        if isinstance(node.op, _ast.Add):
            return a + b
        if isinstance(node.op, _ast.Sub):
            return a - b
        if isinstance(node.op, _ast.Mult):
            return a * b
        if isinstance(node.op, _ast.Div):
            return a / b
        if isinstance(node.op, _ast.Pow):
            return a ** b
    if isinstance(node, _ast.UnaryOp):
        v = _eval_ast(node.operand)
        if isinstance(node.op, _ast.USub):
            return -v
        if isinstance(node.op, _ast.UAdd):
            return v
    if isinstance(node, _ast.Call) and getattr(node.func, "id", "") == "sqrt" and len(node.args) == 1:
        import math as _math
        return _math.sqrt(_eval_ast(node.args[0]))
    raise ValueError("expression non autorisée")


def try_calc(text):
    import re as _re
    import ast as _ast
    t = " " + _re.sub(r"\s+", " ", text.lower().strip()) + " "
    m = _re.search(r"moyenne[^0-9]*([0-9][0-9\s.,;]*)", t)
    if "moyenne" in t and m:
        nums = [float(x.replace(",", ".")) for x in _re.findall(r"\d+(?:[.,]\d+)?", m.group(1))]
        if len(nums) >= 2:
            moy = sum(nums) / len(nums)
            return ("🧮 Moyenne de " + " ; ".join(_fmt_num(n) for n in nums) + " = " +
                    _fmt_num(moy) + " (sur 20 si ce sont des notes).")
    m = _re.search(r"(\d+(?:[.,]\d+)?)\s*(?:%|pour\s*cent)\s*de\s*(\d+(?:[.,]\d+)?)", t)
    if m:
        p = float(m.group(1).replace(",", "."))
        base = float(m.group(2).replace(",", "."))
        return f"🧮 {_fmt_num(p)} % de {_fmt_num(base)} = {_fmt_num(p / 100 * base)}."
    e = _re.sub(r"calcule[rz]?|calculer|combien font|combien fait|ca fait combien|resultat de|egal|=", " ", t)
    e = _re.sub(r"[?!]", " ", e)
    e = _re.sub(r"racine carree de|racine carrée de|racine de", " sqrt ", e)
    e = e.replace("×", "*").replace("÷", "/")
    e = _re.sub(r"(\d)\s*x\s*(\d)", r"\1*\2", e)
    e = _re.sub(r"(\d),(\d)", r"\1.\2", e).replace(",", " ")
    e = _re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1/100)", e)
    e = e.strip()
    if not _re.fullmatch(r"[0-9+\-*/^(). sqrt]+", e) or not _re.search(r"\d", e):
        return None
    if not (_re.search(r"[+\-*/^]", e.lstrip("-")) or "sqrt" in e):
        return None
    e = e.replace("^", "**")
    e = _re.sub(r"sqrt\s*(\([^()]*\)|\d+(?:\.\d+)?)", r"sqrt(\1)", e)
    try:
        val = _eval_ast(_ast.parse(e, mode="eval"))
    except Exception:
        return None
    if val != val or val in (float("inf"), float("-inf")):
        return None
    aff = e.replace("**", " ^ ").replace("sqrt", "√").replace("*", " × ").replace("/", " ÷ ")
    aff = _re.sub(r"\s+", " ", aff).strip()
    return f"🧮 {aff} = {_fmt_num(val)}."


# ---------------- Quiz entraînement + planning de révisions ----------------
QUIZ = [
    ("Que signifie IAM ?", ["Institut Africain de Management", "Institut d'Art Moderne", "International Academy of Music"], 0, "IAM = Institut Africain de Management."),
    ("Lequel de ces langages est un vrai langage de programmation ?", ["HTML", "CSS", "Python"], 2, "HTML structure et CSS met en forme ; Python est un langage de programmation complet."),
    ("Combien font 15 % de 20 000 ?", ["300", "3 000", "30 000"], 1, "20 000 × 15 / 100 = 3 000."),
    ("Que veut dire BBA ?", ["Bachelor of Business Administration", "Brevet de Banque Africaine", "Bachelor of Biology and Arts"], 0, "Le BBA est une licence en administration des affaires."),
    ("Dans le système LMD, la Licence dure…", ["2 ans", "3 ans", "5 ans"], 1, "Licence 3 ans, Master 2 ans, Doctorat 3 ans."),
    ("Quel langage sert à interroger une base de données ?", ["SQL", "HTML", "CSS"], 0, "SQL : SELECT, INSERT, UPDATE, DELETE."),
    ("Un mot de passe fort doit être…", ["Court et facile", "Ton prénom + 123", "Long, unique et mélangé"], 2, "Longueur + unicité + mélange de caractères, et double authentification si possible."),
    ("Comment demander ta moyenne à l'assistant ?", ["Écrire « moyenne de 12, 14, 9 »", "Écrire « raconte une histoire »", "Impossible"], 0, "La calculatrice intégrée comprend « moyenne de … » et toutes les opérations."),
]


def _quiz_message(i):
    q, opts, _good, _expl = QUIZ[i]
    lignes = "\n".join(f"{'ABC'[j]}) {o}" for j, o in enumerate(opts))
    return (f"Question {i + 1}/{len(QUIZ)} — {q}\n{lignes}\n"
            "(Réponds par A, B ou C — ou écris « stop » pour arrêter.)")


def quiz_step(text):
    n = normalize(text)
    if "quiz_i" not in session:
        if n in ("quiz", "lancer un quiz", "mode quiz", "je veux un quiz",
                 "quiz entrainement", "entrainement"):
            session["quiz_i"] = 0
            session["quiz_score"] = 0
            return ("📝 C'est parti pour un quiz d'entraînement "
                    f"({len(QUIZ)} questions) !\n\n" + _quiz_message(0))
        return None
    if n in ("stop", "arreter", "quitter", "abandonner"):
        session.pop("quiz_i", None)
        session.pop("quiz_score", None)
        return "Quiz arrêté. Écris « quiz » quand tu veux recommencer."
    i = session["quiz_i"]
    q, opts, good, expl = QUIZ[i]
    m = re.fullmatch(r"([abc123])[.)]?", n)
    idx = -1
    if m:
        idx = "abc123".index(m.group(1)) % 3
    else:
        for j, o in enumerate(opts):
            if normalize(o) == n:
                idx = j
                break
    if idx < 0:
        return "Réponds par A, B ou C.\n\n" + _quiz_message(i)
    ok = idx == good
    if ok:
        session["quiz_score"] = session.get("quiz_score", 0) + 1
    out = ("✅ Bonne réponse ! " if ok else
           f"❌ Non — la bonne réponse était {'ABC'[good]}) {opts[good]}. ") + expl
    i += 1
    if i >= len(QUIZ):
        score = session.get("quiz_score", 0)
        session.pop("quiz_i", None)
        session.pop("quiz_score", None)
        out += (f"\n\n🏁 Quiz terminé : {score}/{len(QUIZ)}"
                + (" — excellent, tu es prêt !" if score >= 6 else
                   " — bien, continue à réviser." if score >= 4 else
                   " — courage, relis les réponses de la base et réessaie.")
                + "\n(Écris « quiz » pour recommencer.)")
    else:
        session["quiz_i"] = i
        out += "\n\n" + _quiz_message(i)
    return out


def try_planning(text):
    import datetime as _dt
    t = text.lower()
    if "planning" not in t and "plan de revision" not in t and "plan de révision" not in t:
        return None
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", t) or re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if not m:
        return ("Pour te construire un planning, dis-moi la matière et la date de "
                "l'examen. Exemple : « planning Python 20/10/2026 ».")
    if "/" in m.group(0):
        exam = _dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    else:
        exam = _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    today = _dt.date.today()
    days = (exam - today).days
    if days <= 0:
        return ("Cette date est déjà passée. Donne-moi une date d'examen future, "
                "par exemple : « planning Python 20/10/2026 ».")
    if days > 120:
        return (f"L'examen est dans {days} jours : c'est tôt pour un planning "
                "détaillé. Reviens me voir à 30 jours de l'examen ; en attendant, "
                "révise un peu chaque semaine.")
    sujet = re.sub(r"planning|plan de r[ée]visions?|r[ée]visions?|examen|pour|le|la|les|de|du|des",
                   " ", t)
    sujet = re.sub(r"\s+", " ", sujet.replace(m.group(0), " ")).strip()
    sujet = (sujet[:1].upper() + sujet[1:]) if sujet else "La matière"
    j_appr = max(1, int(days * 0.5))
    j_ex = max(1, int(days * 0.3))

    def fmt(d):
        return d.strftime("%d/%m")

    def dj(n):
        return today + _dt.timedelta(days=n)

    return (f"📅 Planning de révisions — {sujet} (examen le {fmt(exam)}, dans {days} jours) :\n"
            f"• Du {fmt(dj(0))} au {fmt(dj(j_appr - 1))} : apprendre le cours — relis chaque chapitre et fais des fiches courtes.\n"
            f"• Du {fmt(dj(j_appr))} au {fmt(dj(j_appr + j_ex - 1))} : exercices et anciens sujets, sans regarder les corrections avant d'avoir essayé.\n"
            "• Les derniers jours : révisions générales + un test en conditions réelles ; la veille, relis tes fiches et dors tôt.\n"
            "Chaque jour : 2 sessions de 45 minutes concentrées valent mieux que 4 heures distrait. Bon courage !")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("message") or "").strip()
    if not text:
        return jsonify({"reponse": "Écris-moi ta question, je t'écoute."})
    qz = quiz_step(text)
    if qz is not None:
        return jsonify({"reponse": qz, "categorie": "Quiz entraînement",
                        "trouve": True, "ia": False})
    plan = try_planning(text)
    if plan:
        return jsonify({"reponse": plan, "categorie": "Planning de révisions",
                        "trouve": True, "ia": False})
    calc = try_calc(text)
    if calc:
        db = get_db()
        db.execute("INSERT INTO chatlog (question, qna_id, source) VALUES (?, NULL, 'calc')",
                   (text,))
        db.commit()
        return jsonify({"reponse": calc, "categorie": "Calcul intégré",
                        "trouve": True, "ia": False})
    row, suggestions = answer_question(text)
    db = get_db()
    if row:
        db.execute("INSERT INTO chatlog (question, qna_id, source) VALUES (?,?, 'kb')",
                   (text, row["id"]))
        db.commit()
        return jsonify({"reponse": row["reponse"], "categorie": row["categorie"],
                        "trouve": True, "ia": False})
    contexte = "\n".join(f"- {s['question']} → {s['reponse']}" for s in suggestions)
    rep_ia = ai_answer(text, contexte)
    if rep_ia:
        db.execute("INSERT INTO chatlog (question, qna_id, source) VALUES (?, NULL, 'ai')",
                   (text,))
        db.commit()
        return jsonify({"reponse": rep_ia, "categorie": "Réponse IA — Google Gemini",
                        "trouve": True, "ia": True})
    db.execute("INSERT INTO chatlog (question, qna_id, source) VALUES (?, NULL, 'none')",
               (text,))
    db.commit()
    rep = ("Je n'ai pas encore la réponse à cette question — je l'ai notée pour que "
           "l'équipe l'ajoute à ma base. En attendant, le secrétariat de l'IAM peut "
           "te renseigner directement.")
    if suggestions:
        rep += " Peut-être que tu cherches : " + " ; ".join(
            f"« {s['question']} »" for s in suggestions)
    rep += (" Tu peux aussi transmettre ta question à Douga sur WhatsApp au "
            "73 25 58 73 : il te répondra et t'expliquera le reste.")
    return jsonify({"reponse": rep, "trouve": False, "ia": False})


@app.route("/questions")
def documentation():
    rows = get_db().execute("SELECT * FROM qna ORDER BY categorie, id").fetchall()
    par_cat = {}
    for r in rows:
        par_cat.setdefault(r["categorie"], []).append(r)
    return render_template("doc.html", par_cat=par_cat, total=len(rows))


@app.route("/questions.json")
def documentation_json():
    rows = get_db().execute(
        "SELECT categorie, question, reponse FROM qna ORDER BY categorie, id").fetchall()
    return Response(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2),
                    mimetype="application/json",
                    headers={"Content-Disposition": "attachment; filename=questions-reponses.json"})


# -------------------------------------------------------------------------- auth
@app.route("/inscription", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Nom, e-mail et mot de passe (6 caractères minimum) sont requis.", "err")
        else:
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?,?,?)",
                    (name, email, generate_password_hash(password)))
                db.commit()
                session["uid"] = cur.lastrowid
                flash(f"Bienvenue, {name} !", "ok")
                return redirect(url_for("admin_home"))
            except sqlite3.IntegrityError:
                flash("Cet e-mail a déjà un compte. Connecte-toi.", "err")
    return render_template("register.html")


@app.route("/connexion", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        u = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if u and check_password_hash(u["password_hash"], password):
            session["uid"] = u["id"]
            return redirect(url_for("admin_home"))
        flash("E-mail ou mot de passe incorrect.", "err")
    return render_template("login.html")


@app.route("/deconnexion")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ------------------------------------------------------------------------- admin
@app.route("/admin")
@login_required
def admin_home():
    me = current_user()
    db = get_db()
    admin_exists = db.execute("SELECT 1 FROM users WHERE is_admin=1").fetchone() is not None
    can_claim = (me["email"] == OWNER_EMAIL) and not admin_exists
    if not me["is_admin"]:
        return render_template("admin.html", locked=True, can_claim=can_claim)
    stats = {
        "qna": db.execute("SELECT COUNT(*) FROM qna").fetchone()[0],
        "questions": db.execute("SELECT COUNT(*) FROM chatlog").fetchone()[0],
        "ia": db.execute(
            "SELECT COUNT(*) FROM chatlog WHERE source='ai'").fetchone()[0],
        "sans_reponse": db.execute(
            "SELECT COUNT(*) FROM chatlog WHERE source='none'").fetchone()[0],
    }
    qnas = db.execute("SELECT * FROM qna ORDER BY categorie, id").fetchall()
    unmatched = db.execute(
        "SELECT * FROM chatlog WHERE source='none' ORDER BY id DESC LIMIT 50").fetchall()
    return render_template("admin.html", locked=False, stats=stats, qnas=qnas,
                           unmatched=unmatched,
                           ia_active=bool(get_setting("relay_url")) or
                           (gemini_key().startswith("AIza") and len(gemini_key()) >= 30))


@app.route("/admin/activer", methods=["POST"])
@login_required
def admin_claim():
    me = current_user()
    db = get_db()
    admin_exists = db.execute("SELECT 1 FROM users WHERE is_admin=1").fetchone() is not None
    if me["email"] != OWNER_EMAIL or admin_exists:
        abort(403)
    db.execute("UPDATE users SET is_admin=1 WHERE id=?", (me["id"],))
    db.commit()
    flash("Espace admin activé pour ton compte.", "ok")
    return redirect(url_for("admin_home"))


@app.route("/admin/ajouter", methods=["POST"])
@admin_required
def admin_add():
    f = request.form
    db = get_db()
    db.execute("INSERT INTO qna (categorie, question, keywords, reponse) VALUES (?,?,?,?)",
               (f.get("categorie", "Divers"), f.get("question", "").strip(),
                f.get("keywords", "").strip(), f.get("reponse", "").strip()))
    db.commit()
    flash("Question/réponse ajoutée à la base.", "ok")
    return redirect(url_for("admin_home"))


@app.route("/admin/supprimer/<int:qna_id>", methods=["POST"])
@admin_required
def admin_delete(qna_id):
    db = get_db()
    db.execute("UPDATE chatlog SET qna_id=NULL WHERE qna_id=?", (qna_id,))
    db.execute("DELETE FROM qna WHERE id=?", (qna_id,))
    db.commit()
    flash("Question/réponse supprimée.", "info")
    return redirect(url_for("admin_home"))


@app.route("/admin/cle", methods=["POST"])
@admin_required
def admin_key_save():
    key = request.form.get("gemini_key", "").strip()
    if len(key) < 20:
        flash("Clé trop courte : copie la clé complète depuis Google AI Studio.", "err")
    else:
        set_setting("gemini_key", key)
        flash("Clé IA enregistrée. L'assistant répond maintenant avec la vraie IA "
              "quand la base n'a pas la réponse.", "ok")
    return redirect(url_for("admin_home"))


@app.route("/admin/cle/supprimer", methods=["POST"])
@admin_required
def admin_key_delete():
    set_setting("gemini_key", "")
    flash("Clé IA supprimée : l'assistant repasse en mode base seule.", "info")
    return redirect(url_for("admin_home"))


@app.route("/admin/export.csv")
@admin_required
def admin_export():
    rows = get_db().execute("SELECT * FROM qna ORDER BY categorie, id").fetchall()
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["id", "categorie", "question", "keywords", "reponse"])
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r[k] for k in ["id", "categorie", "question", "keywords", "reponse"]})
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=base-questions-reponses.csv"})


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=False)
