# Assistant IA pour étudiants — projet n°11

**Projet n°11 « Assistant IA pour étudiants »** de l'atelier **IAM Code to Career** (Université IAM, Bamako — DataInsights).
Réalisé par **Douga dit Ibrahim Diarra**, étudiant en Licence 2 informatique.

Chatbot en français qui répond aux questions fréquentes des étudiants : **atelier Code to Career, emplois du temps, examens, procédures administratives, règlements, orientation**.
Application portable : Python + Flask + **SQLite**.

## Comment ça marche

- **Base de connaissances** : 26 questions/réponses documentées (table `qna`), couvrant l'atelier (horaires, 12 projets, livrables, pitch), l'administration (inscription, certificat de scolarité, relevé de notes, carte d'étudiant), les examens, les règlements généraux et l'orientation.
- **Moteur de réponse** : normalisation du texte (accents, casse), recherche par mots-clés pondérés + recouvrement avec les questions connues. Il comprend les questions écrites sans accents.
- **Honnêteté** : quand il ne sait pas, l'assistant le dit, **enregistre la question** (table `chatlog`) et propose des questions proches. Aucune réponse inventée.
- **Espace admin du propriétaire** : voir les statistiques, la liste des **questions sans réponse** à traiter, **ajouter de nouvelles questions/réponses** (l'assistant y répond aussitôt), supprimer, **exporter la base en CSV**.
- **Documentation publique** : page `/questions` listant toutes les questions/réponses + export JSON — c'est la « documentation des questions/réponses » demandée par le programme.
- **Piste WhatsApp** (demandée comme « intégration possible » par le programme) : le même moteur peut être branché derrière l'API WhatsApp Business — l'auteur a déjà construit un agent WhatsApp complet (voir le dépôt `bronbah-whatsapp-agent`) ; l'endpoint `/api/chat` (JSON) est prêt pour ce branchement.

Tables SQL : `users`, `qna`, `chatlog` (voir `schema.sql`). Mots de passe hachés, jamais affichés ni exportés.

## Lancer en local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
# → http://localhost:5001
```

## Déployer sur Render (gratuit)

1. Compte sur [render.com](https://render.com).
2. **New → Blueprint** → ce dépôt (Render lit `render.yaml`).
3. L'URL fournie par Render est l'adresse publique de l'assistant.

> Note : sur l'offre gratuite, le disque est temporaire — la base repart des 26 questions de départ après un redéploiement (les ajouts admin aussi). Pour une base permanente, ajouter un *Persistent Disk* (option payante).

## Liens

- Portail emploi (projet n°4) : https://github.com/dougadiarra7325-gif/portail-emploi-mali
- Portfolio de l'auteur (projet n°12) : https://dougadiarra7325-gif.github.io/portfolio-douga-diarra/
- LinkedIn : https://www.linkedin.com/in/douga-diarra-1b2129390
