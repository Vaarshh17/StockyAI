# 🌿 Stocky AI

> A proactive decision intelligence agent for Malaysian wet market wholesalers.  
> Lives entirely on Telegram. Speaks Malay, Mandarin, and English. Watches your business while you sleep.

### **UM Hackathon 2026 — Domain: AI for Economic Empowerment & Decision Intelligence**<br>
**Pitch Video**: https://drive.google.com/file/d/1YgCEzYUSTP9JbD0QVYEmU-bPM4GE3nHx/view?usp=sharing<br>
**Pitch Deck**:  ```docs/Stocky_AI_Pitch Deck.pdf```<br><br>
**PRD (Product)**: ```docs/Stocky_AI_PRD.pdf```<br>
**SAD (System)**: ```docs/Stocky_AI_SAD.pdf```<br>
**TAD (Testing)**: ```docs/Stocky_AI_TAD.pdf```<br>


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

### 1. 📦 Inventory & Spoilage Intelligence
Tracks current stock levels per commodity. Calculates days until expiry based on shelf life. Alerts the wholesaler when something is at risk before it's too late to act — with a specific suggestion: discount, push to certain buyers, or call the supplier.

### 2. 💰 Supplier Price Comparison + FAMA Benchmark
Stores quoted prices from each supplier per commodity. Compares against weekly FAMA government benchmark prices. Tells the wholesaler who is cheapest right now, who has drifted above market rate, and factors in supplier reliability — cheapest isn't always best.

### 3. 📊 Trade Logging (Buy & Sell)
Logs every purchase and sale. Calculates sell velocity per commodity over the last 30 days. Powers spoilage prediction and reorder timing — Stocky knows how fast each commodity moves and can tell when stock will run out before the wholesaler notices.

### 4. 💸 Receivables & Credit Tracking
Tracks who owes money, how much, and when it's due. Flags overdue accounts. Drafts the follow-up message in the buyer's preferred language, ready for the wholesaler to approve and send in one tap.

> Notes for 3 & 4: Stocky works from data the user provides — by typing, voice note, or forwarding messages from suppliers and buyers.

### 5. 🌅 Morning Brief (3:30 AM, before market opens)
Every morning, Stocky sends an unprompted brief: what's low on stock, what's expiring today, who's overdue on payment, today's weather and how it affects demand, and one proactive buy recommendation. The wholesaler wakes up already knowing what to do.

### 6. 🔮 Stocky's Instinct
Once a week, appended to the Monday digest, Stocky analyses 14 days of inventory, sales velocity, credit, supplier prices, and FAMA trends together and surfaces one cross-signal pattern. Example: *"Bayam sell velocity dropped 40% in the same week Pak Ali's price went up — buyers are substituting. Consider switching to kangkung next week."* Only fires when the signal crosses a significance threshold — no noise.

### 7. 🎙️ Voice Note Input
Wholesaler sends a voice note → Whisper transcribes it locally → Stocky processes it exactly like a text message. A 55-year-old trader who doesn't want to type can run their entire business through voice.

### 8. 🌐 Multilingual (Malay, Mandarin, English, code-switching)
Stocky understands and responds in whatever language the wholesaler writes or speaks in. Malaysian market traders code-switch mid-sentence — Stocky handles this natively.

### 9. ✉️ Draft Message Generation
When action involves another person (supplier, buyer), Stocky drafts the message in the correct language for that contact and presents it for approval. Wholesaler taps Approve → copies to WhatsApp. One decision, not five steps.

---

## Powered by ILMU (Z.ai / YTL AI Labs)

`ilmu-glm-5.1` is the reasoning core. Without it, this is just a database.  
With it, it synthesizes weather + velocity + shelf life + supplier history + credit into a decision — and explains why.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | ilmu-glm-5.1 (ILMU API by Z.ai / YTL AI Labs) |
| Bot | python-telegram-bot v20 |
| Backend | Python (async) |
| Database | Supabase (Postgres via asyncpg) + SQLite fallback |
| Scheduler | APScheduler |
| Voice | faster-whisper (local, tiny model) |
| Weather | Open-Meteo API (free) |
| Prices | FAMA benchmark (seeded) |

---

## Project Structure

```
stocky_ai/
├── agent/          # 🧠 Agent loop + tools + prompts + memory + instinct
├── bot/            # 📱 Telegram handlers + keyboards + formatters
├── db/             # 🗄️  Database models + queries + seed data
├── scheduler/      # ⏰ Proactive jobs (morning brief, spoilage, velocity, credit, digest)
└── services/       # 🔌 ILMU API client, weather, voice transcription
└── docs/           # 📃 Product, System and Testing documentations for our solution, Stocky AI
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
```

---
## Run Test

```
$ python -m pytest
```


## Demo Commands

```
/start                        — Initialise bot, clear history
/trigger_brief morning        — Fire the 3:30 AM morning brief now
/trigger_brief spoilage       — Run spoilage risk check
/trigger_brief velocity       — Run velocity anomaly check
/trigger_brief credit         — Run overdue credit check
/trigger_brief digest         — Run weekly digest + Instinct
```
