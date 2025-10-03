#!/usr/bin/env python3
import asyncio
from src_python.models.index import create_models, call_models_in_parallel
from src_python.conversation import ConversationManager
from src_python.config import validate_config

async def test_html_generation():
    """Test script to verify automatic HTML generation"""
    print('Testing automatic HTML generation...\n')

    try:
        validate_config()
    except ValueError as e:
        print(f'Configuration error: {e}')
        return

    models = create_models()
    conversation = ConversationManager('data/conversations/test_conversation.json')

    # Add a test conversation round
    test_prompt = "What is the capital of France?"
    messages = [{'role': 'user', 'content': test_prompt}]

    print(f'Sending test prompt: "{test_prompt}"\n')

    responses = await call_models_in_parallel(models, messages)

    # Display responses
    for model, response in responses.items():
        print(f'{model}: {response.get("content", response.get("error", "No response"))[:100]}...')

    # Add round to conversation and save (which should trigger HTML generation)
    conversation.add_round(test_prompt, responses)
    await conversation.save()

    print('\n✅ Test completed. Check public/comparisons/ directory for HTML files.')

if __name__ == '__main__':
    asyncio.run(test_html_generation())