from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional, Callable
from .base import BaseModel
from ..config import config


class OpenAIModel(BaseModel):
    def __init__(self):
        super().__init__('OpenAI')
        self.client = AsyncOpenAI(
            api_key=config['openai']['api_key']
        )
    
    async def send_message(
        self, 
        messages: List[Dict[str, str]], 
        on_chunk: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        try:
            if on_chunk:
                stream = await self.client.chat.completions.create(
                    model='gpt-5',
                    messages=messages,
                    stream=True
                )

                full_content = ''
                usage = None

                try:
                    async for chunk in stream:
                        if (hasattr(chunk, 'choices') and chunk.choices and
                            hasattr(chunk.choices[0], 'delta') and
                            hasattr(chunk.choices[0].delta, 'content') and
                            chunk.choices[0].delta.content):
                            content = chunk.choices[0].delta.content
                            full_content += content
                            on_chunk(self.name, content)

                        # Try to get usage from chunk if available
                        if hasattr(chunk, 'usage') and chunk.usage:
                            try:
                                usage = {
                                    'prompt_tokens': getattr(chunk.usage, 'prompt_tokens', 0),
                                    'completion_tokens': getattr(chunk.usage, 'completion_tokens', 0),
                                    'total_tokens': getattr(chunk.usage, 'total_tokens', 0)
                                }
                            except AttributeError:
                                pass
                except Exception as stream_error:
                    # If streaming fails, fall back gracefully
                    pass

                return {
                    'model': self.name,
                    'content': full_content,
                    'usage': usage
                }
            else:
                response = await self.client.chat.completions.create(
                    model='gpt-5',
                    messages=messages
                )
                
                usage = None
                if hasattr(response, 'usage') and response.usage:
                    try:
                        usage = {
                            'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
                            'completion_tokens': getattr(response.usage, 'completion_tokens', 0),
                            'total_tokens': getattr(response.usage, 'total_tokens', 0)
                        }
                    except AttributeError:
                        pass

                content = ''
                if (hasattr(response, 'choices') and response.choices and
                    hasattr(response.choices[0], 'message') and
                    hasattr(response.choices[0].message, 'content')):
                    content = response.choices[0].message.content or ''

                return {
                    'model': self.name,
                    'content': content,
                    'usage': usage
                }
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"🚨 OPENAI ERROR DEBUG: {error_msg}")
            print(f"🚨 OPENAI TRACEBACK: {traceback.format_exc()}")

            # Check if this is the mysterious 'metadata' error
            if "'metadata'" in error_msg or "metadata" in error_msg.lower():
                print(f"🚨 FOUND METADATA ERROR IN OPENAI: {error_msg}")
                print(f"🚨 FULL TRACEBACK: {traceback.format_exc()}")

            return {
                'model': self.name,
                'error': error_msg
            }