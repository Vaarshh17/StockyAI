"""
Demo Scenario 2: Inventory Update + Velocity Alert
User logs a delivery. Then velocity spike is detected.
Owner: Person 5
"""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

async def run():
    print("=" * 60)
    print("SCENARIO 2: Inventory Update + Velocity")
    print("=" * 60)
    from db.seed import seed_demo_data
    await seed_demo_data()

    from agent.core import run_agent
    print("User says: 'Dapat 2 tan tomato dari Pak Ali, RM2.60 sekilo'\n")
    result = await run_agent(
        user_id=1,
        input_text="Dapat 2 tan tomato dari Pak Ali, RM2.60 sekilo",
        input_type="text"
    )
    print("Bot response:")
    print(result["text"])
    assert "tomato" in result["text"].lower() or "2000" in result["text"] or "2,000" in result["text"]

    print("\n✅ Scenario 2 PASSED")

if __name__ == "__main__":
    asyncio.run(run())
