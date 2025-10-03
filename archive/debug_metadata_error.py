#!/usr/bin/env python3
import asyncio
import sys
from src_python.models.index import create_models, call_models_in_parallel
from src_python.conversation import ConversationManager
from src_python.config import validate_config

async def debug_metadata_error():
    """Debug script to reproduce and catch the metadata error"""
    print('🔍 DEBUG: Starting metadata error debugging session...\n')

    try:
        validate_config()
    except ValueError as e:
        print(f'Configuration error: {e}')
        return

    models = create_models()
    conversation = ConversationManager('debug_conversation.json')

    # Try multiple different scenarios that might trigger the error
    test_cases = [
        "Hello",
        "Write a haiku",
        "Explain quantum physics",
        "",  # Empty string
        "a" * 1000,  # Very long string
    ]

    for i, test_prompt in enumerate(test_cases):
        print(f'\n🧪 Test case {i+1}: "{test_prompt[:50]}{"..." if len(test_prompt) > 50 else ""}"')

        try:
            messages = [{'role': 'user', 'content': test_prompt}] if test_prompt else []

            # Test with callback
            def on_response(model_name, content, duration):
                print(f'✅ {model_name} callback received')

            responses = await call_models_in_parallel(models, messages, max_retries=1, on_response=on_response)

            for model, response in responses.items():
                if 'error' in response:
                    error_msg = response['error']
                    if 'metadata' in error_msg.lower():
                        print(f'🚨 METADATA ERROR FOUND in {model}: {error_msg}')
                    else:
                        print(f'❌ {model}: {error_msg[:100]}...')
                else:
                    print(f'✅ {model}: Success')

            conversation.add_round(test_prompt, responses)
            await conversation.save()

        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f'🚨 EXCEPTION in test case {i+1}: {error_msg}')
            if 'metadata' in error_msg.lower():
                print(f'🚨 METADATA ERROR FOUND IN EXCEPTION: {error_msg}')
                print(f'🚨 FULL TRACEBACK: {traceback.format_exc()}')

    # Test individual models
    print('\n🔬 Testing individual models...')
    for model in models:
        try:
            print(f'\n--- Testing {model.name} individually ---')
            result = await model.send_message([{'role': 'user', 'content': 'test'}])
            if 'error' in result:
                print(f'❌ {model.name}: {result["error"][:100]}...')
            else:
                print(f'✅ {model.name}: Success')

            # Test with callback
            def test_callback(model_name, chunk):
                pass

            result_streaming = await model.send_message([{'role': 'user', 'content': 'test'}], on_chunk=test_callback)
            if 'error' in result_streaming:
                print(f'❌ {model.name} streaming: {result_streaming["error"][:100]}...')
            else:
                print(f'✅ {model.name} streaming: Success')

        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f'🚨 {model.name} EXCEPTION: {error_msg}')
            if 'metadata' in error_msg.lower():
                print(f'🚨 METADATA ERROR in {model.name}: {error_msg}')
                print(f'🚨 TRACEBACK: {traceback.format_exc()}')

    print('\n✅ Debug session completed!')

if __name__ == '__main__':
    try:
        asyncio.run(debug_metadata_error())
    except Exception as e:
        import traceback
        print(f'🚨 TOP-LEVEL EXCEPTION: {str(e)}')
        print(f'🚨 TRACEBACK: {traceback.format_exc()}')