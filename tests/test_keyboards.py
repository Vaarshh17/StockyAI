"""
tests/unit/test_keyboards.py — Unit tests for bot/keyboards.py
"""
from bot.keyboards import approval_keyboard, yes_no_keyboard


class TestApprovalKeyboard:
    def test_creates_inline_keyboard(self):
        kb = approval_keyboard("test123")
        assert kb is not None
        buttons = kb.inline_keyboard
        assert len(buttons) == 1  # One row
        assert len(buttons[0]) == 2  # Two buttons: approve + edit

    def test_approve_button_has_draft_id(self):
        kb = approval_keyboard("abc")
        buttons = kb.inline_keyboard
        approve_btn = buttons[0][0]
        assert "approve_abc" in approve_btn.callback_data

    def test_edit_button_has_draft_id(self):
        kb = approval_keyboard("xyz")
        buttons = kb.inline_keyboard
        edit_btn = buttons[0][1]
        assert "edit_xyz" in edit_btn.callback_data


class TestYesNoKeyboard:
    def test_creates_two_buttons(self):
        kb = yes_no_keyboard("yes_data", "no_data")
        buttons = kb.inline_keyboard
        assert len(buttons) == 1
        assert len(buttons[0]) == 2

    def test_yes_button_data(self):
        kb = yes_no_keyboard("confirm", "cancel")
        yes_btn = kb.inline_keyboard[0][0]
        assert yes_btn.callback_data == "confirm"

    def test_no_button_data(self):
        kb = yes_no_keyboard("confirm", "cancel")
        no_btn = kb.inline_keyboard[0][1]
        assert no_btn.callback_data == "cancel"
