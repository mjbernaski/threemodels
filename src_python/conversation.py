import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConversationManager:
    def __init__(self, filename: str = 'conversation.json'):
        self.filename = filename
        self.conversation = {
            'rounds': [],
            'metadata': {
                'start_time': datetime.now().isoformat(),
                'total_rounds': 0
            }
        }
    
    async def load(self):
        """Load conversation from file"""
        try:
            with open(self.filename, 'r') as f:
                self.conversation = json.load(f)
        except FileNotFoundError:
            print('Starting new conversation')
    
    async def save(self):
        """Save conversation to file"""
        with open(self.filename, 'w') as f:
            json.dump(self.conversation, f, indent=2)
    
    def add_round(self, user_prompt: str, model_responses: Dict[str, Any], is_assessment: bool = False):
        """Add a conversation round"""
        round_data = {
            'id': len(self.conversation['rounds']) + 1,
            'timestamp': datetime.now().isoformat(),
            'userPrompt': user_prompt,
            'responses': model_responses,
            'isAssessment': is_assessment
        }
        
        self.conversation['rounds'].append(round_data)
        self.conversation['metadata']['total_rounds'] += 1
        self.conversation['metadata']['last_updated'] = datetime.now().isoformat()
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages for model context"""
        messages = []
        
        for round_data in self.conversation['rounds']:
            messages.append({
                'role': 'user',
                'content': round_data['userPrompt']
            })
            
            if (not round_data['isAssessment'] and 
                'Anthropic' in round_data['responses'] and 
                'error' not in round_data['responses']['Anthropic']):
                messages.append({
                    'role': 'assistant',
                    'content': round_data['responses']['Anthropic']['content']
                })
        
        return messages
    
    def get_last_responses(self) -> Optional[Dict[str, Any]]:
        """Get the last round's responses"""
        if not self.conversation['rounds']:
            return None
        return self.conversation['rounds'][-1]['responses']
    
    def format_assessment_prompt(self, original_prompt: str, responses: Dict[str, Any]) -> str:
        """Format prompt for model assessment"""
        prompt = f'Original prompt: "{original_prompt}"\n\n'
        prompt += 'Here are the responses from three different AI models:\n\n'
        
        for model, response in responses.items():
            prompt += f'{model} Response:\n'
            if 'error' in response:
                prompt += f'[Error: {response["error"]}]\n\n'
            else:
                prompt += f'{response["content"]}\n\n'
        
        prompt += 'Please analyze and compare these responses.'
        return prompt