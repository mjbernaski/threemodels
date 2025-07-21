import anthropic
from typing import List, Dict, Any, Optional, Callable
from .base import BaseModel
from ..config import config


class AnthropicModel(BaseModel):
    def __init__(self):
        super().__init__('Anthropic')
        self.client = anthropic.AsyncAnthropic(
            api_key=config['anthropic']['api_key']
        )
    
    async def send_message(
        self, 
        messages: List[Dict[str, str]], 
        on_chunk: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        try:
            formatted_messages = self.format_messages(messages)
            
            if on_chunk:
                full_content = ''
                usage = None
                
                async with self.client.messages.stream(
                    model='claude-3-5-sonnet-20241022',
                    max_tokens=4096,
                    messages=formatted_messages
                ) as stream:
                    async for chunk in stream:
                        if hasattr(chunk, 'type'):
                            if chunk.type == 'content_block_delta':
                                full_content += chunk.delta.text
                                on_chunk(self.name, chunk.delta.text)
                            elif chunk.type == 'message_delta' and hasattr(chunk, 'usage'):
                                usage = chunk.usage
                
                return {
                    'model': self.name,
                    'content': full_content,
                    'usage': usage.__dict__ if usage else None
                }
            else:
                response = await self.client.messages.create(
                    model='claude-3-5-sonnet-20241022',
                    max_tokens=4096,
                    messages=formatted_messages
                )
                
                return {
                    'model': self.name,
                    'content': response.content[0].text,
                    'usage': {
                        'input_tokens': response.usage.input_tokens,
                        'output_tokens': response.usage.output_tokens,
                        'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                    } if hasattr(response, 'usage') else None
                }
        except Exception as e:
            return {
                'model': self.name,
                'error': str(e)
            }
    
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return [
            {
                'role': 'assistant' if msg['role'] == 'system' else msg['role'],
                'content': msg['content']
            }
            for msg in messages
        ]