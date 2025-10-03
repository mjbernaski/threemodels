#!/usr/bin/env python3
import asyncio
import sys
from .config import validate_config
from .models.index import create_models, call_models_in_parallel
from .conversation import ConversationManager


async def main():
    print('Multi-Model AI System - Simple Test')
    print('===================================\n')
    
    try:
        validate_config()
    except ValueError as e:
        print(f'Configuration error: {e}')
        sys.exit(1)
    
    models = create_models()
    conversation = ConversationManager('test-conversation.json')
    
    # Test with a simple prompt
    prompt = 'Compare the number systems used in ancient Rome and ancient Egypt.'
    print(f'Prompt: {prompt}\n')
    print('Sending to all models...\n')
    
    messages = [{'role': 'user', 'content': prompt}]
    responses = await call_models_in_parallel(models, messages)
    
    for model, response in responses.items():
        print(f'\n=== {model} Response ===')
        if 'error' in response:
            print(f'Error: {response["error"]}')
        else:
            print(response['content'])
            if response.get('usage') and response['usage'].get('total_tokens'):
                print(f'\nTokens: {response["usage"]["total_tokens"]}')
    
    # Save the conversation
    conversation.add_round(prompt, responses)
    await conversation.save()
    print('\n\nConversation saved to test-conversation.json')
    
    # Test assessment
    print('\n\n--- Running Assessment ---\n')
    
    assessment_prompt = conversation.format_assessment_prompt(prompt, responses)
    assessment_messages = [{'role': 'user', 'content': assessment_prompt}]
    
    assessment_responses = await call_models_in_parallel(models, assessment_messages)
    
    for model, response in assessment_responses.items():
        print(f'\n=== {model} Assessment ===')
        if 'error' in response:
            print(f'Error: {response["error"]}')
        else:
            print(response['content'][:500] + '...')
    
    conversation.add_round(assessment_prompt, assessment_responses, True)
    await conversation.save()


if __name__ == '__main__':
    asyncio.run(main())