# Stocky AI — System Architecture

---

## High-Level Flow

```
[Wholesaler on Telegram]
         │
         │  text / voice / forwarded msg
         ▼
[python-telegram-bot]
         │
         ▼
[bot/handlers.py]  ──────────────────────────────────────┐
         │                                               │
         │  Onboarding gate (4-step persona setup)       │
         │  run_agent(user_id, input)                    │ send_message(user_id, text)
         ▼                                               │
[agent/core.py — The Agent Loop]                         │
    0. Load persona (agent/persona.py)                   │
    1. Build messages (system prompt + history + input)  │
    2. Call GLM with tools                               │
    3. If tool_calls → execute tools                     │
    4. Loop until final response                         │
    5. Return response text                              │
         │                                               │
    ┌────┴─────────────────────────┐                    │
    │         Tool Calls           │                    │
    ▼                              ▼                    │
[db/queries.py]          [services/]                   │
 - get_inventory()        - glm.py (ILMU API)           │
 - update_inventory()     - weather.py (Open-Meteo)     │
 - log_sell()             - fama.py (price benchmarks)  │
 - compare_prices()       - voice.py (Whisper STT)      │
 - get_credit()           - festivals.py (MY calendar)  │
 - log_credit()                                         │
 - get_weekly_digest()    ◄──────────────────────────── │
         │
         ▼
   [Supabase (Postgres via asyncpg)]
   [SQLite fallback for local dev]


[scheduler/jobs.py]  (APScheduler — runs in-process)
    - morning_brief_job()     3:30 AM daily  → run_proactive_brief("morning") → send
    - spoilage_check_job()    8 AM + 2 PM    → check inventory + weather → conditional send
    - velocity_alert_job()    every 4h       → check sell velocity → conditional send
    - credit_reminder_job()   9 AM daily     → check receivables → conditional send
    - monday_digest_job()     Mon 7 AM       → run_proactive_brief("digest") + dashboard link → send


[dashboard/]  (React + Vite + Tailwind + shadcn/ui)
    - Separate frontend, deployed on Lovable
    - Linked from Monday digest and /start welcome back message
    - Currently uses mock data (no live API bridge to Python backend)
```

---

## Database Schema

```sql
-- What stock do we have right now?
CREATE TABLE inventory (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity       TEXT NOT NULL,        -- "tomato", "cili", "bayam"
    quantity_kg     REAL NOT NULL,
    entry_date      DATE NOT NULL,
    shelf_life_days INTEGER DEFAULT 7,
    cost_per_kg     REAL,
    supplier_id     INTEGER,
    notes           TEXT,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Who are our suppliers?
CREATE TABLE suppliers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,        -- "Pak Ali", "Ah Seng"
    phone           TEXT,
    language        TEXT DEFAULT 'malay', -- 'malay', 'mandarin', 'english'
    reliability     REAL DEFAULT 5.0      -- 1-10 score
);

-- What prices have suppliers quoted?
CREATE TABLE supplier_prices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id     INTEGER NOT NULL,
    commodity       TEXT NOT NULL,
    price_per_kg    REAL NOT NULL,
    quantity_kg     REAL,
    quoted_date     DATE NOT NULL,
    source          TEXT DEFAULT 'direct' -- 'direct', 'forwarded'
);

-- All buy/sell transactions
CREATE TABLE trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_type      TEXT NOT NULL,        -- 'buy' or 'sell'
    commodity       TEXT NOT NULL,
    quantity_kg     REAL NOT NULL,
    price_per_kg    REAL NOT NULL,
    counterparty    TEXT,
    trade_date      DATE NOT NULL,
    notes           TEXT
);

-- Credit sales — buyer takes goods, pays later
CREATE TABLE receivables (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_name      TEXT NOT NULL,
    commodity       TEXT,
    amount_rm       REAL NOT NULL,
    due_date        DATE,
    paid            BOOLEAN DEFAULT FALSE,
    paid_date       DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FAMA weekly benchmark prices (seeded from published FAMA data)
CREATE TABLE fama_benchmarks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity       TEXT NOT NULL,
    price_per_kg    REAL NOT NULL,
    week_date       DATE NOT NULL          -- Monday of that week
);

-- User onboarding profile (name, language, commodities, city)
CREATE TABLE user_profiles (
    user_id         INTEGER PRIMARY KEY,
    name            TEXT,
    language        TEXT DEFAULT 'English',
    commodities     TEXT,                  -- JSON array
    city            TEXT DEFAULT 'Kuala Lumpur',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## The Agent Loop (core pattern)

```python
async def run_agent(user_id, input):

    persona  = get_persona(user_id)           # name, language, city, commodities
    messages = [get_system_prompt(persona)]   # persona injected into system prompt
             + get_history(user_id)
             + [user_message]

    while True:
        response = await call_llm(messages, tools=TOOLS)

        if response.tool_calls:
            # GLM wants to call a tool
            for tool_call in response.tool_calls:
                result = await execute_tool(tool_call.name, tool_call.args)
                messages.append(tool_result(result))
            messages.append(response)
            # Loop: call GLM again with tool results
        else:
            # GLM has a final answer
            return response.content
