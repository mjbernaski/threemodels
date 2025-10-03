import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
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


async def call_model_with_retry(
    model,
    messages: List[Dict[str, str]],
    max_retries: int = 3,
    on_response: Optional[Callable[[str, str, float], None]] = None
) -> Dict[str, Any]:
    """Call a single model with retry logic and timing"""
    start_time = time.time()

    for attempt in range(max_retries):
        try:
            result = await model.send_message(messages)
            end_time = time.time()
            duration = end_time - start_time

            # Check if we got an error response (retry if so, unless it's the last attempt)
            if 'error' in result:
                if attempt == max_retries - 1:  # Last attempt
                    result['response_time'] = duration
                    result['attempts'] = attempt + 1
                    return result
                else:
                    # Wait before retry (exponential backoff)
                    print(f'🔄 {model.name} attempt {attempt + 1} failed: {result.get("error", "Unknown error")[:50]}... Retrying in {2 ** attempt}s')
                    await asyncio.sleep(2 ** attempt)
                    continue

            # Success case
            # Call callback if response received successfully
            if on_response:
                on_response(model.name, result.get('content', ''), duration)

            # Add timing information to result
            result['response_time'] = duration
            result['attempts'] = attempt + 1

            return result

        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                end_time = time.time()
                duration = end_time - start_time
                return {
                    'model': model.name,
                    'error': f'Failed after {max_retries} attempts: {str(e)}',
                    'response_time': duration,
                    'attempts': max_retries
                }

            # Wait before retry (exponential backoff)
            print(f'🔄 {model.name} attempt {attempt + 1} exception: {str(e)[:50]}... Retrying in {2 ** attempt}s')
            await asyncio.sleep(2 ** attempt)


async def call_models_in_parallel(
    models: List,
    messages: List[Dict[str, str]],
    max_retries: int = 3,
    on_response: Optional[Callable[[str, str, float], None]] = None
) -> Dict[str, Any]:
    """Call all models in parallel with retry logic and return results"""
    tasks = [
        call_model_with_retry(model, messages, max_retries, on_response)
        for model in models
    ]
    results = await asyncio.gather(*tasks)

    return {
        result['model']: result
        for result in results
    }