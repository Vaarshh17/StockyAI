"""
config.py — Central config for Stocky AI.
All env vars loaded here. Import from here everywhere else.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Always load .env from the same directory as this file, regardless of cwd
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

# ── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ── ILMU API (Z.ai / YTL AI Labs) ─────────────────────────────────────────────
# Get from: console.ilmu.ai → API Keys (starts with sk-)
ILMU_API_KEY: str = os.getenv("ILMU_API_KEY", "")
ILMU_API_URL: str = os.getenv("ILMU_API_URL", "https://api.ilmu.ai/v1")

# Two-model strategy:
#   nemo-super      → complex reasoning (morning brief, instinct, draft messages)
#   ilmu-nemo-nano  → lightweight tool calls (proactive scheduler jobs)
MODEL_SMART: str = os.getenv("MODEL_SMART", "nemo-super")
MODEL_FAST:  str = os.getenv("MODEL_FAST",  "ilmu-nemo-nano")

# ── Supabase / Database ───────────────────────────────────────────────────────
# Get from: Supabase Dashboard → Settings → Database → Connection string (URI)
# Format:   postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")

# Fallback to SQLite for local dev without Supabase
DATABASE_URL: str = SUPABASE_DB_URL or os.getenv("DATABASE_URL", "sqlite+aiosqlite:///stocky_ai.db")

# ── Scheduler ─────────────────────────────────────────────────────────────────
MORNING_BRIEF_HOUR: int = int(os.getenv("MORNING_BRIEF_HOUR", "3"))
MORNING_BRIEF_MIN:  int = int(os.getenv("MORNING_BRIEF_MIN",  "30"))

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_CITY:     str  = os.getenv("DEFAULT_CITY", "Kuala Lumpur")
DEFAULT_LANGUAGE: str  = os.getenv("DEFAULT_LANGUAGE", "malay")
DEMO_MODE:        bool = os.getenv("DEMO_MODE", "False").lower() == "true"

# ── Dashboard ─────────────────────────────────────────────────────────────────
# URL of the deployed React dashboard (Lovable / Vercel / Netlify)
DASHBOARD_URL: str = os.getenv("DASHBOARD_URL", "")


def validate():
    errors = []
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN missing — get from @BotFather on Telegram")
    if not ILMU_API_KEY and not DEMO_MODE:
        errors.append("ILMU_API_KEY missing — get from console.ilmu.ai (set DEMO_MODE=True to bypass)")
    if not SUPABASE_DB_URL and not DEMO_MODE:
        print("⚠️  SUPABASE_DB_URL not set — falling back to local SQLite (ok for dev)")
    if errors:
        raise ValueError("Config errors:\n" + "\n".join(f"  ✗ {e}" for e in errors))
    print(f"✅ Config validated. Model: {MODEL_SMART} | Key: {ILMU_API_KEY[:12]}...")
