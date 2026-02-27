#!/bin/bash

echo "=================================="
echo "GitHub Repository Summarizer"
echo "=================================="
echo ""

python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.10+ required. You have Python $python_version"
    exit 1
fi

echo "Python $python_version detected"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

if [ -f ".env" ]; then
    echo "Found .env file"
    source .env
elif [ -z "$NEBIUS_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    echo "Warning: No API key found!"
    echo ""
    echo "Please create a .env file with your API key:"
    echo "  1. Copy the example: cp .env.example .env"
    echo "  2. Edit .env and add your actual API key"
    echo ""
    echo "Or set an environment variable:"
    echo "  export NEBIUS_API_KEY='your-key-here'"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "API key configured via environment variable"
fi

echo ""
echo "Starting server on http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""
python main.py
