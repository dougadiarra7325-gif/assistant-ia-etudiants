// Proxy sécurisé Gemini pour l'Assistant IAM — version Node (Render, Fly, VPS…)
// Aucune dépendance : `node server.js`
// La clé Gemini vient de la variable d'environnement GEMINI_API_KEY (réglages secrets de l'hébergeur),
// jamais du code, jamais du navigateur des visiteurs.
const http = require("http");

const SYSTEME = "Tu es l'assistant des étudiants de l'Université IAM (Institut Africain de Management) de Bamako, au Mali. Tu réponds en français simple et clair, en 2 à 6 phrases maximum, avec un ton aidant pour des étudiants. Faits sûrs : l'atelier IAM Code to Career est piloté par DataInsights, chef d'atelier Abdoulaye TRAORE ; horaires : lundi à vendredi 9h00-15h00 (vendredi 9h00-13h00) ; 12 projets d'équipe ; livrables : démonstration, code sur GitHub, présentation, projet intégré au CV et au profil en ligne. Règles strictes : n'invente JAMAIS de dates officielles (examens, inscriptions, résultats) ni de numéros de téléphone : pour ces sujets, dis de vérifier auprès du secrétariat ou de l'affichage officiel de l'IAM. Tu peux expliquer des notions de cours (programmation, informatique), donner des conseils d'étude, présenter l'IAM et ses grandes familles de parcours en précisant que les filières ouvertes varient selon le campus et l'année, aider à rédiger ou améliorer un CV étudiant, et répondre simplement à des questions générales de conversation. Tu tiens une vraie conversation suivie : si l'étudiant dit « et ensuite ? », « donne un exemple », « explique autrement » ou « et pour la L2 ? », appuie-toi sur l'historique de conversation fourni pour comprendre de quoi il parle, et réponds dans la continuité.";
const MODELES = ["gemini-2.5-flash", "gemini-2.5-flash", "gemini-2.0-flash"];
const ORIGINES_OK = ["https://dougadiarra7325-gif.github.io"];
const fs = require("fs");
const KEY_FILE = process.env.GEMINI_KEY_FILE || "";
const SETUP_TOKEN = process.env.SETUP_TOKEN || "";
let KEY = process.env.GEMINI_API_KEY || "";
if (!KEY && KEY_FILE) {
  try { KEY = fs.readFileSync(KEY_FILE, "utf8").trim(); } catch (e) { /* pas encore configurée */ }
}
const PORT = process.env.PORT || 8787;

function pageConfiguration() {
  return `<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Configuration — Assistant IAM</title>
<style>body{font-family:system-ui,sans-serif;background:#0b2545;color:#fff;margin:0;padding:24px}main{max-width:520px;margin:6vh auto;background:#fff;color:#14213a;border-radius:18px;padding:24px}h1{font-size:20px;margin:0 0 8px}p{line-height:1.55;font-size:14.5px}input{width:100%;padding:12px;border:1.5px solid #ccd;border-radius:10px;font-size:15px;box-sizing:border-box}button{margin-top:12px;background:#c9a227;color:#241a02;border:0;border-radius:10px;padding:12px 18px;font-weight:800;font-size:15px;width:100%}</style></head>
<body><main><h1>🔑 Activer la vraie IA de l'Assistant IAM</h1>
<p>Colle ta clé gratuite Google Gemini (elle commence par « AIza », récupérée sur <b>aistudio.google.com → Get API key</b>).</p>
<p>Elle est enregistrée <b>uniquement sur le serveur privé du proxy</b> : elle n'apparaît ni dans le site, ni dans le code, ni dans le chat. Cette page se désactive définitivement après l'enregistrement.</p>
<form method="POST" action="/setup"><input type="password" name="key" placeholder="AIza…" autocomplete="off" required><button type="submit">Activer</button></form>
</main></body></html>`;
}

function origineAutorisee(origin) {
  if (!origin) return false;
  if (ORIGINES_OK.includes(origin)) return true;
  return /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
}

