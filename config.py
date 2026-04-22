"""
config.py — Central config for Stocky AI.
All env vars loaded here. Import from here everywhere else.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ── Z.AI / GLM ────────────────────────────────────────────────────────────────
GLM_API_KEY: str = os.getenv("GLM_API_KEY", "")
GLM_MODEL: str   = os.getenv("GLM_MODEL", "glm-4v-plus")
GLM_API_URL: str = os.getenv(
    "GLM_API_URL",
    "https://open.bigmodel.cn/api/paas/v4/chat/completions"
)

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


def validate():
    errors = []
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN missing — get from @BotFather")
    if not GLM_API_KEY and not DEMO_MODE:
        errors.append("GLM_API_KEY missing — get from open.bigmodel.cn (set DEMO_MODE=True to bypass)")
    if not SUPABASE_DB_URL and not DEMO_MODE:
        print("⚠️  SUPABASE_DB_URL not set — falling back to local SQLite (ok for dev)")
    if errors:
        raise ValueError(f"Config errors:\n" + "\n".join(f"  ✗ {e}" for e in errors))
    print("✅ Config validated.")
