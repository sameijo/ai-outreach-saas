#!/bin/bash
# Quick start script — runs backend locally without Docker
set -e

cd "$(dirname "$0")"

echo "🚀 AI Outreach — Quick Start"
echo "============================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Install deps
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt 2>/dev/null

# Create .env if missing
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env — edit it with your API keys"
fi

# Start backend
echo ""
echo "✅ Starting backend on http://localhost:8000"
echo "📖 API docs at http://localhost:8000/docs"
echo "Press Ctrl+C to stop"
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
