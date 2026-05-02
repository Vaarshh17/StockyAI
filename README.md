# 🌿 Stocky AI

> A proactive decision intelligence agent for Malaysian wet market wholesalers.  
> Lives entirely on Telegram. Speaks Malay, Mandarin, and English. Watches your business while you sleep.

### **UM Hackathon 2026 — Domain: AI for Economic Empowerment & Decision Intelligence**<br>
**Pitch Deck**:  ```docs/Stocky_AI_Pitch_Deck.pdf```<br><br>
**Deployment Plan**: ```docs/Stocky_AI_Deployment_Plan.pdf```<br>
**Business Proposal**: ```docs/Stocky_AI_Business_Proposal.pdf```<br>
**Refined Quality Assurance Testing Document**: ```docs/Stocky_AI_Refined_Quality_Assurance_Testing_Document.pdf```<br>

Above documents are also uploaded in drive for easier access.<br>
**Documents**: https://drive.google.com/drive/u/0/folders/1r8BMnYSKIT8ALzwH09g2lqTujCmpzSvY

---

## The Problem

Malaysia's produce wholesalers wake up at 3 AM and buy stock on gut feel.  
They lose 20–50% of produce to spoilage. They track credit in their heads.  
They manage supplier relationships through WhatsApp threads and memory.  
They have no system watching their business for them.

**The gap isn't analytics. It's anticipation.**

---

## The Solution

Stocky AI is a proactive intelligence agent built for the actual user: a 50-year-old market trader, not a tech-savvy professional. No app to download. No dashboard to learn. Just Telegram — the tool they already use every day.

---

## Features

### 1. 🌅 Proactive Intelligence (3:30 AM Morning Brief)
Every morning before the market opens, Stocky sends an unprompted brief: what's low on stock, what's expiring today, who's overdue on payment, today's weather and how it affects demand, and one proactive buy recommendation. The wholesaler wakes up already knowing what to do.

Six scheduled jobs run autonomously:
- **3:30 AM** — Morning brief (inventory + weather + credit + buy list + savings footer)
- **8 AM / 2 PM** — Spoilage check (fires only if item ≤ 2 days left and > 20 kg)
- **Every 4 hours** — Velocity alert (fires if selling >30% faster than baseline = stockout risk, OR >40% slower with expiry within 5 days = spoilage risk)
- **9 AM** — Credit reminder (fires only if payment due today or overdue)
- **Monday 7 AM** — Weekly digest + Stocky's Instinct cross-signal finding
- **Sunday 10 AM** — Proactive loan offer (fires only if eligible + no offer in last 30 days)

### 2. 📦 Inventory & Spoilage Intelligence
Tracks current stock levels per commodity. Calculates days until expiry based on shelf life. Cross-references sell velocity to determine whether stock runs out before it expires. Alerts when something is at risk with a specific suggested action.

### 3. 📊 Supplier Quote Analysis (Forwarded Messages → Decision)
Forward any supplier WhatsApp message to Stocky. It automatically:
- Extracts the commodity, price, and quantity
- Compares against your **lowest historical buy price** (last 60 days) and the **FAMA government benchmark**
- Calculates margin based on your actual average sell price
- Returns a clear **BELI / BOLEH / NEGOTIATE / PASS** verdict with sell price targets
- Always follows with: *"Modal yang perlu: RM X. Awak ada modal ni sekarang?"*

### 4. 💸 Capital Check + Embedded Finance
If the trader says they don't have the capital to buy:
- Stocky checks their creditworthiness from 60 days of transaction data
- If eligible (score ≥ 60 + 14 days data + ≥ RM500/week revenue): presents the full **Agrobank Digital Niaga / AgroCash-i** application package — digital steps, no branch visit, 3–5 day decision
- If not eligible: offers alternatives (smaller order, negotiate credit terms with supplier)

### 5. 💰 Supplier Price Comparison + FAMA Benchmark
Stores quoted prices from each supplier per commodity. Compares against weekly FAMA government benchmark prices. Ranks suppliers by price, notes who has drifted above market rate, and factors in supplier reliability.

### 6. 📈 Trade Logging (Buy & Sell, FIFO)
Logs every purchase and sale. FIFO inventory deduction on each sale. Calculates sell velocity per commodity over the last 7 and 14 days. Powers spoilage prediction and reorder timing.

### 7. 💸 Receivables & Credit Tracking
Tracks who owes money, how much, and when it's due. Flags overdue accounts proactively. Drafts the follow-up message in the buyer's preferred language for wholesaler approval.

### 8. 🔮 Stocky's Instinct
On every commodity-specific query, Stocky checks velocity trend, stockout timing, expiry risk, and supplier price trajectory in real-time — then weaves one natural observation into its reply. Example: *"Tomato jual laju minggu ni — stok tinggal 2 hari. Pak Ali's price pun naik 8% lately, lock in sekarang before it goes higher."*

A deeper cross-commodity 14-day GLM analysis fires with every Monday digest.

### 9. 🎙️ Voice Note Input
Wholesaler sends a voice note → Whisper (local, tiny model) transcribes it → Stocky processes it exactly like a text message. A 55-year-old trader who doesn't want to type can run their entire business through voice. Supports Malay, English, and Mandarin in the same note.

### 10. 🌐 Multilingual (Malay, Mandarin, English, code-switching)
Stocky understands and responds in whatever language the wholesaler writes or speaks in. Malaysian market traders code-switch mid-sentence — Stocky handles this natively.

