import hashlib
import html
import os
import re
import time
from typing import Dict, List, Tuple

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv('/root/.hermes/.env')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
if not BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN missing')
API = f'https://api.telegram.org/bot{BOT_TOKEN}'
STARTED_AT = int(time.time())
LAST_IDEA: Dict[int, str] = {}

app = FastAPI(title='Startup Teardown Telegram Bot', version='1.1.0')

COMPANIES = {
    'ai': [('Jasper', 'raised aggressively for AI copywriting, then cut staff when generic LLM copy became a feature'), ('Copy.ai', 'survived by narrowing into GTM workflows instead of “write me anything”'), ('Intercom Fin', 'wins because it sits inside an existing support workflow and ticket history')],
    'restaurant': [('Toast', 'won restaurant software by owning payments/POS distribution, not by selling a standalone dashboard'), ('BlueCart', 'restaurant procurement network; the value is supplier ordering workflow density'), ('Shelf Engine', 'automated grocery/food ordering; hard part is spoilage risk and operational integration')],
    'fitness': [('Strava', 'durable because athletes already create repeat activity data and status loops'), ('Gympass/Wellhub', 'sold through employers, avoiding pure consumer fitness churn'), ('Fitbit', 'hardware plus tracking created daily habit, but still needed platform/acquisition to sustain growth')],
    'fintech': [('Brex', 'started with startup corporate cards and underwriting from cash/bank data'), ('Ramp', 'won by tying cards to expense-control workflow and measurable savings'), ('Deel', 'remote payroll scaled by owning compliance complexity country by country')],
    'health': [('Ro', 'scaled DTC telehealth by focusing on high-intent conditions and pharmacy fulfillment'), ('One Medical', 'proved clinics plus membership software, then sold to Amazon'), ('Oscar Health', 'consumer-friendly insurance raised billions but learned risk pools beat UX')],
    'marketplace': [('Upwork', 'liquidity took years; matching labor is easy, trust and repeat demand are hard'), ('Toptal', 'differentiated with vetting and managed matching for higher-value talent'), ('Catalant', 'expert marketplace shifted toward enterprise work where budgets and repeat use exist')],
    'social': [('Clubhouse', 'had explosive novelty but weak retention after live audio stopped feeling urgent'), ('BeReal', 'created a fresh mechanic but struggled to prove durable network behavior'), ('Discord', 'won from a high-frequency gamer/community wedge before broadening')],
    'default': [('Airtable', 'made a familiar spreadsheet interface serve operational databases'), ('Zapier', 'grew by connecting existing SaaS demand rather than inventing new behavior'), ('Product Hunt', 'owns a repeated launch ritual and audience, not just a directory')]
}

KEYWORDS = {
    'restaurant': {'restaurant','restaurants','kitchen','inventory','spoilage','produce','chef','menu','grocery','food','meal'},
    'fitness': {'fitness','workout','workouts','gym','run','running','athlete','exercise','wellness'},
    'fintech': {'stripe','payment','payments','payroll','tax','crypto','card','bank','invoice','finance','insurance','cfo'},
    'health': {'telehealth','doctor','clinic','patient','dermatology','medical','health','therapy','vet','claims'},
    'marketplace': {'marketplace','fractional','freelance','experts','talent','buyers','sellers'},
    'social': {'social','friends','community','creator','dating','network'},
    'ai': {'ai','llm','agent','copilot','chatbot','gpt','automation'}
}

PERSONAS = {
    'restaurant': ('operators of multi-location restaurants', 'food cost variance, stockouts, and manager time'),
    'fitness': ('people already paying for coaching, gyms, or employer wellness', 'accountability that survives January-motivation churn'),
    'fintech': ('finance teams with compliance or cash-control pain', 'risk, reconciliation, and regulatory edge cases'),
    'health': ('clinics or payers with reimbursable workflows', 'trust, liability, and integration into care ops'),
    'marketplace': ('budget owners who repeatedly buy the same expert help', 'liquidity, vetting, and trust on both sides'),
    'social': ('communities with an existing repeated ritual', 'retention after novelty fades'),
    'ai': ('a specific job title drowning in repetitive workflow', 'proprietary context and measurable hours saved'),
    'default': ('one narrow buyer with urgent budget', 'distribution and behavior change')
}

FAILURE = {
    'restaurant': 'your “AI forecast” is only useful if it changes tomorrow’s purchase order and someone trusts it over the kitchen manager',
    'fitness': 'consumer fitness apps produce beautiful week-one graphs and brutal week-four retention curves',
    'fintech': 'every edge case becomes compliance/support work, and incumbents can copy the dashboard once the wedge is obvious',
    'health': 'a demo does not overcome HIPAA, clinical liability, reimbursement, and provider workflow resistance',
    'marketplace': 'cold-start liquidity means you are hand-recruiting both sides while pretending software is scaling',
    'social': '“friends will invite friends” is not a moat; it is a hope with push notifications',
    'ai': 'if the product is a prompt plus a prettier UI, OpenAI/Google or an incumbent SaaS can erase the feature',
    'default': 'the pitch describes a product, but not a wedge, buyer, acquisition channel, or reason the habit repeats'
}

