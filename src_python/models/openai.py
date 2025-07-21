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
                    model='gpt-4o',
                    messages=messages,
                    stream=True
                )
                
                full_content = ''
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_content += content
                        on_chunk(self.name, content)
                
                return {
                    'model': self.name,
                    'content': full_content,
                    'usage': None
                }
            else:
                response = await self.client.chat.completions.create(
                    model='gpt-4o',
                    messages=messages
                )
                
                return {
                    'model': self.name,
                    'content': response.choices[0].message.content,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    } if response.usage else None
                }
        except Exception as e:
            return {
                'model': self.name,
                'error': str(e)
            }