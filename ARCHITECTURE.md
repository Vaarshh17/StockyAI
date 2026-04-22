# Stocky AI — System Architecture

---

## High-Level Flow

```
[Wholesaler on Telegram]
         │
         │  text / photo / voice / forwarded msg
         ▼
[python-telegram-bot]
         │
         ▼
[bot/handlers.py]  ──────────────────────────────────────┐
         │                                               │
         │ run_agent(user_id, input)                     │ send_message(user_id, text)
         ▼                                               │
[agent/core.py — The Agent Loop]                         │
    1. Build messages (history + input)                  │
    2. Call GLM with tools                               │
    3. If tool_calls → execute tools                     │
    4. Loop until final response                         │
    5. Return response text                              │
         │                                               │
    ┌────┴─────────────────────────┐                    │
    │         Tool Calls           │                    │
    ▼                              ▼                    │
[db/queries.py]          [services/]                   │
 - get_inventory()        - glm.py (GLM API)            │
 - update_inventory()     - weather.py (Open-Meteo)     │
 - log_trade()            - fama.py (price benchmarks)  │
 - compare_prices()                                     │
 - get_credit()           ◄──────────────────────────── │
 - log_credit()
 - get_weekly_digest()
         │
         ▼
   [SQLite Database]


[scheduler/jobs.py]  (APScheduler — runs independently)
    - morning_brief_job()     → calls agent → sends via bot
    - spoilage_check_job()    → calls tools → conditionally sends
    - velocity_alert_job()    → calls tools → conditionally sends
    - credit_reminder_job()   → calls tools → conditionally sends
    - monday_digest_job()     → calls agent → sends via bot
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
    source          TEXT DEFAULT 'direct' -- 'direct', 'forwarded', 'photo'
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

-- FAMA weekly benchmark prices
CREATE TABLE fama_benchmarks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity       TEXT NOT NULL,
    price_per_kg    REAL NOT NULL,
    week_date       DATE NOT NULL          -- Monday of that week
);
```

---

## The Agent Loop (core pattern)

```python
async def run_agent(user_id, input):

    messages = [system_prompt] + get_history(user_id) + [user_message]

    while True:
        response = await call_glm(messages, tools=TOOLS)

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

This is the entire agent. No framework needed. GLM decides when to stop calling tools.

---

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| No LangChain | Custom loop | Clean code judges can read. 80 lines vs 800. |
| SQLite not Postgres | SQLite | Zero infrastructure. File-based. Perfect for hackathon. |
| Polling not webhook | Polling (dev) | No public URL needed for local dev |
| GLM-4V Plus | Single model | Handles text + vision. One API, one integration. |
| APScheduler | In-process | No Redis/Celery needed. Runs in same Python process. |
| No frontend | Telegram is the UI | Target users are already on Telegram. Zero new app installs. |

---

## Environment Variables

```
BOT_TOKEN=          # From BotFather
GLM_API_KEY=        # From open.bigmodel.cn
DATABASE_URL=       # sqlite:///stocky_ai.db
DEFAULT_CITY=       # Kuala Lumpur (for weather)
MORNING_BRIEF_HOUR= # 3 (3:30 AM)
MORNING_BRIEF_MIN=  # 30
LOG_LEVEL=          # INFO
```
