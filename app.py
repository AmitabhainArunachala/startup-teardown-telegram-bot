import hashlib
import html
import json
import os
import re
import time
from typing import Dict, Optional

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv

load_dotenv('/root/.hermes/.env')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
if not BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN missing')
API = f'https://api.telegram.org/bot{BOT_TOKEN}'
STARTED_AT = int(time.time())
LAST_IDEA: Dict[int, str] = {}

app = FastAPI(title='Startup Teardown Telegram Bot', version='1.0.0')

REAL_COMPANIES = {
    'ai': [
        ('Jasper', 'AI marketing copy platform; raised large rounds, then restructured when generic LLM wrappers commoditized.'),
        ('Copy.ai', 'AI sales/marketing writing product; survived by narrowing toward GTM workflows instead of “write anything” chat.'),
        ('Notion AI', 'Incumbent distribution won: AI embedded into existing workspace behavior rather than sold as a standalone toy.')],
    'food': [
        ('Blue Apron', 'Meal kits reached IPO but struggled with retention, CAC, and grocery/logistics margin pressure.'),
        ('Instacart', 'Grocery delivery scaled via marketplace density, but margins depend on ads and retailer relationships.'),
        ('DoorDash', 'Won through local logistics density and frequency; still had to add ads/subscriptions for profitability.')],
    'health': [
        ('Oscar Health', 'Consumer-friendly health insurance raised billions but learned healthcare distribution and risk pools are brutal.'),
        ('Ro', 'DTC telehealth scaled by focusing on specific high-intent conditions and pharmacy fulfillment.'),
        ('One Medical', 'Primary-care membership model; sold to Amazon after proving clinics plus software, not pure app magic.')],
    'fintech': [
        ('Brex', 'Corporate cards won by starting with startups and underwriting from bank/cash data, then moving upmarket.'),
        ('Ramp', 'Expense/corporate card platform differentiated on savings automation and finance workflow breadth.'),
        ('Chime', 'Consumer neobank scaled with simple wedge and distribution, but depends heavily on interchange economics.')],
    'social': [
        ('Clubhouse', 'Exploded during COVID, then retention fell when the format lacked durable daily utility.'),
        ('BeReal', 'Novel social mechanic won attention, but network retention and monetization remain difficult.'),
        ('Discord', 'Started with gamer voice chat wedge, expanded because communities already had repeated high-frequency use.')],
    'default': [
        ('Product Hunt', 'Community discovery marketplace; durable because it owns a repeated launch ritual and audience.'),
        ('Airtable', 'Spreadsheet-database hybrid won by making a familiar interface serve real operational workflows.'),
        ('Zapier', 'Automation middleware scaled by connecting existing SaaS demand, not by creating new behavior from scratch.')]
}


def escape(s: str) -> str:
    return html.escape(s, quote=False)


def words(idea: str):
    return re.findall(r"[a-zA-Z][a-zA-Z0-9'+-]*", idea.lower())


def category(idea: str) -> str:
    t = set(words(idea))
    if t & {'ai','llm','chatbot','agent','gpt','automation','copilot'}: return 'ai'
    if t & {'food','restaurant','meal','grocery','kitchen','delivery'}: return 'food'
    if t & {'health','doctor','patient','clinic','therapy','fitness','medical'}: return 'health'
    if t & {'bank','money','card','invoice','finance','crypto','payments','fintech'}: return 'fintech'
    if t & {'social','creator','community','dating','friends','network'}: return 'social'
    return 'default'


def score(idea: str) -> int:
    ws = set(words(idea))
    s = 18
    if ws & {'b2b','enterprise','compliance','workflow','vertical','api','infrastructure'}: s += 18
    if ws & {'marketplace','social','consumer','dating'}: s -= 8
    if ws & {'ai','chatbot','wrapper','generic'}: s -= 6
    if ws & {'payments','health','legal','insurance'}: s += 7
    if len(idea) > 120: s += 6
    h = int(hashlib.sha256(idea.encode()).hexdigest()[:2], 16) % 17
    return max(3, min(78, s + h))


def market_phrase(idea: str) -> str:
    c = category(idea)
    return {
        'ai': 'a workflow wedge disguised as an AI feature',
        'food': 'a low-margin logistics business with software lipstick',
        'health': 'a regulated trust-and-distribution problem before it is an app',
        'fintech': 'a distribution and risk-underwriting company, not a dashboard',
        'social': 'a retention lottery where novelty decays faster than CAC',
        'default': 'a behavior-change problem masquerading as a SaaS product'
    }[c]


def teardown(idea: str) -> str:
    idea_clean = ' '.join(idea.split())[:700]
    fp = score(idea_clean)
    c = category(idea_clean)
    killer = {
        'ai': 'Prove one painful workflow where you own proprietary context/data and the user would still pay if OpenAI copied the UI tomorrow.',
        'food': 'Start with one dense geography or captive buyer segment where frequency and basket size beat delivery/support costs.',
        'health': 'Pick a reimbursable or employer-paid wedge and show clinical/legal trust before scaling consumer acquisition.',
        'fintech': 'Find a narrow customer whose existing financial workflow creates underwriting or payment data others cannot see.',
        'social': 'Anchor it around a repeated offline identity or community need; pure novelty will not survive week two.',
        'default': 'Narrow to a segment with urgent budget, measurable ROI, and a distribution channel you can reach without paid ads.'
    }[c]
    return f"""<b>Startup teardown</b>\n\n<b>Idea tested:</b> {escape(idea_clean)}\n\n<b>1) What you think you're building</b>\nA crisp product that makes users say “finally, someone fixed {escape((idea_clean[:90] or 'this problem'))}.” You are imagining adoption driven by obvious utility and a clean demo.\n\n<b>2) What you're actually building</b>\nYou are building {market_phrase(idea_clean)}. The hard part is not the landing page or model prompt — it is repeated usage, distribution, trust, and willingness to pay after the novelty wears off.\n\n<b>3) Why a16z passes</b>\nThe pitch probably lacks a sharp wedge, proprietary advantage, and evidence that this can become a venture-scale category. If the answer to “why now?” is mostly “AI exists” or “people hate the current tools,” partners hear commodity risk plus expensive customer education.\n\n<b>4) Funding probability</b>\n<b>{fp}%</b> seed-fundable as described. It can move up if you show 10+ obsessed design partners, painful budget ownership, and retention that survives the founder manually hand-holding users.\n\n<b>5) The one thing that could save it</b>\n{escape(killer)}"""


