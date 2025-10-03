#!/usr/bin/env python3
"""
Simple demo script to ask a question to all 3 AI models and generate a side-by-side HTML comparison.

This script demonstrates the core functionality of the three-models system:
1. Ask a single question to Anthropic Claude, OpenAI GPT, and Google Gemini
2. Generate a beautiful side-by-side HTML comparison
3. Open the comparison in your browser

Usage:
    python demo_simple_question.py "Your question here"
    
Or run interactively:
    python demo_simple_question.py
"""

import asyncio
import sys
import subprocess
from src_python.config import validate_config
from src_python.models.index import create_models, call_models_in_parallel
from src_python.conversation import ConversationManager
from conversation_side_by_side import create_side_by_side_html


async def ask_simple_question(question: str):
    """
    Ask a single question to all 3 models and generate HTML comparison
    """
    print("🤖 Multi-Model AI Question Demo")
    print("=" * 40)
    print(f"Question: {question}")
    print()
    
    # Validate configuration (check API keys)
    try:
        validate_config()
        print("✅ API keys validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please ensure you have a .env file with:")
        print("  ANTHROPIC_API_KEY=your_key_here")
        print("  OPENAI_API_KEY=your_key_here") 
        print("  GEMINI_API_KEY=your_key_here")
        return
    
    # Create models and conversation manager
    models = create_models()
    conversation = ConversationManager('demo_conversation.json')
    
    print("🚀 Sending question to all models...")
    print()
    
    # Prepare messages for the models
    messages = [{'role': 'user', 'content': question}]
    
    # Track responses as they come in
    completed_models = set()
    
    def on_response_received(model_name: str, content: str, duration: float):
        """Callback for when a model response is received"""
        completed_models.add(model_name)
        print(f"✅ {model_name} responded in {duration:.2f}s")
        print(f"📝 Response preview: {content[:100]}...")
        print("-" * 50)
    
    # Call all models in parallel
    responses = await call_models_in_parallel(
        models, 
        messages, 
        max_retries=3, 
        on_response=on_response_received
    )
    
    # Show summary
    print("\n📊 Final Summary:")
    for model, response in responses.items():
        timing_info = f"⏱️ {response.get('response_time', 0):.2f}s"
        retry_info = f"🔄 {response.get('attempts', 1)} attempt(s)"
        
        if 'error' in response:
            print(f"❌ {model}: Error - {response['error']} | {timing_info} | {retry_info}")
        else:
            tokens = response.get('usage', {}).get('total_tokens', 'N/A')
            print(f"✅ {model}: Success | {timing_info} | {retry_info} | 🪙 {tokens} tokens")
    
    # Add to conversation and save
    conversation.add_round(question, responses)
    await conversation.save()
    
    # Generate HTML comparison
    print("\n📄 Generating HTML comparison...")
    html_file = 'demo_comparison.html'
    create_side_by_side_html('demo_conversation.json', html_file)
    
    # Open in browser
    try:
        subprocess.run(['open', html_file], check=True)
        print(f"🌐 Opening comparison in browser: {html_file}")
    except subprocess.CalledProcessError:
        print(f"⚠️  Could not open browser automatically. Open {html_file} manually.")
    
    print("\n✨ Demo complete! Check out the HTML file to see the side-by-side comparison.")


async def interactive_demo():
    """Run interactive demo where user can ask questions"""
    print("🤖 Interactive Multi-Model AI Demo")
    print("=" * 40)
    print("Type your questions and see responses from all 3 models!")
    print("Type 'exit' to quit.")
    print()
    
    # Validate configuration
    try:
        validate_config()
        print("✅ API keys validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Create models and conversation manager
    models = create_models()
    conversation = ConversationManager('demo_conversation.json')
    
    while True:
        try:
            question = input("\n❓ Your question: ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break
            
            await ask_simple_question(question)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Command line argument provided
        question = ' '.join(sys.argv[1:])
        asyncio.run(ask_simple_question(question))
    else:
        # Interactive mode
        asyncio.run(interactive_demo())