async function appelerGemini(prompt) {
  let lastErr = "inconnu";
  for (let i = 0; i < MODELES.length; i++) {
    const modele = MODELES[i];
    if (i > 0) await new Promise(d => setTimeout(d, 1500));
    try {
      const url = "https://generativelanguage.googleapis.com/v1beta/models/" + modele + ":generateContent?key=" + encodeURIComponent(KEY);
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

// Service IA gratuit sans clé (Pollinations) — utilisé tant qu'aucune clé
// Gemini n'est configurée ; dès qu'une clé est enregistrée, Gemini reprend.
async function appelerIaLibre(prompt) {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 60000);
    const r = await fetch("https://text.pollinations.ai/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: ctrl.signal,
      body: JSON.stringify({ model: "openai", messages: [{ role: "user", content: prompt }] })
    });
    clearTimeout(timer);
    if (!r.ok) return { err: "HTTP " + r.status + " (service IA gratuit)" };
    const t = (await r.text()).trim();
    if (t) return { text: t };
    return { err: "réponse vide du service IA gratuit" };
  } catch (e) {
    return { err: "réseau (" + e.message + ")" };
  }
}

const server = http.createServer((req, res) => {
  const origin = req.headers.origin || "";
  const send = (code, obj, cors) => {
    const headers = { "Content-Type": "application/json; charset=utf-8" };
    if (cors) {
      headers["Access-Control-Allow-Origin"] = origin;
      headers["Access-Control-Allow-Methods"] = "POST, OPTIONS";
      headers["Access-Control-Allow-Headers"] = "Content-Type";
    }
    res.writeHead(code, headers);
    res.end(JSON.stringify(obj));
  };
  if (req.method === "OPTIONS") {
    if (!origineAutorisee(origin)) { res.writeHead(403); return res.end("Origine non autorisée"); }
    res.writeHead(204, {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    });
    return res.end();
  }
  if (req.method === "GET" && req.url === "/") return send(200, { ok: true, service: "Assistant IAM — proxy Gemini" }, false);
  if (req.url.startsWith("/setup")) {
    const u = new URL(req.url, "http://x");
    if (!SETUP_TOKEN || u.searchParams.get("token") !== SETUP_TOKEN) { res.writeHead(404); return res.end("Introuvable"); }
    if (KEY) { res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" }); return res.end("<p>✅ La clé est déjà configurée. Cette page est désactivée.</p>"); }
    if (req.method === "GET") { res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" }); return res.end(pageConfiguration()); }
    if (req.method === "POST") {
      let d = "";
      req.on("data", c => { d += c; if (d.length > 5000) req.destroy(); });
      req.on("end", () => {
        const k = String(new URLSearchParams(d).get("key") || "").trim();
        if (!/^AIza[0-9A-Za-z_\-]{20,}$/.test(k)) { res.writeHead(400, { "Content-Type": "text/html; charset=utf-8" }); return res.end("<p>❌ Cette clé ne ressemble pas à une clé Gemini (elle doit commencer par « AIza »). Recharge la page et réessaie.</p>"); }
        try { fs.writeFileSync(KEY_FILE, k, { mode: 0o600 }); KEY = k; }
        catch (e) { res.writeHead(500, { "Content-Type": "text/html; charset=utf-8" }); return res.end("<p>❌ Enregistrement impossible sur le serveur.</p>"); }
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        return res.end("<p>✅ Clé enregistrée et vraie IA activée ! Tu peux fermer cette page et retourner à l'Assistant IAM : il répond maintenant à toutes les questions.</p>");
      });
      return;
    }
  }
  if (req.method !== "POST") return send(405, { err: "Méthode non autorisée" }, false);
  if (!origineAutorisee(origin)) return send(403, { err: "Origine non autorisée" }, false);

  let data = "";
  req.on("data", c => { data += c; if (data.length > 20000) req.destroy(); });
  req.on("end", async () => {
    let body;
    try { body = JSON.parse(data || "{}"); } catch (e) { return send(400, { err: "Corps JSON invalide" }, true); }
    const question = String(body.question || "").trim();
    const contexte = String(body.contexte || "").slice(0, 6000);
    if (!question) return send(400, { err: "Question vide" }, true);
    if (question.length > 2000) return send(400, { err: "Question trop longue" }, true);
    let prompt = SYSTEME;
    if (contexte) prompt += "\n\nInformations et historique fournis par l'assistant (à utiliser en priorité si elles répondent) :\n" + contexte;
    prompt += "\n\nQuestion de l'étudiant : " + question;
    const out = KEY ? await appelerGemini(prompt) : await appelerIaLibre(prompt);
    send(200, out, true);
  });
});

server.listen(PORT, () => console.log("Proxy Assistant IAM en écoute sur le port " + PORT + (KEY ? " — moteur Gemini" : " — moteur IA gratuit sans clé (Pollinations)")));
