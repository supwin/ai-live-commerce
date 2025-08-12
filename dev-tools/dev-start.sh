#!/bin/bash
# Development Start Script

echo "🚀 Starting AI Live Commerce Development Environment"

# Activate virtual environment
source venv/bin/activate

# Check if database exists
if [ ! -f "ai_live_commerce.db" ]; then
    echo "⚠️ Database not found. Creating new database..."
    python add_scripts_table.py
fi

# Start development server
echo "📡 Starting development server..."
python run_server.py

