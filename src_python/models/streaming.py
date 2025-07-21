import asyncio
from typing import List, Dict, Any, Callable, Optional


async def call_models_in_parallel_with_streaming(
    models: List,
    messages: List[Dict[str, str]],
    on_chunk: Optional[Callable[[str, str], None]] = None
) -> Dict[str, Any]:
    """Call all models in parallel with streaming support"""
    active_models = set(model.name for model in models)
    results = {}
    
    async def process_model(model):
        try:
            result = await model.send_message(messages, on_chunk)
            results[model.name] = result
        finally:
            active_models.discard(model.name)
            if not active_models and on_chunk:
                on_chunk('_complete_', '')
    
    tasks = [process_model(model) for model in models]
    await asyncio.gather(*tasks)
    
    return results