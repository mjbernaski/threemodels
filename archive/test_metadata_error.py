#!/usr/bin/env python3
import asyncio
from src_python.models.index import create_models, call_models_in_parallel
from src_python.conversation import ConversationManager
from src_python.config import validate_config

async def test_metadata_error():
    """Test script to reproduce metadata error"""
    print('Testing metadata error...\n')

    try:
        validate_config()
    except ValueError as e:
        print(f'Configuration error: {e}')
        return

    models = create_models()
    conversation = ConversationManager()

    # Test with a simple prompt
    test_prompt = "Hello, please respond with a simple greeting."
    messages = [{'role': 'user', 'content': test_prompt}]

    print(f'Sending test prompt: "{test_prompt}"\n')

    try:
        responses = await call_models_in_parallel(models, messages)

        for model, response in responses.items():
            print(f'\n=== {model} Response ===')
            if 'error' in response:
                print(f'Error: {response["error"]}')
            else:
                print(f'Content: {response.get("content", "No content")}')
                if response.get('usage'):
                    print(f'Usage: {response["usage"]}')
    except Exception as e:
        print(f'Exception during API call: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_metadata_error())