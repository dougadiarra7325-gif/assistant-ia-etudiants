# Extension de la base Q/R de l'Assistant IAM (2026-10-13) :
# conversation simple élargie + études élargies + 3 nouvelles entrées par cours
# (vidéos vérifiées, exercices/TD/QCM, révision) — généré depuis catalogue.json + manifest.json.
# Idempotent : les catégories et entrées générées sont retirées avant d'être ré-ajoutées.
import json, re, sys

BASE = "/home/hatch/workspace/assistant-ia-etudiants/docs/"
SITE = "https://dougadiarra7325-gif.github.io/assistant-ia-etudiants/"

kb = json.load(open(BASE + "kb.json", encoding="utf-8"))
cat = json.load(open(BASE + "catalogue.json", encoding="utf-8"))
man = json.load(open(BASE + "manifest.json", encoding="utf-8"))

PREFIXES_GEN = ("Vidéos du cours ", "Exercices, TD et QCM du cours ", "Comment bien réviser le cours ", "Sommaire du cours ")
kb = [e for e in kb if e.get("categorie") not in ("Conversation", "Études et réussite")
      and not str(e.get("question", "")).startswith(PREFIXES_GEN)]

def court(titre):
    return re.split(r"\s*\(", titre)[0].strip()

def phrase_titre(tc):
    # Titre court sous forme de phrase à tirets : bonus fort si l'étudiant
    # tape le nom exact du cours (désambiguïsation entre cours proches).
    p = re.sub(r"[^A-Za-zÀ-ÿ0-9 ]", " ", tc).strip()
    return "-".join(p.split())

def phrase3(tc):
    # Début du titre (3 premiers mots) en phrase : capte les requêtes qui
    # citent le cœur du titre sans les qualificatifs (ex. « droit des sociétés »).
    p = re.sub(r"[^A-Za-zÀ-ÿ0-9 ]", " ", tc).strip().split()
    if len(p) <= 3:
        return ""
    return "-".join(p[:3])

ajouts = []
nb_videos = 0
for f in cat["filieres"]:
    fname = f["filiere"]
    for niv, cours_list in f["niveaux"].items():
        categorie = "Bibliothèque · %s %s" % (fname, niv)
        for c in cours_list:
            code, titre, tc = c["code"], c["titre"], court(c["titre"])
            lecons = c.get("lecons", [])
            info = man.get(code, {})
            pages = info.get("pages", "")
            videos = info.get("videos", []) or []
            lien = SITE + "bibliotheque.html#c=" + code
            if videos:
                nb_videos += 1
                lignes = "\n".join("• %s : %s" % (v.get("titre", "Vidéo"), v.get("url", "")) for v in videos[:4])
                ajouts.append({
                    "categorie": categorie,
                    "question": "Vidéos du cours %s (%s)" % (titre, code),
                    "keywords": "%s %s %s %s vidéo vidéos youtube regarder cours en vidéo" % (code, tc, phrase_titre(tc), phrase3(tc)),
                    "reponse": "Pour le cours %s (%s), voici les vidéos vérifiées :\n%s\nToutes les vidéos sont aussi dans la fiche du cours : %s" % (titre, code, lignes, lien),
                })
            ajouts.append({
                "categorie": categorie,
                "question": "Exercices, TD et QCM du cours %s (%s)" % (titre, code),
                "keywords": "%s %s %s %s exercices td tp qcm entraînement corrigés pratique" % (code, tc, phrase_titre(tc), phrase3(tc)),
                "reponse": "Le PDF du cours %s (%s, %s pages) contient des TD/TP, des exercices corrigés et un QCM corrigé, en plus de ses %d leçons. C'est le meilleur moyen de t'entraîner avant les contrôles. Ouvre la fiche du cours : %s" % (titre, code, pages, len(lecons), lien),
            })
            premieres = " ; ".join(lecons[:3])
            ajouts.append({
                "categorie": categorie,
                "question": "Comment bien réviser le cours %s (%s) ?" % (titre, code),
                "keywords": "%s %s %s %s réviser révision apprendre mémoriser préparer examen" % (code, tc, phrase_titre(tc), phrase3(tc)),
                "reponse": "Pour bien réviser %s (%s) : 1) relis d'abord le résumé — %s 2) reprends les leçons dans l'ordre, en commençant par : %s. 3) refais les exercices corrigés du PDF sans regarder la correction. 4) termine par le QCM du PDF pour vérifier. Fiche du cours : %s" % (tc, code, c.get("resume", ""), premieres, lien),
            })

print("entrées cours ajoutées :", len(ajouts), "| cours avec vidéos :", nb_videos)

