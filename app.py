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
    n = db.execute("SELECT COUNT(*) FROM qna").fetchone()[0]
    if n == 0:
        db.executemany(
            "INSERT INTO qna (categorie, question, keywords, reponse) VALUES (?,?,?,?)",
            SEED_QNA)
    db.commit()
    db.close()


# ------------------------------------------------------------- moteur de réponse
STOPWORDS = {"le", "la", "les", "de", "des", "du", "un", "une", "et", "est",
             "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "a", "au",
             "aux", "en", "dans", "sur", "pour", "avec", "que", "qui", "quoi",
             "comment", "quand", "ou", "ce", "se", "sa", "son", "mes", "mon",
             "ma", "tes", "ton", "ta", "cette", "ces", "pas", "plus", "faire"}


def normalize(text):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def answer_question(text):
    """Retourne (qna_row | None, suggestions). Recherche par mots-clés pondérés."""
    norm = normalize(text)
    words = [w for w in norm.split() if w not in STOPWORDS and len(w) > 2]
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
                   if w not in STOPWORDS and len(w) > 2]
        score += sum(1 for w in q_words if w in words)
        if score > 0:
            scored.append((score, row))
        if score > best_score:
            best, best_score = row, score
    if best is not None and best_score >= 3:
        return best, []
    scored.sort(key=lambda x: -x[0])
    return None, [r for _, r in scored[:3]]


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


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("message") or "").strip()
    if not text:
        return jsonify({"reponse": "Écris-moi ta question, je t'écoute."})
    row, suggestions = answer_question(text)
    db = get_db()
    db.execute("INSERT INTO chatlog (question, qna_id) VALUES (?,?)",
               (text, row["id"] if row else None))
    db.commit()
    if row:
        return jsonify({"reponse": row["reponse"], "categorie": row["categorie"],
                        "trouve": True})
    rep = ("Je n'ai pas encore la réponse à cette question — je l'ai notée pour que "
           "l'équipe l'ajoute à ma base. En attendant, le secrétariat de l'IAM peut "
           "te renseigner directement.")
    if suggestions:
        rep += " Peut-être que tu cherches : " + " ; ".join(
            f"« {s['question']} »" for s in suggestions)
    return jsonify({"reponse": rep, "trouve": False})


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
        "sans_reponse": db.execute(
            "SELECT COUNT(*) FROM chatlog WHERE qna_id IS NULL").fetchone()[0],
    }
    qnas = db.execute("SELECT * FROM qna ORDER BY categorie, id").fetchall()
    unmatched = db.execute(
        "SELECT * FROM chatlog WHERE qna_id IS NULL ORDER BY id DESC LIMIT 50").fetchall()
    return render_template("admin.html", locked=False, stats=stats, qnas=qnas,
                           unmatched=unmatched)


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