```

Forwarded messages get an extra `INSTRUCTION:` block appended forcing tool calls
before any reply — prevents the model responding to price quotes without checking
live inventory and FAMA benchmarks first. Duplicate forwards within 60 seconds are
silently dropped (MD5 dedup).

---

## Onboarding Flow (agent/persona.py)

New users go through a 4-step onboarding before any agent interaction:

```
/start
  → Step 1: "What should I call you?"         → saves: name
  → Step 2: "Preferred language?"              → saves: language (English / Malay / 中文)
  → Step 3: "What are your main commodities?"  → saves: commodities[]
  → Step 4: "Which city are you in?"           → saves: city
  → Profile stored in Supabase user_profiles table
  → Persona injected into every system prompt from this point on
```

---

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| No LangChain | Custom loop | Clean code judges can read. ~80 lines vs 800. |
| Supabase not SQLite | Supabase (Postgres) | Persists across restarts, multi-user ready, free tier sufficient |
| SQLite fallback | aiosqlite | Local dev works without Supabase credentials |
| Polling not webhook | Polling | No public URL needed for local dev and demo |
| ilmu-glm-5.1 | Single model | Only model available on ILMU Claw Free plan |
| APScheduler | In-process | No Redis/Celery needed. Same Python process. |
| Telegram as UI | No frontend for core UX | Target users already on Telegram. Zero new app installs. |
| React dashboard | Lovable (separate deploy) | Visual summary for demo day; linked from weekly digest |
| Voice via Whisper | faster-whisper tiny | Runs locally, no API key, fast enough for voice notes |
| FAMA data seeded | Hardcoded historical data | FAMA site parseable but scraper adds risk; seed sufficient for demo |
| Festival calendar | Hardcoded 2025–2026 dates | No API needed; dates known in advance; directly actionable |

---

## Environment Variables

```env
BOT_TOKEN=...                # From @BotFather on Telegram
ILMU_API_KEY=...             # From console.ilmu.ai (starts with sk-)
ILMU_API_URL=https://api.ilmu.ai/v1
MODEL_SMART=ilmu-glm-5.1
MODEL_FAST=ilmu-glm-5.1
SUPABASE_DB_URL=...          # postgresql+asyncpg://... (optional, falls back to SQLite)
MORNING_BRIEF_HOUR=3
MORNING_BRIEF_MIN=30
DEFAULT_CITY=Kuala Lumpur
DEFAULT_LANGUAGE=English
DEMO_MODE=False              # True = skip GLM calls, use mock responses
DASHBOARD_URL=...            # Deployed Lovable dashboard URL
```
