#!/bin/bash
cd "$(dirname "$0")/backend"

echo ""
echo "  =========================================="
echo "    Lyze Backend"
echo "    http://localhost:8000"
echo "  =========================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "  Python 3 not found. Install from https://python.org"
    exit 1
fi

# Install deps if needed
if [ ! -f ".deps_installed" ]; then
    echo "  Installing dependencies..."
    pip3 install -r requirements.txt
    touch .deps_installed
    echo "  Done."
    echo ""
fi

# Check Ollama
if ! command -v ollama &>/dev/null; then
    echo "  WARNING: Ollama not found."
    echo "  Install from https://ollama.com for local AI."
    echo "  Or set API keys in backend/.env for cloud providers."
    echo ""
fi

echo "  Starting backend..."
echo "  Keep this terminal open while using Lyze."
echo "  Press Ctrl+C to stop."
echo ""
python3 main.py
