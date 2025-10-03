## Three Models

A minimal multi‑model conversation runner for Anthropic, OpenAI, and Gemini. It supports:

- Interactive Python CLI that saves conversations and auto‑generates HTML comparisons
- Node web server with a simple UI and real‑time updates via WebSockets
- Clean output structure for saved conversations and generated HTML

### Requirements

- Node.js 18+ (ESM). Recommend 20+
- Python 3.10+

### Setup

1) Install Node dependencies

```bash
npm install
```

2) Create a Python virtual environment and install deps

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3) Configure API keys (create a .env file in the project root)

```bash
# required
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...

# one of these is required for Google/Gemini
GEMINI_API_KEY=...   # preferred
# or
GOOGLE_API_KEY=...
```

Both the Node and Python apps read environment variables via dotenv.

### Running the Web UI (Node)

```bash
npm run web
# opens a local server at http://localhost:3000
```

- Entry point: `web-server.js`
- Static files: `public/`
- Generated comparisons (HTML): `public/comparisons/`
- Conversations (JSON): `data/conversations/` (filenames like `conversation_<timestamp>.json`)

### Running the CLI (Python)

```bash
source venv/bin/activate
python run.py
```

CLI tips:
- Type a prompt and press Enter to ask all models
- Type `assess` to have the models analyze the previous round
- Type `reset` to clear the in‑memory conversation
- Type `exit` to save and quit

On save, the CLI automatically writes:
- JSON conversation to `data/conversations/conversation.json`
- HTML comparison to `public/comparisons/conversation_YYYYMMDD_HHMMSS.html`
  - A convenience `public/comparisons/latest.html` is also written

### Output locations

- Conversations (JSON): `data/conversations/`
- Comparisons (HTML): `public/comparisons/`

These directories are created automatically when needed.

### Scripts and utilities

- Core code:
  - Node: `src/` and `web-server.js`
  - Python: `src_python/` and `run.py`
- Archived examples and legacy utilities: `archive/`

### Troubleshooting

- Missing API keys: ensure `.env` contains the required keys and the shell has access to them
- Cannot open browser automatically: open the generated HTML under `public/comparisons/` manually
- Node ESM errors: use Node 18+ and keep `"type": "module"` in `package.json`

### License

Proprietary. All rights reserved.


