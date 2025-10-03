#!/usr/bin/env python3
import asyncio
from src_python.models.index import create_models, call_models_in_parallel
from src_python.conversation import ConversationManager
from src_python.config import validate_config

async def test_metadata_fix():
    """Quick test to verify metadata errors are fixed"""
    print('Testing metadata error fix...\n')

    try:
        validate_config()
    except ValueError as e:
        print(f'Configuration error: {e}')
        return

    models = create_models()
    conversation = ConversationManager('test_metadata_fix.json')

    # Simple test
    test_prompt = "Say hello"
    messages = [{'role': 'user', 'content': test_prompt}]

    print(f'Testing with prompt: "{test_prompt}"')

    # Test both streaming and non-streaming modes
    print('\n--- Testing NON-streaming mode ---')
    responses = await call_models_in_parallel(models, messages, max_retries=2)

    for model, response in responses.items():
        if 'error' in response:
            print(f'❌ {model}: {response["error"][:100]}...')
        else:
            print(f'✅ {model}: Success ({len(response.get("content", ""))} chars)')

    # Test with streaming callback
    print('\n--- Testing STREAMING mode ---')
    def on_chunk(model_name, chunk):
        pass  # Just consume chunks

    # Test individual models with streaming
    for model in models:
        try:
            result = await model.send_message(messages, on_chunk=on_chunk)
            if 'error' in result:
                print(f'❌ {model.name} streaming: {result["error"][:100]}...')
            else:
                print(f'✅ {model.name} streaming: Success ({len(result.get("content", ""))} chars)')
        except Exception as e:
            print(f'❌ {model.name} streaming exception: {str(e)[:100]}...')

    conversation.add_round(test_prompt, responses)
    await conversation.save()

    print('\n✅ Metadata error test completed!')

if __name__ == '__main__':
    asyncio.run(test_metadata_fix())