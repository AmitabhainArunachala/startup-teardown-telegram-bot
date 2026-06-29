# Startup Teardown Telegram Bot

Live Telegram bot for BountyBook job `d63ab72c`: structured startup-idea teardowns.

## What it does

Send any startup idea to the bot and it responds with:

1. What you think you're building
2. What you're actually building
3. Why a16z passes
4. Funding probability
5. The one thing that could save it

Commands:

- `/roastmore` — deeper market/distribution/moat critique of the last idea
- `/pivotme` — three more fundable adjacent pivots
- `/comparps` — real comparable companies and what happened to them

## Run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=...
uvicorn app:app --host 127.0.0.1 --port 8090
```

Expose the service and set the Telegram webhook:

```bash
cloudflared tunnel --url http://127.0.0.1:8090
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook?url=$TUNNEL_URL/webhook"
```

Health endpoint: `/health`  
Sample outputs: `/sample_outputs`
