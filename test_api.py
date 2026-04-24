"""
test_api.py — Standalone ILMU API test. Run this to verify your key works.
Usage: python test_api.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from same folder as this script
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

api_key = os.getenv("ILMU_API_KEY", "")
api_url = os.getenv("ILMU_API_URL", "https://api.ilmu.ai/v1")
model   = os.getenv("MODEL_SMART", "ilmu-glm-5.1")

print(f"📂 .env path : {env_path}")
print(f"🔑 Key loaded: {'YES — ' + api_key[:16] + '...' if api_key else 'NO — EMPTY!'}")
print(f"🌐 API URL   : {api_url}")
print(f"🤖 Model     : {model}")
print()

if not api_key:
    print("❌ ILMU_API_KEY is empty. Check your .env file.")
    exit(1)

from openai import AsyncOpenAI
import asyncio

async def test():
    client = AsyncOpenAI(api_key=api_key, base_url=api_url)

    print("📡 Sending test message to ILMU API...")
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello in one sentence."}],
            max_tokens=50,
        )
        reply = response.choices[0].message.content
        print(f"✅ API works! Response: {reply}")
    except Exception as e:
        print(f"❌ API call failed: {e}")

asyncio.run(test())
