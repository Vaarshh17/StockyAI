"""
Demo Scenario 3: Credit Ledger + Payment Reminder
User logs credit sale. Reminder is drafted.
Owner: Person 5
"""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

async def run():
    print("=" * 60)
    print("SCENARIO 3: Credit Ledger + Reminder")
    print("=" * 60)
    from db.seed import seed_demo_data
    await seed_demo_data()

    from agent.core import run_agent
    print("User says: 'Kedai Pak Hamid ambil 500kg bayam, bayar Jumaat, RM800'\n")
    result = await run_agent(
        user_id=1,
        input_text="Kedai Pak Hamid ambil 500kg bayam, bayar Jumaat, RM800",
        input_type="text"
    )
    print("Bot response:")
    print(result["text"])

    print("\nChecking outstanding credit...")
    result2 = await run_agent(
        user_id=1,
        input_text="Siapa yang masih belum bayar?",
        input_type="text"
    )
    print("Bot response:")
    print(result2["text"])
    assert "hamid" in result2["text"].lower() or "800" in result2["text"]

    print("\n✅ Scenario 3 PASSED")

if __name__ == "__main__":
    asyncio.run(run())
