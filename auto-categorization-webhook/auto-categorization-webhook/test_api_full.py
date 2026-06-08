#!/usr/bin/env python3
"""
Full API test suite for Auto-Categorization Webhook
"""
import httpx
import json
import asyncio

async def test_classification():
    async with httpx.AsyncClient(timeout=30) as client:
        print('=' * 80)
        print('AUTO-CATEGORIZATION WEBHOOK - FULL API TEST')
        print('=' * 80)
        
        # Test 1: Health Check
        print('\n[TEST 1] Health Check: GET /api/health')
        print('-' * 80)
        try:
            response = await client.get('http://127.0.0.1:8000/api/health')
            print(f'Status: {response.status_code} OK')
            data = response.json()
            for key, value in data.items():
                print(f'  {key}: {value}')
        except Exception as e:
            print(f'ERROR: {e}')
        
        # Test 2: Classification - Authentication Issue
        print('\n[TEST 2] Classification: Authentication Issue')
        print('-' * 80)
        ticket1 = {
            'ticket_id': 'TKT-AUTH-001',
            'title': 'Unable to login to portal',
            'description': 'User cannot access the system after password reset attempt'
        }
        print(f'Request: {json.dumps(ticket1, indent=2)}')
        try:
            response = await client.post('http://127.0.0.1:8000/api/classify', json=ticket1, timeout=30)
            print(f'Status: {response.status_code} OK')
            data = response.json()
            print('Response:')
            print(f'  Category: {data.get("category")}')
            print(f'  Subcategory: {data.get("subcategory")}')
            print(f'  Priority: {data.get("priority")}')
            print(f'  Confidence: {data.get("confidence"):.2f}')
            print(f'  Model: {data.get("model_used")}')
            print(f'  Processing Time: {data.get("processing_time_ms"):.2f}ms')
        except Exception as e:
            print(f'ERROR: {type(e).__name__}: {e}')
        
        # Test 3: Classification - Billing Issue
        print('\n[TEST 3] Classification: Billing Issue')
        print('-' * 80)
        ticket2 = {
            'ticket_id': 'TKT-BILL-001',
            'title': 'Payment failed on subscription renewal',
            'description': 'My credit card payment did not go through for the monthly subscription'
        }
        print(f'Request: {json.dumps(ticket2, indent=2)}')
        try:
            response = await client.post('http://127.0.0.1:8000/api/classify', json=ticket2, timeout=30)
            print(f'Status: {response.status_code} OK')
            data = response.json()
            print('Response:')
            print(f'  Category: {data.get("category")}')
            print(f'  Subcategory: {data.get("subcategory")}')
            print(f'  Priority: {data.get("priority")}')
            print(f'  Confidence: {data.get("confidence"):.2f}')
            print(f'  Model: {data.get("model_used")}')
        except Exception as e:
            print(f'ERROR: {type(e).__name__}: {e}')
        
        # Test 4: Classification - Technical Issue
        print('\n[TEST 4] Classification: Technical Issue')
        print('-' * 80)
        ticket3 = {
            'ticket_id': 'TKT-TECH-001',
            'title': 'Application crashes on startup',
            'description': 'The app crashes immediately after launching with an error code'
        }
        print(f'Request: {json.dumps(ticket3, indent=2)}')
        try:
            response = await client.post('http://127.0.0.1:8000/api/classify', json=ticket3, timeout=30)
            print(f'Status: {response.status_code} OK')
            data = response.json()
            print('Response:')
            print(f'  Category: {data.get("category")}')
            print(f'  Subcategory: {data.get("subcategory")}')
            print(f'  Priority: {data.get("priority")}')
            print(f'  Confidence: {data.get("confidence"):.2f}')
            print(f'  Model: {data.get("model_used")}')
        except Exception as e:
            print(f'ERROR: {type(e).__name__}: {e}')
        
        # Test 5: Get Logs
        print('\n[TEST 5] Get Logs: GET /api/logs')
        print('-' * 80)
        try:
            response = await client.get('http://127.0.0.1:8000/api/logs')
            print(f'Status: {response.status_code} OK')
            data = response.json()
            print(f'  Total Tickets: {data.get("total_tickets")}')
            print(f'  Average Confidence: {data.get("average_confidence"):.3f}')
            print(f'  Category Distribution: {data.get("category_distribution")}')
            print(f'  Priority Distribution: {data.get("priority_distribution")}')
        except Exception as e:
            print(f'ERROR: {type(e).__name__}: {e}')
        
        print('\n' + '=' * 80)
        print('ALL TESTS COMPLETE')
        print('=' * 80)

if __name__ == '__main__':
    asyncio.run(test_classification())
