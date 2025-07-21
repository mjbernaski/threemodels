import os
from dotenv import load_dotenv

load_dotenv()

config = {
    'anthropic': {
        'api_key': os.getenv('ANTHROPIC_API_KEY')
    },
    'openai': {
        'api_key': os.getenv('OPENAI_API_KEY')
    },
    'google': {
        'api_key': os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    }
}

def validate_config():
    missing = []
    if not config['anthropic']['api_key']:
        missing.append('ANTHROPIC_API_KEY')
    if not config['openai']['api_key']:
        missing.append('OPENAI_API_KEY')
    if not config['google']['api_key']:
        missing.append('GEMINI_API_KEY or GOOGLE_API_KEY')
    
    if missing:
        raise ValueError(f"Missing required API keys: {', '.join(missing)}")