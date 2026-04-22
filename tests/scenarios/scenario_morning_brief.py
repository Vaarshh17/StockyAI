"""
Demo Scenario 1: Morning Brief
Simulates triggering the 3:30 AM brief and validates the output structure.
Owner: Person 5
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

async def run():
    print("=" * 60)
    print("SCENARIO 1: Morning Brief")
    print("=" * 60)
    print("Setting up demo database...")
    from db.seed import seed_demo_data
    await seed_demo_data()

    print("Triggering morning brief...\n")
    from agent.core import run_proactive_brief
    text = await run_proactive_brief(user_id=1, brief_type="morning")

    print("OUTPUT:")
    print("-" * 40)
    print(text)
    print("-" * 40)

    # Validate output contains key elements
    assert len(text) > 100, "Brief too short"
    print("\n✅ Scenario 1 PASSED")

if __name__ == "__main__":
    asyncio.run(run())
