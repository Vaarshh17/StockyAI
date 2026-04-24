"""
tests/e2e/test_scenarios.py — End-to-end tests simulating full user journeys.
These test the entire stack: agent loop → tool calls → DB → response.
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import date, timedelta


class TestInventoryScenario:
    @pytest.mark.asyncio
    async def test_user_adds_stock_then_queries(self, seeded_db, reset_memory, reset_persona):
        """User adds inventory, then asks about stock levels."""
        from agent.core import run_agent

        # Mock: first call triggers update_inventory, second call is final answer
        tool_call_resp = {
            "content": None,
            "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {"name": "update_inventory", "arguments": '{"commodity": "mangga", "quantity_kg": 300, "price_per_kg": 3.50, "supplier_name": "Pak Ali"}'}
            }],
        }
        final_resp = {
            "content": "Stok mangga sudah dikemas kini. 300kg ditambah daripada Pak Ali pada RM3.50/kg.",
            "tool_calls": None,
        }

        with patch("agent.core.call_llm", new=AsyncMock(side_effect=[tool_call_resp, final_resp])):
            with patch("agent.core.execute_tool", new=AsyncMock(return_value={"status": "updated", "commodity": "mangga", "added_kg": 300, "total_stock_kg": 300})):
                with patch("agent.core.get_persona", return_value={"name": "Ahmad", "language": "Bahasa Malaysia", "commodities": ["tomato"], "city": "KL"}):
                    result = await run_agent(user_id=1, input_text="Dapat 300kg mangga dari Pak Ali, RM3.50 sekilo")

        assert "text" in result
        assert result["needs_approval"] is False

    @pytest.mark.asyncio
    async def test_user_sells_and_stock_deducted(self, seeded_db, reset_memory, reset_persona):
        """User records a sale, stock should decrease via FIFO."""
        from db.queries import db_get_inventory, db_log_sell

        before = await db_get_inventory("tomato")
        before_qty = sum(r["quantity_kg"] for r in before)

        await db_log_sell("tomato", 100, price_per_kg=3.20, buyer_name="Restoran Maju")

        after = await db_get_inventory("tomato")
        after_qty = sum(r["quantity_kg"] for r in after)
        assert after_qty == before_qty - 100


class TestCreditScenario:
    @pytest.mark.asyncio
    async def test_log_credit_then_check_overdue(self, seeded_db, reset_memory, reset_persona):
        """User logs a credit sale, then checks who owes money."""
        from agent.core import run_agent

        tool_call_resp = {
            "content": None,
            "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {"name": "log_credit", "arguments": '{"buyer_name": "Kedai Baru", "amount_rm": 800, "commodity": "cili", "due_date": "2024-03-01"}'}
            }],
        }
        final_resp = {
            "content": "Kredit RM800 untuk Kedai Baru dicatat. Tarikh matang: 1 Mac 2024.",
            "tool_calls": None,
        }

        with patch("agent.core.call_llm", new=AsyncMock(side_effect=[tool_call_resp, final_resp])):
            with patch("agent.core.execute_tool", new=AsyncMock(return_value={"status": "logged", "buyer_name": "Kedai Baru", "amount_rm": 800, "total_outstanding": 800})):
                with patch("agent.core.get_persona", return_value={"name": "Ahmad", "language": "Bahasa Malaysia", "commodities": ["cili"], "city": "KL"}):
                    result = await run_agent(user_id=1, input_text="Kedai Baru ambil cili RM800, bayar 1 Mac")

        assert "text" in result

    @pytest.mark.asyncio
    async def test_draft_message_for_overdue(self, seeded_db, reset_memory, reset_persona):
        """Agent should offer to draft a payment reminder for overdue credit."""
        from agent.core import run_agent

        # First call: get_outstanding_credit
        tool_call_resp = {
            "content": None,
            "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {"name": "get_outstanding_credit", "arguments": '{}'}
            }],
        }
        # Second call: draft message
        draft_resp = {
            "content": "DRAFT_MESSAGE::Kedai Pak Hamid::malay::Pak Hamid, pembayaran RM1400 untuk bayam sudah lewat. Boleh bayar minggu ini?",
            "tool_calls": None,
        }

        with patch("agent.core.call_llm", new=AsyncMock(side_effect=[tool_call_resp, draft_resp])):
            with patch("agent.core.execute_tool", new=AsyncMock(return_value=[
                {"buyer_name": "Kedai Pak Hamid", "amount_rm": 1400, "days_overdue": 1}
            ])):
                with patch("agent.core.get_persona", return_value={"name": "Ahmad", "language": "Bahasa Malaysia", "commodities": ["bayam"], "city": "KL"}):
                    result = await run_agent(user_id=1, input_text="siapa belum bayar?")

        assert result["needs_approval"] is True
        assert result["draft_id"] is not None


class TestMorningBriefScenario:
    @pytest.mark.asyncio
    async def test_full_morning_brief_flow(self, seeded_db, reset_memory, reset_persona):
        """Full morning brief: agent calls multiple tools, gets weather, adds instinct."""
        from agent.core import run_proactive_brief

        # Simulate: multiple tool calls then final response
        inventory_call = {
            "content": None,
            "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "get_inventory", "arguments": '{}'}}],
        }
        weather_call = {
            "content": None,
            "tool_calls": [{"id": "c2", "type": "function", "function": {"name": "get_weather_forecast", "arguments": '{}'}}],
        }
        credit_call = {
            "content": None,
            "tool_calls": [{"id": "c3", "type": "function", "function": {"name": "get_outstanding_credit", "arguments": '{}'}}],
        }
        final_resp = {
            "content": "🌅 Morning Brief\n📦 Stok: tomato 800kg (5 hari), bayam 920kg (⚠️ 3 hari)\n💸 Hutang: Kedai Pak Hamid RM1400 lewat 1 hari\n🌧️ Hujan dijangka Rabu\n🛒 Cadang beli: cili dari Pak Ali RM4/kg",
            "tool_calls": None,
        }

        with patch("agent.core.call_llm", new=AsyncMock(side_effect=[inventory_call, weather_call, credit_call, final_resp])):
            with patch("agent.core.execute_tool", new=AsyncMock(side_effect=[
                [{"commodity": "tomato", "quantity_kg": 800, "days_remaining": 5}],
                [{"date": "2024-04-20", "condition": "Hujan", "is_rainy": True}],
                [{"buyer_name": "Kedai Pak Hamid", "amount_rm": 1400, "days_overdue": 1}],
            ])):
                with patch("agent.core.get_persona", return_value={"name": "Ahmad", "language": "Bahasa Malaysia", "commodities": ["tomato"], "city": "KL"}):
                    with patch("agent.instinct.get_instinct", new=AsyncMock(return_value="Stocky nampak sesuatu: bayam jual lambat tapi stok tinggi")):
                        result = await run_proactive_brief(user_id=1, brief_type="morning")

        assert "Morning Brief" in result
        assert "Stocky nampak" in result


class TestSupplierComparisonScenario:
    @pytest.mark.asyncio
    async def test_compare_prices_and_recommend(self, seeded_db, reset_memory, reset_persona):
        """User asks who's cheapest for tomato, agent compares suppliers."""
        from agent.core import run_agent

        tool_call_resp = {
            "content": None,
            "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "compare_supplier_prices", "arguments": '{"commodity": "tomato"}'}}],
        }
        final_resp = {
            "content": "🟢 Pak Ali | RM2.60/kg | -5% vs FAMA | Buy\n🔴 Ah Seng | RM2.85/kg | +4% vs FAMA | Skip",
            "tool_calls": None,
        }

        with patch("agent.core.call_llm", new=AsyncMock(side_effect=[tool_call_resp, final_resp])):
            with patch("agent.core.execute_tool", new=AsyncMock(return_value={
                "commodity": "tomato",
                "suppliers": [
                    {"name": "Pak Ali", "price_per_kg": 2.60, "vs_fama_pct": -5},
                    {"name": "Ah Seng", "price_per_kg": 2.85, "vs_fama_pct": 4},
                ],
                "fama_benchmark": 2.75,
                "cheapest": {"name": "Pak Ali", "price_per_kg": 2.60},
            })):
                with patch("agent.core.get_persona", return_value={"name": "Ahmad", "language": "Bahasa Malaysia", "commodities": ["tomato"], "city": "KL"}):
                    result = await run_agent(user_id=1, input_text="siapa paling murah untuk tomato?")

        assert "Pak Ali" in result["text"]


