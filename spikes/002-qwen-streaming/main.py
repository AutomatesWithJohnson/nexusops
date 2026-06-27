"""Spike 002: Test Qwen streaming responses."""

import asyncio
import os
import sys
import time

from openai import AsyncOpenAI

API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

# Try loading from .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
if not API_KEY and os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.startswith("DASHSCOPE_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip()
                break


async def test_streaming():
    """Test streaming responses from Qwen."""
    print("="*60)
    print("SPIKE 002: Qwen Streaming Responses")
    print("="*60)

    client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)

    print("\nStreaming response from qwen-plus:")
    print("-" * 40)

    full_text = ""
    token_count = 0
    start = time.time()

    stream = await client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a helpful business assistant. Write a brief professional email (3-4 sentences) responding to a customer inquiry about pricing."},
            {"role": "user", "content": "A customer named Sarah from Acme Corp asked about Enterprise plan pricing for 50 users."}
        ],
        stream=True,
        max_tokens=200,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            full_text += text
            token_count += 1
            print(text, end="", flush=True)

    elapsed = (time.time() - start) * 1000

    print(f"\n\n{'='*60}")
    print(f"VERDICT")
    print(f"{'='*60}")
    print(f"  Total chunks streamed: {token_count}")
    print(f"  Total characters: {len(full_text)}")
    print(f"  Elapsed time: {elapsed:.0f}ms")
    print(f"  Chunks/sec: {token_count / (elapsed/1000):.1f}")
    print(f"  RESULT: {'PASS' if token_count > 10 else 'FAIL'}")

    return token_count > 10


if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: No DASHSCOPE_API_KEY found")
        sys.exit(1)

    asyncio.run(test_streaming())
