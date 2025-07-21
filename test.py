#!/usr/bin/env python3
import asyncio
import sys
from src_python.config import validate_config
from src_python.models.index import create_models, call_models_in_parallel


async def test():
    print('Testing the multi-model system...\n')
    
    try:
        validate_config()
        print('✓ Configuration validated')
    except ValueError as e:
        print(f'Configuration error: {e}')
        sys.exit(1)
    
    models = create_models()
    print('✓ Models created\n')
    
    test_prompt = 'What is 2+2?'
    print(f'Sending test prompt: "{test_prompt}"\n')
    
    messages = [{'role': 'user', 'content': test_prompt}]
    
    responses = await call_models_in_parallel(models, messages)
    
    for model, response in responses.items():
        print(f'\n=== {model} Response ===')
        if 'error' in response:
            print(f'Error: {response["error"]}')
        else:
            print(response['content'])
            if response.get('usage') and response['usage'].get('total_tokens'):
                print(f'\nTokens: {response["usage"]["total_tokens"]}')


if __name__ == '__main__':
    asyncio.run(test())