def deeper(idea: str) -> str:
    idea = idea or 'the last startup idea'
    c = category(idea)
    comps = REAL_COMPANIES[c]
    return '<b>Deeper roast</b>\n' + '\n'.join([
        f'• <b>Market trap:</b> {escape(market_phrase(idea)).capitalize()}; customers will compare you to spreadsheets, interns, agencies, or incumbent workflows, not just direct startups.',
        '• <b>Distribution test:</b> Name the exact buyer, where they already gather, and what trigger makes them buy this week.',
        '• <b>Moat test:</b> If a competent team cloned the UI in 30 days, the remaining moat must be data, workflow lock-in, regulated access, or community density.',
        f'• <b>Closest warning sign:</b> {escape(comps[0][0])} — {escape(comps[0][1])}'
    ])


def pivots(idea: str) -> str:
    c = category(idea or '')
    base = {
        'ai': ['Compliance-grade AI QA for one regulated document workflow', 'Internal support copilot trained on closed company systems with audit logs', 'Vertical AI agent sold with done-for-you onboarding to a single job title'],
        'food': ['Procurement/ordering OS for independent restaurant groups', 'Waste forecasting for commissary kitchens with guaranteed savings', 'B2B prepared-meal logistics for hospitals or campuses'],
        'health': ['Prior-auth automation for a narrow specialty clinic', 'Remote monitoring ops layer for one reimbursable condition', 'Employer-paid navigation for a costly chronic population'],
        'fintech': ['Cash-flow underwriting API for a specific vertical', 'Accounts payable exception automation for mid-market finance teams', 'Chargeback/fraud workflow for one merchant category'],
        'social': ['Community CRM for paid niche communities', 'Creator sponsorship workflow with verified conversion data', 'Events-to-membership tool for groups that already meet monthly'],
        'default': ['Workflow SaaS for one budget-owning role', 'Data product that benchmarks operators against peers', 'Managed service first, software second, for a painful recurring task']
    }[c]
    return '<b>Three more fundable pivots</b>\n' + '\n'.join(f'{i+1}. {escape(x)} — clearer buyer, sharper pain, and easier ROI proof.' for i,x in enumerate(base))


def comparps(idea: str) -> str:
    comps = REAL_COMPANIES[category(idea or '')]
    return '<b>Real comparable companies</b>\n' + '\n'.join(f'• <b>{escape(n)}</b>: {escape(d)}' for n,d in comps)


def send(chat_id: int, text: str):
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
    r = requests.post(f'{API}/sendMessage', json=payload, timeout=15)
    if not r.ok:
        # Retry plain text if HTML parse ever fails.
        payload.pop('parse_mode', None)
        payload['text'] = re.sub('<[^>]+>', '', text)
        requests.post(f'{API}/sendMessage', json=payload, timeout=15)


@app.get('/')
def root():
    return {'ok': True, 'service': 'Startup Teardown Telegram Bot', 'bot': 'hermes_rushabdev_bot', 'uptime_seconds': int(time.time()) - STARTED_AT, 'commands': ['/roastmore','/pivotme','/comparps']}

@app.get('/health')
def health():
    return {'ok': True, 'uptime_seconds': int(time.time()) - STARTED_AT}

@app.post('/webhook')
async def webhook(req: Request):
    update = await req.json()
    msg = update.get('message') or update.get('edited_message') or {}
    chat = msg.get('chat', {})
    chat_id = chat.get('id')
    text = (msg.get('text') or '').strip()
    if not chat_id or not text:
        return JSONResponse({'ok': True, 'ignored': True})
    if text.startswith('/start') or text.startswith('/help'):
        send(chat_id, 'Send me a startup idea and I will tear it down. Commands: /roastmore, /pivotme, /comparps')
    elif text.startswith('/roastmore'):
        send(chat_id, deeper(LAST_IDEA.get(chat_id, '')))
    elif text.startswith('/pivotme'):
        send(chat_id, pivots(LAST_IDEA.get(chat_id, '')))
    elif text.startswith('/comparps'):
        send(chat_id, comparps(LAST_IDEA.get(chat_id, '')))
    else:
        LAST_IDEA[chat_id] = text
        send(chat_id, teardown(text))
    return JSONResponse({'ok': True})

@app.get('/sample_outputs')
def sample_outputs():
    samples = [
        'AI copilot for restaurant inventory that predicts spoilage and auto-orders produce',
        'A social fitness app where friends bet on weekly workouts',
        'Crypto payroll for remote teams with automatic tax compliance',
        'Telehealth triage bot for dermatology clinics',
        'Marketplace for fractional CFOs for seed-stage startups'
    ]
    return {'samples': [{'idea': x, 'teardown': teardown(x)} for x in samples]}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=int(os.environ.get('PORT', '8090')))
