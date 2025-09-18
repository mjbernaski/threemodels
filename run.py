#!/usr/bin/env python3
import asyncio
import signal
import sys
import os
import subprocess
from src_python.config import validate_config
from src_python.models.index import create_models, call_models_in_parallel
from src_python.conversation import ConversationManager
from conversation_side_by_side import create_side_by_side_html


async def ask_question(prompt: str) -> str:
    """Async input prompt"""
    return await asyncio.get_event_loop().run_in_executor(None, input, prompt)


async def generate_and_open_html(json_file='conversation.json', html_file='conversation_side_by_side.html'):
    """Generate HTML and open in browser"""
    try:
        await asyncio.get_event_loop().run_in_executor(None, create_side_by_side_html, json_file, html_file)
        print(f'\n📄 Side-by-side comparison saved to: {html_file}')

        # Open the HTML file in the default browser
        try:
            subprocess.run(['open', html_file], check=True)
            print('🌐 Opening comparison in browser...')
        except subprocess.CalledProcessError:
            print(f'⚠️  Could not open browser automatically. Open {html_file} manually.')
    except Exception as e:
        print(f'Error generating HTML: {e}')


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
    print('  - Type "reset" to clear conversation and start fresh')
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
                print('\nConversation saved. Generating HTML...')
                await generate_and_open_html()
                print('Goodbye!')
                break

            if user_input.lower() == 'reset':
                conversation = ConversationManager()
                print('\n🔄 Conversation reset. Starting fresh!')
                continue

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

                # Skip if the last round was already an assessment
                if last_round.get('isAssessment', False):
                    print('The last round was already an assessment. Please ask a new question first.')
                    continue

                assessment_prompt = conversation.format_assessment_prompt(
                    last_round['userPrompt'],
                    last_responses
                )
                
                print('\nSending assessment request to all models...\n')
                print(f'📝 Assessment prompt preview: {assessment_prompt[:200]}...')

                assessment_messages = [{
                    'role': 'user',
                    'content': assessment_prompt
                }]

                def on_assessment_response(model_name: str, content: str, duration: float):
                    """Callback for assessment responses"""
                    print(f'\n✅ {model_name} assessment completed in {duration:.2f}s')
                    print(f'=== {model_name} Assessment ===')
                    print(content)
                    print(f'\n⏱️  Response time: {duration:.2f}s')
                    print('─' * 80)

                responses = await call_models_in_parallel(models, assessment_messages, max_retries=3, on_response=on_assessment_response)

                # Show assessment summary
                print('\n📊 Assessment Summary:')
                for model, response in responses.items():
                    timing_info = f"⏱️ {response.get('response_time', 0):.2f}s"
                    retry_info = f"🔄 {response.get('attempts', 1)} attempt(s)"

                    if 'error' in response:
                        print(f'❌ {model}: Error - {response["error"]} | {timing_info} | {retry_info}')
                    else:
                        print(f'✅ {model}: Assessment complete | {timing_info} | {retry_info}')

                conversation.add_round(assessment_prompt, responses, True)
                await conversation.save()
                await generate_and_open_html()
                continue
            
            print('\nSending to all models...\n')

            messages = conversation.get_messages()
            messages.append({'role': 'user', 'content': user_input})

            # Track which models have responded
            completed_models = set()

            def on_response_received(model_name: str, content: str, duration: float):
                """Callback for when a model response is received"""
                completed_models.add(model_name)
                print(f'\n✅ {model_name} responded in {duration:.2f}s')
                print(f'=== {model_name} Response ===')
                print(content)
                print(f'\n⏱️  Response time: {duration:.2f}s')
                print('─' * 80)

            responses = await call_models_in_parallel(models, messages, max_retries=3, on_response=on_response_received)

            # Show final summary with timing and retry info
            print('\n📊 Final Summary:')
            for model, response in responses.items():
                timing_info = f"⏱️ {response.get('response_time', 0):.2f}s"
                retry_info = f"🔄 {response.get('attempts', 1)} attempt(s)"

                if 'error' in response:
                    print(f'❌ {model}: Error - {response["error"]} | {timing_info} | {retry_info}')
                else:
                    tokens = response.get('usage', {}).get('total_tokens', 'N/A')
                    print(f'✅ {model}: Success | {timing_info} | {retry_info} | 🪙 {tokens} tokens')

            conversation.add_round(user_input, responses)
            await conversation.save()
            await generate_and_open_html()
            
        except KeyboardInterrupt:
            print('\n\nReceived interrupt signal. Saving conversation...')
            await conversation.save()
            break
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f'\nError: {error_msg}')

            # Check if this is the mysterious 'metadata' error
            if "'metadata'" in error_msg or "metadata" in error_msg.lower():
                print(f"🚨 FOUND METADATA ERROR IN MAIN: {error_msg}")
                print(f"🚨 FULL TRACEBACK: {traceback.format_exc()}")
            else:
                print(f"🔍 Error details: {traceback.format_exc()}")


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