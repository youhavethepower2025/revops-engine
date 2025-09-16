#!/usr/bin/env python3
"""
Local testing script for Amber Brain
Tests webhook endpoints with sample data
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Test data
TEST_PHONE = "+14155551234"
TEST_CALL_ID = f"test_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

async def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")

async def test_call_start():
    """Test call start webhook"""
    print("\nTesting call start webhook...")
    payload = {
        "call_id": TEST_CALL_ID,
        "from_number": TEST_PHONE,
        "to_number": "+18005551234",
        "agent_id": "test_agent"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/webhooks/retell/call-started",
            json=payload
        )

        if response.status_code == 200:
            print("✅ Call start processed")
            result = response.json()
            print(f"   Caller Type: {result.get('context', {}).get('caller_type')}")
            print(f"   Greeting: {result.get('custom_variables', {}).get('greeting')}")
            return True
        else:
            print(f"❌ Call start failed: {response.status_code}")
            return False

async def test_transcript_update():
    """Test transcript update"""
    print("\nTesting transcript update...")
    payload = {
        "call_id": TEST_CALL_ID,
        "transcript": "Hello, I'm calling about my recent order. I haven't received it yet and I'm getting frustrated.",
        "speaker": "customer"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/webhooks/retell/transcript-update",
            json=payload
        )

        if response.status_code == 200:
            print("✅ Transcript processed")
            result = response.json()
            insights = result.get('insights', {})
            print(f"   Sentiment: {insights.get('sentiment')}")
            print(f"   Urgency: {insights.get('urgency')}")
        else:
            print(f"❌ Transcript update failed: {response.status_code}")

async def test_tool_call():
    """Test tool call"""
    print("\nTesting tool call (check availability)...")
    payload = {
        "call_id": TEST_CALL_ID,
        "tool_name": "check_availability",
        "parameters": {
            "date_range": "next_week"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/webhooks/retell/tool-call",
            json=payload
        )

        if response.status_code == 200:
            print("✅ Tool call processed")
            result = response.json()
            print(f"   Available slots: {len(result.get('result', {}).get('available_slots', []))}")
        else:
            print(f"❌ Tool call failed: {response.status_code}")

async def test_call_end():
    """Test call end webhook"""
    print("\nTesting call end webhook...")

    transcript = """
    Customer: Hello, I'm calling about scheduling an appointment.
    Amber: Hi! I'd be happy to help you schedule an appointment. What type of appointment are you looking for?
    Customer: I need a consultation for next week.
    Amber: I have a few slots available next week. Tuesday at 2 PM or Thursday at 10 AM. Which works better for you?
    Customer: Tuesday at 2 PM works great.
    Amber: Perfect! I've scheduled your consultation for Tuesday at 2 PM. You'll receive a confirmation email shortly.
    Customer: Thank you!
    Amber: You're welcome! Have a great day!
    """

    payload = {
        "call_id": TEST_CALL_ID,
        "duration_seconds": 180,
        "transcript": transcript,
        "end_reason": "completed"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/webhooks/retell/call-ended",
            json=payload
        )

        if response.status_code == 200:
            print("✅ Call end processed")
            result = response.json()
            summary = result.get('summary', {})
            print(f"   Summary generated: {bool(summary)}")
            if summary:
                print(f"   Executive Summary: {summary.get('executive_summary', 'N/A')[:100]}...")
        else:
            print(f"❌ Call end failed: {response.status_code}")

async def test_get_calls():
    """Test getting call list"""
    print("\nTesting call list endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/calls?limit=10")

        if response.status_code == 200:
            print("✅ Call list retrieved")
            result = response.json()
            print(f"   Total calls: {result.get('total', 0)}")
        else:
            print(f"❌ Call list failed: {response.status_code}")

async def run_all_tests():
    """Run all tests in sequence"""
    print("=" * 50)
    print("🧪 Starting Amber Brain Local Tests")
    print("=" * 50)

    await test_health()

    # Only continue if health check passes
    call_started = await test_call_start()

    if call_started:
        await asyncio.sleep(1)  # Small delay between tests
        await test_transcript_update()
        await asyncio.sleep(1)
        await test_tool_call()
        await asyncio.sleep(1)
        await test_call_end()

    await test_get_calls()

    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_all_tests())