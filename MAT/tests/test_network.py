"""
Test network connectivity to RAGFlow server
"""

import asyncio
import aiohttp
import time
from MAT.config_loader import get_config

async def test_network():
    config = get_config()
    ragflow_config = config.get_ragflow_config()

    endpoint = ragflow_config.get('endpoint')
    api_key = ragflow_config.get('api_key')
    dataset_id = ragflow_config.get('dataset_id')

    print(f"\n{'='*80}")
    print("Network Connectivity Test to RAGFlow")
    print(f"{'='*80}")
    print(f"Target: {endpoint}")
    print(f"{'='*80}\n")

    # Simple payload
    payload = {
        "question": "test",
        "dataset_ids": [dataset_id],
        "top_k": 1
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("Sending test request...")
    start = time.time()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                elapsed = time.time() - start
                print(f"✅ Response received in {elapsed:.2f} seconds")
                print(f"Status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    print(f"Success: {data.get('code') == 0}")
                else:
                    text = await response.text()
                    print(f"Error: {text[:200]}")

    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"❌ Timeout after {elapsed:.2f} seconds")
        print("Network issue: Request did not complete within 10 seconds")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Error after {elapsed:.2f} seconds: {e}")

if __name__ == "__main__":
    asyncio.run(test_network())
