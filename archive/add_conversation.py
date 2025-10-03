#!/usr/bin/env python
import asyncio
import json
from datetime import datetime
from src_python.models.index import create_models, call_models_in_parallel

async def main():
    prompt = "why learn latin?"
    print(f"Running prompt: {prompt}\n")

    # Get responses from all models
    models = create_models()
    messages = [{"role": "user", "content": prompt}]
    results = await call_models_in_parallel(models, messages)

    # Load existing conversation
    try:
        with open('data/conversations/conversation.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"rounds": []}

    # Add new round
    new_round = {
        "id": len(data["rounds"]) + 1,
        "timestamp": datetime.now().isoformat(),
        "userPrompt": prompt,
        "responses": results,
        "isAssessment": False
    }

    data["rounds"].append(new_round)

    # Save updated conversation
    import os
    os.makedirs('data/conversations', exist_ok=True)
    with open('data/conversations/conversation.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Conversation saved to data/conversations/conversation.json")

    # Display results
    for model_name, result in results.items():
        print(f"\n{'='*60}")
        print(f"{model_name} Response:")
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Content preview: {result['content'][:200]}...")

if __name__ == "__main__":
    asyncio.run(main())