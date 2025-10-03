import google.generativeai as genai
from typing import List, Dict, Any, Optional, Callable
from .base import BaseModel
from ..config import config


class GeminiModel(BaseModel):
    def __init__(self):
        super().__init__('Gemini')
        genai.configure(api_key=config['google']['api_key'])
        self.model = genai.GenerativeModel('gemini-2.5-pro')
    
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
                usage = None

                try:
                    async for chunk in response:
                        if hasattr(chunk, 'text') and chunk.text:
                            full_content += chunk.text
                            on_chunk(self.name, chunk.text)

                        # Try to extract usage metadata from chunk if available
                        if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                            try:
                                usage = {
                                    'prompt_tokens': getattr(chunk.usage_metadata, 'prompt_token_count', 0),
                                    'completion_tokens': getattr(chunk.usage_metadata, 'candidates_token_count', 0),
                                    'total_tokens': getattr(chunk.usage_metadata, 'total_token_count', 0)
                                }
                            except AttributeError:
                                pass
                except Exception as e:
                    # If streaming fails, fall back to basic response
                    pass

                return {
                    'model': self.name,
                    'content': full_content,
                    'usage': usage
                }
            else:
                chat = self.model.start_chat(history=formatted_messages[:-1])
                response = await chat.send_message_async(
                    formatted_messages[-1]['parts'][0]
                )
                
                usage = None
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    try:
                        usage = {
                            'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                            'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                            'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0)
                        }
                    except AttributeError:
                        pass

                return {
                    'model': self.name,
                    'content': response.text,
                    'usage': usage
                }
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"🚨 GEMINI ERROR DEBUG: {error_msg}")
            print(f"🚨 GEMINI TRACEBACK: {traceback.format_exc()}")

            # Check if this is the mysterious 'metadata' error
            if "'metadata'" in error_msg or "metadata" in error_msg.lower():
                print(f"🚨 FOUND METADATA ERROR IN GEMINI: {error_msg}")
                print(f"🚨 FULL TRACEBACK: {traceback.format_exc()}")

            return {
                'model': self.name,
                'error': error_msg
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