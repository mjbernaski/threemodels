import asyncio
from typing import List, Dict, Any
from .anthropic import AnthropicModel
from .openai import OpenAIModel
from .gemini import GeminiModel


def create_models():
    """Create instances of all models"""
    return [
        AnthropicModel(),
        OpenAIModel(),
        GeminiModel()
    ]


async def call_models_in_parallel(models: List, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """Call all models in parallel and return results"""
    tasks = [model.send_message(messages) for model in models]
    results = await asyncio.gather(*tasks)
    
    return {
        result['model']: result
        for result in results
    }