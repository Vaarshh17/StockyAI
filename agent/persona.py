"""
agent/persona.py — User persona store + onboarding state machine.

Learns user preferences during first conversation and injects them into
the system prompt so Stocky speaks the right language, watches the right
commodities, and addresses the user by name.

Onboarding flow (4 questions, one at a time):
  1. Name
  2. Preferred language
  3. Main commodities
  4. City (for weather)
"""
import logging
from db.queries import db_save_persona, db_get_persona

logger = logging.getLogger(__name__)

# In-memory cache: {user_id: persona_dict}
_personas: dict[int, dict] = {}

# Onboarding state: {user_id: current_step}
_onboarding: dict[int, str] = {}

ONBOARDING_QUESTIONS = {
    "name":        "👋 First, what should I call you?",
    "language":    (
        "🌐 What language do you prefer?\n\n"
        "Reply with: *English*, *Malay*, or *中文*"
    ),
    "commodities": (
        "📦 What are your main commodities?\n\n"
        "_(Separate with commas — e.g. tomato, bayam, cili, mangga)_"
    ),
    "city":        (
        "🌤️ Which city are you based in?\n\n"
        "_(For weather forecasts — e.g. Kuala Lumpur, Ipoh, Johor Bahru)_"
    ),
}

LANGUAGE_MAP = {
    "english":          "English",
    "malay":            "Bahasa Malaysia",
    "bahasa":           "Bahasa Malaysia",
    "bahasa malaysia":  "Bahasa Malaysia",
    "bm":               "Bahasa Malaysia",
    "中文":              "Mandarin",
    "mandarin":         "Mandarin",
    "chinese":          "Mandarin",
}


async def load_persona(user_id: int) -> dict | None:
    """Load persona from DB into memory cache. Call on bot start or /start."""
    if user_id in _personas:
        return _personas[user_id]
    persona = await db_get_persona(user_id)
    if persona:
        _personas[user_id] = persona
        logger.info(f"[persona] loaded for user {user_id}: {persona.get('name')} / {persona.get('language')}")
    return persona


def get_persona(user_id: int) -> dict | None:
    return _personas.get(user_id)


def is_onboarded(user_id: int) -> bool:
    p = _personas.get(user_id)
    return bool(p and p.get("name"))


def get_onboarding_step(user_id: int) -> str | None:
    return _onboarding.get(user_id)


def start_onboarding(user_id: int):
    _onboarding[user_id] = "name"
    logger.info(f"[persona] onboarding started for user {user_id}")


async def process_onboarding_answer(user_id: int, text: str) -> tuple[str, bool]:
    """
    Process one onboarding answer.
    Returns (reply_text, is_complete).
    """
    step = _onboarding.get(user_id)
    persona = _personas.get(user_id, {})
    text = text.strip()

    if step == "name":
        persona["name"] = text.title()
        _personas[user_id] = persona
        _onboarding[user_id] = "language"
        return ONBOARDING_QUESTIONS["language"], False

    elif step == "language":
        mapped = LANGUAGE_MAP.get(text.lower(), "English")
        persona["language"] = mapped
        _personas[user_id] = persona
        _onboarding[user_id] = "commodities"
        return ONBOARDING_QUESTIONS["commodities"], False

    elif step == "commodities":
        commodities = [c.strip().lower() for c in text.split(",") if c.strip()]
        persona["commodities"] = commodities[:6]  # cap at 6
        _personas[user_id] = persona
        _onboarding[user_id] = "city"
        return ONBOARDING_QUESTIONS["city"], False

    elif step == "city":
        persona["city"] = text.title()
        _personas[user_id] = persona
        _onboarding.pop(user_id, None)

        # Persist to DB
        await db_save_persona(user_id, persona)
        logger.info(f"[persona] onboarding complete for user {user_id}: {persona}")

        name = persona.get("name", "there")
        commodities_str = ", ".join(persona.get("commodities", []))
        city = persona.get("city", "Kuala Lumpur")
        language = persona.get("language", "English")

        done_msg = (
            f"✅ All set, *{name}!*\n\n"
            f"📦 Watching: _{commodities_str}_\n"
            f"🌤️ Weather for: _{city}_\n"
            f"🌐 Language: _{language}_\n\n"
            f"You're ready. Try telling me about your latest stock arrival, "
            f"or run `/trigger_brief morning` to see your morning brief."
        )
        return done_msg, True

    # Fallback — shouldn't happen
    return "Let's start over. What should I call you?", False


def build_profile_block(persona: dict) -> str:
    """Build the USER PROFILE section to inject into the system prompt."""
    name = persona.get("name", "")
    commodities = persona.get("commodities", [])
    city = persona.get("city", "Kuala Lumpur")
    commodities_str = ", ".join(commodities) if commodities else "not specified"

    return f"""
═══════════════════════════════════════
USER PROFILE
═══════════════════════════════════════
Name: {name}
Main commodities: {commodities_str}
City: {city}

Always address the user as "{name}".
When giving inventory alerts or buy recommendations, prioritise: {commodities_str}.
Default city for weather forecasts: {city}.
""".strip()
