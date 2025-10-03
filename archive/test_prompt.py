#!/usr/bin/env python
import asyncio
from src_python.models.index import create_models, call_models_in_parallel

async def main():
    prompt = "why learn latin?"
    print(f"Testing prompt: {prompt}\n")
    models = create_models()
    messages = [{"role": "user", "content": prompt}]
    results = await call_models_in_parallel(models, messages)

    for model_name, result in results.items():
        print(f"\n{'='*60}")
        print(f"{model_name} Response:")
        print(f"{'='*60}")
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(result['content'])
            if result.get('usage'):
                print(f"\nTokens: {result['usage']}")

if __name__ == "__main__":
    asyncio.run(main())