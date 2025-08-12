#!/bin/bash

echo "🚀 Quick Start - AI Live Commerce"
echo "================================="

# Check dependencies
echo "📦 Checking dependencies..."
pip install fastapi uvicorn python-multipart sqlalchemy passlib[bcrypt] -q

# Create frontend directory
mkdir -p frontend

# Check if database exists
if [ ! -f "ai_live_commerce.db" ]; then
    echo "📊 Initializing database..."
    python main_minimal.py initdb
fi

# Start server
echo ""
echo "✅ Starting server..."
echo "🌐 Dashboard: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop"
echo ""

python app.py
