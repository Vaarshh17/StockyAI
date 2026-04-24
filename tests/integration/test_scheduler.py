"""
tests/integration/test_scheduler.py — Integration tests for scheduler jobs.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestStartScheduler:
    def test_start_scheduler_registers_jobs(self):
        mock_bot = MagicMock()
        with patch("scheduler.jobs._scheduler") as mock_sched:
            from scheduler.jobs import start_scheduler
            start_scheduler(mock_bot)
            # Should have added 5 jobs
            assert mock_sched.add_job.call_count == 5
            mock_sched.start.assert_called_once()

    def test_start_scheduler_replaces_existing(self):
        mock_bot = MagicMock()
        with patch("scheduler.jobs._scheduler") as mock_sched:
            from scheduler.jobs import start_scheduler
            start_scheduler(mock_bot)
            for call in mock_sched.add_job.call_args_list:
                assert call[1].get("replace_existing") is True


class TestMorningBriefJob:
    @pytest.mark.asyncio
    async def test_skips_if_no_active_users(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.clear()
        mock_bot = AsyncMock()
        from scheduler.jobs import morning_brief_job
        await morning_brief_job(mock_bot)
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_sends_brief_to_active_users(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.add(42)
        try:
            mock_bot = AsyncMock()
            with patch("agent.core.run_proactive_brief", new=AsyncMock(return_value="Morning brief!")):
                from scheduler.jobs import morning_brief_job
                await morning_brief_job(mock_bot)
            mock_bot.send_message.assert_called()
        finally:
            ACTIVE_USERS.discard(42)


class TestSpoilageCheckJob:
    @pytest.mark.asyncio
    async def test_no_alert_when_no_risk(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.add(42)
        try:
            mock_bot = AsyncMock()
            with patch("db.queries.db_get_inventory", new=AsyncMock(return_value=[
                {"commodity": "tomato", "quantity_kg": 500, "days_remaining": 5}
            ])):
                with patch("services.weather.get_forecast", new=AsyncMock(return_value=[])):
                    from scheduler.jobs import spoilage_check_job
                    await spoilage_check_job(mock_bot)
            mock_bot.send_message.assert_not_called()
        finally:
            ACTIVE_USERS.discard(42)

    @pytest.mark.asyncio
    async def test_alerts_when_spoilage_risk(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.add(42)
        try:
            mock_bot = AsyncMock()
            with patch("db.queries.db_get_inventory", new=AsyncMock(return_value=[
                {"commodity": "bayam", "quantity_kg": 200, "days_remaining": 1},
                {"commodity": "tomato", "quantity_kg": 500, "days_remaining": 5},
            ])):
                with patch("services.weather.get_forecast", new=AsyncMock(return_value=[
                    {"date": "2024-04-20", "is_rainy": True},
                ])):
                    from scheduler.jobs import spoilage_check_job
                    await spoilage_check_job(mock_bot)
            mock_bot.send_message.assert_called_once()
            msg = mock_bot.send_message.call_args[1]["text"]
            assert "bayam" in msg.lower() or "Amaran" in msg
        finally:
            ACTIVE_USERS.discard(42)


class TestVelocityAlertJob:
    @pytest.mark.asyncio
    async def test_no_alert_when_normal(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.add(42)
        try:
            mock_bot = AsyncMock()
            with patch("db.queries.db_get_inventory", new=AsyncMock(return_value=[
                {"commodity": "tomato", "quantity_kg": 500}
            ])):
                with patch("db.queries.db_get_velocity", new=AsyncMock(return_value={"avg_daily_kg": 100})):
                    from scheduler.jobs import velocity_alert_job
                    await velocity_alert_job(mock_bot)
            mock_bot.send_message.assert_not_called()
        finally:
            ACTIVE_USERS.discard(42)

    @pytest.mark.asyncio
    async def test_alerts_on_low_stock(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.add(42)
        try:
            mock_bot = AsyncMock()
            with patch("db.queries.db_get_inventory", new=AsyncMock(return_value=[
                {"commodity": "cili", "quantity_kg": 50}
            ])):
                with patch("db.queries.db_get_velocity", new=AsyncMock(return_value={"avg_daily_kg": 100})):
                    from scheduler.jobs import velocity_alert_job
                    await velocity_alert_job(mock_bot)
            mock_bot.send_message.assert_called_once()
        finally:
            ACTIVE_USERS.discard(42)


class TestCreditReminderJob:
    @pytest.mark.asyncio
    async def test_no_alert_when_no_urgent_credit(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.add(42)
        try:
            mock_bot = AsyncMock()
            with patch("db.queries.db_get_credit", new=AsyncMock(return_value=[
                {"buyer_name": "Buyer", "amount_rm": 100, "due_today": False, "days_overdue": 0}
            ])):
                from scheduler.jobs import credit_reminder_job
                await credit_reminder_job(mock_bot)
            mock_bot.send_message.assert_not_called()
        finally:
            ACTIVE_USERS.discard(42)

    @pytest.mark.asyncio
    async def test_alerts_on_overdue_credit(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.add(42)
        try:
            mock_bot = AsyncMock()
            with patch("db.queries.db_get_credit", new=AsyncMock(return_value=[
                {"buyer_name": "Late Payer", "amount_rm": 500, "due_today": False, "days_overdue": 3},
            ])):
                from scheduler.jobs import credit_reminder_job
                await credit_reminder_job(mock_bot)
            mock_bot.send_message.assert_called_once()
            msg = mock_bot.send_message.call_args[1]["text"]
            assert "Late Payer" in msg
        finally:
            ACTIVE_USERS.discard(42)


class TestMondayDigestJob:
    @pytest.mark.asyncio
    async def test_sends_digest(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.add(42)
        try:
            mock_bot = AsyncMock()
            with patch("agent.core.run_proactive_brief", new=AsyncMock(return_value="Weekly digest!")):
                from scheduler.jobs import monday_digest_job
                await monday_digest_job(mock_bot)
            mock_bot.send_message.assert_called()
        finally:
            ACTIVE_USERS.discard(42)


class TestSendToAllUsers:
    @pytest.mark.asyncio
    async def test_sends_to_all_active_users(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.add(1)
        ACTIVE_USERS.add(2)
        try:
            mock_bot = AsyncMock()
            from scheduler.jobs import _send_to_all_users
            await _send_to_all_users(mock_bot, "Test message")
            assert mock_bot.send_message.call_count == 2
        finally:
            ACTIVE_USERS.discard(1)
            ACTIVE_USERS.discard(2)

    @pytest.mark.asyncio
    async def test_handles_send_failure_gracefully(self):
        from bot.handlers import ACTIVE_USERS
        ACTIVE_USERS.add(99)
        try:
            mock_bot = AsyncMock()
            mock_bot.send_message.side_effect = Exception("Send failed")
            from scheduler.jobs import _send_to_all_users
            await _send_to_all_users(mock_bot, "Test")  # Should not raise
        finally:
            ACTIVE_USERS.discard(99)
