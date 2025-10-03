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
                
                try:
                    async with self.client.messages.stream(
                        model='claude-sonnet-4-20250514',
                        max_tokens=4096,
                        messages=formatted_messages
                    ) as stream:
                        async for chunk in stream:
                            if hasattr(chunk, 'type'):
                                if chunk.type == 'content_block_delta' and hasattr(chunk, 'delta'):
                                    full_content += chunk.delta.text
                                    on_chunk(self.name, chunk.delta.text)
                                elif chunk.type == 'message_delta' and hasattr(chunk, 'usage'):
                                    usage = chunk.usage
                except Exception as stream_error:
                    # If streaming fails, fall back gracefully
                    pass
                
                return {
                    'model': self.name,
                    'content': full_content,
                    'usage': usage.__dict__ if usage else None
                }
            else:
                response = await self.client.messages.create(
                    model='claude-sonnet-4-20250514',
                    max_tokens=4096,
                    messages=formatted_messages
                )
                
                usage = None
                if hasattr(response, 'usage') and response.usage:
                    try:
                        usage = {
                            'input_tokens': getattr(response.usage, 'input_tokens', 0),
                            'output_tokens': getattr(response.usage, 'output_tokens', 0),
                            'total_tokens': getattr(response.usage, 'input_tokens', 0) + getattr(response.usage, 'output_tokens', 0)
                        }
                    except AttributeError:
                        pass

                return {
                    'model': self.name,
                    'content': response.content[0].text if response.content else '',
                    'usage': usage
                }
        except Exception as e:
            import traceback
            error_msg = str(e)

            # Enhanced error logging
            print(f"🚨 ANTHROPIC ERROR DEBUG: {error_msg}")
            print(f"🚨 ANTHROPIC TRACEBACK: {traceback.format_exc()}")

            # Check if this is the mysterious 'metadata' error
            if "'metadata'" in error_msg or "metadata" in error_msg.lower():
                print(f"🚨 FOUND METADATA ERROR IN ANTHROPIC: {error_msg}")

            # Enhanced error handling with HTTP status codes and types
            status_code = getattr(e, 'status_code', None) or getattr(e, 'response', {}).get('status_code')
            error_type = getattr(e, 'type', None) or getattr(getattr(e, 'body', {}), 'type', None)

            if status_code == 401:
                detailed_error = f"Authentication failed (401): Check API key validity"
            elif status_code == 429:
                detailed_error = f"Rate limited (429): Too many requests, try again later"
            elif status_code in [500, 502, 503]:
                detailed_error = f"Anthropic server error ({status_code}): Service temporarily unavailable"
            elif status_code == 400:
                detailed_error = f"Invalid request (400): {error_msg}"
            elif error_type == 'overloaded_error' or "overloaded" in error_msg.lower():
                detailed_error = f"Service overloaded: Anthropic servers are experiencing high demand"
            elif any(term in error_msg.lower() for term in ["connection", "timeout", "network", "enotfound", "econnreset", "connectionerror"]):
                detailed_error = f"Network connection error: Unable to reach Anthropic servers - {error_msg}"
            elif "api" in error_msg.lower() and "key" in error_msg.lower():
                detailed_error = f"API key error: {error_msg}"
            elif "rate" in error_msg.lower() and "limit" in error_msg.lower():
                detailed_error = f"Rate limit exceeded: {error_msg}"
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                detailed_error = f"Quota/billing issue: {error_msg}"
            else:
                detailed_error = f"Anthropic API error{f' ({status_code})' if status_code else ''}: {error_msg}"

            return {
                'model': self.name,
                'error': detailed_error
            }
    
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return [
            {
                'role': 'assistant' if msg['role'] == 'system' else msg['role'],
                'content': msg['content']
            }
            for msg in messages
        ]