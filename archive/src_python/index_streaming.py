#!/usr/bin/env python3
import asyncio
import sys
import os
from .config import validate_config
from .models.index import create_models
from .models.streaming import call_models_in_parallel_with_streaming
from .conversation import ConversationManager


async def ask_question(prompt: str) -> str:
    """Async input prompt"""
    return await asyncio.get_event_loop().run_in_executor(None, input, prompt)


MODEL_COLORS = {
    'Anthropic': '\033[34m',    # Blue
    'OpenAI': '\033[32m',       # Green
    'Gemini': '\033[35m',       # Magenta
    'reset': '\033[0m'
}


def print_chunk(model: str, chunk: str):
    """Print colored chunk from model"""
    color = MODEL_COLORS.get(model, MODEL_COLORS['reset'])
    sys.stdout.write(f"{color}[{model}]{MODEL_COLORS['reset']} {chunk}")
    sys.stdout.flush()


async def main():
    print('Multi-Model AI Conversation System (Streaming)')
    print('=============================================\n')
    
    try:
        validate_config()
    except ValueError as e:
        print(f'Configuration error: {e}')
        sys.exit(1)
    
    models = create_models()
    conversation = ConversationManager()
    
    try:
        await conversation.load()
    except Exception:
        print('Starting new conversation\n')
    
    print('Commands:')
    print('  - Type your prompt and press Enter to send to all models')
    print('  - Type "assess" to have models analyze the previous responses')
    print('  - Type "exit" to quit and save the conversation\n')
    
    while True:
        try:
            user_input = await ask_question('\n> ')
            
            if user_input.lower() == 'exit':
                await conversation.save()
                print('\nConversation saved. Goodbye!')
                break

            # Handle file input with @ prefix
            if user_input.startswith('@'):
                file_path = user_input[1:].strip()
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            file_content = f.read()
                        # Join all lines into a single paragraph, removing extra whitespace
                        user_input = ' '.join(line.strip() for line in file_content.splitlines() if line.strip())
                        print(f'\nLoaded content from {file_path} as single paragraph')
                    except Exception as e:
                        print(f'Error reading file {file_path}: {e}')
                        continue
                else:
                    print(f'File not found: {file_path}')
                    continue

            if user_input.lower() == 'assess':
                last_responses = conversation.get_last_responses()
                if not last_responses:
                    print('No previous responses to assess.')
                    continue
                
                last_round = conversation.conversation['rounds'][-1]
                assessment_prompt = conversation.format_assessment_prompt(
                    last_round['userPrompt'],
                    last_responses
                )
                
                print('\nSending assessment request to all models...\n')
                
                assessment_messages = [{
                    'role': 'user',
                    'content': assessment_prompt
                }]
                
                responses = await call_models_in_parallel_with_streaming(
                    models,
                    assessment_messages,
                    lambda model, chunk: print_chunk(model, chunk) if model != '_complete_' else None
                )
                
                print('\n\n--- Assessment Complete ---\n')
                
                conversation.add_round(assessment_prompt, responses, True)
                await conversation.save()
                continue
            
            print('\nStreaming responses from all models...\n')
            
            messages = conversation.get_messages()
            messages.append({'role': 'user', 'content': user_input})
            
            responses = await call_models_in_parallel_with_streaming(
                models,
                messages,
                lambda model, chunk: print_chunk(model, chunk) if model != '_complete_' else None
            )
            
            print('\n\n--- Responses Complete ---\n')
            
            for model, response in responses.items():
                if response.get('usage') and response['usage'].get('total_tokens'):
                    print(f'{model} tokens: {response["usage"]["total_tokens"]}')
            
            conversation.add_round(user_input, responses)
            await conversation.save()
            
        except KeyboardInterrupt:
            print('\n\nReceived interrupt signal. Saving conversation...')
            await conversation.save()
            break
        except Exception as e:
            print(f'\nError: {e}')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Fatal error: {e}')
        sys.exit(1)