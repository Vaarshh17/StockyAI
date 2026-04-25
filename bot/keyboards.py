"""
bot/keyboards.py — Inline keyboard builders.
Owner: Person 3
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def approval_keyboard(draft_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Guna mesej ini", callback_data=f"approve_{draft_id}"),
            InlineKeyboardButton("✏️ Edit",           callback_data=f"edit_{draft_id}"),
        ]
    ])


def yes_no_keyboard(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Ya",   callback_data=yes_data),
            InlineKeyboardButton("❌ Tidak", callback_data=no_data),
        ]
    ])


def action_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    Keyboard shown at the bottom of morning brief / festival alerts
    when Stocky has proposed specific buy orders.
    Approve → executes all orders + generates WhatsApp links.
    Skip → clears pending actions silently.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Laksanakan semua",  callback_data=f"exec_actions_{user_id}"),
            InlineKeyboardButton("⏭️ Skip",             callback_data=f"skip_actions_{user_id}"),
        ]
    ])
