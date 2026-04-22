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