class TestOnboardingE2E:
    @pytest.mark.asyncio
    async def test_new_user_onboarding_flow(self, reset_memory, reset_persona, seeded_db):
        """New user goes through full onboarding, then asks a question."""
        from agent.persona import start_onboarding, process_onboarding_answer, is_onboarded, get_persona

        # Start onboarding
        start_onboarding(1)
        assert is_onboarded(1) is False

        # Complete 4 steps
        with patch("db.queries.db_save_persona", new=AsyncMock()):
            await process_onboarding_answer(1, "Siti")
            await process_onboarding_answer(1, "Malay")
            await process_onboarding_answer(1, "tomato, cili, bayam")
            _, complete = await process_onboarding_answer(1, "Shah Alam")

        assert complete is True
        assert is_onboarded(1) is True

        persona = get_persona(1)
        assert persona["name"] == "Siti"
        assert persona["language"] == "Bahasa Malaysia"
        assert "tomato" in persona["commodities"]
        assert persona["city"] == "Shah Alam"


class TestVoiceInputE2E:
    @pytest.mark.asyncio
    async def test_voice_transcribed_and_processed(self, reset_memory, reset_persona, seeded_db):
        """Voice note → transcribe → agent processes text."""
        from agent.core import run_agent

        final_resp = {
            "content": "Stok tomato 800kg, 5 hari lagi.",
            "tool_calls": None,
        }

        with patch("agent.core.call_llm", new=AsyncMock(return_value=final_resp)):
            with patch("agent.core.get_persona", return_value={"name": "Ahmad", "language": "Bahasa Malaysia", "commodities": ["tomato"], "city": "KL"}):
                result = await run_agent(user_id=1, input_text="stok tomato berapa", input_type="voice")

        assert "text" in result
