# Proxy sécurisé Gemini — Assistant IAM

## Pourquoi un proxy ?

L'Assistant IAM est un site statique (GitHub Pages). Si la clé Gemini était écrite
dans la page, **tout le monde pourrait la lire** (code source, onglet Réseau) et
l'utiliser à la place du propriétaire.

Avec ce proxy, la clé reste **côté serveur, comme secret** :

- le navigateur envoie seulement la question au proxy ;
- le proxy appelle Google Gemini avec la clé secrète ;
- le navigateur reçoit seulement la réponse ;
- la clé n'apparaît **jamais** dans le site, ni dans le code public.

## Option recommandée : Cloudflare Workers (gratuit)

1. Va sur https://dash.cloudflare.com → crée un compte gratuit (ou connecte-toi).
2. **Workers & Pages → Create application → Create Worker** → nomme-le
   `assistant-iam-proxy` → **Deploy**.
3. **Edit code** : efface le code d'exemple, colle tout le contenu de
   `cloudflare-worker.js` (ce dossier), puis **Deploy**.
4. **Settings → Variables and Secrets → Add** :
   - Type : **Secret**
   - Name : `GEMINI_API_KEY`
   - Value : ta clé gratuite Google AI Studio (commence par « AIza »,
     récupérée sur https://aistudio.google.com/apikey)
   → **Deploy** pour appliquer.
5. Copie l'adresse du Worker, du type :
   `https://assistant-iam-proxy.<ton-compte>.workers.dev`
6. Dis cette adresse à Muse (une adresse n'est **pas** un secret) : il la mettra
   dans `ASSISTANT_PROXY_URL` du site, republiera, et vérifiera que l'assistant
   répond aux questions hors base pour tous les visiteurs.

## Option alternative : Node (Render, Fly.io, VPS…)

- Commande de démarrage : `node server.js`
- Variable d'environnement (réglages secrets de l'hébergeur) : `GEMINI_API_KEY`
- Le service expose `GET /` (contrôle) et `POST /` (questions au format JSON
  `{ "question": "…", "contexte": "…" }`, réponse `{ "text": "…" }` ou `{ "err": "…" }`).

## Sécurité intégrée

- Origines autorisées : uniquement le site officiel
  `https://dougadiarra7325-gif.github.io` (+ localhost pour les tests).
- Le prompt système est construit **côté serveur** : un visiteur ne peut pas
  transformer le proxy en « Gemini gratuit général » avec son propre prompt
  (il ne contrôle que sa question d'étudiant, longueur limitée).
- Aucune clé dans le code : le Worker lit le secret `GEMINI_API_KEY`, le serveur
  Node lit la variable d'environnement du même nom.
- Pense à activer une **limite de débit** (rate limiting) dans le tableau de bord
  Cloudflare si le site devient très visité, et à surveiller le quota de la clé
  dans Google AI Studio.

## Après le déploiement

Donne à Muse **uniquement l'adresse publique du proxy** (jamais la clé).
Il branchera le site dessus et testera une vraie question hors base.