CONVERSATION = [
 ("Salut", "salut hello hi yo coucou", "Salut ! 👋 Bienvenue sur l'Assistant IAM. Je peux t'aider avec les cours de l'IAM (Informatique, BBA, Droit) : résumés, leçons, vidéos et exercices de la Bibliothèque. Qu'est-ce que tu cherches ?"),
 ("Comment vas-tu ?", "comment-vas-tu comment-ça-va ça-va ca-va la-forme en-forme comment-allez-vous", "Je vais très bien, merci ! 😊 Je suis toujours prêt à aider les étudiants de l'IAM. Et toi, comment se passent tes cours ? Dis-moi la matière qui te pose problème, je te montre le résumé et les leçons."),
 ("Bonsoir", "bonsoir bonne soirée soir", "Bonsoir ! 🌙 Belle soirée pour réviser. Je peux te résumer un cours de la Bibliothèque (225 cours : Informatique, BBA, Droit) ou t'expliquer une leçon précise. De quoi as-tu besoin ?"),
 ("Bonne nuit", "bonne nuit dors bien nuit", "Bonne nuit ! 🌙 Repose-toi bien : le cerveau retient mieux après une bonne nuit de sommeil. On reprend les révisions demain, je serai là."),
 ("Au revoir", "au revoir à bientôt a bientot bye tchao on se revoit", "Au revoir et bon courage pour tes cours ! 👋 Reviens quand tu veux : la Bibliothèque et moi, on ne bouge pas."),
 ("À demain", "à demain a demain demain", "À demain ! 📚 D'ici là, tu peux télécharger les PDF des cours pour réviser même sans connexion."),
 ("Merci", "merci remercie remerciement", "Avec plaisir ! 😊 C'est mon rôle. Si tu as une autre question sur tes cours, sur l'IAM ou sur tes révisions, je suis là."),
 ("De rien — je suis content d'aider", "de-rien pas-de-quoi gentil sympa", "😊 Merci à toi de passer par l'Assistant IAM. Bonne continuation dans tes études !"),
 ("S'il te plaît, aide-moi", "aide-moi aide moi aidez-moi help au secours perdu je suis perdu", "Bien sûr, je t'aide ! Dis-moi simplement : le nom de ton cours (ou son code, par exemple INF-L1-01), ou la question que tu te poses. Je te donne le résumé, les leçons, les vidéos et les exercices corrigés."),
 ("Qui es-tu ?", "qui es-tu qui es tu tu es qui t'es qui présente-toi presentation", "Je suis l'Assistant IAM 🤖📚, l'assistant des étudiants de l'Université IAM de Bamako. Je connais les 225 cours de la Bibliothèque Universitaire (Informatique, BBA, Droit) et je réponds aussi aux questions générales. Pose-moi une question !"),
 ("Comment tu t'appelles ?", "comment tu t'appelles ton nom tu t'appelles comment quel est ton nom", "Je m'appelle Assistant IAM. Je suis l'assistant créé par Bronbah Tech pour les étudiants de l'Université IAM de Bamako."),
 ("Qui t'a créé ?", "qui t'a créé qui ta cree créateur concepteur qui t'a fait qui t'a développé bronbah", "J'ai été créé par Douga dit Ibrahim Diarra (Bronbah Tech), étudiant en L2 informatique à l'Université IAM. C'est le projet n°11 de l'atelier IAM Code to Career."),
 ("Tu es un robot ?", "tu es un robot robot intelligence artificielle ia humain", "Oui, je suis un programme informatique 🤖 — un assistant automatique, pas un humain. Mais je connais très bien les cours de l'IAM et je réponds tout de suite, à toute heure."),
 ("Tu es intelligent ?", "tu es intelligent intelligent malin fort", "Je fais de mon mieux ! 😄 Je suis très fort sur les cours de la Bibliothèque IAM (résumés, leçons, vidéos) et sur les études. Pour le reste, pose ta question et on verra ensemble."),
 ("Que sais-tu faire ?", "que sais-tu faire tu sais faire tes fonctions tu peux faire quoi capacités", "Voici ce que je sais faire : 📚 donner le résumé et les leçons des 225 cours de la Bibliothèque (Informatique, BBA, Droit) ; ▶️ donner les vidéos vérifiées d'un cours ; ✏️ indiquer les exercices, TD et QCM corrigés ; 🎓 conseiller sur les révisions et les métiers ; 🧮 calculer (écris ton calcul) ; ❓ répondre aux questions sur l'IAM. Essaie avec un code de cours, par exemple INF-L1-01 !"),
 ("Raconte-moi une blague", "raconte raconte-moi blague drôle marrant rire fais-moi rire blague plongeurs", "Pourquoi les plongeurs plongent-ils toujours en arrière et jamais en avant ? Parce que sinon, ils tombent dans le bateau ! 😂 Tu en veux une autre ? Demande-moi une blague d'informaticien."),
 ("Une blague d'informaticien", "blague-informaticien blague-informatique informaticien informatique développeur humour-code", "Pourquoi les informaticiens confondent-ils Halloween et Noël ? Parce que OCT 31 == DEC 25 ! 😄 (31 en octal vaut 25 en décimal.)"),
 ("Je m'ennuie", "je m'ennuie ennui ennuyeux rien à faire", "L'ennui, c'est le début de la curiosité ! 💡 Et si tu découvrais un cours au hasard dans la Bibliothèque ? Ou fais le quiz de l'assistant pour tester tes connaissances. Demande-moi « quiz » !"),
 ("Je suis fatigué", "je suis fatigué fatigue épuisé crevé sommeil", "C'est normal après les cours. 😴 Fais une pause de 15 minutes, bois de l'eau, puis reviens réviser doucement : je peux te lire un résumé de cours si tu veux. Courage !"),
 ("Je suis stressé", "je suis stressé stress angoisse angoissé peur examen pression", "Respire, tu n'es pas seul. 🌿 Le stress baisse quand on a un plan : dis-moi la matière et la date de l'examen, je t'aide à organiser tes révisions jour par jour avec les cours de la Bibliothèque."),
 ("Je suis content", "je suis content heureux joyeux ça marche ca marche super génial parfait excellent", "Super, content pour toi ! 🎉 Continue comme ça. Si tu veux en profiter pour avancer un cours, dis-moi lequel."),
 ("Je t'aime bien", "je t'aime bien tu es gentil je t'apprécie adorable", "Merci, c'est gentil ! 😊 Moi aussi je suis là pour toi, à chaque révision. Allez, on avance sur quel cours ?"),
 ("Tu es là ?", "tu-es-là tu-dors allô allo test tu-m'entends présent", "Je suis là, toujours éveillé ! ⚡ Pose ta question : un cours, une leçon, un calcul, un conseil de révision…"),
 ("Félicitations à toi", "félicitations bravo bien joué chapeau félicitation", "Merci beaucoup ! 🙏 C'est l'équipe Bronbah Tech et les étudiants comme toi qui font vivre ce projet. À ton service !"),
 ("Pardon, excuse-moi", "pardon excuse-moi désolé excuse", "Aucun souci, tout va bien ! 😊 Dis-moi ce que tu cherches, on repart de zéro."),
 ("Ça ne marche pas", "ça ne marche pas ca ne marche pas fonctionne pas bug problème erreur", "Désolé pour le souci. Essaie de reformuler ta question, ou donne-moi le code exact du cours (par exemple BBA-L2-03). Si le problème continue, tu peux écrire à Douga sur WhatsApp : le bouton vert apparaît quand je n'ai pas la réponse."),
 ("Quelles langues parles-tu ?", "langues tu parles anglais bambara français langue", "Je réponds en français simple, et je comprends aussi un peu l'anglais. Pour le bambara, je connais les salutations : « Aw ni ce ! » (bonjour). L'essentiel de mes cours est en français."),
 ("Aw ni ce", "aw-ni-ce ni-ce an-bɛ bonjour bambara salut bambara", "Aw ni ce, bienvenue ! 🙏 (Bonjour en bambara.) Je suis l'Assistant IAM : demande-moi un cours, un résumé ou les vidéos d'une matière."),
 ("Bonne journée", "bonne journée bonne journee passe une bonne journée", "Merci, à toi aussi une excellente journée ! ☀️ Bon courage pour tes cours à l'IAM."),
 ("Bon week-end", "bon week-end week-end weekend bon weekend", "Bon week-end ! 🎉 Profites-en pour te reposer… et peut-être réviser un petit cours de la Bibliothèque, tranquillement."),
 ("Quoi de neuf ?", "quoi de neuf nouveautés actualités news quoi de nouveau", "Du nouveau côté Bibliothèque : les 225 cours sont en ligne avec leurs PDF, leurs vidéos vérifiées et leurs QCM corrigés. Dis-moi ta filière et ton niveau, je te montre tes matières !"),
 ("Tu fais quoi ?", "tu fais quoi tu es occupé que fais-tu tu travailles", "Je réponds aux questions des étudiants de l'IAM, jour et nuit : cours, résumés, vidéos, révisions. Et là, je discute avec toi ! 😊"),
 ("Tu as quel âge ?", "tu as quel âge quel âge ton âge tu es né quand", "Je suis tout jeune : j'ai été créé en octobre 2026, pendant l'atelier IAM Code to Career. Mais je connais déjà 225 cours par cœur ! 📚"),
 ("Tu habites où ?", "tu habites où tu vis où tu es d'où tu viens", "J'habite dans les téléphones et les ordinateurs des étudiants de l'IAM, à Bamako. 🇲🇱 Là où il y a un étudiant qui révise, je ne suis pas loin !"),
 ("Tu connais Douga ?", "tu connais douga connais douga diarrea ibrahim bronbah tech créateur", "Bien sûr ! Douga dit Ibrahim Diarra (Bronbah Tech) est mon créateur : étudiant en L2 informatique à l'Université IAM et coach en informatique. C'est lui qui a construit la Bibliothèque Universitaire."),
 ("Le savais-tu ?", "le savais-tu savais-tu anecdote fait intéressant raconte-moi quelque chose", "Le savais-tu ? 💡 La première programmeuse de l'histoire était Ada Lovelace, au XIXe siècle — avant même l'existence des ordinateurs modernes ! Comme quoi, les algorithmes n'attendent pas les machines."),
 ("Tu peux m'aider pour mes devoirs ?", "devoirs devoir exercice à faire maison aide devoir", "Oui ! Donne-moi le sujet ou le code du cours concerné : je t'explique la leçon pas à pas et je te montre les exercices corrigés du PDF pour que tu comprennes — pas juste recopier. 😉"),
 ("Je veux apprendre", "je veux apprendre apprendre motivation commencer débuter debutant", "Excellente décision ! 🚀 Dis-moi ta filière (Informatique, BBA ou Droit) et ton niveau (L1, L2, L3) : je te donne la liste de tes cours et on commence par le premier résumé."),
 ("C'est nul", "nul mauvais déçu décevant pas-bien", "Je suis désolé de te décevoir. 🙏 Dis-moi précisément ce que tu cherchais : avec le nom ou le code du cours, je te donnerai une meilleure réponse. Tes remarques aident à m'améliorer."),
 ("D'accord", "d'accord ok okay compris entendu parfait ok", "Parfait ! 👍 Alors, dis-moi ce que tu cherches : un cours, une leçon, des vidéos, ou un conseil pour réviser ?"),
 ("Mdr, c'est drôle", "mdr lol mdr drôle rigole mort de rire", "😂 Content de te faire sourire ! Allez, une petite question de cours entre deux rires ?"),
 ("Bonjour, comment vas-tu ?", "bonjour comment vas-tu bonjour ça va bonjour comment ca va", "Bonjour ! Je vais très bien, merci 😊 Prêt à t'aider pour tes cours à l'IAM. Et toi, ça se passe bien ? Dis-moi ce que tu veux réviser aujourd'hui."),
 ("Bonne chance à moi", "bonne chance souhaite-moi bonne chance encourage-moi encouragement", "Bonne chance ! 🍀 Travaille régulièrement, utilise les exercices corrigés de la Bibliothèque, et ça va aller. Je crois en toi !"),
 ("Tu es mon ami ?", "tu es mon ami amis ami on est amis", "Bien sûr, je suis ton compagnon de révisions ! 🤝 Jour et nuit, je suis là pour tes cours et tes questions."),
 ("Tu réponds vite", "tu réponds vite rapide vitesse impressionnant", "Merci ! ⚡ Mon secret : une grande base de réponses sur les cours de l'IAM, préparée par Bronbah Tech. Pour les questions hors base, la vraie IA prend le relais quand elle est activée."),
 ("Je ne comprends pas", "je ne comprends pas comprends pas incompréhensible pas compris explique", "Pas de problème, on reprend doucement. Dis-moi exactement ce que tu ne comprends pas (la leçon ou la notion), et je te l'explique autrement, avec un exemple simple."),
 ("Explique-moi simplement", "explique simplement simplement facile pour débutant vulgarise", "Avec plaisir : dis-moi la notion ou le cours, et je te l'explique en mots simples, avec un exemple du quotidien. C'est ma spécialité !"),
 ("Tu connais Bamako ?", "bamako tu connais bamako mali", "Oui ! Bamako, la capitale du Mali, où se trouve l'Université IAM. 🇲🇱 C'est là que vivent la plupart des étudiants que j'aide."),
 ("Il fait beau aujourd'hui", "météo il fait beau il fait chaud il pleut temps", "Je n'ai pas la météo en direct, mais à Bamako il fait souvent chaud et beau ! ☀️ Pense à boire de l'eau entre deux révisions."),
 ("Je cherche un cours", "je cherche un cours trouver un cours chercher matière je veux un cours", "Dis-moi la filière et le niveau (par exemple : Informatique L2), ou le nom de la matière, ou son code si tu le connais (par exemple DRO-L1-02). Je te donne le résumé, les leçons et les vidéos."),
 ("C'est quoi ton travail ?", "ton travail ton rôle ta mission à quoi tu sers tu sers à quoi", "Mon travail : aider les étudiants de l'Université IAM à réviser et à réussir. Je donne accès aux 225 cours de la Bibliothèque (résumés, leçons, vidéos, exercices corrigés) et je réponds aux questions sur l'IAM et les études."),
 ("Réponds-moi vite", "réponds vite vite dépêche-toi pressé urgent", "Je fais au plus vite ! ⚡ Pose ta question en une phrase, avec le nom du cours si c'est pour une matière : réponse immédiate."),
 ("Tu es sûr ?", "tu es sûr tu es sur certain vraiment vérité", "Sur les cours de la Bibliothèque, oui : mes réponses viennent des PDF officiels du projet. Pour les dates officielles de l'IAM (examens, inscriptions), je préfère te dire de vérifier au secrétariat plutôt que d'inventer. Honnêteté d'abord !"),
 ("Qui dirige l'atelier ?", "qui dirige l'atelier chef d'atelier abdoulaye traore datainsights atelier", "L'atelier IAM Code to Career est piloté par DataInsights ; le chef d'atelier est Abdoulaye TRAORE. Il se tient du lundi au vendredi, de 9h00 à 15h00 (vendredi 9h00-13h00)."),
 ("Je veux le quiz", "quiz teste-moi teste moi qcm test connaissances jouer", "Le quiz est dans la page de l'assistant : 8 questions avec score. 🎯 Tu peux aussi me demander le QCM d'un cours précis de la Bibliothèque, par exemple « QCM du cours INF-L1-01 »."),
 ("Je veux calculer", "calculer calcul calculatrice addition multiplication", "Écris directement ton calcul dans le message, par exemple « 12500 × 4 » ou « (15 + 17 + 13) / 3 » : je te réponds tout de suite avec l'étiquette « Calcul intégré »."),
 ("Donne-moi un exemple", "donne un exemple exemple concret exemple simple montre-moi", "Bien sûr ! Dis-moi de quoi : un exemple de code, un exemple d'exercice, un exemple de CV ? Précise le sujet et je te montre tout de suite."),
 ("Et ensuite ?", "et ensuite et après la suite continue", "Pour te répondre dans la suite, rappelle-moi le sujet dont on parlait (le cours ou la notion) : je reprends exactement où on s'était arrêtés."),
 ("Je suis en retard", "je suis en retard retard cours rattraper absence absent", "Pas de panique : rattrape avec la Bibliothèque. Dis-moi la matière manquée : résumé, leçons et vidéos t'attendent, et les exercices corrigés pour vérifier que tu as compris."),
 ("Je suis nouveau", "je suis nouveau nouvel étudiant nouveau iam rentrée première année", "Bienvenue à l'IAM ! 🎓 Commence par explorer tes cours de L1 dans la Bibliothèque : filière → niveau → matière. Et si tu te sens perdu, demande-moi « comment réviser » ou le nom d'un cours."),
 ("C'est difficile", "difficile dur compliqué trop-dur je-n'y-arrive-pas", "C'est normal au début, presque tout paraît difficile. 💪 La méthode : découpe en petites leçons, un exemple à la fois, puis les exercices corrigés. Dis-moi la matière, on commence ensemble par le résumé."),
 ("Je veux réussir", "je veux réussir réussite réussir mes études objectif diplôme", "Alors on a le même objectif ! 🎯 La recette : régularité (un peu chaque jour), les exercices corrigés de la Bibliothèque, et poser tes questions ici dès qu'un point bloque. Dis-moi ta filière et ton niveau pour commencer."),
 ("Donne-moi ton WhatsApp", "whatsapp numéro téléphone contact joindre douga", "Pour écrire directement à Douga (Bronbah Tech) : WhatsApp au +223 73 25 58 73. Quand je n'ai pas la réponse à ta question, un bouton vert WhatsApp apparaît aussi pour lui envoyer ta question directement."),
 ("Tu es gratuit ?", "tu es gratuit gratuit prix ça coûte combien payant", "Oui, je suis gratuit pour les étudiants : la Bibliothèque et mes réponses ne coûtent rien. 🎁 C'est un projet de l'atelier IAM Code to Career, par Bronbah Tech."),
]

