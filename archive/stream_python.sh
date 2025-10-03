#!/bin/bash
# Convenience script to run the Python streaming version

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    python3 setup.py
fi

echo "Starting Multi-Model AI Conversation System (Python - Streaming)..."
source venv/bin/activate && python -m src_python.index_streaming