SAVE = {
    'restaurant': 'Run a 30-day pilot with 5 restaurants where you auto-create orders and guarantee a 3–5% reduction in waste or stockouts; charge from verified savings.',
    'fitness': 'Sell to gyms/coaches/employers with existing member relationships, and make the bet mechanic trigger real-world attendance data instead of self-reported vibes.',
    'fintech': 'Own one ugly regulated workflow end-to-end — filings, reconciliation, approvals, and audit trail — before claiming platform status.',
    'health': 'Start as workflow software for clinics, not a consumer symptom toy: integrate scheduling/EHR handoff and prove reimbursement or staff-time savings.',
    'marketplace': 'Begin as a managed service in one niche, manually vet supply, publish outcome guarantees, then software-ize matching only after repeat demand is visible.',
    'social': 'Attach the social loop to a pre-existing ritual (class, team, event, paid community) where absence is noticed without the app inventing urgency.',
    'ai': 'Capture proprietary workflow data and ship an action-taking system of record, not another chat window; the output must directly update the tool where work finishes.',
    'default': 'Cut the market to one painfully specific segment and prove a measurable ROI event that happens weekly, not someday.'
}

def esc(s: str) -> str:
    return html.escape(s, quote=False)

def toks(idea: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9'+-]*", idea.lower())

def cat(idea: str) -> str:
    ts = set(toks(idea))
    scores = {k: len(ts & v) for k, v in KEYWORDS.items()}
    # prefer domain over AI if both appear
    if scores['ai'] and max(v for k, v in scores.items() if k != 'ai') == 0:
        return 'ai'
    best = max([k for k in scores if k != 'ai'], key=lambda k: scores[k])
    return best if scores[best] else ('ai' if scores['ai'] else 'default')

def nouns(idea: str) -> str:
    stop={'a','an','the','for','with','and','or','to','of','that','where','app','platform','startup','startup','automatic','auto'}
    ws=[w for w in toks(idea) if w not in stop and len(w)>2]
    return ', '.join(ws[:6]) or 'the proposed workflow'

def score(idea: str, c: str) -> int:
    ts=set(toks(idea)); s={'restaurant':32,'fitness':18,'fintech':36,'health':34,'marketplace':22,'social':14,'ai':24,'default':20}[c]
    if ts & {'b2b','enterprise','clinic','restaurants','teams','compliance','payroll','inventory'}: s += 12
    if ts & {'social','friends','consumer','dating','bet'}: s -= 7
    if ts & {'crypto','marketplace'}: s -= 4
    if ts & {'tax','claims','dermatology','spoilage'}: s += 5
    s += int(hashlib.sha256(idea.encode()).hexdigest()[:2],16)%9
    return max(2,min(72,s))

def teardown(idea: str) -> str:
    idea=' '.join((idea or '').split())[:700]
    c=cat(idea); buyer,pain=PERSONAS[c]; fp=score(idea,c); terms=nouns(idea)
    comps=COMPANIES[c]
    return f"""<b>Startup teardown</b>

<b>Idea tested:</b> {esc(idea)}

<b>1) What you think you're building</b>
A clean product around <b>{esc(terms)}</b>: users describe the problem, your product predicts/matches/automates it, and the demo makes the old workflow look embarrassingly manual.

<b>2) What you're actually building</b>
A go-to-market and trust problem for <b>{esc(buyer)}</b>. The real product is not the interface; it is proving you can repeatedly solve <b>{esc(pain)}</b> in the messy place where work already happens.

<b>3) Why a16z passes</b>
They will like the shape but pass because {esc(FAILURE[c])}. The pitch needs proof of a wedge: named buyer, budget owner, distribution channel, and a metric that improves because of this product — not because a founder babysat the pilot.

<b>4) Funding probability</b>
<b>{fp}%</b> seed-fundable as written. Biggest swing factor: whether you can show a before/after metric tied to {esc(terms.split(',')[0])} and a buyer who says “I would rip out my current workaround for this.”

<b>5) The one thing that could save it</b>
{esc(SAVE[c])}

<b>Comparable warning:</b> {esc(comps[0][0])} — {esc(comps[0][1])}"""

def deeper(idea: str) -> str:
    c=cat(idea or ''); buyer,pain=PERSONAS[c]
    return f"""<b>Deeper market roast</b>
• <b>Buyer:</b> Start with {esc(buyer)}, not “everyone who has this problem.”
• <b>Budget:</b> The budget exists only if {esc(pain)} is already costing money, time, churn, or compliance risk.
• <b>Distribution:</b> Your first channel should be where this buyer already buys: POS/reseller for restaurants, clinics/EHR consultants for health, finance communities for fintech, coaches/employers for fitness.
• <b>Moat:</b> The defensible asset must be workflow data, integrations, approvals, or supply quality — not the model output.
• <b>Kill criteria:</b> If five target buyers will not share real data or let you run the workflow for them, the pain is probably a vitamin."""

def pivots(idea: str) -> str:
    c=cat(idea or '')
    options={
        'restaurant':['Waste-guarantee purchasing assistant for 5–50 location restaurant groups','Invoice-to-inventory reconciliation for kitchens using Toast/Square','Supplier price benchmarking network for independent restaurants'],
        'fitness':['Coach-led accountability product that charges trainers, not casual users','Employer wellness attendance layer with verified gym/class check-ins','Team training challenge software for schools/clubs with existing rituals'],
        'fintech':['Compliance payroll workflow for one remote-worker corridor','AP exception automation for mid-market finance teams','Audit-ready crypto accounting for agencies that already hold client wallets'],
        'health':['Derm clinic intake plus EHR-ready triage notes','Prior-auth automation for one specialty','Patient photo follow-up workflow sold to clinics, not consumers'],
        'marketplace':['Managed fractional CFO matching for SaaS companies between $1–10M ARR','Outcome-guaranteed expert bench for one finance task','Vetted consultant marketplace bundled with templates and project QA'],
        'social':['Community CRM for paid fitness groups','Challenge tooling for existing clubs/classes','Creator-led cohorts where status already matters'],
        'ai':['Copilot that updates one system of record','Compliance QA for one document type','Internal agent with audit logs for a single team workflow'],
        'default':['Managed service first for one painful recurring task','Benchmarking/data product for one operator role','Workflow SaaS with a weekly ROI trigger']
    }[c]
    return '<b>Three more fundable pivots</b>\n' + '\n'.join(f'{i+1}. {esc(x)} — narrower buyer, clearer ROI, less “nice-to-have” risk.' for i,x in enumerate(options))

def comparps_text(idea: str) -> str:
    return '<b>Real comparable companies</b>\n' + '\n'.join(f'• <b>{esc(n)}</b>: {esc(d)}.' for n,d in COMPANIES[cat(idea or '')])

def send(chat_id: int, text: str):
    r=requests.post(f'{API}/sendMessage', json={'chat_id':chat_id,'text':text,'parse_mode':'HTML','disable_web_page_preview':True}, timeout=15)
    if not r.ok:
        requests.post(f'{API}/sendMessage', json={'chat_id':chat_id,'text':re.sub('<[^>]+>','',text)}, timeout=15)

@app.get('/')
def root():
    return {'ok': True, 'service': 'Startup Teardown Telegram Bot', 'bot': 'hermes_rushabdev_bot', 'uptime_seconds': int(time.time())-STARTED_AT, 'commands':['/roastmore','/pivotme','/comparps']}

@app.get('/health')
def health(): return {'ok': True, 'uptime_seconds': int(time.time())-STARTED_AT}

@app.post('/webhook')
async def webhook(req: Request):
    update=await req.json(); msg=update.get('message') or update.get('edited_message') or {}; chat_id=(msg.get('chat') or {}).get('id'); text=(msg.get('text') or '').strip()
    if not chat_id or not text: return JSONResponse({'ok': True, 'ignored': True})
    if text.startswith('/start') or text.startswith('/help'): send(chat_id, 'Send me a startup idea and I will tear it down. Commands: /roastmore, /pivotme, /comparps')
    elif text.startswith('/roastmore'): send(chat_id, deeper(LAST_IDEA.get(chat_id,'')))
    elif text.startswith('/pivotme'): send(chat_id, pivots(LAST_IDEA.get(chat_id,'')))
    elif text.startswith('/comparps'): send(chat_id, comparps_text(LAST_IDEA.get(chat_id,'')))
    else: LAST_IDEA[chat_id]=text; send(chat_id, teardown(text))
    return JSONResponse({'ok': True})

@app.get('/sample_outputs')
def sample_outputs():
    samples=['AI copilot for restaurant inventory that predicts spoilage and auto-orders produce','A social fitness app where friends bet on weekly workouts','Crypto payroll for remote teams with automatic tax compliance','Telehealth triage bot for dermatology clinics','Marketplace for fractional CFOs for seed-stage startups']
    return {'samples':[{'idea':x,'teardown':teardown(x),'roastmore':deeper(x),'pivotme':pivots(x),'comparps':comparps_text(x)} for x in samples]}

if __name__ == '__main__':
    import uvicorn; uvicorn.run(app, host='127.0.0.1', port=int(os.environ.get('PORT','8090')))
