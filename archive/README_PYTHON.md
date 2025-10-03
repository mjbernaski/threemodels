# Three Models - Python Version

A Python implementation of the Multi-Model AI Conversation System that allows you to interact with multiple AI models (Anthropic Claude, OpenAI GPT, and Google Gemini) simultaneously.

## Migration Complete

This project has been fully migrated from JavaScript/Node.js to Python. The Python version maintains all the functionality of the original while providing better async support and improved error handling.

## Features

- **Multi-Model Support**: Chat with Anthropic Claude, OpenAI GPT-4, and Google Gemini simultaneously
- **Conversation Management**: Automatic saving and loading of conversation history
- **Assessment Mode**: Ask models to analyze and compare each other's responses
- **Streaming Support**: Real-time streaming responses with colored output
- **Async Architecture**: Built with Python's asyncio for efficient concurrent API calls

## Setup

### Option 1: Automatic Setup
```bash
python3 setup.py
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with your API keys:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## Usage

### Main Application
```bash
# Using convenience script
./run_python.sh

# Or manually
source venv/bin/activate && python run.py
```

### Streaming Version
```bash
# Using convenience script
./stream_python.sh

# Or manually
source venv/bin/activate && python -m src_python.index_streaming
```

### Testing
```bash
source venv/bin/activate && python test.py
```

### Simple Example
```bash
source venv/bin/activate && python -m src_python.simple
```

## Commands

Once running, you can use these commands:

- **Regular prompt**: Type any question or prompt to send to all models
- **`assess`**: Have models analyze and compare the previous responses
- **`exit`**: Save conversation and quit

## Project Structure

```
├── src_python/           # Python source code
│   ├── models/          # Model implementations
│   │   ├── base.py      # Base model class
│   │   ├── anthropic.py # Anthropic Claude integration
│   │   ├── openai.py    # OpenAI GPT integration
│   │   ├── gemini.py    # Google Gemini integration
│   │   ├── index.py     # Model factory and parallel execution
│   │   └── streaming.py # Streaming utilities
│   ├── config.py        # Configuration and validation
│   ├── conversation.py  # Conversation management
│   ├── index_streaming.py # Streaming version
│   └── simple.py        # Simple test example
├── run.py               # Main application entry point
├── test.py              # Test script
├── setup.py             # Setup script
├── requirements.txt     # Python dependencies
├── run_python.sh        # Convenience script for main app
└── stream_python.sh     # Convenience script for streaming
```

## Migration Notes

### Key Changes from JavaScript Version
- **Async/Await**: Full async implementation using Python's asyncio
- **Type Hints**: Added comprehensive type annotations
- **Error Handling**: Improved exception handling and validation
- **Virtual Environment**: Isolated dependency management
- **Modular Design**: Clear separation of concerns

### API Compatibility
- All original features maintained
- Same conversation format and file structure
- Compatible with existing conversation.json files
- Same command interface

## Dependencies

- `anthropic>=0.39.0` - Anthropic Claude API client
- `openai>=1.54.0` - OpenAI API client  
- `google-generativeai>=0.8.0` - Google Gemini API client
- `python-dotenv>=1.0.0` - Environment variable management
- `asyncio-throttle>=1.0.2` - Async rate limiting utilities

## Troubleshooting

### Virtual Environment Issues
If you encounter virtual environment issues, try:
```bash
rm -rf venv
python3 setup.py
```

### API Key Issues
Ensure your `.env` file is in the project root and contains valid API keys.

### Permission Issues
Make sure scripts are executable:
```bash
chmod +x setup.py run_python.sh stream_python.sh
```

## License

Same as original project.