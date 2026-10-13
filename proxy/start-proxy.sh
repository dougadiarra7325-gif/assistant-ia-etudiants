#!/bin/bash
# (Re)démarre le proxy Assistant IAM hébergé sur la machine de Muse + son tunnel public.
# Clé Gemini : ~/workspace/assistant-proxy-data/gemini-key.txt (mode 600, hors dépôt, jamais lue par Muse).
# Tunnel : SSH vers localhost.run à travers le proxy de sortie HTTP (CONNECT) — cloudflared direct est bloqué ici.
DATA="$HOME/workspace/assistant-proxy-data"
mkdir -p "$DATA"
cd "$HOME/workspace/assistant-ia-etudiants/proxy" || exit 1

if ! pgrep -f "node server.js" > /dev/null; then
  [ -f "$DATA/setup-token.txt" ] || python3 -c "import secrets; print(secrets.token_hex(16))" > "$DATA/setup-token.txt"
  TOKEN=$(cat "$DATA/setup-token.txt")
  PORT=8787 NODE_USE_ENV_PROXY=1 GEMINI_KEY_FILE="$DATA/gemini-key.txt" SETUP_TOKEN="$TOKEN" \
    nohup node server.js >> "$DATA/server.log" 2>&1 &
  echo "Serveur proxy démarré."
fi

if ! pgrep -f "localhost.run" > /dev/null; then
  nohup ssh -o ProxyCommand="nc -X connect -x hatch-egress-proxy:3128 %h %p" \
    -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
    -R 80:localhost:8787 nokey@localhost.run >> "$DATA/ssh-tunnel.log" 2>&1 &
  echo "Tunnel démarré."
fi

sleep 8
grep -oE "https://[a-z0-9]+\.lhr\.life" "$DATA/ssh-tunnel.log" | tail -1
