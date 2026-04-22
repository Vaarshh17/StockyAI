"""
agent/memory.py — Conversation history per user (in-memory).
Stores last N messages per Telegram user_id.
Owner: Person 1
"""
from collections import defaultdict

# In-memory store: {user_id: [messages]}
_history: dict[int, list[dict]] = defaultdict(list)
MAX_TURNS = 10  # keep last 10 turns (20 messages: 10 user + 10 assistant)


def get_history(user_id: int, limit: int = MAX_TURNS) -> list[dict]:
    """Return last `limit` turns of conversation history."""
    history = _history[user_id]
    return history[-(limit * 2):]  # *2 because each turn = 1 user + 1 assistant message


def save_turn(user_id: int, user_msg: dict, assistant_msg: dict):
    """Append a user + assistant message pair to history."""
    _history[user_id].append(user_msg)
    _history[user_id].append(assistant_msg)
    # Trim to MAX_TURNS * 2 messages
    if len(_history[user_id]) > MAX_TURNS * 2:
        _history[user_id] = _history[user_id][-(MAX_TURNS * 2):]


def clear_history(user_id: int):
    """Clear conversation history for a user (e.g., on /start)."""
    _history[user_id] = []


def save_draft(user_id: int, draft_id: str, draft: dict):
    """Store a pending draft message awaiting approval."""
    _drafts[user_id][draft_id] = draft


def get_draft(user_id: int, draft_id: str) -> dict | None:
    return _drafts.get(user_id, {}).get(draft_id)


# Draft store: {user_id: {draft_id: draft_dict}}
_drafts: dict[int, dict[str, dict]] = defaultdict(dict)
