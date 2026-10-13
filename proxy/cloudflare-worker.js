// Proxy sécurisé Gemini pour l'Assistant IAM (Bronbah Tech)
// La clé Gemini est stockée comme SECRET du Worker (variable GEMINI_API_KEY),
// jamais dans le code du site, jamais visible par les visiteurs.
//
// Déploiement rapide (voir README.md) :
//   1. Cloudflare Dashboard → Workers & Pages → Create → coller ce fichier
//      (ou `npx wrangler deploy` dans ce dossier)
//   2. Settings → Variables and Secrets → Add secret : GEMINI_API_KEY = ta clé « AIza… »
//   3. Copier l'adresse du Worker (https://assistant-iam-proxy.<compte>.workers.dev)
//      et la mettre dans ASSISTANT_PROXY_URL (docs/index.html)

const SYSTEME = "Tu es l'assistant des étudiants de l'Université IAM (Institut Africain de Management) de Bamako, au Mali. Tu réponds en français simple et clair, en 2 à 6 phrases maximum, avec un ton aidant pour des étudiants. Faits sûrs : l'atelier IAM Code to Career est piloté par DataInsights, chef d'atelier Abdoulaye TRAORE ; horaires : lundi à vendredi 9h00-15h00 (vendredi 9h00-13h00) ; 12 projets d'équipe ; livrables : démonstration, code sur GitHub, présentation, projet intégré au CV et au profil en ligne. Règles strictes : n'invente JAMAIS de dates officielles (examens, inscriptions, résultats) ni de numéros de téléphone : pour ces sujets, dis de vérifier auprès du secrétariat ou de l'affichage officiel de l'IAM. Tu peux expliquer des notions de cours (programmation, informatique), donner des conseils d'étude, présenter l'IAM et ses grandes familles de parcours en précisant que les filières ouvertes varient selon le campus et l'année, aider à rédiger ou améliorer un CV étudiant, et répondre simplement à des questions générales de conversation. Tu tiens une vraie conversation suivie : si l'étudiant dit « et ensuite ? », « donne un exemple », « explique autrement » ou « et pour la L2 ? », appuie-toi sur l'historique de conversation fourni pour comprendre de quoi il parle, et réponds dans la continuité.";

const MODELES = ["gemini-2.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"];
const ORIGINES_OK = [
  "https://dougadiarra7325-gif.github.io"
];

function origineAutorisee(origin) {
  if (!origin) return false;
  if (ORIGINES_OK.includes(origin)) return true;
  return /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin); // tests locaux
}

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };
}

async function appelerGemini(key, prompt) {
  let lastErr = "inconnu";
  for (let i = 0; i < MODELES.length; i++) {
    const modele = MODELES[i];
    if (i > 0) await new Promise(d => setTimeout(d, 1500));
    try {
      const url = "https://generativelanguage.googleapis.com/v1beta/models/" + modele + ":generateContent?key=" + encodeURIComponent(key);
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 60000);
      const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: ctrl.signal,
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.4, maxOutputTokens: 500, thinkingConfig: { thinkingBudget: 0 } }
        })
      });
      clearTimeout(timer);
      if (!r.ok) { lastErr = "HTTP " + r.status + " (" + modele + ")"; continue; }
      const data = await r.json();
      const t = (data.candidates?.[0]?.content?.parts || []).map(p => p.text || "").join("").trim();
      if (t) return { text: t };
      lastErr = "réponse vide de Google (" + modele + ")";
    } catch (e) {
      lastErr = "réseau (" + e.message + ")";
    }
  }
  return { err: lastErr };
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") {
      if (!origineAutorisee(origin)) return new Response("Origine non autorisée", { status: 403 });
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    if (request.method !== "POST") {
      return new Response(JSON.stringify({ err: "Méthode non autorisée" }), { status: 405, headers: { "Content-Type": "application/json" } });
    }
    if (!origineAutorisee(origin)) {
      return new Response(JSON.stringify({ err: "Origine non autorisée" }), { status: 403, headers: { "Content-Type": "application/json" } });
    }
    const headers = corsHeaders(origin);
    const key = env.GEMINI_API_KEY;
    if (!key) {
      return new Response(JSON.stringify({ err: "Clé Gemini non configurée sur le serveur (secret GEMINI_API_KEY manquant)." }), { status: 500, headers });
    }
    let body;
    try { body = await request.json(); } catch (e) {
      return new Response(JSON.stringify({ err: "Corps JSON invalide" }), { status: 400, headers });
    }
    const question = String(body.question || "").trim();
    const contexte = String(body.contexte || "").slice(0, 6000);
    if (!question) return new Response(JSON.stringify({ err: "Question vide" }), { status: 400, headers });
    if (question.length > 2000) return new Response(JSON.stringify({ err: "Question trop longue" }), { status: 400, headers });

    let prompt = SYSTEME;
    if (contexte) prompt += "\n\nInformations et historique fournis par l'assistant (à utiliser en priorité si elles répondent) :\n" + contexte;
    prompt += "\n\nQuestion de l'étudiant : " + question;

    const res = await appelerGemini(key, prompt);
    return new Response(JSON.stringify(res), { status: 200, headers });
  }
};
