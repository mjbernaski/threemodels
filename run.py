#!/usr/bin/env python3
import asyncio
import signal
import sys
from src_python.config import validate_config
from src_python.models.index import create_models, call_models_in_parallel
from src_python.conversation import ConversationManager


async def ask_question(prompt: str) -> str:
    """Async input prompt"""
    return await asyncio.get_event_loop().run_in_executor(None, input, prompt)


async def main():
    print('\033[2J\033[H')  # Clear screen
    print('Multi-Model AI Conversation System')
    print('==================================\n')
    
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
    
    running = True
    
    def signal_handler(signum, frame):
        nonlocal running
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    while running:
        try:
            user_input = await ask_question('\n> ')
            
            if not user_input or user_input.strip() == '':
                continue
            
            if user_input.lower() == 'exit':
                await conversation.save()
                print('\nConversation saved. Goodbye!')
                break
            
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
                
                responses = await call_models_in_parallel(models, assessment_messages)
                
                for model, response in responses.items():
                    print(f'\n=== {model} Assessment ===')
                    if 'error' in response:
                        print(f'Error: {response["error"]}')
                    else:
                        print(response['content'])
                
                conversation.add_round(assessment_prompt, responses, True)
                await conversation.save()
                continue
            
            print('\nSending to all models...\n')
            
            messages = conversation.get_messages()
            messages.append({'role': 'user', 'content': user_input})
            
            responses = await call_models_in_parallel(models, messages)
            
            for model, response in responses.items():
                print(f'\n=== {model} Response ===')
                if 'error' in response:
                    print(f'Error: {response["error"]}')
                else:
                    print(response['content'])
                    if response.get('usage') and response['usage'].get('total_tokens'):
                        print(f'\nTokens: {response["usage"]["total_tokens"]}')
            
            conversation.add_round(user_input, responses)
            await conversation.save()
            
        except KeyboardInterrupt:
            print('\n\nReceived interrupt signal. Saving conversation...')
            await conversation.save()
            break
        except Exception as e:
            print(f'\nError: {e}')


async def shutdown_handler():
    """Handle graceful shutdown"""
    print('\n\nReceived interrupt signal. Saving conversation...')
    try:
        conversation = ConversationManager()
        await conversation.save()
    except Exception:
        pass
    sys.exit(0)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(shutdown_handler())
    except Exception as e:
        print(f'Fatal error: {e}')
        sys.exit(1)