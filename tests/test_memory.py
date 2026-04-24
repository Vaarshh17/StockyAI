"""
tests/unit/test_memory.py — Unit tests for agent/memory.py
"""
from agent.memory import get_history, save_turn, clear_history, save_draft, get_draft, _history, _drafts


class TestGetHistory:
    def test_empty_history_returns_empty(self, reset_memory):
        result = get_history(999)
        assert result == []

    def test_returns_last_n_turns(self, reset_memory):
        user_msg = {"role": "user", "content": "hi"}
        asst_msg = {"role": "assistant", "content": "hello"}
        for _ in range(15):
            save_turn(1, user_msg, asst_msg)
        history = get_history(1, limit=5)
        assert len(history) == 10  # 5 turns * 2 messages

    def test_different_users_isolated(self, reset_memory):
        save_turn(1, {"role": "user", "content": "user1"}, {"role": "assistant", "content": "a1"})
        save_turn(2, {"role": "user", "content": "user2"}, {"role": "assistant", "content": "a2"})
        assert len(get_history(1)) == 2
        assert len(get_history(2)) == 2
        assert get_history(1)[0]["content"] == "user1"


class TestSaveTurn:
    def test_appends_messages(self, reset_memory):
        save_turn(1, {"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"})
        history = get_history(1)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_trims_to_max_turns(self, reset_memory):
        for i in range(15):
            save_turn(1, {"role": "user", "content": f"msg{i}"}, {"role": "assistant", "content": f"reply{i}"})
        history = get_history(1)
        assert len(history) <= 20  # MAX_TURNS * 2


class TestClearHistory:
    def test_clears_history(self, reset_memory):
        save_turn(1, {"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"})
        clear_history(1)
        assert get_history(1) == []

    def test_doesnt_affect_other_users(self, reset_memory):
        save_turn(1, {"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"})
        save_turn(2, {"role": "user", "content": "yo"}, {"role": "assistant", "content": "sup"})
        clear_history(1)
        assert get_history(1) == []
        assert len(get_history(2)) == 2


class TestDrafts:
    def test_save_and_get_draft(self, reset_memory):
        draft = {"recipient": "Pak Ali", "language": "malay", "message": "test"}
        save_draft(1, "abc123", draft)
        result = get_draft(1, "abc123")
        assert result == draft

    def test_get_nonexistent_draft_returns_none(self, reset_memory):
        assert get_draft(1, "nonexistent") is None

    def test_different_users_isolated(self, reset_memory):
        save_draft(1, "d1", {"message": "user1"})
        save_draft(2, "d2", {"message": "user2"})
        assert get_draft(1, "d1")["message"] == "user1"
        assert get_draft(2, "d2")["message"] == "user2"
