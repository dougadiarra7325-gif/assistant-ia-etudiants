#!/bin/bash
# Superviseur de l'Assistant IA Étudiants (Flask + SQLite)
# 1) gunicorn sur 127.0.0.1:5001  2) tunnel public localhost.run
cd "$HOME/workspace/assistant-ia-etudiants" || exit 1
mkdir -p logs
set -a
. ./.env.local
set +a
export DATABASE_PATH="$HOME/workspace/assistant-ia-etudiants/assistant.db"

(
  while true; do
    echo "=== gunicorn start $(date -u +%FT%TZ) ===" >> logs/app.log
    .venv/bin/gunicorn app:app --bind 127.0.0.1:5001 --workers 2 --timeout 120 >> logs/app.log 2>&1
    echo "=== gunicorn exit $? $(date -u +%FT%TZ), restart in 3s ===" >> logs/app.log
    sleep 3
  done
) &

while true; do
  echo "=== tunnel start $(date -u +%FT%TZ) ===" >> logs/tunnel.log
  ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=15 -o ServerAliveCountMax=4 \
      -o ExitOnForwardFailure=yes -o TCPKeepAlive=yes \
      -o ProxyCommand="python3 $HOME/workspace/tools/proxy-connect.py %h %p" \
      -R 80:localhost:5001 nokey@localhost.run >> logs/tunnel.log 2>&1
  echo "=== tunnel exit code $? $(date -u +%FT%TZ), restart in 3s ===" >> logs/tunnel.log
  sleep 3
done
