from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable


class BaseModel(ABC):
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def send_message(
        self, 
        messages: List[Dict[str, str]], 
        on_chunk: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """Send message to the model and return response"""
        pass
    
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for the specific model API"""
        return messages