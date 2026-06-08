#!/usr/bin/env python3
"""Debug script to test API and see detailed responses."""

import httpx
import json
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test billing ticket
        test_ticket = {
            "ticket_id": "TKT-BILL-001",
            "title": "Payment failed on subscription renewal",
            "description": "My credit card payment did not go through for the monthly subscription"
        }
        
        print(f"\nTesting Classification for: {test_ticket['title']}")
        print(f"Description: {test_ticket['description']}")
        
        response = await client.post("http://127.0.0.1:8000/api/classify", json=test_ticket)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Status: {response.status_code}")
            print(f"Category: {result.get('category')}")
            print(f"Subcategory: {result.get('subcategory')}")
            print(f"Priority: {result.get('priority')}")
            print(f"Confidence: {result.get('confidence')}")
            print(f"Reasoning: {result.get('reasoning')}")
            print(f"\nFull Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"✗ Status: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_api())
