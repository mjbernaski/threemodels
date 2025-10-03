#!/usr/bin/env python3
import asyncio
from src_python.models.index import create_models, call_models_in_parallel
from src_python.conversation import ConversationManager
from src_python.config import validate_config

async def test_retry_and_timing():
    """Test retry logic and timing display"""
    print('Testing retry logic and timing features...\n')

    try:
        validate_config()
    except ValueError as e:
        print(f'Configuration error: {e}')
        return

    models = create_models()
    conversation = ConversationManager('test_retry_conversation.json')

    test_prompt = "Write a short haiku about technology."
    messages = [{'role': 'user', 'content': test_prompt}]

    print(f'Sending test prompt: "{test_prompt}"\n')
    print('Watching for real-time responses...\n')

    def on_response_received(model_name: str, content: str, duration: float):
        """Callback to show responses as they arrive"""
        print(f'\n✅ {model_name} responded in {duration:.2f}s')
        print(f'=== {model_name} Response ===')
        print(content[:200] + ('...' if len(content) > 200 else ''))
        print(f'\n⏱️  Response time: {duration:.2f}s')
        print('─' * 80)

    responses = await call_models_in_parallel(
        models,
        messages,
        max_retries=3,
        on_response=on_response_received
    )

    # Show final summary
    print('\n📊 Final Summary:')
    for model, response in responses.items():
        timing_info = f"⏱️ {response.get('response_time', 0):.2f}s"
        retry_info = f"🔄 {response.get('attempts', 1)} attempt(s)"

        if 'error' in response:
            print(f'❌ {model}: Error - {response["error"][:50]}... | {timing_info} | {retry_info}')
        else:
            tokens = response.get('usage', {}).get('total_tokens', 'N/A')
            print(f'✅ {model}: Success | {timing_info} | {retry_info} | 🪙 {tokens} tokens')

    # Add to conversation and save (triggers HTML generation)
    conversation.add_round(test_prompt, responses)
    await conversation.save()

    print('\n✅ Test completed with retry and timing features!')

if __name__ == '__main__':
    asyncio.run(test_retry_and_timing())