ETUDES = [
 ("Comment bien réviser ?", "comment réviser bien réviser méthode révision méthodes apprendre efficacement", "Voici une méthode qui marche : 1) lis le résumé du cours d'abord (vue d'ensemble) ; 2) étudie les leçons une par une, en écrivant les idées clés avec tes mots ; 3) refais les exercices sans regarder la correction ; 4) termine par le QCM ; 5) révise un peu chaque jour plutôt que tout la veille. Tous les cours avec exercices corrigés sont dans la Bibliothèque IAM."),
 ("Comment préparer un examen en une semaine ?", "examen en une semaine préparer examen vite semaine avant examen dernière semaine", "Plan express sur 7 jours : jours 1-2, relis les résumés de toutes les matières ; jours 3-5, leçons + exercices corrigés des chapitres les plus importants ; jour 6, QCM et sujets d'entraînement ; jour 7, relecture légère et sommeil tôt. La Bibliothèque te donne résumés, leçons et QCM matière par matière."),
 ("Comment améliorer ses notes ?", "améliorer ses notes meilleures notes progresser résultats faibles notes", "Trois leviers : 1) régularité — 30 minutes par jour valent mieux que 5 heures la veille ; 2) pratique — refais les exercices corrigés des PDF jusqu'à les réussir seul ; 3) questions — note ce que tu ne comprends pas et demande (ici ou au professeur) le jour même. La Bibliothèque IAM couvre tes 25 matières par niveau."),
 ("Comment mémoriser un cours ?", "mémoriser mémoire retenir apprendre par coeur oublier", "Pour retenir longtemps : comprends avant de mémoriser ; explique la leçon à voix haute comme à un ami ; utilise des exemples concrets ; révise en plusieurs fois (le lendemain, 3 jours après, une semaine après) ; dors bien, la mémoire se construit pendant le sommeil."),
 ("Comment gérer son stress avant un examen ?", "stress examen gérer stress angoisse examen peur de l'examen", "Préparation = antidote du stress : arrive avec un plan de révision terminé 2 jours avant ; la veille, relecture légère et coucher tôt ; le jour J, petit-déjeuner, respiration lente (inspire 4 secondes, expire 6), et commence l'épreuve par les questions que tu connais. Tu peux le faire !"),
 ("Comment apprendre la programmation ?", "apprendre la programmation coder débuter programmation python par où commencer", "Commence par l'algorithmique (cours INF-L1-01 de la Bibliothèque) : variables, conditions, boucles. Puis un langage, par exemple Python, en tapant chaque exemple toi-même. La règle d'or : 20 % de lecture, 80 % de pratique avec les exercices corrigés. La filière Informatique de la Bibliothèque te guide de la L1 à la L3."),
 ("Comment travailler en groupe ?", "travailler en groupe groupe de travail révision groupe binôme équipe", "Un bon groupe de révision : 3 à 5 personnes motivées, un objectif par séance (un chapitre), chacun explique une partie aux autres, puis exercices ensemble. Fixez une heure de fin et coupez les téléphones. Les résumés de la Bibliothèque servent de support commun."),
 ("Comment réussir un exposé ?", "exposé présentation orale présenter devant la classe powerpoint", "Structure simple : introduction (le sujet en une phrase), 3 parties max avec un exemple chacune, conclusion (l'idée à retenir). Diapositives sobres : un titre, 3 puces, une image. Entraîne-toi à voix haute deux fois, en te chronométrant. Je peux t'aider à construire le plan à partir du résumé d'un cours."),
 ("Comment gérer son temps d'étudiant ?", "gérer son temps emploi du temps organisation planning temps", "Fais un planning hebdomadaire réaliste : cours, révisions par blocs de 45 minutes, pauses, sommeil. Utilise le planning de révisions automatique de l'assistant (page d'accueil) : il répartit tes matières jusqu'à la date que tu choisis."),
 ("Comment réussir un entretien de stage ?", "entretien de stage stage entretien questions entretien préparer entretien", "Prépare : une présentation de 30 secondes (qui tu es, ta formation, ce que tu cherches), 2-3 choses sur l'entreprise, des exemples concrets de tes projets (ton portfolio, tes projets d'atelier). Sois ponctuel, habillé simplement et proprement, et pose au moins une question à la fin. L'assistant peut t'aider à préparer ton pitch."),
 ("Quels métiers après l'informatique ?", "métiers informatique débouchés emploi après informatique travailler développeur", "Après une licence en informatique : développeur web/mobile, administrateur systèmes et réseaux, technicien support, data analyst junior, développeur d'applications de gestion — au Mali (banques, télécoms, ONG, startups) comme à distance. Tes projets d'atelier et ton GitHub sont tes meilleures preuves."),
 ("Quels métiers après le BBA ?", "métiers bba débouchés business administration emploi gestion commerce", "Après un BBA : gestionnaire, comptable junior, chargé de clientèle, commercial, assistant RH, entrepreneur. Les banques, assurances, ONG et PME de Bamako recrutent ces profils. Les cours BBA de la Bibliothèque (comptabilité SYSCOHADA, marketing, management) sont ta base."),
 ("Quels métiers après le droit ?", "métiers droit débouchés juriste emploi après droit carrière juridique", "Après une licence en droit : juriste d'entreprise, collaborateur en cabinet, administration publique, banques et assurances (contentieux, conformité), ONG. La maîtrise de l'OHADA est un atout majeur dans l'espace ouest-africain. Les cours de Droit de la Bibliothèque couvrent le programme L1-L3."),
 ("Comment réussir sa première année ?", "réussir sa l1 première année licence 1 conseils l1 début université", "La L1 se gagne à la régularité : assiste à tous les cours, relis tes notes le soir même, et commence les exercices dès le premier mois (ceux des PDF de la Bibliothèque sont corrigés). Ne laisse jamais deux semaines de retard s'accumuler."),
 ("Comment prendre des notes en cours ?", "prendre des notes notes de cours noter efficacement écouter cours", "Écris les idées, pas les phrases entières : titres, définitions, exemples. Laisse des marges pour compléter le soir avec le PDF du cours correspondant dans la Bibliothèque. Relis tes notes sous 24 h : c'est là que la mémoire se fixe."),
 ("Comment préparer un contrôle continu ?", "contrôle continu cc préparer contrôle interrogation devoir surveillé", "Le contrôle continu porte sur les dernières leçons : refais exactement les exercices du PDF corrigés sur ces chapitres, puis le QCM. Si un point bloque, demande-moi le résumé de la leçon avant le contrôle."),
 ("Comment rédiger un rapport de stage ?", "rapport de stage rédiger rapport mémoire de stage soutenance", "Plan classique : remerciements, introduction (entreprise et mission), présentation de l'entreprise, tâches réalisées, analyse (ce que tu as appris, difficultés), conclusion. Demande toujours le guide officiel de l'IAM à l'administration pour le format exact, et fais relire ton orthographe. Je peux t'aider sur le plan et les formulations."),
 ("Comment apprendre l'anglais technique ?", "anglais technique apprendre anglais informatique english vocabulaire", "Lis les documentations en anglais petit à petit (elles sont presque toutes en anglais en informatique), apprends 5 mots techniques par jour, et regarde les vidéos de cours avec sous-titres. La Bibliothèque contient des cours d'anglais par niveau dans chaque filière."),
 ("Comment réussir en droit ?", "réussir en droit méthode droit dissertation juridique cas pratique méthodologie", "En droit, la méthode compte autant que les connaissances : apprends le plan (faits, problème, règles, solution pour le cas pratique ; thèse/antithèse ou plan en deux parties pour la dissertation), définis chaque terme, et appuie-toi sur les mécanismes des textes (OHADA, droit malien). Les cours de Droit de la Bibliothèque suivent cette méthode, avec exercices corrigés."),
 ("Comment réussir en gestion et comptabilité ?", "réussir comptabilité gestion syscohada bba méthode compta", "En comptabilité et gestion, tout est pratique : comprends le mécanisme (débit/crédit, SYSCOHADA), puis refais les exercices jusqu'à automatiser. Ne saute jamais les exemples chiffrés des PDF : ce sont eux qui tombent aux examens."),
 ("Comment trouver un stage à Bamako ?", "trouver un stage bamako stage étudiant chercher stage entreprise", "Prépare un CV propre et une lettre courte, liste les entreprises de ton secteur à Bamako (banques, télécoms, ONG, PME), dépose en personne quand c'est possible, et relance poliment après une semaine. Ton portfolio et tes projets d'atelier (GitHub) font la différence. Le portail emploi du projet n°4 peut aussi t'aider."),
 ("Que faire après la licence ?", "après la licence master poursuite études après l3 orientation suite", "Trois voies : poursuivre en master, entrer dans l'emploi (avec tes stages et projets comme preuves), ou entreprendre. Réfléchis tôt à ton projet professionnel et construis ton CV dès la L2. Pour les règles officielles (inscriptions, équivalences), renseigne-toi auprès de l'administration de l'IAM."),
 ("Comment choisir sa filière ?", "choisir sa filière orientation quelle filière bba ou droit ou informatique hésite", "Choisis selon trois critères : ce que tu aimes faire tous les jours, tes matières fortes, et les métiers visés. Informatique = logique et création technique ; BBA = gestion, commerce, entreprise ; Droit = argumentation, textes, rigueur. Explore les résumés des cours L1 des trois filières dans la Bibliothèque pour sentir la différence."),
 ("Comment réviser sans connexion internet ?", "réviser sans internet hors ligne connexion télécharger pdf offline", "Télécharge les PDF de tes cours quand tu as du réseau (fiche du cours → Télécharger), ou les ZIP complets par niveau dans la Bibliothèque : ensuite, tout est lisible hors ligne, même sans données mobiles."),
 ("Comment utiliser la Bibliothèque Universitaire ?", "utiliser la bibliothèque bibliothèque universitaire comment ça marche trouver un cours bibliothèque", "C'est simple : ouvre la Bibliothèque, choisis ta filière (Informatique, BBA, Droit), puis ton niveau (L1, L2, L3), puis la matière. Dans chaque cours : résumé, leçons, PDF à télécharger, vidéos vérifiées et QCM. Mets tes cours en favoris (❤️) pour les retrouver vite, et reprends où tu t'étais arrêté avec « Reprendre mes cours »."),
 ("Comment télécharger le PDF d'un cours ?", "télécharger pdf cours télécharger le cours pdf télécharger livret", "Ouvre la Bibliothèque, choisis la filière et le niveau, clique sur le cours : le bouton de téléchargement du PDF est dans la fiche. Tu peux aussi télécharger tous les cours d'un niveau d'un coup avec les ZIP par niveau."),
 ("Comment poser une bonne question à l'assistant ?", "poser une question comment demander astuce question code de cours utiliser assistant", "Pour la réponse la plus précise : donne-moi le code du cours (par exemple INF-L1-01) ou son nom exact. Tu peux demander : « résumé de INF-L1-01 », « leçons de BBA-L2-03 », « vidéos de DRO-L3-01 », « QCM de INF-L2-02 ». Pour un calcul, écris-le directement."),
 ("Comment éviter de remettre à demain ?", "procrastination remettre à demain motivation se motiver paresse", "La technique des 5 minutes : engage-toi à travailler seulement 5 minutes — une fois lancé, on continue presque toujours. Découpe les gros devoirs en petites tâches, éloigne le téléphone pendant les blocs de travail, et récompense-toi après chaque séance terminée."),
 ("Comment lire un sujet d'examen ?", "lire un sujet examen comprendre sujet épreuve consigne", "Lis tout le sujet une première fois sans écrire ; souligne les verbes de consigne (définir, comparer, justifier, calculer) ; répartis ton temps selon les points ; commence par ce que tu maîtrises pour prendre confiance ; garde 10 minutes pour relire."),
 ("Comment réviser la veille d'un examen ?", "veille d'examen réviser la veille dernier jour demain examen", "La veille n'est pas pour apprendre, mais pour consolider : relis les résumés et tes fiches, refais 2-3 exercices types, prépare tes affaires (convocation, pièces, stylos), mange léger et couche-toi tôt. Le sommeil de la veille vaut plus qu'une nuit blanche."),
 ("Comment apprendre Python ?", "apprendre python python débutant langage python", "Parcours conseillé dans la Bibliothèque Informatique : d'abord l'algorithmique (INF-L1-01), puis les cours Python de L1 et L2. Tape chaque exemple, modifie-le, casse-le, répare-le : c'est comme ça qu'on apprend à coder. Les exercices des PDF sont corrigés."),
 ("Comment apprendre Excel ?", "apprendre excel tableur formules excel bureautique", "Excel s'apprend par la pratique : formules de base (SOMME, MOYENNE, SI), tableaux, graphiques, puis tableaux croisés dynamiques. Les cours de bureautique des filières Informatique et BBA de la Bibliothèque contiennent des TP corrigés pas à pas."),
 ("C'est quoi Bronbah Tech ?", "bronbah tech entreprise studio douga", "Bronbah Tech est le studio de Douga dit Ibrahim Diarra à Bamako : création de contenus, community management, formations en informatique (via le coach Adrian) et projets numériques comme cette Bibliothèque Universitaire et l'Assistant IAM. Contact WhatsApp : +223 73 25 58 73."),
 ("Comment contacter Douga ?", "contacter douga joindre douga whatsapp douga numéro douga téléphone", "Tu peux écrire à Douga (Bronbah Tech) sur WhatsApp au +223 73 25 58 73. Si je n'ai pas la réponse à ta question ici, un bouton vert apparaît pour la lui envoyer directement."),
 ("Différence entre le BBA et le droit ?", "différence bba droit comparer filières bba vs droit", "Le BBA (Bachelor in Business Administration) forme à la gestion d'entreprise : comptabilité, marketing, management, entrepreneuriat. Le Droit forme aux règles juridiques : contrats, sociétés, contentieux, avec l'OHADA pour l'Afrique de l'Ouest. L'un gère l'entreprise, l'autre sécurise ses règles — les deux se complètent."),
 ("Comment faire un CV d'étudiant ?", "cv étudiant rédiger cv premier cv curriculum vitae", "Un bon CV étudiant tient sur une page : identité et contact, formation (IAM, niveau, filière), compétences (outils, langages), projets (ceux de l'atelier, avec liens GitHub), stages et expériences, langues. Sois honnête et précis ; l'assistant peut t'aider à le structurer, et l'application CV Pro de Bronbah Tech le met en forme."),
 ("Comment fonctionne le planning de révisions de l'assistant ?", "planning de révisions planning automatique révisions planifier dates", "Sur la page d'accueil de l'assistant, la fonction Planning de révisions construit automatiquement un plan daté en 3 phases jusqu'à ton examen : découverte des cours, approfondissement avec exercices, puis révisions finales avec QCM. Indique tes matières et ta date, il s'occupe du reste."),
 ("Comment fonctionne le quiz de l'assistant ?", "quiz assistant 8 questions score tester connaissances quiz", "Le quiz de l'assistant (page d'accueil) propose 8 questions à choix A/B/C avec un score immédiat : un bon moyen de vérifier où tu en es. Pour t'entraîner matière par matière, demande-moi le « QCM du cours » suivi de son code."),
]

