#!/usr/bin/env bash
set -euo pipefail
cd /root/startup-roast-bot
LOG=/root/startup-roast-bot/watchdog.log
ENV=/root/.hermes/.env
PORT=8090

stamp() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }

if ! pgrep -f "uvicorn app:app.*--port ${PORT}" >/dev/null; then
  echo "$(stamp) starting uvicorn" >> "$LOG"
  nohup .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port "$PORT" >> uvicorn.log 2>&1 &
  sleep 3
fi

if ! curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  echo "$(stamp) local health failed; restarting uvicorn" >> "$LOG"
  pkill -f "uvicorn app:app.*--port ${PORT}" || true
  nohup .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port "$PORT" >> uvicorn.log 2>&1 &
  sleep 3
fi

if ! pgrep -f "cloudflared tunnel --url http://127.0.0.1:${PORT}" >/dev/null; then
  echo "$(stamp) starting cloudflared" >> "$LOG"
  nohup cloudflared tunnel --url "http://127.0.0.1:${PORT}" --no-autoupdate --loglevel info >> cloudflared_current.log 2>&1 &
  sleep 12
fi

URL=$(grep -Eo 'https://[-a-z0-9]+\.trycloudflare\.com' cloudflared_current.log | tail -1 || true)
if [ -n "$URL" ]; then
  echo "$URL" > current_url.txt
  TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' "$ENV" | tail -1 | cut -d= -f2- | tr -d '"')
  python3 - "$TOKEN" "$URL" >> "$LOG" 2>&1 <<'PY'
import sys, requests, datetime
TOKEN, URL = sys.argv[1], sys.argv[2]
api=f'https://api.telegram.org/bot{TOKEN}'
try:
    info=requests.get(api+'/getWebhookInfo', timeout=15).json().get('result', {})
    target=URL.rstrip('/')+'/webhook'
    if info.get('url') != target:
        r=requests.post(api+'/setWebhook', json={'url': target, 'drop_pending_updates': False}, timeout=15)
        print(datetime.datetime.utcnow().isoformat()+'Z setWebhook '+str(r.status_code)+' '+r.text[:200])
    else:
        print(datetime.datetime.utcnow().isoformat()+'Z ok '+URL)
except Exception as e:
    print(datetime.datetime.utcnow().isoformat()+'Z telegram webhook check failed '+repr(e))
PY
fi
