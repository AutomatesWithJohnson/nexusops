"""Spike 001: Test Qwen function calling via DashScope API.

Validates that Qwen models support OpenAI-compatible tool calling.
"""

import asyncio
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openai import AsyncOpenAI

# Load API key
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

if not API_KEY:
    # Try loading from .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("DASHSCOPE_API_KEY="):
                    API_KEY = line.split("=", 1)[1].strip()
                    break

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country, e.g. 'Lagos, Nigeria'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_crm",
            "description": "Search customer records in the CRM database",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (name, email, company)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }
]

MOCK_RESULTS = {
    "get_weather": {"temperature": 32, "condition": "Sunny", "humidity": 65},
    "search_crm": {"results": [
        {"name": "Acme Corp", "email": "contact@acme.com", "tier": "gold"},
        {"name": "Acme Solutions", "email": "hello@acmesol.com", "tier": "silver"},
    ]}
}


async def test_basic_chat():
    """Test 1: Basic chat without tools."""
    print("\n" + "="*60)
    print("TEST 1: Basic Chat (no tools)")
    print("="*60)

    client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
    response = await client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Reply in one sentence."},
            {"role": "user", "content": "What is 2+2?"}
        ],
        max_tokens=100,
    )
    result = response.choices[0].message.content
    print(f"Model: {response.model}")
    print(f"Response: {result}")
    print(f"Tokens: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")
    print(f"RESULT: {'PASS' if result else 'FAIL'}")
    return bool(result)


async def test_function_calling():
    """Test 2: Function calling with tool_use."""
    print("\n" + "="*60)
    print("TEST 2: Function Calling")
    print("="*60)

    client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)

    # Step 1: Ask model to use a tool
    response = await client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a business assistant. Use the provided tools when needed."},
            {"role": "user", "content": "What's the weather like in Lagos today?"}
        ],
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=200,
    )

    choice = response.choices[0]
    print(f"Finish reason: {choice.finish_reason}")

    if choice.message.tool_calls:
        for tc in choice.message.tool_calls:
            print(f"Tool call: {tc.function.name}")
            print(f"Arguments: {tc.function.arguments}")
            args = json.loads(tc.function.arguments)
            result = MOCK_RESULTS.get(tc.function.name, {"error": "unknown"})
            print(f"Mock result: {json.dumps(result)}")

        # Step 2: Send tool result back
        messages = [
            {"role": "system", "content": "You are a business assistant. Use the provided tools when needed."},
            {"role": "user", "content": "What's the weather like in Lagos today?"},
            choice.message.model_dump(),
        ]
        for tc in choice.message.tool_calls:
            result = MOCK_RESULTS.get(tc.function.name, {"error": "unknown"})
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result),
            })

        response2 = await client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            tools=TOOLS,
            max_tokens=200,
        )
        final = response2.choices[0].message.content
        print(f"Final response: {final}")
        print(f"RESULT: {'PASS' if final else 'FAIL'}")
        return bool(final)
    else:
        print("No tool calls made (model responded directly)")
        print(f"Response: {choice.message.content}")
        print("RESULT: PARTIAL (model didn't use tools)")
        return False


async def test_multi_tool():
    """Test 3: Multiple tool calls in sequence."""
    print("\n" + "="*60)
    print("TEST 3: Multi-Tool Sequence")
    print("="*60)

    client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
    response = await client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a business assistant. Use tools to answer questions. Always search CRM first."},
            {"role": "user", "content": "Find Acme Corp in our CRM and tell me the weather at their location."}
        ],
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=300,
    )

    choice = response.choices[0]
    tool_count = len(choice.message.tool_calls) if choice.message.tool_calls else 0
    print(f"Tool calls made: {tool_count}")

    if choice.message.tool_calls:
        for tc in choice.message.tool_calls:
            print(f"  - {tc.function.name}({tc.function.arguments})")

    print(f"RESULT: {'PASS' if tool_count >= 1 else 'FAIL'}")
    return tool_count >= 1


async def main():
    if not API_KEY:
        print("ERROR: No DASHSCOPE_API_KEY found.")
        print("Set it in your .env file or as an environment variable.")
        sys.exit(1)

    print("NexusOps Spike 001: Qwen Function Calling Validation")
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")

    results = {}
    results["basic_chat"] = await test_basic_chat()
    results["function_calling"] = await test_function_calling()
    results["multi_tool"] = await test_multi_tool()

    print("\n" + "="*60)
    print("SPIKE VERDICT")
    print("="*60)
    for test, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test}: {status}")

    if all(results.values()):
        print("\nVERDICT: VALIDATED")
        print("Qwen function calling works with OpenAI-compatible API.")
        print("Safe to proceed with agent framework development.")
    elif any(results.values()):
        print("\nVERDICT: PARTIAL")
        print("Some tests passed. Review failures before proceeding.")
    else:
        print("\nVERDICT: INVALIDATED")
        print("Qwen function calling may need a different approach.")


if __name__ == "__main__":
    asyncio.run(main())
