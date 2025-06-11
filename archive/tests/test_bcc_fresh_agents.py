"""
Test BCC Integration with Fresh Agents
Test the Control Center chat with Solomon and David fresh agents
"""

import asyncio
import json
from datetime import datetime

import httpx


async def test_bcc_chat():
    """Test BCC chat integration with fresh agents"""

    print("🎯 Testing BCC Integration with Fresh Agents")
    print("=" * 60)

    base_url = "http://localhost:8888"

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Test 1: Chat with Fresh Solomon
        print("🧠 Test 1: Chat with Fresh Solomon")
        print("-" * 40)

        solomon_message = "Hello Solomon! I need a strategic analysis of our current position and next steps for growth."

        try:
            response = await client.post(
                f"{base_url}/api/chat",
                json={"agent": "solomon", "message": solomon_message},
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: {result['status']}")
                print(f"🤖 Agent: {result['agent']}")
                print(f"📝 Response Preview:")
                response_lines = result["response"].split("\n")
                for i, line in enumerate(response_lines[:8]):
                    print(f"  {line}")
                if len(response_lines) > 8:
                    print(f"  ... (+{len(response_lines)-8} more lines)")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Request failed: {e}")

        print("\n" + "=" * 60)

        # Test 2: Chat with Fresh David
        print("👨‍💼 Test 2: Chat with Fresh David")
        print("-" * 40)

        david_message = "David, as CEO I need your executive decision on expanding our team and investing in infrastructure for scaling."

        try:
            response = await client.post(
                f"{base_url}/api/chat",
                json={"agent": "david", "message": david_message},
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: {result['status']}")
                print(f"🤖 Agent: {result['agent']}")
                print(f"📝 Response Preview:")
                response_lines = result["response"].split("\n")
                for i, line in enumerate(response_lines[:8]):
                    print(f"  {line}")
                if len(response_lines) > 8:
                    print(f"  ... (+{len(response_lines)-8} more lines)")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Request failed: {e}")

        print("\n" + "=" * 60)

        # Test 3: Complex Multi-Agent Request
        print("🔄 Test 3: Complex Multi-Agent Request via Adam")
        print("-" * 40)

        complex_message = "I need a comprehensive strategy for scaling BoarderframeOS to 120+ agents and $15K monthly revenue, including both strategic analysis and executive approval."

        try:
            response = await client.post(
                f"{base_url}/api/chat",
                json={"agent": "adam", "message": complex_message},
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: {result['status']}")
                print(f"🤖 Agent: {result['agent']}")
                print(f"📝 Response Preview:")
                response_lines = result["response"].split("\n")
                for i, line in enumerate(response_lines[:10]):
                    print(f"  {line}")
                if len(response_lines) > 10:
                    print(f"  ... (+{len(response_lines)-10} more lines)")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Request failed: {e}")

        print("\n" + "=" * 60)

        # Test 4: Check BCC Health
        print("📊 Test 4: BCC Health Check")
        print("-" * 40)

        try:
            response = await client.get(f"{base_url}/api/health")

            if response.status_code == 200:
                health = response.json()
                print(f"✅ BCC Status: {health.get('status', 'unknown')}")
                print(f"🔄 Last Refresh: {health.get('last_refresh', 'unknown')}")
                print(
                    f"📊 System Metrics Available: {len(health.get('system_metrics', {}))}"
                )
                print(f"🤖 Agent Status Available: {'agents' in health}")
            else:
                print(f"❌ Health check failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Health check failed: {e}")

    print("\n✅ BCC Integration Testing Complete!")


async def main():
    """Run the BCC integration tests"""

    try:
        await test_bcc_chat()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
