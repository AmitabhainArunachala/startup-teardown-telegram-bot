# Startup Teardown Telegram Bot

Live Telegram bot for BountyBook job d63ab72c: structured startup-idea teardowns.

**Live bot:** [@hermes_rushabdev_bot](https://t.me/hermes_rushabdev_bot)  
**GitHub repo:** https://github.com/AmitabhainArunachala/startup-teardown-telegram-bot

## What it does

Send any startup idea to the bot and it responds with:

1. **What you think you're building**
2. **What you're actually building**
3. **Why a16z passes**
4. **Funding probability** (percentage score)
5. **The one thing that could save it**

Commands:
- `/roastmore` - deeper market/distribution/moat critique of the last idea
- `/pivotme` - three more fundable adjacent pivots with reasoning
- `/comparps` - real comparable companies and what happened to them (real companies with real outcomes, no hallucination)

## Deploy Instructions

### Prerequisites
- Python 3.10+
- A Telegram bot token (create one via @BotFather)
- cloudflared installed (for tunnel) OR a public domain

### Steps

1. Clone the repo:
```bash
git clone https://github.com/AmitabhainArunachala/startup-teardown-telegram-bot.git
cd startup-teardown-telegram-bot
```

2. Create virtualenv and install dependencies:
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

3. Set your Telegram bot token:
```bash
export TELEGRAM_BOT_TOKEN=your_bot_token_here
```

4. Start the server:
```bash
uvicorn app:app --host 127.0.0.1 --port 8090
```

5. Expose the service with a tunnel (e.g., cloudflared):
```bash
cloudflared tunnel --url http://127.0.0.1:8090
# Note the tunnel URL, e.g., https://xxxx.trycloudflare.com
```

6. Set the Telegram webhook:
```bash
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook?url=https://xxxx.trycloudflare.com/webhook"
```

7. Verify deployment:
```bash
# Health check
curl http://127.0.0.1:8090/health
# Expected: {"ok":true,"uptime_seconds":N}

# Sample outputs (5 startup teardowns with comparps)
curl http://127.0.0.1:8090/sample_outputs

# Comparps endpoint (real companies with real outcomes)
curl http://127.0.0.1:8090/comparps
```

8. Test in Telegram: Send a startup idea to your bot. It should respond with a structured teardown.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| / | GET | Service info and uptime |
| /health | GET | Health check (returns {"ok":true,"uptime_seconds":N}) |
| /webhook | POST | Telegram webhook receiver |
| /sample_outputs | GET | 5 sample startup teardowns with all command outputs |
| /comparps | GET | Real comparable companies with real outcomes |
| /commands | GET | Available bot commands |

## How it works

The bot categorizes each startup idea by keyword matching (restaurant, fitness, fintech, health, marketplace, social, AI) and generates a category-specific teardown. Each category has:
- Real comparable companies (Toast, BlueCart, Shelf Engine, Strava, Brex, Ramp, Deel, Ro, One Medical, Upwork, Toptal, etc.)
- Category-specific failure modes and save strategies
- A deterministic funding probability score based on keywords and idea hash

All comparable companies are real companies with verifiable outcomes - no hallucinated data.

## Tech Stack

- **FastAPI** - web framework
- **uvicorn** - ASGI server
- **Telegram Bot API** (via webhook) - Telegram integration
- **cloudflared** - tunnel for public access

## License

MIT