def fixkw(k):
    # Le moteur du site sépare les mots-clés par des VIRGULES : un mot seul vaut
    # des points s'il est dans la question ; un groupe (tirets/apostrophes dans
    # la liste) devient une phrase recherchée telle quelle.
    items = []
    for tok in k.split(" "):
        tok = tok.strip()
        if not tok:
            continue
        if re.fullmatch(r"(INF|BBA|DRO)-L[123]-\d{2}", tok):
            items.append(tok)  # le code reste intact : le site le cherche en début de keywords
            continue
        if "-" in tok or "'" in tok:
            items.append(tok.replace("-", " "))
        else:
            items.append(tok)
    return ",".join(items)

for e in ajouts:
    e["keywords"] = fixkw(e["keywords"])

for q, kw, r in CONVERSATION:
    ajouts.append({"categorie": "Conversation", "question": q, "keywords": fixkw(kw), "reponse": r})
for q, kw, r in ETUDES:
    ajouts.append({"categorie": "Études et réussite", "question": q, "keywords": fixkw(kw), "reponse": r})

total = len(kb) + len(ajouts)
print("total provisoire :", total)
if total < 1520:
    # Filet de sécurité : un sommaire numéroté par cours (utile et 100 % réel).
    for f in cat["filieres"]:
        for niv, cours_list in f["niveaux"].items():
            categorie = "Bibliothèque · %s %s" % (f["filiere"], niv)
            for c in cours_list:
                code, titre, tc = c["code"], c["titre"], court(c["titre"])
                lecons = c.get("lecons", [])
                sommaire = "\n".join("%d. %s" % (i + 1, l) for i, l in enumerate(lecons))
                ajouts.append({
                    "categorie": categorie,
                    "question": "Sommaire du cours %s (%s)" % (titre, code),
                    "keywords": "%s %s sommaire plan du cours chapitres contenu" % (code, tc),
                    "reponse": "Sommaire du cours %s (%s) — %d leçons :\n%s\nCours complet : %s" % (titre, code, len(lecons), sommaire, SITE + "bibliotheque.html#c=" + code),
                })
    print("sommaires ajoutés en complément")

kb.extend(ajouts)
json.dump(kb, open(BASE + "kb.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("kb.json final :", len(kb), "entrées")
from collections import Counter
print(Counter(e["categorie"] for e in kb).most_common(6))