### 11. ✉️ Draft Message Generation
When action involves another person (supplier, buyer), Stocky drafts the message in the correct language for that contact and presents it for approval. Wholesaler taps Approve → copies to WhatsApp. One decision, not five steps.

### 12. 📰 Market News + Festival Intelligence
Real web search via DDG (`ddgs` library) scoped to Malaysian produce market — no API key required. Returns actual news articles with dates. Also hardcodes the complete 2026 Malaysian public holiday calendar with per-festival demand profiles: which commodities spike, how far in advance to stock up, and an action recommendation based on current inventory.

### 13. 💳 Financial Profile + Embedded Finance (Data Engine)
After 14+ days of trading, Stocky computes a creditworthiness score from actual transaction data: revenue stability (CoV), receivables collection rate, supplier savings vs FAMA, overdue rate, and cash flow speed. Traders who qualify receive a proactive working capital offer inside Telegram — no bank branch visit.

Stocky doesn't just connect traders to banks — it **creates the financial data** that makes lending possible. Every below-FAMA buy is tracked as a saving: *"Stocky has saved you RM 1,240 this month."*

**Loan program: Agrobank Digital Niaga / AgroCash-i** (RM300M pool for Malaysian MSMEs). Application fully digital via the Borong–Agrobank Digital Niaga Program — consent-based transaction data sharing, 3–5 day decision, no paperwork.

### 14. 📈 Live Dashboard
Full business analytics at **https://stocky-ai-dashboard.lovable.app/** — injected into the weekly digest and available anytime by typing *"dashboard"* or *"laporan"*.

---

## Powered by ILMU (Z.ai / YTL AI Labs)

`ilmu-glm-5.1` is the reasoning core. Without it, this is just a database.  
With it, it synthesizes weather + velocity + shelf life + supplier history + credit + news into a decision — and explains why.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | ilmu-glm-5.1 (ILMU API by Z.ai / YTL AI Labs) |
| Bot | python-telegram-bot v20 |
| Backend | Python (async) |
| Database | Supabase (Postgres via asyncpg) + SQLite fallback |
| Scheduler | APScheduler (6 jobs, Asia/Kuala_Lumpur timezone) |
| Voice | faster-whisper (local, tiny model) |
| Weather | Open-Meteo API (free, no key) |
| Prices | FAMA benchmark (seeded weekly) |
| Market News | ddgs (DuckDuckGo — real web search, no API key) |
| Loan Program | Agrobank Digital Niaga / AgroCash-i (RM300M pool) |
| Dashboard | https://stocky-ai-dashboard.lovable.app/ |

---

## Project Structure

```
stocky_ai/
├── agent/          # 🧠 Agent loop, tools, prompts, memory, instinct, insight, quote, finance
├── bot/            # 📱 Telegram handlers, keyboards, formatters
├── db/             # 🗄️  Database models, queries, seed data (60-day demo)
├── scheduler/      # ⏰ 6 proactive jobs (morning, spoilage, velocity, credit, digest, finance)
├── services/       # 🔌 ILMU API, weather, voice, FAMA, web search (ddgs)
├── scripts/        # 🔧 Test utilities (check_inventory, test_websearch, test_quote)
└── docs/           # 📃 PRD, SAD, TAD documentation
```

---

## Setup

```bash
git clone <repo>
cd stocky_ai
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
# Fill in BOT_TOKEN and ILMU_API_KEY in .env
python main.py               # Initialises DB, seeds demo data, starts bot
```

### Environment Variables

```env
BOT_TOKEN=...                # From @BotFather on Telegram
ILMU_API_KEY=...             # From console.ilmu.ai
ILMU_API_URL=https://api.ilmu.ai/v1
MODEL_SMART=ilmu-glm-5.1
MODEL_FAST=ilmu-glm-5.1
SUPABASE_DB_URL=...          # Optional — falls back to local SQLite
DEFAULT_CITY=Kuala Lumpur
```

---

## Run Tests

```
$ python -m pytest
```

## Reset & Re-seed Demo Data

If the DB already has data and you need a fresh seed (e.g. after changing seed.py):

```bash
python -m db.seed --force
```

---

## Demo Commands

```
/start                        — Initialise bot, clear history
/trigger_brief morning        — Fire the 3:30 AM morning brief now
/trigger_brief spoilage       — Run spoilage risk check
/trigger_brief velocity       — Run velocity anomaly check
/trigger_brief credit         — Run overdue credit check
/trigger_brief digest         — Run weekly digest + Instinct + dashboard link
/trigger_finance              — Show financial profile + loan eligibility (Section 8 demo)
```

## Conversational Triggers (type these in Telegram)

```
[forward supplier message]    — Auto-detects price quote, gives BELI/PASS verdict + capital check
"macam mana tomato aku?"      — Commodity insight (velocity, stockout, expiry, price trend)
"takda modal"                 — Capital check → loan eligibility → Digital Niaga application
"mohon pinjaman"              — Full AgroCash-i / Agrobank application package
"bila raya haji?"             — Festival date + demand impact on stock (Aidiladha: June 7, 2026)
"ada berita banjir?"          — Live web search for supply disruption news
"profil saya"                 — Full financial profile + creditworthiness score
"dashboard" / "laporan"       — Link to live analytics dashboard
```
