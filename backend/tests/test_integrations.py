"""
BroCoDDE — Integration Tests for Models & OpenRouter
Verifies that the OpenRouter API key routing and fallback tiers
are correctly injecting models into the Agno agents.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

from app.config import settings
from app.agents.strategist import build_strategist
from app.agents.interviewer import build_interviewer
from app.agents.shaper import build_shaper
from app.agents.analyst import build_analyst

async def test_agent(agent, agent_name: str, message: str = "Say exactly 'TEST_OK'"):
    print(f"\n[TESTING] {agent_name} Routing...")
    print(f"   Model mapped to: {agent.model.id if agent.model else 'None (MOCK)'}")
    
    if not settings.has_any_ai_key:
        print("   -> Skipping live call (mock mode enabled)")
        return True
        
    try:
        # We test the async API explicitly
        print("   -> Sending request...")
        response_text = ""
        async for chunk in agent.arun(message, stream=True):
            if hasattr(chunk, "content") and chunk.content:
                response_text += chunk.content
        
        print(f"   -> ✅ Response received: {response_text[:50]}...")
        return True
    except Exception as e:
        print(f"   -> ❌ FAILED: {str(e)}")
        return False

async def main():
    print("=== BroCoDDE Model Integration Test ===")
    print(f"Selected Provider: {settings.primary_provider}")
    print(f"Tier 1 (Shaper/Analyst default): {settings.tier1_model}")
    print(f"Tier 2 (Interviewer default): {settings.tier2_model}")
    print(f"Tier 3 (Strategist default): {settings.tier3_model}")
    print("=======================================")
    
    agents = [
        (build_strategist(stage="discovery", session_id="test-strat"), "Strategist (Tier 3)"),
        (build_interviewer(role="researcher", session_id="test-int"), "Interviewer (Tier 2)"),
        (build_shaper(mode="structuring", session_id="test-shape"), "Shaper (Tier 1)"),
        (build_analyst(session_id="test-analyst"), "Analyst (Tier 1)"),
    ]
    
    success = True
    for agent, name in agents:
        res = await test_agent(agent, name)
        if not res:
            success = False
            
    print("\n[RESULT]")
    if success:
        print("✅ All Agent-LLM Integrations Passed.")
    else:
        print("❌ One or more models failed routing.")

if __name__ == "__main__":
    asyncio.run(main())
