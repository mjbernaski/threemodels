#!/bin/bash
# Convenience script to run the Python version

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    python3 setup.py
fi

echo "Starting Multi-Model AI Conversation System (Python)..."
source venv/bin/activate && python run.py