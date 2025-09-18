# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Python Version (Primary)
- **Run main app**: `./run_python.sh` or `source venv/bin/activate && python run.py`
- **Run streaming version**: `./stream_python.sh` or `source venv/bin/activate && python -m src_python.index_streaming`
- **Run tests**: `source venv/bin/activate && python test.py`
- **Install dependencies**: `python3 setup.py` (handles venv creation and pip install)

### JavaScript Version (Legacy)
- **Run main app**: `npm start` or `node run.js`
- **Run streaming version**: `npm run stream`
- **Run tests**: `npm test` or `node test.js`

## Architecture

This is a multi-model AI conversation system that queries three AI models (Anthropic Claude, OpenAI GPT, and Google Gemini) simultaneously and displays their responses for comparison.

### Core Components

1. **Model Integration Layer** (`src_python/models/`)
   - Base model abstraction in `base.py` defines the interface
   - Each model (Anthropic, OpenAI, Gemini) implements the base interface
   - `index.py` handles parallel execution of all models via asyncio

2. **Conversation Management** (`src_python/conversation.py`)
   - Persists conversations to `conversation.json`
   - Maintains message history and metadata
   - Supports "assess" mode where models analyze each other's responses

3. **HTML Visualization** (`conversation_side_by_side.py`)
   - Generates side-by-side comparisons of model responses
   - Converts markdown to HTML with proper formatting
   - Creates interactive web view for conversation analysis

### Model Specifics

- **Anthropic**: Uses `claude-sonnet-4-20250514` model
- **OpenAI**: Uses `gpt-5` model
- **Gemini**: Uses `gemini-2.5-pro` model

All models support both streaming and non-streaming modes. The system handles API response format differences transparently.

### Configuration

Requires `.env` file with API keys:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`