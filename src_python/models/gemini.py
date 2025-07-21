import google.generativeai as genai
from typing import List, Dict, Any, Optional, Callable
from .base import BaseModel
from ..config import config


class GeminiModel(BaseModel):
    def __init__(self):
        super().__init__('Gemini')
        genai.configure(api_key=config['google']['api_key'])
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    async def send_message(
        self, 
        messages: List[Dict[str, str]], 
        on_chunk: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        try:
            formatted_messages = self.format_messages(messages)
            
            if on_chunk:
                chat = self.model.start_chat(history=formatted_messages[:-1])
                response = await chat.send_message_async(
                    formatted_messages[-1]['parts'][0],
                    stream=True
                )
                
                full_content = ''
                async for chunk in response:
                    if chunk.text:
                        full_content += chunk.text
                        on_chunk(self.name, chunk.text)
                
                return {
                    'model': self.name,
                    'content': full_content,
                    'usage': None
                }
            else:
                chat = self.model.start_chat(history=formatted_messages[:-1])
                response = await chat.send_message_async(
                    formatted_messages[-1]['parts'][0]
                )
                
                return {
                    'model': self.name,
                    'content': response.text,
                    'usage': {
                        'prompt_tokens': response.usage_metadata.prompt_token_count,
                        'completion_tokens': response.usage_metadata.candidates_token_count,
                        'total_tokens': response.usage_metadata.total_token_count
                    } if hasattr(response, 'usage_metadata') else None
                }
        except Exception as e:
            return {
                'model': self.name,
                'error': str(e)
            }
    
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        formatted = []
        for msg in messages:
            if msg['role'] == 'user':
                formatted.append({
                    'role': 'user',
                    'parts': [msg['content']]
                })
            elif msg['role'] == 'assistant':
                formatted.append({
                    'role': 'model',
                    'parts': [msg['content']]
                })
        return formatted