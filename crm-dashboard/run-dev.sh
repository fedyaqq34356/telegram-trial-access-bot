#!/usr/bin/env bash
# Запуск CRM в режиме разработки (backend :8000 + frontend :3000)
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "▶ Backend (FastAPI) на http://localhost:8000"
cd "$ROOT/backend"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env
uvicorn app.main:app --reload --port 8000 &
BACK_PID=$!

echo "▶ Frontend (Next.js) на http://localhost:3000"
cd "$ROOT/frontend"
[ -d node_modules ] || npm install
[ -f .env.local ] || cp .env.local.example .env.local
npm run dev &
FRONT_PID=$!

trap "kill $BACK_PID $FRONT_PID 2>/dev/null" EXIT
echo "✓ Открой http://localhost:3000 (логин: admin / admin123)"
wait
